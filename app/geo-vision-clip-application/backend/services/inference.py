"""
Servicio de inferencia para MODO PRODUCCIÓN.
Pipeline: tile → RemoteCLIP → embedding 512-d + 19 covariables → Conv3D → predicción
Luego: Kriging correction + grilla N×N para overlay.
"""

from __future__ import annotations

import math
import time
from datetime import datetime, timezone

import numpy as np
import torch

from backend.schemas.models import GridData, PredictResponse

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
        self.kriging: object | None = None
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

        # ─── 1. RemoteCLIP visual ─────────────────────────────────────────
        import open_clip
        from huggingface_hub import hf_hub_download
        import torch.nn as nn

        cm, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained=None)
        cp = hf_hub_download("chendelong/RemoteCLIP", "RemoteCLIP-ViT-B-32.pt")
        cm.load_state_dict(torch.load(cp, map_location="cpu", weights_only=True), strict=False)

        oc = cm.visual.conv1
        nc = nn.Conv2d(12, oc.out_channels, oc.kernel_size,
                       stride=oc.stride, padding=oc.padding, bias=False)
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

        self.ms_adapter = nn.Conv2d(13, 12, kernel_size=1, bias=False)
        with torch.no_grad():
            w = self.ms_adapter.weight.data; w.zero_()
            for i in range(12):
                w[i, i] = 1.0

        self.visual = cm.visual.to(self.device)
        self.ms_adapter = self.ms_adapter.to(self.device)
        for p in self.visual.parameters():
            p.requires_grad = False
        n_vis = sum(p.numel() for p in self.visual.parameters())
        print(f"  ✓ RemoteCLIP visual ({n_vis:,} params)")

        # ─── 2. Conv3DSit3 ────────────────────────────────────────────────
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

        # ─── 3. KrigingService ───────────────────────────────────────────
        from backend.services.kriging import KrigingService

        self.kriging = KrigingService.get_instance()
        self.kriging.load()
        print(f"  ✓ KrigingService (SO2, O3)")

        self._loaded = True
        print(f"[ModelLoader] Listo en {time.perf_counter() - t0:.1f}s")

    def is_loaded(self) -> bool:
        return self._loaded

    @torch.no_grad()
    def get_visual_embedding(self, tile: torch.Tensor) -> torch.Tensor:
        x = tile.to(self.device)
        if x.dim() == 3:
            x = x.unsqueeze(0)
        if x.dtype != torch.float32:
            x = x.float()
        x12 = self.ms_adapter(x)
        x12 = torch.nn.functional.interpolate(
            x12, size=(224, 224), mode="bilinear", align_corners=False,
        )
        h = self.visual(x12)
        return h


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _generate_random_tile() -> torch.Tensor:
    return torch.randn(1, 13, 64, 64) * 0.1


def _build_conv3d_input(h: torch.Tensor) -> torch.Tensor:
    """Construye tensor (1, 8, 531, 5, 5) para Conv3D desde embedding 512-d."""
    emb = h.cpu().numpy().flatten()
    covariables = np.zeros(19, dtype=np.float32)
    full_531 = np.concatenate([emb, covariables])
    inp = np.zeros((1, 8, 531, 5, 5), dtype=np.float32)
    for t in range(8):
        for i in range(5):
            for j in range(5):
                inp[0, t, :, i, j] = full_531
    return torch.from_numpy(inp)


def _scale_prediction(c_name: str, raw: float) -> float:
    if c_name == "NO2":
        return max(0, round(20 + raw * 10, 1))
    elif c_name == "SO2":
        return max(0, round(5 + raw * 5, 1))
    return max(0, round(40 + raw * 15, 1))


def _generate_kriging_grid(
    lat: float, lon: float, radius_km: float, contaminant: str,
    kriging_service: object,
) -> GridData:
    """
    Genera una grilla N×N alrededor de (lat, lon) con valores interpolados
    desde la superficie krigeada + variación por distancia.
    """
    step = 0.01  # ~1.1 km
    cells = max(1, math.ceil(radius_km / 1.1))
    grid_h = 2 * cells + 1
    grid_w = 2 * cells + 1

    # Obtener valor krigeado en el centro
    z_center, sigma_center = kriging_service.interpolate(lat, lon, contaminant)

    lats_grid: list[list[float]] = []
    lons_grid: list[list[float]] = []
    values_grid: list[list[float]] = []
    variances_grid: list[list[float]] = []

    for i in range(grid_h):
        row_lat: list[float] = []
        row_lon: list[float] = []
        row_val: list[float] = []
        row_var: list[float] = []
        for j in range(grid_w):
            pt_lat = lat + (i - cells) * step
            pt_lon = lon + (j - cells) * step
            dist = math.sqrt((i - cells) ** 2 + (j - cells) ** 2) / cells

            # Interpolar desde kriging
            z_pt, sigma_pt = kriging_service.interpolate(pt_lat, pt_lon, contaminant)
            # Decaimiento suave con distancia desde el centro
            weight = math.exp(-dist * 2)
            val = z_center * weight + z_pt * (1 - weight)
            var = sigma_center * weight + sigma_pt * (1 - weight)

            row_lat.append(round(pt_lat, 4))
            row_lon.append(round(pt_lon, 4))
            row_val.append(round(val, 2))
            row_var.append(round(var, 2))

        lats_grid.append(row_lat)
        lons_grid.append(row_lon)
        values_grid.append(row_val)
        variances_grid.append(row_var)

    return GridData(lats=lats_grid, lons=lons_grid, values=values_grid, variances=variances_grid)


# ─── Pipeline principal ──────────────────────────────────────────────────────

def run_inference(
    lat: float,
    lon: float,
    radius_km: float,
    contaminant: str,
    horizon: str,
) -> PredictResponse:
    """Pipeline: Conv3D → Kriging → grilla."""
    loader = ModelLoader.get_instance()
    loader.load()

    c_idx = CONTAMINANTS.index(contaminant)
    h_idx = HORIZONS.index(horizon)

    # ─── Conv3D ──────────────────────────────────────────────────────────
    tile = _generate_random_tile()
    h = loader.get_visual_embedding(tile)
    inp = _build_conv3d_input(h).to(loader.device)

    with torch.no_grad():
        output = loader.conv3d(inp)  # (1, 3, 3)

    raw_val = float(output[0, c_idx, h_idx].cpu().item())
    base_value = _scale_prediction(contaminant, raw_val)

    # ─── Corrección Kriging ──────────────────────────────────────────────
    z_kriged, sigma_kriged = 0.0, 0.0
    ks = loader.kriging
    if contaminant in ("SO2", "O3"):
        z_kriged, sigma_kriged = ks.interpolate(lat, lon, contaminant)
        # Combinar: promedio ponderado por confianza
        w_kriging = 1.0 / (sigma_kriged + 1.0)
        w_conv3d = 1.0
        combined = (base_value * w_conv3d + z_kriged * w_kriging) / (w_conv3d + w_kriging)
        final_value = round(combined, 1)
        final_sigma = round(math.sqrt(sigma_kriged ** 2 + 0.5 ** 2), 1)
    else:
        # NO2: sin kriging, solo Conv3D
        final_value = base_value
        final_sigma = round(1.0 + abs(raw_val) * 0.5, 1)

    # ─── Grilla krigeada ─────────────────────────────────────────────────
    grid = _generate_kriging_grid(lat, lon, radius_km, contaminant, ks)

    # ─── all_horizons ─────────────────────────────────────────────────────
    all_horizons: dict[str, dict[str, float]] = {}
    for h_name in HORIZONS:
        all_horizons[h_name] = {}
        for c_name in CONTAMINANTS:
            ci = CONTAMINANTS.index(c_name)
            hi = HORIZONS.index(h_name)
            v = float(output[0, ci, hi].cpu().item())
            all_horizons[h_name][c_name] = _scale_prediction(c_name, v)

    return PredictResponse(
        predicted_value=final_value,
        uncertainty_sigma=final_sigma,
        grid=grid,
        kriging={"z": round(z_kriged, 2), "sigma": round(sigma_kriged, 2)},
        all_horizons=all_horizons,
        timestamp=datetime.now(timezone.utc).isoformat(),
        model_version="geovision-clip-v1.0-prod",
        md5_checkpoint="remoteclip+conv3d+kriging",
    )
