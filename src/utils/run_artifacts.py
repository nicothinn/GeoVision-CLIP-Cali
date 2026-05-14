"""Guardado de checkpoint con MD5 y subida a GCS (artefactos de entrenamiento)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import torch


def md5_of_file(path: Path) -> str:
    h = hashlib.md5()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def save_checkpoint_bundle(
    path: Path,
    *,
    state_dict: dict[str, Any],
    hparams: dict[str, Any],
    epoch: int,
    metrics: dict[str, float],
) -> str:
    """Guarda `.pt` y `.md5` adyacente; devuelve hex MD5."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "state_dict": state_dict,
        "hparams": hparams,
        "epoch": epoch,
        "metrics": metrics,
    }
    torch.save(bundle, path)
    md5 = md5_of_file(path)
    (path.with_suffix(path.suffix + ".md5")).write_text(md5 + "\n", encoding="utf-8")
    return md5


def upload_run_directory(
    local_dir: Path,
    bucket_name: str,
    gcs_prefix: str,
    project: str | None = None,
) -> int:
    """Sube todos los archivos bajo `local_dir` a gs://bucket/gcs_prefix/rel."""
    try:
        from google.cloud import storage
    except ImportError as e:  # pragma: no cover
        raise ImportError("pip install google-cloud-storage") from e

    client = storage.Client(project=project) if project else storage.Client()
    bucket = client.bucket(bucket_name)
    n = 0
    local_dir = Path(local_dir)
    for p in local_dir.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(local_dir).as_posix()
        blob = bucket.blob(f"{gcs_prefix.rstrip('/')}/{rel}")
        blob.upload_from_filename(str(p))
        n += 1
    return n


def write_config_json(path: Path, cfg: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
