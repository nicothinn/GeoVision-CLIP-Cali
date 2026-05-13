"""Exportador unificado de fuentes satelitales a GCS usando Dask Distributed.

Cumple con la consigna de la Situacion 1:
- ETL distribuido (Dask) en lugar de single-thread o ThreadPool.
- Recorta cada imagen al BBox de Cali + Yumbo + Acopi.
- Guarda los GeoTIFF en `gs://geovision-cali/{prefijo}/raw/`.
- Calcula MD5 inline por cada archivo y lo persiste en un sidecar JSON
  por fuente (`gs://geovision-cali/{prefijo}/manifest_partial.json`),
  usado luego por `manifest.py` para construir el manifest global.

Uso (PowerShell):
    python pipeline\\exportar.py --fuente no2
    python pipeline\\exportar.py --fuente s2 --max-imagenes 50
    python pipeline\\exportar.py --todas
    python pipeline\\exportar.py --fuente era5 --dry-run
    python pipeline\\exportar.py --fuente era5 --anio 2023
    python pipeline\\exportar.py --fuente s2 --inicio 2023-01-01 --fin 2024-01-01
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
import base64
import hashlib
import io
import json
import random
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import ee
import requests
from dask.distributed import Client, LocalCluster, as_completed, get_worker
from google.cloud import storage
from tqdm import tqdm

from config import (
    BBOX,
    BUCKET,
    CRS,
    DASK_MEMORY_LIMIT,
    DASK_N_WORKERS,
    DASK_THREADS_PER_WORKER,
    FECHA_FIN,
    FECHA_FIN_INCLUSIVA,
    FECHA_INICIO,
    FUENTES,
    PROJECT_GCP,
    PROJECT_GEE,
    get_fuente,
)

from trazabilidad import Run, evento
from trazabilidad.dask_plugin import forward_logs


@dataclass
class RegistroArchivo:
    """Metadata por archivo, base del manifest global."""

    fuente: str
    img_id: str
    banda: str | None
    path: str
    md5: str
    size_bytes: int
    fecha_adquisicion: str
    bbox: list[float]
    escala_m: float
    estado: str


def extraer_fecha(img_id: str, fuente_id: str) -> str:
    """Extrae fecha ISO (YYYY-MM-DD) desde el system:index segun la fuente."""
    if fuente_id == "ECMWF/ERA5/HOURLY":
        if len(img_id) >= 8:
            return f"{img_id[0:4]}-{img_id[4:6]}-{img_id[6:8]}"
        return img_id
    if fuente_id.startswith("MODIS/"):
        for tok in img_id.split("_"):
            if (
                tok.startswith("A")
                and len(tok) >= 8
                and tok[1:8].isdigit()
            ):
                try:
                    anio = int(tok[1:5])
                    dia_juliano = int(tok[5:8])
                    d = date(anio, 1, 1) + timedelta(days=dia_juliano - 1)
                    return d.isoformat()
                except (ValueError, OverflowError):
                    continue
        return img_id
    for sep in ("T", "_"):
        if sep in img_id:
            cabeza = img_id.split(sep)[0]
            if len(cabeza) == 8 and cabeza.isdigit():
                return f"{cabeza[0:4]}-{cabeza[4:6]}-{cabeza[6:8]}"
    if len(img_id) >= 10 and img_id[4] == "_" and img_id[7] == "_":
        return img_id[:10].replace("_", "-")
    if len(img_id) >= 8 and img_id[:8].isdigit():
        return f"{img_id[0:4]}-{img_id[4:6]}-{img_id[6:8]}"
    return img_id


def _worker_bucket_solo_gcs(bucket_nombre: str, project_gcp: str):
    """Un solo `storage.Client` + bucket por proceso worker (no por tarea)."""
    w = get_worker()
    if not hasattr(w, "_etl_bucket_solo_gcs"):
        cli = storage.Client(project=project_gcp)
        w._etl_cliente_gcs = cli
        w._etl_bucket_solo_gcs = cli.bucket(bucket_nombre)
    return w._etl_bucket_solo_gcs


def _worker_ensure_ee(project_gee: str) -> None:
    """Earth Engine solo la primera vez que el worker descarga (no en cache)."""
    w = get_worker()
    if getattr(w, "_etl_ee_init", False):
        return
    ee.Initialize(project=project_gee)
    w._etl_ee_init = True


_RETRY_CODIGOS = {429, 500, 502, 503, 504}
_RETRY_INTENTOS_MAX = 6
_RETRY_BASE_S = 2.0
_RETRY_TOPE_S = 60.0


def _descargar_con_reintento(url: str, timeout_s: int = 600) -> bytes:
    """GET con reintento + backoff exponencial para 429/5xx y errores de red.

    Backoff: 2s, 4s, 8s, 16s, 32s, 60s (con jitter aleatorio +/- 25%).
    Reintenta tambien errores de conexion / timeout. En 4xx (excepto 429)
    propaga el error al instante (no tiene sentido reintentar un 404).
    """
    intento = 0
    ultimo_exc = None
    while intento < _RETRY_INTENTOS_MAX:
        intento += 1
        try:
            resp = requests.get(url, timeout=timeout_s, stream=True)
            if resp.status_code in _RETRY_CODIGOS:
                ultimo_exc = requests.exceptions.HTTPError(
                    f"{resp.status_code} {resp.reason}",
                    response=resp,
                )
            else:
                resp.raise_for_status()
                return resp.content
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ChunkedEncodingError,
        ) as exc:
            ultimo_exc = exc
        except requests.exceptions.HTTPError as exc:
            raise exc
        if intento >= _RETRY_INTENTOS_MAX:
            break
        espera = min(_RETRY_BASE_S * (2 ** (intento - 1)), _RETRY_TOPE_S)
        espera *= 0.75 + 0.5 * random.random()
        time.sleep(espera)
    if ultimo_exc is not None:
        raise ultimo_exc
    raise RuntimeError("descarga fallida sin excepcion registrada")


def prelistar_raw_en_bucket(
    prefijo: str,
    bucket_nombre: str,
    project_gcp: str,
) -> dict[str, tuple[int, str]]:
    """Lista una vez `prefijo/raw/*.tif` en GCS: nombre_blob -> (size_bytes, md5_hex).

    Asi los aciertos de cache no hacen un `exists()` por archivo (23k RTT).
    """
    cliente = storage.Client(project=project_gcp)
    bucket = cliente.bucket(bucket_nombre)
    pref = f"{prefijo}/raw/"
    index: dict[str, tuple[int, str]] = {}
    for blob in bucket.list_blobs(prefix=pref):
        if not blob.name.endswith(".tif"):
            continue
        md5_hex = ""
        if blob.md5_hash:
            try:
                md5_hex = base64.b64decode(blob.md5_hash).hex()
            except Exception:
                md5_hex = ""
        index[blob.name] = (int(blob.size or 0), md5_hex)
    return index


def _exportar_archivo_remoto(
    fuente_id: str,
    img_id: str,
    bandas: list[str],
    escala: float,
    prefijo: str,
    bucket_nombre: str,
    project_gcp: str,
    project_gee: str,
    bbox: list[float],
    banda_individual: str | None = None,
    cache_index: dict[str, tuple[int, str]] | None = None,
) -> dict:
    """Funcion ejecutada en el worker Dask. Descarga + sube + calcula MD5.

    Optimizaciones:
    - Indice `cache_index` (broadcast): cache sin llamadas GCS por archivo.
    - `storage.Client` y bucket reutilizados por proceso worker.
    - `ee.Initialize` solo si hace falta descargar (no en cache).
    """
    if banda_individual is not None:
        path = f"{prefijo}/raw/{img_id}__{banda_individual}.tif"
        seleccion = [banda_individual]
        banda_meta = banda_individual
    else:
        path = f"{prefijo}/raw/{img_id}.tif"
        seleccion = list(bandas)
        banda_meta = None

    idx = cache_index or {}
    if path in idx:
        size_bytes, md5_hex = idx[path]
        return {
            "fuente": fuente_id,
            "img_id": img_id,
            "banda": banda_meta,
            "path": f"gs://{bucket_nombre}/{path}",
            "md5": md5_hex,
            "size_bytes": size_bytes,
            "fecha_adquisicion": extraer_fecha(img_id, fuente_id),
            "bbox": bbox,
            "escala_m": float(escala),
            "estado": "cache",
        }

    bucket = _worker_bucket_solo_gcs(bucket_nombre, project_gcp)
    blob = bucket.blob(path)
    if blob.exists():
        try:
            blob.reload()
            md5_hex = ""
            if blob.md5_hash:
                md5_hex = base64.b64decode(blob.md5_hash).hex()
            size = int(blob.size or 0)
        except Exception:
            md5_hex = ""
            size = 0
        return {
            "fuente": fuente_id,
            "img_id": img_id,
            "banda": banda_meta,
            "path": f"gs://{bucket_nombre}/{path}",
            "md5": md5_hex,
            "size_bytes": size,
            "fecha_adquisicion": extraer_fecha(img_id, fuente_id),
            "bbox": bbox,
            "escala_m": float(escala),
            "estado": "cache",
        }

    _worker_ensure_ee(project_gee)

    region = ee.Geometry.Rectangle(bbox)
    imagen = ee.Image(f"{fuente_id}/{img_id}").select(seleccion).clip(region)
    url = imagen.getDownloadURL(
        {
            "region": region,
            "scale": escala,
            "crs": CRS,
            "format": "GEO_TIFF",
        }
    )

    t0 = time.perf_counter()
    contenido = _descargar_con_reintento(url, timeout_s=600)
    t_descarga = time.perf_counter() - t0
    md5_hex = hashlib.md5(contenido).hexdigest()
    size = len(contenido)

    t1 = time.perf_counter()
    blob.upload_from_file(io.BytesIO(contenido), content_type="image/tiff")
    t_subida = time.perf_counter() - t1

    return {
        "fuente": fuente_id,
        "img_id": img_id,
        "banda": banda_meta,
        "path": f"gs://{bucket_nombre}/{path}",
        "md5": md5_hex,
        "size_bytes": size,
        "fecha_adquisicion": extraer_fecha(img_id, fuente_id),
        "bbox": bbox,
        "escala_m": float(escala),
        "latencia_s": round(t_descarga + t_subida, 4),
        "latencia_descarga_s": round(t_descarga, 4),
        "latencia_subida_s": round(t_subida, 4),
        "estado": "ok",
    }


def listar_imagenes(
    fuente_id: str,
    inicio_iso: str | None = None,
    fin_iso: str | None = None,
) -> list[str]:
    """Lista los system:index de una fuente filtrados por bbox y fechas.

    `inicio_iso` y `fin_iso` (ambos en formato YYYY-MM-DD) sobrescriben los
    valores globales `FECHA_INICIO` / `FECHA_FIN`. `fin_iso` es exclusivo
    como en `ee.ImageCollection.filterDate`.
    """
    region = ee.Geometry.Rectangle(BBOX)
    coleccion = (
        ee.ImageCollection(fuente_id)
        .filterBounds(region)
        .filterDate(inicio_iso or FECHA_INICIO, fin_iso or FECHA_FIN)
    )
    ids = coleccion.aggregate_array("system:index").getInfo() or []
    return list(ids)


def construir_tareas(fuente_id: str, ids: list[str]) -> list[dict]:
    """Genera la lista de tareas (una por archivo final) para Dask."""
    cfg = FUENTES[fuente_id]
    bandas = cfg["bandas"]
    escala = cfg["escala"]
    prefijo = cfg["prefijo"]
    modo = cfg["modo"]

    tareas: list[dict] = []
    for img_id in ids:
        if modo == "por_banda":
            for banda in bandas:
                tareas.append(
                    {
                        "fuente_id": fuente_id,
                        "img_id": img_id,
                        "bandas": bandas,
                        "escala": escala,
                        "prefijo": prefijo,
                        "bucket_nombre": BUCKET,
                        "project_gcp": PROJECT_GCP,
                        "project_gee": PROJECT_GEE,
                        "bbox": BBOX,
                        "banda_individual": banda,
                    }
                )
        else:
            tareas.append(
                {
                    "fuente_id": fuente_id,
                    "img_id": img_id,
                    "bandas": bandas,
                    "escala": escala,
                    "prefijo": prefijo,
                    "bucket_nombre": BUCKET,
                    "project_gcp": PROJECT_GCP,
                    "project_gee": PROJECT_GEE,
                    "bbox": BBOX,
                    "banda_individual": None,
                }
            )
    return tareas


def guardar_manifest_parcial(
    prefijo: str,
    registros: list[dict],
    cliente: storage.Client,
) -> str:
    """Sube un manifest_partial.json al bucket con los registros de esta corrida."""
    payload = {
        "fuente": prefijo,
        "generado_utc": datetime.now(timezone.utc).isoformat(),
        "fecha_inicio": FECHA_INICIO,
        "fecha_fin_inclusiva": FECHA_FIN_INCLUSIVA,
        "bbox": BBOX,
        "n_archivos": len(registros),
        "size_bytes_total": sum(r.get("size_bytes", 0) for r in registros),
        "archivos": registros,
    }
    bucket = cliente.bucket(BUCKET)
    path = f"{prefijo}/manifest_partial.json"
    blob = bucket.blob(path)
    blob.upload_from_string(
        json.dumps(payload, indent=2, ensure_ascii=False),
        content_type="application/json",
    )
    return f"gs://{BUCKET}/{path}"


def _path_de_tarea(t: dict) -> str:
    """Reconstruye el path GCS que produciria una tarea (igual logica que el worker)."""
    if t.get("banda_individual"):
        return f"{t['prefijo']}/raw/{t['img_id']}__{t['banda_individual']}.tif"
    return f"{t['prefijo']}/raw/{t['img_id']}.tif"


def _registro_cache_desde_indice(t: dict, idx_entry: tuple[int, str]) -> dict:
    """Construye el registro 'cache' sin pasar por Dask (usa indice prelistado)."""
    size_bytes, md5_hex = idx_entry
    path = _path_de_tarea(t)
    return {
        "fuente": t["fuente_id"],
        "img_id": t["img_id"],
        "banda": t.get("banda_individual"),
        "path": f"gs://{t['bucket_nombre']}/{path}",
        "md5": md5_hex,
        "size_bytes": size_bytes,
        "fecha_adquisicion": extraer_fecha(t["img_id"], t["fuente_id"]),
        "bbox": t["bbox"],
        "escala_m": float(t["escala"]),
        "estado": "cache",
    }


def exportar_fuente(
    fuente_id: str,
    client: Client,
    run: Run,
    max_imagenes: int | None = None,
    dry_run: bool = False,
    prelista_gcs: bool = True,
    inicio_iso: str | None = None,
    fin_iso: str | None = None,
    fin_inclusiva_iso: str | None = None,
) -> list[dict]:
    """Orquesta la exportacion de una fuente con Dask y trazabilidad.

    `inicio_iso`, `fin_iso`, `fin_inclusiva_iso` permiten acotar la ventana
    sin tocar `config.py` (CLI: --anio, --inicio, --fin).
    """
    cfg = FUENTES[fuente_id]
    inicio_efectivo = inicio_iso or FECHA_INICIO
    fin_efectivo = fin_iso or FECHA_FIN
    fin_inclusiva_efectiva = fin_inclusiva_iso or FECHA_FIN_INCLUSIVA
    run.info(
        "Fuente %s | escala %sm | bandas %s | modo %s",
        fuente_id,
        cfg["escala"],
        len(cfg["bandas"]),
        cfg["modo"],
    )
    evento(
        "fuente_inicio",
        fuente=fuente_id,
        escala_m=cfg["escala"],
        bandas=cfg["bandas"],
        modo=cfg["modo"],
        prefijo=cfg["prefijo"],
        bbox=BBOX,
        fecha_inicio=inicio_efectivo,
        fecha_fin_inclusiva=fin_inclusiva_efectiva,
    )

    run.info("Listando system:index en GEE (puede tardar)")
    with run.medir(f"listar_imagenes_{cfg['prefijo']}"):
        ids = listar_imagenes(fuente_id, inicio_efectivo, fin_efectivo)
    run.info(
        "Imagenes encontradas: %d (ventana %s -> %s)",
        len(ids),
        inicio_efectivo,
        fin_inclusiva_efectiva,
    )
    evento("imagenes_listadas", fuente=fuente_id, n=len(ids))

    if max_imagenes is not None:
        ids = ids[:max_imagenes]
        run.warning("Recortado a %d imagenes (--max-imagenes)", len(ids))

    tareas = construir_tareas(fuente_id, ids)
    run.info("Tareas totales: %d", len(tareas))

    if dry_run:
        run.warning("[DRY RUN] no se descarga nada")
        evento("dry_run", fuente=fuente_id, n_tareas=len(tareas))
        return []

    cache_index_map: dict[str, tuple[int, str]] = {}
    if prelista_gcs:
        run.info(
            "Precargando indice GCS gs://%s/%s/raw/ (una sola lista, acelera cache)",
            BUCKET,
            cfg["prefijo"],
        )
        with run.medir(f"prelista_gcs_{cfg['prefijo']}"):
            cache_index_map = prelistar_raw_en_bucket(
                cfg["prefijo"], BUCKET, PROJECT_GCP
            )
        run.info("Indice GCS: %d GeoTIFF ya listados", len(cache_index_map))
        evento(
            "prelista_gcs_listo",
            fuente=fuente_id,
            prefijo=cfg["prefijo"],
            n_blobs=len(cache_index_map),
        )

    registros: list[dict] = []
    tareas_pendientes: list[dict] = []
    for t in tareas:
        path_t = _path_de_tarea(t)
        idx_entry = cache_index_map.get(path_t)
        if idx_entry is not None:
            registros.append(_registro_cache_desde_indice(t, idx_entry))
        else:
            tareas_pendientes.append(t)
    n_cache_pre = len(registros)
    n_pendientes = len(tareas_pendientes)
    run.info(
        "Cache prefiltrado: %d en cache, %d pendientes a Dask",
        n_cache_pre,
        n_pendientes,
    )
    evento(
        "cache_prefiltrado",
        fuente=fuente_id,
        n_cache=n_cache_pre,
        n_pendientes=n_pendientes,
    )

    fallas = 0
    t0 = time.time()
    if n_pendientes == 0:
        run.info("Nada que despachar a Dask: 100%% en cache")
    else:
        if cache_index_map and n_pendientes > 0:
            [cache_arg] = client.scatter([cache_index_map], broadcast=True)
        else:
            cache_arg = None

        futuros = [
            client.submit(
                _exportar_archivo_remoto,
                **{**t, "cache_index": cache_arg},
                pure=False,
            )
            for t in tareas_pendientes
        ]

        with tqdm(total=len(futuros), desc=cfg["prefijo"], unit="arch") as bar:
            for fut in as_completed(futuros):
                try:
                    reg = fut.result()
                    registros.append(reg)
                    if reg.get("estado") != "cache":
                        evento("archivo_procesado", **reg)
                    bar.set_postfix_str(
                        f"{reg['estado']} {reg['size_bytes'] / 1024:.1f}KB"
                    )
                except Exception as exc:
                    fallas += 1
                    run.error("Fallo tarea: %s", exc, exc_info=True)
                    evento(
                        "archivo_fallido",
                        fuente=fuente_id,
                        excepcion_tipo=type(exc).__name__,
                        excepcion_mensaje=str(exc),
                    )
                    bar.set_postfix_str(f"FAIL {exc.__class__.__name__}")
                bar.update(1)

    dt = time.time() - t0
    n_cache = sum(1 for r in registros if r.get("estado") == "cache")
    n_ok = sum(1 for r in registros if r.get("estado") == "ok")
    total_mb = sum(r["size_bytes"] for r in registros) / 1048576
    evento(
        "export_fuente_resumen",
        fuente=fuente_id,
        n_cache=n_cache,
        n_ok=n_ok,
        n_fallas=fallas,
        size_mb=round(total_mb, 4),
        duracion_s=round(dt, 3),
    )
    run.info(
        "Fuente %s completada | cache=%d ok=%d | %d fallas | %.1f MB | %.1fs",
        fuente_id,
        n_cache,
        n_ok,
        fallas,
        total_mb,
        dt,
    )

    cliente_storage = storage.Client(project=PROJECT_GCP)
    ruta = guardar_manifest_parcial(cfg["prefijo"], registros, cliente_storage)
    run.info("Manifest parcial subido: %s", ruta)
    evento(
        "fuente_fin",
        fuente=fuente_id,
        n_ok=len(registros),
        n_fallas=fallas,
        n_cache=n_cache,
        n_descargas_ok=n_ok,
        size_mb=round(total_mb, 3),
        duracion_s=round(dt, 3),
        manifest_partial=ruta,
    )

    return registros


def main() -> None:
    parser = argparse.ArgumentParser(description="Exportador GCS con Dask")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument(
        "--fuente",
        help="alias o id de fuente (no2, so2, o3, s2, era5, modis)",
    )
    grupo.add_argument(
        "--todas",
        action="store_true",
        help="exporta las 6 fuentes",
    )
    parser.add_argument("--max-imagenes", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help=(
            "n workers Dask. Por defecto usa el override de la fuente "
            "(si existe en config.FUENTES) o DASK_N_WORKERS."
        ),
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=None,
        help=(
            "threads por worker. Por defecto usa el override de la fuente "
            "(si existe) o DASK_THREADS_PER_WORKER."
        ),
    )
    parser.add_argument(
        "--sin-prelista-gcs",
        action="store_true",
        help=(
            "no listar gs://.../prefijo/raw/ al inicio (cache mas lento: "
            "un exists por archivo)"
        ),
    )
    parser.add_argument(
        "--anio",
        type=int,
        default=None,
        help=(
            "atajo: descarga solo un anio completo (ej. --anio 2023 ~ "
            "--inicio 2023-01-01 --fin 2024-01-01). Tiene prioridad sobre "
            "FECHA_INICIO/FECHA_FIN del config."
        ),
    )
    parser.add_argument(
        "--inicio",
        default=None,
        help="fecha inicio ISO (YYYY-MM-DD). Sobrescribe FECHA_INICIO del config.",
    )
    parser.add_argument(
        "--fin",
        default=None,
        help=(
            "fecha fin ISO (YYYY-MM-DD), exclusiva como en filterDate de GEE. "
            "Sobrescribe FECHA_FIN del config."
        ),
    )
    args = parser.parse_args()

    if args.anio is not None and (args.inicio or args.fin):
        parser.error("usa --anio O (--inicio/--fin), no ambos")
    if args.anio is not None:
        inicio_iso = f"{args.anio:04d}-01-01"
        fin_iso = f"{args.anio + 1:04d}-01-01"
        fin_inclusiva_iso = f"{args.anio:04d}-12-31"
    else:
        inicio_iso = args.inicio
        fin_iso = args.fin
        fin_inclusiva_iso = None
        if args.fin:
            try:
                d_fin = datetime.strptime(args.fin, "%Y-%m-%d").date()
                fin_inclusiva_iso = (d_fin - timedelta(days=1)).isoformat()
            except ValueError:
                parser.error(f"--fin debe ser YYYY-MM-DD, recibi {args.fin!r}")

    if args.todas:
        objetivos = list(FUENTES.keys())
        nombre_run = "exportar_todas"
    else:
        clave = args.fuente.lower()
        if clave in {"o3", "so2", "no2", "sentinel2", "s2", "modis", "era5"}:
            objetivos = [get_fuente(args.fuente)["id"]]
        else:
            objetivos = [args.fuente]
        nombre_run = f"exportar_{clave}"

    workers_efectivos = args.workers
    threads_efectivos = args.threads
    if workers_efectivos is None or threads_efectivos is None:
        if len(objetivos) == 1:
            cfg_o = FUENTES[objetivos[0]]
            if workers_efectivos is None:
                workers_efectivos = cfg_o.get("dask_n_workers", DASK_N_WORKERS)
            if threads_efectivos is None:
                threads_efectivos = cfg_o.get(
                    "dask_threads_per_worker", DASK_THREADS_PER_WORKER
                )
        else:
            if workers_efectivos is None:
                workers_efectivos = DASK_N_WORKERS
            if threads_efectivos is None:
                threads_efectivos = DASK_THREADS_PER_WORKER

    contexto = {
        "fuentes_objetivo": objetivos,
        "max_imagenes": args.max_imagenes,
        "dry_run": args.dry_run,
        "prelista_gcs": not args.sin_prelista_gcs,
        "workers": workers_efectivos,
        "threads_por_worker": threads_efectivos,
        "bbox": BBOX,
        "fecha_inicio": inicio_iso or FECHA_INICIO,
        "fecha_fin": fin_iso or FECHA_FIN,
        "fecha_fin_inclusiva": fin_inclusiva_iso or FECHA_FIN_INCLUSIVA,
        "anio_filtro": args.anio,
        "bucket": BUCKET,
        "project_gcp": PROJECT_GCP,
        "project_gee": PROJECT_GEE,
    }

    with Run(nombre_run, contexto=contexto) as run:
        run.info("Inicializando Earth Engine (project=%s)", PROJECT_GEE)
        ee.Initialize(project=PROJECT_GEE)

        run.info(
            "Levantando Dask local: %d workers x %d threads (memoria %s)",
            workers_efectivos,
            threads_efectivos,
            DASK_MEMORY_LIMIT,
        )
        cluster = LocalCluster(
            n_workers=workers_efectivos,
            threads_per_worker=threads_efectivos,
            memory_limit=DASK_MEMORY_LIMIT,
        )
        client = Client(cluster)
        run.info("Dashboard Dask: %s", client.dashboard_link)
        evento(
            "dask_cluster_listo",
            workers=workers_efectivos,
            threads=threads_efectivos,
            memory_limit=DASK_MEMORY_LIMIT,
            dashboard=client.dashboard_link,
        )

        forward_logs(client)

        try:
            for fuente_id in objetivos:
                exportar_fuente(
                    fuente_id,
                    client=client,
                    run=run,
                    max_imagenes=args.max_imagenes,
                    dry_run=args.dry_run,
                    prelista_gcs=not args.sin_prelista_gcs,
                    inicio_iso=inicio_iso,
                    fin_iso=fin_iso,
                    fin_inclusiva_iso=fin_inclusiva_iso,
                )
        finally:
            client.close()
            cluster.close()
            run.info("Cluster Dask cerrado")


if __name__ == "__main__":
    main()
