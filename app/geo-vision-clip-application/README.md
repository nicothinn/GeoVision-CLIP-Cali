# GeoVision-CLIP Cali — Frontend + Backend

Aplicación web profesional en **Next.js 16 + Tailwind v4 + Leaflet** con **backend FastAPI** para visualizar predicciones de contaminantes atmosféricos (NO₂, SO₂, O₃) sobre Santiago de Cali.

---

## Arquitectura general

```
┌─────────────────────────────────────────────────────────────────┐
│                    HuggingFace Spaces / Local                    │
│                                                                  │
│  ┌─────────────────────────┐    ┌────────────────────────────┐  │
│  │   Frontend (Next.js 16)  │    │   Backend (FastAPI :8000)  │  │
│  │                         │    │                            │  │
│  │  :3000 (dev)            │◄──►│  POST /api/predict         │  │
│  │  build/ (prod static)   │    │  GET  /api/stations        │  │
│  │                         │    │  GET  /api/validate        │  │
│  │  hooks/ → /api/*        │    │  GET  /api/download/{fmt}  │  │
│  └─────────────────────────┘    └──────────┬─────────────────┘  │
│                                            │                    │
│                                 ┌──────────▼─────────────────┐  │
│                                 │   Modelos (modo prod)       │  │
│                                 │                            │  │
│                                 │  RemoteCLIP ViT-B/32       │  │
│                                 │  MS Adapter 13→12 canales  │  │
│                                 │  SAE 512→2048→512          │  │
│                                 │  Conv3DSit3 (531 canales)   │  │
│                                 └────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Modo desarrollo** (`MODE=dev`): los endpoints devuelven datos mock sin cargar modelos.
**Modo producción** (`MODE=prod`): carga los checkpoints entrenados y ejecuta inferencia real.

---

## Cómo correr en local

### Prerrequisitos

| Herramienta | Versión mínima | Verificar |
|-------------|---------------|-----------|
| Node.js | ≥ 18 | `node -v` |
| pnpm | cualquiera | `pnpm -v` |
| Python | ≥ 3.10 | `python --version` |

> **¿No tienes pnpm?** `npm install -g pnpm`

### Backend (FastAPI)

```powershell
# 1. Entrar a la carpeta
cd app/geo-vision-clip-application

# 2. Opcional: crear y activar entorno virtual
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r backend/requirements.txt

# 4. Opcional: instalar dependencias de modelos (para modo prod)
pip install torch open-clip-torch transformers huggingface_hub

# 5. Levantar servidor
#    Modo desarrollo (datos mock, sin modelos):
$env:MODE='dev'
uvicorn backend.main:app --reload --port 8000

#    Modo producción (modelos reales):
$env:MODE='prod'
uvicorn backend.main:app --reload --port 8000
```

El backend queda en: **http://localhost:8000**

Documentación interactiva (solo en modo dev): **http://localhost:8000/docs**

### Frontend (Next.js)

```bash
# 1. Entrar a la carpeta
cd app/geo-vision-clip-application

# 2. Instalar dependencias
pnpm install

# 3. Levantar servidor de desarrollo
pnpm dev
```

Frontend en: **http://localhost:3000**

En desarrollo, el `next.config.mjs` redirige automáticamente `/api/*` a `http://localhost:8000/api/*`.
En producción (build estático), las API routes de Next.js se usan de forma nativa.

### Variables de entorno

Crea un archivo `.env.local` si necesitas personalizar:

```env
# URL del backend FastAPI (solo si difiere del default)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Estructura completa del proyecto

```
geo-vision-clip-application/
│
├── backend/                      # ← Backend FastAPI (NUEVO)
│   ├── main.py                   # Entry point FastAPI + CORS + health check
│   ├── config.py                 # MODE=dev/prod, HOST, PORT, CORS
│   ├── requirements.txt          # Dependencias Python
│   │
│   ├── api/                      # Routers de la API
│   │   ├── predict.py            # POST /api/predict
│   │   ├── stations.py           # GET  /api/stations
│   │   ├── validate.py           # GET  /api/validate
│   │   └── download.py           # GET  /api/download/{csv|geotiff}
│   │
│   ├── models/                   # Arquitecturas de modelos (desde notebooks)
│   │   ├── sae.py                # SAE 512→2048→512 sin bias
│   │   ├── convlstm2d.py         # Conv3DSit3 (CNN 3D con MaxPool)
│   │   ├── geovision_clip_sae.py # RemoteCLIP + SAE completo
│   │   └── clip_metrics.py       # Recall@k, sparsity, MSE
│   │
│   ├── services/                 # Lógica de inferencia
│   │   ├── mock_inference.py     # Modo dev: datos mock deterministas
│   │   └── inference.py          # Modo prod: pipeline completo
│   │
│   ├── schemas/models.py         # Contratos Pydantic (request/response)
│   ├── data/stations.py          # 9 estaciones DAGMA
│   │
│   └── checkpoints/              # Pesos entrenados (gitignored)
│       ├── sae_modelo_final/     # SAE + CLIP checkpoints
│       │   ├── sae_best.pt       # SAE entrenado (512→2048→512)
│       │   ├── clip_modelo/      # CLIP text encoder fine-tuneado
│       │   └── embeddings/       # Embeddings extraídos
│       └── sit3_convlstm_weights/ # Conv3DSit3 entrenado
│           └── best.ckpt         # Checkpoint PyTorch Lightning
│
├── app/                          # Next.js App Router
│   ├── globals.css               # Estilos globales + dark/light mode
│   ├── layout.tsx                # Layout raíz
│   ├── page.tsx                  # Página principal
│   └── api/                      # API Routes (fallback standalone)
│
├── components/                   # Componentes React
│   ├── Map/                      # Leaflet: CaliMap, GradientOverlay, etc.
│   ├── Controls/                 # HorizonSlider
│   ├── Dashboard/                # KPICards, PredictionPanel, GridMaps
│   ├── Sidebar/                  # Sidebar + ValidationTable
│   ├── Layout/                   # Navbar
│   ├── Sections/                 # HeroSection, MapSection, AnalyticsSection
│   └── ui/                       # shadcn/ui primitives
│
├── hooks/                        # usePrediction, useStations, useValidation
├── store/                        # Zustand (theme, contaminant, horizon, point)
├── lib/                          # mockData.ts, constants.ts, utils.ts
├── public/                       # GeoJSON, manifest
├── package.json
├── next.config.mjs               # Rewrites → FastAPI en desarrollo
└── tsconfig.json
```

---

## Pipeline de inferencia (modo producción)

Cuando el usuario hace clic en un punto del mapa, el backend ejecuta:

```
Tile Sentinel-2 (13, 64, 64)
       │
       ▼
MS Adapter Conv2d(13→12)    ← Adapta 13 bandas a 12 canales
       │
       ▼
RemoteCLIP ViT-B/32 visual   ← Pre-entrenado (94.9M params)
       │                        Cargado desde chendelong/RemoteCLIP
       ▼
Embedding visual 512-d
       │
       ▼
+ 19 covariables (ERA5 + MODIS)  ← Placebo en desarrollo, real en prod
       │
       ▼
Vector 531-d
       │
       ▼
Conv3DSit3                     ← Checkpoint entrenado (295K params)
  Bottleneck Conv3d(531→32)       MaxPool → Conv3d(64→128) → MaxPool
  Conv3d(32→64) + BN + ReLU       AdaptiveAvgPool3d → Dropout
       │
       ▼
3 cabezas lineales (NO₂, SO₂, O₃)
  Cada cabeza → 3 horizontes (T+1, T+3, T+7)
       │
       ▼
Predicción (3, 3) + grilla espacial + varianza σ²
```

### KPIs del modelo (consigna)

| KPI | Mínimo | Excelente |
|-----|--------|-----------|
| Recall@1 imagen→texto | ≥ 0.45 | ≥ 0.65 |
| Recall@5 imagen→texto | ≥ 0.70 | ≥ 0.85 |
| Sparsity SAE visual | ≥ 0.70 | ≥ 0.85 |
| Loss reconstrucción SAE | ≤ 0.05 | ≤ 0.02 |
| RMSE LOO-CV NO₂ (T+1) | ≤ 8 µg/m³ | ≤ 4 µg/m³ |
| RMSE LOO-CV SO₂ (T+1) | ≤ 6 µg/m³ | ≤ 3 µg/m³ |
| RMSE LOO-CV O₃ (T+1) | ≤ 12 µg/m³ | ≤ 6 µg/m³ |
| R² LOO-CV (promedio) | ≥ 0.55 | ≥ 0.75 |
| Moran I (predicciones) | > 0.30 (p<0.05) | > 0.50 |

---

## API Backend — Contratos

### POST /api/predict

```json
// Request
{ "lat": 3.4516, "lon": -76.5320, "radius_km": 5,
  "contaminant": "NO2", "horizon": "T+1" }

// Response
{ "predicted_value": 22.4, "uncertainty_sigma": 3.1,
  "unit": "µg/m³",
  "grid": { "lats": [[...]], "lons": [[...]],
            "values": [[...]], "variances": [[...]] },
  "all_horizons": { "T+1": {"NO2": 22.4, "SO2": 15.2, "O3": 85.1}, ... },
  "timestamp": "2026-05-26T...",
  "model_version": "geovision-clip-v1.0-prod",
  "md5_checkpoint": "remoteclip+sae_best+conv3d_best" }
```

### GET /api/stations

```json
{ "stations": [{ "id": 1, "name": "Estación Pance",
    "lat": 3.3333, "lon": -76.5431, "zone": "Sur",
    "last_reading": { "NO2": 42.3, "SO2": 15.1, "O3": 85.4 },
    "timestamp": "2026-05-26T..." }, ...] }
```

### GET /api/validate

```json
{ "loo_cv": { "NO2": {"RMSE": 5.2, "MAE": 3.8, "R2": 0.71}, ... },
  "moran_i": { "I": 0.41, "p_value": 0.002 },
  "kpis": { "recall_at_1": 0.52, "recall_at_5": 0.79,
            "sparsity_sae": 0.78, "loss_sae_recon": 0.031 } }
```

### GET /api/download/{format}?lat=...&lon=...&contaminant=...

Formatos: `csv` (descarga .csv) o `geotiff` (placeholder, requiere GDAL).

---

## Scripts disponibles

### Frontend

| Comando | Qué hace |
|---------|----------|
| `pnpm dev` | Servidor de desarrollo con hot-reload |
| `pnpm build` | Genera build de producción en `.next/` |
| `pnpm start` | Corre el build de producción |
| `pnpm lint` | Ejecuta ESLint |

### Backend

| Comando | Qué hace |
|---------|----------|
| `uvicorn backend.main:app --reload --port 8000` | Servidor dev (mock) |
| `$env:MODE='prod'; uvicorn backend.main:app --port 8000` | Servidor prod (modelos) |

---

## Flujo de datos frontend

```
Usuario hace click en el mapa
        ↓
CaliMapInner → onPointClick(lat, lon)
        ↓
MapSection → setPoint(lat, lon) en Zustand
        ↓
usePrediction hook → fetch POST /api/predict
        ↓
Backend (dev: mock / prod: modelos reales)
        ↓
┌────────────────────────────────────┐
│ GradientOverlay ← grid data        │ (overlay de calor en mapa)
│ PredictionPanel ← valor ± σ        │ (panel lateral derecho)
│ GridMaps ← all_horizons            │ (9 mini-mapas 3×3)
│ TimeSeriesChart ← historial        │ (gráfico 8 fechas)
└────────────────────────────────────┘
```

---

## Problemas comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `window is not defined` | Leaflet en SSR | Ya resuelto con `dynamic(ssr:false)` |
| `No module named 'backend'` | PYTHONPATH no configurado | Correr desde `app/geo-vision-clip-application/` |
| Modelos no cargan en prod | Checkpoints faltantes | Verificar `backend/checkpoints/` |
| `open_clip` no instalado | Falta dependencia | `pip install open-clip-torch` |
| Puerto 3000 en uso | Otro proceso | `pnpm dev -- --port 3001` |

---

*GeoVision-CLIP Cali · Analítica de Datos I · 2026*
