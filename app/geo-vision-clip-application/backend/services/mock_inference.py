"""
Servicio mock para MODO DESARROLLO.
Replica los mismos datos aleatorios deterministas que el frontend usa actualmente.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

from backend.schemas.models import (
    GridData,
    Kpis,
    LooCv,
    MetricRow,
    MoranI,
    PredictResponse,
    Station,
    StationReading,
    StationsResponse,
    ValidateResponse,
)
from backend.data.stations import DAGMA_STATIONS

CONTAMINANTS = ["NO2", "SO2", "O3"]
HORIZONS = ["T+1", "T+3", "T+7"]


def _seeded_random(seed: int) -> float:
    """Generador pseudoaleatorio determinista (port del frontend)."""
    s = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
    return (s >> 0) / 0xFFFFFFFF


def _generate_grid(lat: float, lon: float, radius_km: float, seed: int) -> GridData:
    """Genera una grilla NxN alrededor de un punto."""
    step = 0.01
    cells = math.ceil(radius_km / 1.1)
    lats: list[list[float]] = []
    lons: list[list[float]] = []
    values: list[list[float]] = []
    variances: list[list[float]] = []

    for i in range(-cells, cells + 1):
        row_lat: list[float] = []
        row_lon: list[float] = []
        row_val: list[float] = []
        row_var: list[float] = []
        for j in range(-cells, cells + 1):
            dist = math.sqrt(i * i + j * j) / cells if cells > 0 else 0
            s = seed + i * (2 * cells + 1) + j
            r = _seeded_random(s)
            row_lat.append(lat + i * step)
            row_lon.append(lon + j * step)
            row_val.append(round(30 + r * 100 * (1 - dist * 0.5), 1))
            row_var.append(round(2 + r * 15, 1))
        lats.append(row_lat)
        lons.append(row_lon)
        values.append(row_val)
        variances.append(row_var)

    return GridData(lats=lats, lons=lons, values=values, variances=variances)


def get_mock_stations() -> StationsResponse:
    now = datetime.now(timezone.utc).isoformat()
    stations = []
    for i, s in enumerate(DAGMA_STATIONS):
        r = _seeded_random(42 + i * 7)
        stations.append(Station(
            id=s["id"],
            name=s["name"],
            lat=s["lat"],
            lon=s["lon"],
            zone=s["zone"],
            last_reading=StationReading(
                NO2=round(20 + r * 60, 1),
                SO2=round(5 + r * 40, 1),
                O3=round(60 + r * 80, 1),
            ),
            timestamp=now,
        ))
    return StationsResponse(stations=stations)


def get_mock_prediction(
    lat: float,
    lon: float,
    radius_km: float,
    contaminant: str,
    horizon: str,
) -> PredictResponse:
    seed = int(
        round(lat * 100 + lon * 100)
        + CONTAMINANTS.index(contaminant) * 7
        + HORIZONS.index(horizon) * 3
    )
    r1 = _seeded_random(seed + 1)

    predicted_value = round(30 + r1 * 100, 1)
    uncertainty_sigma = round(2 + r1 * 12, 1)

    all_horizons: dict[str, dict[str, float]] = {}
    for h in HORIZONS:
        all_horizons[h] = {}
        for c in CONTAMINANTS:
            s = seed + ord(c[0]) + HORIZONS.index(h)
            r = _seeded_random(s)
            all_horizons[h][c] = round(20 + r * 100, 1)

    return PredictResponse(
        predicted_value=predicted_value,
        uncertainty_sigma=uncertainty_sigma,
        grid=_generate_grid(lat, lon, radius_km, seed + 2),
        all_horizons=all_horizons,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def get_mock_validation() -> ValidateResponse:
    return ValidateResponse(
        loo_cv=LooCv(
            NO2=MetricRow(RMSE=5.2, MAE=3.8, R2=0.71),
            SO2=MetricRow(RMSE=3.1, MAE=2.4, R2=0.68),
            O3=MetricRow(RMSE=8.4, MAE=6.1, R2=0.61),
        ),
        moran_i=MoranI(I=0.41, p_value=0.002),
        kpis=Kpis(
            recall_at_1=0.52,
            recall_at_5=0.79,
            sparsity_sae=0.78,
            loss_sae_recon=0.031,
        ),
    )
