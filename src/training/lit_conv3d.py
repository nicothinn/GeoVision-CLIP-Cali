import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset
try:
    import lightning.pytorch as pl
except ImportError:
    import pytorch_lightning as pl
from src.modelos.conv3d_sit3 import Conv3DSit3


class Sit3Conv3DDataset(Dataset):
    'Dataset que carga X e y desde archivos .npy.'
    def __init__(self, x_path, y_path, split_indices=None):
        self.X = np.load(x_path, mmap_mode="r")
        self.y = np.load(y_path, mmap_mode="r")
        if split_indices is not None:
            self.X = self.X[split_indices]
            self.y = self.y[split_indices]

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        x = torch.from_numpy(self.X[idx].copy()).float()
        y = torch.from_numpy(self.y[idx].copy()).float()
        return {"x": x, "y": y}


POLLUTANTS = ["NO2", "SO2", "O3"]
HORIZONS = ["T+1", "T+3", "T+7"]
CONV_FACTOR = {"NO2": 5750.0, "SO2": 8008.0, "O3": 6000.0}
KPI_UGM3 = {"NO2": 8.0, "SO2": 6.0, "O3": 12.0}


class LitConv3D(pl.LightningModule):
    'LightningModule para Conv3DSit3 (Situacion 3).'
    WEIGHTS_DEFAULT = [1.0, 1.0, 1.0]

    def __init__(self, model, lr=1e-4, weight_decay=1e-5, loss_weights=None,
                 y_mean=None, y_std=None):
        super().__init__()
        self.save_hyperparameters(ignore=["model"])
        self.model = model
        self.lr = lr
        self.weight_decay = weight_decay
        self.loss_weights = loss_weights or self.WEIGHTS_DEFAULT
        self.y_mean = y_mean
        self.y_std = y_std
        self._test_preds = []
        self._test_trues = []

    def forward(self, x):
        return self.model(x)

    def _loss(self, y_pred, y_true):
        'MSE enmascarada con pesos por contaminante.'
        w = torch.tensor(self.loss_weights, device=y_pred.device)
        mask = ~torch.isnan(y_true)
        loss_p = torch.zeros(3, device=y_pred.device)
        for p in range(3):
            pmask = mask[:, :, p]
            if pmask.sum() > 0:
                loss_p[p] = F.mse_loss(y_pred[:, :, p][pmask], y_true[:, :, p][pmask], reduction="mean")
        return (loss_p * w).sum() / w.sum()

    def training_step(self, batch, batch_idx):
        y_pred = self.model(batch["x"])
        loss = self._loss(y_pred, batch["y"])
        self.log("train/loss", loss, on_step=True, on_epoch=True, prog_bar=True)
        return loss

    def validation_step(self, batch, batch_idx):
        y_pred = self.model(batch["x"])
        loss = self._loss(y_pred, batch["y"])
        self.log("val/loss", loss, on_epoch=True, prog_bar=True)

    def test_step(self, batch, batch_idx):
        y_pred = self.model(batch["x"])
        y_true = batch["y"]
        self.log("test/loss", self._loss(y_pred, y_true), on_epoch=True)
        self._test_preds.append(y_pred.detach().cpu())
        self._test_trues.append(y_true.detach().cpu())

    def on_test_end(self):
        'Imprime tabla de metricas completa al final del test.'
        all_preds = torch.cat(self._test_preds, dim=0).numpy()
        all_trues = torch.cat(self._test_trues, dim=0).numpy()
        # Denormalizar si stats disponibles
        if self.y_mean is not None and self.y_std is not None:
            ym = np.array(self.y_mean).reshape(1, 1, 3)
            ys = np.array(self.y_std).reshape(1, 1, 3)
            all_preds = all_preds * ys + ym
            all_trues = all_trues * ys + ym
        mask = ~np.isnan(all_trues)

        print()
        print("=" * 70)
        print("  TABLA RESUMEN - Conv3D (SIT. 3)")
        print("=" * 70)

        # --- Global ---
        loss_val = float(np.nanmean((all_preds - all_trues) ** 2))
        rmse_val = float(np.sqrt(loss_val))
        print(f"  MSE global:              {loss_val:.6e}")
        print(f"  RMSE global (mol/m2):    {rmse_val:.6f}")
        print()

        # --- Por contaminante ---
        print(f"  {'Contaminante':15s} {'RMSE mol/m2':14s} {'RMSE ug/m3':12s} {'KPI ug/m3':10s} {'Cumple':8s} {'R2':8s}")
        print(f"  {'-'*15} {'-'*14} {'-'*12} {'-'*10} {'-'*8} {'-'*8}")
        for pi, pn in enumerate(POLLUTANTS):
            pmask = mask[:, :, pi]
            y_p = all_preds[:, :, pi][pmask]
            y_t = all_trues[:, :, pi][pmask]
            if len(y_p) > 0:
                rmse_p = float(np.sqrt(np.mean((y_p - y_t) ** 2)))
                ug = rmse_p * CONV_FACTOR.get(pn, 1.0)
                ss_res = float(np.sum((y_p - y_t) ** 2))
                ss_tot = float(np.sum((y_t - np.mean(y_t)) ** 2))
                r2 = 1.0 - ss_res / (ss_tot + 1e-12) if ss_tot > 0 else float("nan")
                kpi = KPI_UGM3.get(pn, float("inf"))
                cumple = "SI" if ug <= kpi else "NO"
            else:
                rmse_p, ug, r2, cumple = float("nan"), float("nan"), float("nan"), "N/A"
            print(f"  {pn:15s} {rmse_p:>8.2e}     {ug:>7.2f} ug/m3  {kpi:>6.1f}     {cumple:8s}  {r2:>7.4f}")

        print()

        # --- Por horizonte (CADA contaminante por separado) ---
        print("  R2 por horizonte y contaminante:")
        print(f"  {'Horizonte':10s} {'NO2 R2':8s} {'SO2 R2':8s} {'O3 R2':8s}")
        print(f"  {'-'*10} {'-'*8} {'-'*8} {'-'*8}")
        for hi, hn in enumerate(HORIZONS):
            r2s = []
            for pi in range(3):
                m = mask[:, hi, pi]
                y_ph = all_preds[:, hi, pi][m]
                y_th = all_trues[:, hi, pi][m]
                if len(y_ph) > 0:
                    ss_res = float(np.sum((y_ph - y_th) ** 2))
                    ss_tot = float(np.sum((y_th - np.mean(y_th)) ** 2))
                    r2_h = 1.0 - ss_res / (ss_tot + 1e-12) if ss_tot > 0 else float("nan")
                else:
                    r2_h = float("nan")
                r2s.append(r2_h)
            print(f"  {hn:10s} {r2s[0]:>7.4f}  {r2s[1]:>7.4f}  {r2s[2]:>7.4f}")

        # --- Degradacion por contaminante ---
        print()
        print("  Degradacion T+1 -> T+7 por contaminante:")
        for pi, pn in enumerate(POLLUTANTS):
            m1 = mask[:, 0, pi]
            m7 = mask[:, 2, pi]
            if m1.sum() > 0 and m7.sum() > 0:
                r1 = float(np.sqrt(np.mean((all_preds[:, 0, pi][m1] - all_trues[:, 0, pi][m1]) ** 2)))
                r7 = float(np.sqrt(np.mean((all_preds[:, 2, pi][m7] - all_trues[:, 2, pi][m7]) ** 2)))
                degradacion = (r7 / r1 - 1) * 100 if r1 > 0 else float("nan")
            else:
                degradacion = float("nan")
            print(f"    {pn:4s}: {degradacion:.1f}%" if not np.isnan(degradacion) else f"    {pn:4s}: N/A")

        print()
        print("=" * 70)
        self._test_preds.clear()
        self._test_trues.clear()

    def configure_optimizers(self):
        opt = torch.optim.AdamW(self.model.parameters(), lr=self.lr, weight_decay=self.weight_decay)
        sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode="min", factor=0.5, patience=10, min_lr=1e-7)
        return {"optimizer": opt, "lr_scheduler": {"scheduler": sched, "monitor": "val/loss"}}
