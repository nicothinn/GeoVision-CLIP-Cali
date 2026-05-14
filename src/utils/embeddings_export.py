"""Exportar embeddings a disco (parquet liviano con columnas numéricas por dim)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader


@torch.no_grad()
def export_split_embeddings(
    model: torch.nn.Module,
    loader: DataLoader,
    device: torch.device,
    out_parquet: Path,
    max_rows: int | None = None,
) -> int:
    """Guarda `tile_id`, `clase`, y componentes de e_img / e_txt (256+256 columnas)."""
    from src.modelos.geovision_clip_sae import GeoVisionClipSAEModel

    if not isinstance(model, GeoVisionClipSAEModel):
        raise TypeError("model debe ser GeoVisionClipSAEModel")
    rows: list[dict] = []
    n = 0
    for batch in loader:
        tiles = batch["tile"].to(device)
        ids = batch["input_ids"].to(device)
        mask = batch["attention_mask"].to(device)
        vi = model.encode_image(tiles)
        vt = model.encode_text(ids, mask)
        e_img = F.normalize(vi["e"], dim=-1).cpu().numpy()
        e_txt = F.normalize(vt["e"], dim=-1).cpu().numpy()
        z_img = vi["z"].cpu().numpy()
        z_txt = vt["z"].cpu().numpy()
        b = e_img.shape[0]
        for i in range(b):
            d: dict = {
                "tile_id": batch["tile_id"][i],
                "clase": batch["clase"][i],
            }
            for j in range(e_img.shape[1]):
                d[f"e_img_{j}"] = float(e_img[i, j])
            for j in range(e_txt.shape[1]):
                d[f"e_txt_{j}"] = float(e_txt[i, j])
            for j in range(z_img.shape[1]):
                d[f"z_img_{j}"] = float(z_img[i, j])
            for j in range(z_txt.shape[1]):
                d[f"z_txt_{j}"] = float(z_txt[i, j])
            rows.append(d)
            n += 1
            if max_rows is not None and n >= max_rows:
                break
        if max_rows is not None and n >= max_rows:
            break
    out_parquet = Path(out_parquet)
    out_parquet.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(out_parquet, index=False)
    return len(rows)
