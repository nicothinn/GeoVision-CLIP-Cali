"""GeoVision-CLIP: ViT-B/32 (RemoteCLIP) + texto multilingüe + SAE + proyección 256-d."""

from __future__ import annotations

import math
from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F

from .sae import SparseAutoencoder, sae_loss

# OpenAI CLIP mean/std (RGB)
_CLIP_MEAN = (0.48145466, 0.4578275, 0.40821073)
_CLIP_STD = (0.26862954, 0.26130258, 0.27577711)


def _load_openclip_visual(
    model_name: str = "ViT-B-32",
    pretrained: str = "remoteclip",
) -> tuple[nn.Module, str]:
    """Carga solo la torre visual de open_clip. Prueba variantes de `pretrained`."""
    import open_clip

    candidates = [pretrained, "remoteclip", "laion400m_e32", "openai"]
    last_err: Exception | None = None
    for tag in candidates:
        try:
            model, _, _ = open_clip.create_model_and_transforms(
                model_name,
                pretrained=tag,
            )
            return model.visual, tag
        except Exception as e:  # pragma: no cover
            last_err = e
            continue
    raise RuntimeError(f"No se pudo cargar open_clip {model_name}: {last_err}")


class GeoVisionClipSAEModel(nn.Module):
    """Adaptador 13→3, ViT RemoteCLIP, MiniLM multilingüe, SAEs y cabezas 256-d."""

    def __init__(
        self,
        text_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        dim_latent_sae: int = 512,
        dim_contrastive: int = 256,
        alpha_sae: float = 0.1,
        lambda_l1: float = 1e-3,
        openclip_name: str = "ViT-B-32",
        openclip_pretrained: str = "remoteclip",
    ) -> None:
        super().__init__()
        self.dim_latent_sae = dim_latent_sae
        self.dim_contrastive = dim_contrastive
        self.alpha_sae = alpha_sae
        self.lambda_l1 = lambda_l1

        self.ms_adapter = nn.Conv2d(13, 3, kernel_size=1, bias=True)

        self.visual, _tag = _load_openclip_visual(openclip_name, openclip_pretrained)
        dim_img = int(getattr(self.visual, "output_dim", 512))

        from transformers import AutoModel, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(text_model_name)
        self.text_encoder = AutoModel.from_pretrained(text_model_name)
        dim_txt_hidden = int(self.text_encoder.config.hidden_size)

        self.text_to_sae = nn.Linear(dim_txt_hidden, dim_latent_sae)

        self.sae_img = SparseAutoencoder(dim_img, dim_latent_sae)
        self.sae_txt = SparseAutoencoder(dim_latent_sae, dim_latent_sae)

        self.proj_img = nn.Linear(dim_latent_sae, dim_contrastive)
        self.proj_txt = nn.Linear(dim_latent_sae, dim_contrastive)

        self.logit_scale = nn.Parameter(torch.ones([]) * math.log(1.0 / 0.07))

        self.register_buffer(
            "clip_mean",
            torch.tensor(_CLIP_MEAN).view(1, 3, 1, 1),
            persistent=False,
        )
        self.register_buffer(
            "clip_std",
            torch.tensor(_CLIP_STD).view(1, 3, 1, 1),
            persistent=False,
        )

    def encode_image(self, tiles: torch.Tensor) -> dict[str, torch.Tensor]:
        """tiles: (B,13,H,W) float o int; devuelve h, z, h_hat, e (256)."""
        if tiles.dtype != torch.float32:
            tiles = tiles.float()
        x3 = self.ms_adapter(tiles)
        x3 = F.interpolate(x3, size=(224, 224), mode="bicubic", align_corners=False)
        x3 = (x3 - self.clip_mean) / self.clip_std
        h = self.visual(x3)
        h_hat, z = self.sae_img(h)
        e = self.proj_img(z)
        return {"h": h, "z": z, "h_hat": h_hat, "e": e}

    def encode_text(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> dict[str, torch.Tensor]:
        out = self.text_encoder(input_ids=input_ids, attention_mask=attention_mask)
        last = out.last_hidden_state
        mask = attention_mask.unsqueeze(-1).float()
        pooled = (last * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-6)
        h = self.text_to_sae(pooled)
        h_hat, z = self.sae_txt(h)
        e = self.proj_txt(z)
        return {"h": h, "z": z, "h_hat": h_hat, "e": e}

    def clip_infonce(self, e_img: torch.Tensor, e_txt: torch.Tensor) -> torch.Tensor:
        e_img = F.normalize(e_img, dim=-1)
        e_txt = F.normalize(e_txt, dim=-1)
        logit_scale = self.logit_scale.exp().clamp(max=100.0)
        logits = logit_scale * e_img @ e_txt.T
        targets = torch.arange(logits.shape[0], device=logits.device)
        loss_i = F.cross_entropy(logits, targets)
        loss_t = F.cross_entropy(logits.T, targets)
        return 0.5 * (loss_i + loss_t)

    def forward(
        self,
        tiles: torch.Tensor,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> dict[str, Any]:
        vi = self.encode_image(tiles)
        vt = self.encode_text(input_ids, attention_mask)

        l_infonce = self.clip_infonce(vi["e"], vt["e"])

        ls_i, mse_i, _ = sae_loss(vi["h"], vi["h_hat"], vi["z"], self.lambda_l1)
        ls_t, mse_t, _ = sae_loss(vt["h"], vt["h_hat"], vt["z"], self.lambda_l1)
        l_sae = ls_i + ls_t

        total = l_infonce + self.alpha_sae * l_sae

        return {
            "loss": total,
            "loss_infonce": l_infonce.detach(),
            "loss_sae_img": ls_i.detach(),
            "loss_sae_txt": ls_t.detach(),
            "mse_sae_img": mse_i.detach(),
            "mse_sae_txt": mse_t.detach(),
            "e_img": vi["e"],
            "e_txt": vt["e"],
            "z_img": vi["z"],
            "z_txt": vt["z"],
            "h_img": vi["h"],
            "h_txt": vt["h"],
            "h_hat_img": vi["h_hat"],
            "h_hat_txt": vt["h_hat"],
        }

    def set_text_trainable(self, trainable: bool) -> None:
        for p in self.text_encoder.parameters():
            p.requires_grad = trainable
        for p in self.text_to_sae.parameters():
            p.requires_grad = trainable
