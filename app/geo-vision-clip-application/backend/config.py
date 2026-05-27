"""Configuración del backend: modo desarrollo vs producción."""

from __future__ import annotations

import os


class Settings:
    """Configuración global del backend."""

    # ─── Modo ──────────────────────────────────────────────────────────────
    # "dev" → datos mock (sin modelos)
    # "prod" → modelos reales cargados con pre-trained weights
    MODE: str = os.getenv("MODE", "dev").lower()

    # ─── Servidor ──────────────────────────────────────────────────────────
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # ─── CORS ──────────────────────────────────────────────────────────────
    # Orígenes permitidos (frontend Next.js)
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "https://huggingface.co",
        "https://*.hf.space",  # Spaces de HuggingFace
    ]

    # ─── Modelos ───────────────────────────────────────────────────────────
    CHECKPOINT_DIR: str = os.getenv("CHECKPOINT_DIR", "backend/checkpoints")
    DEVICE: str = os.getenv("DEVICE", "cpu")  # "cpu", "cuda", "auto"

    @property
    def is_dev(self) -> bool:
        return self.MODE == "dev"

    @property
    def is_prod(self) -> bool:
        return self.MODE == "prod"


settings = Settings()
