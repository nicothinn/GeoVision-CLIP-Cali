"""Prepara covariables espacio-temporales para ConvLSTM (Sit. 3).

Carga metadatos.parquet de dataset_sit2/ y genera covariables.parquet
con features adicionales para el entrenamiento del ConvLSTM:

  - Features temporales: day-of-year (sin/cos), mes (sin/cos)
  - Indices espectrales: NDVI, BSI, NDBI (ya en metadatos)
  - Contaminantes S5P: no2, so2, o3 normalizados por percentiles
  - Posicion: lat, lon normalizados
  - Gap desde ultimo tile disponible

OPCIONAL: si encuentra archivos ERA5/MODIS (desde HF o locales),
los cruza con cada tile y agrega columnas de covariables ambientales.

Uso:
    python pipeline/preparar_covariables_convlstm.py
    python pipeline/preparar_covariables_convlstm.py --era5-path ./data/era5.zarr --modis-path ./data/modis.zarr

Requiere: pandas, numpy, zarr, xarray (opcional para ERA5/MODIS).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA_DIR = ROOT / "dataset_sit2"
EDA_DIR = ROOT / "eda_sit2"

SEED = 42


def _cargar_metadatos() -> pd.DataFrame:
    """Carga metadatos.parquet y parsea fechas."""
    path = DATA_DIR / "metadatos.parquet"
    if not path.is_file():
        raise FileNotFoundError(f"No se encuentra {path}")
    df = pd.read_parquet(path)
    df["fecha_dt"] = pd.to_datetime(df["fecha"])
    return df


def _cargar_percentiles() -> dict[str, dict[str, float]]:
    """Carga percentiles S5P desde dataset_sit2/percentiles.json."""
    path = DATA_DIR / "percentiles.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _agregar_features_temporales(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega codificacion temporal (dia/mes en sin/cos)."""
    doy = df["fecha_dt"].dt.dayofyear
    mes = df["fecha_dt"].dt.month

    df["doy_sin"] = np.sin(2 * np.pi * doy / 365.25).astype(np.float32)
    df["doy_cos"] = np.cos(2 * np.pi * doy / 365.25).astype(np.float32)
    df["mes_sin"] = np.sin(2 * np.pi * mes / 12).astype(np.float32)
    df["mes_cos"] = np.cos(2 * np.pi * mes / 12).astype(np.float32)

    return df


def _agregar_posicion(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega lat/lon normalizados (z-score)."""
    lat = df["centroide_lat"].values.astype(np.float32)
    lon = df["centroide_lon"].values.astype(np.float32)

    df["lat_norm"] = (lat - lat.mean()) / (lat.std() + 1e-8)
    df["lon_norm"] = (lon - lon.mean()) / (lon.std() + 1e-8)

    return df


def _agregar_s5p_normalizado(df: pd.DataFrame, pct: dict) -> pd.DataFrame:
    """Normaliza NO2/SO2/O3 usando percentiles como referencia."""
    for pol, col in [("NO2", "no2"), ("SO2", "so2"), ("O3", "o3")]:
        vals = df[col].values.copy().astype(np.float32)
        # Manejar NaN
        nan_mask = np.isnan(vals)
        if nan_mask.any():
            # Imputar con la mediana del percentil p50
            p50 = pct.get(pol, {}).get("p50", np.nanmedian(vals[~nan_mask]))
            vals[nan_mask] = p50 if np.isfinite(p50) else 0.0

        # Normalizar con p50 y p90 (centrado y escalado robusto)
        p50_val = pct.get(pol, {}).get("p50", np.nanmedian(vals))
        p90_val = pct.get(pol, {}).get("p90", np.nanpercentile(vals, 90))
        iqr = p90_val - p50_val if p90_val > p50_val else 1.0
        df[f"{col}_norm"] = ((vals - p50_val) / (iqr + 1e-12)).astype(np.float32)
        df[f"{col}_log"] = np.log1p(np.maximum(vals, 0)).astype(np.float32)

    return df


def _agregar_gap_temporal(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula el gap en dias desde el tile anterior en la misma celda 0.05°."""
    # Agrupar por celda 0.05°
    celda_lat = (df["centroide_lat"] / 0.05).round() * 0.05
    celda_lon = (df["centroide_lon"] / 0.05).round() * 0.05

    df["gap_dias_desde_anterior"] = np.nan

    for (clat, clon), grp_idx in df.groupby([celda_lat, celda_lon]).groups.items():
        idx = grp_idx.values
        sub = df.loc[idx].sort_values("fecha_dt")
        if len(sub) >= 2:
            gaps = sub["fecha_dt"].diff().dt.days.values
            df.loc[sub.index, "gap_dias_desde_anterior"] = gaps

    df["gap_dias_desde_anterior"] = (
        df["gap_dias_desde_anterior"]
        .fillna(30)
        .astype(np.float32)
    )

    return df


def _intentar_cargar_era5(path: str | None, df: pd.DataFrame) -> pd.DataFrame:
    """Si se proporciona ruta a Zarr ERA5, extrae valores para cada tile."""
    if path is None:
        df["era5_t2m"] = np.float32(0.0)
        df["era5_blh"] = np.float32(0.0)
        df["era5_wind_u"] = np.float32(0.0)
        df["era5_wind_v"] = np.float32(0.0)
        df["era5_presion"] = np.float32(0.0)
        return df

    try:
        import xarray as xr

        ds = xr.open_zarr(path)
        print(f"ERA5 cargado: {ds}")

        # Para cada tile, extraer el punto mas cercano
        t2m_vals, blh_vals = [], []
        wu_vals, wv_vals, pres_vals = [], [], []

        for _, row in df.iterrows():
            lat, lon = row["centroide_lat"], row["centroide_lon"]
            fecha = row["fecha_dt"]

            try:
                punto = ds.sel(
                    latitude=lat, longitude=lon, time=fecha, method="nearest"
                )
                t2m_vals.append(float(punto["temperature_2m"].values))
                blh_vals.append(float(punto["boundary_layer_height"].values))
                wu_vals.append(float(punto["u_component_of_wind_10m"].values))
                wv_vals.append(float(punto["v_component_of_wind_10m"].values))
                pres_vals.append(float(punto["surface_pressure"].values))
            except Exception:
                t2m_vals.append(np.nan)
                blh_vals.append(np.nan)
                wu_vals.append(np.nan)
                wv_vals.append(np.nan)
                pres_vals.append(np.nan)

        df["era5_t2m"] = np.array(t2m_vals, dtype=np.float32)
        df["era5_blh"] = np.array(blh_vals, dtype=np.float32)
        df["era5_wind_u"] = np.array(wu_vals, dtype=np.float32)
        df["era5_wind_v"] = np.array(wv_vals, dtype=np.float32)
        df["era5_presion"] = np.array(pres_vals, dtype=np.float32)
        print("ERA5 extraido correctamente para todos los tiles.")
    except Exception as e:
        print(f"ERROR cargando ERA5: {e}")
        print("Usando valores por defecto (0.0).")
        for c in ["era5_t2m", "era5_blh", "era5_wind_u", "era5_wind_v", "era5_presion"]:
            df[c] = np.float32(0.0)

    return df


def _intentar_cargar_modis(path: str | None, df: pd.DataFrame) -> pd.DataFrame:
    """Si se proporciona ruta a Zarr MODIS, extrae valores para cada tile."""
    if path is None:
        df["modis_aod_047"] = np.float32(0.0)
        df["modis_aod_055"] = np.float32(0.0)
        return df

    try:
        import xarray as xr

        ds = xr.open_zarr(path)
        print(f"MODIS cargado: {ds}")

        aod47_vals, aod55_vals = [], []
        for _, row in df.iterrows():
            lat, lon = row["centroide_lat"], row["centroide_lon"]
            fecha = row["fecha_dt"]
            try:
                punto = ds.sel(
                    latitude=lat, longitude=lon, time=fecha, method="nearest"
                )
                aod47_vals.append(float(punto["Optical_Depth_047"].values))
                aod55_vals.append(float(punto["Optical_Depth_055"].values))
            except Exception:
                aod47_vals.append(np.nan)
                aod55_vals.append(np.nan)

        df["modis_aod_047"] = np.array(aod47_vals, dtype=np.float32)
        df["modis_aod_055"] = np.array(aod55_vals, dtype=np.float32)
        print("MODIS extraido correctamente para todos los tiles.")
    except Exception as e:
        print(f"ERROR cargando MODIS: {e}")
        print("Usando valores por defecto (0.0).")
        df["modis_aod_047"] = np.float32(0.0)
        df["modis_aod_055"] = np.float32(0.0)

    return df


def _conversion_unidades_s5p(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte S5P de mol/m2 a ug/m3 (referencia para ConvLSTM)."""
    # NO2: mol/m2 -> ug/m3 (asumiendo altura trop. 8km para Cali)
    # 1 mol/m2 / 8000m = mol/m3; * 46.005 g/mol * 1e6 = ug/m3
    for pol, col, masa_molar in [
        ("NO2", "no2", 46.005),
        ("SO2", "so2", 64.064),
        ("O3", "o3", 48.0),
    ]:
        vals = df[col].values.copy()
        nan_mask = np.isnan(vals)
        vals[nan_mask] = 0.0
        altura_trop = 8000.0  # metros (Cali ~1000m, tropico)
        ugm3 = vals / altura_trop * masa_molar * 1e6
        ugm3 = np.maximum(ugm3, 0)  # valores negativos -> 0
        df[f"{col}_ugm3"] = ugm3.astype(np.float32)

    return df


def _generar_resumen(df: pd.DataFrame, out_dir: Path) -> dict:
    """Genera JSON resumen de las covariables."""
    resumen = {
        "n_tiles_total": len(df),
        "columnas_covariables": [c for c in df.columns if c not in [
            "tile_id", "clase", "descripcion", "fecha", "img_id_s2",
            "fecha_dt", "split"
        ]],
        "n_covariables": len(df.columns) - 7,
        "columnas_con_nan": {
            c: int(df[c].isna().sum())
            for c in df.columns
            if df[c].isna().any() and c not in ["tile_id", "descripcion"]
        },
    }

    (out_dir / "resumen_covariables.json").write_text(
        json.dumps(resumen, indent=2, default=str), encoding="utf-8"
    )
    return resumen


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Prepara covariables para ConvLSTM (Sit. 3)."
    )
    p.add_argument(
        "--era5-path",
        default=None,
        help="Ruta a Zarr ERA5 (opcional, si no se provee usa defaults 0)",
    )
    p.add_argument(
        "--modis-path",
        default=None,
        help="Ruta a Zarr MODIS (opcional, si no se provee usa defaults 0)",
    )
    p.add_argument(
        "--data-dir",
        type=Path,
        default=DATA_DIR,
        help=f"Carpeta dataset_sit2/ (default: {DATA_DIR})",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    data_dir = args.data_dir

    print("=" * 55)
    print("  PREPARAR COVARIABLES CONVLSTM (Sit. 3)")
    print("=" * 55)

    # 1. Cargar metadatos
    print("\n[1/7] Cargando metadatos.parquet...")
    df = _cargar_metadatos()
    print(f"  Tiles cargados: {len(df)}")

    # 2. Cargar percentiles
    print("\n[2/7] Cargando percentiles S5P...")
    pct = _cargar_percentiles()
    print(f"  Contaminantes: {list(pct.keys())}")

    # 3. Features temporales
    print("\n[3/7] Agregando features temporales...")
    df = _agregar_features_temporales(df)
    print(f"  Columnas: doy_sin, doy_cos, mes_sin, mes_cos")

    # 4. Posicion
    print("\n[4/7] Agregando codificacion de posicion...")
    df = _agregar_posicion(df)
    print(f"  Columnas: lat_norm, lon_norm")

    # 5. S5P normalizado + conversion a ug/m3
    print("\n[5/7] Normalizando contaminantes S5P...")
    df = _agregar_s5p_normalizado(df, pct)
    df = _conversion_unidades_s5p(df)
    print(f"  Columnas: no2_norm, so2_norm, o3_norm, no2_log, *_ugm3")

    # 6. Gap temporal
    print("\n[6/7] Calculando gap temporal...")
    df = _agregar_gap_temporal(df)
    print(f"  Columna: gap_dias_desde_anterior")

    # 7. ERA5 y MODIS (opcional)
    print("\n[7/7] Covariables ambientales (ERA5/MODIS)...")
    df = _intentar_cargar_era5(args.era5_path, df)
    df = _intentar_cargar_modis(args.modis_path, df)

    # Guardar
    out_path = data_dir / "covariables.parquet"
    cols_guardar = [
        "tile_id", "fecha", "centroide_lat", "centroide_lon",
        "clase", "split",
        "ndvi", "bsi", "ndbi",
        "no2", "so2", "o3",
        "no2_norm", "so2_norm", "o3_norm",
        "no2_log", "so2_log", "o3_log",
        "no2_ugm3", "so2_ugm3", "o3_ugm3",
        "doy_sin", "doy_cos", "mes_sin", "mes_cos",
        "lat_norm", "lon_norm",
        "gap_dias_desde_anterior",
        "era5_t2m", "era5_blh", "era5_wind_u", "era5_wind_v", "era5_presion",
        "modis_aod_047", "modis_aod_055",
    ]
    cols_existentes = [c for c in cols_guardar if c in df.columns]
    df_out = df[cols_existentes].copy()

    df_out.to_parquet(out_path, index=False)
    print(f"\nOK Covariables guardadas en: {out_path}")
    print(f"   Shape: {df_out.shape[0]} tiles x {df_out.shape[1]} columnas")
    print(f"   Columnas: {df_out.columns.tolist()}")

    # Resumen
    resumen = _generar_resumen(df_out, data_dir)
    print(f"\nResumen guardado en: {data_dir / 'resumen_covariables.json'}")

    # Mostrar estadisticas basicas
    print("\nEstadisticas basicas (columnas numericas):")
    print(df_out.describe().round(4).to_string())


if __name__ == "__main__":
    main()
