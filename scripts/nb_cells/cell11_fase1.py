# @title Fase 1 — contraste + augment (épocas 0–19)
# Visual congelado | captions múltiples | α_SAE 0→0.05
lit = load_lit(ckpt_path=None)
trainer, ckpt_cb = build_trainer(PHASE1_MAX_EPOCH, "fase1-{epoch:02d}-r1{val/recall_at_1:.3f}")
trainer.fit(lit, train_dataloaders=train_loader, val_dataloaders=val_loader)
PHASE1_CKPT_PATH = _copy_best_ckpt(ckpt_cb, PHASE1_CKPT)
print("Fase 1 terminada. Mejor ckpt:", PHASE1_CKPT_PATH or ckpt_cb.best_model_path)
