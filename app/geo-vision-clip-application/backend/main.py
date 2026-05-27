"""
FastAPI entry point — GeoVision-CLIP Cali Backend.

Modos:
  MODE=dev   → datos mock (no requiere modelos)
  MODE=prod  → modelos reales con pre-trained weights

Uso:
  uvicorn backend.main:app --reload          # modo dev (por defecto)
  MODE=prod uvicorn backend.main:app --reload  # modo producción
"""

from __future__ import annotations

import logging
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("geovision-backend")

# ─── Crear app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="GeoVision-CLIP Cali API",
    description="Backend de predicción geoestadística de contaminantes atmosféricos",
    version="1.0.0",
    docs_url="/docs" if settings.is_dev else None,
    redoc_url="/redoc" if settings.is_dev else None,
)

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Incluir routers ─────────────────────────────────────────────────────────
from backend.api.predict import router as predict_router
from backend.api.stations import router as stations_router
from backend.api.validate import router as validate_router
from backend.api.download import router as download_router

app.include_router(predict_router)
app.include_router(stations_router)
app.include_router(validate_router)
app.include_router(download_router)


# ─── Eventos de ciclo de vida ────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    log.info("=" * 60)
    log.info(f"GeoVision-CLIP Backend — Modo: {settings.MODE.upper()}")
    log.info(f"Dispositivo: {settings.DEVICE}")
    log.info(f"CORS origins: {settings.CORS_ORIGINS}")
    log.info("=" * 60)

    if settings.is_prod:
        log.info("Modo PRODUCCIÓN: cargando modelos...")
        try:
            from backend.services.inference import ModelLoader

            loader = ModelLoader.get_instance()
            loader.load()
            log.info("Modelos cargados exitosamente")
        except Exception as e:
            log.error(f"Error cargando modelos: {e}")
            log.warning("El servidor arrancará pero /predict fallará en modo prod")
    else:
        log.info("Modo DESARROLLO: usando datos mock (sin modelos)")


@app.on_event("shutdown")
async def shutdown():
    log.info("GeoVision-CLIP Backend detenido")


# ─── Health check ────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    """Health check para monitoreo del deployment."""
    from backend.services.inference import ModelLoader

    loader = ModelLoader.get_instance()
    return {
        "status": "ok",
        "mode": settings.MODE,
        "models_loaded": loader.is_loaded(),
        "device": settings.DEVICE,
    }


# ─── Entry point (ejecución directa) ─────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_dev,
    )
