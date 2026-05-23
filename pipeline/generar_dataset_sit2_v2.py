"""Construye el dataset de pares imagen-texto para la Situacion 2 (v2).

MEJORAS RESPECTO A V1:
  1.  Score-based class assignment: en vez de if/elif con prioridad fija
      (NO2 siempre gana), asigna a la clase contaminante con MAYOR exceso
      relativo (valor / umbral).  Asi SO2 y O3 no quedan enterrados.
  2.  NDBI como metadato adicional (ademas de BSI), para compatibilidad
      con analisis cruzados del EDA del companero.
  3.  Descripciones mas distintivas entre clases (varian estructura y
      vocabulario) para que el encoder textual pueda discriminar mejor.
  4.  Columnas de diagnostico en metadatos: exceso_NO2, exceso_SO2,
      exceso_O3, ndbi, p90_NO2, p90_SO2, p90_O3.
  5.  Balance tracking mejorado: muestra en cada escena cuantos tiles
      califican para cada clase ANTES de aplicar cap.
  6.  Seed de Python/numpy dentro de construir_dataset para evitar
      interferencias entre corridas.

Uso identico a v1 (PowerShell):
    python pipeline\\generar_dataset_sit2_v2.py ^
        --meta-objetivo 1500 ^
        --max-timestamps-s2 1463 ^
        --max-tiles-por-escena 40 ^
        --stride-pix 32 ^
        --cap-por-clase 300 ^
        --min-por-clase 20 ^
        --paciencia-escenas 30 ^
        --dask-workers 4 ^
        --max-frac-nubes 0.3 ^
        --min-frac-claros 0.1 ^
        --zarr-flush-every 128

Salidas en `dataset_sit2/` (o `--salida-local`):
    tiles.zarr, metadatos.parquet, percentiles.json,
    secuencias.json, resumen.json
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
PARENT = HERE.parent
REPO_ROOT = PARENT.resolve()
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

import silenciar_warnings  # noqa: F401  # side-effect: silencia warnings

import argparse
import json
import math
import os
import random
import re
import shutil
import time
import warnings
from datetime import datetime, timezone
from typing import Any, Iterator

import gcsfs
import numpy as np
import pandas as pd
import xarray as xr
import zarr
from sklearn.model_selection import train_test_split

try:
    from dask import compute, delayed
    _DASK_OK = True
except Exception:
    compute = None
    delayed = None
    _DASK_OK = False

from config import BUCKET, FUENTES, PROJECT_GCP
from trazabilidad import Run, evento

try:
    from google.cloud import storage as gcs_storage
except Exception:
    gcs_storage = None


# =============================================================================
# Constantes
# =============================================================================
SEED = 42
TILE_PIX = 64
PERCENTILES_OBJETIVO = [25, 50, 75, 90, 99]  # sin p95 (por decision del grupo)

CLASES = [
    "contaminacion_alta_NO2",
    "contaminacion_alta_SO2",
    "ozono_anomalo",
    "vegetacion_densa",
    "suelo_urbano",
]

# Bandas S2 desde config
BANDAS_S2 = list(FUENTES["COPERNICUS/S2_SR_HARMONIZED"]["bandas"])  # 13

# Umbrales NDVI/BSI
UMBRAL_NDVI_DENSO = 0.45
UMBRAL_NDVI_SUELO = 0.35
UMBRAL_BSI_SUELO = 0.02

# SCL
_SCL_NUBE_O_DUDOSO: frozenset[int] = frozenset({1, 2, 3, 8, 9, 10, 11})
_SCL_CLARO: frozenset[int] = frozenset({4, 5, 6, 7})

MAX_DT_DIAS = 1


# =============================================================================
# Helpers de I/O (identicos a v1)
# =============================================================================
_gcs_fs: gcsfs.GCSFileSystem | None = None


def _zarr_local_store(ruta: str):
    try:
        return zarr.storage.LocalStore(ruta)
    except AttributeError:
        return zarr.DirectoryStore(ruta)


def _proyecto_gcp() -> str:
    return (
        os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("GCP_PROJECT")
        or PROJECT_GCP
    )


def _get_gcsfs() -> gcsfs.GCSFileSystem:
    global _gcs_fs
    if _gcs_fs is None:
        token = os.environ.get("GCSFS_TOKEN", "google_default")
        _gcs_fs = gcsfs.GCSFileSystem(project=_proyecto_gcp(), token=token)
    return _gcs_fs


def _abrir_zarr(prefijo: str) -> xr.Dataset:
    fs = _get_gcsfs()
    uri = f"{BUCKET}/{prefijo}/panel.zarr"
    mapper = fs.get_mapper(uri)
    try:
        return xr.open_zarr(mapper, consolidated=True)
    except Exception as exc:
        warnings.warn(
            f"open_zarr consolidated=True fallo para {uri} ({exc!r}); reintento.",
            stacklevel=1,
        )
        return xr.open_zarr(mapper, consolidated=False)


_FECHA_RE = re.compile(r"(\d{8})")


def img_id_a_fecha(img_id: str) -> str | None:
    m = _FECHA_RE.search(img_id)
    if not m:
        return None
    raw = m.group(1)
    try:
        return datetime.strptime(raw, "%Y%m%d").date().isoformat()
    except ValueError:
        return None


def _times_a_fechas(times: np.ndarray) -> np.ndarray:
    out: list[str | None] = []
    for t in times:
        out.append(img_id_a_fecha(str(t)))
    return np.array(out, dtype=object)


# =============================================================================
# Percentiles globales sobre S5P (identico a v1)
# =============================================================================
def calcular_percentiles_globales(
    run: Run,
    step_temporal: int = 8,
    step_espacial: int = 2,
    rng: random.Random | None = None,
) -> dict[str, dict[str, float]]:
    rng = rng or random.Random(SEED)
    resultado: dict[str, dict[str, float]] = {}

    fuentes_target = {
        "NO2": "Sentinel5P/NO2",
        "SO2": "Sentinel5P/SO2",
        "O3": "Sentinel5P/O3",
    }
    for nombre, prefijo in fuentes_target.items():
        run.info("Percentiles: abriendo %s ...", prefijo)
        ds = _abrir_zarr(prefijo)
        da = ds["data"]
        n_t = int(da.sizes["time"])
        idx = list(range(0, n_t, max(1, step_temporal)))
        rng.shuffle(idx)
        muestra = da.isel(
            time=idx,
            band=0,
            y=slice(None, None, step_espacial),
            x=slice(None, None, step_espacial),
        ).values.astype("float64")
        muestra = muestra[np.isfinite(muestra)]
        n_finitos = int(muestra.size)
        if nombre in ("NO2", "SO2"):
            muestra_pos = muestra[muestra > 0]
            if muestra_pos.size > 0:
                run.info(
                    "Percentiles %s: usando %d valores >0 (de %d finitos, %.1f%% son 0)",
                    nombre, muestra_pos.size, n_finitos,
                    100 * (1 - muestra_pos.size / max(1, n_finitos)),
                )
                muestra = muestra_pos
        if muestra.size == 0:
            run.warning("Percentiles: %s sin pixeles validos", nombre)
            resultado[nombre] = {f"p{p}": float("nan") for p in PERCENTILES_OBJETIVO}
            continue
        ps = np.percentile(muestra, PERCENTILES_OBJETIVO)
        resultado[nombre] = {f"p{p}": float(v) for p, v in zip(PERCENTILES_OBJETIVO, ps)}
        run.info(
            "Percentiles %s: %s (n_validos=%d)",
            nombre,
            ", ".join(f"p{p}={v:.4g}" for p, v in zip(PERCENTILES_OBJETIVO, ps)),
            int(muestra.size),
        )
        evento("percentiles_calculados", contaminante=nombre, **resultado[nombre], n_pixeles=int(muestra.size))

    return resultado


# =============================================================================
# Indices espectrales (NDVI, BSI, NDBI)
# =============================================================================
_IDX_S2: dict[str, int] = {b: i for i, b in enumerate(BANDAS_S2)}
_IDX_SCL = _IDX_S2.get("SCL", len(BANDAS_S2) - 1)


def metricas_scl(scl: np.ndarray) -> tuple[float, float, float]:
    s = np.rint(scl).astype(np.int16).ravel()
    n = max(1, s.size)
    nodata = int(np.sum(s <= 0))
    nube = int(np.sum(np.isin(s, list(_SCL_NUBE_O_DUDOSO))))
    claro = int(np.sum(np.isin(s, list(_SCL_CLARO))))
    return nube / n, claro / n, nodata / n


def calcular_indices_espectrales(
    tile: np.ndarray,
    mascara_claro: np.ndarray | None = None,
) -> tuple[float, float, float]:
    """Devuelve (NDVI_medio, BSI_medio, NDBI_medio).

    NDBI = (B11 - B8) / (B11 + B8)   — Normalized Difference Built-up Index.
    BSI  = ((B11+B4) - (B8+B2)) / ((B11+B4)+(B8+B2))  — Bare Soil Index.
    NDVI = (B8 - B4) / (B8 + B4).
    """
    eps = 1e-6
    b2 = tile[_IDX_S2["B2"]].astype("float32")
    b4 = tile[_IDX_S2["B4"]].astype("float32")
    b8 = tile[_IDX_S2["B8"]].astype("float32")
    b11 = tile[_IDX_S2["B11"]].astype("float32")

    ndvi = (b8 - b4) / (b8 + b4 + eps)
    bsi = ((b11 + b4) - (b8 + b2)) / ((b11 + b4) + (b8 + b2) + eps)
    ndbi = (b11 - b8) / (b11 + b8 + eps)

    if mascara_claro is not None and np.any(mascara_claro):
        ndvi = ndvi[mascara_claro]
        bsi = bsi[mascara_claro]
        ndbi = ndbi[mascara_claro]

    ndvi = ndvi[np.isfinite(ndvi)]
    bsi = bsi[np.isfinite(bsi)]
    ndbi = ndbi[np.isfinite(ndbi)]

    return (
        float(ndvi.mean()) if ndvi.size else float("nan"),
        float(bsi.mean()) if bsi.size else float("nan"),
        float(ndbi.mean()) if ndbi.size else float("nan"),
    )


_S5P_BUFFER = 2


def _valor_grilla(arr: np.ndarray, yv: np.ndarray, xv: np.ndarray, lat: float, lon: float) -> float:
    if arr.size == 0 or yv.size == 0 or xv.size == 0:
        return float("nan")
    iy = int(np.argmin(np.abs(yv - lat)))
    ix = int(np.argmin(np.abs(xv - lon)))
    H, W = arr.shape
    try:
        v = float(arr[iy, ix])
        if math.isfinite(v):
            return v
    except Exception:
        pass
    y0 = max(0, iy - _S5P_BUFFER)
    y1 = min(H, iy + _S5P_BUFFER + 1)
    x0 = max(0, ix - _S5P_BUFFER)
    x1 = min(W, ix + _S5P_BUFFER + 1)
    patch = arr[y0:y1, x0:x1].ravel()
    validos = patch[np.isfinite(patch)]
    return float(np.median(validos)) if validos.size > 0 else float("nan")


# =============================================================================
# AccesoS5P (identico a v1)
# =============================================================================
class _AccesoS5P:
    def __init__(self, run: Run | None = None) -> None:
        self._run = run
        self._cache: dict[str, dict] = {}

    def _cargar(self, contaminante: str) -> dict:
        if contaminante in self._cache:
            return self._cache[contaminante]
        prefijo = {
            "NO2": "Sentinel5P/NO2",
            "SO2": "Sentinel5P/SO2",
            "O3": "Sentinel5P/O3",
        }[contaminante]
        ds = _abrir_zarr(prefijo)
        da = ds["data"].isel(band=0)
        y_vals = np.asarray(ds["y"].values, dtype="float64")
        x_vals = np.asarray(ds["x"].values, dtype="float64")
        times = np.asarray(ds["time"].values)
        fechas = _times_a_fechas(times)
        fecha_a_indices: dict[str, list[int]] = {}
        for k, f in enumerate(fechas):
            if f is not None:
                fecha_a_indices.setdefault(f, []).append(k)
        if self._run is not None:
            self._run.info("S5P %s cargado: n_time=%d fechas_unicas=%d", contaminante, len(times), len(fecha_a_indices))
        cache = {
            "da": da, "y": y_vals, "x": x_vals,
            "fechas": fechas, "fecha_a_indices": fecha_a_indices,
            "fechas_lista": sorted(fecha_a_indices.keys()),
        }
        self._cache[contaminante] = cache
        return cache

    @staticmethod
    def _fechas_en_ventana(objetivo: str, fechas: list[str], max_dt_dias: int = MAX_DT_DIAS) -> list[str]:
        t0 = datetime.strptime(objetivo, "%Y-%m-%d").date()
        resultado: list[str] = []
        for f in fechas:
            tf = datetime.strptime(f, "%Y-%m-%d").date()
            if abs((tf - t0).days) <= max_dt_dias:
                resultado.append(f)
        return resultado

    def mapas_2d_para_fecha(self, fecha_s2: str) -> dict[str, dict[str, np.ndarray | str]] | None:
        resultado: dict[str, dict[str, np.ndarray | str]] = {}
        for nom in ("NO2", "SO2", "O3"):
            c = self._cargar(nom)
            fechas_ventana = self._fechas_en_ventana(fecha_s2, c["fechas_lista"])
            if not fechas_ventana:
                return None
            all_t_idx: list[int] = []
            for f in fechas_ventana:
                all_t_idx.extend(c["fecha_a_indices"][f])
            stack = np.asarray(c["da"].isel(time=all_t_idx).values, dtype=np.float64)
            stack[stack == 0] = np.nan
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                arr_agg = np.nanmax(stack, axis=0)
            resultado[nom] = {
                "fecha": fechas_ventana[0],
                "arr": arr_agg,
                "y": np.asarray(c["y"], dtype=np.float64),
                "x": np.asarray(c["x"], dtype=np.float64),
                "n_orbitas": len(all_t_idx),
            }
        return resultado

    def valor(self, contaminante: str, lat: float, lon: float, fecha: str) -> float:
        c = self._cargar(contaminante)
        fechas_ventana = self._fechas_en_ventana(fecha, c["fechas_lista"])
        if not fechas_ventana:
            return float("nan")
        all_t_idx: list[int] = []
        for f in fechas_ventana:
            all_t_idx.extend(c["fecha_a_indices"][f])
        iy = int(np.argmin(np.abs(c["y"] - lat)))
        ix = int(np.argmin(np.abs(c["x"] - lon)))
        try:
            vals = np.asarray(c["da"].isel(time=all_t_idx, y=iy, x=ix).values, dtype="float64")
            vals = vals[np.isfinite(vals) & (vals != 0)]
            if vals.size > 0:
                return float(np.max(vals))
        except Exception:
            pass
        return float("nan")


# =============================================================================
# Asignacion de clase semi-supervisada — VERSION MEJORADA (score-based)
# =============================================================================
def _p(percentiles: dict, contaminante: str, nivel: str) -> float:
    try:
        return float(percentiles[contaminante][nivel])
    except (KeyError, TypeError):
        return float("nan")


def asignar_clase_score_based(
    no2: float,
    so2: float,
    o3: float,
    ndvi: float,
    bsi: float,
    ndbi: float,
    percentiles: dict[str, dict[str, float]],
    frac_built_up: float = 0.0,
) -> tuple[str | None, dict[str, float]]:
    """Asigna clase segun el contaminante con MAYOR exceso relativo.

    En vez de if/elif con prioridad fija (NO2 > SO2 > O3), calcula
    cuantas veces cada contaminante supera su umbral percentil.
    El tile va a la clase con el score mas alto.

    Retorna (clase, dict_scores) donde dict_scores tiene los scores
    de cada contaminante para diagnostico.

    Si ningun contaminante supera su umbral, evalua vegetacion y
    suelo urbano con las reglas clasicas.
    """
    p90_no2 = _p(percentiles, "NO2", "p90")
    p90_so2 = _p(percentiles, "SO2", "p90")
    p99_so2 = _p(percentiles, "SO2", "p99")
    p90_o3 = _p(percentiles, "O3", "p90")
    p25_o3 = _p(percentiles, "O3", "p25")

    umbral_so2 = p90_so2 if (math.isfinite(p90_so2) and p90_so2 > 0) else p99_so2

    # Calcular scores de exceso para cada contaminante
    scores: dict[str, float] = {}

    if math.isfinite(no2) and no2 > 0 and math.isfinite(p90_no2) and p90_no2 > 0:
        scores["NO2"] = no2 / p90_no2
    else:
        scores["NO2"] = 0.0

    if math.isfinite(so2) and so2 > 0 and math.isfinite(umbral_so2) and umbral_so2 > 0:
        scores["SO2"] = so2 / umbral_so2
    else:
        scores["SO2"] = 0.0

    if math.isfinite(o3):
        # Para O3, score es el maximo entre exceso alto y deficit bajo
        score_o3_alto = (o3 / p90_o3) if (math.isfinite(p90_o3) and p90_o3 > 0) else 0.0
        score_o3_bajo = (p25_o3 / o3) if (math.isfinite(p25_o3) and p25_o3 > 0 and o3 > 0) else 0.0
        scores["O3"] = max(score_o3_alto, score_o3_bajo)
        # Solo cuenta si realmente supera el umbral correspondiente
        o3_califica = (math.isfinite(p90_o3) and o3 >= p90_o3) or (math.isfinite(p25_o3) and o3 <= p25_o3)
        if not o3_califica:
            scores["O3"] = 0.0
    else:
        scores["O3"] = 0.0

    # Encontrar el contaminante con mayor score > 1.0
    mejor_cont = max(scores, key=scores.__getitem__)  # type: ignore[arg-type]
    if scores[mejor_cont] > 1.0:
        clase_cont = {
            "NO2": "contaminacion_alta_NO2",
            "SO2": "contaminacion_alta_SO2",
            "O3": "ozono_anomalo",
        }[mejor_cont]
        return clase_cont, scores

    # Si ningun contaminante pasa: evaluar vegetacion / suelo
    if math.isfinite(ndvi) and ndvi >= UMBRAL_NDVI_DENSO:
        if not (math.isfinite(frac_built_up) and frac_built_up >= 0.15):
            return "vegetacion_densa", scores

    if (
        math.isfinite(ndvi) and ndvi <= UMBRAL_NDVI_SUELO
        and math.isfinite(bsi) and bsi >= UMBRAL_BSI_SUELO
    ):
        return "suelo_urbano", scores

    if math.isfinite(frac_built_up) and frac_built_up >= 0.15:
        return "suelo_urbano", scores

    return None, scores


# =============================================================================
# Descripcion mejorada — mas distintiva entre clases
# =============================================================================
_DESCRIPCIONES = {
    "contaminacion_alta_NO2": (
        "Imagen satelital Sentinel-2 del area metropolitana de Cali que muestra "
        "un foco de alta concentracion de dioxido de nitrogeno troposferico, "
        "asociado a emisiones vehiculares e industriales en zonas urbanas densas."
    ),
    "contaminacion_alta_SO2": (
        "Escena Sentinel-2 en los alrededores de Cali con nivel elevado de "
        "dioxido de azufre en la troposfera, tipicamente vinculado a actividad "
        "industrial, refinerias o procesos de combustion de combustible fosil."
    ),
    "ozono_anomalo": (
        "Tile de Sentinel-2 sobre Cali donde la columna de ozono troposferico "
        "presenta un valor atipico, ya sea por formacion fotoquimica en epocas "
        "de alta radiacion solar o por condiciones meteorologicas particulares."
    ),
    "vegetacion_densa": (
        "Parche de Sentinel-2 con cubierta vegetal densa y saludable en la region "
        "de Cali, con bajos niveles de contaminacion atmosferica. Predominan areas "
        "verdes, cultivos o cobertura boscosa."
    ),
    "suelo_urbano": (
        "Fragmento de Sentinel-2 correspondiente a zona urbana o suelo expuesto "
        "en Cali, con alta reflectancia en el infrarrojo de onda corta y escasa "
        "vegetacion. Incluye infraestructura gris y lotes sin cobertura vegetal."
    ),
}


def generar_descripcion_v2(
    clase: str,
    no2: float,
    so2: float,
    o3: float,
    ndvi: float,
    bsi: float,
    ndbi: float,
    fecha: str,
    lat: float,
    lon: float,
) -> str:
    base = _DESCRIPCIONES[clase]
    return (
        f"{base} "
        f"Coordenadas ({lat:.4f}N, {lon:.4f}O), fecha {fecha}. "
        f"Indices: NDVI={ndvi:.2f}, BSI={bsi:.2f}, NDBI={ndbi:.2f}. "
        f"Concentraciones: NO2={no2:.2e}, SO2={so2:.2e}, O3={o3:.2e}."
    )


# =============================================================================
# Procesamiento de tiles
# =============================================================================
def _tile_a_int16(tile: np.ndarray) -> np.ndarray:
    t = np.where(np.isfinite(tile), tile, 0.0)
    t = np.clip(t, -32768, 32767)
    return t.astype("int16")


def _mascara_claro_scl(scl_hw: np.ndarray) -> np.ndarray:
    s = np.rint(scl_hw).astype(np.int16)
    return np.isin(s, list(_SCL_CLARO))


def _procesar_tile_candidato_v2(
    tile: np.ndarray,
    yi: int,
    xi: int,
    cy: float,
    cx: float,
    img_id: str,
    fecha: str,
    valid_ratio: float,
    max_frac_nubes: float,
    min_frac_claros: float,
    usar_filtro_scl: bool,
    percentiles: dict[str, dict[str, float]],
    no2_arr: np.ndarray,
    y_no2: np.ndarray,
    x_no2: np.ndarray,
    so2_arr: np.ndarray,
    y_so2: np.ndarray,
    x_so2: np.ndarray,
    o3_arr: np.ndarray,
    y_o3: np.ndarray,
    x_o3: np.ndarray,
) -> dict[str, object] | None:
    scl = tile[_IDX_SCL]
    frac_nube, frac_claro, frac_nd = metricas_scl(scl)
    scl_int = np.rint(scl).astype(np.int16)
    frac_built_up = float(np.sum((scl_int == 5) | (scl_int == 6))) / max(1, scl_int.size)

    if usar_filtro_scl:
        if frac_nube > max_frac_nubes or frac_claro < min_frac_claros:
            return None
        masc = _mascara_claro_scl(scl)
        mask = masc if np.any(masc) else None
        ndvi, bsi, ndbi = calcular_indices_espectrales(tile, mask)
    else:
        ndvi, bsi, ndbi = calcular_indices_espectrales(tile, None)

    no2 = _valor_grilla(no2_arr, y_no2, x_no2, cy, cx)
    so2 = _valor_grilla(so2_arr, y_so2, x_so2, cy, cx)
    o3 = _valor_grilla(o3_arr, y_o3, x_o3, cy, cx)

    clase, scores = asignar_clase_score_based(no2, so2, o3, ndvi, bsi, ndbi, percentiles, frac_built_up)
    if clase is None:
        return None

    # Referencias de percentiles para diagnostico
    p90_no2 = _p(percentiles, "NO2", "p90")
    p90_so2 = _p(percentiles, "SO2", "p90")
    p90_o3 = _p(percentiles, "O3", "p90")

    tile_id = f"{img_id}__y{yi:04d}__x{xi:04d}"
    descripcion = generar_descripcion_v2(clase, no2, so2, o3, ndvi, bsi, ndbi, fecha, cy, cx)

    return {
        "record": {
            "tile_id": tile_id,
            "clase": clase,
            "descripcion": descripcion,
            "fecha": fecha,
            "img_id_s2": img_id,
            "centroide_lat": cy,
            "centroide_lon": cx,
            "yi": yi,
            "xi": xi,
            "valid_ratio": valid_ratio,
            "frac_nubes_scl": frac_nube,
            "frac_claros_scl": frac_claro,
            "frac_nodata_scl": frac_nd,
            "frac_built_up": frac_built_up,
            "ndvi": ndvi,
            "bsi": bsi,
            "ndbi": ndbi,
            "no2": no2,
            "so2": so2,
            "o3": o3,
            # Scores de exceso para diagnostico
            "exceso_NO2": round(scores.get("NO2", 0.0), 4),
            "exceso_SO2": round(scores.get("SO2", 0.0), 4),
            "exceso_O3": round(scores.get("O3", 0.0), 4),
            # Umbrales de referencia
            "p90_NO2": p90_no2 if math.isfinite(p90_no2) else None,
            "p90_SO2": p90_so2 if math.isfinite(p90_so2) else None,
            "p90_O3": p90_o3 if math.isfinite(p90_o3) else None,
        },
        "tile_i16": _tile_a_int16(tile),
    }


# =============================================================================
# Escritura incremental de tiles.zarr (identico a v1)
# =============================================================================
class IncrementalTilesZarr:
    def __init__(self, path: Path, flush_every: int) -> None:
        self.path = path
        self.flush_every = max(1, int(flush_every))
        self.z: zarr.Array | None = None
        self._n: int = 0
        self._buf: list[np.ndarray] = []

    def _append_batch(self, batch: np.ndarray) -> None:
        if batch.size == 0:
            return
        n0 = self._n
        n1 = n0 + int(batch.shape[0])
        if self.z is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.exists():
                shutil.rmtree(self.path, ignore_errors=True)
            store = _zarr_local_store(str(self.path))
            self.z = zarr.zeros(
                shape=(n1, batch.shape[1], batch.shape[2], batch.shape[3]),
                chunks=(min(64, self.flush_every), batch.shape[1], batch.shape[2], batch.shape[3]),
                dtype="int16",
                store=store,
            )
            self.z[:] = batch
        else:
            self.z.resize((n1, batch.shape[1], batch.shape[2], batch.shape[3]))
            self.z[n0:n1] = batch
        self._n = n1

    def push(self, tile_i16: np.ndarray) -> None:
        self._buf.append(tile_i16)
        if len(self._buf) >= self.flush_every:
            self.flush()

    def flush(self) -> None:
        if not self._buf:
            return
        batch = np.stack(self._buf, axis=0)
        self._buf.clear()
        self._append_batch(batch)

    def finalize_attrs(self, tile_ids: list[str]) -> None:
        self.flush()
        if self.z is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.exists():
                shutil.rmtree(self.path, ignore_errors=True)
            store = _zarr_local_store(str(self.path))
            self.z = zarr.zeros(
                shape=(0, len(BANDAS_S2), TILE_PIX, TILE_PIX),
                chunks=(64, len(BANDAS_S2), TILE_PIX, TILE_PIX),
                dtype="int16",
                store=store,
            )
        self.z.attrs["bandas"] = BANDAS_S2
        self.z.attrs["tile_pix"] = TILE_PIX
        self.z.attrs["tile_ids"] = tile_ids


# =============================================================================
# Iteracion sobre tiles de una escena S2
# =============================================================================
def iter_tiles_escena(
    cubo_escena: np.ndarray,
    y_vals: np.ndarray,
    x_vals: np.ndarray,
    tile_pix: int,
    stride_pix: int,
    max_tiles: int,
    rng: random.Random,
) -> Iterator[dict]:
    _, H, W = cubo_escena.shape
    if H < tile_pix or W < tile_pix:
        return
    ys = list(range(0, H - tile_pix + 1, stride_pix))
    xs = list(range(0, W - tile_pix + 1, stride_pix))
    coords = [(yi, xi) for yi in ys for xi in xs]
    rng.shuffle(coords)
    coords = coords[:max_tiles]

    for yi, xi in coords:
        tile = cubo_escena[:, yi : yi + tile_pix, xi : xi + tile_pix]
        if not np.isfinite(tile).any():
            continue
        valid_ratio = float(np.isfinite(tile).mean())
        if valid_ratio < 0.5:
            continue
        cy = float(y_vals[yi + tile_pix // 2])
        cx = float(x_vals[xi + tile_pix // 2])
        yield {
            "tile": tile.astype("float32"),
            "yi": int(yi),
            "xi": int(xi),
            "centroide_lat": cy,
            "centroide_lon": cx,
            "valid_ratio": valid_ratio,
        }


# =============================================================================
# Construccion del dataset (v2)
# =============================================================================
def construir_dataset_v2(
    args: argparse.Namespace,
    percentiles: dict,
    run: Run,
) -> tuple[pd.DataFrame, np.ndarray | None]:
    """Version mejorada: score-based class assignment + NDBI + descripciones
    distintivas + columnas de diagnostico."""
    rng = random.Random(SEED)
    s5p = _AccesoS5P(run=run)
    usar_filtro_scl = not getattr(args, "sin_filtro_scl", False)
    usar_dask = _DASK_OK and getattr(args, "dask_workers", 0) > 0
    if getattr(args, "dask_workers", 0) > 0 and not _DASK_OK:
        run.warning("dask no instalado; procesamiento de tiles en serie.")

    tiles_zarr_path = Path(args.salida_local) / "tiles.zarr"
    z_writer = IncrementalTilesZarr(tiles_zarr_path, flush_every=getattr(args, "zarr_flush_every", 128))

    run.info("Abriendo Sentinel-2 ...")
    ds_s2 = _abrir_zarr(FUENTES["COPERNICUS/S2_SR_HARMONIZED"]["prefijo"])
    da_s2 = ds_s2["data"]
    n_t = int(da_s2.sizes["time"])
    y_vals = np.asarray(ds_s2["y"].values, dtype="float64")
    x_vals = np.asarray(ds_s2["x"].values, dtype="float64")
    times = np.asarray(ds_s2["time"].values)
    fechas_s2 = _times_a_fechas(times)

    idxs_t = list(range(n_t))
    rng.shuffle(idxs_t)
    idxs_t = idxs_t[: args.max_timestamps_s2]
    run.info("Escenas S2 a procesar: %d / %d (max_timestamps_s2=%d)", len(idxs_t), n_t, args.max_timestamps_s2)

    conteo: dict[str, int] = {c: 0 for c in CLASES}
    registros: list[dict] = []
    escenas_sin_aporte = 0
    t0_global = time.perf_counter()
    log_clave = {
        "contaminacion_alta_NO2": "N2",
        "contaminacion_alta_SO2": "S2",
        "ozono_anomalo": "O3",
        "vegetacion_densa": "veg",
        "suelo_urbano": "sue",
    }

    for ord_idx, t_idx in enumerate(idxs_t):
        fecha = fechas_s2[t_idx]
        img_id = str(times[t_idx])
        if fecha is None:
            continue

        if len(registros) >= args.meta_objetivo and all(conteo[c] >= args.min_por_clase for c in CLASES):
            run.info("Meta y minimos cumplidos. Cortando.")
            break

        if escenas_sin_aporte >= args.paciencia_escenas:
            run.warning("Paciencia agotada: %d escenas seguidas sin aporte. Cortando.", escenas_sin_aporte)
            break

        cubo_escena = da_s2.isel(time=t_idx).values
        if cubo_escena.ndim != 3:
            continue

        mapas = s5p.mapas_2d_para_fecha(fecha)
        if mapas is None:
            escenas_sin_aporte += 1
            if (ord_idx + 1) % 10 == 0 or ord_idx == len(idxs_t) - 1:
                run.info("Escena %d/%d (fecha=%s) sin mapas S5P | pares=%d | %.1fs",
                         ord_idx + 1, len(idxs_t), fecha, len(registros), time.perf_counter() - t0_global)
            continue

        no2_m = mapas["NO2"]["arr"]
        y_no2 = mapas["NO2"]["y"]
        x_no2 = mapas["NO2"]["x"]
        so2_m = mapas["SO2"]["arr"]
        y_so2 = mapas["SO2"]["y"]
        x_so2 = mapas["SO2"]["x"]
        o3_m = mapas["O3"]["arr"]
        y_o3 = mapas["O3"]["y"]
        x_o3 = mapas["O3"]["x"]

        candidatos = list(
            iter_tiles_escena(cubo_escena, y_vals, x_vals,
                              tile_pix=TILE_PIX, stride_pix=args.stride_pix,
                              max_tiles=args.max_tiles_por_escena, rng=rng)
        )

        def _evaluar_uno(ti: dict) -> dict[str, object] | None:
            return _procesar_tile_candidato_v2(
                ti["tile"], ti["yi"], ti["xi"],
                ti["centroide_lat"], ti["centroide_lon"],
                img_id, fecha, ti["valid_ratio"],
                args.max_frac_nubes, args.min_frac_claros,
                usar_filtro_scl, percentiles,
                no2_m, y_no2, x_no2,
                so2_m, y_so2, x_so2,
                o3_m, y_o3, x_o3,
            )

        resultados: list[dict[str, object] | None] = []
        if usar_dask and delayed is not None and compute is not None:
            chunk = max(1, int(getattr(args, "dask_chunk_tiles", 16)))
            for i0 in range(0, len(candidatos), chunk):
                bloque = candidatos[i0: i0 + chunk]
                tareas = [delayed(_evaluar_uno)(ti) for ti in bloque]
                resultados.extend(compute(*tareas, scheduler="threads", num_workers=int(args.dask_workers)))
        else:
            for ti in candidatos:
                resultados.append(_evaluar_uno(ti))

        # --- Diagnostico: cuantos tiles califican para cada clase ANTES del cap ---
        conteo_pre_cap: dict[str, int] = {c: 0 for c in CLASES}
        for res in resultados:
            if res is not None:
                c = str(res["record"]["clase"])
                if c in conteo_pre_cap:
                    conteo_pre_cap[c] += 1

        aporte_escena = 0
        cortar_meta = False
        for res in resultados:
            if res is None:
                continue
            rec = res["record"]
            clase = str(rec["clase"])
            if conteo[clase] >= args.cap_por_clase:
                continue
            if len(registros) >= args.meta_objetivo and all(conteo[c] >= args.min_por_clase for c in CLASES):
                cortar_meta = True
                break
            registros.append(rec)
            z_writer.push(res["tile_i16"])
            conteo[clase] += 1
            aporte_escena += 1

        if cortar_meta:
            run.info("Meta y minimos cumplidos (dentro de escena). Cortando.")
            break

        if aporte_escena == 0:
            escenas_sin_aporte += 1
        else:
            escenas_sin_aporte = 0

        if (ord_idx + 1) % 10 == 0 or ord_idx == len(idxs_t) - 1:
            dt = time.perf_counter() - t0_global
            run.info(
                "Escena %d/%d (fecha=%s) | pre-cap: %s | pares=%d (%s) | %.1fs",
                ord_idx + 1, len(idxs_t), fecha,
                ", ".join(f"{k}={conteo_pre_cap[k]}" for k in CLASES),
                len(registros),
                ", ".join(f"{log_clave[c]}={conteo[c]}" for c in CLASES),
                dt,
            )
            evento("progreso_construccion", ord_idx=ord_idx + 1, fecha=fecha,
                   pares=len(registros), conteo=dict(conteo), duracion_s=round(dt, 2))

    run.info("Construccion terminada: %d pares. Balance: %s",
             len(registros), ", ".join(f"{c}={conteo[c]}" for c in CLASES))
    evento("construccion_fin", pares=len(registros), conteo=dict(conteo))

    df = pd.DataFrame(registros)
    ids = df["tile_id"].tolist() if not df.empty else []
    z_writer.finalize_attrs(ids)
    return df, None


# =============================================================================
# Split estratificado (identico a v1)
# =============================================================================
def split_estratificado(df: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    if df.empty:
        out = df.copy()
        out["split"] = pd.Series(index=out.index, dtype="string")
        return out

    try:
        train_idx, temp_idx = train_test_split(df.index, test_size=0.30, stratify=df["clase"], random_state=seed)
    except ValueError:
        train_idx, temp_idx = train_test_split(df.index, test_size=0.30, random_state=seed)

    df_temp = df.loc[temp_idx]
    try:
        val_idx, test_idx = train_test_split(df_temp.index, test_size=0.50, stratify=df_temp["clase"], random_state=seed)
    except ValueError:
        val_idx, test_idx = train_test_split(df_temp.index, test_size=0.50, random_state=seed)

    asign = pd.Series("train", index=df.index)
    asign.loc[val_idx] = "val"
    asign.loc[test_idx] = "test"
    df = df.copy()
    df["split"] = asign.values
    return df


# =============================================================================
# Secuencias temporales (identico a v1)
# =============================================================================
def generar_secuencias_temporales(
    df: pd.DataFrame,
    n_secuencias: int,
    longitud: int,
    seed: int = SEED,
    cell_deg: float = 0.10,
    max_gap_dias: int = 90,
) -> list[dict]:
    if df.empty:
        return []

    rng = random.Random(seed)
    df_ord = df.copy()
    df_ord["fecha_dt"] = pd.to_datetime(df_ord["fecha"])
    df_ord["celda_lat"] = (df_ord["centroide_lat"] / cell_deg).round() * cell_deg
    df_ord["celda_lon"] = (df_ord["centroide_lon"] / cell_deg).round() * cell_deg

    secuencias: list[dict] = []
    usados: set[str] = set()
    grupos = list(df_ord.groupby(["celda_lat", "celda_lon"]))
    rng.shuffle(grupos)

    for (clat, clon), g in grupos:
        if len(secuencias) >= n_secuencias:
            break
        g = g[~g["tile_id"].isin(usados)]
        g = g.sort_values("fecha_dt").drop_duplicates("fecha_dt")
        if len(g) < longitud:
            continue
        fechas_dt = g["fecha_dt"].tolist()
        ids_list = g["tile_id"].tolist()
        for i in range(len(fechas_dt) - longitud + 1):
            ventana_fechas = fechas_dt[i: i + longitud]
            ok = True
            for j in range(1, longitud):
                gap = (ventana_fechas[j] - ventana_fechas[j - 1]).days
                if gap > max_gap_dias or gap < 1:
                    ok = False
                    break
            if not ok:
                continue
            ventana_ids = ids_list[i: i + longitud]
            if any(tid in usados for tid in ventana_ids):
                continue
            secuencias.append({
                "celda_lat": float(clat), "celda_lon": float(clon),
                "longitud": longitud, "tile_ids": ventana_ids,
                "fechas": [f.isoformat()[:10] for f in ventana_fechas],
            })
            usados.update(ventana_ids)
            if len(secuencias) >= n_secuencias:
                break
    return secuencias


# =============================================================================
# Persistencia local (identico a v1, salvo que incluye nuevas columnas)
# =============================================================================
def guardar_dataset_local(
    df: pd.DataFrame,
    tiles: np.ndarray | None,
    percentiles: dict,
    secuencias: list[dict],
    salida_dir: Path,
    run: Run,
) -> dict:
    salida_dir.mkdir(parents=True, exist_ok=True)

    meta_path = salida_dir / "metadatos.parquet"
    try:
        df.to_parquet(meta_path, index=False)
    except Exception as exc:
        run.warning("Fallback a CSV (no pyarrow: %s)", exc)
        meta_path = salida_dir / "metadatos.csv"
        df.to_csv(meta_path, index=False)

    tiles_path = salida_dir / "tiles.zarr"
    incremental_ok = False
    if tiles is None and tiles_path.exists():
        nz = int(zarr.open(str(tiles_path), mode="r").shape[0])
        if nz == len(df):
            incremental_ok = True
        else:
            run.warning("tiles.zarr tiene %d filas pero metadatos %d.", nz, len(df))
    if incremental_ok:
        run.info("tiles.zarr ya escrito incrementalmente (n=%d).", len(df))
    elif tiles is not None and tiles.size > 0:
        if tiles_path.exists():
            for p in tiles_path.rglob("*"):
                if p.is_file():
                    p.unlink()
            try:
                tiles_path.rmdir()
            except OSError:
                pass
        z = zarr.open(str(tiles_path), mode="w",
                      shape=tiles.shape,
                      chunks=(min(64, max(1, tiles.shape[0])), tiles.shape[1], tiles.shape[2], tiles.shape[3]),
                      dtype="int16")
        z[:] = tiles
        z.attrs["bandas"] = BANDAS_S2
        z.attrs["tile_pix"] = TILE_PIX
        z.attrs["tile_ids"] = df["tile_id"].tolist()
    else:
        if tiles_path.exists():
            for p in tiles_path.rglob("*"):
                if p.is_file():
                    p.unlink()
            try:
                tiles_path.rmdir()
            except OSError:
                pass
        z = zarr.open(str(tiles_path), mode="w",
                      shape=(0, len(BANDAS_S2), TILE_PIX, TILE_PIX),
                      chunks=(64, len(BANDAS_S2), TILE_PIX, TILE_PIX),
                      dtype="int16")
        z.attrs["bandas"] = BANDAS_S2
        z.attrs["tile_pix"] = TILE_PIX
        z.attrs["tile_ids"] = []

    (salida_dir / "percentiles.json").write_text(json.dumps(percentiles, indent=2, ensure_ascii=False), encoding="utf-8")
    (salida_dir / "secuencias.json").write_text(json.dumps(secuencias, indent=2, ensure_ascii=False), encoding="utf-8")

    balance: dict[str, dict[str, int]] = {}
    if not df.empty:
        for split in ("train", "val", "test"):
            sub = df[df["split"] == split]
            balance[split] = {c: int((sub["clase"] == c).sum()) for c in CLASES}
            balance[split]["_total"] = int(len(sub))
    resumen = {
        "generado_utc": datetime.now(timezone.utc).isoformat(),
        "n_pares": int(len(df)),
        "n_secuencias": len(secuencias),
        "clases": CLASES,
        "tile_pix": TILE_PIX,
        "bandas_s2": BANDAS_S2,
        "percentiles": percentiles,
        "balance_por_split": balance,
        "balance_global": {c: int((df["clase"] == c).sum()) for c in CLASES} if not df.empty else {},
        "version": "v2",
        "cambios_v2": [
            "Score-based class assignment (en vez de if/elif con prioridad fija)",
            "NDBI agregado como metadato",
            "Descripciones mas distintivas entre clases",
            "Columnas de diagnostico: exceso_NO2, exceso_SO2, exceso_O3, ndbi, p90_*",
            "Balance tracking pre-cap por escena",
        ],
    }
    (salida_dir / "resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    run.info("Dataset v2 guardado en %s", salida_dir)
    evento("dataset_guardado_v2", ruta=str(salida_dir), n_pares=int(len(df)))
    return resumen


# =============================================================================
# Subida a GCS (opcional, identico a v1)
# =============================================================================
def subir_dataset_gcs(salida_dir: Path, prefijo_gcs: str, run: Run) -> None:
    if gcs_storage is None:
        run.warning("google-cloud-storage no disponible; omito subida a GCS")
        return
    cliente = gcs_storage.Client(project=_proyecto_gcp())
    bucket = cliente.bucket(BUCKET)
    n = 0
    for p in salida_dir.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(salida_dir).as_posix()
        blob = bucket.blob(f"{prefijo_gcs}/{rel}")
        blob.upload_from_filename(str(p))
        n += 1
    run.info("Subidos %d archivos a gs://%s/%s/", n, BUCKET, prefijo_gcs)
    evento("dataset_subido_gcs", prefijo=prefijo_gcs, n_archivos=n)


# =============================================================================
# CLI
# =============================================================================
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Construye dataset Sit 2 v2 (score-based).")
    parser.add_argument("--meta-objetivo", type=int, default=1500, help="Total minimo de pares.")
    parser.add_argument("--max-timestamps-s2", type=int, default=1463, help="Max escenas S2.")
    parser.add_argument("--max-tiles-por-escena", type=int, default=40, help="Tiles candidatos por escena.")
    parser.add_argument("--stride-pix", type=int, default=32, help="Stride en pixeles entre tiles.")
    parser.add_argument("--cap-por-clase", type=int, default=300, help="Cota superior por clase.")
    parser.add_argument("--min-por-clase", type=int, default=20, help="Cota inferior por clase.")
    parser.add_argument("--paciencia-escenas", type=int, default=80, help="Escenas sin aporte para cortar.")
    parser.add_argument("--solo-percentiles", action="store_true", help="Solo percentiles.")
    parser.add_argument("--n-secuencias", type=int, default=30, help="Minimo de secuencias temporales.")
    parser.add_argument("--longitud-secuencia", type=int, default=8, help="Largo de cada secuencia.")
    parser.add_argument("--salida-local", type=Path, default=REPO_ROOT / "dataset_sit2",
                        help="Directorio de salida.")
    parser.add_argument("--subir-a-gcs", action="store_true", help="Subir a GCS al terminar.")
    parser.add_argument("--prefijo-gcs", default="datasets/sit2_v2", help="Prefijo GCS.")
    parser.add_argument("--dask-workers", type=int, default=0, help="Hilos Dask (0=serie).")
    parser.add_argument("--dask-chunk-tiles", type=int, default=16, help="Bloque de tiles para Dask.")
    parser.add_argument("--zarr-flush-every", type=int, default=128, help="Cada cuantos tiles flush a disco.")
    parser.add_argument("--max-frac-nubes", type=float, default=0.30, help="Max fraccion nubes SCL.")
    parser.add_argument("--min-frac-claros", type=float, default=0.10, help="Min fraccion claros SCL.")
    parser.add_argument("--sin-filtro-scl", action="store_true", help="Desactivar filtro SCL.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    random.seed(SEED)
    np.random.seed(SEED)

    nombre_run = "dataset_sit2_v2"
    contexto = {
        "meta_objetivo": args.meta_objetivo,
        "max_timestamps_s2": args.max_timestamps_s2,
        "max_tiles_por_escena": args.max_tiles_por_escena,
        "stride_pix": args.stride_pix,
        "cap_por_clase": args.cap_por_clase,
        "min_por_clase": args.min_por_clase,
        "paciencia_escenas": args.paciencia_escenas,
        "seed": SEED,
        "dask_workers": args.dask_workers,
        "zarr_flush_every": args.zarr_flush_every,
        "max_frac_nubes": args.max_frac_nubes,
        "min_frac_claros": args.min_frac_claros,
        "sin_filtro_scl": args.sin_filtro_scl,
        "version": "v2",
    }
    runs_root = REPO_ROOT / "runs"
    with Run(nombre_run, contexto=contexto, root=runs_root) as run:
        run.info("=== %s ===", nombre_run)
        run.info("REPO_ROOT=%s cwd=%s", REPO_ROOT, Path.cwd())
        run.info("Argumentos: %s", contexto)

        with run.medir("percentiles_globales"):
            percentiles = calcular_percentiles_globales(run)

        salida = args.salida_local
        salida.mkdir(parents=True, exist_ok=True)
        (salida / "percentiles.json").write_text(json.dumps(percentiles, indent=2, ensure_ascii=False), encoding="utf-8")
        run.info("Percentiles escritos en %s/percentiles.json", salida)

        if args.solo_percentiles:
            run.info("--solo-percentiles activado; no construyo pares.")
            return

        with run.medir("construccion_pares"):
            df, tiles = construir_dataset_v2(args, percentiles, run)

        with run.medir("split_estratificado"):
            df = split_estratificado(df, seed=SEED)

        with run.medir("secuencias_temporales"):
            secuencias = generar_secuencias_temporales(df, n_secuencias=args.n_secuencias,
                                                        longitud=args.longitud_secuencia)
            run.info("Secuencias: %d (objetivo >= %d)", len(secuencias), args.n_secuencias)

        with run.medir("guardar_local"):
            guardar_dataset_local(df, tiles, percentiles, secuencias, salida, run)

        if args.subir_a_gcs:
            with run.medir("subir_a_gcs"):
                subir_dataset_gcs(salida, args.prefijo_gcs, run)


if __name__ == "__main__":
    main()
