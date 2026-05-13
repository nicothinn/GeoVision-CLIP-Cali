# GeoVision-CLIP Cali - Guia operativa del equipo

Este repositorio es la base unica para implementar la consigna del proyecto (Situacion 1, 2 y 3) sin scripts sueltos en computadores personales.

---

## 1) Estructura del repositorio

```text
GeoVision-CLIP-Cali/
  pipeline/                    # Nucleo ETL y preparacion de datos
    config.py                  # BBox, fuentes, bandas, Dask, GCP/GEE
    exportar.py                # Pipeline distribuido Dask -> GCS con MD5
    convertir_zarr.py          # GeoTIFF -> Zarr con ThreadPoolExecutor
    validar_zarr.py            # Validacion de integridad de paneles Zarr
    manifest.py                # Consolidador de manifest global
    dataset_sit2_par_imagen_texto.py  # Dataset pares imagen-texto Sit.2
    silenciar_warnings.py      # Filtro de warnings ruidosos
    trazabilidad/              # Sistema de runs + eventos JSONL + logs
       sistema.py / dask_plugin.py / __init__.py
  1Situacion/                  # Material Situacion 1
    DagmaDATA/                 # Ground truth DAGMA 2019-2023 (15 CSVs)
      NO2DAGMASISNO2/ O3DAGMA/ SO2DAGMA/
    notebooks/                 # 9 notebooks Jupyter
      DAGMA/                   # Procesamiento ground truth
        DAGMANO2.ipynb / DAGMAO3 (1).ipynb / DAGMASO2 (1).ipynb
        PrediccionesNO2_SO2.ipynb
      EDAs/                    # Analisis exploratorio
        EDA_Sentinel2.ipynb    # 10 visualizaciones panel optico
        EDA_Sentinel5P.ipynb   # 12 visualizaciones, 3 contaminantes
      Satelites/               # Descarga y procesamiento satelital
        DatasetS5PRO3.ipynb / Sentinel2PRO3.ipynb
      Prototipo_ETL_R2.ipynb   # Prototipo ETL GEE -> Cloudflare R2
    guides/                    # Resumenes de los 7 papers de referencia
      PAPERS_GUIA_PROYECTO.md  # Guia maestra papers -> tareas
    manifests/                 # Manifiestos parciales por fuente
    Papers/                    # PDFs originales de referencia
  2Situacion/                  # Modelo CLIP+SAE (proxima etapa)
  3Situacion/                  # ConvLSTM + Kriging + Frontend (etapa final)
  papersglobales/              # Documentos estrategicos
    consigna_proyecto.md       # Consigna oficial completa
    Contrapropuesta_Minimo_Viable_Evaluable.md
    Preguntas.md
    PDF/                       # Documento formal del proyecto
      ProyectoFinal_GeoVisionCLIP_Cali.pdf
  informe/                     # Template LaTeX del informe final
    template_geovision.tex
  src/                         # Arquitectura futura (scaffold)
    etl/  models/  geo/
  frontend/                    # App web React + Vite + Leaflet (proxima etapa)
  scripts/                     # Entrypoints ejecutables
  runs/                        # Trazabilidad de ejecuciones
  Dockerfile                   # Imagen Python 3.11-slim multi-stage
  requirements.txt
  .gitignore
  README.md
```

---

## 2) ETLs que exige la consigna y como montarlos

Segun la consigna, el pipeline ETL obligatorio de Situacion 1 debe cubrir:

1. Credenciales GEE + CDSE + Earthdata.
2. Descarga distribuida (Dask o Spark), no secuencial.
3. Recorte HARP para Sentinel-5P L2 sobre bbox de Cali.
4. Conversion a Zarr o Parquet particionado.
5. Persistencia en almacenamiento de objetos (S3/GCS/Azure).
6. Manifest JSON con hash MD5 y metadatos.
7. EDA de cobertura/calidad/series.

### 3.1 Fuentes integradas en el pipeline

Todas las fuentes satelitales estan configuradas en `pipeline/config.py` con sus bandas, escalas nativas y prefijos GCS:

| Fuente | Coleccion GEE / API | Modo | Prefijo GCS |
|--------|---------------------|------|-------------|
| Sentinel-5P NO2 | `COPERNICUS/S5P/OFFL/L3_NO2` | multibanda (3 bandas) | `Sentinel5P/NO2/` |
| Sentinel-5P SO2 | `COPERNICUS/S5P/OFFL/L3_SO2` | multibanda (3 bandas) | `Sentinel5P/SO2/` |
| Sentinel-5P O3 | `COPERNICUS/S5P/OFFL/L3_O3` | multibanda (3 bandas) | `Sentinel5P/O3/` |
| Sentinel-2 L2A | `COPERNICUS/S2_SR_HARMONIZED` | por banda (13 bandas B2-B12) | `Sentinel2/` |
| ERA5-Land | CDS API (T2m, viento, BLH, RH) | multibanda | `ERA5/` |
| MODIS MCD19A2 | `MODIS/061/MCD19A2_GRANULES` | multibanda (AOD) | `MODIS/` |

**Ground truth DAGMA:** 15 archivos CSV ya descargados en `1Situacion/DagmaDATA/` con 5 anos de datos horarios (2019-2023) de NO2, SO2 y O3 para las 9 estaciones de monitoreo.

### 3.2 BBox operativa

Definida en `pipeline/config.py`, ligeramente ampliada respecto a la consigna para incluir el corredor industrial Yumbo-Acopi y la zona de cultivos de cana del norte del Valle:

- lon_min: -76.65
- lat_min:  3.30
- lon_max: -76.30
- lat_max:  3.65

### 3.3 Arquitectura ETL implementada en `pipeline/`

Todo el ETL se concentra en el directorio `pipeline/` como modulos autocontenidos con CLI:

| Modulo | Funcion |
|--------|---------|
| `pipeline/config.py` | Constantes centrales: proyecto GCP `proyecto3ia-494900`, bucket `gs://geovision-cali`, BBox, 5 fuentes satelitales con bandas/escalas, configuracion Dask (4 workers x 2 threads, 4 GB) |
| `pipeline/exportar.py` | Pipeline maestro de descarga distribuida. Lista imagenes en GEE por fuente, construye tareas Dask (una por banda/fecha/tile), descarga con reintento + backoff exponencial, calcula MD5 inline, sube a `gs://geovision-cali/{fuente}/raw/` y genera `manifest_partial.json` por fuente. Soporta `--fuente`, `--todas`, `--max-imagenes`, `--dry-run`, `--anio`, `--inicio`, `--fin` |
| `pipeline/convertir_zarr.py` | Convierte GeoTIFF crudos en GCS a paneles Zarr con chunking espacio-temporal. Usa ThreadPoolExecutor para lecturas paralelas, escribe esqueleto Zarr lazy via xarray+dask, procesa en batches seguros por hilo |
| `pipeline/validar_zarr.py` | Valida integridad de paneles Zarr en GCS: presencia, shape, bandas, rango temporal, chunks, %NaN |
| `pipeline/manifest.py` | Consolida los `manifest_partial.json` de cada fuente en un `manifest.json` global con rutas GCS, MD5, dimensiones, fecha y bbox. Soporta `--subir-a-gcs` |
| `pipeline/dataset_sit2_par_imagen_texto.py` | Construye el dataset de pares imagen-texto para Situacion 2: calcula percentiles globales de NO2/SO2/O3 desde Zarr, extrae tiles Sentinel-2 64x64, asigna clase semi-supervisada (5 clases), genera descripcion en espanol, split estratificado 70/15/15 seed=42, secuencias temporales de 8 fechas |
| `pipeline/trazabilidad/` | Sistema de Runs con timestamp + eventos JSONL + logs. Cada ejecucion deja traza completa en `runs/` |
| `pipeline/silenciar_warnings.py` | Filtro de warnings de GEE y dependencias |

---

## 3) Orden de ejecucion (Situacion 1)

### 4.1 Credenciales
Autenticarse en GEE y GCP antes de ejecutar cualquier modulo:
```bash
gcloud auth application-default login
python -c "import ee; ee.Initialize(project='proyecto3ia-494900')"
```

### 4.2 Descarga distribuida del panel completo
El pipeline `exportar.py` orquesta todo el ETL en un solo comando:
```bash
# Descargar todas las fuentes (S5P NO2/SO2/O3, Sentinel-2, ERA5, MODIS)
python pipeline/exportar.py --todas

# O por fuente individual + ventana temporal
python pipeline/exportar.py --fuente Sentinel5P/NO2 --anio 2023

# Modo dry-run para verificar acceso sin descargar
python pipeline/exportar.py --todas --dry-run
```
Cada ejecucion genera automaticamente `manifest_partial.json` con MD5 por archivo y deja traza en `runs/`.

### 4.3 Conversion a Zarr
```bash
python pipeline/convertir_zarr.py --fuente Sentinel5P/NO2
python pipeline/convertir_zarr.py --todas
```

### 4.4 Consolidar manifest global
```bash
python pipeline/manifest.py --subir-a-gcs
```

### 4.5 Validar integridad
```bash
python pipeline/validar_zarr.py --fuente Sentinel5P/NO2
```

### 4.6 EDA
Abrir y ejecutar los notebooks en `1Situacion/notebooks/`:
- `EDA_Sentinel2.ipynb` — 10 visualizaciones del panel optico
- `EDA_Sentinel5P.ipynb` — 12 visualizaciones, series temporales por contaminante

---

## 4) Reglas tecnicas ETL (importantes para evaluacion)

- Paralelizacion obligatoria por banda/fecha/tile: implementada via Dask Distributed (4 workers, 2 threads c/u) en `pipeline/exportar.py`.
- Evitar leakage: los targets (S5P) nunca se pasan como input directo al modelo; solo se usan para pseudo-etiquetado en Situacion 2.
- Trazabilidad completa: cada ejecucion de `pipeline/exportar.py` deja un directorio en `runs/` con `log.txt` + `eventos.jsonl`. El sistema de Runs esta en `pipeline/trazabilidad/`.
- Umbral de datos: dataset final verificado >= 50 GB (verificable con `python pipeline/manifest.py`).
- Datos pesados no se suben a Git: solo manifest, codigo y notebooks. Los GeoTIFF y Zarr residen en `gs://geovision-cali`.
- MD5 por archivo: calculado inline durante la descarga en `pipeline/exportar.py`, consolidado en `manifest.json`.

---

## 5) Contrato JSON de `/predict` (borrador inicial)

Este contrato alinea backend y frontend para Situacion 3.

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
  "request_id": "pred_2026_05_05_0001",
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
      "grid_asset_uri": "s3://bucket/path/no2_t1.tif"
    }
  ],
  "meta": {
    "model_version": "v0.1.0",
    "timestamp_utc": "2026-05-05T21:30:00Z"
  }
}
```

---

## 6) Entregables que salen de este repo

- `manifests/manifest.json` — hashes MD5 + metadatos de todo el panel.
- `1Situacion/notebooks/EDAs/EDA_Sentinel5P.ipynb` — EDA con 12 visualizaciones del panel S5P.
- `1Situacion/notebooks/EDAs/EDA_Sentinel2.ipynb` — EDA con 10 visualizaciones del panel S2.
- `1Situacion/notebooks/DAGMA/` — 4 notebooks de procesamiento ground truth DAGMA.
- `informe/template_geovision.tex` — template LaTeX del informe final.
- `runs/` — trazabilidad completa de todas las ejecuciones.
- URL del sistema desplegado y URL del repositorio Git.


