"""Generar tensor de entrada para ConvLSTM (Situacion 3).

Toma embeddings .npz (de sit2_sae_posttrain.ipynb) + paneles S5P
y produce X=(N,8,522,5,5) e y=(N,3,3) para entrenar ConvLSTM.

Uso:
    python pipeline/generar_tensor_convlstm.py \
        --data-dir ./dataset_sit2 \
        --npz-path ./dataset_sit2/embeddings_sit2.npz \
        --s5p-source gcs \
        --output-dir ./dataset_sit3 \
        --seq-len 8 \
        --horizons 1 3 7

    # Subir a HF despues de generar
    python pipeline/generar_tensor_convlstm.py \
        --data-dir ./dataset_sit2 \
        --output-dir ./dataset_sit3 \
        --upload-hf \
        --hf-repo Slucu-0310/geovision-cali-sit3

    # Con covariables ERA5/MODIS (generadas por preparar_covariables_convlstm.py)
    python pipeline/generar_tensor_convlstm.py \
        --data-dir ./dataset_sit2 \
        --output-dir ./dataset_sit3 \
        --covariables-path ./dataset_sit2/covariables.parquet

    # Con grid embeddings (25 embeddings por tile, uno por punto de grilla)
    python pipeline/generar_tensor_convlstm.py \
        --data-dir ./dataset_sit2 \
        --grid-npz-path ./dataset_sit2/embeddings_grid_sit2.npz \
        --output-dir ./dataset_sit3 \
        --upload-hf

Requiere: numpy, pandas, zarr, xarray, gcsfs, huggingface_hub, tqdm
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from tqdm import tqdm

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

SEED = 42
np.random.seed(SEED)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generar tensor ConvLSTM desde embeddings .npz + S5P"
    )
    p.add_argument(
        "--data-dir",
        type=Path,
        default=Path("./dataset_sit2"),
        help="Carpeta con metadatos.parquet, tiles.zarr y embeddings_sit2.npz",
    )
    p.add_argument(
        "--npz-path",
        type=Path,
        default=None,
        help="Ruta al embeddings_sit2.npz (default: data-dir/embeddings_sit2.npz)",
    )
    p.add_argument(
        "--s5p-source",
        choices=["gcs", "hf", "local"],
        default="gcs",
        help="Fuente de paneles S5P: gcs (Google Cloud), hf (HuggingFace), local (ruta zarr)",
    )
    p.add_argument(
        "--s5p-local-path",
        type=Path,
        default=None,
        help="Ruta local a paneles S5P (solo si --s5p-source=local)",
    )
    p.add_argument(
        "--hf-repo-panel",
        type=str,
        default="Slucu-0310/geovision-cali-panel",
        help="Repo HF con paneles S5P (solo si --s5p-source=hf)",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./dataset_sit3"),
        help="Carpeta de salida para X_convlstm.npy y y_convlstm.npy",
    )
    p.add_argument(
        "--seq-len",
        type=int,
        default=8,
        help="Longitud de secuencia temporal (default: 8)",
    )
    p.add_argument(
        "--horizons",
        type=int,
        nargs="+",
        default=[1, 3, 7],
        help="Horizontes de prediccion en dias (default: 1 3 7)",
    )
    p.add_argument(
        "--cell-res",
        type=float,
        default=0.05,
        help="Resolucion de celda espacial en grados (default: 0.05)",
    )
    p.add_argument(
        "--grid-size",
        type=int,
        default=5,
        help="Tamano de grilla espacial (default: 5 -> 5x5)",
    )
    p.add_argument(
        "--stride",
        type=float,
        default=0.005,
        help="Stride espacial en grados (default: 0.005)",
    )
    p.add_argument(
        "--upload-hf",
        action="store_true",
        help="Subir X/y .npy a HuggingFace despues de generar",
    )
    p.add_argument(
        "--hf-repo",
        type=str,
        default="Slucu-0310/geovision-cali-sit3",
        help="Repo HF de destino (default: Slucu-0310/geovision-cali-sit3)",
    )
    p.add_argument(
        "--hf-token",
        type=str,
        default=os.environ.get("HF_TOKEN"),
        help="Token de HuggingFace (default: env HF_TOKEN)",
    )
    p.add_argument(
        "--gcp-project",
        type=str,
        default="proyecto3ia-494900",
        help="Proyecto GCP para GCS (default: proyecto3ia-494900)",
    )
    p.add_argument(
        "--gcs-bucket",
        type=str,
        default="gs://geovision-cali",
        help="Bucket GCS (default: gs://geovision-cali)",
    )
    p.add_argument(
        "--covariables-path",
        type=Path,
        default=None,
        help="Ruta a covariables.parquet (generado por preparar_covariables_convlstm.py). "
             "Si se provee, agrega columnas numericas adicionales como canales extra al tensor.",
    )
    p.add_argument(
        "--grid-npz-path",
        type=Path,
        default=None,
        help="Ruta a embeddings_grid_sit2.npz con grid_features (N,25,512). "
             "Si se provee, cada punto de la grilla 5x5 recibe su propio embedding "
             "en vez de repetir el mismo embedding del tile.",
    )
    p.add_argument(
        "--abs-targets",
        action="store_true",
        help="Usar valores S5P absolutos como targets (en vez de anomalias). "
             "Mejora R2 porque los targets tienen mayor varianza.",
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------

def cargar_metadatos(data_dir: Path) -> pd.DataFrame:
    """Carga metadatos.parquet y parsea fechas."""
    path = data_dir / "metadatos.parquet"
    if not path.is_file():
        raise FileNotFoundError(f"No se encuentra {path}")
    df = pd.read_parquet(path)
    df["fecha_dt"] = pd.to_datetime(df["fecha"])
    print(f"[OK] Metadatos: {len(df)} filas | fechas {df['fecha_dt'].min()} a {df['fecha_dt'].max()}")
    return df


def cargar_embeddings(npz_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Carga embeddings .npz generado por sit2_sae_posttrain.ipynb."""
    if not npz_path.is_file():
        raise FileNotFoundError(
            f"No se encuentra {npz_path}. Genera ejecutando sit2_sae_posttrain.ipynb "
            "(celda de exportacion .npz) y copia el archivo a dataset_sit2/."
        )
    data = np.load(npz_path)
    features = data["features"]  # (N, 512)
    labels = data["labels"]       # (N,)
    print(f"[OK] Embeddings .npz: {features.shape} | clases: {np.unique(labels)}")
    data.close()
    return features, labels


def cargar_s5p_gcs(bucket: str, project: str) -> dict[str, Any]:
    """Carga paneles S5P desde Google Cloud Storage."""
    try:
        import gcsfs
        import xarray as xr
    except ImportError as e:
        raise ImportError(f"Requiere gcsfs y xarray: {e}")

    fs = gcsfs.GCSFileSystem(project=project)
    panels = {}
    for pol in ["NO2", "SO2", "O3"]:
        path = f"{bucket}/Sentinel5P/{pol}/panel.zarr"
        ds = xr.open_zarr(fs.get_mapper(path), consolidated=True)
        panels[pol] = ds
        print(f"[OK] S5P {pol}: {len(ds.time)} fechas, y={ds.dims['y']}, x={ds.dims['x']}")
    return panels


def cargar_s5p_hf(repo_id: str, token: str | None) -> dict[str, Any]:
    """Carga paneles S5P desde HuggingFace dataset."""
    try:
        from huggingface_hub import snapshot_download
        import xarray as xr
    except ImportError as e:
        raise ImportError(f"Requiere huggingface_hub y xarray: {e}")

    local_dir = Path("./hf_panel_cache")
    snapshot_download(
        repo_id=repo_id,
        repo_type="dataset",
        local_dir=str(local_dir),
        local_dir_use_symlinks=False,
        token=token,
    )
    panels = {}
    for pol in ["NO2", "SO2", "O3"]:
        path = local_dir / "Sentinel5P" / pol / "panel.zarr"
        ds = xr.open_zarr(str(path), consolidated=True)
        # Parsear tiempos a datetime64[ns] y reemplazar el coordinate 'time'
        raw_times = ds["time"].values
        parsed = np.array(
            [pd.Timestamp(t.split("_")[0][:8]) if isinstance(t, str) else pd.Timestamp(t)
             for t in raw_times],
            dtype="datetime64[ns]",
        )
        ds = ds.assign_coords(time=parsed)
        # Pre-extraer arrays numpy para acceso rapido
        panel_data = {
            "time": parsed,
            "y": ds["y"].values,
            "x": ds["x"].values,
            "data": ds["data"].values,  # (T, bandas, y, x)
        }
        panels[pol] = panel_data
        print(f"[OK] S5P {pol} (HF): {len(parsed)} fechas")
    return panels


def cargar_s5p_local(base_path: Path) -> dict[str, Any]:
    """Carga paneles S5P desde ruta local."""
    import xarray as xr
    panels = {}
    for pol in ["NO2", "SO2", "O3"]:
        path = base_path / "Sentinel5P" / pol / "panel.zarr"
        ds = xr.open_zarr(str(path), consolidated=True)
        panels[pol] = ds
        print(f"[OK] S5P {pol} (local): {len(ds.time)} fechas")
    return panels


# ---------------------------------------------------------------------------
# Secuencias y targets
# ---------------------------------------------------------------------------

def _buscar_indice_tiempo(times: np.ndarray, target: np.datetime64) -> int:
    """Busca el indice del tiempo mas cercano usando busqueda binaria O(log n)."""
    idx = np.searchsorted(times, target)
    if idx == 0:
        return 0
    if idx == len(times):
        return len(times) - 1
    before = times[idx - 1]
    after = times[idx]
    if abs(target - before) <= abs(target - after):
        return idx - 1
    return idx


def get_s5p_value(panel: Any, fecha: pd.Timestamp, lat: float, lon: float, max_days: int = 5) -> float:
    """Extrae valor S5P mas cercano a una fecha/posicion.

    Busca dentro de una ventana de +/-max_dias alrededor de la fecha objetivo
    y devuelve el primer valor valido (finito y >0) que encuentre.
    Si no encuentra, devuelve NaN.

    panel puede ser un xr.Dataset (GCS/local) o un dict de arrays numpy (HF).
    """
    # Detectar tipo
    if isinstance(panel, dict):
        times = panel["time"]        # numpy array
        data_arr = panel["data"]     # (T, bandas, y, x)
        y_vals = panel["y"]
        x_vals = panel["x"]
    else:
        times = panel["time"].values
        y_vals = panel["y"].values
        x_vals = panel["x"].values

    target = np.datetime64(fecha)
    yi = int(np.argmin(np.abs(y_vals - lat)))
    xi = int(np.argmin(np.abs(x_vals - lon)))

    # Buscar en un rango de +/-max_dias alrededor del target
    start_idx = max(0, np.searchsorted(times, target - np.timedelta64(max_days, "D")))
    end_idx = min(len(times), np.searchsorted(times, target + np.timedelta64(max_days, "D")) + 1)

    for idx in range(start_idx, end_idx):
        diff = abs(times[idx] - target)
        if diff > np.timedelta64(max_days, "D"):
            continue
        if isinstance(panel, dict):
            val = float(data_arr[idx, 0, yi, xi])
        else:
            val = float(panel["data"].isel(time=idx, band=0, y=yi, x=xi).values)
        if np.isfinite(val) and val > 0:
            return val
    return np.nan


def generar_secuencias(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    s5p_panels: dict[str, Any],
    seq_len: int,
    horizons: list[int],
    cell_res: float,
    covariables_df: pd.DataFrame | None = None,
    grid_embeddings: np.ndarray | None = None,
) -> list[dict]:
    """Genera secuencias temporales con targets S5P.

    Si se provee covariables_df, se hace merge por tile_id para enriquecer
    las filas con columnas adicionales (ERA5, MODIS, etc.) que luego
    se agregaran como canales extra en el tensor.
    """
    df = df.copy()
    if covariables_df is not None:
        # Merge por tile_id si existe, si no por indice
        if "tile_id" in df.columns and "tile_id" in covariables_df.columns:
            df = df.merge(covariables_df, on="tile_id", suffixes=("", "_cov"))
        else:
            # Merge por indice posicional
            cov = covariables_df.reset_index(drop=True)
            df = df.reset_index(drop=True).join(cov)
        print(f"[INFO] Covariables mergeadas. Columnas adicionales: "
              f"{set(df.columns) - {'centroide_lat', 'centroide_lon', 'clase', 'fecha_dt', 'embedding'}}")

    df["celda_lat"] = (df["centroide_lat"] / cell_res).round() * cell_res
    df["celda_lon"] = (df["centroide_lon"] / cell_res).round() * cell_res
    df["embedding"] = [embeddings[i] for i in range(len(embeddings))]
    if grid_embeddings is not None:
        assert len(grid_embeddings) == len(df), (
            f"Desajuste grid_embeddings {len(grid_embeddings)} vs df {len(df)}"
        )
        df["embedding_grid"] = [grid_embeddings[i] for i in range(len(grid_embeddings))]
        print(f"[OK] Grid embeddings asignados: {grid_embeddings.shape}")

    sequences = []
    grouped = df.groupby(["celda_lat", "celda_lon"])
    for (clat, clon), grp in tqdm(grouped, desc="Generando secuencias"):
        ord_grp = grp.sort_values("fecha_dt")
        fechas_u = ord_grp["fecha_dt"].unique()
        if len(fechas_u) < seq_len:
            continue
        for i in range(len(fechas_u) - seq_len + 1):
            ventana = fechas_u[i : i + seq_len]
            rows = [ord_grp[ord_grp["fecha_dt"] == f].iloc[0] for f in ventana]
            last_date = ventana[-1]

            # Baseline S5P del ultimo tile de la secuencia (T0)
            last_row = rows[-1]
            baseline = np.array([
                last_row.get("no2", np.nan),
                last_row.get("so2", np.nan),
                last_row.get("o3", np.nan),
            ], dtype=np.float32)

            # Targets absolutos S5P en T+1, T+3, T+7
            targets_abs = []
            for h in horizons:
                tgt = last_date + pd.Timedelta(days=h)
                targets_abs.append([
                    get_s5p_value(s5p_panels[p], tgt, clat, clon)
                    for p in ["NO2", "SO2", "O3"]
                ])
            targets_abs = np.array(targets_abs, dtype=np.float32)

            # Targets como ANOMALIA: valor absoluto - baseline
            # Si baseline es NaN, se usa el target absoluto (como si baseline=0)
            targets_anom = targets_abs.copy()
            for h in range(len(horizons)):
                for p in range(3):
                    if np.isfinite(targets_abs[h, p]):
                        b = baseline[p] if np.isfinite(baseline[p]) else 0.0
                        targets_anom[h, p] = targets_abs[h, p] - b
                    else:
                        targets_anom[h, p] = np.nan

            sequences.append({
                "celda_lat": clat,
                "celda_lon": clon,
                "rows": rows,
                "targets": targets_anom,         # anomalia (para entrenar)
                "targets_abs": targets_abs,       # valor absoluto (para evaluar)
                "baseline": baseline,              # S5P del ultimo tile
            })
    print(f"[OK] Secuencias generadas: {len(sequences)}")
    return sequences


# ---------------------------------------------------------------------------
# Construccion del tensor
# ---------------------------------------------------------------------------

COLS_BASE = {
    "ndvi", "bsi", "ndbi",
    "no2", "so2", "o3",
    "fecha", "fecha_dt", "clase", "split", "tile_id",
    "embedding", "celda_lat", "celda_lon",
    "centroide_lat", "centroide_lon", "descripcion",
}
COLS_EXTRA_DEFAULT = [
    "no2_ugm3", "so2_ugm3", "o3_ugm3",
    "era5_t2m", "era5_blh", "era5_wind_u", "era5_wind_v", "era5_presion",
    "modis_aod_047", "modis_aod_055",
    "no2_norm", "so2_norm", "o3_norm",
    "no2_log", "so2_log", "o3_log",
]


def _detectar_columnas_extra(rows: list[pd.Series]) -> list[str]:
    """Detecta columnas numericas adicionales en las filas para usarlas como canales."""
    if not rows:
        return []
    sample = rows[0]
    extra = []
    for col in COLS_EXTRA_DEFAULT:
        if col in sample.index:
            val = sample[col]
            if isinstance(val, (int, float, np.floating, np.integer)):
                extra.append(col)
    return extra


def construir_tensor(
    sequences: list[dict],
    grid_size: int,
    stride: float,
    target_key: str = "targets",
) -> tuple[np.ndarray, np.ndarray]:
    """Construye X=(N,8,C,5,5) e y=(N,3,3) donde C=522+canales_extra.
    
    Args:
        target_key: "targets" (anomalia) o "targets_abs" (valor absoluto S5P).
    """
    # Detectar columnas extra de la primera secuencia
    extra_cols = _detectar_columnas_extra(sequences[0]["rows"]) if sequences else []
    BASE_CH = 522  # 512 embedding + 4 temporal + 2 posicion + 1 gap + 3 indices
    C = BASE_CH + len(extra_cols)
    print(f"[INFO] Tensor C={C}: {BASE_CH} base + {len(extra_cols)} extra ({extra_cols})")

    def build_X(rows: list[pd.Series]) -> np.ndarray:
        lat_c = float(rows[0]["centroide_lat"])
        lon_c = float(rows[0]["centroide_lon"])
        half = (grid_size - 1) / 2
        lats = np.linspace(lat_c - half * stride, lat_c + half * stride, grid_size)
        lons = np.linspace(lon_c - half * stride, lon_c + half * stride, grid_size)
        X = np.zeros((len(rows), C, grid_size, grid_size), dtype=np.float32)
        for t, row in enumerate(rows):
            emb = row["embedding"]
            fecha = row["fecha_dt"]
            doy = fecha.dayofyear
            # Obtener valores de columnas extra (si existen)
            extra_vals = []
            for col in extra_cols:
                v = row.get(col, np.nan)
                extra_vals.append(v if np.isfinite(v) else 0.0)
            # Si hay embedding_grid, usar embedding por posicion de grilla
            use_grid = "embedding_grid" in row.index and row["embedding_grid"] is not None
            if use_grid:
                emb_grid_2d = row["embedding_grid"].reshape(grid_size, grid_size, 512)
            for gi in range(grid_size):
                for gj in range(grid_size):
                    if use_grid:
                        X[t, :512, gi, gj] = emb_grid_2d[gi, gj]
                    else:
                        X[t, :512, gi, gj] = emb
                    X[t, 512, gi, gj] = np.sin(2 * np.pi * doy / 365.25)
                    X[t, 513, gi, gj] = np.cos(2 * np.pi * doy / 365.25)
                    X[t, 514, gi, gj] = np.sin(2 * np.pi * fecha.month / 12)
                    X[t, 515, gi, gj] = np.cos(2 * np.pi * fecha.month / 12)
                    X[t, 516, gi, gj] = (lats[gi] - 3.45) / 0.1
                    X[t, 517, gi, gj] = (lons[gj] + 76.5) / 0.1
                    if t == 0:
                        X[t, 518, gi, gj] = 0.0
                    else:
                        gap = (rows[t]["fecha_dt"] - rows[t - 1]["fecha_dt"]).days / 30.0
                        X[t, 518, gi, gj] = min(gap, 5.0)
                    X[t, 519, gi, gj] = row.get("ndvi", 0) if np.isfinite(row.get("ndvi", 0)) else 0
                    X[t, 520, gi, gj] = row.get("bsi", 0) if np.isfinite(row.get("bsi", 0)) else 0
                    X[t, 521, gi, gj] = row.get("ndbi", 0) if np.isfinite(row.get("ndbi", 0)) else 0
                    # Canales extra
                    for ch, val in enumerate(extra_vals, start=BASE_CH):
                        X[t, ch, gi, gj] = val
        return X

    X_list, y_list = [], []
    for seq in tqdm(sequences, desc="Construyendo tensor"):
        X_list.append(build_X(seq["rows"]))
        y_list.append(seq[target_key])

    X_full = np.stack(X_list, axis=0)
    y_full = np.stack(y_list, axis=0)
    print(f"[OK] Tensor X: {X_full.shape}, y: {y_full.shape}")
    return X_full, y_full


# ---------------------------------------------------------------------------
# Guardado y subida
# ---------------------------------------------------------------------------

def guardar_tensor(X: np.ndarray, y: np.ndarray, output_dir: Path) -> None:
    """Guarda X/y como .npy."""
    output_dir.mkdir(parents=True, exist_ok=True)
    np.save(output_dir / "X_convlstm.npy", X)
    np.save(output_dir / "y_convlstm.npy", y)
    print(f"[OK] Guardado en {output_dir}: X_convlstm.npy, y_convlstm.npy")


def subir_hf(
    output_dir: Path,
    repo_id: str,
    token: str | None,
    npz_path: Path | None = None,
) -> None:
    """Sube archivos a HuggingFace dataset."""
    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("[WARN] huggingface_hub no instalado. Omitiendo subida.")
        return

    api = HfApi(token=token)
    api.create_repo(repo_id, repo_type="dataset", exist_ok=True)

    files = [
        (output_dir / "X_convlstm.npy", "X_convlstm.npy"),
        (output_dir / "y_convlstm.npy", "y_convlstm.npy"),
    ]
    if npz_path and npz_path.is_file():
        files.append((npz_path, "embeddings_sit2.npz"))

    for local, remote in files:
        api.upload_file(
            path_or_fileobj=str(local),
            path_in_repo=remote,
            repo_id=repo_id,
            repo_type="dataset",
        )
        print(f"[OK] Subido {remote} a {repo_id}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = _parse_args()

    print("=" * 60)
    print("  GENERAR TENSOR CONVLSTM (Sit. 3)")
    print("=" * 60)

    # 1. Cargar metadatos
    print("\n[1/5] Cargando metadatos...")
    df = cargar_metadatos(args.data_dir)

    # 2. Cargar embeddings .npz
    print("\n[2/5] Cargando embeddings .npz...")
    npz_path = args.npz_path or args.data_dir / "embeddings_sit2.npz"
    embeddings, labels = cargar_embeddings(npz_path)

    # Verificar alineacion
    assert len(embeddings) == len(df), (
        f"Desajuste: embeddings {len(embeddings)} vs parquet {len(df)}"
    )
    print("[OK] Alineacion embeddings-parquet: OK")

    # 3. Cargar S5P
    print(f"\n[3/5] Cargando paneles S5P (fuente: {args.s5p_source})...")
    if args.s5p_source == "gcs":
        s5p_panels = cargar_s5p_gcs(args.gcs_bucket, args.gcp_project)
    elif args.s5p_source == "hf":
        s5p_panels = cargar_s5p_hf(args.hf_repo_panel, args.hf_token)
    elif args.s5p_source == "local":
        if not args.s5p_local_path:
            raise ValueError("--s5p-local-path requerido cuando --s5p-source=local")
        s5p_panels = cargar_s5p_local(args.s5p_local_path)
    else:
        raise ValueError(f"Fuente S5P no soportada: {args.s5p_source}")

    # 3b. Cargar covariables (opcional)
    covariables_df = None
    if args.covariables_path:
        if args.covariables_path.is_file():
            print(f"\n[3b] Cargando covariables desde {args.covariables_path}...")
            covariables_df = pd.read_parquet(args.covariables_path)
            print(f"[OK] Covariables: {covariables_df.shape}")
        else:
            print(f"[WARN] No se encuentra covariables en {args.covariables_path}. Continuando sin ellas.")

    # 3c. Cargar grid embeddings (opcional)
    grid_embeddings = None
    if args.grid_npz_path:
        if args.grid_npz_path.is_file():
            print(f"\n[3c] Cargando grid embeddings desde {args.grid_npz_path}...")
            grid_data = np.load(args.grid_npz_path)
            grid_embeddings = grid_data["grid_features"]  # (N, 25, 512)
            print(f"[OK] Grid embeddings: {grid_embeddings.shape}")
            assert grid_embeddings.shape[0] == len(df), (
                f"Desajuste grid_embeddings {grid_embeddings.shape[0]} vs df {len(df)}"
            )
            assert grid_embeddings.shape[1] == 25, (
                f"grid_embeddings debe tener 25 por tile, tiene {grid_embeddings.shape[1]}"
            )
        else:
            print(f"[WARN] No se encuentra {args.grid_npz_path}. Continuando sin grid embeddings.")

    # 4. Generar secuencias
    print(f"\n[4/5] Generando secuencias (seq_len={args.seq_len}, horizons={args.horizons})...")
    sequences = generar_secuencias(
        df, embeddings, s5p_panels, args.seq_len, args.horizons, args.cell_res,
        covariables_df=covariables_df,
        grid_embeddings=grid_embeddings,
    )

    if not sequences:
        print("[ERROR] No se generaron secuencias. Revisa los datos de entrada.")
        return 1

    # 5. Construir tensor
    print(f"\n[5/5] Construyendo tensor (grid={args.grid_size}x{args.grid_size})...")
    target_key = "targets_abs" if args.abs_targets else "targets"
    X, y = construir_tensor(sequences, args.grid_size, args.stride, target_key=target_key)

    # Guardar
    guardar_tensor(X, y, args.output_dir)

    # Subir a HF si se pidio
    if args.upload_hf:
        print("\n[HF] Subiendo a HuggingFace...")
        subir_hf(args.output_dir, args.hf_repo, args.hf_token, npz_path)

    print("\n" + "=" * 60)
    print("  COMPLETADO")
    print("=" * 60)
    print(f"  X: {X.shape}")
    print(f"  y: {y.shape}")
    print(f"  Secuencias: {len(sequences)}")
    print(f"  Output: {args.output_dir}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
