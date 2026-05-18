# @title Fase 2 — unfreeze ViT parcial (épocas 20–39)
# Últimos 2 bloques ViT | continúa desde checkpoint Fase 1
_resume = str(PHASE1_CKPT) if PHASE1_CKPT.exists() else None
if not _resume:
    raise FileNotFoundError("Ejecuta primero la celda Fase 1 (falta checkpoints/fase1_best.ckpt)")
lit = LitGeoVisionClipSAE()
trainer, ckpt_cb = build_trainer(PHASE2_MAX_EPOCH, "fase2-{epoch:02d}-r1{val/recall_at_1:.3f}")
trainer.fit(lit, train_dataloaders=train_loader, val_dataloaders=val_loader, ckpt_path=_resume)
PHASE2_CKPT_PATH = _copy_best_ckpt(ckpt_cb, PHASE2_CKPT)
print("Fase 2 terminada. Mejor ckpt:", PHASE2_CKPT_PATH or ckpt_cb.best_model_path)
