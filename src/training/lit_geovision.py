"""LightningModule para entrenar GeoVision-CLIP + SAE."""

from __future__ import annotations

from typing import Any

import torch
from torch.utils.data import DataLoader, Dataset

try:
    import lightning.pytorch as pl
except ImportError:  # pragma: no cover
    import pytorch_lightning as pl

from .clip_metrics import recall_at_k_image_to_text, sparsity_ratio
from .geovision_clip_sae import GeoVisionClipSAEModel


def _collate(batch: list[dict]) -> dict[str, torch.Tensor | list]:
    return {
        "tile": torch.stack([b["tile"] for b in batch], dim=0),
        "input_ids": torch.stack([b["input_ids"] for b in batch], dim=0),
        "attention_mask": torch.stack([b["attention_mask"] for b in batch], dim=0),
        "tile_id": [b["tile_id"] for b in batch],
        "clase": [b["clase"] for b in batch],
    }


class LitGeoVisionClipSAE(pl.LightningModule):
    def __init__(
        self,
        lr: float = 1e-4,
        weight_decay: float = 0.01,
        warmup_steps: int = 100,
        freeze_text_epochs: int = 1,
        **model_kwargs: Any,
    ) -> None:
        super().__init__()
        self.save_hyperparameters(ignore=[])
        self.model = GeoVisionClipSAEModel(
            **{k: v for k, v in model_kwargs.items()},
        )
        self.lr = lr
        self.weight_decay = weight_decay
        self.warmup_steps = warmup_steps
        self.freeze_text_epochs = freeze_text_epochs
        self._val_embeds_img: list[torch.Tensor] = []
        self._val_embeds_txt: list[torch.Tensor] = []

    def on_train_epoch_start(self) -> None:
        if self.current_epoch < self.freeze_text_epochs:
            self.model.set_text_trainable(False)
        else:
            self.model.set_text_trainable(True)

    def training_step(self, batch: dict[str, torch.Tensor], batch_idx: int) -> torch.Tensor:
        out = self.model(batch["tile"], batch["input_ids"], batch["attention_mask"])
        loss = out["loss"]
        self.log("train/loss", loss, prog_bar=True, on_step=True, on_epoch=True)
        self.log("train/infonce", out["loss_infonce"], on_step=False, on_epoch=True)
        self.log("train/sae_img", out["loss_sae_img"], on_step=False, on_epoch=True)
        self.log("train/sae_txt", out["loss_sae_txt"], on_step=False, on_epoch=True)
        sp_i = sparsity_ratio(out["z_img"])
        sp_t = sparsity_ratio(out["z_txt"])
        self.log("train/sparsity_img", sp_i, on_step=False, on_epoch=True)
        self.log("train/sparsity_txt", sp_t, on_step=False, on_epoch=True)
        return loss

    def validation_step(self, batch: dict[str, torch.Tensor], batch_idx: int) -> None:
        out = self.model(batch["tile"], batch["input_ids"], batch["attention_mask"])
        self.log("val/loss", out["loss"], prog_bar=True, on_epoch=True)
        self.log("val/infonce", out["loss_infonce"], on_epoch=True)
        self.log("val/mse_img", out["mse_sae_img"], on_epoch=True)
        self.log("val/mse_txt", out["mse_sae_txt"], on_epoch=True)
        self._val_embeds_img.append(out["e_img"].detach().cpu())
        self._val_embeds_txt.append(out["e_txt"].detach().cpu())

    def on_validation_epoch_start(self) -> None:
        self._val_embeds_img.clear()
        self._val_embeds_txt.clear()

    def on_validation_epoch_end(self) -> None:
        if not self._val_embeds_img:
            return
        img = torch.cat(self._val_embeds_img, dim=0).to(self.device)
        txt = torch.cat(self._val_embeds_txt, dim=0).to(self.device)
        r1 = recall_at_k_image_to_text(img, txt, k=1)
        r5 = recall_at_k_image_to_text(img, txt, k=5)
        self.log("val/recall_at_1", r1, prog_bar=True, on_epoch=True)
        self.log("val/recall_at_5", r5, prog_bar=True, on_epoch=True)

    def configure_optimizers(self):
        opt = torch.optim.AdamW(self.model.parameters(), lr=self.lr, weight_decay=self.weight_decay)
        return opt
