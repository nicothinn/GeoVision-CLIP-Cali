"""LightningModule para entrenar ConvLSTM 1D + MLP (Situacion 3)."""

from __future__ import annotations

from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

try:
    import lightning.pytorch as pl
except ImportError:
    import pytorch_lightning as pl

from src.modelos.convlstm import ConvLSTM1DModel, masked_mse_loss


class Sit3ConvLSTMDataset(Dataset):
    """Dataset que carga X e y desde archivos .npy.

    Args:
        x_path: Ruta a X_convlstm.npy.
        y_path: Ruta a y_convlstm.npy.
        split: "train", "val", "test" o None para cargar todo.
        split_indices: Lista de indices para este split.
            Si es None, se usan todos los indices.
    """

    def __init__(
        self,
        x_path: str,
        y_path: str,
        split_indices: list[int] | None = None,
    ):
        import numpy as np

        self.X = np.load(x_path, mmap_mode="r")
        self.y = np.load(y_path, mmap_mode="r")

        if split_indices is not None:
            self.X = self.X[split_indices]
            self.y = self.y[split_indices]

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        x = torch.from_numpy(self.X[idx].copy()).float()
        y = torch.from_numpy(self.y[idx].copy()).float()
        return {"x": x, "y": y}


class LitConvLSTM(pl.LightningModule):
    """LightningModule para ConvLSTM 1D.

    Args:
        model: Instancia de ConvLSTM1DModel.
        lr: Learning rate (default: 1e-3).
        weight_decay: Weight decay (default: 1e-5).
    """

    WEIGHTS_DEFAULT = [100.0, 10.0, 1.0]  # NO2, SO2, O3

    def __init__(
        self,
        model: ConvLSTM1DModel,
        lr: float = 1e-3,
        weight_decay: float = 1e-5,
        loss_weights: list[float] | None = None,
    ):
        super().__init__()
        self.save_hyperparameters(ignore=["model"])

        self.model = model
        self.lr = lr
        self.weight_decay = weight_decay
        self.loss_weights = loss_weights or self.WEIGHTS_DEFAULT

        self._pollutants = ["NO2", "SO2", "O3"]
        self._horizons = ["T+1", "T+3", "T+7"]

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)

    def _compute_metrics(
        self, y_pred: torch.Tensor, y_true: torch.Tensor, prefix: str
    ) -> dict[str, torch.Tensor]:
        """Computa RMSE y R2 por contaminante y horizonte."""
        metrics = {}
        mask = ~torch.isnan(y_true)

        # Loss enmascarada global
        loss = masked_mse_loss(y_pred, y_true)
        metrics[f"{prefix}/loss"] = loss
        metrics[f"{prefix}/rmse"] = loss.sqrt()

        # RMSE por contaminante (promedio sobre horizontes)
        for p, pname in enumerate(self._pollutants):
            vals = y_pred[:, :, p]
            trues = y_true[:, :, p]
            m = ~torch.isnan(trues)
            if m.sum() > 0:
                rmse = F.mse_loss(vals[m], trues[m], reduction="mean").sqrt()
                metrics[f"{prefix}/rmse/{pname}"] = rmse

        # RMSE por horizonte (promedio sobre contaminantes)
        for h, hname in enumerate(self._horizons):
            vals = y_pred[:, h, :]
            trues = y_true[:, h, :]
            m = ~torch.isnan(trues)
            if m.sum() > 0:
                rmse = F.mse_loss(vals[m], trues[m], reduction="mean").sqrt()
                metrics[f"{prefix}/rmse/{hname}"] = rmse

        # R2 score global (sobre todos los valores validos)
        y_p = y_pred[mask]
        y_t = y_true[mask]
        if len(y_p) > 1:
            ss_res = F.mse_loss(y_p, y_t, reduction="sum")
            ss_tot = ((y_t - y_t.mean()) ** 2).sum()
            r2 = 1.0 - ss_res / (ss_tot + 1e-8)
            metrics[f"{prefix}/r2"] = r2

        return metrics

    def _loss(self, y_pred: torch.Tensor, y_true: torch.Tensor) -> torch.Tensor:
        w = torch.tensor(self.loss_weights, device=y_pred.device)
        return masked_mse_loss(y_pred, y_true, weights=w)

    def training_step(self, batch: dict[str, torch.Tensor], batch_idx: int) -> torch.Tensor:
        x, y = batch["x"], batch["y"]
        y_pred = self.model(x)
        loss = self._loss(y_pred, y)

        self.log("train/loss", loss, on_step=True, on_epoch=True, prog_bar=True)
        return loss

    def validation_step(self, batch: dict[str, torch.Tensor], batch_idx: int) -> None:
        x, y = batch["x"], batch["y"]
        y_pred = self.model(x)
        loss = self._loss(y_pred, y)
        self.log("val/loss", loss, on_epoch=True, prog_bar=True)
        self.log("val/rmse", loss.sqrt(), on_epoch=True, prog_bar=True)
        self._log_rmse_per_pollutant(y_pred, y, "val")

    def test_step(self, batch: dict[str, torch.Tensor], batch_idx: int) -> None:
        x, y = batch["x"], batch["y"]
        y_pred = self.model(x)
        loss = self._loss(y_pred, y)
        self.log("test/loss", loss, on_epoch=True)
        self.log("test/rmse", loss.sqrt(), on_epoch=True)
        self._log_rmse_per_pollutant(y_pred, y, "test")
        self._test_preds.append(y_pred.detach().cpu())
        self._test_trues.append(y.detach().cpu())

    def on_test_end(self) -> None:
        """Imprime tabla resumen con KPIs al finalizar test."""
        logs = {k: float(v) for k, v in self.trainer.logged_metrics.items() if "test/" in k}

        # Factores de conversion mol/m2 -> ug/m3 (altura trop. 8km)
        CONV = {"NO2": 5750.0, "SO2": 8008.0, "O3": 6000.0}
        KPIS = {
            "NO2": {"max": 8.0, "unit": "ug/m3"},
            "SO2": {"max": 6.0, "unit": "ug/m3"},
            "O3": {"max": 12.0, "unit": "ug/m3"},
        }

        print()
        print("=" * 70)
        print("  TABLA RESUMEN — CONVLSTM (SIT. 3)")
        print("=" * 70)

        # Loss global
        loss_val = logs.get("test/loss", 0)
        rmse_val = logs.get("test/rmse", 0)
        print(f"  Loss global (MSE):    {loss_val:.6e}")
        print(f"  RMSE global (mol/m2): {rmse_val:.6f}")
        print()

        # RMSE por contaminante
        print(f"  {'Contaminante':15s} {'RMSE mol/m2':15s} {'RMSE ug/m3':15s} {'KPI max':10s} {'Cumple':8s}")
        print(f"  {'-'*15} {'-'*15} {'-'*15} {'-'*10} {'-'*8}")
        for pname in ["NO2", "SO2", "O3"]:
            key = f"test/rmse/{pname}"
            rmse_p = logs.get(key, float("nan"))
            ugm3 = rmse_p * CONV.get(pname, 1.0)
            kpi_max = KPIS.get(pname, {}).get("max", float("inf"))
            cumple = "SI" if (not np.isnan(rmse_p) and ugm3 <= kpi_max) else "NO"
            print(f"  {pname:15s} {rmse_p:.6e}      {ugm3:8.2f} ug/m3     {kpi_max:6.1f}     {cumple:8s}")

        # RMSE por horizonte
        print()
        print(f"  {'Horizonte':10s} {'RMSE mol/m2':15s}")
        print(f"  {'-'*10} {'-'*15}")
        for hname in ["T+1", "T+3", "T+7"]:
            key = f"test/rmse/{hname}"
            rmse_h = logs.get(key, float("nan"))
            print(f"  {hname:10s} {rmse_h:.6e}")

        # R2
        r2_val = logs.get("test/r2", float("nan"))
        print()
        print(f"  R2 score: {r2_val:.4f}  {'(KPI >= 0.55)' if r2_val >= 0.55 else '(KPI NO cumplido)'}")

        print("=" * 70)

    def configure_optimizers(self) -> dict:
        optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.lr,
            weight_decay=self.weight_decay,
        )
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="min", factor=0.5, patience=10, min_lr=1e-7
        )
        return {
            "optimizer": optimizer,
            "lr_scheduler": {
                "scheduler": scheduler,
                "monitor": "val/loss",
                "frequency": 1,
            },
        }
