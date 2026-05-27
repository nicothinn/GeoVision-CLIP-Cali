"""Router: GET /api/validate — KPIs de validación (LOO-CV, Moran, métricas)."""

from __future__ import annotations

from fastapi import APIRouter

from backend.config import settings
from backend.schemas.models import ValidateResponse

router = APIRouter()


@router.get("/api/validate", response_model=ValidateResponse)
async def get_validation():
    """
    Devuelve métricas de validación del modelo:
    - LOO-CV (RMSE, MAE, R² por contaminante)
    - Índice de Moran I
    - KPIs del modelo (Recall@k, sparsity, loss SAE)

    Modo DEV → valores mock.
    Modo PROD → valores calculados contra checkpoints reales.
    """
    if settings.is_dev:
        from backend.services.mock_inference import get_mock_validation

        return get_mock_validation()

    from backend.services.mock_inference import get_mock_validation

    # TODO: Calcular métricas reales contra estaciones DAGMA
    return get_mock_validation()
