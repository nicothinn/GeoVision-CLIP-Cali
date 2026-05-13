"""Configuracion central del pipeline GeoVision-CLIP Cali.

Define las constantes que comparten todos los scripts del pipeline:
bbox del area de estudio, fechas, proyectos GEE/GCP, bucket destino y
catalogo de fuentes con sus bandas y escala nativa.
"""

from __future__ import annotations

PROJECT_GEE: str = "proyecto3ia-494900"
PROJECT_GCP: str = "proyecto3ia-494900"
BUCKET: str = "geovision-cali"

BBOX: list[float] = [-76.65, 3.3, -76.3, 3.65]

FECHA_INICIO: str = "2019-01-01"
FECHA_FIN: str = "2024-01-01"
FECHA_FIN_INCLUSIVA: str = "2023-12-31"

CRS: str = "EPSG:4326"

DASK_N_WORKERS: int = 4
DASK_THREADS_PER_WORKER: int = 2
DASK_MEMORY_LIMIT: str = "4GB"


FUENTES: dict[str, dict] = {
    "COPERNICUS/S5P/OFFL/L3_NO2": {
        "bandas": [
            "tropospheric_NO2_column_number_density",
            "NO2_column_number_density",
            "cloud_fraction",
        ],
        "escala": 1113,
        "prefijo": "Sentinel5P/NO2",
        "modo": "multibanda",
    },
    "COPERNICUS/S5P/OFFL/L3_SO2": {
        "bandas": [
            "SO2_column_number_density",
            "cloud_fraction",
        ],
        "escala": 1113,
        "prefijo": "Sentinel5P/SO2",
        "modo": "multibanda",
    },
    "COPERNICUS/S5P/OFFL/L3_O3": {
        "bandas": [
            "O3_column_number_density",
            "cloud_fraction",
        ],
        "escala": 1113,
        "prefijo": "Sentinel5P/O3",
        "modo": "multibanda",
    },
    "COPERNICUS/S2_SR_HARMONIZED": {
        "bandas": [
            "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A",
            "B9", "B11", "B12", "SCL",
        ],
        "escala": 10,
        "prefijo": "Sentinel2",
        "modo": "por_banda",
        "dask_n_workers": 2,
        "dask_threads_per_worker": 1,
    },
    "ECMWF/ERA5/HOURLY": {
        "bandas": [
            "temperature_2m",
            "dewpoint_temperature_2m",
            "u_component_of_wind_10m",
            "v_component_of_wind_10m",
            "boundary_layer_height",
            "surface_pressure",
            "total_precipitation",
        ],
        "escala": 27830,
        "prefijo": "ERA-5",
        "modo": "multibanda",
    },
    "MODIS/061/MCD19A2_GRANULES": {
        "bandas": [
            "Optical_Depth_047",
            "Optical_Depth_055",
            "Column_WV",
            "AOD_QA",
        ],
        "escala": 927,
        "prefijo": "MODIS_MCD",
        "modo": "multibanda",
    },
}


def get_fuente(nombre: str) -> dict:
    """Devuelve el dict de configuracion de una fuente, normalizando alias cortos."""
    if nombre in FUENTES:
        return FUENTES[nombre]
    alias = {
        "no2": "COPERNICUS/S5P/OFFL/L3_NO2",
        "so2": "COPERNICUS/S5P/OFFL/L3_SO2",
        "o3": "COPERNICUS/S5P/OFFL/L3_O3",
        "s2": "COPERNICUS/S2_SR_HARMONIZED",
        "sentinel2": "COPERNICUS/S2_SR_HARMONIZED",
        "era5": "ECMWF/ERA5/HOURLY",
        "modis": "MODIS/061/MCD19A2_GRANULES",
    }
    clave = alias.get(nombre.lower())
    if clave is None:
        opciones = ", ".join(list(FUENTES.keys()) + list(alias.keys()))
        raise KeyError(f"Fuente desconocida: {nombre}. Opciones: {opciones}")
    return {**FUENTES[clave], "id": clave}
