"""Construye el dataset de pares imagen-texto para la Situacion 2.

Requisitos de la consigna (Situacion 2):
- Minimo 1000 pares (tile Sentinel-2 64x64 px, descripcion en espanol)
  distribuidos en al menos 5 clases:
      contaminacion_alta_NO2, contaminacion_alta_SO2, ozono_anomalo,
      vegetacion_densa, suelo_urbano.
- Etiquetado semi-supervisado: usar las concentraciones de Sentinel-5P
  sobre el centroide del tile como pseudo-label, agrupado por percentiles
  (p25, p50, p75, p90, p99 de la distribucion sobre Cali en los 5 anios).
- Split estratificado 70/15/15 con semilla fija (SEED=42).
- >= 30 secuencias de 8 fechas consecutivas para alimentar el modulo de
  forecasting de la Situacion 3.

Salidas en `dataset_sit2/`:
- `tiles.zarr`            paneles S2 recortados (N, 13, 64, 64), int16.
- `metadatos.parquet`     metadata por tile (clase, descripcion, centroide,
                          fecha, valores S5P, NDVI, BSI, split).
- `percentiles.json`      umbrales p25/p50/p75/p90/p99 por contaminante.
- `secuencias.json`       lista de secuencias temporales para forecasting.
- `resumen.json`          resumen de cardinalidad, balance de clases, etc.

Uso (PowerShell):
    python pipeline\\dataset_sit2_par_imagen_texto.py --solo-percentiles
    python pipeline\\dataset_sit2_par_imagen_texto.py `
        --meta-objetivo 1500 `
        --max-timestamps-s2 1463 `
        --max-tiles-por-escena 40 `
        --stride-pix 32 `
        --cap-por-clase 250 `
        --min-por-clase 20 `
        --paciencia-escenas 30
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
PARENT = HERE.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

import silenciar_warnings  # noqa: F401  # side-effect: silencia warnings

import argparse
import json
import math
import random
import re
import time
from datetime import datetime, timezone
from typing import Iterator

import gcsfs
import numpy as np
import pandas as pd
import xarray as xr
import zarr
from sklearn.model_selection import train_test_split

from config import BUCKET, FUENTES, PROJECT_GCP
from trazabilidad import Run, evento

try:  # noqa: SIM105
    from google.cloud import storage as gcs_storage
except Exception:  # pragma: no cover
    gcs_storage = None  # type: ignore[assignment]


# =============================================================================
# Constantes
# =============================================================================
SEED = 42
TILE_PIX = 64
PERCENTILES_OBJETIVO = [25, 50, 75, 90, 99]

CLASES = [
    "contaminacion_alta_NO2",
    "contaminacion_alta_SO2",
    "ozono_anomalo",
    "vegetacion_densa",
    "suelo_urbano",
]

# Bandas S2 que sabemos vienen en orden estable desde config.FUENTES.
BANDAS_S2 = list(FUENTES["COPERNICUS/S2_SR_HARMONIZED"]["bandas"])  # 13

# Umbrales NDVI/BSI para diferenciar vegetacion densa vs suelo urbano.
UMBRAL_NDVI_DENSO = 0.45
UMBRAL_NDVI_SUELO = 0.20
UMBRAL_BSI_SUELO = 0.05

# Tolerancia temporal entre S2 y S5P (dias). El TROPOMI tiene revisita diaria
# pero ocasionalmente hay gaps; permitimos +/- 3 dias.
MAX_DT_DIAS = 3


# =============================================================================
# Helpers de I/O
# =============================================================================
def _abrir_zarr(prefijo: str) -> xr.Dataset:
    fs = gcsfs.GCSFileSystem(project=PROJECT_GCP)
    mapper = fs.get_mapper(f"{BUCKET}/{prefijo}/panel.zarr")
    return xr.open_zarr(mapper, consolidated=True)


_FECHA_RE = re.compile(r"(\d{8})")


def img_id_a_fecha(img_id: str) -> str | None:
    """Convierte un img_id de GEE a una fecha ISO `YYYY-MM-DD` si la contiene."""
    m = _FECHA_RE.search(img_id)
    if not m:
        return None
    raw = m.group(1)
    try:
        return datetime.strptime(raw, "%Y%m%d").date().isoformat()
    except ValueError:
        return None


def _times_a_fechas(times: np.ndarray) -> np.ndarray:
    """Vectoriza img_id_a_fecha sobre el coord time del Zarr."""
    out: list[str | None] = []
    for t in times:
        out.append(img_id_a_fecha(str(t)))
    return np.array(out, dtype=object)


# =============================================================================
# Percentiles globales sobre S5P
# =============================================================================
def calcular_percentiles_globales(
    run: Run,
    step_temporal: int = 8,
    step_espacial: int = 2,
    rng: random.Random | None = None,
) -> dict[str, dict[str, float]]:
    """Calcula p25/p50/p75/p90/p99 de NO2/SO2/O3 muestreando los Zarr."""
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
            band=0,  # primera banda = columna troposferica
            y=slice(None, None, step_espacial),
            x=slice(None, None, step_espacial),
        ).values.astype("float64")
        muestra = muestra[np.isfinite(muestra)]
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
        evento(
            "percentiles_calculados",
            contaminante=nombre,
            **resultado[nombre],
            n_pixeles=int(muestra.size),
        )

    return resultado


# =============================================================================
# Indices NDVI y BSI sobre tile S2
# =============================================================================
_IDX_S2: dict[str, int] = {b: i for i, b in enumerate(BANDAS_S2)}


def calcular_ndvi_bsi(tile: np.ndarray) -> tuple[float, float]:
    """`tile` shape (13, 64, 64). Devuelve (NDVI_medio, BSI_medio).

    NDVI = (B8 - B4) / (B8 + B4)
    BSI  = ((B11 + B4) - (B8 + B2)) / ((B11 + B4) + (B8 + B2))
    """
    eps = 1e-6
    b2 = tile[_IDX_S2["B2"]].astype("float32")
    b4 = tile[_IDX_S2["B4"]].astype("float32")
    b8 = tile[_IDX_S2["B8"]].astype("float32")
    b11 = tile[_IDX_S2["B11"]].astype("float32")
    ndvi = (b8 - b4) / (b8 + b4 + eps)
    bsi = ((b11 + b4) - (b8 + b2)) / ((b11 + b4) + (b8 + b2) + eps)
    ndvi = ndvi[np.isfinite(ndvi)]
    bsi = bsi[np.isfinite(bsi)]
    return (
        float(ndvi.mean()) if ndvi.size else float("nan"),
        float(bsi.mean()) if bsi.size else float("nan"),
    )


# =============================================================================
# Busqueda nearest en S5P por (lat, lon, fecha)
# =============================================================================
class _AccesoS5P:
    """Cachea los Zarr de S5P y permite consultar (lat, lon, fecha) -> valor."""

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
        fecha_a_t: dict[str, int] = {}
        for k, f in enumerate(fechas):
            if f is not None and f not in fecha_a_t:
                fecha_a_t[f] = k
        if self._run is not None:
            self._run.info(
                "S5P %s cargado: n_time=%d fechas_unicas=%d",
                contaminante,
                len(times),
                len(fecha_a_t),
            )
        cache = {
            "da": da,
            "y": y_vals,
            "x": x_vals,
            "fechas": fechas,
            "fecha_a_t": fecha_a_t,
            "fechas_lista": sorted(set(f for f in fechas if f is not None)),
        }
        self._cache[contaminante] = cache
        return cache

    @staticmethod
    def _fecha_mas_cercana(
        objetivo: str, fechas: list[str], max_dt_dias: int = MAX_DT_DIAS
    ) -> str | None:
        if not fechas:
            return None
        t0 = datetime.strptime(objetivo, "%Y-%m-%d").date()
        mejor: tuple[int, str] | None = None
        for f in fechas:
            tf = datetime.strptime(f, "%Y-%m-%d").date()
            dt = abs((tf - t0).days)
            if dt > max_dt_dias:
                continue
            if mejor is None or dt < mejor[0]:
                mejor = (dt, f)
        return mejor[1] if mejor else None

    def valor(self, contaminante: str, lat: float, lon: float, fecha: str) -> float:
        c = self._cargar(contaminante)
        f = self._fecha_mas_cercana(fecha, c["fechas_lista"])
        if f is None:
            return float("nan")
        t_idx = c["fecha_a_t"][f]
        iy = int(np.argmin(np.abs(c["y"] - lat)))
        ix = int(np.argmin(np.abs(c["x"] - lon)))
        try:
            v = float(c["da"].isel(time=t_idx, y=iy, x=ix).values)
        except Exception:
            v = float("nan")
        return v


# =============================================================================
# Asignacion de clase semi-supervisada
# =============================================================================
def asignar_clase(
    no2: float,
    so2: float,
    o3: float,
    ndvi: float,
    bsi: float,
    percentiles: dict[str, dict[str, float]],
) -> str | None:
    """Devuelve la clase del tile (o None si no aplica ninguna regla)."""
    p90 = lambda c: percentiles[c]["p90"]  # noqa: E731
    p50 = lambda c: percentiles[c]["p50"]  # noqa: E731

    # Reglas con prioridad: contaminacion > anomalia O3 > vegetacion > suelo.
    if math.isfinite(no2) and math.isfinite(p90("NO2")) and no2 >= p90("NO2"):
        return "contaminacion_alta_NO2"
    if math.isfinite(so2) and math.isfinite(p90("SO2")) and so2 >= p90("SO2"):
        return "contaminacion_alta_SO2"
    if math.isfinite(o3) and math.isfinite(p90("O3")) and o3 >= p90("O3"):
        return "ozono_anomalo"
    if (
        math.isfinite(ndvi)
        and ndvi >= UMBRAL_NDVI_DENSO
        and math.isfinite(no2)
        and math.isfinite(p50("NO2"))
        and no2 <= p50("NO2")
    ):
        return "vegetacion_densa"
    if (
        math.isfinite(ndvi)
        and ndvi <= UMBRAL_NDVI_SUELO
        and math.isfinite(bsi)
        and bsi >= UMBRAL_BSI_SUELO
    ):
        return "suelo_urbano"
    return None


# =============================================================================
# Descripcion en espanol
# =============================================================================
def generar_descripcion(
    clase: str,
    no2: float,
    so2: float,
    o3: float,
    ndvi: float,
    bsi: float,
    fecha: str,
    lat: float,
    lon: float,
) -> str:
    base = {
        "contaminacion_alta_NO2": (
            "Tile Sentinel-2 sobre Cali con concentracion alta de NO2 troposferico"
        ),
        "contaminacion_alta_SO2": (
            "Tile Sentinel-2 sobre Cali con concentracion alta de SO2"
        ),
        "ozono_anomalo": (
            "Tile Sentinel-2 sobre Cali con columna de ozono troposferico anomala"
        ),
        "vegetacion_densa": (
            "Tile Sentinel-2 sobre Cali con vegetacion densa y baja contaminacion"
        ),
        "suelo_urbano": (
            "Tile Sentinel-2 sobre Cali con cobertura urbana de suelo expuesto"
        ),
    }[clase]
    return (
        f"{base} ({fecha}, lat={lat:.4f}, lon={lon:.4f}, "
        f"NDVI={ndvi:.2f}, BSI={bsi:.2f}, "
        f"NO2={no2:.2e}, SO2={so2:.2e}, O3={o3:.2e})."
    )


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
    """Genera tiles `tile_pix x tile_pix` sobre la escena S2 con stride dado."""
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
# Construccion del dataset
# =============================================================================
def construir_dataset(
    args: argparse.Namespace,
    percentiles: dict,
    run: Run,
) -> tuple[pd.DataFrame, np.ndarray]:
    """Itera sobre escenas S2 generando tiles y registros del dataset."""
    rng = random.Random(SEED)
    s5p = _AccesoS5P(run=run)

    run.info("Abriendo Sentinel-2 ...")
    ds_s2 = _abrir_zarr(FUENTES["COPERNICUS/S2_SR_HARMONIZED"]["prefijo"])
    da_s2 = ds_s2["data"]
    n_t = int(da_s2.sizes["time"])
    y_vals = np.asarray(ds_s2["y"].values, dtype="float64")
    x_vals = np.asarray(ds_s2["x"].values, dtype="float64")
    times = np.asarray(ds_s2["time"].values)
    fechas_s2 = _times_a_fechas(times)

    # Orden aleatorio reproducible para diversificar la cobertura temporal.
    idxs_t = list(range(n_t))
    rng.shuffle(idxs_t)
    idxs_t = idxs_t[: args.max_timestamps_s2]
    run.info(
        "Escenas S2 a procesar: %d / %d (max_timestamps_s2=%d)",
        len(idxs_t),
        n_t,
        args.max_timestamps_s2,
    )

    conteo: dict[str, int] = {c: 0 for c in CLASES}
    registros: list[dict] = []
    tiles_buffer: list[np.ndarray] = []
    escenas_sin_aporte = 0
    t0_global = time.perf_counter()

    for ord_idx, t_idx in enumerate(idxs_t):
        fecha = fechas_s2[t_idx]
        img_id = str(times[t_idx])
        if fecha is None:
            continue

        if len(registros) >= args.meta_objetivo and all(
            conteo[c] >= args.min_por_clase for c in CLASES
        ):
            run.info("Meta y minimos cumplidos. Cortando.")
            break

        if escenas_sin_aporte >= args.paciencia_escenas:
            run.warning(
                "Paciencia agotada: %d escenas seguidas sin aporte. Cortando.",
                escenas_sin_aporte,
            )
            break

        # Cargar la escena completa una sola vez.
        cubo_escena = da_s2.isel(time=t_idx).values  # (band, y, x)
        if cubo_escena.ndim != 3:
            continue

        aporte_escena = 0
        for tile_info in iter_tiles_escena(
            cubo_escena,
            y_vals,
            x_vals,
            tile_pix=TILE_PIX,
            stride_pix=args.stride_pix,
            max_tiles=args.max_tiles_por_escena,
            rng=rng,
        ):
            tile = tile_info["tile"]
            cy, cx = tile_info["centroide_lat"], tile_info["centroide_lon"]
            ndvi, bsi = calcular_ndvi_bsi(tile)

            no2 = s5p.valor("NO2", cy, cx, fecha)
            so2 = s5p.valor("SO2", cy, cx, fecha)
            o3 = s5p.valor("O3", cy, cx, fecha)

            clase = asignar_clase(no2, so2, o3, ndvi, bsi, percentiles)
            if clase is None:
                continue
            if conteo[clase] >= args.cap_por_clase:
                continue
            if len(registros) >= args.meta_objetivo and all(
                conteo[c] >= args.min_por_clase for c in CLASES
            ):
                break

            tile_id = f"{img_id}__y{tile_info['yi']:04d}__x{tile_info['xi']:04d}"
            descripcion = generar_descripcion(
                clase, no2, so2, o3, ndvi, bsi, fecha, cy, cx
            )

            registros.append(
                {
                    "tile_id": tile_id,
                    "clase": clase,
                    "descripcion": descripcion,
                    "fecha": fecha,
                    "img_id_s2": img_id,
                    "centroide_lat": cy,
                    "centroide_lon": cx,
                    "yi": tile_info["yi"],
                    "xi": tile_info["xi"],
                    "valid_ratio": tile_info["valid_ratio"],
                    "ndvi": ndvi,
                    "bsi": bsi,
                    "no2": no2,
                    "so2": so2,
                    "o3": o3,
                }
            )
            tiles_buffer.append(_tile_a_int16(tile))
            conteo[clase] += 1
            aporte_escena += 1

        if aporte_escena == 0:
            escenas_sin_aporte += 1
        else:
            escenas_sin_aporte = 0

        if (ord_idx + 1) % 10 == 0 or ord_idx == len(idxs_t) - 1:
            dt = time.perf_counter() - t0_global
            run.info(
                "Escena %d/%d (fecha=%s) | pares=%d (%s) | %.1fs",
                ord_idx + 1,
                len(idxs_t),
                fecha,
                len(registros),
                ", ".join(f"{c[:3]}={conteo[c]}" for c in CLASES),
                dt,
            )
            evento(
                "progreso_construccion",
                ord_idx=ord_idx + 1,
                fecha=fecha,
                pares=len(registros),
                conteo=dict(conteo),
                duracion_s=round(dt, 2),
            )

    run.info(
        "Construccion terminada: %d pares totales. Balance: %s",
        len(registros),
        ", ".join(f"{c}={conteo[c]}" for c in CLASES),
    )
    evento("construccion_fin", pares=len(registros), conteo=dict(conteo))

    df = pd.DataFrame(registros)
    tiles_arr = (
        np.stack(tiles_buffer, axis=0)
        if tiles_buffer
        else np.zeros((0, len(BANDAS_S2), TILE_PIX, TILE_PIX), dtype="int16")
    )
    return df, tiles_arr


def _tile_a_int16(tile: np.ndarray) -> np.ndarray:
    """Casta a int16 (S2 viene en uint16/int32) reemplazando NaN por 0."""
    t = np.where(np.isfinite(tile), tile, 0.0)
    t = np.clip(t, -32768, 32767)
    return t.astype("int16")


# =============================================================================
# Split estratificado con fallback robusto
# =============================================================================
def split_estratificado(df: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    """70/15/15 estratificado por clase, con fallback si una clase es muy chica."""
    if df.empty:
        df = df.copy()
        df["split"] = []
        return df

    # Primer split: train (70%) vs temp (30%).
    try:
        train_idx, temp_idx = train_test_split(
            df.index, test_size=0.30, stratify=df["clase"], random_state=seed,
        )
    except ValueError:
        train_idx, temp_idx = train_test_split(
            df.index, test_size=0.30, random_state=seed,
        )

    df_temp = df.loc[temp_idx]
    # Segundo split: val (50% del temp = 15% total) vs test (50% del temp = 15% total).
    try:
        val_idx, test_idx = train_test_split(
            df_temp.index,
            test_size=0.50,
            stratify=df_temp["clase"],
            random_state=seed,
        )
    except ValueError:
        # Fallback robusto: split sin estratificar si alguna clase tiene < 2 ej.
        val_idx, test_idx = train_test_split(
            df_temp.index, test_size=0.50, random_state=seed,
        )

    asign = pd.Series("train", index=df.index)
    asign.loc[val_idx] = "val"
    asign.loc[test_idx] = "test"
    df = df.copy()
    df["split"] = asign.values
    return df


# =============================================================================
# Secuencias temporales para forecasting (Sit. 3)
# =============================================================================
def generar_secuencias_temporales(
    df: pd.DataFrame,
    n_secuencias: int,
    longitud: int,
    seed: int = SEED,
) -> list[dict]:
    """Encuentra >= n_secuencias secuencias de `longitud` fechas consecutivas.

    Estrategia: agrupar por (centroide_lat, centroide_lon) redondeado y tomar
    las fechas consecutivas mas densas; si no hay suficientes con la misma
    coordenada exacta, agrupamos por celda S5P (resolucion ~0.01 grados).
    """
    if df.empty:
        return []

    rng = random.Random(seed)
    df_ord = df.copy()
    df_ord["fecha_dt"] = pd.to_datetime(df_ord["fecha"])
    df_ord["celda_lat"] = (df_ord["centroide_lat"] / 0.01).round() * 0.01
    df_ord["celda_lon"] = (df_ord["centroide_lon"] / 0.01).round() * 0.01

    secuencias: list[dict] = []
    grupos = list(df_ord.groupby(["celda_lat", "celda_lon"]))
    rng.shuffle(grupos)

    for (clat, clon), g in grupos:
        if len(secuencias) >= n_secuencias:
            break
        g = g.sort_values("fecha_dt").drop_duplicates("fecha_dt")
        if len(g) < longitud:
            continue
        # Tomar la primera ventana de tamanio `longitud`.
        ids = g["tile_id"].tolist()[:longitud]
        fechas = [f.isoformat()[:10] for f in g["fecha_dt"].tolist()[:longitud]]
        secuencias.append(
            {
                "celda_lat": float(clat),
                "celda_lon": float(clon),
                "longitud": longitud,
                "tile_ids": ids,
                "fechas": fechas,
            }
        )
    return secuencias


# =============================================================================
# Persistencia local
# =============================================================================
def guardar_dataset_local(
    df: pd.DataFrame,
    tiles: np.ndarray,
    percentiles: dict,
    secuencias: list[dict],
    salida_dir: Path,
    run: Run,
) -> dict:
    salida_dir.mkdir(parents=True, exist_ok=True)

    # 1) Metadatos en parquet (con fallback a CSV si pyarrow no esta).
    meta_path = salida_dir / "metadatos.parquet"
    try:
        df.to_parquet(meta_path, index=False)
    except Exception as exc:  # pragma: no cover
        run.warning("Fallback a CSV (no pyarrow disponible: %s)", exc)
        meta_path = salida_dir / "metadatos.csv"
        df.to_csv(meta_path, index=False)

    # 2) Tiles en Zarr.
    tiles_path = salida_dir / "tiles.zarr"
    if tiles_path.exists():
        for p in tiles_path.rglob("*"):
            if p.is_file():
                p.unlink()
        try:
            tiles_path.rmdir()
        except OSError:
            pass
    z = zarr.open(
        str(tiles_path),
        mode="w",
        shape=tiles.shape,
        chunks=(min(64, max(1, tiles.shape[0])), tiles.shape[1], tiles.shape[2], tiles.shape[3]) if tiles.size else None,
        dtype="int16",
    )
    if tiles.size:
        z[:] = tiles
    z.attrs["bandas"] = BANDAS_S2
    z.attrs["tile_pix"] = TILE_PIX
    z.attrs["tile_ids"] = df["tile_id"].tolist()

    # 3) Percentiles.
    (salida_dir / "percentiles.json").write_text(
        json.dumps(percentiles, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # 4) Secuencias temporales.
    (salida_dir / "secuencias.json").write_text(
        json.dumps(secuencias, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # 5) Resumen.
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
    }
    (salida_dir / "resumen.json").write_text(
        json.dumps(resumen, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    run.info("Dataset guardado en %s", salida_dir)
    evento("dataset_guardado", ruta=str(salida_dir), **{k: v for k, v in resumen.items() if k != "percentiles"})
    return resumen


# =============================================================================
# Subida a GCS (opcional)
# =============================================================================
def subir_dataset_gcs(salida_dir: Path, prefijo_gcs: str, run: Run) -> None:
    if gcs_storage is None:
        run.warning("google-cloud-storage no disponible; omito subida a GCS")
        return
    cliente = gcs_storage.Client(project=PROJECT_GCP)
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
    parser = argparse.ArgumentParser(
        description=(
            "Construye el dataset de pares imagen-texto para la Situacion 2."
        ),
    )
    parser.add_argument("--meta-objetivo", type=int, default=1500,
                        help="Total minimo de pares (default 1500).")
    parser.add_argument("--max-timestamps-s2", type=int, default=1463,
                        help="Numero maximo de escenas S2 a recorrer.")
    parser.add_argument("--max-tiles-por-escena", type=int, default=40,
                        help="Tiles 64x64 candidatos por escena.")
    parser.add_argument("--stride-pix", type=int, default=32,
                        help="Stride en pixeles entre tiles dentro de una escena.")
    parser.add_argument("--cap-por-clase", type=int, default=250,
                        help="Cota superior de muestras por clase.")
    parser.add_argument("--min-por-clase", type=int, default=20,
                        help="Cota inferior por clase antes de detener por meta.")
    parser.add_argument("--paciencia-escenas", type=int, default=30,
                        help="Escenas seguidas sin aporte antes de cortar.")
    parser.add_argument("--solo-percentiles", action="store_true",
                        help="Solo calcula p25/p50/p75/p90/p99 de S5P y termina.")
    parser.add_argument("--n-secuencias", type=int, default=30,
                        help="Numero minimo de secuencias temporales a generar.")
    parser.add_argument("--longitud-secuencia", type=int, default=8,
                        help="Longitud temporal de cada secuencia (Sit 3).")
    parser.add_argument("--salida-local", type=Path,
                        default=Path("dataset_sit2"),
                        help="Directorio local donde escribir el dataset.")
    parser.add_argument("--subir-a-gcs", action="store_true",
                        help="Tras construir, sube el directorio a GCS.")
    parser.add_argument("--prefijo-gcs", default="datasets/sit2",
                        help="Prefijo destino en el bucket si --subir-a-gcs.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    random.seed(SEED)
    np.random.seed(SEED)

    nombre_run = "dataset_sit2"
    contexto = {
        "meta_objetivo": args.meta_objetivo,
        "max_timestamps_s2": args.max_timestamps_s2,
        "max_tiles_por_escena": args.max_tiles_por_escena,
        "stride_pix": args.stride_pix,
        "cap_por_clase": args.cap_por_clase,
        "min_por_clase": args.min_por_clase,
        "paciencia_escenas": args.paciencia_escenas,
        "seed": SEED,
    }
    with Run(nombre_run, contexto=contexto) as run:
        run.info("=== %s ===", nombre_run)
        run.info("Argumentos: %s", contexto)

        with run.medir("percentiles_globales"):
            percentiles = calcular_percentiles_globales(run)

        salida = args.salida_local
        salida.mkdir(parents=True, exist_ok=True)
        (salida / "percentiles.json").write_text(
            json.dumps(percentiles, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        run.info("Percentiles escritos en %s/percentiles.json", salida)

        if args.solo_percentiles:
            run.info("--solo-percentiles activado; no construyo pares.")
            return

        with run.medir("construccion_pares"):
            df, tiles = construir_dataset(args, percentiles, run)

        with run.medir("split_estratificado"):
            df = split_estratificado(df, seed=SEED)

        with run.medir("secuencias_temporales"):
            secuencias = generar_secuencias_temporales(
                df,
                n_secuencias=args.n_secuencias,
                longitud=args.longitud_secuencia,
            )
            run.info(
                "Secuencias generadas: %d (objetivo >= %d, longitud=%d)",
                len(secuencias),
                args.n_secuencias,
                args.longitud_secuencia,
            )

        with run.medir("guardar_local"):
            guardar_dataset_local(df, tiles, percentiles, secuencias, salida, run)

        if args.subir_a_gcs:
            with run.medir("subir_a_gcs"):
                subir_dataset_gcs(salida, args.prefijo_gcs, run)


if __name__ == "__main__":
    main()
