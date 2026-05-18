"""Aplica entrenamiento por fases al notebook sit2_geovision_clip.ipynb."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB_PATH = ROOT / "notebooks" / "sit2_geovision_clip.ipynb"

CELL6 = r'''# @title Configuración entrenamiento (4 fases)
import math
import random
import torch

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

# --- Fases (épocas 0-indexed) ---
# Fase 0-1 (0-19): visual congelado, captions múltiples, augment, α_SAE bajo
# Fase 2   (20-39): últimos 2 bloques ViT + adaptador espectral
# Fase 3   (40-59): α_SAE consigna (0.1), afinar sparsity
NUM_EPOCHS = 60
PHASE1_END = 19
PHASE2_END = 39
MIN_EPOCHS_BEFORE_EARLY_STOP = 20

BATCH_SIZE = 64
GRAD_ACCUM_STEPS = 1
VAL_CHECK_INTERVAL = 1.0
NUM_WORKERS = 2

LR_HEAD = 5e-5
LR_TEXT = 1e-5
LR_VISUAL = 5e-6
WEIGHT_DECAY = 0.05
WARMUP_EPOCHS = 3
MIN_LR_RATIO = 0.01
FREEZE_TEXT_EPOCHS = 3
EARLY_STOP_PATIENCE = 12

ALPHA_SAE_WARMUP_EPOCHS = 5
ALPHA_SAE_PHASE1 = 0.05
ALPHA_SAE_PHASE3 = 0.1
LAMBDA_L1 = 1e-3
LAMBDA_L1_PHASE3 = 3e-3

VISUAL_UNFREEZE_BLOCKS = 2
AUGMENT_TRAIN = True
BAND_JITTER_STD = 0.02
USE_CAPTION_VARIANTS = True

FREEZE_VISUAL = True

WANDB_PROJECT = "geovision-sit2-clip"
WANDB_RUN_NAME = "colab_phased_4fases"
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
EMBEDDINGS_TEST = RUN_DIR / "embeddings_test_mejor.npz"
TEST_METRICS_JSON = RUN_DIR / "metricas_test.json"

KPI_RECALL1_MIN, KPI_RECALL1_EXC = 0.45, 0.65
KPI_RECALL5_MIN, KPI_RECALL5_EXC = 0.70, 0.85
KPI_SPARSITY_MIN, KPI_SPARSITY_EXC = 0.70, 0.85
KPI_MSE_SAE_MAX, KPI_MSE_SAE_EXC = 0.05, 0.02

def training_phase(epoch: int) -> int:
    if epoch <= PHASE1_END:
        return 1
    if epoch <= PHASE2_END:
        return 2
    return 3

device = "cuda" if torch.cuda.is_available() else "cpu"
print("device:", device, "| batch:", BATCH_SIZE, "| epochs:", NUM_EPOCHS)
print("Fases: 1 (0-%d) | 2 (%d-%d) | 3 (%d-%d)" % (
    PHASE1_END, PHASE1_END + 1, PHASE2_END, PHASE2_END + 1, NUM_EPOCHS - 1))
print("Metricas JSON:", METRICS_JSON)
if device == "cpu":
    print("AVISO: activa GPU en Colab (Runtime -> T4 GPU -> Reiniciar)")
'''

CELL8 = r'''# @title DataLoaders (augment + captions múltiples)
from transformers import AutoTokenizer

try:
    import lightning.pytorch as pl
except ImportError:
    import pytorch_lightning as pl

_CLASE_ETIQUETAS = {
    "contaminacion_alta_NO2": "contaminación alta de NO₂ troposférico",
    "contaminacion_alta_SO2": "contaminación alta de SO₂",
    "ozono_anomalo": "columna de ozono troposférico anómala",
    "vegetacion_densa": "vegetación densa y baja contaminación",
    "suelo_urbano": "cobertura urbana y suelo expuesto",
}

def build_caption_variants(row) -> list[str]:
    desc = str(row["descripcion"])
    clase = str(row.get("clase", ""))
    label = _CLASE_ETIQUETAS.get(clase, clase.replace("_", " "))
    ndvi = float(row.get("ndvi", 0) or 0)
    bsi = float(row.get("bsi", 0) or 0)
    variants = [
        desc,
        f"Imagen satelital Sentinel-2 sobre Cali: {label}.",
        f"Vista aérea centrada de la región con {label}.",
        f"Tile multispectral 64×64 en Cali, clase {label}, NDVI={ndvi:.2f}, BSI={bsi:.2f}.",
        f"Región metropolitana de Cali caracterizada por {label}.",
    ]
    return variants

def augment_tile(tile: torch.Tensor) -> torch.Tensor:
    if random.random() < 0.5:
        tile = torch.flip(tile, dims=(2,))
    k = random.randint(0, 3)
    if k:
        tile = torch.rot90(tile, k, dims=(1, 2))
    if random.random() < 0.3:
        tile = tile + torch.randn_like(tile) * BAND_JITTER_STD
    return tile

class Sit2TileDataset(Dataset):
    def __init__(
        self, frame, tiles_zarr, split, band_mean, band_std, tokenizer,
        max_length=256, augment=False, caption_variants=False,
    ):
        self.df = frame.reset_index(drop=True)
        mask = self.df["split"].values == split
        self._indices = np.nonzero(mask)[0].astype(np.int64)
        self.z = tiles_zarr
        self.mean = torch.as_tensor(band_mean, dtype=torch.float32).view(13, 1, 1)
        self.std = torch.as_tensor(band_std, dtype=torch.float32).view(13, 1, 1).clamp(min=1e-6)
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.augment = augment
        self.caption_variants = caption_variants
        self._caption_cache = {}
        if caption_variants:
            for i, r in self.df.iterrows():
                self._caption_cache[i] = build_caption_variants(r)

    def __len__(self):
        return int(len(self._indices))

    def _pick_text(self, j: int, row) -> str:
        if not self.caption_variants:
            return str(row["descripcion"])
        variants = self._caption_cache.get(j, [str(row["descripcion"])])
        return random.choice(variants) if self.augment else variants[0]

    def __getitem__(self, i):
        j = int(self._indices[i])
        row = self.df.iloc[j]
        tile = torch.from_numpy(np.asarray(self.z[j], dtype=np.float32))
        tile = (tile - self.mean) / self.std
        if self.augment:
            tile = augment_tile(tile)
        text = self._pick_text(j, row)
        tok = self.tokenizer(
            text, truncation=True, max_length=self.max_length,
            padding="max_length", return_tensors="pt",
        )
        return {
            "tile": tile,
            "input_ids": tok["input_ids"].squeeze(0),
            "attention_mask": tok["attention_mask"].squeeze(0),
            "tile_id": str(row["tile_id"]),
            "clase": str(row["clase"]),
            "row_idx": j,
        }

class Sit2PromptEnsembleDataset(Sit2TileDataset):
    """Test: varias captions por tile para ensemble en eval (SenCLIP)."""

    def __getitem__(self, i):
        j = int(self._indices[i])
        row = self.df.iloc[j]
        tile = torch.from_numpy(np.asarray(self.z[j], dtype=np.float32))
        tile = (tile - self.mean) / self.std
        variants = self._caption_cache.get(j, [str(row["descripcion"])])
        tok = self.tokenizer(
            variants[0], truncation=True, max_length=self.max_length,
            padding="max_length", return_tensors="pt",
        )
        return {
            "tile": tile,
            "input_ids": tok["input_ids"].squeeze(0),
            "attention_mask": tok["attention_mask"].squeeze(0),
            "tile_id": str(row["tile_id"]),
            "clase": str(row["clase"]),
            "caption_variants": variants,
        }

def collate_sit2(batch):
    return {
        "tile": torch.stack([b["tile"] for b in batch]),
        "input_ids": torch.stack([b["input_ids"] for b in batch]),
        "attention_mask": torch.stack([b["attention_mask"] for b in batch]),
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

band_mean, band_std = compute_band_stats(ZARR_PATH)
text_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
tokenizer = AutoTokenizer.from_pretrained(text_name)

ds_train = Sit2TileDataset(
    df, tiles_z, "train", band_mean, band_std, tokenizer,
    augment=AUGMENT_TRAIN, caption_variants=USE_CAPTION_VARIANTS,
)
ds_val = Sit2TileDataset(
    df, tiles_z, "val", band_mean, band_std, tokenizer,
    augment=False, caption_variants=False,
)
ds_test = Sit2TileDataset(
    df, tiles_z, "test", band_mean, band_std, tokenizer,
    augment=False, caption_variants=False,
)
ds_test_ensemble = Sit2PromptEnsembleDataset(
    df, tiles_z, "test", band_mean, band_std, tokenizer,
    augment=False, caption_variants=True,
)
ds_seq = Sit2SequenceDataset(df, tiles_z, secuencias, band_mean, band_std, tokenizer)
print(f"Train: {len(ds_train)} | Val: {len(ds_val)} | Test: {len(ds_test)} | Secuencias: {len(ds_seq)}")

train_loader = DataLoader(
    ds_train, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS,
    collate_fn=collate_sit2, pin_memory=torch.cuda.is_available(), drop_last=True,
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

CELL7_EXTRA = r'''

@torch.no_grad()
def recall_at_k_prompt_ensemble(model, loader, device, k=1):
    model.eval()
    img_parts, txt_parts = [], []
    for batch in loader:
        tiles = batch["tile"].to(device)
        vi = model.encode_image(tiles)
        img_parts.append(vi["e"].cpu())
        ids, masks = batch["input_ids"].to(device), batch["attention_mask"].to(device)
        vt = model.encode_text(ids, masks)
        txt_parts.append(vt["e"].cpu())
    if not img_parts:
        return 0.0
    return recall_at_k_image_to_text(torch.cat(img_parts, 0), torch.cat(txt_parts, 0), k)
'''

CELL13 = r'''# @title Guardar checkpoint final (mejor val/recall@1)
import hashlib

def _bundle_from_module(lit_module):
    return {
        "state_dict": lit_module.model.state_dict(),
        "band_mean": band_mean.tolist(),
        "band_std": band_std.tolist(),
        "hparams": {
            "num_epochs": NUM_EPOCHS,
            "phases": {"1_end": PHASE1_END, "2_end": PHASE2_END},
            "batch_size": BATCH_SIZE,
            "lr_head": LR_HEAD,
            "lr_text": LR_TEXT,
            "lr_visual": LR_VISUAL,
            "seed": SEED,
        },
        "best_checkpoint": str(ckpt_cb.best_model_path or ""),
        "test_metrics": json.loads(TEST_METRICS_JSON.read_text(encoding="utf-8"))
        if TEST_METRICS_JSON.exists() else {},
    }

ckpt_path = RUN_DIR / "checkpoint.pt"
src_lit = lit_best if "lit_best" in dir() else lit
torch.save(_bundle_from_module(src_lit), ckpt_path)
h = hashlib.md5(ckpt_path.read_bytes()).hexdigest()
(ckpt_path.with_suffix(".pt.md5")).write_text(h + "\n", encoding="utf-8")
print("Checkpoint:", ckpt_path, "| MD5:", h)
if ckpt_cb.best_model_path:
    print("Pesos alineados con:", ckpt_cb.best_model_path)
'''


def _src_to_nb_lines(src: str) -> list[str]:
    if not src.endswith("\n"):
        src += "\n"
    return [line if line.endswith("\n") else line + "\n" for line in src.splitlines(keepends=True)]


def main():
    nb = json.loads(NB_PATH.read_text(encoding="utf-8"))
    cells_dir = ROOT / "scripts" / "nb_cells"
    cell9 = (cells_dir / "cell9_model.py").read_text(encoding="utf-8")
    cell10 = (cells_dir / "cell10_train.py").read_text(encoding="utf-8")

    nb["cells"][6]["source"] = _src_to_nb_lines(CELL6)
    c7 = "".join(nb["cells"][7]["source"])
    if "recall_at_k_prompt_ensemble" not in c7:
        nb["cells"][7]["source"] = _src_to_nb_lines(c7.rstrip() + CELL7_EXTRA)
    nb["cells"][8]["source"] = _src_to_nb_lines(CELL8)
    nb["cells"][9]["source"] = _src_to_nb_lines(cell9)
    nb["cells"][10]["source"] = _src_to_nb_lines(cell10)
    nb["cells"][13]["source"] = _src_to_nb_lines(CELL13)

    md0 = "".join(nb["cells"][0]["source"])
    if "4 fases" not in md0:
        nb["cells"][0]["source"] = _src_to_nb_lines(
            md0.replace(
                "| Train | InfoNCE + SAE;",
                "| Train | **4 fases** (augment, captions, unfreeze ViT, test);",
            ).replace("40 épocas", "60 épocas (4 fases)")
        )

    NB_PATH.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Notebook actualizado:", NB_PATH)


if __name__ == "__main__":
    main()
