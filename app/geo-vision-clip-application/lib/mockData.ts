import { DAGMA_STATIONS, CONTAMINANTS, HORIZONS } from "./constants";

// ─── Seeded random for deterministic mocks ───────────────────────────────────
function seededRandom(seed: number) {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) & 0xffffffff;
    return (s >>> 0) / 0xffffffff;
  };
}

// ─── Generate a grid around a point ─────────────────────────────────────────
function generateGrid(lat: number, lon: number, radiusKm: number) {
  const rng = seededRandom(Math.round(lat * 100 + lon * 100));
  const step = 0.01;
  const cells = Math.ceil(radiusKm / 1.1);
  const lats: number[][] = [];
  const lons: number[][] = [];
  const values: number[][] = [];
  const variances: number[][] = [];

  for (let i = -cells; i <= cells; i++) {
    const rowLat: number[] = [];
    const rowLon: number[] = [];
    const rowVal: number[] = [];
    const rowVar: number[] = [];
    for (let j = -cells; j <= cells; j++) {
      const dist = Math.sqrt(i * i + j * j) / cells || 0;
      rowLat.push(lat + i * step);
      rowLon.push(lon + j * step);
      rowVal.push(30 + rng() * 100 * (1 - dist * 0.5));
      rowVar.push(2 + rng() * 15);
    }
    lats.push(rowLat);
    lons.push(rowLon);
    values.push(rowVal);
    variances.push(rowVar);
  }
  return { lats, lons, values, variances };
}

// ─── Mock /stations response ─────────────────────────────────────────────────
export function getMockStations() {
  const rng = seededRandom(42);
  return {
    stations: DAGMA_STATIONS.map((s) => ({
      ...s,
      last_reading: {
        NO2: Math.round(20 + rng() * 60),
        SO2: Math.round(5 + rng() * 40),
        O3:  Math.round(60 + rng() * 80),
      },
      timestamp: "2026-05-18T16:00:00",
    })),
  };
}

// ─── Mock /predict response ──────────────────────────────────────────────────
export function getMockPrediction(
  lat: number,
  lon: number,
  radiusKm: number,
  contaminant: string,
  horizon: string
) {
  const seed = Math.round(lat * 100 + lon * 100 + CONTAMINANTS.indexOf(contaminant as never) * 7 + HORIZONS.indexOf(horizon as never) * 3);
  const rng = seededRandom(seed + 1);

  const predicted_value = parseFloat((30 + rng() * 100).toFixed(1));
  const uncertainty_sigma = parseFloat((2 + rng() * 12).toFixed(1));

  const all_horizons: Record<string, Record<string, number>> = {};
  for (const h of HORIZONS) {
    all_horizons[h] = {};
    for (const c of CONTAMINANTS) {
      const r2 = seededRandom(seed + c.charCodeAt(0) + HORIZONS.indexOf(h));
      all_horizons[h][c] = parseFloat((20 + r2() * 100).toFixed(1));
    }
  }

  return {
    predicted_value,
    uncertainty_sigma,
    unit: "µg/m³",
    grid: generateGrid(lat, lon, radiusKm),
    all_horizons,
    timestamp: "2026-05-18T17:30:00",
    model_version: "geovision-clip-v1.0",
    md5_checkpoint: "a3f9c2b1d4e8f70a",
  };
}

// ─── Mock /validate response ─────────────────────────────────────────────────
export function getMockValidation() {
  return {
    loo_cv: {
      NO2: { RMSE: 5.2, MAE: 3.8, R2: 0.71 },
      SO2: { RMSE: 3.1, MAE: 2.4, R2: 0.68 },
      O3:  { RMSE: 8.4, MAE: 6.1, R2: 0.61 },
    },
    moran_i: { I: 0.41, p_value: 0.002 },
    kpis: {
      recall_at_1: 0.52,
      recall_at_5: 0.79,
      sparsity_sae: 0.78,
      loss_sae_recon: 0.031,
    },
  };
}

// ─── Mock historical time series ─────────────────────────────────────────────
export function getMockTimeSeries(contaminant: string) {
  const rng = seededRandom(contaminant.charCodeAt(0) * 13);
  const dates = ["May 11", "May 12", "May 13", "May 14", "May 15", "May 16", "May 17", "May 18"];
  return dates.map((date) => ({
    date,
    value: parseFloat((25 + rng() * 80).toFixed(1)),
  }));
}
