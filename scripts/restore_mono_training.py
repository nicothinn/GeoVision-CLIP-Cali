"""Restaura entrenamiento monolítico (una celda) como antes."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks" / "sit2_geovision_clip.ipynb"

CELL6 = r'''# @title Configuración entrenamiento
import math
import random
import torch

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

BATCH_SIZE = 32
NUM_EPOCHS = 40
EARLY_STOP_PATIENCE = 6
VAL_CHECK_INTERVAL = 1.0
NUM_WORKERS = 2
LR = 1e-4
WEIGHT_DECAY = 0.01
FREEZE_TEXT_EPOCHS = 1
FREEZE_VISUAL = True
ALPHA_SAE = 0.1
LAMBDA_L1 = 1e-3

WANDB_PROJECT = "geovision-sit2-clip"
WANDB_RUN_NAME = "colab_clip_sae_train"
USE_WANDB = True

os.environ.setdefault("WANDB_SILENT", "true")
os.environ.setdefault("WANDB_DISABLE_CODE", "true")

def setup_wandb():
    global USE_WANDB
    if not USE_WANDB:
        os.environ["WANDB_MODE"] = "disabled"
        print("WANDB desactivado (USE_WANDB=False)")
        return
    try:
        import wandb
    except ImportError:
        USE_WANDB = False
        os.environ["WANDB_MODE"] = "disabled"
        print("wandb no instalado; solo CSVLogger")
        return
    key = os.environ.get("WANDB_API_KEY")
    if not key:
        try:
            from google.colab import userdata
            key = userdata.get("WANDB_API_KEY")
            os.environ["WANDB_API_KEY"] = key
        except Exception:
            pass
    if key:
        wandb.login(key=key, relogin=True)
        print("WANDB: login OK")
    else:
        os.environ["WANDB_MODE"] = "offline"
        print("WANDB: modo offline (sin API key). Secret WANDB_API_KEY o USE_WANDB=False")

setup_wandb()

METRICS_JSON = RUN_DIR / "metricas_por_epoca.json"
EMBEDDINGS_BEST = RUN_DIR / "embeddings_val_mejor.npz"
TEST_METRICS_JSON = RUN_DIR / "metricas_test.json"

KPI_RECALL1_MIN, KPI_RECALL1_EXC = 0.45, 0.65
KPI_RECALL5_MIN, KPI_RECALL5_EXC = 0.70, 0.85
KPI_SPARSITY_MIN, KPI_SPARSITY_EXC = 0.70, 0.85
KPI_MSE_SAE_MAX, KPI_MSE_SAE_EXC = 0.05, 0.02

device = "cuda" if torch.cuda.is_available() else "cpu"
print("device:", device, "| batch:", BATCH_SIZE, "| epochs:", NUM_EPOCHS)
print("Metricas JSON:", METRICS_JSON)
if device == "cpu":
    print("AVISO: activa GPU en Colab (Runtime -> T4 GPU -> Reiniciar)")
'''

CELL8 = r'''# @title DataLoaders (13 bandas normalizadas + tokenizer)
from transformers import AutoTokenizer

try:
    import lightning.pytorch as pl
except ImportError:
    import pytorch_lightning as pl

class Sit2TileDataset(Dataset):
    def __init__(self, frame, tiles_zarr, split, band_mean, band_std, tokenizer, max_length=256):
        self.df = frame.reset_index(drop=True)
        mask = self.df["split"].values == split
        self._indices = np.nonzero(mask)[0].astype(np.int64)
        self.z = tiles_zarr
        self.mean = torch.as_tensor(band_mean, dtype=torch.float32).view(13, 1, 1)
        self.std = torch.as_tensor(band_std, dtype=torch.float32).view(13, 1, 1).clamp(min=1e-6)
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return int(len(self._indices))

    def __getitem__(self, i):
        j = int(self._indices[i])
        row = self.df.iloc[j]
        tile = torch.from_numpy(np.asarray(self.z[j], dtype=np.float32))
        tile = (tile - self.mean) / self.std
        tok = self.tokenizer(
            str(row["descripcion"]), truncation=True, max_length=self.max_length,
            padding="max_length", return_tensors="pt",
        )
        return {
            "tile": tile,
            "input_ids": tok["input_ids"].squeeze(0),
            "attention_mask": tok["attention_mask"].squeeze(0),
            "tile_id": str(row["tile_id"]),
            "clase": str(row["clase"]),
        }

class Sit2SequenceDataset(Dataset):
    def __init__(self, frame, tiles_zarr, secuencias, band_mean, band_std, tokenizer, max_length=256):
        self.z = tiles_zarr
        self.seqs = secuencias
        self.mean = torch.as_tensor(band_mean, dtype=torch.float32).view(13, 1, 1)
        self.std = torch.as_tensor(band_std, dtype=torch.float32).view(13, 1, 1).clamp(min=1e-6)
        self.tokenizer = tokenizer
        self.max_length = max_length
        id2j = {str(r["tile_id"]): i for i, r in frame.reset_index(drop=True).iterrows()}
        self._valid = []
        for s in secuencias:
            js = [id2j.get(tid) for tid in s["tile_ids"]]
            if all(j is not None for j in js):
                self._valid.append((js, s["tile_ids"][-1], str(s["fechas"][-1])))

    def __len__(self):
        return len(self._valid)

    def __getitem__(self, i):
        js, last_tid, _ = self._valid[i]
        tiles = []
        for j in js:
            t = torch.from_numpy(np.asarray(self.z[int(j)], dtype=np.float32))
            tiles.append((t - self.mean) / self.std)
        tiles = torch.stack(tiles, dim=0)
        row = df[df["tile_id"] == last_tid].iloc[0]
        tok = self.tokenizer(
            str(row["descripcion"]), truncation=True, max_length=self.max_length,
            padding="max_length", return_tensors="pt",
        )
        return {
            "tiles_seq": tiles,
            "input_ids": tok["input_ids"].squeeze(0),
            "attention_mask": tok["attention_mask"].squeeze(0),
        }

def collate_sit2(batch):
    return {
        "tile": torch.stack([b["tile"] for b in batch]),
        "input_ids": torch.stack([b["input_ids"] for b in batch]),
        "attention_mask": torch.stack([b["attention_mask"] for b in batch]),
    }

band_mean, band_std = compute_band_stats(ZARR_PATH)
text_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
tokenizer = AutoTokenizer.from_pretrained(text_name)

ds_train = Sit2TileDataset(df, tiles_z, "train", band_mean, band_std, tokenizer)
ds_val = Sit2TileDataset(df, tiles_z, "val", band_mean, band_std, tokenizer)
ds_test = Sit2TileDataset(df, tiles_z, "test", band_mean, band_std, tokenizer)
ds_seq = Sit2SequenceDataset(df, tiles_z, secuencias, band_mean, band_std, tokenizer)
print(f"Train: {len(ds_train)} | Val: {len(ds_val)} | Test: {len(ds_test)} | Secuencias: {len(ds_seq)}")

train_loader = DataLoader(
    ds_train, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS,
    collate_fn=collate_sit2, pin_memory=torch.cuda.is_available(),
)
val_loader = DataLoader(
    ds_val, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS,
    collate_fn=collate_sit2, pin_memory=torch.cuda.is_available(),
)
test_loader = DataLoader(
    ds_test, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS,
    collate_fn=collate_sit2, pin_memory=torch.cuda.is_available(),
)
'''

CELL9 = r'''# @title Modelo GeoVision-CLIP + SAE
import open_clip
from huggingface_hub import hf_hub_download
from transformers import AutoModel

_CLIP_MEAN = (0.48145466, 0.4578275, 0.40821073)
_CLIP_STD = (0.26862954, 0.26130258, 0.27577711)

REMOTECLIP_HF_REPO = "chendelong/RemoteCLIP"
REMOTECLIP_MODEL_NAME = "ViT-B-32"
REMOTECLIP_CACHE_DIR = Path("/content/checkpoints")

def load_remoteclip_visual(model_name: str = REMOTECLIP_MODEL_NAME):
    REMOTECLIP_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    ckpt_path = hf_hub_download(
        REMOTECLIP_HF_REPO,
        f"RemoteCLIP-{model_name}.pt",
        cache_dir=str(REMOTECLIP_CACHE_DIR),
        token=token,
    )
    print(f"{model_name} descargado en: {ckpt_path}")
    model, _, _ = open_clip.create_model_and_transforms(model_name)
    try:
        ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=True)
    except TypeError:
        ckpt = torch.load(ckpt_path, map_location="cpu")
    msg = model.load_state_dict(ckpt)
    print("load_state_dict:", msg)
    visual = model.visual
    print(f"OK: RemoteCLIP visual ({model_name}) listo.")
    return visual, ckpt_path

class GeoVisionClipSAEModel(nn.Module):
    def __init__(self, text_model_name=text_name, dim_latent_sae=512, dim_contrastive=256,
                 alpha_sae=ALPHA_SAE, lambda_l1=LAMBDA_L1, freeze_visual=FREEZE_VISUAL):
        super().__init__()
        self.alpha_sae = alpha_sae
        self.lambda_l1 = lambda_l1
        self.ms_adapter = nn.Conv2d(13, 3, 1, bias=True)
        self.visual, self.visual_pretrained_tag = load_remoteclip_visual(REMOTECLIP_MODEL_NAME)
        if freeze_visual:
            for p in self.visual.parameters():
                p.requires_grad = False
        dim_img = int(getattr(self.visual, "output_dim", 512))
        self.text_encoder = AutoModel.from_pretrained(text_model_name)
        dtxt = int(self.text_encoder.config.hidden_size)
        self.text_to_sae = nn.Linear(dtxt, dim_latent_sae)
        self.sae_img = SparseAutoencoder(dim_img, dim_latent_sae)
        self.sae_txt = SparseAutoencoder(dim_latent_sae, dim_latent_sae)
        self.proj_img = nn.Linear(dim_latent_sae, dim_contrastive)
        self.proj_txt = nn.Linear(dim_latent_sae, dim_contrastive)
        self.logit_scale = nn.Parameter(torch.ones([]) * math.log(1.0 / 0.07))
        self.register_buffer("clip_mean", torch.tensor(_CLIP_MEAN).view(1, 3, 1, 1), persistent=False)
        self.register_buffer("clip_std", torch.tensor(_CLIP_STD).view(1, 3, 1, 1), persistent=False)

    def encode_image(self, tiles):
        tiles = tiles.float()
        x3 = self.ms_adapter(tiles)
        x3 = F.interpolate(x3, (224, 224), mode="bicubic", align_corners=False)
        x3 = (x3 - self.clip_mean) / self.clip_std
        h = self.visual(x3)
        h_hat, z = self.sae_img(h)
        return {"h": h, "z": z, "h_hat": h_hat, "e": self.proj_img(z)}

    def encode_text(self, input_ids, attention_mask):
        out = self.text_encoder(input_ids=input_ids, attention_mask=attention_mask)
        m = attention_mask.unsqueeze(-1).float()
        pooled = (out.last_hidden_state * m).sum(1) / m.sum(1).clamp(min=1e-6)
        h = self.text_to_sae(pooled)
        h_hat, z = self.sae_txt(h)
        return {"h": h, "z": z, "h_hat": h_hat, "e": self.proj_txt(z)}

    def clip_infonce(self, e_img, e_txt):
        e_img = F.normalize(e_img, dim=-1)
        e_txt = F.normalize(e_txt, dim=-1)
        scale = self.logit_scale.exp().clamp(max=100.0)
        logits = scale * (e_img @ e_txt.T)
        t = torch.arange(logits.size(0), device=logits.device)
        return 0.5 * (F.cross_entropy(logits, t) + F.cross_entropy(logits.T, t))

    def forward(self, tiles, input_ids, attention_mask):
        vi = self.encode_image(tiles)
        vt = self.encode_text(input_ids, attention_mask)
        l_infonce = self.clip_infonce(vi["e"], vt["e"])
        li, msei, _ = sae_loss(vi["h"], vi["h_hat"], vi["z"], self.lambda_l1)
        lt, mset, _ = sae_loss(vt["h"], vt["h_hat"], vt["z"], self.lambda_l1)
        total = l_infonce + self.alpha_sae * (li + lt)
        return {
            "loss": total, "loss_infonce": l_infonce.detach(),
            "loss_sae_img": li.detach(), "loss_sae_txt": lt.detach(),
            "mse_sae_img": msei.detach(), "mse_sae_txt": mset.detach(),
            "z_img": vi["z"], "z_txt": vt["z"],
        }

    def set_text_trainable(self, trainable):
        for p in self.text_encoder.parameters():
            p.requires_grad = trainable
        for p in self.text_to_sae.parameters():
            p.requires_grad = trainable

class LitGeoVisionClipSAE(pl.LightningModule):
    def __init__(self):
        super().__init__()
        self.model = GeoVisionClipSAEModel()
        self._val_img, self._val_txt = [], []
        self._val_z_img, self._val_z_txt = [], []

    def on_train_epoch_start(self):
        self.model.set_text_trainable(self.current_epoch >= FREEZE_TEXT_EPOCHS)

    def training_step(self, batch, batch_idx):
        o = self.model(batch["tile"], batch["input_ids"], batch["attention_mask"])
        self.log("train/loss", o["loss"], prog_bar=True, on_step=False, on_epoch=True)
        self.log("train/infonce", o["loss_infonce"], on_epoch=True)
        self.log("train/mse_sae_img", o["mse_sae_img"], on_epoch=True)
        self.log("train/mse_sae_txt", o["mse_sae_txt"], on_epoch=True)
        self.log("train/sparsity_img", sparsity_ratio(o["z_img"]), on_epoch=True, prog_bar=True)
        self.log("train/sparsity_txt", sparsity_ratio(o["z_txt"]), on_epoch=True)
        return o["loss"]

    def on_validation_epoch_start(self):
        self._val_img.clear()
        self._val_txt.clear()
        self._val_z_img.clear()
        self._val_z_txt.clear()

    def validation_step(self, batch, batch_idx):
        o = self.model(batch["tile"], batch["input_ids"], batch["attention_mask"])
        self.log("val/loss", o["loss"], on_epoch=True, prog_bar=True)
        self.log("val/infonce", o["loss_infonce"], on_epoch=True)
        self.log("val/mse_sae_img", o["mse_sae_img"], on_epoch=True)
        self.log("val/mse_sae_txt", o["mse_sae_txt"], on_epoch=True)
        self.log("val/sparsity_img", sparsity_ratio(o["z_img"]), on_epoch=True, prog_bar=True)
        with torch.no_grad():
            vi = self.model.encode_image(batch["tile"])
            vt = self.model.encode_text(batch["input_ids"], batch["attention_mask"])
        self._val_img.append(vi["e"].detach().cpu())
        self._val_txt.append(vt["e"].detach().cpu())
        self._val_z_img.append(vi["z"].detach().cpu())
        self._val_z_txt.append(vt["z"].detach().cpu())

    def on_validation_epoch_end(self):
        if not self._val_img:
            return
        img = torch.cat(self._val_img, 0).to(self.device)
        txt = torch.cat(self._val_txt, 0).to(self.device)
        self.log("val/recall_at_1", recall_at_k_image_to_text(img, txt, 1), prog_bar=True, on_epoch=True)
        self.log("val/recall_at_5", recall_at_k_image_to_text(img, txt, 5), prog_bar=True, on_epoch=True)

    def configure_optimizers(self):
        params = [p for p in self.model.parameters() if p.requires_grad]
        return torch.optim.AdamW(params, lr=LR, weight_decay=WEIGHT_DECAY)
'''

CELL10 = r'''# @title Entrenamiento + validación (una sola corrida)
import json
import sys
from pytorch_lightning.loggers import WandbLogger
from pytorch_lightning.callbacks import ModelCheckpoint, LearningRateMonitor, EarlyStopping, TQDMProgressBar
try:
    from lightning.pytorch.utilities.rank_zero import rank_zero_info
except ImportError:
    from pytorch_lightning.utilities.rank_zero import rank_zero_info

def _scalar(v):
    if hasattr(v, "item"):
        return float(v.item())
    return float(v)

def _kpi_flag(val, min_ok=None, max_ok=None, exc=None):
    if val is None:
        return "n/a"
    if min_ok is not None and val < min_ok:
        return "FAIL"
    if max_ok is not None and val > max_ok:
        return "FAIL"
    if exc is not None and val >= exc:
        return "EXC"
    if min_ok is not None and val >= min_ok:
        return "OK"
    if max_ok is not None and val <= max_ok:
        return "OK"
    return "parcial"

class EpochMetricsJsonCallback(pl.Callback):
    def __init__(self, json_path, embeddings_path, val_tile_ids):
        self.json_path = Path(json_path)
        self.embeddings_path = Path(embeddings_path)
        self.val_tile_ids = list(val_tile_ids)
        self.history = {"kpi_umbrales": {
            "recall_at_1_min": KPI_RECALL1_MIN, "recall_at_1_exc": KPI_RECALL1_EXC,
            "recall_at_5_min": KPI_RECALL5_MIN, "recall_at_5_exc": KPI_RECALL5_EXC,
            "sparsity_min": KPI_SPARSITY_MIN, "mse_sae_max": KPI_MSE_SAE_MAX,
        }, "epochs": [], "best": None}
        self._best_r1 = -1.0

    def _flush_json(self):
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        self.json_path.write_text(json.dumps(self.history, indent=2, ensure_ascii=False), encoding="utf-8")

    def on_train_epoch_end(self, trainer, pl_module):
        ep = int(trainer.current_epoch)
        m = {k: _scalar(v) for k, v in trainer.callback_metrics.items() if not k.startswith("_")}
        row = {"epoch": ep}
        for key in (
            "train/loss_epoch", "train/infonce", "train/mse_sae_img", "train/mse_sae_txt",
            "train/sparsity_img", "train/sparsity_txt",
            "val/loss", "val/infonce", "val/mse_sae_img", "val/mse_sae_txt",
            "val/sparsity_img", "val/recall_at_1", "val/recall_at_5",
        ):
            if key in m:
                row[key] = round(m[key], 6)
        self.history["epochs"].append(row)
        r1 = row.get("val/recall_at_1")
        r5 = row.get("val/recall_at_5")
        sp = row.get("val/sparsity_img")
        mse = row.get("val/mse_sae_img")
        improved = r1 is not None and r1 > self._best_r1
        if improved:
            self._best_r1 = r1
            self.history["best"] = dict(row)
            if pl_module._val_img:
                np.savez_compressed(
                    self.embeddings_path,
                    e_img=torch.cat(pl_module._val_img, 0).numpy(),
                    e_txt=torch.cat(pl_module._val_txt, 0).numpy(),
                    z_img=torch.cat(pl_module._val_z_img, 0).numpy(),
                    z_txt=torch.cat(pl_module._val_z_txt, 0).numpy(),
                    tile_ids=np.array(self.val_tile_ids, dtype=object),
                    epoch=ep,
                )
        self._flush_json()
        lines = [
            "", "=" * 60, f"Época {ep:03d}", "=" * 60,
            f"  train/loss = {row.get('train/loss_epoch', '—')}",
            f"  val/loss   = {row.get('val/loss', '—')}",
            f"  val/recall@1 = {r1}  [{_kpi_flag(r1, min_ok=KPI_RECALL1_MIN, exc=KPI_RECALL1_EXC)}]",
            f"  val/recall@5 = {r5}  [{_kpi_flag(r5, min_ok=KPI_RECALL5_MIN, exc=KPI_RECALL5_EXC)}]",
            f"  val/sparsity = {sp}  [{_kpi_flag(sp, min_ok=KPI_SPARSITY_MIN)}]",
            f"  val/mse_sae  = {mse}  [{_kpi_flag(mse, max_ok=KPI_MSE_SAE_MAX)}]",
        ]
        if improved:
            lines.append(f"  >> mejor recall@1 -> {self.embeddings_path.name}")
        rank_zero_info("\n".join(lines))
        sys.stdout.flush()

csv_logger = pl.loggers.CSVLogger(save_dir=str(RUN_DIR), name="metrics")
loggers = [csv_logger]
if USE_WANDB and os.environ.get("WANDB_API_KEY"):
    loggers.insert(0, WandbLogger(project=WANDB_PROJECT, name=WANDB_RUN_NAME, save_dir=str(RUN_DIR)))
else:
    print("WANDB omitido; metricas en", RUN_DIR)

val_tile_ids = df.loc[df["split"] == "val", "tile_id"].astype(str).tolist()
metrics_cb = EpochMetricsJsonCallback(METRICS_JSON, EMBEDDINGS_BEST, val_tile_ids)
ckpt_cb = ModelCheckpoint(
    dirpath=str(RUN_DIR / "checkpoints"),
    filename="best-{epoch:02d}-r1{val/recall_at_1:.3f}",
    monitor="val/recall_at_1", mode="max", save_top_k=1,
)
early_cb = EarlyStopping(monitor="val/recall_at_1", mode="max", patience=EARLY_STOP_PATIENCE, verbose=False)

if not torch.cuda.is_available():
    raise RuntimeError("GPU no detectada. Colab: Runtime -> T4 GPU -> Reiniciar.")

lit = LitGeoVisionClipSAE()
trainer = pl.Trainer(
    max_epochs=NUM_EPOCHS,
    accelerator="gpu",
    devices=1,
    logger=loggers,
    callbacks=[ckpt_cb, early_cb, metrics_cb, TQDMProgressBar(refresh_rate=10), LearningRateMonitor(logging_interval="epoch")],
    default_root_dir=str(RUN_DIR),
    log_every_n_steps=10,
    val_check_interval=VAL_CHECK_INTERVAL,
    enable_progress_bar=True,
    enable_model_summary=False,
)
trainer.fit(lit, train_dataloaders=train_loader, val_dataloaders=val_loader)
print("\nEntrenamiento terminado.")
print("Mejor checkpoint:", ckpt_cb.best_model_path)
print("Historial JSON:", METRICS_JSON)
print("Embeddings val:", EMBEDDINGS_BEST)
if USE_WANDB:
    import wandb
    wandb.finish()
'''

CELL11_MD = """## Gráficos de línea (después del entrenamiento)

Lee `metricas_por_epoca.json` y genera curvas.
"""

CELL12_GRAPHS = None  # keep from existing

CELL13_CKPT = r'''# @title Guardar checkpoint final
import hashlib

ckpt_path = RUN_DIR / "checkpoint.pt"
best = ckpt_cb.best_model_path if ckpt_cb.best_model_path else None
if best:
    lit_save = LitGeoVisionClipSAE()
    lit_save.load_state_dict(torch.load(best, map_location="cpu")["state_dict"])
else:
    lit_save = lit

bundle = {
    "state_dict": lit_save.model.state_dict(),
    "band_mean": band_mean.tolist(),
    "band_std": band_std.tolist(),
    "hparams": {"lr": LR, "batch_size": BATCH_SIZE, "epochs": NUM_EPOCHS, "seed": SEED},
    "best_checkpoint": str(best or ""),
}
torch.save(bundle, ckpt_path)
h = hashlib.md5(ckpt_path.read_bytes()).hexdigest()
(ckpt_path.with_suffix(".pt.md5")).write_text(h + "\n", encoding="utf-8")
print("Checkpoint:", ckpt_path, "| MD5:", h)
if best:
    print("Pesos desde:", best)
'''


def _lines(text: str) -> list[str]:
    if not text.endswith("\n"):
        text += "\n"
    return [ln if ln.endswith("\n") else ln + "\n" for ln in text.splitlines(keepends=True)]


def _code(text: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "source": _lines(text), "outputs": [], "execution_count": None}


def _md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": _lines(text)}


def main():
    nb = json.loads(NB.read_text(encoding="utf-8"))
    head = nb["cells"][:6]
    tail_graphs = None
    tail_kpi = None
    for c in nb["cells"]:
        src = "".join(c.get("source", []))
        if "Gráficos desde metricas_por_epoca" in src:
            tail_graphs = c
        if "KPIs consigna" in src and c["cell_type"] == "markdown":
            tail_kpi = c

    md0 = "".join(head[0]["source"])
    head[0]["source"] = _lines(
        md0.replace("4 celdas", "1 celda")
        .replace("Fase 1→2→3", "InfoNCE + SAE")
        .replace("60 épocas en 3 celdas + eval test", "40 épocas + early stopping")
    )

    new_tail = []
    if tail_graphs:
        new_tail.append(_md(CELL11_MD))
        new_tail.append(tail_graphs)
        tail_graphs["outputs"] = []
    if tail_kpi:
        new_tail.append(tail_kpi)

    nb["cells"] = head + [
        _code(CELL6),
        nb["cells"][7],
        _code(CELL8),
        _code(CELL9),
        _code(CELL10),
    ] + new_tail + [_code(CELL13_CKPT)]

    if not any("KPIs consigna" in "".join(c.get("source", [])) for c in nb["cells"]):
        nb["cells"].append(tail_kpi or _md("## KPIs consigna (val)\n\nRecall@1 ≥ 0.45, Recall@5 ≥ 0.70, Sparsity ≥ 0.70\n"))

    for c in nb["cells"]:
        if c["cell_type"] == "code":
            c["outputs"] = []
            c["execution_count"] = None

    NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Restaurado monolítico:", NB, "celdas:", len(nb["cells"]))


if __name__ == "__main__":
    main()
