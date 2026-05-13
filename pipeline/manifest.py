"""Consolidador del manifest global del pipeline.

Cada fuente genera, al final de `exportar.py`, un `manifest_partial.json`
en `gs://<bucket>/<prefijo>/manifest_partial.json` con la lista de archivos
crudos exportados (path, md5, size_bytes, fecha_adquisicion, ...).

Este script:

1. Descarga el `manifest_partial.json` de cada fuente conocida en
   `config.FUENTES` (las que no existan se reportan como `faltantes`).
2. Consolida todos los registros en un unico `manifest.json` con:
     - `generado_utc`        timestamp ISO UTC.
     - `bucket`              nombre del bucket GCS.
     - `bbox`                BBox de Cali.
     - `fecha_inicio`/`fecha_fin_inclusiva`.
     - `fuentes`             dict con n_archivos y size_bytes_total por fuente.
     - `n_archivos`          total global.
     - `size_bytes_total`    total global.
     - `archivos`            lista completa (orden estable por fuente, img_id).
3. Lo escribe en `manifests/manifest.json` (relativo a la raiz del proyecto).
4. Si se pasa `--subir-a-gcs`, lo sube tambien a
   `gs://<bucket>/manifests/manifest.json`.

Uso (PowerShell):
    python pipeline\\manifest.py
    python pipeline\\manifest.py --subir-a-gcs
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
from datetime import datetime, timezone

from google.cloud import storage

from config import BBOX, BUCKET, FECHA_FIN_INCLUSIVA, FECHA_INICIO, FUENTES, PROJECT_GCP
from trazabilidad import Run, evento


SALIDA_LOCAL = PARENT / "manifests" / "manifest.json"
SALIDA_GCS = "manifests/manifest.json"


def _descargar_partial(cliente: storage.Client, prefijo: str) -> dict | None:
    """Descarga `gs://<BUCKET>/<prefijo>/manifest_partial.json` si existe."""
    bucket = cliente.bucket(BUCKET)
    blob = bucket.blob(f"{prefijo}/manifest_partial.json")
    if not blob.exists():
        return None
    payload = blob.download_as_bytes()
    return json.loads(payload.decode("utf-8"))


def consolidar(cliente: storage.Client) -> dict:
    """Recorre todas las fuentes en config.FUENTES y arma el manifest global."""
    fuentes_info: dict[str, dict] = {}
    archivos: list[dict] = []
    faltantes: list[str] = []

    for fuente_id, cfg in FUENTES.items():
        prefijo = cfg["prefijo"]
        evento("consolidar_fuente_inicio", fuente=fuente_id, prefijo=prefijo)
        partial = _descargar_partial(cliente, prefijo)
        if partial is None:
            faltantes.append(fuente_id)
            fuentes_info[fuente_id] = {
                "prefijo": prefijo,
                "presente": False,
                "n_archivos": 0,
                "size_bytes_total": 0,
            }
            evento("consolidar_fuente_faltante", fuente=fuente_id, prefijo=prefijo)
            continue
        regs = list(partial.get("archivos", []))
        for r in regs:
            r.setdefault("fuente", fuente_id)
        archivos.extend(regs)
        fuentes_info[fuente_id] = {
            "prefijo": prefijo,
            "presente": True,
            "n_archivos": len(regs),
            "size_bytes_total": sum(int(r.get("size_bytes", 0)) for r in regs),
            "manifest_partial_generado_utc": partial.get("generado_utc"),
        }
        evento(
            "consolidar_fuente_ok",
            fuente=fuente_id,
            n_archivos=len(regs),
            size_bytes_total=fuentes_info[fuente_id]["size_bytes_total"],
        )

    archivos.sort(key=lambda r: (r.get("fuente", ""), r.get("img_id", ""), r.get("banda") or ""))

    return {
        "generado_utc": datetime.now(timezone.utc).isoformat(),
        "bucket": BUCKET,
        "project_gcp": PROJECT_GCP,
        "bbox": BBOX,
        "fecha_inicio": FECHA_INICIO,
        "fecha_fin_inclusiva": FECHA_FIN_INCLUSIVA,
        "fuentes": fuentes_info,
        "faltantes": faltantes,
        "n_archivos": len(archivos),
        "size_bytes_total": sum(int(r.get("size_bytes", 0)) for r in archivos),
        "archivos": archivos,
    }


def escribir_local(payload: dict, ruta: Path = SALIDA_LOCAL) -> Path:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return ruta


def subir_a_gcs(cliente: storage.Client, payload: dict, path: str = SALIDA_GCS) -> str:
    bucket = cliente.bucket(BUCKET)
    blob = bucket.blob(path)
    blob.upload_from_string(
        json.dumps(payload, indent=2, ensure_ascii=False),
        content_type="application/json",
    )
    return f"gs://{BUCKET}/{path}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Consolida manifests parciales de cada fuente.")
    parser.add_argument(
        "--subir-a-gcs",
        action="store_true",
        help="Sube tambien el manifest consolidado a gs://<bucket>/manifests/manifest.json",
    )
    parser.add_argument(
        "--salida-local",
        default=str(SALIDA_LOCAL),
        help=f"Ruta de salida local (default: {SALIDA_LOCAL})",
    )
    args = parser.parse_args()

    cliente = storage.Client(project=PROJECT_GCP)

    with Run("manifest_consolidar", contexto={"bucket": BUCKET}) as run:
        run.info("Consolidando manifests parciales del bucket gs://%s/", BUCKET)
        payload = consolidar(cliente)
        run.info(
            "Resumen: %d archivos en %d/%d fuentes (faltantes=%s)",
            payload["n_archivos"],
            len([f for f, v in payload["fuentes"].items() if v["presente"]]),
            len(payload["fuentes"]),
            ",".join(payload["faltantes"]) or "-",
        )
        ruta_local = escribir_local(payload, Path(args.salida_local))
        run.info("Manifest local: %s", ruta_local)
        evento(
            "manifest_local_escrito",
            ruta=str(ruta_local),
            n_archivos=payload["n_archivos"],
            size_bytes_total=payload["size_bytes_total"],
        )
        if args.subir_a_gcs:
            run.info("Subiendo a gs://%s/%s ...", BUCKET, SALIDA_GCS)
            ruta_gcs = subir_a_gcs(cliente, payload)
            run.info("Manifest en GCS: %s", ruta_gcs)
            evento("manifest_gcs_escrito", ruta=ruta_gcs)


if __name__ == "__main__":
    main()
