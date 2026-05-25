"""Publicar o descargar el panel GeoVision en Hugging Face (sin pasar TIFF raw).

Modos:
  subir     GCS (gs://geovision-cali) -> Hugging Face Hub
  descargar Hugging Face Hub -> disco local

Por defecto excluye GeoTIFF en **/raw/**. Con --sin-sentinel2 (o --ligero) omite
Sentinel2/panel.zarr (~66 GB); util para notebooks y manifests ligeros.

Ejemplos (PowerShell):
  # Solo descargar lo liviano desde HF (Sit.2 + S5P + manifests, sin S2)
  python pipeline\\publicar_hf.py descargar ^
    --repo-id Slucu-0310/geovision-cali-panel ^
    --local-dir .\\data_hf_ligero ^
    --sin-sentinel2

  # Subir a HF desde GCS sin el panel S2
  python pipeline\\publicar_hf.py subir ^
    --repo-id Slucu-0310/geovision-cali-panel ^
    --sin-sentinel2 ^
    --dry-run

  # Subir todo excepto raw/*.tif (incluye Sentinel2 Zarr completo)
  python pipeline\\publicar_hf.py subir --repo-id Slucu-0310/geovision-cali-panel

Requiere: huggingface_hub, google-cloud-storage (subir), HF_TOKEN en entorno.
Logs: runs/<timestamp>_publicar_hf_<modo>/
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
REPO_ROOT = PARENT.resolve()
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

import silenciar_warnings  # noqa: F401

from config import BUCKET, PROJECT_GCP
from trazabilidad import Run, evento

# Prefijos GCS que se consideran en modo "ligero" (sin Sentinel2 Zarr)
PREFIJOS_LIGEROS = (
    "manifests/",
    "Sentinel5P/",
    "ERA-5/",
    "MODIS_MCD/",
    "datasets/",
)

# Solo covariables ambientales (ERA5 + MODIS, sin S5P ni S2)
PREFIJOS_AMBIENTALES = (
    "ERA-5/",
    "MODIS_MCD/",
)

# Siempre excluir (TIFF crudos y carpetas raw)
EXCLUIR_GLOB_SIEMPRE = (
    "**/raw/**",
    "**/*.tif",
    "**/*.tiff",
    "**/*.TIF",
    "**/*.TIFF",
)

EXCLUIR_S2_GLOB = (
    "Sentinel2/**",
    "**/Sentinel2/**",
)


def _patrones_hf(sin_sentinel2: bool) -> tuple[list[str], list[str]]:
    """Devuelve (allow_patterns, ignore_patterns) para snapshot_download."""
    ignore = list(EXCLUIR_GLOB_SIEMPRE)
    if sin_sentinel2:
        ignore.extend(EXCLUIR_S2_GLOB)
    # allow vacio = todo salvo ignore
    allow: list[str] = []
    if sin_sentinel2:
        allow = [
            "manifests/**",
            "Sentinel5P/**",
            "ERA-5/**",
            "MODIS_MCD/**",
            "datasets/**",
            "**/*.json",
            "**/*.parquet",
            "README.md",
            ".gitattributes",
        ]
    return allow, ignore


def _blob_excluido(name: str, sin_sentinel2: bool) -> bool:
    """True si el blob GCS no debe subirse a HF."""
    n = name.replace("\\", "/")
    if "/raw/" in n or n.endswith("/raw"):
        return True
    low = n.lower()
    if low.endswith(".tif") or low.endswith(".tiff"):
        return True
    if sin_sentinel2:
        if n.startswith("Sentinel2/") or "/Sentinel2/" in n:
            return True
    return False


def _listar_blobs_gcs(bucket: str, sin_sentinel2: bool, solo_ligero: bool, solo_ambientales: bool = False):
    from google.cloud import storage

    cliente = storage.Client(project=PROJECT_GCP)
    b = cliente.bucket(bucket)

    if solo_ambientales:
        prefijos = PREFIJOS_AMBIENTALES
    elif solo_ligero and sin_sentinel2:
        prefijos = PREFIJOS_LIGEROS
    else:
        prefijos = None

    if prefijos:
        for prefijo in prefijos:
            for blob in b.list_blobs(prefix=prefijo):
                name = blob.name
                if _blob_excluido(name, sin_sentinel2):
                    continue
                yield blob
    else:
        for blob in b.list_blobs():
            name = blob.name
            if _blob_excluido(name, sin_sentinel2):
                continue
            yield blob


def cmd_descargar(args: argparse.Namespace, run: Run) -> None:
    from huggingface_hub import snapshot_download

    allow, ignore = _patrones_hf(args.sin_sentinel2)
    run.info(
        "Descarga HF repo=%s -> %s | sin_sentinel2=%s",
        args.repo_id,
        args.local_dir,
        args.sin_sentinel2,
    )
    run.evento(
        "hf_descarga_inicio",
        repo_id=args.repo_id,
        local_dir=str(args.local_dir),
        sin_sentinel2=args.sin_sentinel2,
        allow_patterns=allow,
        ignore_patterns=ignore,
    )

    kwargs: dict = {
        "repo_id": args.repo_id,
        "repo_type": "dataset",
        "local_dir": str(args.local_dir),
        "local_dir_use_symlinks": False,
        "ignore_patterns": ignore,
    }
    if allow:
        kwargs["allow_patterns"] = allow

    if args.dry_run:
        run.info("DRY-RUN: no se llama snapshot_download. Patrones ignore=%s", ignore)
        if allow:
            run.info("DRY-RUN: allow_patterns=%s", allow)
        return

    path = snapshot_download(**kwargs)
    run.info("Descarga completada en: %s", path)
    run.evento("hf_descarga_fin", path=str(path))


def cmd_subir(args: argparse.Namespace, run: Run) -> None:
    from google.cloud import storage
    from huggingface_hub import HfApi, upload_folder

    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    api = HfApi(token=token)
    repo_id = args.repo_id

    if not args.dry_run:
        api.create_repo(repo_id, repo_type="dataset", exist_ok=True, private=args.private)

    # Crear directorio temporal para descargar desde GCS
    tmp_dir = REPO_ROOT / "data_hf" / "_tmp_upload"
    if tmp_dir.exists():
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    n_total = 0
    bytes_total = 0

    # 1. DESCARGAR: GCS -> local
    run.info("Paso 1/2: Descargando desde GCS a local...")
    for blob in _listar_blobs_gcs(args.bucket, args.sin_sentinel2, args.sin_sentinel2, args.solo_ambientales):
        path_in_repo = blob.name
        size = blob.size or 0
        local_path = tmp_dir / path_in_repo
        local_path.parent.mkdir(parents=True, exist_ok=True)

        if args.dry_run:
            run.info("[dry-run] descargar %s (%s bytes)", path_in_repo, size)
            n_total += 1
            bytes_total += size
            continue

        if local_path.is_file() and local_path.stat().st_size == size:
            n_total += 1
            bytes_total += size
            continue

        blob.download_to_filename(str(local_path))
        n_total += 1
        bytes_total += size

        if n_total % 50 == 0:
            run.info("  Descargados %d archivos (%.2f MB)...", n_total, bytes_total / 1e6)

    run.info("Descarga completa: %d archivos, %.2f MB", n_total, bytes_total / 1e6)

    if args.dry_run:
        run.info("DRY-RUN: no se sube a HF")
        return

    # 2. SUBIR: local -> HF (en un solo commit con upload_folder)
    run.info("Paso 2/2: Subiendo desde local a HF...")
    try:
        upload_folder(
            folder_path=str(tmp_dir),
            repo_id=repo_id,
            repo_type="dataset",
            token=token,
            commit_message=f"Subida panel GCS a HF ({n_total} archivos, {bytes_total/1e6:.0f} MB)",
        )
        run.info("Subida exitosa a %s", repo_id)
        run.evento("hf_subida_fin", repo_id=repo_id, n_archivos=n_total, bytes=bytes_total)
    except Exception as e:
        run.error("Error en subida: %s", e)
        run.evento("hf_subida_error", error=str(e))
        raise

    # Limpiar
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)
    run.info("Temporal limpiado: %s", tmp_dir)
        )
        batch_bytes += size

        # Subir batch cada BATCH_SIZE archivos
        if len(batch_ops) >= BATCH_SIZE:
            try:
                api.create_commit(
                    repo_id=repo_id,
                    repo_type="dataset",
                    operations=batch_ops,
                    commit_message=f"Subida lote {n_ok + 1}-{n_ok + len(batch_ops)}",
                )
                n_ok += len(batch_ops)
                bytes_subidos += batch_bytes
                run.info(
                    "Subidos %d archivos (%.2f GB)...",
                    n_ok,
                    bytes_subidos / 1e9,
                )
                evento(
                    "hf_subida_progreso",
                    n_ok=n_ok,
                    gb=round(bytes_subidos / 1e9, 3),
                )
            except Exception as e:
                n_err += len(batch_ops)
                run.error("Fallo lote %d archivos: %s", len(batch_ops), e)
                run.evento("hf_subida_error", lote=len(batch_ops), error=str(e))
            finally:
                for fh in batch_fhs:
                    fh.close()
                batch_ops = []
                batch_fhs = []
                batch_bytes = 0

    # Subir lote final
    if batch_ops:
        try:
            api.create_commit(
                repo_id=repo_id,
                repo_type="dataset",
                operations=batch_ops,
                commit_message=f"Subida lote final {n_ok + 1}-{n_ok + len(batch_ops)}",
            )
            n_ok += len(batch_ops)
            bytes_subidos += batch_bytes
        except Exception as e:
            n_err += len(batch_ops)
            run.error("Fallo lote final %d archivos: %s", len(batch_ops), e)
            run.evento("hf_subida_error", lote=len(batch_ops), error=str(e))
        finally:
            for fh in batch_fhs:
                fh.close()
                batch_ops = []
                batch_bytes = 0

    # Subir lote final
    if batch_ops:
        try:
            api.create_commit(
                repo_id=repo_id,
                repo_type="dataset",
                operations=batch_ops,
                commit_message=f"Subida lote final {n_ok + 1}-{n_ok + len(batch_ops)}",
            )
            n_ok += len(batch_ops)
            bytes_subidos += batch_bytes
        except Exception as e:
            n_err += len(batch_ops)
            run.error("Fallo lote final %d archivos: %s", len(batch_ops), e)
            run.evento("hf_subida_error", lote=len(batch_ops), error=str(e))
        finally:
            for op in batch_ops:
                op.file_obj.close()

    run.info(
        "Subida fin: ok=%d skip=%d err=%d bytes=%.2f GB",
        n_ok,
        n_skip,
        n_err,
        bytes_subidos / 1e9,
    )
    run.evento(
        "hf_subida_fin",
        repo_id=repo_id,
        n_ok=n_ok,
        n_skip=n_skip,
        n_err=n_err,
        bytes=bytes_subidos,
        sin_sentinel2=args.sin_sentinel2,
    )


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Subir GCS->HF o descargar HF->local (flag --sin-sentinel2 omite ~66GB S2 Zarr).",
    )
    p.add_argument(
        "modo",
        choices=("subir", "descargar"),
        help="subir: GCS->HF | descargar: HF->local",
    )
    p.add_argument(
        "--repo-id",
        default=os.environ.get("HF_REPO_ID", "Slucu-0310/geovision-cali-panel"),
        help="Dataset en Hugging Face Hub",
    )
    p.add_argument("--bucket", default=BUCKET, help="Bucket GCS origen (solo subir)")
    p.add_argument(
        "--local-dir",
        type=Path,
        default=REPO_ROOT / "data_hf",
        help="Carpeta destino (solo descargar)",
    )
    p.add_argument(
        "--sin-sentinel2",
        "--ligero",
        dest="sin_sentinel2",
        action="store_true",
        help="Excluir Sentinel2/panel.zarr (~66 GB). Incluye S5P, ERA5, MODIS, datasets/, manifests.",
    )
    p.add_argument(
        "--solo-ambientales",
        action="store_true",
        help="Subir solo ERA-5 y MODIS_MCD (sin S5P ni S2 ni manifests).",
    )
    p.add_argument("--private", action="store_true", help="Repo HF privado (solo subir)")
    p.add_argument(
        "--reanudar",
        action="store_true",
        help="Omitir archivos ya en HF con mismo tamano (solo subir)",
    )
    p.add_argument("--dry-run", action="store_true", help="Solo listar / mostrar patrones")
    p.add_argument(
        "--runs-root",
        type=Path,
        default=REPO_ROOT / "runs",
        help="Raiz de trazabilidad runs/",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    nombre = f"publicar_hf_{args.modo}"
    if args.sin_sentinel2:
        nombre += "_ligero"
    if args.solo_ambientales:
        nombre += "_ambientales"
    contexto = {
        "modo": args.modo,
        "repo_id": args.repo_id,
        "sin_sentinel2": args.sin_sentinel2,
        "solo_ambientales": args.solo_ambientales,
        "dry_run": args.dry_run,
    }
    with Run(nombre, contexto=contexto, root=args.runs_root) as run:
        if args.modo == "descargar":
            args.local_dir.mkdir(parents=True, exist_ok=True)
            cmd_descargar(args, run)
        else:
            cmd_subir(args, run)


if __name__ == "__main__":
    main()
