# @title Entrenamiento por fases + eval test (Fase 4)
import json
import sys
from pytorch_lightning.loggers import WandbLogger
from pytorch_lightning.callbacks import (
    ModelCheckpoint, LearningRateMonitor, EarlyStopping, TQDMProgressBar, Callback,
)
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


class MinEpochEarlyStopping(EarlyStopping):
    """Early stopping solo después de MIN_EPOCHS_BEFORE_EARLY_STOP."""

    def on_validation_end(self, trainer, pl_module):
        if trainer.current_epoch < MIN_EPOCHS_BEFORE_EARLY_STOP:
            return
        super().on_validation_end(trainer, pl_module)


class EpochMetricsJsonCallback(pl.Callback):
    def __init__(self, json_path, embeddings_path, val_tile_ids):
        self.json_path = Path(json_path)
        self.embeddings_path = Path(embeddings_path)
        self.val_tile_ids = list(val_tile_ids)
        self.history = {
            "fases": {"1": f"0-{PHASE1_END}", "2": f"{PHASE1_END+1}-{PHASE2_END}", "3": f"{PHASE2_END+1}-{NUM_EPOCHS-1}"},
            "kpi_umbrales": {
                "recall_at_1_min": KPI_RECALL1_MIN,
                "recall_at_5_min": KPI_RECALL5_MIN,
                "sparsity_min": KPI_SPARSITY_MIN,
                "mse_sae_max": KPI_MSE_SAE_MAX,
            },
            "epochs": [],
            "best": None,
        }
        self._best_r1 = -1.0

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
            f"  α_SAE           = {getattr(pl_module.model, 'alpha_sae', '—')}",
            f"  train/loss      = {row.get('train/loss_epoch', '—')}",
            f"  val/loss        = {row.get('val/loss', '—')}",
            f"  val/recall@1    = {r1}  [{_kpi_flag(r1, min_ok=KPI_RECALL1_MIN, exc=KPI_RECALL1_EXC)}]",
            f"  val/recall@5    = {r5}  [{_kpi_flag(r5, min_ok=KPI_RECALL5_MIN, exc=KPI_RECALL5_EXC)}]",
            f"  val/sparsity    = {sp}  [{_kpi_flag(sp, min_ok=KPI_SPARSITY_MIN)}]",
            f"  val/mse_sae_img = {mse}  [{_kpi_flag(mse, max_ok=KPI_MSE_SAE_MAX)}]",
        ]
        if improved:
            lines.append(f"  >> mejor recall@1 -> {self.embeddings_path.name}")
        lines.append(f"  JSON -> {self.json_path}")
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
    filename="best-{epoch:02d}-p{train/phase:.0f}-r1{val/recall_at_1:.3f}",
    monitor="val/recall_at_1",
    mode="max",
    save_top_k=1,
)
early_cb = MinEpochEarlyStopping(
    monitor="val/recall_at_1", mode="max", patience=EARLY_STOP_PATIENCE, verbose=False,
)
progress_cb = TQDMProgressBar(refresh_rate=10)

if not torch.cuda.is_available():
    raise RuntimeError("GPU no detectada. Colab: Runtime -> T4 GPU -> Reiniciar.")

lit = LitGeoVisionClipSAE()
trainer = pl.Trainer(
    max_epochs=NUM_EPOCHS,
    accelerator="gpu",
    devices=1,
    logger=loggers,
    callbacks=[ckpt_cb, early_cb, metrics_cb, progress_cb, LearningRateMonitor(logging_interval="epoch")],
    default_root_dir=str(RUN_DIR),
    log_every_n_steps=10,
    val_check_interval=VAL_CHECK_INTERVAL,
    accumulate_grad_batches=GRAD_ACCUM_STEPS,
    enable_progress_bar=True,
    enable_model_summary=False,
)
trainer.fit(lit, train_dataloaders=train_loader, val_dataloaders=val_loader)

print("\nEntrenamiento terminado.")
print("Mejor checkpoint:", ckpt_cb.best_model_path)

# --- Fase 4: evaluación test con mejor checkpoint ---
if ckpt_cb.best_model_path:
    lit_best = LitGeoVisionClipSAE()
    ckpt_raw = torch.load(ckpt_cb.best_model_path, map_location=device)
    lit_best.load_state_dict(ckpt_raw["state_dict"])
else:
    lit_best = lit
lit_best = lit_best.to(device)
lit_best.eval()

@torch.no_grad()
def eval_split(model_module, loader, split_name):
    model_module.eval()
    imgs, txts, zimgs = [], [], []
    for batch in loader:
        tiles = batch["tile"].to(device)
        ids = batch["input_ids"].to(device)
        masks = batch["attention_mask"].to(device)
        vi = model_module.model.encode_image(tiles)
        vt = model_module.model.encode_text(ids, masks)
        imgs.append(vi["e"].cpu())
        txts.append(vt["e"].cpu())
        zimgs.append(vi["z"].cpu())
    img = torch.cat(imgs, 0)
    txt = torch.cat(txts, 0)
    z = torch.cat(zimgs, 0)
    r1 = recall_at_k_image_to_text(img, txt, 1)
    r5 = recall_at_k_image_to_text(img, txt, 5)
    sp = sparsity_ratio(z)
    return {"split": split_name, "recall_at_1": r1, "recall_at_5": r5, "sparsity_img": sp, "n": int(img.shape[0])}


@torch.no_grad()
def eval_test_prompt_ensemble(model_module, dataset, batch_size=BATCH_SIZE):
    """Promedia embeddings de texto sobre variantes de caption (SenCLIP)."""
    model_module.eval()
    img_list, txt_list = [], []
    for start in range(0, len(dataset), batch_size):
        batch_rows = [dataset[i] for i in range(start, min(start + batch_size, len(dataset)))]
        tiles = torch.stack([b["tile"] for b in batch_rows]).to(device)
        vi = model_module.model.encode_image(tiles)
        txt_embs = []
        for b in batch_rows:
            variants = b.get("caption_variants") or [str(b["tile_id"])]
            vecs = []
            for cap in variants:
                tok = tokenizer(
                    cap, truncation=True, max_length=256,
                    padding="max_length", return_tensors="pt",
                )
                vt = model_module.model.encode_text(
                    tok["input_ids"].to(device), tok["attention_mask"].to(device),
                )
                vecs.append(vt["e"])
            txt_embs.append(torch.stack(vecs, 0).mean(0))
        img_list.append(vi["e"].cpu())
        txt_list.append(torch.stack(txt_embs, 0).cpu())
    img = torch.cat(img_list, 0)
    txt = torch.cat(txt_list, 0)
    r1 = recall_at_k_image_to_text(img, txt, 1)
    r5 = recall_at_k_image_to_text(img, txt, 5)
    return r1, r5

test_metrics = eval_split(lit_best, test_loader, "test")
r1_ens, r5_ens = eval_test_prompt_ensemble(lit_best, ds_test_ensemble)
test_metrics["recall_at_1_ensemble"] = r1_ens
test_metrics["recall_at_5_ensemble"] = r5_ens
test_metrics["checkpoint"] = str(ckpt_cb.best_model_path or "")

TEST_METRICS_JSON.write_text(json.dumps(test_metrics, indent=2), encoding="utf-8")
print("\n=== Fase 4 — Test ===")
for k, v in test_metrics.items():
    print(f"  {k}: {v}")
print("Guardado:", TEST_METRICS_JSON)
print("Historial val:", METRICS_JSON)
print("Embeddings val:", EMBEDDINGS_BEST)

if USE_WANDB:
    import wandb
    wandb.finish()
