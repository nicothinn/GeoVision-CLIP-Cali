"""
Servicio de Kriging Ordinario 2D para SO₂ y O₃.
Basado en sit3-kriging-eval.ipynb (celdas 2, 3, 4).

NO₂ queda excluido: solo 1 estación (Univalle) — insuficiente para variograma.

Flujo:
  1. Cargar DAGMA (mediana diaria por estación)
  2. Variograma experimental + ajuste WLS (exponencial/gaussiano/esférico)
  3. OrdinaryKriging 2D → superficie z(s) + varianza σ²(s) en grilla Cali
  4. Cachear superficie para consultas rápidas (interpolación bilineal)
"""

from __future__ import annotations

import pickle
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pykrige.ok import OrdinaryKriging
from scipy.optimize import least_squares
from scipy.spatial.distance import pdist, squareform
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# ─── Constantes ───────────────────────────────────────────────────────────────
DATA_DIR = Path("backend/data")
DAGMA_PATH = DATA_DIR / "DAGMA_con_Acopi_NO2.parquet"
CACHE_PATH = DATA_DIR / "kriging_surface.pkl"

POLLUTANTS_KRIGING = ["SO2", "O3"]  # NO2 excluido
POLLUTANTS = ["NO2", "SO2", "O3"]
KPI_UGM3 = {"NO2": 8.0, "SO2": 6.0, "O3": 12.0}

# BBox Cali (consigna)
BBOX = [-76.65, 3.30, -76.30, 3.65]  # lon_min, lat_min, lon_max, lat_max
GRID_RES = 0.005  # ~500 m

# Estaciones DAGMA (del notebook)
DAGMA_STATIONS = {
    "Base_Aerea":            (3.4646, -76.5142),
    "Canaveralejo":          (3.4189, -76.5417),
    "Compartir":             (3.4306, -76.4764),
    "ERA_-_Obrero":          (3.4537, -76.5208),
    "Ermita":                (3.4515, -76.5322),
    "Flora":                 (3.4918, -76.5142),
    "Pance":                 (3.3278, -76.5486),
    "Transitoria_-_Navarro": (3.4789, -76.4892),
    "Univalle":              (3.3779, -76.5338),
}

POLLUTANT_COLS = {
    "NO2": ["Univalle_NO2"],
    "SO2": ["Base_Aerea_SO2", "Canaveralejo_SO2", "Ermita_SO2",
            "Flora_SO2", "Transitoria_-_Navarro_SO2"],
    "O3":  ["Base_Aerea_O3", "Compartir_O3", "ERA_-_Obrero_O3",
            "Flora_O3", "Pance_O3", "Univalle_O3"],
}

# Variograma
DEG_TO_KM = 111.0
MAX_LAG_KM = 30.0
N_BINS = 8


# ─── Modelos de variograma ────────────────────────────────────────────────────

def _model_exp(h, c0, c, a):
    return c0 + c * (1.0 - np.exp(-3.0 * h / max(a, 1e-9)))

def _model_gauss(h, c0, c, a):
    return c0 + c * (1.0 - np.exp(-3.0 * (h / max(a, 1e-9)) ** 2))

def _model_sph(h, c0, c, a):
    hh = np.minimum(h / max(a, 1e-9), 1.0)
    return c0 + c * (1.5 * hh - 0.5 * hh ** 3)

_MODELS = {
    "exponential": _model_exp,
    "gaussian":    _model_gauss,
    "spherical":   _model_sph,
}


# ─── Semivariograma experimental ──────────────────────────────────────────────

def _semivariogram_exp(coords_km, vals):
    n = len(vals)
    if n < 3:
        return np.array([]), np.array([]), np.array([])
    d = squareform(pdist(coords_km))
    sq = 0.5 * (vals[:, None] - vals[None, :]) ** 2
    edges = np.linspace(0, MAX_LAG_KM, N_BINS + 1)
    lags, gammas, npairs = [], [], []
    iu = np.triu_indices(n, k=1)
    dist_v = d[iu]; sq_v = sq[iu]
    for i in range(N_BINS):
        mask = (dist_v >= edges[i]) & (dist_v < edges[i + 1])
        if mask.sum() < 1:
            continue
        lags.append(0.5 * (edges[i] + edges[i + 1]))
        gammas.append(float(sq_v[mask].mean()))
        npairs.append(int(mask.sum()))
    return np.array(lags), np.array(gammas), np.array(npairs)


def _fit_wls(lags, gammas, npairs, model_fn):
    if len(lags) < 3:
        return None, np.inf
    sill0 = float(np.nanmax(gammas))
    a0 = float(lags[-1] * 0.5 + 1e-3)
    c00 = float(np.nanmin(gammas))
    weights = np.sqrt(np.clip(npairs, 1, None))

    def resid(p):
        c0, c, a = p
        return weights * (model_fn(lags, c0, c, a) - gammas)

    try:
        sol = least_squares(
            resid, x0=[c00, max(sill0 - c00, 1e-6), a0],
            bounds=([0.0, 0.0, 1e-3], [sill0 * 5 + 1, sill0 * 5 + 1, MAX_LAG_KM * 3]),
            max_nfev=1000,
        )
        c0, c, a = sol.x
        sse = float(np.sum((weights * (model_fn(lags, c0, c, a) - gammas)) ** 2))
        return {"nugget": float(c0), "psill": float(c), "range_km": float(a)}, sse
    except Exception:
        return None, np.inf


# ─── Clase principal ──────────────────────────────────────────────────────────

class KrigingService:
    """
    Servicio singleton de Kriging.
    Carga DAGMA → computa variograma → OK2D → cachea superficie.

    Uso:
        ks = KrigingService.get_instance()
        ks.load()                     # carga/entrena una vez
        val, sig = ks.interpolate(lat, lon, "SO2")
    """

    _instance: KrigingService | None = None

    def __init__(self):
        self._loaded = False
        self.kriging_surf: dict[str, dict[str, Any]] = {}  # gas → {z, sigma2, lats, lons}
        self.kriging_kpi: dict[str, dict[str, float]] = {}
        self.variogram_fits: dict[str, dict] = {}
        self.dagma_daily: pd.DataFrame | None = None
        self.lat_grid: np.ndarray | None = None
        self.lon_grid: np.ndarray | None = None

    @classmethod
    def get_instance(cls) -> KrigingService:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def is_loaded(self) -> bool:
        return self._loaded

    def load(self, force_recompute: bool = False) -> None:
        """Carga (o computa) el modelo de Kriging."""
        if self._loaded and not force_recompute:
            return
        t0 = time.perf_counter()
        print("[KrigingService] Iniciando...")

        # ─── 1. Intentar cargar desde caché ───────────────────────────────
        if CACHE_PATH.exists() and not force_recompute:
            try:
                with open(CACHE_PATH, "rb") as f:
                    data = pickle.load(f)
                self.kriging_surf = data["kriging_surf"]
                self.kriging_kpi = data["kriging_kpi"]
                self.variogram_fits = data["variogram_fits"]
                self.lat_grid = data["lat_grid"]
                self.lon_grid = data["lon_grid"]
                self._loaded = True
                print(f"  ✓ Cargado desde caché ({CACHE_PATH})")
                print(f"[KrigingService] Listo en {time.perf_counter() - t0:.1f}s")
                return
            except Exception as e:
                print(f"  ⚠ Caché corrupto: {e}. Recomputando...")

        # ─── 2. Cargar DAGMA ──────────────────────────────────────────────
        print("  Cargando DAGMA...")
        if not DAGMA_PATH.exists():
            raise FileNotFoundError(f"DAGMA no encontrado en {DAGMA_PATH}")
        dagma_wide = pd.read_parquet(DAGMA_PATH)

        # Wide → long
        rows = []
        for gas, cols in POLLUTANT_COLS.items():
            for c in cols:
                if c not in dagma_wide.columns:
                    continue
                if c.endswith("_NO2") or c.endswith("_SO2"):
                    st = c[:-4]
                elif c.endswith("_O3"):
                    st = c[:-3]
                else:
                    st = c
                sub = dagma_wide[["Fecha_Hora", c]].dropna()
                for _, r in sub.iterrows():
                    rows.append({
                        "estacion": st, "gas": gas,
                        "fecha": r["Fecha_Hora"], "concentracion": float(r[c]),
                    })
        dagma_long = pd.DataFrame(rows)
        dagma_long["fecha"] = pd.to_datetime(dagma_long["fecha"])
        dagma_long["dia"] = dagma_long["fecha"].dt.normalize()

        # Diario por mediana
        dagma_daily = (
            dagma_long
            .groupby(["estacion", "gas", "dia"])
            .concentracion.median()
            .reset_index()
            .dropna(subset=["concentracion"])
        )
        dagma_daily["lat"] = dagma_daily["estacion"].map(
            lambda e: DAGMA_STATIONS.get(e, (np.nan, np.nan))[0])
        dagma_daily["lon"] = dagma_daily["estacion"].map(
            lambda e: DAGMA_STATIONS.get(e, (np.nan, np.nan))[1])
        dagma_daily = dagma_daily.dropna(subset=["lat", "lon"])
        self.dagma_daily = dagma_daily
        print(f"  DAGMA: {len(dagma_daily)} filas, {dagma_daily['estacion'].nunique()} estaciones")

        # ─── 3. Grilla de interpolación común ────────────────────────────
        self.lat_grid = np.arange(BBOX[1], BBOX[3] + GRID_RES, GRID_RES)
        self.lon_grid = np.arange(BBOX[0], BBOX[2] + GRID_RES, GRID_RES)
        print(f"  Grilla: {len(self.lat_grid)}×{len(self.lon_grid)} = {len(self.lat_grid)*len(self.lon_grid)} pts")

        # ─── 4. Por cada gas (SO2, O3): variograma + kriging ─────────────
        for gas in POLLUTANTS_KRIGING:
            print(f"\n  [{gas}] Computando...")
            sub = (
                dagma_daily[dagma_daily.gas == gas]
                .groupby(["estacion", "lat", "lon"])
                .concentracion.median()
                .reset_index()
            )
            if len(sub) < 3:
                print(f"    SKIP: solo {len(sub)} estaciones (<3)")
                continue

            # Variograma experimental
            coords_km = np.column_stack([
                sub["lon"].values * DEG_TO_KM,
                sub["lat"].values * DEG_TO_KM,
            ])
            vals = sub.concentracion.values
            lags, gammas, npairs = _semivariogram_exp(coords_km, vals)

            if len(lags) < 3:
                print(f"    SKIP: solo {len(lags)} lags")
                continue

            # Ajuste WLS de modelos
            best = None
            best_name = None
            best_sse = np.inf
            all_models = {}
            for name, fn in _MODELS.items():
                p, sse = _fit_wls(lags, gammas, npairs, fn)
                if p is None:
                    continue
                all_models[name] = {"params": p, "sse": sse}
                if sse < best_sse:
                    best, best_name, best_sse = p, name, sse

            if best is None:
                print(f"    SKIP: ajuste falló")
                continue

            self.variogram_fits[gas] = {
                "best_model": best_name,
                "params": best,
                "n_estaciones": int(len(sub)),
            }
            print(f"    Mejor: {best_name}  nugget={best['nugget']:.3f}  "
                  f"psill={best['psill']:.3f}  range={best['range_km']:.2f} km")

            # ─── OrdinaryKriging 2D ──────────────────────────────────────
            range_deg = max(best["range_km"] / DEG_TO_KM, 1e-3)
            psill = max(best["psill"], 1e-3)
            nugget = max(best["nugget"], 0.0)

            OK = OrdinaryKriging(
                sub["lon"].values, sub["lat"].values, sub["concentracion"].values,
                variogram_model=best_name,
                variogram_parameters={
                    "sill": psill + nugget,
                    "range": range_deg,
                    "nugget": nugget,
                },
                verbose=False, enable_plotting=False,
            )
            z_grid, ss_grid = OK.execute("grid", self.lon_grid, self.lat_grid)
            z_grid = np.asarray(z_grid, dtype=np.float64)
            ss_grid = np.asarray(ss_grid, dtype=np.float64)

            self.kriging_surf[gas] = {
                "z": z_grid,
                "sigma2": ss_grid,
                "sigma": np.sqrt(np.clip(ss_grid, 0, None)),
                "lats": self.lat_grid,
                "lons": self.lon_grid,
            }
            print(f"    Superficie: {z_grid.shape}")

        # ─── 5. Calcular LOO-CV ──────────────────────────────────────────
        print("\n  [LOO-CV espacial]")
        for gas in POLLUTANTS_KRIGING:
            if gas not in self.kriging_surf:
                continue
            fit = self.variogram_fits.get(gas)
            if not fit:
                continue
            sub = (
                dagma_daily[dagma_daily.gas == gas]
                .groupby(["estacion", "lat", "lon"])
                .concentracion.median()
                .reset_index()
            )
            range_deg = max(fit["params"]["range_km"] / DEG_TO_KM, 1e-3)
            psill = max(fit["params"]["psill"], 1e-3)
            nugget = max(fit["params"]["nugget"], 0.0)

            loo_pred, loo_true = [], []
            for i in range(len(sub)):
                train = sub.drop(sub.index[i])
                test = sub.iloc[i]
                try:
                    OKi = OrdinaryKriging(
                        train["lon"].values, train["lat"].values, train["concentracion"].values,
                        variogram_model=fit["best_model"],
                        variogram_parameters={
                            "sill": psill + nugget,
                            "range": range_deg,
                            "nugget": nugget,
                        },
                        verbose=False, enable_plotting=False,
                    )
                    zp, _ = OKi.execute("points", np.array([test["lon"]]), np.array([test["lat"]]))
                    loo_pred.append(float(zp[0]))
                    loo_true.append(float(test["concentracion"]))
                except Exception as e:
                    print(f"    LOO {gas}/{test['estacion']}: {e}")

            if len(loo_pred) >= 2:
                yp = np.array(loo_pred)
                yt = np.array(loo_true)
                rmse = float(np.sqrt(mean_squared_error(yt, yp)))
                mae = float(mean_absolute_error(yt, yp))
                try:
                    r2 = float(r2_score(yt, yp))
                except Exception:
                    r2 = float("nan")
                self.kriging_kpi[gas] = {"rmse": rmse, "mae": mae, "r2": r2, "n": len(yp)}
                print(f"    {gas}: RMSE={rmse:.2f}  MAE={mae:.2f}  R²={r2:.3f}  n={len(yp)}")

        # ─── 6. Guardar caché ────────────────────────────────────────────
        try:
            with open(CACHE_PATH, "wb") as f:
                pickle.dump({
                    "kriging_surf": self.kriging_surf,
                    "kriging_kpi": self.kriging_kpi,
                    "variogram_fits": self.variogram_fits,
                    "lat_grid": self.lat_grid,
                    "lon_grid": self.lon_grid,
                }, f)
            print(f"\n  ✓ Caché guardado: {CACHE_PATH}")
        except Exception as e:
            print(f"  ⚠ Error guardando caché: {e}")

        self._loaded = True
        print(f"[KrigingService] Listo en {time.perf_counter() - t0:.1f}s")

    # ─── Interpolación bilineal en superficie krigeada ─────────────────────

    def interpolate(self, lat: float, lon: float, contaminant: str
                    ) -> tuple[float, float]:
        """
        Interpola el valor krigeado y la desviación σ en (lat, lon).

        Args:
            lat, lon: coordenadas del punto
            contaminant: "NO2", "SO2" o "O3"

        Returns:
            (z_kriged: float, sigma: float)
            Si no hay superficie krigeada para ese contaminante, retorna (0, 0).
        """
        if not self._loaded:
            self.load()

        if contaminant not in self.kriging_surf:
            # NO2 no tiene kriging; retornamos 0
            return 0.0, 0.0

        surf = self.kriging_surf[contaminant]
        z = surf["z"]
        sigma = surf["sigma"]
        lats = surf["lats"]
        lons = surf["lons"]

        # Índices del punto más cercano en la grilla
        i = np.argmin(np.abs(lats - lat))
        j = np.argmin(np.abs(lons - lon))

        return float(z[i, j]), float(sigma[i, j])

    def get_kpi(self, contaminant: str) -> dict[str, float] | None:
        """Retorna KPIs de Kriging (RMSE, MAE, R²) si existen."""
        return self.kriging_kpi.get(contaminant)

    def get_summary(self) -> dict:
        """Resumen del servicio para /validate endpoint."""
        summary = {}
        for gas in POLLUTANTS_KRIGING:
            if gas in self.kriging_kpi:
                summary[gas] = self.kriging_kpi[gas].copy()
                summary[gas]["kpi_rmse_max"] = KPI_UGM3[gas]
                summary[gas]["cumple"] = self.kriging_kpi[gas]["rmse"] <= KPI_UGM3[gas]
        summary["NO2"] = {
            "rmse": None, "mae": None, "r2": None,
            "kpi_rmse_max": KPI_UGM3["NO2"],
            "cumple": None,
            "nota": "NO2 excluido: solo 1 estacion DAGMA (Univalle)",
        }
        return summary
