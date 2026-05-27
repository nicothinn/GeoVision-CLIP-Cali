"""Router: POST /api/predict — predicción de contaminantes."""

from __future__ import annotations

from fastapi import APIRouter

from backend.config import settings
from backend.schemas.models import PredictRequest, PredictResponse

router = APIRouter()


@router.post("/api/predict", response_model=PredictResponse)
async def predict(body: PredictRequest):
    """
    Recibe un punto (lat, lon), contaminante y horizonte.
    Devuelve valor predicho, incertidumbre y grilla espacial.

    Modo DEV → datos mock deterministas.
    Modo PROD → inferencia real con modelos cargados.
    """
    if settings.is_dev:
        from backend.services.mock_inference import get_mock_prediction

        return get_mock_prediction(
            lat=body.lat,
            lon=body.lon,
            contaminant=body.contaminant,
            horizon=body.horizon,
        )

    from backend.services.inference import run_inference

    return run_inference(
        lat=body.lat,
        lon=body.lon,
        contaminant=body.contaminant,
        horizon=body.horizon,
    )
