"""Precomputar covariables ERA5+MODIS para inyectar como canales extra en tensor ConvLSTM.

Genera un .parquet con una fila por tile (2263) que contiene:
  - Variables ERA5: t2m, blh, wind_speed, presion, precipitacion
  - Derivadas temporales: delta diario, rolling 3d
  - MODIS AOD 550nm: interpolado a 5x5 + promedio espacial

Uso:
    python pipeline/preparar_covariables_convlstm.py \\
        --data-dir ./dataset_sit2 \\
        --output ./dataset_sit2/covariables.parquet
"""

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from scipy.interpolate import RegularGridInterpolator
from tqdm import tqdm

warnings.filterwarnings("ignore")

SEED = 42
np.random.seed(SEED)

# Variables objetivo de ERA5 (segun recomendacion de Grok)
# Se usan 5: T2m, BLH, WindSpeed, Presion, Precipitacion
ERA5_VARS = {
    "temperature_2m": "t2m",
    "boundary_layer_height": "blh",
    "u_component_of_wind_10m": None,  # se combina en wind_speed
    "v_component_of_wind_10m": None,
    "surface_pressure": "sp",
    "total_precipitation": "tp",
}

# Bandas de interes de MODIS
MODIS_BAND = "Optical_Depth_055"  # AOD 550nm


def _parse_modis_filename(fname: str) -> str:
    """Extrae fecha YYYYMMDD del nombre de archivo MCD19A2."""
    # Formato: MCD19A2_A2018001_h10v08_061_2023114142810_01
    parts = fname.split("_")
    if len(parts) >= 2:
        return parts[1][1:9]  # "2018001" -> dia 1 de 2018
    return ""


def cargar_metadatos(data_dir: Path) -> pd.DataFrame:
    path = data_dir / "metadatos.parquet"
    df = pd.read_parquet(path)
    df["fecha_dt"] = pd.to_datetime(df["fecha"])
    print(f"[OK] Metadatos: {len(df)} filas")
    return df


def extraer_era5_features(
    era5_ds: xr.Dataset,
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Extrae variables ERA5 para cada tile y computa derivadas temporales.

    Para cada tile (con lat, lon, fecha):
    1. Busca el valor ERA5 mas cercano en espacio y tiempo
    2. Calcula delta diario y rolling mean 3d
    3. Retorna DataFrame con las features

    Nota: ERA5 tiene 2x2 sobre Cali. Se usa el pixel mas cercano (broadcast).
    """
    times = pd.to_datetime(era5_ds.time.values)
    y_vals = era5_ds.y.values
    x_vals = era5_ds.x.values

    # Pre-extraer arrays para acceso rapido
    # ERA5 data shape: (time, band, y, x)
    data = era5_ds["data"].values  # carga completa (43815, 7, 2, 2) ~ 5MB

    # Indices para cada variable
    band_names = list(era5_ds.band.values)
    idx_t2m = band_names.index("temperature_2m")
    idx_blh = band_names.index("boundary_layer_height")
    idx_u = band_names.index("u_component_of_wind_10m")
    idx_v = band_names.index("v_component_of_wind_10m")
    idx_sp = band_names.index("surface_pressure")
    idx_tp = band_names.index("total_precipitation")

    # Ordenar df por fecha para procesamiento secuencial
    df_sorted = df.sort_values("fecha_dt").reset_index(drop=True)

    cols = []
    for idx, row in tqdm(df_sorted.iterrows(), total=len(df_sorted), desc="ERA5"):
        lat, lon = row["centroide_lat"], row["centroide_lon"]
        fecha = row["fecha_dt"]

        # Encontrar pixel ERA5 mas cercano
        yi = int(np.argmin(np.abs(y_vals - lat)))
        xi = int(np.argmin(np.abs(x_vals - lon)))

        # Encontrar tiempo mas cercano (ERA5 tiene datos horarios)
        target = np.datetime64(fecha)
        ti = int(np.argmin(np.abs(times.values - target)))

        # Extraer valores
        t2m = float(data[ti, idx_t2m, yi, xi])  # Kelvin
        blh = float(data[ti, idx_blh, yi, xi])  # metros
        u10 = float(data[ti, idx_u, yi, xi])    # m/s
        v10 = float(data[ti, idx_v, yi, xi])    # m/s
        sp = float(data[ti, idx_sp, yi, xi])    # Pa
        tp = float(data[ti, idx_tp, yi, xi])    # m (precipitacion)

        # Velocidad del viento (invariante rotacional)
        wind_speed = np.sqrt(u10**2 + v10**2)

        cols.append({
            "era5_t2m": (t2m - 292.0) / 5.0,       # z-score aprox
            "era5_blh": blh / 1000.0,               # normalizar a km
            "era5_wind_speed": wind_speed / 5.0,    # z-score aprox
            "era5_sp": (sp - 88000.0) / 2000.0,     # z-score aprox
            "era5_tp": tp * 1000.0,                 # escalar a mm
        })

    era5_df = pd.DataFrame(cols)

    # Calcular derivadas temporales: delta diario
    deltas = era5_df.diff().fillna(0)
    for col in era5_df.columns:
        era5_df[f"{col}_delta"] = deltas[col].values

    # Rolling mean 3 dias
    for col in era5_df.columns:
        if not col.endswith("_delta"):
            era5_df[f"{col}_roll3"] = era5_df[col].rolling(3, min_periods=1).mean().values

    # Agregar al df original
    result = df_sorted.copy()
    for col in era5_df.columns:
        result[col] = era5_df[col].values

    print(f"[OK] Features ERA5: {len([c for c in result.columns if c.startswith('era5')])} columnas")
    return result


def extraer_modis_aod(
    modis_ds: xr.Dataset,
    df: pd.DataFrame,
    grid_size: int = 5,
    stride: float = 0.005,
) -> pd.DataFrame:
    """Extrae MODIS AOD 550nm para cada tile con interpolacion a 5x5.

    Para cada tile:
    1. Define grilla 5x5 centrada en el tile
    2. Interpola MODIS 43x43 a la grilla 5x5
    3. Guarda mean AOD como escalar + opcionalmente grid 5x5

    NOTA: Los nombres de tiempo MODIS son MCD19A2_A2018001_...
    Se parsea AAAA+DDD del nombre.
    """
    times_modis = modis_ds.time.values
    modis_y = modis_ds.y.values  # (43,) lat
    modis_x = modis_ds.x.values  # (43,) lon

    # Parsear fechas de nombres MODIS
    # Formato: MCD19A2_A2018001_h10v08_... -> AaaaDDD -> fecha real
    import datetime as dt
    times_modis = modis_ds.time.values
    modis_y = modis_ds.y.values
    modis_x = modis_ds.x.values

    modis_dates = []
    for t in times_modis:
        parts = str(t).split("_")
        if len(parts) >= 2:
            d = parts[1][1:9]  # "2018001"
            try:
                year = int(d[:4])
                doy = int(d[4:7])
                dt = np.datetime64(pd.Timestamp(year=year, month=1, day=1) + pd.Timedelta(days=doy-1))
                modis_dates.append(dt)
            except:
                modis_dates.append(np.datetime64("NaT"))
        else:
            modis_dates.append(np.datetime64("NaT"))
    modis_dates = np.array(modis_dates)

    # Band index
    band_names = list(modis_ds.band.values)
    aod_band_idx = band_names.index(MODIS_BAND)

    # Cargar data completa para acceso rapido
    # MODIS data shape: (140120, 4, 43, 43) pero no cargamos toda en memoria
    # En vez de eso, accedemos por fechas
    modis_data = modis_ds["data"]
    valid_mask = ~np.isnat(modis_dates)

    cols = []
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="MODIS AOD"):
        lat_c, lon_c = row["centroide_lat"], row["centroide_lon"]
        fecha = row["fecha_dt"]
        target = np.datetime64(fecha)

        # Buscar la fecha MODIS mas cercana (ventana +/- 5 dias)
        diff = np.abs(modis_dates - target)
        diff[~valid_mask] = np.timedelta64(999, "D")
        nearest = np.argmin(diff)

        if diff[nearest] > np.timedelta64(5, "D"):
            cols.append({"modis_aod_055": 0.0, "modis_aod_055_grid": None})
            continue

        # Extraer AOD del tile MODIS mas cercano
        aod_slice = modis_data.isel(time=nearest, band=aod_band_idx).values  # (43, 43)

        # Si todo es NaN, retornar 0
        if not np.isfinite(aod_slice).any():
            cols.append({"modis_aod_055": 0.0, "modis_aod_055_grid": None})
            continue

        # Rellenar NaNs con 0 para interpolacion
        aod_clean = np.nan_to_num(aod_slice, nan=0.0)

        # Crear grilla 5x5 del tile
        half = (grid_size - 1) / 2
        lats_tile = np.linspace(lat_c - half * stride, lat_c + half * stride, grid_size)
        lons_tile = np.linspace(lon_c - half * stride, lon_c + half * stride, grid_size)

        # Interpolar MODIS 43x43 a la grilla 5x5
        # MODIS coordinates are descending lat, ascending lon
        try:
            interp = RegularGridInterpolator(
                (modis_y, modis_x),
                aod_clean,
                bounds_error=False,
                fill_value=0.0,
            )
            lon_grid, lat_grid = np.meshgrid(lons_tile, lats_tile)
            points = np.stack([lat_grid.ravel(), lon_grid.ravel()], axis=1)
            aod_5x5 = interp(points).reshape(grid_size, grid_size)
            aod_mean = float(np.mean(aod_5x5))
        except Exception:
            aod_mean = 0.0
            aod_5x5 = np.zeros((grid_size, grid_size))

        cols.append({
            "modis_aod_055": aod_mean,
            "modis_aod_055_grid": aod_5x5,  # (5,5) con variacion espacial
        })

    modis_df = pd.DataFrame(cols)
    for col in modis_df.columns:
        df[col] = modis_df[col].values

    print(f"[OK] MODIS AOD extraido para {len(df)} tiles")
    return df


def main():
    p = argparse.ArgumentParser(description="Precomputar covariables ERA5+MODIS")
    p.add_argument("--data-dir", type=Path, default=Path("./dataset_sit2"))
    p.add_argument("--output", type=Path, default=Path("./dataset_sit2/covariables.parquet"))
    args = p.parse_args()

    print("=" * 60)
    print("  PRECOMPUTAR COVARIABLES Sit.3")
    print("=" * 60)

    # 1. Cargar metadatos
    print("\n[1] Cargando metadatos...")
    df = cargar_metadatos(args.data_dir)

    # 2. Extraer ERA5
    print("\n[2] Extrayendo ERA5...")
    # Usar paneles desde hf_panel_cache (dataset_sit2 solo tiene metadata)
    era5_path = Path("./hf_panel_cache/ERA-5/panel.zarr")
    if not era5_path.is_dir():
        era5_path = Path("./dataset_sit2/ERA-5_panel")
    era5_ds = xr.open_zarr(str(era5_path), consolidated=True)
    df = extraer_era5_features(era5_ds, df)

    # 3. Extraer MODIS AOD
    print("\n[3] Extrayendo MODIS AOD...")
    modis_path = Path("./hf_panel_cache/MODIS_MCD/panel.zarr")
    if not modis_path.is_dir():
        modis_path = Path("./dataset_sit2/MODIS_MCD_panel")
    modis_ds = xr.open_zarr(str(modis_path), consolidated=True)
    df = extraer_modis_aod(modis_ds, df)

    # 4. Guardar
    print(f"\n[4] Guardando covariables...")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Seleccionar solo columnas de covariables + tile_id para merge
    cov_cols = [c for c in df.columns if c.startswith(("era5_", "modis_")) or c == "tile_id"]
    if "tile_id" not in df.columns:
        df["tile_id"] = df.index.astype(str)
        cov_cols.insert(0, "tile_id")

    cov_df = df[cov_cols].copy()
    cov_df.to_parquet(args.output, index=False)
    print(f"[OK] Covariables guardadas: {args.output}")
    print(f"     Shape: {cov_df.shape}")
    print(f"     Columnas: {list(cov_df.columns)}")
    print("=" * 60)


def _parse_modinis_filename(fname: str) -> str:
    """Extrae fecha de nombre MCD19A2."""
    if isinstance(fname, str):
        parts = fname.split("_")
        if len(parts) >= 2:
            return parts[1][1:9]  # AAAA DDD
    return ""


if __name__ == "__main__":
    main()
