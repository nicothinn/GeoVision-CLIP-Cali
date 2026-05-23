export type BarrioProperties = {
  id_barrio: string;
  barrio: string;
  comuna: string;
};

export type ComunaProperties = {
  comuna: string;
};

export type GeoGeometry = {
  type: string;
  coordinates: unknown;
};

export type BarrioFeature = {
  type: "Feature";
  properties: BarrioProperties;
  geometry: GeoGeometry;
};

export type ComunaFeature = {
  type: "Feature";
  properties: ComunaProperties;
  geometry: GeoGeometry;
};

export type BarriosCollection = {
  type: "FeatureCollection";
  features: BarrioFeature[];
};

export type ComunasCollection = {
  type: "FeatureCollection";
  features: ComunaFeature[];
};

const BARRIOS_URL = "/geo/barrios_cali.geojson";
const COMUNAS_URL = "/geo/comunas_cali.geojson";

let barriosCache: BarriosCollection | null = null;
let comunasCache: ComunasCollection | null = null;

async function fetchGeoJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`No se pudo cargar ${url}: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function loadBarriosGeoJson(): Promise<BarriosCollection> {
  if (!barriosCache) {
    barriosCache = await fetchGeoJson<BarriosCollection>(BARRIOS_URL);
  }
  return barriosCache;
}

export async function loadComunasGeoJson(): Promise<ComunasCollection> {
  if (!comunasCache) {
    comunasCache = await fetchGeoJson<ComunasCollection>(COMUNAS_URL);
  }
  return comunasCache;
}

export async function loadMcBarriosLayers(): Promise<{
  barrios: BarriosCollection;
  comunas: ComunasCollection;
}> {
  const [barrios, comunas] = await Promise.all([
    loadBarriosGeoJson(),
    loadComunasGeoJson(),
  ]);
  return { barrios, comunas };
}
