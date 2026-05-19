// ─── Geographic Center of Cali ──────────────────────────────────────────────
export const CALI_CENTER: [number, number] = [3.4516, -76.532];

// ─── DAGMA Monitoring Stations ──────────────────────────────────────────────
export const DAGMA_STATIONS = [
  { id: 1, name: "Estación Pance",        lat: 3.3333, lon: -76.5431, zone: "Sur" },
  { id: 2, name: "Estación Compartir",    lat: 3.3897, lon: -76.5303, zone: "Sur" },
  { id: 3, name: "Estación Univalle",     lat: 3.3739, lon: -76.5342, zone: "Sur" },
  { id: 4, name: "Estación Centro",       lat: 3.4372, lon: -76.5225, zone: "Centro" },
  { id: 5, name: "Estación Chiminangos",  lat: 3.4506, lon: -76.5431, zone: "Centro" },
  { id: 6, name: "Estación Meléndez",     lat: 3.3861, lon: -76.5539, zone: "Oeste" },
  { id: 7, name: "Estación Guabal",       lat: 3.4208, lon: -76.5347, zone: "Centro" },
  { id: 8, name: "Estación Yumbo",        lat: 3.5933, lon: -76.4956, zone: "Norte" },
  { id: 9, name: "Estación Acopi",        lat: 3.5700, lon: -76.4980, zone: "Norte" },
];

// ─── Contaminants & Horizons ────────────────────────────────────────────────
export const CONTAMINANTS = ["NO2", "SO2", "O3"] as const;
export type Contaminant = typeof CONTAMINANTS[number];

export const HORIZONS = ["T+1", "T+3", "T+7"] as const;
export type Horizon = typeof HORIZONS[number];

// ─── AQI Color Scale ─────────────────────────────────────────────────────────
export const AQI_SCALE = [
  { threshold: 0.0,  color: "#10b981", label: "Bueno" },
  { threshold: 0.25, color: "#f59e0b", label: "Moderado" },
  { threshold: 0.50, color: "#f97316", label: "Dañino" },
  { threshold: 0.75, color: "#e11d48", label: "Peligroso" },
  { threshold: 0.90, color: "#9333ea", label: "Emergencia" },
];

export function getColorForValue(value: number, min: number, max: number): string {
  const normalized = (value - min) / (max - min + 1e-9);
  let color = AQI_SCALE[0].color;
  for (const step of AQI_SCALE) {
    if (normalized >= step.threshold) color = step.color;
  }
  return color;
}

// ─── Map Tile URLs ────────────────────────────────────────────────────────────
export const TILE_DARK  = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
export const TILE_LIGHT = "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";
export const TILE_ATTRIBUTION = '&copy; <a href="https://carto.com">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>';

// ─── Contaminant Units & Ranges ──────────────────────────────────────────────
export const CONTAMINANT_META: Record<string, { unit: string; min: number; max: number; label: string }> = {
  NO2: { unit: "µg/m³", min: 0,  max: 200, label: "Dióxido de nitrógeno" },
  SO2: { unit: "µg/m³", min: 0,  max: 100, label: "Dióxido de azufre" },
  O3:  { unit: "µg/m³", min: 0,  max: 180, label: "Ozono troposférico" },
};
