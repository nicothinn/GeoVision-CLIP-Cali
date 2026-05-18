# @title Fase 4 — evaluación test + prompt ensemble
_best = PHASE3_CKPT if PHASE3_CKPT.exists() else PHASE2_CKPT if PHASE2_CKPT.exists() else PHASE1_CKPT
lit_best = load_lit(_best if _best.exists() else None).to(device)
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
    img, txt, z = torch.cat(imgs, 0), torch.cat(txts, 0), torch.cat(zimgs, 0)
    return {
        "split": split_name,
        "recall_at_1": recall_at_k_image_to_text(img, txt, 1),
        "recall_at_5": recall_at_k_image_to_text(img, txt, 5),
        "sparsity_img": sparsity_ratio(z),
        "n": int(img.shape[0]),
    }


@torch.no_grad()
def eval_test_prompt_ensemble(model_module, dataset, batch_size=BATCH_SIZE):
    model_module.eval()
    img_list, txt_list = [], []
    for start in range(0, len(dataset), batch_size):
        rows = [dataset[i] for i in range(start, min(start + batch_size, len(dataset)))]
        tiles = torch.stack([r["tile"] for r in rows]).to(device)
        vi = model_module.model.encode_image(tiles)
        img_list.append(vi["e"].cpu())
        txt_batch = []
        for r in rows:
            vecs = []
            for cap in r.get("caption_variants", []):
                tok = tokenizer(
                    cap, truncation=True, max_length=256,
                    padding="max_length", return_tensors="pt",
                )
                vt = model_module.model.encode_text(
                    tok["input_ids"].to(device), tok["attention_mask"].to(device),
                )
                vecs.append(vt["e"])
            txt_batch.append(torch.stack(vecs, 0).mean(0))
        txt_list.append(torch.stack(txt_batch, 0).cpu())
    img = torch.cat(img_list, 0)
    txt = torch.cat(txt_list, 0)
    return recall_at_k_image_to_text(img, txt, 1), recall_at_k_image_to_text(img, txt, 5)


test_metrics = eval_split(lit_best, test_loader, "test")
r1_ens, r5_ens = eval_test_prompt_ensemble(lit_best, ds_test_ensemble)
test_metrics["recall_at_1_ensemble"] = r1_ens
test_metrics["recall_at_5_ensemble"] = r5_ens
test_metrics["checkpoint"] = str(_best)
TEST_METRICS_JSON.write_text(json.dumps(test_metrics, indent=2), encoding="utf-8")
print("\n=== Fase 4 — Test ===")
for k, v in test_metrics.items():
    print(f"  {k}: {v}")
print("Guardado:", TEST_METRICS_JSON)

if USE_WANDB:
    import wandb
    wandb.finish()
