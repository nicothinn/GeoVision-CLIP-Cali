"""Filtrado de warnings ruidosos del pipeline.

Suprime mensajes que ensucian la consola y el log humano sin aportar valor:

1. `_CLOUD_SDK_CREDENTIALS_WARNING` de `google.auth._default`
   ("Your application has authenticated using end user credentials..."):
   se dispara cuando ADC viene de `gcloud auth application-default login`
   sin un `quota project`. La forma "correcta" es ejecutar
   `gcloud auth application-default set-quota-project <PROJECT_ID>`,
   pero en este equipo `gcloud` no esta instalado, asi que silenciamos
   el aviso para mantener limpia la salida.

2. `FutureWarning` de `google.api_core._python_version_support`:
   recordatorio de que Python 3.10 dejara de recibir updates en 2026-10-04.
   Es informativo, no afecta a la corrida.

3. Avisos de deprecacion sobre `pkg_resources` que algunos paquetes
   imprimen en Python 3.10+.

4. Avisos `CE_Warning` de GDAL/libtiff al abrir GeoTIFF multibanda
   ("Warning 1: TIFFReadDirectory: Sum of Photometric type-related color
   channels and ExtraSamples doesn't match SamplesPerPixel..."):
   son ruido inofensivo. Sucede porque los GeoTIFF cientificos de GEE
   traen N bandas sin rol fotografico (R/G/B/alpha), entonces libtiff
   las cataloga como ExtraSamples e imprime el aviso por archivo.
   No afecta a los datos.

Importar este modulo **antes** que `google.auth`, `google.cloud`, `ee`,
`rasterio` y `rioxarray` para que los filtros tomen efecto. La parte de
warnings se propaga a procesos hijos via `PYTHONWARNINGS`.
"""

from __future__ import annotations

import logging
import os
import warnings

_FILTROS_PYTHONWARNINGS = ",".join(
    [
        "ignore:.*end user credentials.*Google Cloud SDK.*:UserWarning",
        "ignore::FutureWarning:google.api_core._python_version_support",
        "ignore::DeprecationWarning:pkg_resources",
    ]
)

os.environ.setdefault("PYTHONWARNINGS", _FILTROS_PYTHONWARNINGS)

os.environ.setdefault("CPL_DEBUG", "OFF")
os.environ.setdefault("GDAL_PAM_ENABLED", "NO")

warnings.filterwarnings(
    "ignore",
    message=".*end user credentials.*Google Cloud SDK.*",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    module=r"google\.api_core\._python_version_support",
)
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    module="pkg_resources.*",
)


class _SoloUnaVez(logging.Filter):
    """Deja pasar cada mensaje a lo sumo una vez en todo el proceso."""

    def __init__(self) -> None:
        super().__init__()
        self._vistos = set()

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            firma = record.getMessage()
        except Exception:
            firma = str(record.msg)
        if firma in self._vistos:
            return False
        self._vistos.add(firma)
        return True


def _silenciar_libtiff(modo: str = "siempre") -> None:
    """Suprime los `CE_Warning` que rasterio reenvia via logging.

    modo='siempre'   -> silencia totalmente (se sigue viendo CE_Failure/Error).
    modo='una_vez'   -> deja pasar cada mensaje unico una sola vez.
    """
    nombres = ("rasterio", "rasterio._env", "rasterio._io")
    if modo == "una_vez":
        filtro = _SoloUnaVez()
        for nombre in nombres:
            lg = logging.getLogger(nombre)
            lg.setLevel(logging.WARNING)
            lg.addFilter(filtro)
    else:
        for nombre in nombres:
            logging.getLogger(nombre).setLevel(logging.ERROR)


_silenciar_libtiff(os.environ.get("PIPELINE_LIBTIFF_WARNINGS", "siempre"))
