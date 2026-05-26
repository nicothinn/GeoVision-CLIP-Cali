"""Script para Kaggle: descarga paneles, extrae covariables, inyecta y re-entrena.

Uso en Kaggle (primera celda nueva del notebook):
    %run pipeline/preparar_y_entrenar_con_covariables.py
"""

import os, sys, warnings, json
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
from scipy.interpolate import RegularGridInterpolator
from sklearn.model_selection import train_test_split
from tqdm import tqdm

warnings.filterwarnings("ignore")
SEED = 42
np.random.seed(SEED)

DATA_DIR = Path("/content/dataset_sit2")
SIT3_DIR = Path("/content/dataset_sit3")
PANEL_DIR = Path("/content/panels")
CELL_RES = 0.05
SEQ_LEN = 8
HORIZONS = [1, 3, 7]
GRID_SIZE = 5
STRIDE = 0.005

# Variables a extraer
ERA5_VARS_MAP = {
    "temperature_2m": "era5_t2m",
    "boundary_layer_height": "era5_blh",
    "surface_pressure": "era5_sp",
    "total_precipitation": "era5_tp",
}

COV_CHANNELS = [
    "era5_t2m", "era5_blh", "era5_wind_speed",
    "era5_sp", "era5_tp", "modis_aod_055",
    "era5_t2m_delta", "era5_blh_delta", "era5_wind_speed_delta",
]


def download_panels():
    """Descarga paneles ERA5 y MODIS desde HF a Kaggle."""
    from huggingface_hub import snapshot_download
    print("\n[1] Descargando paneles ERA5 y MODIS...")

    PANEL_DIR.mkdir(parents=True, exist_ok=True)

    for folder in ["ERA-5", "MODIS_MCD"]:
        dst = PANEL_DIR / folder / "panel.zarr"
        if dst.exists():
            print(f"  {folder}: ya existe, saltando")
            continue
        print(f"  {folder}: descargando...")
        snapshot_download(
            repo_id="Slucu-0310/geovision-cali-panel",
            repo_type="dataset",
            allow_patterns=f"{folder}/panel.zarr/**",
            local_dir=str(PANEL_DIR),
        )
    print("  OK: paneles descargados")


def load_era5_panel():
    return xr.open_zarr(str(PANEL_DIR / "ERA-5" / "panel.zarr"), consolidated=True)


def load_modis_panel():
    return xr.open_zarr(str(PANEL_DIR / "MODIS_MCD" / "panel.zarr"), consolidated=True)


def extract_era5(era5_ds, df):
    """Extrae y computa features ERA5."""
    print("\n[2] Extrayendo ERA5...")
    times = pd.to_datetime(era5_ds.time.values)
    y_vals = era5_ds.y.values
    x_vals = era5_ds.x.values
    data = era5_ds["data"].values  # (T, bandas, 2, 2)

    band_names = list(era5_ds.band.values)
    idx_map = {
        "era5_t2m": band_names.index("temperature_2m"),
        "era5_blh": band_names.index("boundary_layer_height"),
        "era5_sp": band_names.index("surface_pressure"),
        "era5_tp": band_names.index("total_precipitation"),
    }
    idx_u = band_names.index("u_component_of_wind_10m")
    idx_v = band_names.index("v_component_of_wind_10m")

    rows = []
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="ERA5"):
        lat, lon = row["centroide_lat"], row["centroide_lon"]
        fecha = row["fecha_dt"]

        yi = int(np.argmin(np.abs(y_vals - lat)))
        xi = int(np.argmin(np.abs(x_vals - lon)))
        target = np.datetime64(fecha)
        ti = int(np.argmin(np.abs(times.values - target)))

        t2m = float(data[ti, idx_map["era5_t2m"], yi, xi])
        blh = float(data[ti, idx_map["era5_blh"], yi, xi])
        sp = float(data[ti, idx_map["era5_sp"], yi, xi])
        tp = float(data[ti, idx_map["era5_tp"], yi, xi])
        u10 = float(data[ti, idx_u, yi, xi])
        v10 = float(data[ti, idx_v, yi, xi])
        wind_speed = np.sqrt(u10**2 + v10**2)

        rows.append({
            "era5_t2m": (t2m - 292.0) / 5.0 if np.isfinite(t2m) else 0,
            "era5_blh": blh / 1000.0 if np.isfinite(blh) else 0,
            "era5_wind_speed": wind_speed / 5.0 if np.isfinite(wind_speed) else 0,
            "era5_sp": (sp - 88000) / 2000.0 if np.isfinite(sp) else 0,
            "era5_tp": tp * 1000.0 if np.isfinite(tp) else 0,
        })

    era5_df = pd.DataFrame(rows)

    # Deltas
    for col in list(era5_df.columns):
        era5_df[f"{col}_delta"] = era5_df[col].diff().fillna(0)

    # Rolling 3d
    for col in list(era5_df.columns):
        if not col.endswith("_delta"):
            era5_df[f"{col}_roll3"] = era5_df[col].rolling(3, min_periods=1).mean()

    for col in era5_df.columns:
        df[col] = era5_df[col].values

    nz = {c: int((df[c] != 0).sum()) for c in COV_CHANNELS[:5]}
    print(f"  OK: {len(df)} tiles, nonzero counts: {nz}")
    return df


def extract_modis(modis_ds, df):
    """Extrae MODIS AOD 550nm con interpolacion."""
    print("\n[3] Extrayendo MODIS AOD...")
    raw_times = modis_ds.time.values
    modis_dates = []
    for t in raw_times:
        parts = str(t).split("_")
        if len(parts) >= 2:
            try:
                d = parts[1][1:9]  # A2018001
                modis_dates.append(np.datetime64(f"{d[:4]}-{d[4:7]}"))
            except:
                modis_dates.append(np.datetime64("NaT"))
        else:
            modis_dates.append(np.datetime64("NaT"))
    modis_dates = np.array(modis_dates)

    aod_idx = list(modis_ds.band.values).index("Optical_Depth_055")
    modis_y = modis_ds.y.values
    modis_x = modis_ds.x.values

    valid_mask = ~np.isnat(modis_dates)
    aod_vals = []
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="MODIS"):
        lat_c, lon_c = row["centroide_lat"], row["centroide_lon"]
        target = np.datetime64(row["fecha_dt"])

        diff = np.abs(modis_dates - target)
        diff[~valid_mask] = np.timedelta64(999, "D")
        nearest = int(np.argmin(diff))

        if diff[nearest] > np.timedelta64(5, "D"):
            aod_vals.append(0.0)
            continue

        aod_slice = modis_ds["data"].isel(time=nearest, band=aod_idx).values
        aod_clean = np.nan_to_num(aod_slice, nan=0.0)

        if not np.isfinite(aod_clean).any():
            aod_vals.append(0.0)
            continue

        half = (GRID_SIZE - 1) / 2
        lats_tile = np.linspace(lat_c - half * STRIDE, lat_c + half * STRIDE, GRID_SIZE)
        lons_tile = np.linspace(lon_c - half * STRIDE, lon_c + half * STRIDE, GRID_SIZE)

        try:
            interp = RegularGridInterpolator(
                (modis_y, modis_x), aod_clean, bounds_error=False, fill_value=0.0
            )
            lon_grid, lat_grid = np.meshgrid(lons_tile, lats_tile)
            pts = np.stack([lat_grid.ravel(), lon_grid.ravel()], axis=1)
            aod_5x5 = interp(pts).reshape(GRID_SIZE, GRID_SIZE)
            aod_vals.append(float(np.nanmean(aod_5x5)))
        except Exception:
            aod_vals.append(0.0)

    df["modis_aod_055"] = aod_vals
    nz = int((df["modis_aod_055"] != 0).sum())
    print(f"  OK: MODIS AOD extraido, nonzero={nz}/{len(df)}")
    return df


def reconstruct_sequences(df):
    """Reconstruye las mismas 1403 secuencias que el pipeline original."""
    df["celda_lat"] = (df["centroide_lat"] / CELL_RES).round() * CELL_RES
    df["celda_lon"] = (df["centroide_lon"] / CELL_RES).round() * CELL_RES

    sequences = []
    grouped = df.groupby(["celda_lat", "celda_lon"])
    for (clat, clon), grp in grouped:
        ord_grp = grp.sort_values("fecha_dt")
        fechas_u = ord_grp["fecha_dt"].unique()
        if len(fechas_u) < SEQ_LEN:
            continue
        for i in range(len(fechas_u) - SEQ_LEN + 1):
            ventana = fechas_u[i : i + SEQ_LEN]
            rows = [ord_grp[ord_grp["fecha_dt"] == f].iloc[0] for f in ventana]
            sequences.append(rows)
    return sequences


def inject_covariables(sequences, X_existing):
    """Inyecta 9 canales de covariables al tensor existente."""
    print(f"\n[4] Inyectando covariables (522 -> 531 canales)...")
    n_cov = len(COV_CHANNELS)
    X_extra = np.zeros((len(sequences), SEQ_LEN, n_cov, 5, 5), dtype=np.float32)

    zeros_found = 0
    for si, rows in enumerate(tqdm(sequences, desc="Inyectando")):
        for ti in range(SEQ_LEN):
            row = rows[ti]
            for ci, col in enumerate(COV_CHANNELS):
                val = row.get(col, 0.0)
                if not np.isfinite(val):
                    val = 0.0
                    zeros_found += 1
                X_extra[si, ti, ci, :, :] = val

    print(f"  Values set to zero (NaN/invalid): {zeros_found}")

    X_new = np.concatenate([X_existing, X_extra], axis=2)
    print(f"  X: {X_existing.shape} -> {X_new.shape}")

    # Check non-zero
    for ci, col in enumerate(COV_CHANNELS):
        nz = int(np.count_nonzero(X_extra[:, :, ci, :, :]))
        print(f"    Canal {522+ci} {col:25s}: nonzero={nz}/{X_extra[:,:,ci,:,:].size}")

    y = np.load(SIT3_DIR / "y_convlstm.npy")
    return X_new, y


def main():
    print("=" * 70)
    print("  PIPELINE COVARIABLES COMPLETO (Kaggle)")
    print("=" * 70)

    # 1. Download panels
    download_panels()

    # 2. Load metadata and existing tensor
    print("\nCargando metadatos y tensor existente...")
    df = pd.read_parquet(DATA_DIR / "metadatos.parquet")
    df["fecha_dt"] = pd.to_datetime(df["fecha"])
    print(f"  Metadatos: {len(df)} tiles")

    X_existing = np.load(SIT3_DIR / "X_convlstm.npy", mmap_mode="r")
    print(f"  X existente: {X_existing.shape}")

    # 3. Extract ERA5
    era5_ds = load_era5_panel()
    df = extract_era5(era5_ds, df)

    # 4. Extract MODIS
    modis_ds = load_modis_panel()
    df = extract_modis(modis_ds, df)

    # 5. Reconstruct sequences
    print("\nReconstruyendo secuencias...")
    sequences = reconstruct_sequences(df)
    print(f"  Secuencias: {len(sequences)}")
    assert len(sequences) == len(X_existing), f"Mismatch: {len(sequences)} vs {len(X_existing)}"

    # 6. Inject and save
    X_new, y = inject_covariables(sequences, X_existing)

    out_dir = Path("/content/dataset_sit3_extra")
    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "X_convlstm.npy", X_new)
    np.save(out_dir / "y_convlstm.npy", y)
    print(f"\n[OK] Tensor guardado en {out_dir}/")
    print(f"  Shape: {X_new.shape}")
    print("=" * 70)


if __name__ == "__main__":
    main()
