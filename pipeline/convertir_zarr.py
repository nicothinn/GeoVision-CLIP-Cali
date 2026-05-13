"""Convierte los GeoTIFF crudos del bucket a un panel Zarr por fuente.

Estrategia (no usa Dask Distributed):
- Se construye el "esqueleto" del Zarr en GCS con xarray + dask.array
  lazy y `to_zarr(..., compute=False)`: solo metadatos y coordenadas.
- Se procesa la dim `time` en bloques del tamano de un chunk Zarr.
  Cada bloque: un `ThreadPoolExecutor` descarga los GeoTIFF en paralelo,
  arma un ndarray (k, band, y, x) y se escribe como una region.
- Asi dos hilos NUNCA tocan el mismo chunk fisico del Zarr.
- Al final se consolidan metadatos para apertura rapida en remoto.

Uso (PowerShell):
    python pipeline\\convertir_zarr.py --fuente no2
    python pipeline\\convertir_zarr.py --fuente s2 --max-imagenes 100
    python pipeline\\convertir_zarr.py --todas
    python pipeline\\convertir_zarr.py --fuente era5 --workers 8
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

import silenciar_warnings  # noqa: F401  # side-effect: silencia warnings ruidosos

import argparse
import io
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import dask.array as darr
import gcsfs
import numpy as np
import rioxarray  # noqa: F401  # registra el accessor .rio en xarray
import xarray as xr
import zarr
from google.cloud import storage
from tqdm import tqdm

from config import BUCKET, FUENTES, PROJECT_GCP

# Trazabilidad: Run/evento/run_actual del paquete trazabilidad/.
from trazabilidad import Run, evento, run_actual


WORKERS_DEFAULT = 8


class _LogShim:
    """Permite log.info/warning con o sin Run activo."""

    def info(self, msg: str, *args) -> None:
        r = run_actual()
        if r is not None:
            r.info(msg, *args)
            return
        print(msg % args if args else msg)

    def warning(self, msg: str, *args) -> None:
        r = run_actual()
        if r is not None:
            r.warning(msg, *args)
            return
        print(("[WARN] " + msg) % args if args else "[WARN] " + msg)

    def debug(self, msg: str, *args) -> None:
        r = run_actual()
        if r is not None:
            r.debug(msg, *args)


log = _LogShim()


_tls = threading.local()


def _bucket_thread_local() -> storage.Bucket:
    if not hasattr(_tls, "bucket"):
        cliente = storage.Client(project=PROJECT_GCP)
        _tls.cliente = cliente
        _tls.bucket = cliente.bucket(BUCKET)
    return _tls.bucket


def _agrupar_blobs(blobs: list[storage.Blob], modo: str) -> list[dict]:
    """Agrupa blobs en items {img_id, paths}.

    - modo='multibanda': 1 archivo por img_id (sin '__' en el nombre).
    - modo='por_banda':  N archivos por img_id, uno por banda (con '__banda').
    """
    grupos = defaultdict(lambda: {"img_id": "", "bandas": {}})
    for b in blobs:
        nombre = b.name.rsplit("/", 1)[-1].removesuffix(".tif")
        if "__" in nombre:
            img_id, banda = nombre.split("__", 1)
        else:
            img_id, banda = nombre, "_solo"
        grupos[img_id]["img_id"] = img_id
        grupos[img_id]["bandas"][banda] = b.name
    items = sorted(grupos.values(), key=lambda x: x["img_id"])
    if modo == "multibanda":
        items = [it for it in items if "_solo" in it["bandas"]]
    return items


def _leer_tif_3d(blob_path: str) -> np.ndarray:
    """GeoTIFF multibanda -> (band, y, x) float32."""
    bucket = _bucket_thread_local()
    data = bucket.blob(blob_path).download_as_bytes()
    da = rioxarray.open_rasterio(io.BytesIO(data))
    return da.values.astype("float32")


def _leer_tif_2d(blob_path: str) -> np.ndarray:
    """GeoTIFF de una sola banda -> (y, x) float32."""
    bucket = _bucket_thread_local()
    data = bucket.blob(blob_path).download_as_bytes()
    da = rioxarray.open_rasterio(io.BytesIO(data))
    if "band" in da.dims and da.sizes["band"] == 1:
        da = da.isel(band=0)
    return da.values.astype("float32")


def _shape_y_coords(blob_path: str) -> tuple[tuple[int, int], np.ndarray, np.ndarray]:
    bucket = _bucket_thread_local()
    data = bucket.blob(blob_path).download_as_bytes()
    da = rioxarray.open_rasterio(io.BytesIO(data))
    if "band" in da.dims:
        da = da.isel(band=0)
    return (da.sizes["y"], da.sizes["x"]), da.y.values, da.x.values


def _leer_item(item: dict, modo: str, bandas: list[str]) -> np.ndarray:
    """Lee un item completo y devuelve (band, y, x) float32."""
    if modo == "multibanda":
        return _leer_tif_3d(item["bandas"]["_solo"])
    capas = [_leer_tif_2d(item["bandas"][b]) for b in bandas]
    return np.stack(capas, axis=0)


def _crear_esqueleto_zarr(
    mapper,
    n: int,
    bandas: list[str],
    y_vals: np.ndarray,
    x_vals: np.ndarray,
    times: np.ndarray,
    chunk_time: int,
    chunk_y: int,
    chunk_x: int,
    H: int,
    W: int,
) -> None:
    """Escribe metadatos + coords del Zarr en GCS, sin materializar data."""
    plantilla = xr.Dataset(
        {
            "data": (
                ("time", "band", "y", "x"),
                darr.zeros(
                    (n, len(bandas), H, W),
                    chunks=(chunk_time, len(bandas), chunk_y, chunk_x),
                    dtype="float32",
                ),
            )
        },
        coords={
            "time": times,
            "band": list(bandas),
            "y": y_vals[:H],
            "x": x_vals[:W],
        },
    )
    plantilla.to_zarr(
        mapper,
        mode="w",
        compute=False,
        consolidated=False,
        zarr_format=2,
    )


def convertir_fuente(
    fuente_id: str,
    max_imagenes: int | None,
    max_workers: int,
) -> str:
    """Convierte una fuente completa a Zarr en GCS con ThreadPoolExecutor."""
    cfg = FUENTES[fuente_id]
    prefijo = cfg["prefijo"]
    bandas = cfg["bandas"]
    modo = cfg["modo"]

    cliente = storage.Client(project=PROJECT_GCP)
    bucket = cliente.bucket(BUCKET)

    log.info("Listando blobs en %s/raw/", prefijo)
    blobs = [
        b
        for b in bucket.list_blobs(prefix=f"{prefijo}/raw/")
        if b.name.endswith(".tif")
    ]
    log.info("Blobs encontrados: %d", len(blobs))

    items = _agrupar_blobs(blobs, modo)
    if modo == "por_banda":
        items = [it for it in items if all(b in it["bandas"] for b in bandas)]
    if max_imagenes is not None:
        items = items[:max_imagenes]
    n = len(items)
    b_count = len(bandas)
    log.info("Imagenes para apilar: %d", n)
    if not items:
        raise SystemExit("No hay imagenes para procesar (revisa la exportacion).")

    if modo == "multibanda":
        muestra = items[0]["bandas"]["_solo"]
    else:
        muestra = items[0]["bandas"][bandas[0]]
    (H, W), y_vals, x_vals = _shape_y_coords(muestra)
    log.info("Shape espacial: y=%d x=%d", H, W)

    chunk_time = max(1, 268435456 // max(1, b_count * H * W * 4))
    chunk_y = min(512, H)
    chunk_x = min(512, W)
    log.info(
        "Chunks Zarr -> time=%d band=%d y=%d x=%d",
        chunk_time,
        b_count,
        chunk_y,
        chunk_x,
    )

    times = np.array([it["img_id"] for it in items])

    fs = gcsfs.GCSFileSystem(project=PROJECT_GCP)
    ruta = f"{BUCKET}/{prefijo}/panel.zarr"
    mapper = fs.get_mapper(ruta)

    log.info("Escribiendo esqueleto Zarr en gs://%s ...", ruta)
    _crear_esqueleto_zarr(
        mapper,
        n,
        bandas,
        y_vals,
        x_vals,
        times,
        chunk_time,
        chunk_y,
        chunk_x,
        H,
        W,
    )
    evento(
        "zarr_esqueleto_listo",
        fuente=fuente_id,
        n_timesteps=n,
        bandas=b_count,
        H=H,
        W=W,
        chunk_time=chunk_time,
        chunk_y=chunk_y,
        chunk_x=chunk_x,
    )

    n_batches = (n + chunk_time - 1) // chunk_time
    log.info(
        "Procesando %d items en %d batches (~%d items/batch) con %d hilos",
        n,
        n_batches,
        chunk_time,
        max_workers,
    )
    evento(
        "zarr_threadpool_inicio",
        fuente=fuente_id,
        max_workers=max_workers,
        n_batches=n_batches,
        chunk_time=chunk_time,
    )

    t0 = time.perf_counter()
    n_ok = 0
    n_fallas = 0

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        with tqdm(total=n, desc=prefijo, unit="img") as bar:
            for inicio in range(0, n, chunk_time):
                fin = min(inicio + chunk_time, n)
                batch = items[inicio:fin]
                datos = np.full(
                    (fin - inicio, b_count, H, W),
                    np.nan,
                    dtype="float32",
                )

                t_batch = time.perf_counter()
                futuros = {
                    ex.submit(_leer_item, it, modo, bandas): k
                    for k, it in enumerate(batch)
                }

                for f in as_completed(futuros):
                    k = futuros[f]
                    try:
                        datos[k] = f.result()
                        n_ok += 1
                    except Exception as exc:
                        n_fallas += 1
                        log.warning(
                            "Falla item %s: %s",
                            batch[k]["img_id"],
                            exc,
                        )
                    bar.update(1)
                t_lectura = time.perf_counter() - t_batch

                t_w = time.perf_counter()
                ds_batch = xr.Dataset({"data": (("time", "band", "y", "x"), datos)})
                ds_batch.to_zarr(
                    mapper,
                    region={"time": slice(inicio, fin)},
                    consolidated=False,
                )
                t_escritura = time.perf_counter() - t_w

                evento(
                    "zarr_batch_escrito",
                    fuente=fuente_id,
                    inicio=inicio,
                    fin=fin,
                    n=fin - inicio,
                    t_lectura_s=round(t_lectura, 3),
                    t_escritura_s=round(t_escritura, 3),
                )

    dur = time.perf_counter() - t0

    log.info("Consolidando metadatos del Zarr ...")
    zarr.consolidate_metadata(mapper)

    log.info(
        "Zarr listo: gs://%s | ok=%d fallas=%d en %.1fs",
        ruta,
        n_ok,
        n_fallas,
        dur,
    )
    evento(
        "zarr_escrito",
        fuente=fuente_id,
        ruta=f"gs://{ruta}",
        n_timesteps=n,
        n_ok=n_ok,
        n_fallas=n_fallas,
        dims={"time": n, "band": b_count, "y": H, "x": W},
        duracion_s=round(dur, 2),
        max_workers=max_workers,
    )
    return f"gs://{ruta}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="GeoTIFF -> Zarr con ThreadPoolExecutor",
    )
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument(
        "--fuente",
        help="alias o id (no2, so2, o3, s2, era5, modis)",
    )
    grupo.add_argument("--todas", action="store_true")
    parser.add_argument("--max-imagenes", type=int, default=None)
    parser.add_argument("--workers", type=int, default=WORKERS_DEFAULT)
    args = parser.parse_args()

    if args.todas:
        objetivos = list(FUENTES.keys())
        nombre_run = "zarr_todas"
    else:
        from config import get_fuente

        try:
            objetivos = [get_fuente(args.fuente)["id"]]
        except KeyError:
            objetivos = [args.fuente]
        nombre_run = f"zarr_{args.fuente.lower()}"

    contexto = {
        "fuentes_objetivo": objetivos,
        "max_imagenes": args.max_imagenes,
        "workers": args.workers,
        "bucket": BUCKET,
        "project_gcp": PROJECT_GCP,
        "estrategia": "ThreadPoolExecutor + region writes",
    }

    with Run(nombre_run, contexto=contexto) as run:
        for fuente_id in objetivos:
            run.info("=== %s ===", fuente_id)
            evento(
                "zarr_fuente_inicio",
                fuente=fuente_id,
                workers=args.workers,
                max_imagenes=args.max_imagenes,
            )
            with run.medir(f"zarr_{fuente_id}"):
                convertir_fuente(
                    fuente_id,
                    max_imagenes=args.max_imagenes,
                    max_workers=args.workers,
                )
            evento("zarr_fuente_fin", fuente=fuente_id)


if __name__ == "__main__":
    main()
