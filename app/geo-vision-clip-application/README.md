# 🌍 GeoVision-CLIP Cali — Frontend App

Aplicación web profesional en **Next.js 16 + Tailwind v4 + Leaflet** para visualizar predicciones de contaminantes atmosféricos (NO₂, SO₂, O₃) sobre Santiago de Cali.

---

## 🚀 Cómo correr en local

### Prerrequisitos

| Herramienta | Versión mínima | Verificar |
|-------------|---------------|-----------|
| Node.js | ≥ 18 | `node -v` |
| pnpm | cualquiera | `pnpm -v` |

> **¿No tienes pnpm?** Instálalo con: `npm install -g pnpm`

### Pasos

```bash
# 1. Entrar a la carpeta del frontend
cd app/geo-vision-clip-application

# 2. Instalar dependencias (usa pnpm, NO npm, porque hay pnpm-lock.yaml)
pnpm install

# 3. Levantar servidor de desarrollo
pnpm dev
```

La app queda disponible en: **http://localhost:3000**

### Scripts disponibles

| Comando | Qué hace |
|---------|----------|
| `pnpm dev` | Servidor de desarrollo con hot-reload |
| `pnpm build` | Genera build de producción en `.next/` |
| `pnpm start` | Corre el build de producción (requiere `pnpm build` antes) |
| `pnpm lint` | Ejecuta ESLint sobre todo el código |

### Variables de entorno (opcional)

Crea un archivo `.env.local` en esta carpeta si necesitas apuntar a un backend real:

```env
# URL del backend FastAPI (por defecto las rutas API son internas de Next.js)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🗂️ Estructura completa del proyecto

```
geo-vision-clip-application/
│
├── app/                         # Next.js App Router
│   ├── globals.css              # Estilos globales + variables CSS dark/light
│   ├── layout.tsx               # Layout raíz: fuentes, providers, metadata
│   ├── page.tsx                 # Página principal (/) — ensambla secciones
│   └── api/                    # API Routes internas de Next.js (mock backend)
│       ├── predict/             # POST /api/predict
│       ├── stations/            # GET /api/stations
│       ├── validate/            # GET /api/validate
│       └── download/            # GET /api/download
│
├── components/                  # Todos los componentes React
│   ├── Map/                     # Componentes del mapa Leaflet
│   ├── Controls/                # Controles de usuario (slider, selects)
│   ├── Dashboard/               # Paneles de datos y visualizaciones
│   ├── Sidebar/                 # Barra lateral + tabla de validación
│   ├── Layout/                  # Navbar
│   ├── Sections/                # Secciones de página completa
│   ├── ui/                      # shadcn/ui — componentes primitivos
│   ├── Providers.tsx            # QueryClient + ThemeProvider
│   └── theme-provider.tsx       # next-themes wrapper
│
├── hooks/                       # Custom hooks de React
├── store/                       # Estado global (Zustand)
├── lib/                         # Utilidades
├── styles/                      # Estilos adicionales
├── public/                      # Assets estáticos
├── package.json
├── tsconfig.json
├── next.config.mjs
└── components.json              # Config de shadcn/ui
```

---

## 🔬 Análisis de Componentes

### 📦 `app/` — Páginas y API Routes

#### `app/layout.tsx`
**Qué hace:** Layout raíz de Next.js. Envuelve toda la app con los `Providers` (React Query + tema dark/light), define las fuentes tipográficas (Inter + JetBrains Mono via Google Fonts) y la metadata de SEO del proyecto.

#### `app/page.tsx`
**Qué hace:** Página principal (`/`). Ensambla las tres secciones grandes en orden vertical:
1. `HeroSection` — encabezado
2. `MapSection` — mapa + controles
3. `AnalyticsSection` — métricas y validación

#### `app/globals.css`
**Qué hace:** Define las variables CSS para dark/light mode (colores Slate + Emerald), estilos base del mapa Leaflet, y utilidades globales. Es el sistema de diseño central.

#### `app/api/predict/`
**Qué hace:** API Route de Next.js que simula `POST /api/predict`. Recibe `{lat, lon, contaminant, horizon, radius_km}` y devuelve datos mock de predicción con grilla, valor predicho y varianza σ². Permite trabajar sin backend FastAPI levantado.

#### `app/api/stations/`
**Qué hace:** `GET /api/stations` — Devuelve las 9 estaciones DAGMA hardcodeadas con coordenadas reales de Cali y lecturas de contaminantes simuladas.

#### `app/api/validate/`
**Qué hace:** `GET /api/validate` — Devuelve los KPIs del modelo (Recall@1, Recall@5, Sparsity SAE) y métricas de validación LOO-CV por estación.

#### `app/api/download/`
**Qué hace:** `GET /api/download` — Endpoint para descargar las predicciones en formato CSV o GeoTIFF.

---

### 🗺️ `components/Map/` — El corazón visual

#### `CaliMap.tsx`
**Qué hace:** Componente de entrada del mapa. Como Leaflet necesita el navegador (no funciona en SSR de Next.js), este componente usa `dynamic import` con `ssr: false` para cargar `CaliMapInner` solo en el cliente. Es el "wrapper" del mapa.

**Por qué existe separado:** Next.js renderiza en servidor por defecto. Leaflet usa `window` y `document`, que no existen en el servidor. El patrón `dynamic(() => import('./CaliMapInner'), { ssr: false })` resuelve esto.

#### `CaliMapInner.tsx`
**Qué hace:** El mapa real de Leaflet. Contiene:
- `MapContainer` centrado en Cali (lat=3.4516, lon=-76.5320, zoom=12)
- `TileLayer` con CartoDB Dark Matter / CartoDB Positron según el tema
- Captura clicks del mapa → llama `onPointClick(lat, lon)` → dispara predicción
- Renderiza `DagmaMarkers`, `GradientOverlay`, `AqiLegend`

**Integración:** Recibe props desde `MapSection` con los datos del overlay y el handler de click.

#### `DagmaMarkers.tsx`
**Qué hace:** Renderiza las 9 estaciones DAGMA como marcadores `CircleMarker` en el mapa. Cada marcador tiene un `Popup` con el nombre de la estación y sus últimas lecturas de NO₂, SO₂, O₃. Color: `emerald-500` (`#10b981`).

#### `GradientOverlay.tsx`
**Qué hace:** Recibe la grilla de predicciones `{lats, lons, values, variances}` y pinta un overlay de calor sobre el mapa usando la escala AQI de 5 colores (emerald → amber → orange → rose → purple). La opacidad de cada celda es inversamente proporcional a la varianza σ² (más incertidumbre = más transparente).

**Algoritmo:** Usa `L.Rectangle` de Leaflet para cada celda de la grilla con `fillColor = getColorForValue(value, min, max)` y `fillOpacity = 1 / (1 + sigma)`.

#### `AqiLegend.tsx`
**Qué hace:** Leyenda fija en la esquina inferior derecha del mapa con los 5 colores AQI y sus etiquetas (Bueno / Moderado / Dañino / Peligroso / Emergencia). Siempre visible.

#### `MiniMap.tsx` + `MiniMapInner.tsx`
**Qué hace:** Versión miniatura del mapa para la grilla 3×3. Mismo patrón `dynamic` + SSR-safe que `CaliMap`. El inner tiene `zoomControl={false}`, `dragging={false}`, `scrollWheelZoom={false}` para mapas no interactivos. Incluye la etiqueta flotante `absolute top-2 left-2` con el contaminante y horizonte.

---

### 🎛️ `components/Controls/`

#### `HorizonSlider.tsx`
**Qué hace:** Slider temporal estilo reproductor de video con botones Play/Pause usando `lucide-react`. Tres posiciones: T+1 / T+3 / T+7. Al cambiar actualiza el store de Zustand. Pills con `bg-emerald-500` para la posición activa. El botón Play anima automáticamente entre los 3 horizontes con un intervalo de 1.5s.

---

### 📊 `components/Dashboard/`

#### `KPICards.tsx`
**Qué hace:** Cuatro tarjetas con los KPIs del modelo obtenidos de `/api/validate`:
- Recall@1 imagen→texto (umbral ≥ 0.45)
- Recall@5 imagen→texto (umbral ≥ 0.70)
- Sparsity ratio SAE visual (umbral ≥ 0.70)
- Índice de Moran I (umbral > 0.30)
Cada tarjeta muestra un semáforo verde/amarillo/rojo según si supera el umbral de la consigna.

#### `PredictionPanel.tsx`
**Qué hace:** Panel lateral derecho. Muestra el resultado de la predicción para el punto clickeado en el mapa:
- Valor predicho en `font-mono` grande (ej: `44.6 µg/m³`)
- Incertidumbre `± σ` 
- Clasificación AQI con color semántico
- Los 9 valores (3 contaminantes × 3 horizontes) en una tabla compacta
- Spinner `Loader2` de lucide-react mientras carga la predicción

#### `TimeSeriesChart.tsx`
**Qué hace:** Gráfico de línea con Recharts mostrando el histórico de las últimas 8 fechas del contaminante seleccionado para el punto clickeado. Usa los colores AQI del sistema de diseño. Tooltip con valores en `font-mono`.

#### `GridMaps.tsx`
**Qué hace:** Grilla 3 columnas × 3 filas con `MiniMap` para cada combinación (NO₂/SO₂/O₃) × (T+1/T+3/T+7). Usa `grid grid-cols-3 gap-2`. Cada mini-mapa recibe los datos del horizonte/contaminante correspondiente del store.

#### `DownloadButtons.tsx`
**Qué hace:** Dos botones (GeoTIFF y CSV) que llaman a `/api/download?format=geotiff|csv` y descargan el archivo. Usa `anchor` con `download` attribute. Solo habilitados si hay un punto seleccionado.

---

### 📋 `components/Sidebar/`

#### `Sidebar.tsx`
**Qué hace:** Barra lateral izquierda con:
- Lista de las 9 estaciones DAGMA con su estado actual (lectura más reciente)
- Selector de contaminante (NO₂ / SO₂ / O₃) vía `@radix-ui/react-select`
- Control de radio (1-15 km) vía `@radix-ui/react-slider`
- Efecto glassmorphism (`bg-slate-900/80 backdrop-blur-md`)

#### `ValidationTable.tsx`
**Qué hace:** Tabla con los resultados LOO-CV por estación DAGMA (RMSE, MAE, R²) para el contaminante seleccionado. Datos obtenidos de `/api/validate`. Filas con colores condicionales: verde si RMSE < umbral "Excelente", amarillo si < "Mínimo", rojo si supera el mínimo.

---

### 🏗️ `components/Layout/`

#### `Navbar.tsx`
**Qué hace:** Barra de navegación superior con:
- Logo + nombre "GeoVision-CLIP Cali"
- Selector rápido de contaminante (pills NO₂/SO₂/O₃)
- Botón de toggle Dark/Light mode con íconos `Moon`/`Sun` de lucide-react
- Sticky en el top con `backdrop-blur`

---

### 📄 `components/Sections/`

#### `HeroSection.tsx`
**Qué hace:** Sección de presentación al tope de la página. Título del proyecto, descripción del problema (calidad del aire en Cali), badges con las tecnologías usadas (CLIP, SAE, Kriging, DAGMA) y un CTA de scroll hacia el mapa. Incluye animaciones de entrada con `useScrollReveal`.

#### `MapSection.tsx`
**Qué hace:** Sección principal que contiene el layout de 3 columnas:
- Izquierda: `Sidebar`
- Centro: `CaliMap` + `HorizonSlider` debajo
- Derecha: `PredictionPanel`
Orquesta el flujo: click en mapa → `usePrediction` → actualiza estado → pasa datos a `GradientOverlay` y `PredictionPanel`.

#### `AnalyticsSection.tsx`
**Qué hace:** Sección inferior con:
- `KPICards` con métricas del modelo
- `GridMaps` 3×3
- `ValidationTable`
- `DownloadButtons`
- `TimeSeriesChart`

---

### 🪝 `hooks/`

| Hook | Qué hace |
|------|----------|
| `usePrediction.ts` | React Query: `POST /api/predict` cuando cambia lat/lon/contaminante/horizonte |
| `useStations.ts` | React Query: `GET /api/stations` al montar la app (cache 5min) |
| `useValidation.ts` | React Query: `GET /api/validate` para KPIs y LOO-CV |
| `use-mobile.ts` | Detecta si el viewport es mobile (< 768px) para layout responsive |
| `use-toast.ts` | Sistema de notificaciones toast (de shadcn/ui) |
| `useScrollReveal.ts` | Intersection Observer para animaciones de entrada al hacer scroll |

---

### 🗄️ `store/appStore.ts`

Estado global con **Zustand**:

```typescript
{
  theme: 'dark' | 'light'          // Tema visual
  contaminant: 'NO2' | 'SO2' | 'O3' // Contaminante activo
  horizon: 'T+1' | 'T+3' | 'T+7'   // Horizonte temporal
  radiusKm: number                  // Radio de búsqueda (1-15)
  selectedPoint: { lat, lon } | null // Punto clickeado en el mapa

  // Acciones:
  toggleTheme()
  setContaminant(c)
  setHorizon(h)
  setRadius(r)
  setPoint(lat, lon)
}
```

---

### 🧩 `components/Providers.tsx`

**Qué hace:** Componente que envuelve toda la app con:
1. `QueryClientProvider` de React Query (cache de 5min, 3 retries)
2. `ThemeProvider` de `next-themes` (persiste el tema en `localStorage`)

Separado del layout para poder usar hooks de cliente sin marcar todo el layout como `"use client"`.

---

### 🎨 `components/ui/`

Componentes primitivos de **shadcn/ui** (Button, Select, Slider, Card, Badge, Tooltip, etc.). Son componentes accesibles basados en Radix UI + Tailwind. No los modifiques directamente — están auto-generados.

---

## 🔌 Flujo de Datos

```
Usuario hace click en el mapa
        ↓
CaliMapInner → onPointClick(lat, lon)
        ↓
MapSection → setPoint(lat, lon) en Zustand
        ↓
usePrediction hook detecta cambio → POST /api/predict
        ↓
API Route /api/predict → responde { predicted_value, grid, all_horizons, ... }
        ↓
┌────────────────────────────────────┐
│ GradientOverlay ← grid data        │ (actualiza overlay del mapa)
│ PredictionPanel ← valor ± σ        │ (muestra resultado lateral)
│ GridMaps ← all_horizons            │ (actualiza 9 mini-mapas)
│ TimeSeriesChart ← historial        │ (actualiza gráfico)
└────────────────────────────────────┘
```

---

## ⚠️ Problemas comunes al correr en local

| Error | Causa | Solución |
|-------|-------|----------|
| `window is not defined` | Leaflet en SSR | Ya está resuelto con `dynamic(..., {ssr: false})` en `CaliMap.tsx` y `MiniMap.tsx` |
| `Cannot find module 'leaflet'` | Dependencias no instaladas | Correr `pnpm install` |
| Puerto 3000 en uso | Otro proceso en el puerto | Cambiar con `pnpm dev -- --port 3001` |
| Mapa no carga (pantalla blanca) | CSS de Leaflet no importado | Verificar que `globals.css` importa `leaflet/dist/leaflet.css` |
| `pnpm: command not found` | pnpm no instalado | `npm install -g pnpm` |

---

*GeoVision-CLIP Cali · Analítica de Datos I · 2026*
