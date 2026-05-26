"""Crear notebook sit3-kriging-eval.ipynb"""
import json
import os

cells = []

def md(source):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": [source]})

def code(source):
    cells.append({"cell_type": "code", "metadata": {}, "source": [source], "outputs": []})

# ============================================================
# CELDA 0: Titulo
# ============================================================
md("""# Sit.3 -- ST-Kriging + Moran I sobre Conv3D

**Flujo:**
1. Carga DAGMA + checkpoint Conv3D + resultados LOO-CV
2. ST-Kriging puro como baseline (sin deep learning)
3. Kriging de residuos Conv3D (diagnostico espacial)
4. Moran I global + LISA local
5. Tabla comparativa: Conv3D vs Kriging vs Conv3D+Kriging
6. Mapas y exportacion

Dataset: Slucu-0310/geovision-cali-sit3 + Slucu-0310/dagma-cali
""")

# ============================================================
# CELDA 1: Instalacion e imports
# ============================================================
code("""# @title 1. Instalar dependencias e imports
!pip install -q pykrige libpysal esda huggingface_hub pandas numpy matplotlib scikit-learn

import os, json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from pykrige.ok import OrdinaryKriging
from libpysal.weights import DistanceBand
from esda.moran import Moran, Moran_Local

# Constantes globales
POLLUTANTS = ["NO2", "SO2", "O3"]
HORIZONS = [1, 3, 7]
BBOX = [-76.65, 3.30, -76.30, 3.65]
GRID_RES = 0.005  # ~500m
SEED = 42

WORKING = Path("/kaggle/working")
DATA = Path("/kaggle/input")

print("Dependencias OK: pykrige, libpysal, esda, huggingface_hub")
""")

# ============================================================
# CELDA 2: Cargar DAGMA
# ============================================================
code("""# @title 2. Cargar DAGMA desde HuggingFace

from huggingface_hub import hf_hub_download

print("Cargando DAGMA desde HF (Slucu-0310/dagma-cali)...")
dagma_path = hf_hub_download(
    repo_id="Slucu-0310/dagma-cali",
    filename="DAGMA_con_Acopi_NO2.parquet",
    repo_type="dataset",
    cache_dir=WORKING / "hf_cache",
)
dagma_raw = pd.read_parquet(dagma_path)
print(f"  DAGMA raw: {dagma_raw.shape}")

# Filtrar contaminantes de interes
dagma = dagma_raw[dagma_raw["gas"].isin(POLLUTANTS)].copy()
dagma["fecha"] = pd.to_datetime(dagma["fecha"])

# Agregar a diario por estacion y gas
dagma_diario = dagma.groupby(
    ["nombre_est", "latitud", "longitud", "gas", pd.Grouper(key="fecha", freq="D")]
)["concentracion"].mean().reset_index()

print(f"  DAGMA diario: {dagma_diario.shape}")
print(f"  Estaciones: {sorted(dagma_diario.nombre_est.unique())}")
print(f"  Rango: {dagma_diario.fecha.min()} -> {dagma_diario.fecha.max()}")

# Mostrar estadisticas por estacion y gas
print()
for gas in POLLUTANTS:
    sub = dagma_diario[dagma_diario.gas == gas]
    ests = sub.groupby("nombre_est").agg(
        n=("concentracion", "count"),
        mean=("concentracion", "mean"),
        lat=("latitud", "first"),
        lon=("longitud", "first"),
    ).round(1)
    print(f"\\n{gas}: {len(ests)} estaciones")
    print(ests.to_string())

# Extraer coordenadas unicas por estacion
estaciones = dagma_diario.groupby("nombre_est").agg(
    lat=("latitud", "first"),
    lon=("longitud", "first"),
).reset_index()
print(f"\\nEstaciones con coordenadas: {len(estaciones)}")
print(estaciones.to_string())
""")

# ============================================================
# CELDA 3: ST-Kriging puro (baseline)
# ============================================================
code("""# @title 3. ST-Kriging puro como baseline

# Kriging puro: interpola DAGMA usando solo coordenadas (sin deep learning).
# Usa la mediana historica por estacion como target.

# Grilla de prediccion
lat_grid = np.arange(BBOX[1], BBOX[3], GRID_RES)
lon_grid = np.arange(BBOX[0], BBOX[2], GRID_RES)
print(f"Grilla: {len(lat_grid)} lat x {len(lon_grid)} lon = {len(lat_grid)*len(lon_grid)} puntos")

kriging_baseline = {}
variogram_params = {}

for gas in POLLUTANTS:
    gas_data = (
        dagma_diario[dagma_diario.gas == gas]
        .groupby(["nombre_est", "latitud", "longitud"])
        .concentracion.median()
        .reset_index()
    )

    if len(gas_data) < 3:
        print(f"\\n{gas}: SKIP ({len(gas_data)} estaciones, min 3)")
        continue

    lons = gas_data.longitud.values
    lats = gas_data.latitud.values
    vals = gas_data.concentracion.values
    print(f"\\n{gas}: {len(gas_data)} est, rango=[{vals.min():.1f}, {vals.max():.1f}] ug/m3")

    try:
        OK = OrdinaryKriging(
            lons, lats, vals,
            variogram_model="exponential",
            verbose=False, enable_plotting=False,
        )
        z_pred, sigma = OK.execute("grid", lon_grid, lat_grid)
        z_pred = np.asarray(z_pred)
        sigma = np.asarray(sigma)

        params = OK.variogram_model_parameters
        variogram_params[gas] = {
            "psill": float(params[0]),
            "range": float(params[1]),
            "nugget": float(params[2]),
        }
        kriging_baseline[gas] = {"z_pred": z_pred, "sigma": sigma, "stations": gas_data}
        print(f"  Variograma: psill={params[0]:.2f}, range={params[1]:.4f}deg, nugget={params[2]:.2f}")
    except Exception as e:
        print(f"  Error: {e}")

# Validacion LOO del kriging (dejar una estacion fuera)
print("\\n=== LOO Kriging Baseline ===")
kriging_metrics = []
for gas in POLLUTANTS:
    gas_data = (
        dagma_diario[dagma_diario.gas == gas]
        .groupby(["nombre_est", "latitud", "longitud"])
        .concentracion.median()
        .reset_index()
    )
    if len(gas_data) < 4:
        continue

    for i in range(len(gas_data)):
        train = gas_data.drop(i)
        test = gas_data.iloc[i]
        try:
            OK = OrdinaryKriging(
                train.longitud.values, train.latitud.values, train.concentracion.values,
                variogram_model="exponential", verbose=False, enable_plotting=False,
            )
            zp, _ = OK.execute("points", np.array([test.longitud]), np.array([test.latitud]))
            kriging_metrics.append({
                "gas": gas, "estacion": test.nombre_est,
                "y_true": float(test.concentracion), "y_pred": float(zp[0]),
            })
        except Exception:
            pass

if kriging_metrics:
    kriging_df = pd.DataFrame(kriging_metrics)
    print()
    for gas in POLLUTANTS:
        sub = kriging_df[kriging_df.gas == gas]
        if len(sub) == 0:
            continue
        rmse = np.sqrt(mean_squared_error(sub.y_true, sub.y_pred))
        mae = mean_absolute_error(sub.y_true, sub.y_pred)
        r2 = r2_score(sub.y_true, sub.y_pred)
        print(f"{gas}: RMSE={rmse:.2f}, MAE={mae:.2f}, R2={r2:.3f}")
""")

# ============================================================
# CELDA 4: Cargar modelo Conv3D
# ============================================================
code("""# @title 4. Cargar modelo Conv3D entrenado

import torch
import torch.nn as nn

class Conv3DSit3(nn.Module):
    def __init__(self, input_channels=531, hidden_dim=128, dropout=0.3):
        super().__init__()
        self.bottleneck = nn.Conv3d(input_channels, 32, kernel_size=1)
        self.bn0 = nn.BatchNorm3d(32)
        self.conv1 = nn.Conv3d(32, 64, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm3d(64)
        self.pool1 = nn.MaxPool3d(2)
        self.conv2 = nn.Conv3d(64, hidden_dim, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm3d(hidden_dim)
        self.pool2 = nn.MaxPool3d(2)
        self.gap = nn.AdaptiveAvgPool3d(1)
        self.dropout = nn.Dropout(dropout)
        self.head_no2 = nn.Linear(hidden_dim, 3)
        self.head_so2 = nn.Linear(hidden_dim, 3)
        self.head_o3 = nn.Linear(hidden_dim, 3)

    def forward(self, x):
        x = self.bottleneck(x)
        x = torch.relu(self.bn0(x))
        x = torch.relu(self.bn1(self.conv1(x)))
        x = self.pool1(x)
        x = torch.relu(self.bn2(self.conv2(x)))
        x = self.pool2(x)
        x = self.gap(x)
        x = x.view(x.size(0), -1)
        x = self.dropout(x)
        no2 = self.head_no2(x)
        so2 = self.head_so2(x)
        o3 = self.head_o3(x)
        return torch.stack([no2, so2, o3], dim=1)

# Buscar checkpoint
ckpt_files = list(Path("/kaggle/input").rglob("best.ckpt"))
if not ckpt_files:
    ckpt_files = list(WORKING.rglob("best.ckpt"))

if ckpt_files:
    ckpt_path = ckpt_files[0]
    print(f"Checkpoint: {ckpt_path}")

    model = Conv3DSit3(input_channels=531)
    state = torch.load(ckpt_path, map_location="cpu", weights_only=True)
    sd = state.get("state_dict", state)
    if any(k.startswith("model.") for k in sd):
        sd = {k.replace("model.", ""): v for k, v in sd.items()}
    model.load_state_dict(sd)
    model.eval()
    print("Modelo cargado OK")

    # Stats de normalizacion del entrenamiento
    Y_MEAN = np.array([2.90e-05, 2.73e-04, 1.16e-01], dtype=np.float32)
    Y_STD  = np.array([1.72e-05, 2.88e-04, 5.43e-03], dtype=np.float32)
else:
    print("WARN: No se encontro best.ckpt.")
    print("El kriging baseline (Celda 3) funciona sin modelo.")
    print("Para kriging de residuos necesitas el checkpoint del Conv3D.")
    model = None
""")

# ============================================================
# CELDA 5: Kriging de residuos Conv3D
# ============================================================
code("""# @title 5. Kriging de residuos Conv3D

# residuo = DAGMA_obs - Conv3D_pred
# Si el modelo es perfecto, los residuos son ruido blanco (nugget puro).
# Si hay estructura espacial (range > 0), el modelo deja patrones sin explicar.

# Buscar resultados LOO-CV
loocv_file = WORKING / "resultados_loo.json"
if not loocv_file.exists():
    loocv_file = Path("/kaggle/input/geovision-sit3-conv3d/resultados_loo.json")

residuos_kriging = {}

if loocv_file.exists() and model is not None:
    print(f"Cargando LOO-CV: {loocv_file}")
    with open(loocv_file, "r") as f:
        loocv_results = json.load(f)

    # Agrupar predicciones por estacion y gas
    preds_by = {}
    for r in loocv_results:
        key = (r["gas"], r["estacion"])
        preds_by.setdefault(key, []).extend(r["y_pred"])

    # Calcular residuos
    rows = []
    for gas in POLLUTANTS:
        for _, est in estaciones.iterrows():
            key = (gas, est.nombre_est)
            if key in preds_by:
                med_pred = np.median(preds_by[key])
                med_obs = dagma_diario[
                    (dagma_diario.nombre_est == est.nombre_est) &
                    (dagma_diario.gas == gas)
                ].concentracion.median()
                rows.append({
                    "gas": gas, "estacion": est.nombre_est,
                    "lat": est.lat, "lon": est.lon,
                    "obs": med_obs, "pred": med_pred,
                    "residuo": med_obs - med_pred,
                })

    residuos_df = pd.DataFrame(rows)
    print(f"Residuos: {len(residuos_df)} filas")

    for gas in POLLUTANTS:
        sub = residuos_df[residuos_df.gas == gas].dropna(subset=["residuo"])
        if len(sub) < 3:
            print(f"\\n{gas}: SKIP ({len(sub)} estaciones)")
            continue

        lons = sub.lon.values
        lats = sub.lat.values
        vals = sub.residuo.values
        print(f"\\n{gas}: {len(sub)} est, residuos=[{vals.min():.1f}, {vals.max():.1f}]")

        try:
            OK = OrdinaryKriging(
                lons, lats, vals,
                variogram_model="exponential",
                verbose=False, enable_plotting=False,
            )
            zp, ss = OK.execute("grid", lon_grid, lat_grid)
            params = OK.variogram_model_parameters
            residuos_kriging[gas] = {
                "z_pred": np.asarray(zp), "sigma": np.asarray(ss),
                "data": sub,
                "variogram": {"psill": float(params[0]), "range": float(params[1]), "nugget": float(params[2])},
            }
            rng = params[1]
            print(f"  range={rng:.4f}deg -> {'Nugget puro (OK!)' if rng < 0.001 else 'Estructura espacial presente'}")
        except Exception as e:
            print(f"  Error: {e}")
else:
    print("No se encontraron LOO-CV o modelo.")
    print(f"LOO-CV buscado en: {loocv_file}")
    print("Ejecuta primero el LOO-CV del notebook de entrenamiento.")
""")

# ============================================================
# CELDA 6: Moran I
# ============================================================
code("""# @title 6. Moran I sobre residuos

moran_results = {}

if "residuos_df" in dir() and len(residuos_df) > 0:
    for gas in POLLUTANTS:
        sub = residuos_df[residuos_df.gas == gas].dropna(subset=["residuo"])
        if len(sub) < 4:
            print(f"{gas}: SKIP Moran ({len(sub)} est)")
            continue

        coords = np.column_stack([sub.lon.values, sub.lat.values])
        try:
            w = DistanceBand(coords, threshold=0.015, binary=True)
        except Exception as e:
            print(f"{gas}: error pesos -> {e}")
            continue

        try:
            moran = Moran(sub.residuo.values, w, permutations=999)
            sig = "***" if moran.p_sim < 0.001 else ("**" if moran.p_sim < 0.01 else ("*" if moran.p_sim < 0.05 else "ns"))
            print(f"{gas}: I={moran.I:.4f} p={moran.p_sim:.4f} EI={moran.EI:.4f} {sig}")
            moran_results[gas] = {"I": float(moran.I), "p": float(moran.p_sim), "EI": float(moran.EI), "n": len(sub)}

            if len(sub) >= 5:
                lisa = Moran_Local(sub.residuo.values, w, permutations=999)
                q = lisa.q
                sig_mask = lisa.p_sim < 0.05
                hh = (q[sig_mask] == 1).sum()
                ll = (q[sig_mask] == 3).sum()
                lh = (q[sig_mask] == 2).sum()
                hl = (q[sig_mask] == 4).sum()
                print(f"  LISA: HH={hh} LL={ll} LH={lh} HL={hl}")
        except Exception as e:
            print(f"{gas}: error Moran -> {e}")
else:
    print("No hay datos de residuos. Ejecuta Celda 5 primero.")
""")

# ============================================================
# CELDA 7: Tabla comparativa
# ============================================================
code("""# @title 7. Tabla comparativa final

print("=" * 70)
print("  COMPARATIVA: Conv3D vs Kriging Baseline")
print("=" * 70)

filas = []

# Kriging baseline
if "kriging_df" in dir():
    for gas in POLLUTANTS:
        sub = kriging_df[kriging_df.gas == gas]
        if len(sub) > 0:
            filas.append({
                "Metodo": "Kriging puro",
                "Gas": gas,
                "RMSE": np.sqrt(mean_squared_error(sub.y_true, sub.y_pred)),
                "MAE": mean_absolute_error(sub.y_true, sub.y_pred),
                "R2": r2_score(sub.y_true, sub.y_pred),
            })

# Conv3D LOO-CV
if "loocv_results" in dir():
    for gas in POLLUTANTS:
        runs = [r for r in loocv_results if r["gas"] == gas]
        if runs:
            yt = np.concatenate([r["y_true"] for r in runs])
            yp = np.concatenate([r["y_pred"] for r in runs])
            filas.append({
                "Metodo": "Conv3D LOO-CV",
                "Gas": gas,
                "RMSE": np.sqrt(mean_squared_error(yt, yp)),
                "MAE": mean_absolute_error(yt, yp),
                "R2": r2_score(yt, yp),
            })

if filas:
    comp_df = pd.DataFrame(filas).round(3)
    print(comp_df.to_string(index=False))
else:
    print("No hay datos suficientes para comparar.")

# KPIs
print()
print("=== vs KPIs ===")
KPIS = {"NO2": 8, "SO2": 6, "O3": 12}
for metodo in comp_df.Metodo.unique() if filas else []:
    sub = comp_df[comp_df.Metodo == metodo]
    print(f"\\n{metodo}:")
    for _, row in sub.iterrows():
        kpi = KPIS.get(row.Gas, 99)
        ok = "SI" if row.RMSE <= kpi else "NO"
        print(f"  {row.Gas}: RMSE={row.RMSE:.2f} (KPI<={kpi}) -> {ok}")
""")

# ============================================================
# CELDA 8: Mapas
# ============================================================
code("""# @title 8. Mapas de prediccion Kriging

n_gases = len(kriging_baseline)
if n_gases == 0:
    print("No hay kriging para graficar.")
else:
    fig, axes = plt.subplots(n_gases, 2, figsize=(14, 5 * n_gases))
    if n_gases == 1:
        axes = axes.reshape(1, -1)

    for i, gas in enumerate(POLLUTANTS):
        if gas not in kriging_baseline:
            for j in range(2):
                axes[i, j].axis("off")
            continue

        kb = kriging_baseline[gas]
        st = kb["stations"]

        # Mapa 1: Prediccion
        im0 = axes[i, 0].pcolormesh(lon_grid, lat_grid, kb["z_pred"], cmap="RdYlGn_r", shading="auto")
        axes[i, 0].scatter(st.longitud, st.latitud, c="blue", s=40, edgecolor="black", zorder=5)
        for _, s in st.iterrows():
            axes[i, 0].annotate(s.nombre_est[:12], (s.longitud, s.latitud), fontsize=7, ha="center")
        axes[i, 0].set_title(f"{gas} - Kriging (mediana historica)")
        plt.colorbar(im0, ax=axes[i, 0], shrink=0.8)

        # Mapa 2: Sigma
        im1 = axes[i, 1].pcolormesh(lon_grid, lat_grid, kb["sigma"], cmap="magma", shading="auto")
        axes[i, 1].scatter(st.longitud, st.latitud, c="cyan", s=20, zorder=5)
        axes[i, 1].set_title(f"{gas} - Sigma Kriging")
        plt.colorbar(im1, ax=axes[i, 1], shrink=0.8)

    plt.tight_layout()
    plt.savefig(WORKING / "mapas_kriging_sit3.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Mapa guardado: mapas_kriging_sit3.png")

# Mapa de residuos si existen
if residuos_kriging:
    n_res = len(residuos_kriging)
    fig2, axes2 = plt.subplots(1, n_res, figsize=(6 * n_res, 5))
    if n_res == 1:
        axes2 = [axes2]

    for i, gas in enumerate(POLLUTANTS):
        if gas not in residuos_kriging:
            continue
        rk = residuos_kriging[gas]
        vmax = max(abs(rk["z_pred"].min()), abs(rk["z_pred"].max()))
        im = axes2[i].pcolormesh(lon_grid, lat_grid, rk["z_pred"], cmap="RdBu_r", vmin=-vmax, vmax=vmax, shading="auto")
        axes2[i].scatter(rk["data"].lon, rk["data"].lat, c="black", s=30, zorder=5)
        axes2[i].set_title(f"{gas} - Residuos Conv3D krigeados")
        plt.colorbar(im, ax=axes2[i], shrink=0.8)

    plt.tight_layout()
    plt.savefig(WORKING / "mapas_residuos_sit3.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Mapa de residuos guardado: mapas_residuos_sit3.png")
""")

# ============================================================
# CELDA 9: Exportar
# ============================================================
code("""# @title 9. Exportar resultados

resultados = {
    "fecha": pd.Timestamp.now().isoformat(),
    "bbox": BBOX,
    "grid_res": GRID_RES,
    "variogram_params": variogram_params,
    "moran_results": moran_results,
    "n_estaciones": len(estaciones),
}

# Metricas kriging baseline
if "kriging_df" in dir():
    for gas in POLLUTANTS:
        sub = kriging_df[kriging_df.gas == gas]
        if len(sub) > 0:
            resultados[f"kriging_{gas}_rmse"] = float(np.sqrt(mean_squared_error(sub.y_true, sub.y_pred)))
            resultados[f"kriging_{gas}_r2"] = float(r2_score(sub.y_true, sub.y_pred))

# Guardar JSON
json_path = WORKING / "resumen_kriging_sit3.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2, default=str)
print(f"JSON: {json_path}")

# Listar archivos generados
print()
for f in sorted(WORKING.iterdir()):
    if f.is_file():
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name}: {size_kb:.1f} KB")

print()
print("=" * 50)
print("  ST-KRIGING COMPLETADO")
print("=" * 50)
print("Salidas:")
print("  - mapas_kriging_sit3.png")
print("  - mapas_residuos_sit3.png")
print("  - resumen_kriging_sit3.json")
""")

# ============================================================
# ARMAR NOTEBOOK
# ============================================================
nb = {
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12.0"},
        "kaggle": {
            "accelerator": "nvidiaTeslaT4",
            "isInternetEnabled": True,
            "language": "python",
            "sourceType": "notebook",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
    "cells": cells,
}

OUT = r"C:\Users\Samuel\Desktop\FINALPROYECTO3\GeoVision-CLIP-Cali\notebooks\Situacion_3\sit3-kriging-eval.ipynb"
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"Notebook creado: {OUT}")
print(f"Celdas: {len(cells)}")
for i, c in enumerate(cells):
    src = "".join(c["source"])[:80].replace("\n", " ")
    print(f"  [{i}] [{c['cell_type']:4s}] {src}...")
