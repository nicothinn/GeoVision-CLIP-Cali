# @title Entrenamiento — utilidades compartidas (callbacks + trainer)
import json
import sys
from pytorch_lightning.loggers import WandbLogger
from pytorch_lightning.callbacks import (
    ModelCheckpoint, LearningRateMonitor, EarlyStopping, TQDMProgressBar,
)
try:
    from lightning.pytorch.utilities.rank_zero import rank_zero_info
except ImportError:
    from pytorch_lightning.utilities.rank_zero import rank_zero_info

PHASE1_MAX_EPOCH = PHASE1_END + 1
PHASE2_MAX_EPOCH = PHASE2_END + 1
PHASE3_MAX_EPOCH = NUM_EPOCHS

PHASE1_CKPT = RUN_DIR / "checkpoints" / "fase1_best.ckpt"
PHASE2_CKPT = RUN_DIR / "checkpoints" / "fase2_best.ckpt"
PHASE3_CKPT = RUN_DIR / "checkpoints" / "fase3_best.ckpt"


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


class MinEpochEarlyStopping(EarlyStopping):
    def on_validation_end(self, trainer, pl_module):
        if trainer.current_epoch < MIN_EPOCHS_BEFORE_EARLY_STOP:
            return
        super().on_validation_end(trainer, pl_module)


class EpochMetricsJsonCallback(pl.Callback):
    def __init__(self, json_path, embeddings_path, val_tile_ids):
        self.json_path = Path(json_path)
        self.embeddings_path = Path(embeddings_path)
        self.val_tile_ids = list(val_tile_ids)
        self._best_r1 = -1.0
        if self.json_path.exists():
            self.history = json.loads(self.json_path.read_text(encoding="utf-8"))
            best = self.history.get("best") or {}
            self._best_r1 = float(best.get("val/recall_at_1", -1.0))
        else:
            self.history = {
                "fases": {
                    "1": f"0-{PHASE1_END}",
                    "2": f"{PHASE1_END + 1}-{PHASE2_END}",
                    "3": f"{PHASE2_END + 1}-{NUM_EPOCHS - 1}",
                },
                "kpi_umbrales": {
                    "recall_at_1_min": KPI_RECALL1_MIN,
                    "recall_at_5_min": KPI_RECALL5_MIN,
                    "sparsity_min": KPI_SPARSITY_MIN,
                    "mse_sae_max": KPI_MSE_SAE_MAX,
                },
                "epochs": [],
                "best": None,
            }

    def _flush_json(self):
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        self.json_path.write_text(json.dumps(self.history, indent=2, ensure_ascii=False), encoding="utf-8")

    def on_train_epoch_end(self, trainer, pl_module):
        ep = int(trainer.current_epoch)
        phase = training_phase(ep)
        m = {k: _scalar(v) for k, v in trainer.callback_metrics.items() if not k.startswith("_")}
        row = {"epoch": ep, "phase": phase}
        for key in (
            "train/loss_epoch", "train/infonce", "train/alpha_sae", "train/sparsity_img",
            "val/loss", "val/infonce", "val/recall_at_1", "val/recall_at_5",
            "val/sparsity_img", "val/mse_sae_img",
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
                    phase=phase,
                )
        self._flush_json()
        lines = [
            "",
            "=" * 60,
            f"Época {ep:03d} | Fase {phase}",
            "=" * 60,
            f"  α_SAE = {getattr(pl_module.model, 'alpha_sae', '—')}",
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


def _copy_best_ckpt(ckpt_cb, dest: Path):
    src = ckpt_cb.best_model_path
    if not src:
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy2(src, dest)
    print("Checkpoint fase guardado:", dest)
    return str(dest)


def build_trainer(max_epochs: int, ckpt_filename: str):
    ckpt_cb = ModelCheckpoint(
        dirpath=str(RUN_DIR / "checkpoints"),
        filename=ckpt_filename,
        monitor="val/recall_at_1",
        mode="max",
        save_top_k=1,
    )
    early_cb = MinEpochEarlyStopping(
        monitor="val/recall_at_1", mode="max", patience=EARLY_STOP_PATIENCE, verbose=False,
    )
    loggers = [pl.loggers.CSVLogger(save_dir=str(RUN_DIR), name="metrics")]
    if USE_WANDB and os.environ.get("WANDB_API_KEY"):
        loggers.insert(0, WandbLogger(project=WANDB_PROJECT, name=WANDB_RUN_NAME, save_dir=str(RUN_DIR)))
    trainer = pl.Trainer(
        max_epochs=max_epochs,
        accelerator="gpu",
        devices=1,
        logger=loggers,
        callbacks=[ckpt_cb, early_cb, metrics_cb, TQDMProgressBar(refresh_rate=10), LearningRateMonitor(logging_interval="epoch")],
        default_root_dir=str(RUN_DIR),
        log_every_n_steps=10,
        val_check_interval=VAL_CHECK_INTERVAL,
        accumulate_grad_batches=GRAD_ACCUM_STEPS,
        enable_progress_bar=True,
        enable_model_summary=False,
    )
    return trainer, ckpt_cb


def load_lit(ckpt_path=None):
    if ckpt_path and Path(ckpt_path).exists():
        print("Cargando pesos desde:", ckpt_path)
        lit_m = LitGeoVisionClipSAE()
        raw = torch.load(str(ckpt_path), map_location="cpu")
        lit_m.load_state_dict(raw["state_dict"])
        return lit_m
    print("Modelo nuevo (sin checkpoint previo)")
    return LitGeoVisionClipSAE()


if not torch.cuda.is_available():
    raise RuntimeError("GPU no detectada. Colab: Runtime -> T4 GPU -> Reiniciar.")

val_tile_ids = df.loc[df["split"] == "val", "tile_id"].astype(str).tolist()
metrics_cb = EpochMetricsJsonCallback(METRICS_JSON, EMBEDDINGS_BEST, val_tile_ids)
print("Listo: metrics_cb, build_trainer(), load_lit()")
