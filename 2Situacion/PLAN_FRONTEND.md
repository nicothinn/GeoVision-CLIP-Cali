# 🌐 Plan de Ejecución — Frontend GeoVision-CLIP Cali

> Stack obligatorio: **React + Vite** | **FastAPI** | **Docker** | **Leaflet**
> Prohibido: Streamlit, Gradio
> Bonus: Dark mode (+2 pts), Audio Whisper (+3 pts)

---

## 1. Arquitectura General del Sistema

```
┌────────────────────────────────────────────────────────────┐
│                    USUARIO (Navegador)                       │
│              React + Vite + Leaflet + Recharts               │
└─────────────────────┬──────────────────────────────────────┘
                      │ HTTP/REST
┌─────────────────────▼──────────────────────────────────────┐
│                  FastAPI Backend                             │
│   /predict  /validate  /stations  /download  /health        │
└──────┬────────────────┬───────────────────────────────────┘
       │                │
┌──────▼──────┐  ┌──────▼──────────────────────────────────┐
│  GeoVision  │  │  Geoestadística                          │
│  CLIP+SAE   │  │  PyKrige + PySAL (Moran/LISA)            │
│  ConvLSTM   │  │  ST-Kriging → varianza σ²                │
└──────┬──────┘  └──────┬───────────────────────────────────┘
       └────────┬────────┘
┌───────────────▼────────────────────────────────────────────┐
│  Zarr/Parquet en GCS/S3 (datos panel ≥50GB)                │
└────────────────────────────────────────────────────────────┘
```

---

## 2. Estructura de Carpetas del Proyecto

```
geovision-cali/
├── frontend/                    # React + Vite
│   ├── public/
│   │   └── favicon.ico
│   ├── src/
│   │   ├── components/
│   │   │   ├── Map/
│   │   │   │   ├── CaliMap.jsx          # Mapa Leaflet principal
│   │   │   │   ├── DagmaMarkers.jsx     # 9 estaciones DAGMA
│   │   │   │   ├── GradientOverlay.jsx  # Overlay de contaminante
│   │   │   │   └── UncertaintyLayer.jsx # Capa opacidad σ²
│   │   │   ├── Controls/
│   │   │   │   ├── ContaminantSelector.jsx  # NO2/SO2/O3
│   │   │   │   ├── HorizonSlider.jsx        # T+1, T+3, T+7
│   │   │   │   ├── RadiusControl.jsx        # 1–15 km
│   │   │   │   └── DownloadButtons.jsx      # GeoTIFF / CSV
│   │   │   ├── Dashboard/
│   │   │   │   ├── KPICards.jsx         # Recall@1, Sparsity, etc.
│   │   │   │   ├── PredictionPanel.jsx  # Valor ± σ del punto clickeado
│   │   │   │   ├── GridMaps.jsx         # 9 mapas (3x3)
│   │   │   │   └── TimeSeriesChart.jsx  # Recharts historico
│   │   │   ├── Sidebar/
│   │   │   │   ├── StationList.jsx      # Lista 9 estaciones DAGMA
│   │   │   │   └── ValidationTable.jsx  # LOO-CV por estación
│   │   │   └── Layout/
│   │   │       ├── Navbar.jsx
│   │   │       ├── ThemeToggle.jsx      # Dark/Light mode
│   │   │       └── Footer.jsx
│   │   ├── hooks/
│   │   │   ├── usePrediction.js    # React Query → /predict
│   │   │   ├── useStations.js      # /stations
│   │   │   └── useMapClick.js      # click lat/lon
│   │   ├── store/
│   │   │   └── appStore.js         # Zustand: tema, contaminante, horizonte
│   │   ├── services/
│   │   │   └── api.js              # axios instance baseURL
│   │   ├── styles/
│   │   │   ├── index.css           # Variables CSS dark/light
│   │   │   └── map.css
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
│
├── backend/                     # FastAPI
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, rutas
│   │   ├── routers/
│   │   │   ├── predict.py       # POST /predict
│   │   │   ├── validate.py      # GET /validate
│   │   │   ├── stations.py      # GET /stations
│   │   │   └── download.py      # GET /download/{format}
│   │   ├── services/
│   │   │   ├── clip_service.py  # Carga modelo GeoVision-CLIP
│   │   │   ├── kriging_service.py # ST-Kriging
│   │   │   └── data_service.py  # Acceso Zarr/S5P
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic: PredictRequest, PredictResponse
│   │   └── config.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml
├── nginx.conf                   # Reverse proxy
└── README.md
```

---

## 3. Diseño Visual de la Interfaz

### 3.1 Paleta de Colores (Tailwind Slate + Emerald)

Base **Slate** (grises azulados) — fatigan menos la vista en sesiones largas de análisis.

#### Colores Base de la Interfaz

| Elemento | Tailwind | Hex (Dark / Light) | Propósito |
|----------|----------|--------------------|-----------|
| Fondo Principal | `slate-900` / `slate-50` | `#0f172a` / `#f8fafc` | Lienzo de la app |
| Tarjetas y Sidebar | `slate-800` / `white` | `#1e293b` / `#ffffff` | Contenedores |
| Texto Principal | `slate-100` / `slate-900` | `#f1f5f9` / `#0f172a` | Títulos y métricas |
| Acento / Brand | `emerald-500` | `#10b981` | Botones activos, DAGMA |
| Bordes | `slate-700/50` | `#374151` semitransparente | Glassmorphism |

#### Colores Semánticos — Escala AQI (semáforo ambiental)

```
🟢 Bueno:              emerald-500  #10b981
🟡 Moderado:           amber-500    #f59e0b
🟠 Dañino a la salud:  orange-500   #f97316
🔴 Peligroso:          rose-600     #e11d48
🟣 Emergencia:         purple-600   #9333ea
```

```css
/* Dark Mode */
--bg-primary:      #0f172a;   /* slate-900 */
--bg-card:         #1e293b;   /* slate-800 */
--accent-brand:    #10b981;   /* emerald-500 */
--aqi-good:        #10b981;
--aqi-moderate:    #f59e0b;
--aqi-unhealthy:   #f97316;
--aqi-dangerous:   #e11d48;
--aqi-emergency:   #9333ea;
--text-primary:    #f1f5f9;   /* slate-100 */
--text-secondary:  #94a3b8;   /* slate-400 */
--border:          rgba(51,65,85,0.5); /* slate-700/50 */

/* Light Mode */
--bg-primary:      #f8fafc;   /* slate-50 */
--bg-card:         #ffffff;
--text-primary:    #0f172a;   /* slate-900 */
--text-secondary:  #475569;   /* slate-600 */
```

### 3.2 Gradientes por Contaminante (escala AQI)

Usa **siempre** la misma escala AQI de 5 colores para todos los contaminantes. El cerebro humano ya está entrenado para el semáforo ambiental:

```js
// colorScale.js — reutilizar en GradientOverlay y Tooltips
export const AQI_SCALE = [
  { threshold: 0.0,  color: '#10b981', label: 'Bueno' },       // emerald-500
  { threshold: 0.25, color: '#f59e0b', label: 'Moderado' },    // amber-500
  { threshold: 0.50, color: '#f97316', label: 'Dañino' },      // orange-500
  { threshold: 0.75, color: '#e11d48', label: 'Peligroso' },   // rose-600
  { threshold: 0.90, color: '#9333ea', label: 'Emergencia' },  // purple-600
];

// Función de interpolación para el overlay Leaflet:
export function getColorForValue(value, min, max) {
  const normalized = (value - min) / (max - min + 1e-9);
  const step = AQI_SCALE.findLast(s => normalized >= s.threshold);
  return step?.color ?? '#10b981';
}
```

### 3.3 Estilo del Mapa — Tiles Base (Crucial)

> ⚠️ El tile por defecto de OpenStreetMap tiene demasiados colores (calles amarillas, parques verdes) y **destruye visualmente** los gradientes de contaminantes.

```js
// CaliMap.jsx — tiles según tema
const TILE_DARK  = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
const TILE_LIGHT = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';
// CartoDB Dark Matter (oscuro) y CartoDB Positron (claro)
// → mapas base en escala de grises → cualquier overlay resalta inmediatamente

<TileLayer
  url={theme === 'dark' ? TILE_DARK : TILE_LIGHT}
  attribution='&copy; <a href="https://carto.com">CARTO</a>'
/>
```

### 3.4 Efectos de UI — Glassmorphism y Tipografía

#### Paneles flotantes sobre el mapa
```jsx
// Clase Tailwind para sidebar y controles flotantes:
// bg-slate-900/80 backdrop-blur-md border border-slate-700/50 rounded-xl
<div className="bg-slate-900/80 backdrop-blur-md border border-slate-700/50 rounded-xl p-4">
  {/* Controles */}
</div>
```

#### Tipografía
```html
<!-- index.html → Google Fonts -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
```

```css
body        { font-family: 'Inter', sans-serif; }
.mono-value { font-family: 'JetBrains Mono', monospace; } /* para 24.5 µg/m³ */
```

#### Slider Temporal — Estilo "línea de tiempo de video"
```jsx
import { Play, Pause, SkipForward } from 'lucide-react';

// Centrado debajo del mapa, ancho completo
// Apariencia: barra de progreso tipo reproductor multimedia
<div className="flex items-center gap-4 w-full px-8 py-3
                bg-slate-900/80 backdrop-blur-md border-t border-slate-700/50">
  <button onClick={togglePlay}>
    {playing ? <Pause size={20}/> : <Play size={20}/>}
  </button>
  <input type="range" min={0} max={2} value={horizonIndex}
         className="flex-1 accent-emerald-500"
         onChange={e => setHorizon(HORIZONS[e.target.value])}/>
  <div className="flex gap-2">
    {HORIZONS.map((h, i) => (
      <span key={h}
            className={`px-3 py-1 rounded-full text-sm font-mono
                       ${horizonIndex===i ? 'bg-emerald-500 text-white' : 'bg-slate-700 text-slate-300'}`}>
        {h}
      </span>
    ))}
  </div>
</div>
```

### 3.5 Layout Principal (Wireframe)

```
┌────────────────────────────────────────────────────────────────┐
│  🌍 GeoVision-CLIP Cali    [NO₂][SO₂][O₃]    [🔍 buscar]  [🌙]│ ← Navbar slate-900
├──────────┬─────────────────────────────────────┬───────────────┤
│          │                                     │               │
│ SIDEBAR  │    MAPA LEAFLET PRINCIPAL            │  PANEL        │
│ glass-   │    CartoDB Dark/Positron             │  glass-       │
│ morphism │    + 9 marcadores emerald DAGMA       │  morphism     │
│          │    + overlay gradiente AQI            │               │
│ Estacion.│    + opacidad σ² (uncertainty)        │  Valor ± σ   │
│ activas  │    + leyenda AQI (5 colores)          │  mono-font    │
│          │                                     │               │
│ [NO₂ ▼] │                                     │  Sparkline    │
│ Radio:5km│                                     │  8 fechas     │
│ [━━●━━━] │                                     │  (recharts)   │
│          │                                     │               │
├──────────┴──────────── SLIDER ─────────────────┴───────────────┤
│  ◀  [▶]  ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━○  │
│          [T+1]              [T+3]              [T+7]            │ ← lucide-react
├────────────────────────────────────────────────────────────────┤
│  GRILLA 3×3 — sin zoomControl, título flotante absolute        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │ NO₂ T+1  │  │ NO₂ T+3  │  │ NO₂ T+7  │  ← label absolute  │
│  └──────────┘  └──────────┘  └──────────┘    top-2 left-2     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐    text-xs          │
│  │ SO₂ T+1  │  │ SO₂ T+3  │  │ SO₂ T+7  │    bg-slate-900/90 │
│  └──────────┘  └──────────┘  └──────────┘                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │ O₃  T+1  │  │ O₃  T+3  │  │ O₃  T+7  │                    │
│  └──────────┘  └──────────┘  └──────────┘                     │
├────────────────────────────────────────────────────────────────┤
│  Recall@1: 0.52  Recall@5: 0.79  Sparsity: 0.78  Moran I:0.41│ ← mono-font
└────────────────────────────────────────────────────────────────┘
```

#### Reglas de la Grilla 3×3
```jsx
// GridMaps.jsx — sin controles de zoom, etiqueta flotante
<MapContainer
  center={CALI_CENTER} zoom={11}
  zoomControl={false}          // ← Crítico: eliminar zoom en mapas pequeños
  scrollWheelZoom={false}
  dragging={false}
  className="h-32 w-full rounded-lg"
>
  {/* Etiqueta flotante absolute */}
  <div className="absolute top-2 left-2 z-[400] bg-slate-900/90
                  px-2 py-1 rounded text-xs text-slate-200 font-mono">
    {contaminant} {horizon}
  </div>
  <TileLayer url={TILE_DARK} />
  <GradientOverlay data={data} />
</MapContainer>
```

---

## 4. Endpoints del Backend

### POST /predict
```json
// Request:
{
  "lat": 3.4516,
  "lon": -76.5320,
  "radius_km": 5,
  "contaminant": "NO2",
  "horizon": "T+1"
}

// Response:
{
  "predicted_value": 42.3,
  "uncertainty_sigma": 8.1,
  "unit": "µg/m³",
  "grid": {
    "lats": [[...], ...],
    "lons": [[...], ...],
    "values": [[...], ...],
    "variances": [[...], ...]
  },
  "all_horizons": {
    "T+1": { "NO2": 42.3, "SO2": 12.1, "O3": 87.4 },
    "T+3": { "NO2": 45.1, "SO2": 13.0, "O3": 85.2 },
    "T+7": { "NO2": 41.8, "SO2": 11.8, "O3": 89.1 }
  },
  "timestamp": "2026-05-18T17:30:00",
  "model_version": "geovision-clip-v1.0",
  "md5_checkpoint": "a3f9c2b1..."
}
```

### GET /stations
```json
{
  "stations": [
    {
      "id": "DAGMA-01",
      "name": "Estación Centro",
      "lat": 3.4372,
      "lon": -76.5225,
      "last_reading": { "NO2": 38.2, "SO2": 9.1, "O3": 92.4 },
      "timestamp": "2026-05-18T16:00:00"
    }
    // ... 8 más
  ]
}
```

### GET /validate
```json
{
  "loo_cv": {
    "NO2": { "RMSE": 5.2, "MAE": 3.8, "R2": 0.71 },
    "SO2": { "RMSE": 3.1, "MAE": 2.4, "R2": 0.68 },
    "O3":  { "RMSE": 8.4, "MAE": 6.1, "R2": 0.61 }
  },
  "moran_i": { "I": 0.41, "p_value": 0.002 },
  "kpis": {
    "recall_at_1": 0.52,
    "recall_at_5": 0.79,
    "sparsity_sae": 0.78,
    "loss_sae_recon": 0.031
  }
}
```

### GET /download/{format}?lat=&lon=&contaminant=
- `format` = `geotiff` o `csv`
- Devuelve archivo para descarga directa

---

## 5. Componentes Clave — Código Base

### 5.1 CaliMap.jsx (Leaflet)
```jsx
import { MapContainer, TileLayer, useMapEvents } from 'react-leaflet';
import { useState } from 'react';

const CALI_CENTER = [3.4516, -76.5320];
const DAGMA_STATIONS = [...]; // 9 estaciones

export function CaliMap({ onPointClick, contaminant, gradientData }) {
  function ClickHandler() {
    useMapEvents({
      click: (e) => onPointClick(e.latlng.lat, e.latlng.lng)
    });
    return null;
  }

  return (
    <MapContainer center={CALI_CENTER} zoom={12} className="map-container">
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution="CartoDB Dark Matter"
      />
      <ClickHandler />
      <DagmaMarkers stations={DAGMA_STATIONS} />
      {gradientData && <GradientOverlay data={gradientData} contaminant={contaminant} />}
    </MapContainer>
  );
}
```

### 5.2 usePrediction.js (React Query)
```js
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

export function usePrediction(lat, lon, contaminant, horizon, radiusKm) {
  return useQuery({
    queryKey: ['prediction', lat, lon, contaminant, horizon],
    queryFn: () => api.post('/predict', { lat, lon, contaminant, horizon, radius_km: radiusKm }),
    enabled: lat !== null && lon !== null,
    staleTime: 5 * 60 * 1000,  // 5 min cache
  });
}
```

### 5.3 GridMaps.jsx (9 mapas miniatura)
```jsx
const CONTAMINANTS = ['NO2', 'SO2', 'O3'];
const HORIZONS = ['T+1', 'T+3', 'T+7'];

export function GridMaps({ allData }) {
  return (
    <div className="grid-3x3">
      {CONTAMINANTS.map(cont => (
        HORIZONS.map(hz => (
          <MiniMap
            key={`${cont}-${hz}`}
            data={allData?.[cont]?.[hz]}
            contaminant={cont}
            horizon={hz}
          />
        ))
      ))}
    </div>
  );
}
```

### 5.4 ThemeToggle + Zustand store
```js
// store/appStore.js
import { create } from 'zustand';

export const useAppStore = create((set) => ({
  theme: 'dark',
  contaminant: 'NO2',
  horizon: 'T+1',
  radiusKm: 5,
  selectedPoint: null,

  toggleTheme: () => set(s => ({ theme: s.theme === 'dark' ? 'light' : 'dark' })),
  setContaminant: (c) => set({ contaminant: c }),
  setHorizon: (h) => set({ horizon: h }),
  setRadius: (r) => set({ radiusKm: r }),
  setPoint: (lat, lon) => set({ selectedPoint: { lat, lon } }),
}));
```

---

## 6. Backend FastAPI — Código Base

### main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import predict, validate, stations, download

app = FastAPI(
    title="GeoVision-CLIP Cali API",
    version="1.0.0",
    description="Predicción de contaminantes atmosféricos en Cali"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://tu-dominio.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router, prefix="/predict", tags=["Predicción"])
app.include_router(validate.router, prefix="/validate", tags=["Validación"])
app.include_router(stations.router, prefix="/stations", tags=["Estaciones"])
app.include_router(download.router, prefix="/download", tags=["Descarga"])

@app.get("/health")
def health():
    return {"status": "ok", "model": "geovision-clip-v1.0"}
```

### schemas.py (Pydantic)
```python
from pydantic import BaseModel, Field
from typing import Literal

class PredictRequest(BaseModel):
    lat: float = Field(..., ge=3.30, le=3.55, description="Latitud dentro de Cali")
    lon: float = Field(..., ge=-76.60, le=-76.40, description="Longitud dentro de Cali")
    radius_km: float = Field(5.0, ge=1.0, le=15.0)
    contaminant: Literal["NO2", "SO2", "O3"] = "NO2"
    horizon: Literal["T+1", "T+3", "T+7"] = "T+1"

class PredictResponse(BaseModel):
    predicted_value: float
    uncertainty_sigma: float
    unit: str
    grid: dict
    all_horizons: dict
    timestamp: str
    model_version: str
    md5_checkpoint: str
```

---

## 7. Docker Compose

```yaml
version: '3.9'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://backend:8000
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - MODEL_PATH=/models/geovision_clip_checkpoint.pt
      - ZARR_PATH=gs://geovision-cali/panel.zarr
      - HF_TOKEN=${HF_TOKEN}
    volumes:
      - ./models:/models
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - frontend
      - backend
```

---

## 8. Plan de Ejecución por Fases

### Fase 1 — Setup (Día 1, 2h)
```bash
# 1. Crear proyecto Vite + React
npm create vite@latest frontend -- --template react
cd frontend
npm install react-leaflet leaflet @tanstack/react-query zustand recharts axios

# 2. Crear backend FastAPI
mkdir backend && cd backend
pip install fastapi uvicorn pydantic torch open_clip_torch \
    sentence-transformers pykrige pysal rasterio

# 3. Init docker
touch docker-compose.yml
```

### Fase 2 — Frontend Base (Día 1-2, 6h)
1. Configurar variables CSS dark/light en `index.css`
2. Implementar `appStore.js` con Zustand
3. Crear `CaliMap.jsx` con Leaflet centrado en Cali
4. Añadir 9 marcadores DAGMA con coordenadas reales
5. Implementar `ThemeToggle` y conectar con store

### Fase 3 — Backend Base (Día 2-3, 6h)
1. Crear esquemas Pydantic
2. Endpoint `/health` y `/stations` (datos DAGMA hardcoded primero)
3. Cargar modelo GeoVision-CLIP en startup (singleton)
4. Endpoint `/predict` con respuesta mock primero, luego real

### Fase 4 — Integración (Día 3-4, 8h)
1. Conectar `usePrediction` hook con `/predict`
2. Renderizar `GradientOverlay` en el mapa con datos reales
3. Implementar `GridMaps` 3×3
4. Panel lateral con valor ± σ del punto clickeado
5. Slider temporal T+1/T+3/T+7

### Fase 5 — Features Avanzadas (Día 4-5, 6h)
1. Descarga GeoTIFF/CSV (`/download` endpoint + botones)
2. `ValidationTable` con LOO-CV por estación
3. `TimeSeriesChart` con Recharts (histórico de 8 fechas)
4. KPI Cards en footer

### Fase 6 — Polish y Deploy (Día 5-6, 4h)
1. Verificar dark mode completo (bonus +2 pts)
2. Animación slider temporal
3. Build producción: `npm run build`
4. Desplegar en Render o HuggingFace Spaces
5. Obtener URL pública y verificar latencia < 8s

---

## 9. Dependencias npm y pip

### package.json (frontend)
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-leaflet": "^4.2.1",
    "leaflet": "^1.9.4",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^4.5.0",
    "recharts": "^2.12.0",
    "axios": "^1.7.0",
    "lucide-react": "^0.400.0"
  }
}
```

### requirements.txt (backend)
```
fastapi==0.111.0
uvicorn[standard]==0.30.0
pydantic==2.7.0
torch==2.3.0
open_clip_torch==2.24.0
sentence-transformers==3.0.0
pykrige==1.7.2
esda==2.6.0
libpysal==4.10.0
rasterio==1.3.10
zarr==2.18.0
numpy==1.26.4
pandas==2.2.2
httpx==0.27.0
python-multipart==0.0.9
```

---

## 10. Coordenadas DAGMA (hardcoded para el mapa)

```js
export const DAGMA_STATIONS = [
  { id: 1, name: "Estación Pance",         lat: 3.3333, lon: -76.5431, zone: "Sur" },
  { id: 2, name: "Estación Compartir",     lat: 3.3897, lon: -76.5303, zone: "Sur" },
  { id: 3, name: "Estación Univalle",      lat: 3.3739, lon: -76.5342, zone: "Sur" },
  { id: 4, name: "Estación Centro",        lat: 3.4372, lon: -76.5225, zone: "Centro" },
  { id: 5, name: "Estación Chiminangos",   lat: 3.4506, lon: -76.5431, zone: "Centro" },
  { id: 6, name: "Estación Meléndez",      lat: 3.3861, lon: -76.5539, zone: "Oeste" },
  { id: 7, name: "Estación Guabal",        lat: 3.4208, lon: -76.5347, zone: "Centro" },
  { id: 8, name: "Estación Yumbo",         lat: 3.5933, lon: -76.4956, zone: "Norte" },
  { id: 9, name: "Estación Acopi",         lat: 3.5700, lon: -76.4980, zone: "Norte" },
];
```

---

## 11. Prompt Listo para Usar (para pasarle a otra IA)

```
Eres un experto en React + Vite, FastAPI y mapas interactivos con Leaflet.
Debes crear una aplicación web profesional para el proyecto GeoVision-CLIP Cali,
que predice contaminantes atmosféricos (NO2, SO2, O3) en cualquier punto de
Santiago de Cali, Colombia, usando un modelo de Deep Learning + Kriging.

STACK OBLIGATORIO:
- Frontend: React 18 + Vite + react-leaflet + zustand + @tanstack/react-query + recharts
- Backend: FastAPI + Uvicorn + Pydantic v2
- Docker + docker-compose con nginx reverse proxy
- NO usar Streamlit, Gradio ni ningún framework de prototipado rápido

FUNCIONALIDADES REQUERIDAS:
1. Mapa Leaflet centrado en Cali (lat=3.4516, lon=-76.5320, zoom=12)
   con tile layer dark (CartoDB Dark Matter)
2. 9 marcadores DAGMA con popup mostrando últimas lecturas
3. Click en cualquier punto del mapa → disparar POST /predict → mostrar overlay
4. Overlay de gradiente de colores para el contaminante seleccionado (NO2=verde-rojo, SO2=celeste-granate, O3=menta-azul)
5. Capa de incertidumbre (opacidad inversamente proporcional a σ² Kriging)
6. Controles: selector de contaminante (NO2/SO2/O3), slider de horizonte (T+1/T+3/T+7), radio (1-15km)
7. Panel lateral: valor predicho ± σ, tooltips, serie temporal histórica (recharts)
8. Grilla 3×3 de mapas miniatura (3 contaminantes × 3 horizontes)
9. Botones de descarga GeoTIFF y CSV
10. Tabla LOO-CV con resultados de validación por estación DAGMA
11. Barra de KPIs en footer: Recall@1, Recall@5, Sparsity SAE, Moran I
12. Dark/Light mode toggle con persistencia (Zustand)
13. Totalmente responsive

PALETA DARK MODE:
--bg-primary: #0a0f1e (azul noche)
--bg-card: #1f2937
--accent-primary: #3b82f6 (azul eléctrico)
--accent-success: #10b981 (verde)
--accent-warning: #f59e0b (ámbar)
--accent-danger: #ef4444 (rojo)

ENDPOINTS BACKEND:
- POST /predict → { lat, lon, radius_km, contaminant, horizon } → { predicted_value, uncertainty_sigma, grid{lats,lons,values,variances}, all_horizons }
- GET /stations → lista de 9 estaciones DAGMA con coordenadas y lecturas
- GET /validate → métricas LOO-CV + Moran I + KPIs del modelo
- GET /download/{geotiff|csv} → archivo para descarga

ESTRUCTURA:
[usar la estructura de carpetas detallada del plan PLAN_FRONTEND.md]

DISEÑO Y ESTILOS:
- Paleta BASE: Tailwind Slate (slate-900/800/700) + Emerald-500 como acento de brand
- Escala AQI fija (5 colores): emerald-500 → amber-500 → orange-500 → rose-600 → purple-600
- Dark mode: fondo slate-900 (#0f172a), tarjetas slate-800 (#1e293b)
- Light mode: fondo slate-50 (#f8fafc), tarjetas white
- Persistencia del tema en Zustand + localStorage
- Tiles del mapa: CartoDB Dark Matter (modo oscuro) / CartoDB Positron (modo claro)
  → NUNCA usar el tile por defecto de OSM
- Paneles flotantes con glassmorphism: bg-slate-900/80 backdrop-blur-md border border-slate-700/50
- Tipografía: Inter (body) + JetBrains Mono (valores numéricos como '24.5 µg/m³ ± 2.1')
- Slider temporal: estilo reproductor de video con lucide-react (Play/Pause), centrado bajo el mapa
  Botones T+1/T+3/T+7 como pills con emerald-500 para el activo
- Grilla 3×3: zoomControl=false, dragging=false, scrollWheelZoom=false
  Cada mapa tiene etiqueta flotante: absolute top-2 left-2 z-[400] bg-slate-900/90 px-2 py-1 rounded text-xs
- El mapa principal ocupa ~60% del viewport (col-span en grid)
- Grilla 3×3 debajo del mapa con gap-2
- Footer con KPIs en font-mono
- Micro-animaciones: hover:scale-105 transition-all en tarjetas, hover:bg-emerald-600 en botones
- Latencia < 8s: mostrar spinner (lucide-react Loader2 animate-spin) mientras carga
- Leyenda AQI siempre visible en esquina del mapa principal
```

---

*Plan generado para GeoVision-CLIP Cali · Mayo 2026*
