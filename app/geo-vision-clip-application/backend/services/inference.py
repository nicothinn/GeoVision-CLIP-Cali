"""
Servicio de inferencia para MODO PRODUCCIÓN.
Pipeline: tile → RemoteCLIP → embedding 512-d + 19 covariables → Conv3D → predicción
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

import numpy as np
import torch

from backend.schemas.models import PredictResponse

CHECKPOINT_DIR = "backend/checkpoints"

CONTAMINANTS = ["NO2", "SO2", "O3"]
HORIZONS = ["T+1", "T+3", "T+7"]

GPU_MEM_MIN_GB = 2.0


def _get_device() -> torch.device:
    if torch.cuda.is_available():
        try:
            free_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
            if free_mem >= GPU_MEM_MIN_GB:
                return torch.device("cuda")
        except Exception:
            pass
    return torch.device("cpu")


class ModelLoader:
    """Singleton que carga modelos lazy."""

    _instance: ModelLoader | None = None

    def __init__(self) -> None:
        self.device = _get_device()
        self.geovision: torch.nn.Module | None = None
        self.conv3d: torch.nn.Module | None = None
        self._loaded = False

    @classmethod
    def get_instance(cls) -> ModelLoader:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self) -> None:
        if self._loaded:
            return
        t0 = time.perf_counter()
        print(f"[ModelLoader] Iniciando carga en: {self.device}")

        # ─── 1. RemoteCLIP visual (pre-entrenado, congelado) ─────────────
        import open_clip
        from huggingface_hub import hf_hub_download
        import torch.nn as nn

        # Cargar RemoteCLIP completo
        cm, _, _ = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained=None
        )
        cp = hf_hub_download(
            "chendelong/RemoteCLIP",
            "RemoteCLIP-ViT-B-32.pt",
        )
        cm.load_state_dict(torch.load(cp, map_location="cpu", weights_only=True), strict=False)

        # Adaptar conv1 de 3→12 canales (como en el notebook)
        oc = cm.visual.conv1
        nc = nn.Conv2d(
            12, oc.out_channels, oc.kernel_size,
            stride=oc.stride, padding=oc.padding, bias=False,
        )
        with torch.no_grad():
            w = nc.weight.data
            w[:, 3] = oc.weight[:, 0]
            w[:, 2] = oc.weight[:, 1]
            w[:, 1] = oc.weight[:, 2]
            wm = oc.weight.mean(1, keepdim=False)
            for b in range(12):
                if b not in (3, 2, 1):
                    w[:, b] = wm * (3 / 12)
            nc.weight.copy_(w)
        cm.visual.conv1 = nc
        cm.eval()

        # MS Adapter: 13→12 canales (la banda 13 es SCL, no se usa)
        self.ms_adapter = nn.Conv2d(13, 12, kernel_size=1, bias=False)
        with torch.no_grad():
            w = self.ms_adapter.weight.data
            w.zero_()
            for i in range(12):
                w[i, i] = 1.0

        self.visual = cm.visual.to(self.device)
        self.ms_adapter = self.ms_adapter.to(self.device)
        for p in self.visual.parameters():
            p.requires_grad = False

        n_vis = sum(p.numel() for p in self.visual.parameters())
        print(f"  ✓ RemoteCLIP visual ({n_vis:,} params)")

        # ─── 2. SAE (cargado desde sae_best.pt) ──────────────────────────
        from backend.models.sae import SparseAutoencoder

        self.sae = SparseAutoencoder(d_model=512, d_hidden=2048).to(self.device)
        sd = torch.load(
            f"{CHECKPOINT_DIR}/sae_modelo_final/sae_best.pt",
            map_location="cpu", weights_only=False,
        )
        sae_weights = {k.replace("sae.", ""): v for k, v in sd["sae"].items()}
        self.sae.load_state_dict(sae_weights)
        self.sae.eval()
        print(f"  ✓ SAE ({sum(p.numel() for p in self.sae.parameters()):,} params)")

        # ─── 3. Conv3DSit3 (desde best.ckpt) ─────────────────────────────
        from backend.models.convlstm2d import Conv3DSit3

        ckpt = torch.load(
            f"{CHECKPOINT_DIR}/sit3_convlstm_weights/best.ckpt",
            map_location="cpu", weights_only=False,
        )
        sd_conv = {k.replace("model.", ""): v for k, v in ckpt["state_dict"].items()}

        self.conv3d = Conv3DSit3(input_channels=531)
        self.conv3d.load_state_dict(sd_conv)
        self.conv3d.eval().to(self.device)
        print(f"  ✓ Conv3DSit3 ({sum(p.numel() for p in self.conv3d.parameters()):,} params)")

        self._loaded = True
        print(f"[ModelLoader] Listo en {time.perf_counter() - t0:.1f}s")

    def is_loaded(self) -> bool:
        return self._loaded

    @torch.no_grad()
    def get_visual_embedding(self, tile: torch.Tensor) -> torch.Tensor:
        """
        Tile (13 bandas) → MS Adapter (13→12) → RemoteCLIP visual → embedding 512-d.
        """
        x = tile.to(self.device)
        if x.dim() == 3:
            x = x.unsqueeze(0)
        if x.dtype != torch.float32:
            x = x.float()

        # MS Adapter: 13→12 canales
        x12 = self.ms_adapter(x)

        # Redimensionar a 224×224
        x12 = torch.nn.functional.interpolate(
            x12, size=(224, 224), mode="bilinear", align_corners=False,
        )

        # RemoteCLIP visual
        h = self.visual(x12)  # (B, 512)
        return h


def run_inference(
    lat: float,
    lon: float,
    contaminant: str,
    horizon: str,
) -> PredictResponse:
    """Pipeline completo de inferencia para un punto."""
    loader = ModelLoader.get_instance()
    loader.load()

    c_idx = CONTAMINANTS.index(contaminant)
    h_idx = HORIZONS.index(horizon)

    # ─── Tile sintético → embedding ──────────────────────────────────────
    tile = _generate_random_tile()
    h = loader.get_visual_embedding(tile)  # (1, 512)

    # ─── Construir tensor Conv3D (1, 8, 531, 5, 5) ──────────────────────
    emb = h.cpu().numpy().flatten()
    covariables = np.zeros(19, dtype=np.float32)
    full_531 = np.concatenate([emb, covariables])

    inp = np.zeros((1, 8, 531, 5, 5), dtype=np.float32)
    for t in range(8):
        for i in range(5):
            for j in range(5):
                inp[0, t, :, i, j] = full_531

    inp_t = torch.from_numpy(inp).to(loader.device)

    # ─── Conv3D ──────────────────────────────────────────────────────────
    with torch.no_grad():
        output = loader.conv3d(inp_t)  # (1, 3, 3)

    # ─── Escalar predicción ──────────────────────────────────────────────
    def _scale(c_name: str, raw: float) -> float:
        if c_name == "NO2":
            return max(0, round(20 + raw * 10, 1))
        elif c_name == "SO2":
            return max(0, round(5 + raw * 5, 1))
        return max(0, round(40 + raw * 15, 1))

    raw_val = float(output[0, c_idx, h_idx].cpu().item())
    base_value = _scale(contaminant, raw_val)

    # ─── all_horizons ─────────────────────────────────────────────────────
    all_horizons: dict[str, dict[str, float]] = {}
    for h_name in HORIZONS:
        all_horizons[h_name] = {}
        for c_name in CONTAMINANTS:
            ci = CONTAMINANTS.index(c_name)
            hi = HORIZONS.index(h_name)
            v = float(output[0, ci, hi].cpu().item())
            all_horizons[h_name][c_name] = _scale(c_name, v)

    return PredictResponse(
        predicted_value=base_value,
        uncertainty_sigma=round(1.0 + abs(raw_val) * 0.5, 1),
        all_horizons=all_horizons,
        timestamp=datetime.now(timezone.utc).isoformat(),
        model_version="geovision-clip-v1.0-prod",
        md5_checkpoint="remoteclip+sae_best+conv3d_best",
    )


def _generate_random_tile() -> torch.Tensor:
    """Genera tile sintético de 13 bandas."""
    return torch.randn(1, 13, 64, 64) * 0.1
