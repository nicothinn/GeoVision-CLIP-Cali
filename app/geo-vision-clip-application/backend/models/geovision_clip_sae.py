"""
GeoVision-CLIP + SAE para inferencia.
Carga RemoteCLIP visual pre-entrenado + SAE (sae_best.pt).

Arquitectura real:
  Sentinel-2 tile (13 bandas) → MS Adapter Conv2d(13→3) → RemoteCLIP ViT-B/32 → 
  embedding 512-d → SAE (512→2048→512) → embedding SAE 512-d

El text encoder (CLIP fine-tuneado de clip_modelo/best.pt) solo se usa
durante entrenamiento, no en inferencia.
"""

from __future__ import annotations

import math

import torch
import torch.nn as nn
import torch.nn.functional as F

from .sae import SparseAutoencoder

# Media/std de CLIP para normalizar RGB
_CLIP_MEAN = (0.48145466, 0.4578275, 0.40821073)
_CLIP_STD = (0.26862954, 0.26130258, 0.27577711)

CHECKPOINT_DIR = "backend/checkpoints"


def load_openclip_visual(
    model_name: str = "ViT-B-32",
    pretrained: str = "remoteclip",
) -> nn.Module:
    """Carga la torre visual de open_clip (pre-entrenada)."""
    import open_clip

    candidates = [pretrained, "remoteclip", "laion400m_e32", "openai"]
    last_err: Exception | None = None
    for tag in candidates:
        try:
            model, _, _ = open_clip.create_model_and_transforms(
                model_name, pretrained=tag,
            )
            return model.visual
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"No se pudo cargar open_clip {model_name}: {last_err}")


def load_sae_weights(sae: SparseAutoencoder, path: str) -> None:
    """Carga pesos del SAE desde sae_best.pt."""
    state = torch.load(path, map_location="cpu", weights_only=False)
    sd = state["sae"]  # OrderedDict con encoder.weight, decoder.weight
    # sae_best.pt guarda como 'sae.encoder.weight' y 'sae.decoder.weight'
    cleaned = {}
    for k, v in sd.items():
        # Remueve prefijo 'sae.' si existe
        key = k.replace("sae.", "")
        cleaned[key] = v
    sae.load_state_dict(cleaned)
    print(f"  ✓ SAE cargado desde {path}")


class GeoVisionClipSAEModel(nn.Module):
    """
    Modelo completo de inferencia.
    Tile → RemoteCLIP → SAE → embedding 512-d listo para Conv3D.
    """

    def __init__(
        self,
        dim_sae: int = 512,
        dim_hidden_sae: int = 2048,
        device: str = "cpu",
    ):
        super().__init__()
        self.device = device

        # MS Adapter: 13 bandas Sentinel-2 → 3 canales RGB
        self.ms_adapter = nn.Conv2d(13, 3, kernel_size=1, bias=True)

        # Encoder visual RemoteCLIP (pre-entrenado, congelado)
        self.visual = load_openclip_visual()
        for p in self.visual.parameters():
            p.requires_grad = False

        # SAE (512 → 2048 → 512, cargado desde sae_best.pt)
        self.sae = SparseAutoencoder(d_model=dim_sae, d_hidden=dim_hidden_sae)

        # Buffers de normalización CLIP
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

        self.to(device)
        self.eval()

    def forward(self, tiles: torch.Tensor) -> dict[str, torch.Tensor]:
        """
        tiles: (B, 13, H, W) float
        Devuelve: h (embedding RemoteCLIP 512-d),
                  z (latente SAE),
                  h_hat (reconstrucción),
                  e (embedding SAE normalizado)
        """
        if tiles.dtype != torch.float32:
            tiles = tiles.float()

        # MS Adapter 13→3 canales
        x3 = self.ms_adapter(tiles)

        # Redimensionar a 224×224 (tamaño CLIP)
        x3 = F.interpolate(x3, size=(224, 224), mode="bicubic", align_corners=False)

        # Normalizar
        x3 = (x3 - self.clip_mean) / self.clip_std

        # RemoteCLIP visual encoder
        h = self.visual(x3)  # (B, 512)

        # SAE
        h_hat, z = self.sae(h)
        e = F.normalize(z, dim=-1)

        return {"h": h, "h_hat": h_hat, "z": z, "e": e}

    @torch.no_grad()
    def get_embedding(self, tile: torch.Tensor) -> torch.Tensor:
        """Inferencia rápida: tile → embedding 512-d normalizado."""
        out = self.forward(tile)
        return out["e"]


def load_geovision_model(
    sae_path: str = f"{CHECKPOINT_DIR}/sae_modelo_final/sae_best.pt",
    device: str = "cpu",
) -> GeoVisionClipSAEModel:
    """Carga el modelo completo con pesos del SAE."""
    model = GeoVisionClipSAEModel(device=device)
    load_sae_weights(model.sae, sae_path)
    return model
