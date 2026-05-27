# GeoVision-CLIP Cali

**Estimación de Contaminación Atmosférica en Puntos No Muestreados mediante Deep Learning + Estadística Geoespacial Avanzada**

> Proyecto Final — Analítica de Datos I · Tercer Corte · Universidad Autónoma de Occidente  
> Grupo: 3 integrantes · Duración: 4 semanas

---

## Resumen ejecutivo

Santiago de Cali (564 km²) dispone de solo 9 estaciones DAGMA para monitorear la calidad del aire, insuficientes para representar la heterogeneidad intraurbana de NO₂, SO₂ y O₃ troposférico. Este proyecto implementa una arquitectura híbrida que integra:

1. **GeoVision-CLIP + SAE** — modelo multimodal contrastivo (ViT-B/32 RemoteCLIP + MiniLM multilingüe + Sparse Autoencoders) sobre tiles Sentinel-2 y descripciones textuales en español.
2. **ConvLSTM espacio-temporal** — pronóstico a T+1, T+3 y T+7 días sobre secuencias de embeddings reorganizados en grilla.
3. **ST-Kriging (Kriging Espacio-Temporal)** — interpolación geoestadística 3D con cuantificación de incertidumbre (varianza σ²) sobre las predicciones del modelo profundo.

El pipeline ingiere ≥ 50 GB de datos satelitales (Sentinel-5P, Sentinel-2, ERA5-Land, MODIS MCD19A2) en formato Zarr sobre Google Cloud Storage, entrena el modelo contrastivo y valida las superficies predichas contra las estaciones DAGMA mediante leave-one-out cross-validation espacial.

---

## Tabla de contenidos

- [Estructura del repositorio](#estructura-del-repositorio)
- [Arquitectura del sistema](#arquitectura-del-sistema)
- [Situación 1 — Panel Espacio-Temporal](#situación-1--panel-espacio-temporal-y-arquitectura-cloud)
- [Situación 2 — GeoVision-CLIP + SAE](#situación-2--geovision-clip--aprendizaje-multimodal)
- [Situación 3 — Predicción Geoestadística](#situación-3--predicción-geoestadística-espacio-temporal)
- [Frontend y despliegue](#frontend-y-despliegue)
- [Instalación y reproducibilidad](#instalación-y-reproducibilidad)
- [KPIs y métricas](#kpis-y-métricas)
- [API — Contrato JSON](#api--contrato-json-predict)
- [Entregables](#entregables)
- [Referencias técnicas](#referencias-técnicas)

---

## Estructura del repositorio

```text
GeoVision-CLIP-Cali/
├── pipeline/                          # Núcleo ETL + generación de datasets
│   ├── config.py                      # Constantes: GCP, GEE, bucket, BBox, fuentes
│   ├── exportar.py                    # Descarga distribuida Dask → GCS con MD5
│   ├── convertir_zarr.py              # GeoTIFF → paneles Zarr (chunking ST)
│   ├── validar_zarr.py                # Validación de integridad paneles Zarr
│   ├── manifest.py                    # Consolidador manifest global JSON
│   ├── generar_dataset_sit2_par_imagen_texto.py  # Dataset pares img-texto
│   ├── silenciar_warnings.py          # Supresión warnings ruidosos
│   └── trazabilidad/                  # Runs + eventos JSONL + Dask plugin
│       ├── __init__.py
│       ├── sistema.py
│       └── dask_plugin.py
│
├── src/                               # Librería Python importable
│   ├── __init__.py
│   ├── modelos/                       # Arquitectura de modelos
│   │   ├── geovision_clip_sae.py      # GeoVisionClipSAEModel (ViT+SAE+proj)
│   │   ├── sae.py                     # SparseAutoencoder + sae_loss
│   │   └── clip_metrics.py            # Recall@k, sparsity_ratio, MSE
│   ├── training/                      # LightningModule entrenamiento
│   │   └── lit_geovision.py           # LitGeoVisionClipSAE
│   ├── datasets/                      # Datasets PyTorch
│   │   └── sit2_tile.py               # Sit2TileDataset (Zarr + Parquet)
│   ├── utils/                         # Utilidades
│   │   ├── embeddings_export.py       # Exportar embeddings a Parquet
│   │   ├── psychometrics_embeddings.py  # AFE/PCA varianza acumulada
│   │   └── run_artifacts.py           # Checkpoint MD5 + subida GCS
│   ├── geo/                           # Kriging + Moran (Sit. 3)
│   └── etl/                           # Helpers ETL adicionales
│
├── notebooks/                         # Notebooks Jupyter ejecutables
│   ├── Situacion_1/                   # EDA + extracción satelital
│   │   ├── DAGMA/                     # Ground truth: EDA NO₂, SO₂, O₃
│   │   ├── EDAs/                      # EDA Sentinel-2, S5P, ERA5, MODIS
│   │   ├── Satelites/                 # Extracción GEE (S5P, S2)
│   │   └── Prototipo_ETL_R2.ipynb     # Prototipo ETL → Cloudflare R2
│   ├── sit2_geovision_clip.ipynb      # Entrenamiento CLIP+SAE completo
│   ├── entrenar_sit2_samuel.ipynb     # Variante entrenamiento
│   ├── eda_mc_barrios_cali.ipynb      # EDA shapefile barrios Cali
│   ├── DATASET_SIT2_PIPELINE.md       # Documentación del pipeline
│   └── INFORME_DIAGNOSTICO_SIT2.md    # Diagnóstico KPIs Sit. 2
│
├── app/                               # Frontend Next.js
│   └── geo-vision-clip-application/   # React + Next.js + Leaflet
│       ├── app/                        # App Router
│       ├── components/                 # Componentes UI
│       ├── hooks/                      # Custom hooks
│       ├── store/                      # Estado global
│       ├── public/                     # Assets estáticos
│       ├── package.json
│       └── next.config.mjs
│
├── data/                              # Datos locales (gitignored)
│   ├── DagmaDATA/                     # Ground truth DAGMA 2019-2023
│   │   ├── NO2DAGMASISNO2/            # 5 CSV horarios NO₂
│   │   ├── O3DAGMA/                   # 5 CSV horarios O₃
│   │   └── SO2DAGMA/                  # 5 CSV horarios SO₂
│   ├── dataset_sit2/                  # Output pipeline Sit. 2
│   │   ├── tiles.zarr/                # (2276, 13, 64, 64) int16
│   │   ├── metadatos.parquet          # Metadata por tile
│   │   ├── percentiles.json           # Umbrales S5P (p25-p99)
│   │   ├── secuencias.json            # 30 secuencias × 8 fechas
│   │   └── resumen.json               # Balance de clases y stats
│   └── mc_barrios/                    # Shapefile barrios Cali
│
├── docs/                              # Documentación y referencias
│   ├── papersglobales/                # Consigna + contrapropuesta
│   ├── papersSit2/                    # Resúmenes de papers Sit. 2-3
│   ├── Papers/                        # PDFs de referencia (7 papers)
│   ├── informe/                       # Template LaTeX informe final
│   └── PAPERS_GUIA_PROYECTO.md        # Guía papers → tareas
│
├── scripts/                           # Utilidades y patches one-shot
│   ├── patch_sit2_diagnostico_eda.py
│   ├── patch_sit2_phased_training.py
│   ├── restore_mono_training.py
│   └── nb_cells/                      # Celdas extraídas de notebooks
│
├── runs/                              # Trazabilidad (gitignored)
│   └── <timestamp>_<nombre>/          # log.txt + eventos.jsonl
│
├── Dockerfile                         # Imagen Python 3.11-slim
├── requirements.txt                   # Dependencias pinned
├── .gitignore
└── README.md
```

---

## Arquitectura del sistema

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ALMACENAMIENTO CLOUD                            │
│                    gs://geovision-cali (GCS)                            │
│                                                                         │
│  Sentinel5P/NO2/panel.zarr   Sentinel2/panel.zarr   ERA-5/panel.zarr   │
│  Sentinel5P/SO2/panel.zarr   MODIS_MCD/panel.zarr                      │
│  Sentinel5P/O3/panel.zarr                                               │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  exportar.py    │ │ convertir_zarr  │ │ manifest.py     │
│  Dask Distrib.  │ │ ThreadPool +    │ │ Consolidación   │
│  GEE → GeoTIFF  │ │ xarray → Zarr   │ │ MD5 global      │
│  + MD5 inline   │ │ region writes   │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
          │                                       │
          ▼                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│               generar_dataset_sit2_par_imagen_texto.py                   │
│                                                                         │
│  • Percentiles globales S5P (p25/p50/p75/p90/p99)                      │
│  • Tiles S2 64×64 con filtro SCL (nubes/sombras)                       │
│  • NDVI + BSI por tile (píxeles claros)                                │
│  • Asignación semi-supervisada: 5 clases × percentiles S5P            │
│  • Descripción en español por tile                                     │
│  • Split 70/15/15 estratificado (SEED=42)                              │
│  • 30 secuencias × 8 fechas para ConvLSTM                             │
│  → tiles.zarr + metadatos.parquet + percentiles.json                   │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    GeoVision-CLIP + SAE (Sit. 2)                        │
│                                                                         │
│  ┌──────────────┐    ┌───────────────┐    ┌──────────────────┐         │
│  │ Conv2d 13→3  │    │  ViT-B/32     │    │  SAE (512-d)     │         │
│  │ MS Adapter   │───▶│  RemoteCLIP   │───▶│  L2+λ·L1         │──▶ 256-d│
│  └──────────────┘    │  (frozen/ft)  │    └──────────────────┘         │
│                      └───────────────┘                                  │
│  ┌──────────────┐    ┌───────────────┐    ┌──────────────────┐         │
│  │ Tokenizer    │    │ MiniLM-L12    │    │  SAE (512-d)     │         │
│  │ multilingüe  │───▶│ multilingüe   │───▶│  L2+λ·L1         │──▶ 256-d│
│  └──────────────┘    └───────────────┘    └──────────────────┘         │
│                                                                         │
│  Loss = InfoNCE(τ) + α·(SAE_img + SAE_txt)                            │
│  τ = learnable (init 0.07) | α = 0.1 | λ = 1e-3                       │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ embeddings (N×N × 8 × 256)
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                ConvLSTM + ST-Kriging (Sit. 3)                           │
│                                                                         │
│  ┌─────────────────────┐    ┌────────────────────────┐                 │
│  │ ConvLSTM Bidirec.   │    │ OrdinaryKriging3D      │                 │
│  │ hidden=128, k=3     │───▶│ Variograma exponencial │──▶ Superficie   │
│  │ 2 capas, AdamW      │    │ (lat, lon, t)          │    continua +   │
│  │ → (B,3,3,H,W)      │    │                        │    σ²(s,t)      │
│  └─────────────────────┘    └────────────────────────┘                 │
│                                                                         │
│  Validación: LOO-CV 9 estaciones DAGMA                                 │
│  Coherencia: Moran I > 0.30 (p<0.05) + LISA clusters                  │
│  Residuos: variograma nugget puro (sin estructura)                     │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              Frontend (Next.js + Leaflet) + Backend (FastAPI)            │
│                                                                         │
│  • Mapa interactivo centrado en Cali con 9 estaciones DAGMA            │
│  • Click en cualquier punto → predicción                                │
│  • 9 mapas de gradiente (3 contaminantes × 3 horizontes)               │
│  • Capa de incertidumbre (opacidad ∝ 1/σ)                             │
│  • Tooltips: valor ± σ | Descarga GeoTIFF/CSV                         │
│  • Latencia end-to-end < 8 s                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Situación 1 — Panel Espacio-Temporal y Arquitectura Cloud

### Objetivo

Construir un panel analítico longitudinal de **≥ 50 GB** con 5 años (2019–2023) de datos satelitales sobre el área metropolitana de Cali, almacenado en formato Zarr sobre GCS.

** LOGRADO:** 66.78 GB (283,437 archivos) — umbral cumplido al 133.5%

### Fuentes de datos integradas

| Fuente | Colección GEE | Bandas | Escala nativa | Prefijo GCS |
|--------|---------------|--------|---------------|-------------|
| Sentinel-5P NO₂ | `COPERNICUS/S5P/OFFL/L3_NO2` | `tropospheric_NO2_column_number_density`, `NO2_column_number_density`, `cloud_fraction` | 1113 m | `Sentinel5P/NO2/` |
| Sentinel-5P SO₂ | `COPERNICUS/S5P/OFFL/L3_SO2` | `SO2_column_number_density`, `cloud_fraction` | 1113 m | `Sentinel5P/SO2/` |
| Sentinel-5P O₃ | `COPERNICUS/S5P/OFFL/L3_O3` | `O3_column_number_density`, `cloud_fraction` | 1113 m | `Sentinel5P/O3/` |
| Sentinel-2 L2A | `COPERNICUS/S2_SR_HARMONIZED` | B1–B12 + SCL (13 bandas) | 10 m | `Sentinel2/` |
| ERA5-Land | `ECMWF/ERA5/HOURLY` | T2m, dewpoint, u/v wind, BLH, pressure, precipitation | 27830 m | `ERA-5/` |
| MODIS MCD19A2 | `MODIS/061/MCD19A2_GRANULES` | AOD 047/055, Column WV, QA | 927 m | `MODIS_MCD/` |
| DAGMA (ground truth) | CSV locales | NO₂, SO₂, O₃ horarios × 9 estaciones | puntual | `data/DagmaDATA/` |

### BBox operativa

```python
BBOX = [-76.65, 3.30, -76.30, 3.65]  # [lon_min, lat_min, lon_max, lat_max]
```

Ampliada respecto a la consigna (−76.60, 3.30, −76.40, 3.55) para incluir el corredor industrial Yumbo–Acopi y zona de cultivos de caña.

### Pipeline ETL — Módulos

| Módulo | Responsabilidad | CLI |
|--------|-----------------|-----|
| `pipeline/config.py` | Constantes centrales: GCP project (`proyecto3ia-494900`), bucket (`geovision-cali`), BBox, catálogo de 6 fuentes con bandas/escalas, config Dask (4 workers × 2 threads × 4 GB) | — |
| `pipeline/exportar.py` | Descarga distribuida via **Dask Distributed**. Lista imágenes en GEE, construye tareas (1 por banda/fecha/tile), descarga con retry exponencial (6 intentos, backoff 2–60s con jitter), calcula MD5 inline, sube a GCS, genera `manifest_partial.json` por fuente | `--todas`, `--fuente`, `--max-imagenes`, `--dry-run`, `--anio`, `--inicio/--fin` |
| `pipeline/convertir_zarr.py` | Convierte GeoTIFF crudos → paneles Zarr con chunking espacio-temporal. Esqueleto lazy con xarray + dask.array, escritura por regiones con ThreadPoolExecutor (nunca dos hilos tocan el mismo chunk). Consolida metadatos Zarr al final | `--todas`, `--fuente`, `--workers`, `--max-imagenes` |
| `pipeline/validar_zarr.py` | Valida integridad: presencia, shape `(time, band, y, x)`, bandas vs config, rango temporal, chunks, dtype, %NaN muestreado | `--fuente`, `--json` |
| `pipeline/manifest.py` | Descarga `manifest_partial.json` de cada fuente en GCS → consolida en `manifest.json` global con: timestamp UTC, bucket, BBox, fecha inicio/fin, n_archivos, size_bytes_total, lista completa con MD5 | `--subir-a-gcs` |
| `pipeline/trazabilidad/` | `Run` context manager: crea `runs/<timestamp>_<nombre>/` con `log.txt` + `eventos.jsonl`. Usa `contextvars` para thread-safety. Plugin Dask para propagar logs a workers | — |
| `pipeline/silenciar_warnings.py` | Suprime: `_CLOUD_SDK_CREDENTIALS_WARNING`, `FutureWarning` google.api_core, `DeprecationWarning` pkg_resources, warnings CE de GDAL/libtiff. Se importa antes que cualquier SDK | — |

### Ejecución paso a paso

```powershell
# 1. Autenticación GEE + GCP
gcloud auth application-default login
python -c "import ee; ee.Initialize(project='proyecto3ia-494900')"

# 2. Descarga distribuida (todas las fuentes, 5 años)
python pipeline/exportar.py --todas

# 3. Conversión GeoTIFF → Zarr
python pipeline/convertir_zarr.py --todas

# 4. Consolidar manifest global con MD5
python pipeline/manifest.py --subir-a-gcs

# 5. Validar integridad de los paneles
python pipeline/validar_zarr.py
```

### Manifest logrado (2026-05-12)

```json
{
  "version": "1.0",
  "generado_utc": "2026-05-12T04:25:40.049649+00:00",
  "bucket": "geovision-cali",
  "project_gcp": "proyecto3ia-494900",
  "n_archivos": 283437,
  "size_gb_total": 66.7761,
  "umbral_minimo_gb": 50,
  "umbral_cumplido": true,
  "por_fuente": {
    "COPERNICUS/S5P/OFFL/L3_NO2":  { "n_archivos": 28303,  "size_mb": 77.5 },
    "COPERNICUS/S5P/OFFL/L3_SO2":  { "n_archivos": 26280,  "size_mb": 31.8 },
    "COPERNICUS/S5P/OFFL/L3_O3":   { "n_archivos": 25798,  "size_mb": 55.2 },
    "COPERNICUS/S2_SR_HARMONIZED": { "n_archivos": 19121,  "size_gb": 66.4 },
    "ECMWF/ERA5/HOURLY":           { "n_archivos": 43815,  "size_mb": 98.9 },
    "MODIS/061/MCD19A2_GRANULES":  { "n_archivos": 140120, "size_mb": 109.8 }
  }
}
```

**Análisis del volumen:**
- Sentinel-2 representa el 99.4% del tamaño total (66.4 GB de 66.78 GB)
- S5P NO₂/SO₂/O₃ combinados: 164.5 MB (28k+26k+26k archivos)
- ERA5-Land: 98.9 MB (43,815 archivos horarios)
- MODIS MCD19A2: 109.8 MB (140,120 granules AOD diarios)

### EDA (Notebooks)

| Notebook | Contenido |
|----------|-----------|
| `notebooks/Situacion_1/EDAs/EDA_Sentinel5P.ipynb` | Extracción y visualización S5P: series temporales NO₂/SO₂/O₃, mapas compuestos 2018–2022, cobertura por órbita |
| `notebooks/Situacion_1/EDAs/EDA_Sentinel2.ipynb` | Muestreo imágenes ópticas alta resolución: bandas MSI, filtro nubosidad < 60%, NDVI, texturas urbanas |
| `notebooks/Situacion_1/EDAs/ERA5_.ipynb` | ERA5-Land via GEE: T2m, viento, BLH, presión, humedad |
| `notebooks/Situacion_1/EDAs/MODIS_MCD19A2_.ipynb` | MODIS MAIAC AOD: proxy PM2.5, Angstrom Exponent |
| `notebooks/Situacion_1/DAGMA/DAGMANO2.ipynb` | EDA series horarias NO₂ DAGMA (9 estaciones) |
| `notebooks/Situacion_1/DAGMA/DAGMASO2.ipynb` | EDA series horarias SO₂ DAGMA |
| `notebooks/Situacion_1/DAGMA/DAGMAO3.ipynb` | EDA series horarias O₃ DAGMA |
| `notebooks/Situacion_1/DAGMA/PrediccionesNO2_SO2.ipynb` | Ensemble (XGBoost + RF + GBR) para imputar series faltantes DAGMA con datos API datos.gov.co |
| `notebooks/Situacion_1/Satelites/DatasetS5PRO3.ipynb` | Extracción Sentinel-5P (GEE → xarray) |
| `notebooks/Situacion_1/Satelites/Sentinel2PRO3.ipynb` | Extracción Sentinel-2 (GEE → tiles) |
| `notebooks/Situacion_1/Prototipo_ETL_R2.ipynb` | Prototipo ETL: GEE → Cloudflare R2 (Zarr via xee) |
| `notebooks/eda_mc_barrios_cali.ipynb` | EDA shapefile barrios/comunas de Cali (339 polígonos, EPSG:6249) |

---

## Situación 2 — GeoVision-CLIP · Aprendizaje Multimodal

### Dataset de pares imagen–texto

Generado por `pipeline/generar_dataset_sit2_par_imagen_texto.py`:

| Parámetro | Valor |
|-----------|-------|
| Total pares | **2 276** (meta: ≥ 1 000) |
| Tile size | 64 × 64 px (13 bandas S2) |
| Clases | `contaminacion_alta_NO2` (500), `contaminacion_alta_SO2` (276), `ozono_anomalo` (500), `vegetacion_densa` (500), `suelo_urbano` (500) |
| Split | Train 1 593 / Val 341 / Test 342 (70/15/15, SEED=42) |
| Secuencias temporales | 30 × 8 fechas (para ConvLSTM Sit. 3) |
| Filtro de nubes | SCL band: `frac_nube ≤ 0.10`, `frac_claro ≥ 0.10` |
| Etiquetado | Semi-supervisado por percentiles S5P (p25/p50/p75/p90/p99) |
| Descripciones | En español, generadas automáticamente con contexto geográfico |

**Percentiles calculados sobre Cali (5 años):**

| Contaminante | p25 | p50 | p75 | p90 | p99 |
|-------------|-----|-----|-----|-----|-----|
| NO₂ (mol/m²) | 1.75e-5 | 2.40e-5 | 3.31e-5 | 4.57e-5 | 8.56e-5 |
| SO₂ (mol/m²) | 8.93e-5 | 2.04e-4 | 3.70e-4 | 5.90e-4 | 1.28e-3 |
| O₃ (mol/m²) | 0.1105 | 0.1147 | 0.1185 | 0.1219 | 0.1285 |

### Generación del dataset

```powershell
# Solo percentiles (rápido, verifica acceso a GCS)
python pipeline/generar_dataset_sit2_par_imagen_texto.py --solo-percentiles

# Dataset completo
python pipeline/generar_dataset_sit2_par_imagen_texto.py `
    --meta-objetivo 1500 `
    --max-timestamps-s2 1463 `
    --max-tiles-por-escena 40 `
    --stride-pix 32 `
    --cap-por-clase 250 `
    --min-por-clase 20 `
    --paciencia-escenas 80 `
    --dask-workers 4 `
    --max-frac-nubes 0.10 `
    --min-frac-claros 0.10 `
    --zarr-flush-every 128
```

### Arquitectura del modelo

```
src/modelos/geovision_clip_sae.py → GeoVisionClipSAEModel
├── ms_adapter: Conv2d(13, 3, kernel_size=1)     # Sentinel-2 → RGB
├── visual: ViT-B/32 (RemoteCLIP pretrained)     # Encoder visual
├── text_encoder: MiniLM-L12 multilingüe         # Encoder textual
├── text_to_sae: Linear(384, 512)                # Proyección a dim SAE
├── sae_img: SparseAutoencoder(512, 512)          # SAE rama visual
├── sae_txt: SparseAutoencoder(512, 512)          # SAE rama textual
├── proj_img: Linear(512, 256)                    # Cabeza proyección img
├── proj_txt: Linear(512, 256)                    # Cabeza proyección txt
└── logit_scale: Parameter (init log(1/0.07))     # Temperatura learnable
```

**Función de pérdida:**
$$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{InfoNCE}}(\tau) + \alpha \cdot (\mathcal{L}_{\text{SAE,img}} + \mathcal{L}_{\text{SAE,txt}})$$

donde $\mathcal{L}_{\text{SAE}} = \|x - \hat{x}\|^2 + \lambda \cdot \|z\|_1$ con $\alpha = 0.1$, $\lambda = 10^{-3}$, $d_{\text{SAE}} = 512$, $d_{\text{contrastivo}} = 256$.

### Entrenamiento

- **Framework:** PyTorch Lightning (`src/training/lit_geovision.py`)
- **Dataset:** `src/datasets/sit2_tile.py` → `Sit2TileDataset` (Zarr + Parquet)
- **Infraestructura:** Kaggle Notebooks (T4 GPU × 30h) + Google Colab (A100 × 12h)
- **Optimizer:** AdamW (lr=1e-4, weight_decay=0.01)
- **Warm-up:** 100 steps, freeze text encoder 1 época
- **Métricas por época:** loss total, InfoNCE, SAE img/txt, sparsity img/txt, Recall@1, Recall@5
- **Hardware utilizado:**
  - Kaggle: 2× P100 16GB, 4× T4 16GB
  - Colab Pro: 1× A100 40GB (fine-tuning final)
  - Batch size: 32 (Kaggle), 64 (Colab A100)

### Validación psicométrica (AFE + AFC)

Implementada en `src/utils/psychometrics_embeddings.py`:
- **AFE:** PCA con varianza acumulada — criterio ≥ 80% para determinar `m` factores
- **AFC:** 4 constructos latentes (Carga Antropogénica, Estrés Vegetal, Densidad Urbana, Volatilidad Atmosférica) evaluados con RMSEA, CFI, SRMR

### Notebook de entrenamiento

`notebooks/sit2_geovision_clip.ipynb` — ejecutable en Google Colab con descarga automática del dataset desde HuggingFace (`Slucu-0310/geovision-cali-sit2`).

---

## Situación 3 — Predicción Geoestadística Espacio-Temporal

### Pipeline integral

```
INPUT: (lat, lon) ∈ Cali, radio R ∈ [1, 15] km, contaminante ∈ {NO₂, SO₂, O₃}

PASO 1 → Generar grilla N×N (resolución 0.005°)
PASO 2 → Recuperar tile S2 + serie S5P histórica (últimas 8 fechas)
PASO 3 → GeoVision-CLIP+SAE → embeddings ∈ ℝ^(N×N × 8 × 256)
PASO 4 → ConvLSTM bidireccional → predicción (3 horizontes × N×N)
PASO 5 → Ajustar variograma experimental sobre residuos DL
PASO 6 → ST-Kriging (OrdinaryKriging3D) → superficie + σ²(s,t)
PASO 7 → LOO-CV contra 9 estaciones DAGMA → RMSE, MAE, R²
PASO 8 → Moran I global + LISA → clusters significancia local

OUTPUT: 9 mapas de gradiente + 9 mapas de incertidumbre
```

### Componente A — ConvLSTM

- Bidireccional, hidden=128, kernel=3×3, 2 capas
- Entrada: secuencias de embeddings en grilla espacial
- Salida: tensor `(B, 3, 3, H, W)` → [horizonte] × [contaminante] × [grilla]
- Capa final: Conv 1×1 → 9 predicciones simultáneas
- Entrenamiento: AdamW (lr=1e-4), early stopping sobre RMSE val

### Componente B — ST-Kriging

```python
from pykrige.ok3d import OrdinaryKriging3D

# Interpolación 3D (lat, lon, t) con normalización anisotrópica
ok = OrdinaryKriging3D(lat_n, lon_n, t_n, values,
                       variogram_model='exponential')
z, var = ok.execute('points', q_lats_n, q_lons_n, q_t_n)
# z = valor predicho, var = varianza Kriging (incertidumbre)
```

### Componente C — Validación geoestadística

1. **LOO-CV espacial:** para cada estación $e_i$, entrenar con las 8 restantes, predecir $e_i$
2. **Variograma de residuos:** debe ser nugget puro (sin estructura remanente)
3. **Moran I global:** permutation test (n=999), esperado $I > 0.30$ con $p < 0.05$
4. **LISA:** Local Indicators of Spatial Association → clusters hot/cold

---

## Frontend y despliegue

| Capa | Tecnología | Notas |
|------|-----------|-------|
| Frontend | **Next.js** + React + Leaflet | `app/geo-vision-clip-application/` |
| Backend API | FastAPI + Uvicorn | Endpoints `/predict`, `/validate` |
| Entrenamiento | Kaggle Notebooks + Colab Pro | T4/P100/A100 GPUs |
| Contenedor | Docker (Python 3.11-slim) | Multi-stage build |
| Despliegue | HuggingFace Spaces / Render | Free tier |
| Trazabilidad | Weights & Biases | Logging de runs |
| Almacenamiento | Google Cloud Storage (Zarr) | 66.78 GB verificados |

**Funcionalidades del frontend:**
- Mapa interactivo centrado en Cali con 9 estaciones DAGMA georreferenciadas
- Click en cualquier punto → consulta predicción
- Selector de contaminante y horizonte temporal
- 9 mapas de gradiente (3×3) con slider temporal animado T+1/T+3/T+7
- Capa de incertidumbre (opacidad inversamente proporcional a σ)
- Tooltips con valor predicho ± σ
- Descarga como GeoTIFF o CSV

---

## Instalación y reproducibilidad

### Requisitos

- Python 3.10+ (probado en 3.10 Windows)
- Google Cloud SDK (autenticación GEE/GCS)
- Node.js 18+ (frontend)
- CUDA 11.8+ (entrenamiento GPU, opcional)

### Setup local

```powershell
# Clonar repositorio
git clone <URL_REPOSITORIO>
cd GeoVision-CLIP-Cali

# Entorno virtual Python
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Autenticación cloud
gcloud auth application-default login
python -c "import ee; ee.Initialize(project='proyecto3ia-494900')"

# Frontend
cd app/geo-vision-clip-application
pnpm install
pnpm dev
```

### Semillas y reproducibilidad

```python
SEED = 42  # Todas las operaciones estocásticas
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
```

### Docker

```powershell
docker build -t geovision-clip-cali .
docker run -p 8000:8000 geovision-clip-cali
```

---

## KPIs y métricas

### Situación 2 — GeoVision-CLIP

| KPI | Umbral mínimo | Excelente | Medición |
|-----|---------------|-----------|----------|
| Recall@1 img→txt | ≥ 0.45 | ≥ 0.65 | `clip_metrics.recall_at_k_image_to_text(e_img, e_txt, k=1)` |
| Recall@5 img→txt | ≥ 0.70 | ≥ 0.85 | `clip_metrics.recall_at_k_image_to_text(e_img, e_txt, k=5)` |
| Sparsity SAE visual | ≥ 0.70 | ≥ 0.85 | `clip_metrics.sparsity_ratio(z_img, threshold=0.01)` |
| Loss reconstrucción SAE | ≤ 0.05 | ≤ 0.02 | `clip_metrics.mse_reconstruction(x, x_hat)` |
| Varianza explicada AFE | ≥ 80% | ≥ 90% | `psychometrics_embeddings.scree_accumulated_variance()` |
| RMSEA (AFC) | < 0.08 | < 0.05 | semopy |
| CFI (AFC) | > 0.90 | > 0.95 | semopy |

### Situación 3 — Predicción geoestadística

| KPI | Mínimo | Excelente | Verificación |
|-----|--------|-----------|--------------|
| RMSE LOO-CV NO₂ (T+1) | ≤ 8 µg/m³ | ≤ 4 µg/m³ | vs. DAGMA |
| RMSE LOO-CV SO₂ (T+1) | ≤ 6 µg/m³ | ≤ 3 µg/m³ | vs. DAGMA |
| RMSE LOO-CV O₃ (T+1) | ≤ 12 µg/m³ | ≤ 6 µg/m³ | vs. DAGMA |
| R² LOO-CV (promedio) | ≥ 0.55 | ≥ 0.75 | scikit-learn |
| Moran I predicciones | > 0.30 (p<0.05) | > 0.50 | esda.Moran |
| Variograma residuos | Nugget puro | Nugget puro | PyKrige |
| Cobertura cinturón 95% | ≥ 92% | ≥ 95% | Empírico LOO |
| Degradación T+1→T+7 | < 60% aumento | < 30% | Ratio RMSE |
| Latencia end-to-end | < 8 s | < 3 s | `time.perf_counter` |

---

## API — Contrato JSON `/predict`

### Request

```json
{
  "lat": 3.4516,
  "lon": -76.5320,
  "radius_km": 5,
  "horizons_days": [1, 3, 7],
  "pollutants": ["NO2", "SO2", "O3"]
}
```

### Response

```json
{
  "request_id": "pred_2026_05_19_0001",
  "input": {
    "lat": 3.4516,
    "lon": -76.5320,
    "radius_km": 5
  },
  "results": [
    {
      "pollutant": "NO2",
      "horizon_day": 1,
      "value_ug_m3": 22.4,
      "kriging_variance": 3.1,
      "uncertainty_sigma": 1.76,
      "grid_asset_uri": "gs://geovision-cali/predictions/no2_t1.tif"
    }
  ],
  "meta": {
    "model_version": "v1.0.0",
    "checkpoint_md5": "a1b2c3d4e5f6...",
    "timestamp_utc": "2026-05-19T21:30:00Z",
    "latency_ms": 2450
  }
}
```

---

## Entregables

### Situación 1
- [x] Diagrama de arquitectura cloud (almacenamiento + cómputo + orquestación)
- [x] Manifest JSON con ≥ 50 GB verificados y hashes MD5 → **LOGRADO: 66.78 GB (133.5%)**
- [x] Notebook EDA con ≥ 8 visualizaciones del panel → **12 notebooks EDA ejecutados**
- [x] Pipeline ETL distribuido (Dask 4 workers) → **283,437 archivos procesados**
- [x] Reporte de costos cloud y discusión de cuellos de botella

### Situación 2
- [x] Dataset ≥ 1 000 pares imagen-texto → **LOGRADO: 2,276 pares (227.6%)**
- [x] Split estratificado 70/15/15 (SEED=42) → **1,593 / 341 / 342**
- [x] 5 clases semi-supervisadas → **Balance: 500/276/500/500/500**
- [x] 30 secuencias temporales × 8 fechas → **Para ConvLSTM Sit. 3**
- [x] Checkpoint `.pt` con MD5 verificable → **Entrenado en Kaggle T4 + Colab A100**
- [x] Curvas de entrenamiento (loss, InfoNCE, SAE, sparsity)
- [x] Reporte AFE+AFC (matriz de cargas, scree plot, RMSEA/CFI/SRMR)
- [x] Análisis de neuronas activas SAE por clase

### Situación 3
- [x] Notebook ConvLSTM con curvas y métricas reproducibles
- [x] Reporte geoestadístico: variogramas + Moran I + LISA
- [x] Tabla LOO-CV por estación DAGMA y contaminante
- [x] Sistema desplegado con 9 mapas de gradiente + incertidumbre
- [x] Análisis de perfiles tipológicos (K-Means sobre superficies)

### Entrega final
- [x] Informe PDF (15–25 páginas) con estructura completa
- [x] Notebooks ejecutados con outputs visibles
- [x] Manifest con MD5
- [ ] Dockerfile funcional
- [x] URL pública del sistema desplegado
- [x] URL del repositorio Git

---

## Stack tecnológico

| Capa | Tecnología | Versión / Notas |
|------|-----------|----------------|
| Almacenamiento | Google Cloud Storage (Zarr) | 66.78 GB, 283k archivos |
| ETL distribuido | Dask Distributed | ≥ 2024.1, 4 workers × 2 threads |
| Arrays N-D | xarray + zarr | zarr 2.16–2.18 |
| Modelo CLIP | open-clip-torch (RemoteCLIP) | ≥ 2.24, ViT-B/32 |
| Texto multilingüe | sentence-transformers MiniLM-L12 | 384-d embeddings |
| Entrenamiento | PyTorch + Lightning | ≥ 2.1, Kaggle + Colab |
| GPUs utilizadas | Kaggle T4/P100 + Colab A100 | 42h cómputo total |
| Geoestadística | PyKrige + PySAL (esda) | OrdinaryKriging3D |
| Geoespacial | GeoPandas + rioxarray | EPSG:4326 |
| Backend | FastAPI + Uvicorn | — |
| Frontend | Next.js + React + Leaflet | — |
| Contenedor | Docker (Python 3.11-slim) | Multi-stage |
| Trazabilidad | Custom (JSONL) + W&B | `runs/` + cloud |

---

## Referencias técnicas

1. Veefkind, J.P. et al. (2012). *TROPOMI on the ESA Sentinel-5 Precursor*. Remote Sensing of Environment, 120, 70–83.
2. van Geffen, J. et al. (2022). *Sentinel-5P TROPOMI NO₂ retrieval*. AMT.
3. Theys, N. et al. (2017). *Sulfur dioxide retrievals from TROPOMI onboard Sentinel-5 Precursor*. AMT.
4. Liu et al. (2024). *RemoteCLIP: A Vision Language Foundation Model for Remote Sensing*. IEEE TGRS.
5. Cressie, N. & Wikle, C. (2011). *Statistics for Spatio-Temporal Data*. Wiley.
6. Anselin, L. (1995). *Local Indicators of Spatial Association — LISA*. Geographical Analysis 27(2).
7. Templeton, T. et al. (2023). *Sparse Autoencoders for Mechanistic Interpretability*. Anthropic Technical Report.

---

## Licencia

Proyecto académico — Universidad Autónoma de Occidente, Cali, Colombia.


