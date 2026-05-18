# @title Fase 3 — SAE consigna (épocas 40–59)
# α_SAE=0.1 | continúa desde checkpoint Fase 2
_resume = str(PHASE2_CKPT) if PHASE2_CKPT.exists() else (str(PHASE1_CKPT) if PHASE1_CKPT.exists() else None)
if not _resume:
    raise FileNotFoundError("Ejecuta Fase 1 y Fase 2 antes.")
lit = LitGeoVisionClipSAE()
trainer, ckpt_cb = build_trainer(PHASE3_MAX_EPOCH, "fase3-{epoch:02d}-r1{val/recall_at_1:.3f}")
trainer.fit(lit, train_dataloaders=train_loader, val_dataloaders=val_loader, ckpt_path=_resume)
PHASE3_CKPT_PATH = _copy_best_ckpt(ckpt_cb, PHASE3_CKPT)
print("Fase 3 terminada. Mejor ckpt:", PHASE3_CKPT_PATH or ckpt_cb.best_model_path)
print("Historial:", METRICS_JSON)
