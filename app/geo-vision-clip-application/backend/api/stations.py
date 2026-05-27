"""Router: GET /api/stations — estaciones DAGMA."""

from __future__ import annotations

from fastapi import APIRouter

from backend.config import settings
from backend.schemas.models import StationsResponse

router = APIRouter()


@router.get("/api/stations", response_model=StationsResponse)
async def get_stations():
    """
    Devuelve las 9 estaciones DAGMA con lecturas actuales.

    Modo DEV → lecturas mock.
    Modo PROD → intenta datos reales desde API DAGMA/SISAIRE (o mock si no disponible).
    """
    if settings.is_dev:
        from backend.services.mock_inference import get_mock_stations

        return get_mock_stations()

    from backend.services.mock_inference import get_mock_stations

    # TODO: Integrar API real del DAGMA/SISAIRE cuando esté disponible
    return get_mock_stations()
