# @title Modelo GeoVision-CLIP + SAE (adaptador espectral + fases)
import open_clip
from huggingface_hub import hf_hub_download
from transformers import AutoModel

_CLIP_MEAN = (0.48145466, 0.4578275, 0.40821073)
_CLIP_STD = (0.26862954, 0.26130258, 0.27577711)

REMOTECLIP_HF_REPO = "chendelong/RemoteCLIP"
REMOTECLIP_MODEL_NAME = "ViT-B-32"
REMOTECLIP_CACHE_DIR = Path("/content/checkpoints")


def load_remoteclip_visual(model_name: str = REMOTECLIP_MODEL_NAME):
    REMOTECLIP_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    ckpt_path = hf_hub_download(
        REMOTECLIP_HF_REPO,
        f"RemoteCLIP-{model_name}.pt",
        cache_dir=str(REMOTECLIP_CACHE_DIR),
        token=token,
    )
    print(f"{model_name} descargado en: {ckpt_path}")
    model, _, _ = open_clip.create_model_and_transforms(model_name)
    try:
        ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=True)
    except TypeError:
        ckpt = torch.load(ckpt_path, map_location="cpu")
    msg = model.load_state_dict(ckpt)
    print("load_state_dict:", msg)
    visual = model.visual
    print(f"OK: RemoteCLIP visual ({model_name}) listo.")
    return visual, ckpt_path


def _vit_resblocks(visual):
    if hasattr(visual, "transformer") and hasattr(visual.transformer, "resblocks"):
        return visual.transformer.resblocks
    trunk = getattr(visual, "trunk", None)
    if trunk is not None and hasattr(trunk, "transformer"):
        return trunk.transformer.resblocks
    return None


def set_visual_trainable(visual, mode: str, n_blocks: int = VISUAL_UNFREEZE_BLOCKS):
    for p in visual.parameters():
        p.requires_grad = False
    if mode == "frozen":
        return
    if mode == "partial":
        blocks = _vit_resblocks(visual)
        if blocks is None:
            print("AVISO: no se encontraron resblocks ViT; visual sigue congelado.")
            return
        for block in list(blocks)[-n_blocks:]:
            for p in block.parameters():
                p.requires_grad = True
        return
    if mode == "full":
        for p in visual.parameters():
            p.requires_grad = True


class SpectralAdapter(nn.Module):
    """13 bandas Sentinel-2 -> 3 canales (TimeSenCLIP / RemoteCLIP)."""

    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(13, 32, kernel_size=1, bias=True),
            nn.GELU(),
            nn.Conv2d(32, 3, kernel_size=1, bias=True),
        )

    def forward(self, x):
        return self.net(x)


class GeoVisionClipSAEModel(nn.Module):
    def __init__(
        self,
        text_model_name=text_name,
        dim_latent_sae=512,
        dim_contrastive=256,
        alpha_sae=ALPHA_SAE_PHASE1,
        lambda_l1=LAMBDA_L1,
    ):
        super().__init__()
        self.alpha_sae = alpha_sae
        self.lambda_l1 = lambda_l1
        self.training_phase = 1
        self.ms_adapter = SpectralAdapter()
        self.visual, self.visual_pretrained_tag = load_remoteclip_visual(REMOTECLIP_MODEL_NAME)
        set_visual_trainable(self.visual, "frozen")
        dim_img = int(getattr(self.visual, "output_dim", 512))
        self.text_encoder = AutoModel.from_pretrained(text_model_name)
        dtxt = int(self.text_encoder.config.hidden_size)
        self.text_to_sae = nn.Linear(dtxt, dim_latent_sae)
        self.sae_img = SparseAutoencoder(dim_img, dim_latent_sae)
        self.sae_txt = SparseAutoencoder(dim_latent_sae, dim_latent_sae)
        self.proj_img = nn.Linear(dim_latent_sae, dim_contrastive)
        self.proj_txt = nn.Linear(dim_latent_sae, dim_contrastive)
        self.logit_scale = nn.Parameter(torch.ones([]) * math.log(1.0 / 0.07))
        self.register_buffer("clip_mean", torch.tensor(_CLIP_MEAN).view(1, 3, 1, 1), persistent=False)
        self.register_buffer("clip_std", torch.tensor(_CLIP_STD).view(1, 3, 1, 1), persistent=False)

    def apply_training_phase(self, phase: int, epoch: int):
        self.training_phase = phase
        if phase == 1:
            set_visual_trainable(self.visual, "frozen")
            self.alpha_sae = 0.0 if epoch < ALPHA_SAE_WARMUP_EPOCHS else ALPHA_SAE_PHASE1
            self.lambda_l1 = LAMBDA_L1
        elif phase == 2:
            set_visual_trainable(self.visual, "partial")
            self.alpha_sae = ALPHA_SAE_PHASE1
            self.lambda_l1 = LAMBDA_L1
        else:
            set_visual_trainable(self.visual, "partial")
            self.alpha_sae = ALPHA_SAE_PHASE3
            self.lambda_l1 = LAMBDA_L1_PHASE3

    def encode_image(self, tiles):
        tiles = tiles.float()
        x3 = self.ms_adapter(tiles)
        x3 = F.interpolate(x3, (224, 224), mode="bicubic", align_corners=False)
        x3 = (x3 - self.clip_mean) / self.clip_std
        h = self.visual(x3)
        h_hat, z = self.sae_img(h)
        return {"h": h, "z": z, "h_hat": h_hat, "e": self.proj_img(z)}

    def encode_text(self, input_ids, attention_mask):
        out = self.text_encoder(input_ids=input_ids, attention_mask=attention_mask)
        m = attention_mask.unsqueeze(-1).float()
        pooled = (out.last_hidden_state * m).sum(1) / m.sum(1).clamp(min=1e-6)
        h = self.text_to_sae(pooled)
        h_hat, z = self.sae_txt(h)
        return {"h": h, "z": z, "h_hat": h_hat, "e": self.proj_txt(z)}

    def clip_infonce(self, e_img, e_txt):
        e_img = F.normalize(e_img, dim=-1)
        e_txt = F.normalize(e_txt, dim=-1)
        scale = self.logit_scale.exp().clamp(max=100.0)
        logits = scale * (e_img @ e_txt.T)
        t = torch.arange(logits.size(0), device=logits.device)
        return 0.5 * (F.cross_entropy(logits, t) + F.cross_entropy(logits.T, t))

    def forward(self, tiles, input_ids, attention_mask):
        vi = self.encode_image(tiles)
        vt = self.encode_text(input_ids, attention_mask)
        l_infonce = self.clip_infonce(vi["e"], vt["e"])
        li, msei, _ = sae_loss(vi["h"], vi["h_hat"], vi["z"], self.lambda_l1)
        lt, mset, _ = sae_loss(vt["h"], vt["h_hat"], vt["z"], self.lambda_l1)
        total = l_infonce + self.alpha_sae * (li + lt)
        return {
            "loss": total,
            "loss_infonce": l_infonce.detach(),
            "loss_sae_img": li.detach(),
            "loss_sae_txt": lt.detach(),
            "mse_sae_img": msei.detach(),
            "mse_sae_txt": mset.detach(),
            "z_img": vi["z"],
            "z_txt": vt["z"],
            "alpha_sae": self.alpha_sae,
        }

    def set_text_trainable(self, trainable: bool):
        for p in self.text_encoder.parameters():
            p.requires_grad = trainable
        for p in self.text_to_sae.parameters():
            p.requires_grad = trainable

    def param_groups(self):
        head = (
            list(self.ms_adapter.parameters())
            + list(self.sae_img.parameters())
            + list(self.sae_txt.parameters())
            + list(self.proj_img.parameters())
            + list(self.proj_txt.parameters())
            + [self.logit_scale]
        )
        text = list(self.text_encoder.parameters()) + list(self.text_to_sae.parameters())
        visual = list(self.visual.parameters())
        return [
            {"params": head, "lr": LR_HEAD},
            {"params": text, "lr": LR_TEXT},
            {"params": visual, "lr": LR_VISUAL},
        ]


class LitGeoVisionClipSAE(pl.LightningModule):
    def __init__(self):
        super().__init__()
        self.model = GeoVisionClipSAEModel()
        self._val_img, self._val_txt = [], []
        self._val_z_img, self._val_z_txt = [], []

    def on_train_epoch_start(self):
        ep = int(self.current_epoch)
        phase = training_phase(ep)
        self.model.apply_training_phase(phase, ep)
        self.model.set_text_trainable(ep >= FREEZE_TEXT_EPOCHS)
        self.log("train/phase", float(phase), on_epoch=True)
        self.log("train/alpha_sae", float(self.model.alpha_sae), on_epoch=True)

    def training_step(self, batch, batch_idx):
        o = self.model(batch["tile"], batch["input_ids"], batch["attention_mask"])
        self.log("train/loss", o["loss"], prog_bar=True, on_step=False, on_epoch=True)
        self.log("train/infonce", o["loss_infonce"], on_epoch=True)
        self.log("train/mse_sae_img", o["mse_sae_img"], on_epoch=True)
        self.log("train/mse_sae_txt", o["mse_sae_txt"], on_epoch=True)
        self.log("train/sparsity_img", sparsity_ratio(o["z_img"]), on_epoch=True, prog_bar=True)
        self.log("train/sparsity_txt", sparsity_ratio(o["z_txt"]), on_epoch=True)
        return o["loss"]

    def on_validation_epoch_start(self):
        self._val_img.clear()
        self._val_txt.clear()
        self._val_z_img.clear()
        self._val_z_txt.clear()

    def validation_step(self, batch, batch_idx):
        o = self.model(batch["tile"], batch["input_ids"], batch["attention_mask"])
        self.log("val/loss", o["loss"], on_epoch=True, prog_bar=True)
        self.log("val/infonce", o["loss_infonce"], on_epoch=True)
        self.log("val/mse_sae_img", o["mse_sae_img"], on_epoch=True)
        self.log("val/mse_sae_txt", o["mse_sae_txt"], on_epoch=True)
        self.log("val/sparsity_img", sparsity_ratio(o["z_img"]), on_epoch=True, prog_bar=True)
        with torch.no_grad():
            vi = self.model.encode_image(batch["tile"])
            vt = self.model.encode_text(batch["input_ids"], batch["attention_mask"])
        self._val_img.append(vi["e"].detach().cpu())
        self._val_txt.append(vt["e"].detach().cpu())
        self._val_z_img.append(vi["z"].detach().cpu())
        self._val_z_txt.append(vt["z"].detach().cpu())

    def on_validation_epoch_end(self):
        if not self._val_img:
            return
        img = torch.cat(self._val_img, 0).to(self.device)
        txt = torch.cat(self._val_txt, 0).to(self.device)
        self.log("val/recall_at_1", recall_at_k_image_to_text(img, txt, 1), prog_bar=True, on_epoch=True)
        self.log("val/recall_at_5", recall_at_k_image_to_text(img, txt, 5), prog_bar=True, on_epoch=True)

    def configure_optimizers(self):
        opt = torch.optim.AdamW(self.model.param_groups(), weight_decay=WEIGHT_DECAY)

        def lr_lambda(epoch):
            if epoch < WARMUP_EPOCHS:
                return max(1e-3, (epoch + 1) / WARMUP_EPOCHS)
            progress = (epoch - WARMUP_EPOCHS) / max(1, NUM_EPOCHS - WARMUP_EPOCHS)
            return MIN_LR_RATIO + (1.0 - MIN_LR_RATIO) * 0.5 * (1.0 + math.cos(math.pi * progress))

        sched = torch.optim.lr_scheduler.LambdaLR(opt, lr_lambda=lr_lambda)
        return {"optimizer": opt, "lr_scheduler": {"scheduler": sched, "interval": "epoch"}}
