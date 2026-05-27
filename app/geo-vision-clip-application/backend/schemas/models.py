"""Pydantic models — contratos exactos que el frontend espera."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ─── Predict ──────────────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    lat: float = Field(..., description="Latitud del punto de consulta")
    lon: float = Field(..., description="Longitud del punto de consulta")
    radius_km: float = Field(default=5, ge=1, le=15, description="Radio en km")
    contaminant: str = Field(default="NO2", pattern=r"^(NO2|SO2|O3)$")
    horizon: str = Field(default="T+1", pattern=r"^(T\+1|T\+3|T\+7)$")


class GridData(BaseModel):
    lats: list[list[float]]
    lons: list[list[float]]
    values: list[list[float]]
    variances: list[list[float]]


class PredictResponse(BaseModel):
    predicted_value: float
    uncertainty_sigma: float
    unit: str = "µg/m³"
    grid: GridData | None = None
    kriging: dict[str, float] | None = None
    all_horizons: dict[str, dict[str, float]]
    timestamp: str
    model_version: str = "geovision-clip-v1.0"
    md5_checkpoint: str = "a3f9c2b1d4e8f70a"


# ─── Stations ─────────────────────────────────────────────────────────────────

class StationReading(BaseModel):
    NO2: float
    SO2: float
    O3: float


class Station(BaseModel):
    id: int
    name: str
    lat: float
    lon: float
    zone: str
    last_reading: StationReading
    timestamp: str


class StationsResponse(BaseModel):
    stations: list[Station]


# ─── Validate ─────────────────────────────────────────────────────────────────

class MetricRow(BaseModel):
    RMSE: float
    MAE: float
    R2: float


class LooCv(BaseModel):
    NO2: MetricRow
    SO2: MetricRow
    O3: MetricRow


class MoranI(BaseModel):
    I: float
    p_value: float


class Kpis(BaseModel):
    recall_at_1: float
    recall_at_5: float
    sparsity_sae: float
    loss_sae_recon: float


class ValidateResponse(BaseModel):
    loo_cv: LooCv
    moran_i: MoranI
    kpis: Kpis


# ─── Download ─────────────────────────────────────────────────────────────────

class DownloadParams(BaseModel):
    lat: float
    lon: float
    contaminant: str
    horizon: str = "T+1"
