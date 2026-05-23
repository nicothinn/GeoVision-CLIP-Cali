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


def _listar_blobs_gcs(bucket: str, sin_sentinel2: bool, solo_ligero: bool):
    from google.cloud import storage

    cliente = storage.Client(project=PROJECT_GCP)
    b = cliente.bucket(bucket)
    for blob in b.list_blobs():
        name = blob.name
        if _blob_excluido(name, sin_sentinel2):
            continue
        if solo_ligero and sin_sentinel2:
            if not any(name.startswith(p) for p in PREFIJOS_LIGEROS):
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
    from huggingface_hub import HfApi

    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    api = HfApi(token=token)
    repo_id = args.repo_id

    if not args.dry_run:
        try:
            api.create_repo(repo_id, repo_type="dataset", exist_ok=True, private=args.private)
        except Exception as e:
            run.warning("create_repo: %s (puede existir ya)", e)

    n_ok = n_skip = n_err = 0
    bytes_subidos = 0

    for blob in _listar_blobs_gcs(args.bucket, args.sin_sentinel2, args.sin_sentinel2):
        path_in_repo = blob.name
        size = blob.size or 0

        if args.reanudar and not args.dry_run:
            try:
                info = api.get_paths_info(
                    repo_id, paths=[path_in_repo], repo_type="dataset"
                )
                if info and info[0].size == size:
                    n_skip += 1
                    continue
            except Exception:
                pass

        if args.dry_run:
            run.info("[dry-run] subir %s (%s bytes)", path_in_repo, size)
            n_ok += 1
            bytes_subidos += size
            continue

        try:
            with blob.open("rb") as f:
                api.upload_file(
                    path_or_fileobj=f,
                    path_in_repo=path_in_repo,
                    repo_id=repo_id,
                    repo_type="dataset",
                    commit_message=None,
                )
            n_ok += 1
            bytes_subidos += size
            if n_ok % 50 == 0:
                run.info("Subidos %d archivos (%.2f GB)...", n_ok, bytes_subidos / 1e9)
                evento("hf_subida_progreso", n_ok=n_ok, gb=round(bytes_subidos / 1e9, 3))
        except Exception as e:
            n_err += 1
            run.error("Fallo %s: %s", path_in_repo, e)
            run.evento("hf_subida_error", path=path_in_repo, error=str(e))

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
    contexto = {
        "modo": args.modo,
        "repo_id": args.repo_id,
        "sin_sentinel2": args.sin_sentinel2,
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
