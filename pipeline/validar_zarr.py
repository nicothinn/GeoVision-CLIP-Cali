"""Validador de los paneles Zarr en GCS.

Para cada fuente en `config.FUENTES`, abre el Zarr correspondiente en
`gs://<bucket>/<prefijo>/panel.zarr` y reporta:

- presente / faltante,
- shape `(time, band, y, x)`,
- numero de bandas vs `len(cfg["bandas"])`,
- rango temporal (primer y ultimo `img_id`),
- chunks y dtype,
- porcentaje de NaN aproximado (muestreado, no carga todo en RAM).

Sale con codigo 0 si todos los paneles existen y son consistentes con la
configuracion; codigo 1 si alguno falta o esta corrupto.

Uso (PowerShell):
    python pipeline\\validar_zarr.py
    python pipeline\\validar_zarr.py --fuente no2
    python pipeline\\validar_zarr.py --json
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

import silenciar_warnings  # noqa: F401

import argparse
import json
import math

import gcsfs
import numpy as np
import xarray as xr

from config import BUCKET, FUENTES, PROJECT_GCP, get_fuente
from trazabilidad import Run, evento


def _abrir_zarr(prefijo: str) -> xr.Dataset:
    fs = gcsfs.GCSFileSystem(project=PROJECT_GCP)
    mapper = fs.get_mapper(f"{BUCKET}/{prefijo}/panel.zarr")
    return xr.open_zarr(mapper, consolidated=True)


def _pct_nan_muestreado(da: xr.DataArray, n_muestras: int = 4) -> float:
    """Estima % de NaN tomando n_muestras pasos de tiempo equiespaciados."""
    n_t = int(da.sizes.get("time", 0))
    if n_t == 0:
        return float("nan")
    idx = np.linspace(0, n_t - 1, min(n_muestras, n_t), dtype=int)
    sub = da.isel(time=idx).values
    if sub.size == 0:
        return float("nan")
    return float(np.isnan(sub).mean() * 100.0)


def validar_fuente(fuente_id: str) -> dict:
    cfg = FUENTES[fuente_id]
    prefijo = cfg["prefijo"]
    bandas_cfg = list(cfg["bandas"])
    info: dict = {
        "fuente": fuente_id,
        "prefijo": prefijo,
        "uri": f"gs://{BUCKET}/{prefijo}/panel.zarr",
        "ok": False,
        "presente": False,
        "bandas_esperadas": bandas_cfg,
    }
    try:
        ds = _abrir_zarr(prefijo)
    except Exception as exc:
        info["error"] = f"no se pudo abrir Zarr: {exc}"
        return info

    info["presente"] = True
    da = ds["data"] if "data" in ds.variables else None
    if da is None:
        info["error"] = "variable 'data' no existe en el Zarr"
        return info

    dims = {k: int(v) for k, v in da.sizes.items()}
    info.update(
        shape=dims,
        dtype=str(da.dtype),
        chunks=tuple(map(int, da.chunks[0])) if da.chunks else None,
    )
    info["chunks_por_dim"] = (
        {dim: int(c[0]) for dim, c in zip(da.dims, da.chunks)} if da.chunks else None
    )

    n_band = dims.get("band", 0)
    info["n_bandas"] = n_band
    info["n_bandas_match"] = n_band == len(bandas_cfg)

    times = ds["time"].values if "time" in ds.coords else np.array([])
    if times.size:
        info["time_inicio"] = str(times[0])
        info["time_fin"] = str(times[-1])
        info["n_timesteps"] = int(times.size)
    else:
        info["n_timesteps"] = 0

    info["pct_nan_muestreado"] = _pct_nan_muestreado(da)

    info["ok"] = (
        info["n_bandas_match"]
        and info["n_timesteps"] > 0
        and not math.isnan(info["pct_nan_muestreado"])
    )
    return info


def _imprimir(info: dict) -> None:
    estado = "OK " if info.get("ok") else "FAIL"
    print(f"[{estado}] {info['fuente']:<32s}  {info['uri']}")
    if "error" in info:
        print(f"        ! {info['error']}")
        return
    shape = info.get("shape", {})
    print(
        f"        timesteps={info.get('n_timesteps', 0):<5d} "
        f"bandas={info.get('n_bandas', 0)}/{len(info.get('bandas_esperadas', []))}"
        f"  shape={shape}  dtype={info.get('dtype')}"
    )
    if info.get("time_inicio"):
        print(f"        rango={info['time_inicio']} -> {info['time_fin']}")
    if not math.isnan(info.get("pct_nan_muestreado", float("nan"))):
        print(f"        nan%={info['pct_nan_muestreado']:.2f} (muestreado)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida los paneles Zarr en GCS.")
    parser.add_argument(
        "--fuente",
        default=None,
        help="alias o id; si se omite, valida todas las fuentes de config.FUENTES.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emite solo JSON con los resultados (sin tabla humana).",
    )
    args = parser.parse_args()

    if args.fuente is not None:
        cfg = get_fuente(args.fuente)
        fuente_ids = [cfg.get("id") or args.fuente]
    else:
        fuente_ids = list(FUENTES.keys())

    resultados: list[dict] = []
    with Run("validar_zarr", contexto={"fuentes": fuente_ids}) as run:
        for fid in fuente_ids:
            run.info("Validando %s ...", fid)
            info = validar_fuente(fid)
            evento("validar_zarr_resultado", **{k: v for k, v in info.items() if k != "bandas_esperadas"})
            resultados.append(info)
            if not args.json:
                _imprimir(info)
        ok_total = sum(1 for r in resultados if r.get("ok"))
        run.info("Resumen: %d/%d fuentes OK", ok_total, len(resultados))

    if args.json:
        print(json.dumps(resultados, indent=2, ensure_ascii=False, default=str))

    if any(not r.get("ok") for r in resultados):
        sys.exit(1)


if __name__ == "__main__":
    main()
