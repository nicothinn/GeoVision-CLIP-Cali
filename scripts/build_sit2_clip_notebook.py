"""Genera notebooks/sit2_geovision_clip_entrenamiento.ipynb con toda la logica inline."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks" / "sit2_geovision_clip_entrenamiento.ipynb"

MD1 = r"""# GeoVision-CLIP + SAE (Sit. 2) — entrenamiento

**Todo el codigo de entrenamiento vive en este notebook** (sin depender de `src/`).

- **RemoteCLIP** (ViT-B/32): inicio visual en teledeteccion.
- **SenCLIP**: gap dominio natural vs Sentinel-2 y prompts en español.
- **TimeSenCLIP**: referencia para series temporales; aqui usamos **tiles estaticos** (no bloquea este entrenamiento).
- **Estimating NO2**: contexto de pseudo-etiquetas por columna troposferica.

**No incluye** validacion psicometrica de embeddings (AFE/AFC sobre `z`/`e`); eso sera otro notebook.

Perdidas: \(L = L_{InfoNCE} + 0.1 \cdot (L_{SAE,img} + L_{SAE,txt})\), SAE con MSE + \(10^{-3}\|z\|_1\), temperatura learnable init 0.07.
"""

C_SETUP = r"""from pathlib import Path
import os
import sys

# Raiz del repositorio (padre de notebooks/)
REPO_ROOT = Path.cwd()
if not (REPO_ROOT / "pipeline").is_dir():
    REPO_ROOT = Path.cwd().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# --- Configuracion ---
SEED = 42
DATA_SOURCE = "local"  # "local" | "gcs"

# Local (por defecto)
META_PARQUET = REPO_ROOT / "dataset_sit2" / "metadatos.parquet"
ZARR_TILES = REPO_ROOT / "dataset_sit2" / "tiles.zarr"

# GCS (si DATA_SOURCE == "gcs"): ajusta prefijo si subiste el dataset con otro path
GCS_META = "gs://geovision-cali/datasets/sit2/metadatos.parquet"
GCS_ZARR = "gs://geovision-cali/datasets/sit2/tiles.zarr"

# Entrenamiento
BATCH_SIZE = 8
NUM_EPOCHS = 5
LR = 1e-4
WEIGHT_DECAY = 0.01
FREEZE_TEXT_EPOCHS = 1
NUM_WORKERS = 0  # Windows: 0 suele ser mas estable

# Salidas
RUN_DIR = REPO_ROOT / "runs" / "sit2_clip_notebook"
RUN_DIR.mkdir(parents=True, exist_ok=True)

import random
import numpy as np
import torch

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

print("REPO_ROOT:", REPO_ROOT)
print("DATA_SOURCE:", DATA_SOURCE)
"""

C_IMPORTS = r"""import math
from typing import Any, Literal

import matplotlib.pyplot as plt
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import zarr
from torch.utils.data import DataLoader, Dataset

try:
    import lightning.pytorch as pl
except ImportError:
    import pytorch_lightning as pl

import open_clip
from transformers import AutoModel, AutoTokenizer
"""

C_METRICS_SAE = r"""# --- Metricas (Recall@k, sparsidad) y SAE ---

@torch.no_grad()
def recall_at_k_image_to_text(
    image_embeds: torch.Tensor,
    text_embeds: torch.Tensor,
    k: int,
) -> float:
    image_embeds = F.normalize(image_embeds, dim=-1)
    text_embeds = F.normalize(text_embeds, dim=-1)
    sim = image_embeds @ text_embeds.T
    n = sim.shape[0]
    labels = torch.arange(n, device=sim.device)
    kk = min(k, sim.shape[1])
    topk = sim.topk(kk, dim=1).indices
    return float((topk == labels.unsqueeze(1)).any(dim=1).float().mean().item())


@torch.no_grad()
def sparsity_ratio(z: torch.Tensor, threshold: float = 0.01) -> float:
    return float((z.abs() < threshold).float().mean().item())


class SparseAutoencoder(nn.Module):
    def __init__(self, dim_in: int, dim_latent: int = 512) -> None:
        super().__init__()
        self.encoder = nn.Linear(dim_in, dim_latent)
        self.decoder = nn.Linear(dim_latent, dim_in)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        z = self.encoder(x)
        return self.decoder(z), z


def sae_loss(x, x_hat, z, lambda_l1: float = 1e-3):
    mse = F.mse_loss(x_hat, x)
    l1 = z.abs().mean()
    return mse + lambda_l1 * l1, mse, l1
"""

C_DATASET = r"""# --- Dataset Sit2 (parquet + zarr alineados por fila) ---

SplitName = Literal["train", "val", "test"]


def open_tiles_zarr(zarr_path):
    path = str(zarr_path)
    if path.startswith("gs://"):
        import gcsfs
        fs = gcsfs.GCSFileSystem()
        store = fs.get_mapper(path.rstrip("/"))
        root = zarr.open(store, mode="r")
    else:
        root = zarr.open(path, mode="r")
    if isinstance(root, zarr.Array):
        return root
    if isinstance(root, zarr.hierarchy.Group):
        if "tiles" in root:
            return root["tiles"]
        for _, arr in root.arrays():
            return arr
    raise ValueError(zarr_path)


def compute_band_stats(zarr_path, n_sample=512, seed=42):
    rng = np.random.default_rng(seed)
    arr = open_tiles_zarr(zarr_path)
    n = int(arr.shape[0])
    idx = rng.choice(n, size=min(n_sample, n), replace=False)
    sample = np.stack([np.asarray(arr[i], dtype=np.float32) for i in idx], axis=0)
    mean = sample.mean(axis=(0, 2, 3))
    std = np.maximum(sample.std(axis=(0, 2, 3)), 1e-3)
    return mean.astype("float32"), std.astype("float32")


class Sit2TileDataset(Dataset):
    def __init__(self, df, tiles_z, split: SplitName, band_mean, band_std, tokenizer, max_length=256):
        self.df = df.reset_index(drop=True)
        mask = self.df["split"].values == split
        self._indices = np.nonzero(mask)[0].astype(np.int64)
        self.z = tiles_z
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
            str(row["descripcion"]),
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )
        return {
            "tile": tile,
            "input_ids": tok["input_ids"].squeeze(0),
            "attention_mask": tok["attention_mask"].squeeze(0),
        }


def collate_sit2(batch):
    return {
        "tile": torch.stack([b["tile"] for b in batch]),
        "input_ids": torch.stack([b["input_ids"] for b in batch]),
        "attention_mask": torch.stack([b["attention_mask"] for b in batch]),
    }
"""

C_MODEL = r"""# --- Modelo GeoVision-CLIP + SAE (consigna) ---

_CLIP_MEAN = (0.48145466, 0.4578275, 0.40821073)
_CLIP_STD = (0.26862954, 0.26130258, 0.27577711)


def load_openclip_visual(model_name="ViT-B-32", pretrained="hf-hub:chendong/RemoteCLIP-ViT-B-32"):
    tags = [pretrained, "hf-hub:chendong/RemoteCLIP-ViT-B-32"]
    errs = []
    for tag in dict.fromkeys(tags):
        try:
            m, _, _ = open_clip.create_model_and_transforms(model_name, pretrained=tag)
            print(f"RemoteCLIP cargado: {tag!r}")
            return m.visual, tag
        except Exception as e:
            errs.append(f"{tag}: {e}")
    raise RuntimeError("RemoteCLIP no disponible. Sin fallback LAION.\\n" + "\\n".join(errs))


class GeoVisionClipSAEModel(nn.Module):
    def __init__(
        self,
        text_model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        dim_latent_sae=512,
        dim_contrastive=256,
        alpha_sae=0.1,
        lambda_l1=1e-3,
        openclip_name="ViT-B-32",
        openclip_pretrained="remoteclip",
    ):
        super().__init__()
        self.alpha_sae = alpha_sae
        self.lambda_l1 = lambda_l1
        self.ms_adapter = nn.Conv2d(13, 3, 1, bias=True)
        self.visual, _tag = load_openclip_visual(openclip_name, openclip_pretrained)
        dim_img = int(getattr(self.visual, "output_dim", 512))
        self.tokenizer = AutoTokenizer.from_pretrained(text_model_name)
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
        if tiles.dtype != torch.float32:
            tiles = tiles.float()
        x3 = self.ms_adapter(tiles)
        x3 = F.interpolate(x3, (224, 224), mode="bicubic", align_corners=False)
        x3 = (x3 - self.clip_mean) / self.clip_std
        h = self.visual(x3)
        h_hat, z = self.sae_img(h)
        e = self.proj_img(z)
        return {"h": h, "z": z, "h_hat": h_hat, "e": e}

    def encode_text(self, input_ids, attention_mask):
        out = self.text_encoder(input_ids=input_ids, attention_mask=attention_mask)
        last = out.last_hidden_state
        m = attention_mask.unsqueeze(-1).float()
        pooled = (last * m).sum(1) / m.sum(1).clamp(min=1e-6)
        h = self.text_to_sae(pooled)
        h_hat, z = self.sae_txt(h)
        e = self.proj_txt(z)
        return {"h": h, "z": z, "h_hat": h_hat, "e": e}

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
        l_sae = li + lt
        total = l_infonce + self.alpha_sae * l_sae
        return {
            "loss": total,
            "loss_infonce": l_infonce.detach(),
            "loss_sae_img": li.detach(),
            "loss_sae_txt": lt.detach(),
            "mse_sae_img": msei.detach(),
            "mse_sae_txt": mset.detach(),
            "e_img": vi["e"],
            "e_txt": vt["e"],
            "z_img": vi["z"],
            "z_txt": vt["z"],
        }

    def set_text_trainable(self, trainable: bool):
        for p in self.text_encoder.parameters():
            p.requires_grad = trainable
        for p in self.text_to_sae.parameters():
            p.requires_grad = trainable


class LitGeoVisionClipSAE(pl.LightningModule):
    def __init__(self, lr=1e-4, weight_decay=0.01, freeze_text_epochs=1, **model_kw):
        super().__init__()
        self.save_hyperparameters(ignore=[])
        self.model = GeoVisionClipSAEModel(**model_kw)
        self.lr = lr
        self.weight_decay = weight_decay
        self.freeze_text_epochs = freeze_text_epochs
        self._val_img, self._val_txt = [], []

    def on_train_epoch_start(self):
        self.model.set_text_trainable(self.current_epoch >= self.freeze_text_epochs)

    def training_step(self, batch, batch_idx):
        o = self.model(batch["tile"], batch["input_ids"], batch["attention_mask"])
        self.log("train/loss", o["loss"], prog_bar=True, on_step=True, on_epoch=True)
        self.log("train/infonce", o["loss_infonce"], on_epoch=True)
        self.log("train/sparsity_img", sparsity_ratio(o["z_img"]), on_epoch=True)
        self.log("train/sparsity_txt", sparsity_ratio(o["z_txt"]), on_epoch=True)
        return o["loss"]

    def validation_step(self, batch, batch_idx):
        o = self.model(batch["tile"], batch["input_ids"], batch["attention_mask"])
        self.log("val/loss", o["loss"], on_epoch=True)
        self.log("val/infonce", o["loss_infonce"], on_epoch=True)
        self.log("val/mse_img", o["mse_sae_img"], on_epoch=True)
        self.log("val/mse_txt", o["mse_sae_txt"], on_epoch=True)
        self._val_img.append(o["e_img"].detach().cpu())
        self._val_txt.append(o["e_txt"].detach().cpu())

    def on_validation_epoch_start(self):
        self._val_img.clear()
        self._val_txt.clear()

    def on_validation_epoch_end(self):
        if not self._val_img:
            return
        img = torch.cat(self._val_img, 0).to(self.device)
        txt = torch.cat(self._val_txt, 0).to(self.device)
        self.log("val/recall_at_1", recall_at_k_image_to_text(img, txt, 1), prog_bar=True, on_epoch=True)
        self.log("val/recall_at_5", recall_at_k_image_to_text(img, txt, 5), prog_bar=True, on_epoch=True)

    def configure_optimizers(self):
        return torch.optim.AdamW(self.model.parameters(), lr=self.lr, weight_decay=self.weight_decay)
"""

C_TRAIN = r"""# --- Cargar datos, DataLoaders, entrenar ---

if DATA_SOURCE == "gcs":
    meta_path, zarr_path = GCS_META, GCS_ZARR
else:
    meta_path, zarr_path = str(META_PARQUET), str(ZARR_TILES)

df = pd.read_parquet(meta_path)
tiles_z = open_tiles_zarr(zarr_path)
mean, std = compute_band_stats(zarr_path, n_sample=min(512, tiles_z.shape[0]))

text_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
tokenizer = AutoTokenizer.from_pretrained(text_name)

ds_train = Sit2TileDataset(df, tiles_z, "train", mean, std, tokenizer)
ds_val = Sit2TileDataset(df, tiles_z, "val", mean, std, tokenizer)

train_loader = DataLoader(
    ds_train, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS, collate_fn=collate_sit2, pin_memory=True
)
val_loader = DataLoader(
    ds_val, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS, collate_fn=collate_sit2, pin_memory=True
)

lit = LitGeoVisionClipSAE(lr=LR, weight_decay=WEIGHT_DECAY, freeze_text_epochs=FREEZE_TEXT_EPOCHS)

logger = pl.loggers.CSVLogger(save_dir=str(RUN_DIR), name="metrics")
trainer = pl.Trainer(
    max_epochs=NUM_EPOCHS,
    default_root_dir=str(RUN_DIR),
    logger=logger,
    accelerator="gpu" if torch.cuda.is_available() else "cpu",
    devices=1,
    enable_checkpointing=True,
)
trainer.fit(lit, train_loader, val_loader)
print("Metricas CSV en:", Path(logger.log_dir) / "metrics.csv")
"""

C_SAVE = r"""# --- Curvas rapidas, checkpoint + MD5 (subida GCS opcional) ---

import hashlib
import json

log_root = RUN_DIR / "metrics"
csvs = sorted(log_root.glob("**/metrics.csv"))
if not csvs:
    raise FileNotFoundError("No se encontro metrics.csv bajo " + str(log_root))
log_csv = csvs[-1]
print("Leyendo:", log_csv)
metrics_df = pd.read_csv(log_csv)
print("Columnas:", list(metrics_df.columns))

fig, ax = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
loss_cols = [c for c in metrics_df.columns if "loss" in c.lower() and "epoch" not in c.lower()]
if "epoch" in metrics_df.columns:
    for c in loss_cols[:4]:
        ax[0].plot(metrics_df["epoch"], metrics_df[c], label=c)
    ax[0].legend(fontsize=7)
ax[0].set_ylabel("Loss")
inf_cols = [c for c in metrics_df.columns if "infonce" in c.lower() and "epoch" not in c.lower()]
if "epoch" in metrics_df.columns:
    for c in inf_cols[:4]:
        ax[1].plot(metrics_df["epoch"], metrics_df[c], label=c)
    ax[1].legend(fontsize=7)
ax[1].set_xlabel("epoch")
plt.tight_layout()
plt.savefig(RUN_DIR / "curvas_loss.png", dpi=120)
plt.show()

ckpt_path = RUN_DIR / "checkpoint.pt"
bundle = {
    "state_dict": lit.model.state_dict(),
    "hparams": dict(lr=LR, batch_size=BATCH_SIZE, epochs=NUM_EPOCHS, seed=SEED),
    "epoch": int(trainer.current_epoch),
}
torch.save(bundle, ckpt_path)
h = hashlib.md5()
with open(ckpt_path, "rb") as f:
    for chunk in iter(lambda: f.read(1024 * 1024), b""):
        h.update(chunk)
md5_hex = h.hexdigest()
(ckpt_path.with_suffix(".pt.md5")).write_text(md5_hex + "\n", encoding="utf-8")
print("Checkpoint:", ckpt_path)
print("MD5:", md5_hex)

# Opcional: subir RUN_DIR a GCS (descomenta y ajusta prefijo)
# from google.cloud import storage
# client = storage.Client(project="proyecto3ia-494900")
# bucket = client.bucket("geovision-cali")
# prefix = "experiments/sit2_clip_notebook/20260101/"
# for p in RUN_DIR.rglob("*"):
#     if p.is_file():
#         blob = bucket.blob(prefix + p.relative_to(RUN_DIR).as_posix())
#         blob.upload_from_filename(str(p))

meta = {"md5_checkpoint": md5_hex, "run_dir": str(RUN_DIR), "log_csv": str(log_csv)}
(RUN_DIR / "resumen_run.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
print("Listo.")
"""


def cell(source: str, markdown: bool = False):
    src = source if isinstance(source, list) else source.splitlines(keepends=True)
    if not markdown and src and not src[-1].endswith("\n"):
        src[-1] += "\n"
    out = {
        "cell_type": "markdown" if markdown else "code",
        "metadata": {},
        "source": src,
    }
    if not markdown:
        out["outputs"] = []
        out["execution_count"] = None
    return out


nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
    },
    "cells": [
        cell(MD1, markdown=True),
        cell(C_SETUP),
        cell(C_IMPORTS),
        cell(C_METRICS_SAE),
        cell(C_DATASET),
        cell(C_MODEL),
        cell(C_TRAIN),
        cell(C_SAVE),
    ],
}

NB.parent.mkdir(parents=True, exist_ok=True)
NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("Wrote", NB)
