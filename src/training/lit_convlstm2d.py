import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset
try:
    import lightning.pytorch as pl
except ImportError:
    import pytorch_lightning as pl
from src.modelos.convlstm2d import ConvLSTM2D, masked_mse_loss


class Sit3ConvLSTMDataset(Dataset):
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


class LitConvLSTM2D(pl.LightningModule):
    'LightningModule para ConvLSTM2D (Situacion 3).'
    WEIGHTS_DEFAULT = [10000.0, 1000.0, 1.0]

    def __init__(self, model, lr=1e-4, weight_decay=1e-5, loss_weights=None):
        super().__init__()
        self.save_hyperparameters(ignore=["model"])
        self.model = model
        self.lr = lr
        self.weight_decay = weight_decay
        self.loss_weights = loss_weights or self.WEIGHTS_DEFAULT
        self._test_preds = []
        self._test_trues = []

    def forward(self, x):
        return self.model(x)

    def _loss(self, y_pred, y_true):
        w = torch.tensor(self.loss_weights, device=y_pred.device)
        return masked_mse_loss(y_pred, y_true, weights=w)

    def training_step(self, batch, batch_idx):
        y_pred = self.model(batch["x"])
        loss = self._loss(y_pred, batch["y"])
        self.log("train/loss", loss, on_step=True, on_epoch=True, prog_bar=True)
        return loss

    def validation_step(self, batch, batch_idx):
        y_pred = self.model(batch["x"])
        loss = self._loss(y_pred, batch["y"])
        self.log("val/loss", loss, on_epoch=True, prog_bar=True)
        self.log("val/rmse", loss.sqrt(), on_epoch=True, prog_bar=True)

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
        mask = ~np.isnan(all_trues)

        print()
        print("=" * 70)
        print("  TABLA RESUMEN - CONVLSTM (SIT. 3)")
        print("=" * 70)

        loss_val = float(masked_mse_loss(torch.from_numpy(all_preds), torch.from_numpy(all_trues)))
        rmse_val = float(np.sqrt(loss_val))
        print(f"  Loss global (MSE):       {loss_val:.6e}")
        print(f"  RMSE global (mol/m2):    {rmse_val:.6f}")
        print()

        # Tabla por contaminante
        h1 = f"  {'Contaminante':15s} {'RMSE mol/m2':14s} {'RMSE ug/m3':12s} {'KPI ug/m3':10s} {'Cumple':8s} {'R2':8s}"
        s1 = f"  {'-'*15} {'-'*14} {'-'*12} {'-'*10} {'-'*8} {'-'*8}"
        print(h1)
        print(s1)
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

        # Tabla por horizonte
        h2 = f"  {'Horizonte':10s} {'RMSE mol/m2':14s} {'R2':8s}"
        s2 = f"  {'-'*10} {'-'*14} {'-'*8}"
        print(h2)
        print(s2)
        for hi, hn in enumerate(HORIZONS):
            hmask = mask[:, hi, :]
            y_ph = all_preds[:, hi, :][hmask]
            y_th = all_trues[:, hi, :][hmask]
            if len(y_ph) > 0:
                rmse_h = float(np.sqrt(np.mean((y_ph - y_th) ** 2)))
                ss_res = float(np.sum((y_ph - y_th) ** 2))
                ss_tot = float(np.sum((y_th - np.mean(y_th)) ** 2))
                r2_h = 1.0 - ss_res / (ss_tot + 1e-12) if ss_tot > 0 else float("nan")
            else:
                rmse_h, r2_h = float("nan"), float("nan")
            print(f"  {hn:10s} {rmse_h:>8.2e}     {r2_h:>7.4f}")

        # Degradacion
        print()
        mask1 = mask[:, 0, :]
        mask7 = mask[:, 2, :]
        if mask1.sum() > 0 and mask7.sum() > 0:
            r1 = float(np.sqrt(np.mean((all_preds[:, 0, :][mask1] - all_trues[:, 0, :][mask1]) ** 2)))
            r7 = float(np.sqrt(np.mean((all_preds[:, 2, :][mask7] - all_trues[:, 2, :][mask7]) ** 2)))
            degradacion = (r7 / r1 - 1) * 100 if r1 > 0 else float("nan")
            cumple_degr = "SI" if degradacion < 60 else "NO"
            print(f"  Degradacion T+1 -> T+7: {degradacion:.1f}%  (KPI < 60% -> {cumple_degr})")
        else:
            print("  Degradacion T+1 -> T+7: N/A")

        # Desglose
        print()
        print("=" * 70)
        print("  DESGLOSE: Contaminante x Horizonte")
        print("=" * 70)
        for pi, pn in enumerate(POLLUTANTS):
            print()
            print(f"  {pn}:")
            h3 = f"  {'Horizonte':10s} {'RMSE mol/m2':14s} {'RMSE ug/m3':12s} {'R2':8s} {'N':6s}"
            s3 = f"  {'-'*10} {'-'*14} {'-'*12} {'-'*8} {'-'*6}"
            print(h3)
            print(s3)
            for hi, hn in enumerate(HORIZONS):
                m = mask[:, hi, pi]
                y_ph = all_preds[:, hi, pi][m]
                y_th = all_trues[:, hi, pi][m]
                n = len(y_ph)
                if n > 0:
                    rmse_ph = float(np.sqrt(np.mean((y_ph - y_th) ** 2)))
                    ug = float(rmse_ph * CONV_FACTOR.get(pn, 1.0))
                    ss_res = float(np.sum((y_ph - y_th) ** 2))
                    ss_tot = float(np.sum((y_th - np.mean(y_th)) ** 2))
                    r2_ph = 1.0 - ss_res / (ss_tot + 1e-12) if ss_tot > 0 else float("nan")
                else:
                    rmse_ph, ug, r2_ph = float("nan"), float("nan"), float("nan")
                print(f"  {hn:10s} {rmse_ph:>8.2e}     {ug:>7.2f} ug/m3  {r2_ph:>7.4f}  {n:5d}")

        print()
        print("=" * 70)
        self._test_preds.clear()
        self._test_trues.clear()

    def configure_optimizers(self):
        opt = torch.optim.AdamW(self.model.parameters(), lr=self.lr, weight_decay=self.weight_decay)
        sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode="min", factor=0.5, patience=10, min_lr=1e-7)
        return {"optimizer": opt, "lr_scheduler": {"scheduler": sched, "monitor": "val/loss"}}
