"""Agrega covariables ERA5+MODIS como canales extra al tensor X existente.

Carga X_convlstm.npy (522 canales), reconstruye la asignacion secuencia->tiles
desde metadatos, extrae covariables, y genera tensor con 531 canales.

Uso:
    python pipeline/inyectar_covariables.py
"""

import warnings
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm

warnings.filterwarnings("ignore")

DATA_DIR = Path("./dataset_sit2")
SIT3_DIR = Path("./dataset_sit3")
OUTPUT_DIR = Path("./dataset_sit3_extra")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CELL_RES = 0.05
SEQ_LEN = 8

# Columnas de covariables que se inyectaran como canales extra (broadcast)
# Ordenadas: primero basicas, luego derivadas (opcional)
COV_CHANNELS = [
    "era5_t2m",
    "era5_blh",
    "era5_wind_speed",
    "era5_sp",
    "era5_tp",
    "modis_aod_055",
    "era5_t2m_delta",
    "era5_blh_delta",
    "era5_wind_speed_delta",
]

print("=" * 60)
print("  INYECTAR COVARIABLES AL TENSOR")
print("=" * 60)

# 1. Cargar metadatos
print("\n[1] Cargando metadatos...")
df = pd.read_parquet(DATA_DIR / "metadatos.parquet")
df["fecha_dt"] = pd.to_datetime(df["fecha"])
print(f"  {len(df)} tiles")

# 2. Cargar covariables
print("\n[2] Cargando covariables...")
cov = pd.read_parquet(DATA_DIR / "covariables.parquet")
print(f"  {cov.shape}")

# Merge covariables a metadatos
if "tile_id" in df.columns and "tile_id" in cov.columns:
    df = df.merge(cov, on="tile_id", suffixes=("", "_cov"))
else:
    cov = cov.reset_index(drop=True)
    df = df.reset_index(drop=True).join(cov)
print(f"  Merge OK. Total columnas: {len(df.columns)}")

# 3. Reconstruir agrupacion por celda (misma logica que generar_secuencias)
print("\n[3] Reconstruyendo secuencias...")
df["celda_lat"] = (df["centroide_lat"] / CELL_RES).round() * CELL_RES
df["celda_lon"] = (df["centroide_lon"] / CELL_RES).round() * CELL_RES

# Reconstruir las mismas secuencias que genero generar_tensor_convlstm.py
sequences = []  # cada elemento: lista de 8 indices df
grouped = df.groupby(["celda_lat", "celda_lon"])
for (clat, clon), grp in grouped:
    ord_grp = grp.sort_values("fecha_dt")
    fechas_u = ord_grp["fecha_dt"].unique()
    if len(fechas_u) < SEQ_LEN:
        continue
    for i in range(len(fechas_u) - SEQ_LEN + 1):
        ventana = fechas_u[i:i + SEQ_LEN]
        rows = [ord_grp[ord_grp["fecha_dt"] == f].iloc[0] for f in ventana]
        sequences.append(rows)

print(f"  Secuencias reconstruidas: {len(sequences)}")

# Verificar que coincida con el tensor existente
X_existing = np.load(SIT3_DIR / "X_convlstm.npy", mmap_mode="r")
assert len(sequences) == len(X_existing), (
    f"Numero de secuencias no coincide: {len(sequences)} vs tensor {len(X_existing)}"
)
print(f"  Tensor existente: {X_existing.shape}")

# 4. Construir canales extra para cada secuencia
print("\n[4] Construyendo canales de covariables...")
N_COV = len(COV_CHANNELS)
X_extra = np.zeros((len(sequences), SEQ_LEN, N_COV, 5, 5), dtype=np.float32)

for si, rows in enumerate(tqdm(sequences, desc="Covariables")):
    for ti in range(SEQ_LEN):
        row = rows[ti]
        for ci, col in enumerate(COV_CHANNELS):
            val = row.get(col, 0.0)
            if not np.isfinite(val):
                val = 0.0
            X_extra[si, ti, ci, :, :] = val

print(f"  Canales extra shape: {X_extra.shape}")

# 5. Concatenar y guardar
print("\n[5] Concatenando y guardando...")
# Cargar X completo (puede ser grande)
X_full = X_existing[:]  # load completo en memoria
print(f"  X original: {X_full.shape}")

X_new = np.concatenate([X_full, X_extra], axis=2)
print(f"  X nuevo: {X_new.shape}")

# Cargar y (sin cambios)
y = np.load(SIT3_DIR / "y_convlstm.npy")
print(f"  y: {y.shape}")

# Guardar
np.save(OUTPUT_DIR / "X_convlstm.npy", X_new)
np.save(OUTPUT_DIR / "y_convlstm.npy", y)
print(f"\n[OK] Tensor guardado en {OUTPUT_DIR}/")

# Mostrar mapeo canales
print(f"\n  Canales: 0-511 embedding, 512-521 codificacion, "
      f"522-{521+N_COV} covariables")
for i, col in enumerate(COV_CHANNELS):
    print(f"    Canal {522+i}: {col}")

# Estadisticas basicas
print(f"\n  Stats covariables (mean+-std):")
for i, col in enumerate(COV_CHANNELS):
    vals = X_extra[:, :, i, :, :].ravel()
    vals = vals[vals != 0]
    if len(vals) > 0:
        print(f"    {col:25s}: {float(vals.mean()):.4f} +- {float(vals.std()):.4f}")

print("\n" + "=" * 60)
print("  COMPLETADO")
print("=" * 60)
