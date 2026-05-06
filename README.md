# GeoVision-CLIP Cali - Guia operativa del equipo

Este repositorio es la base unica para implementar la consigna del proyecto (Situacion 1, 2 y 3) sin scripts sueltos en computadores personales.

---

## 1) Estructura del repositorio

```text
proyecto 3.1/
  src/
    etl/          # pipelines de descarga, recorte, transformacion, validacion
    models/       # CLIP+SAE, ConvLSTM, entrenamiento/inferencia
    geo/          # Kriging, Moran/LISA, LOO-CV, evaluaciones espaciales
  scripts/        # entrypoints ejecutables
  notebooks/      # EDA, entrenamiento y reportes ejecutados
  manifests/      # manifiestos de datos + hashes
  frontend/       # app web (React/Vite)
  Dockerfile
  requirements.txt
  .gitignore
  README.md
```

---

## 2) Roles del equipo (recomendado)

- Persona 1 (Datos/ETL): descarga, limpieza, transformacion, manifest y hashes.
- Persona 2 (Modelos): CLIP+SAE, entrenamiento, evaluacion, checkpoints y AFE/AFC de embeddings.
- Persona 3 (Geo + API + Frontend): ConvLSTM, Kriging, backend y frontend.

Regla de trabajo:
- No se desarrolla fuera de este repo.
- Notebook nuevo debe apoyarse en codigo reutilizable de `src/` o `scripts/`.

---

## 3) ETLs que exige la consigna y como montarlos

Segun la consigna, el pipeline ETL obligatorio de Situacion 1 debe cubrir:

1. Credenciales GEE + CDSE + Earthdata.
2. Descarga distribuida (Dask o Spark), no secuencial.
3. Recorte HARP para Sentinel-5P L2 sobre bbox de Cali.
4. Conversion a Zarr o Parquet particionado.
5. Persistencia en almacenamiento de objetos (S3/GCS/Azure).
6. Manifest JSON con hash MD5 y metadatos.
7. EDA de cobertura/calidad/series.

### 3.1 Fuentes a integrar en ETL

- Sentinel-5P OFFL L2/L3: NO2, SO2, O3.
- Sentinel-2 L2A: bandas opticas.
- MODIS MCD19A2 (AOD).
- ERA5-Land (meteorologia).
- DAGMA/SISAIRE (ground truth estaciones).

### 3.2 BBox operativa

Usar la huella definida en consigna para Cali:
- lon_min: -76.60
- lat_min: 3.30
- lon_max: -76.40
- lat_max: 3.55

### 3.3 Como dividir ETL en este repo

En `src/etl/` separar por etapas:

- `auth.py`: manejo de credenciales y validaciones de acceso.
- `extract_s5p.py`: descarga S5P por contaminante y fecha.
- `extract_s2.py`: descarga Sentinel-2 por tile/fecha.
- `extract_era5.py`: descarga ERA5-Land por rango temporal.
- `extract_modis.py`: descarga MAIAC AOD.
- `extract_ground.py`: ingestión DAGMA/SISAIRE.
- `harp_crop.py`: recorte espacial HARP para S5P.
- `transform_store.py`: conversion/chunking a Zarr o Parquet.
- `quality_checks.py`: validaciones de completitud/duplicados/esquema.
- `manifest.py`: generacion de manifiesto con hashes.

En `scripts/` dejar entrypoints:

- `run_etl_auth.py`
- `run_etl_extract.py`
- `run_etl_harp.py`
- `run_etl_transform.py`
- `run_etl_manifest.py`
- `run_etl_eda.py`

---

## 4) Orden de ejecucion sugerido (Situacion 1)

1. `python scripts/run_etl_auth.py`  
   Verifica que todas las credenciales funcionen.

2. `python scripts/run_etl_extract.py`  
   Ejecuta descargas distribuidas por fuente y tiempo (Dask/Spark).

3. `python scripts/run_etl_harp.py`  
   Aplica recorte HARP para S5P sobre bbox Cali.

4. `python scripts/run_etl_transform.py`  
   Convierte y guarda en Zarr/Parquet particionado.

5. `python scripts/run_etl_manifest.py`  
   Genera `manifests/dataset_manifest.json` con hash MD5 por archivo.

6. `python scripts/run_etl_eda.py`  
   Produce tablas/figuras para el notebook de EDA.

---

## 5) Reglas tecnicas ETL (importantes para evaluacion)

- Paralelizacion obligatoria por banda/fecha/tile.
- Evitar leakage: no mezclar target y features de forma incorrecta.
- Trazabilidad completa por archivo (ruta + hash + metadata).
- Umbral de datos: dataset final verificado >= 50 GB.
- Datos pesados no se suben a Git; solo manifest y codigo.

---

## 6) Contrato JSON de `/predict` (borrador inicial)

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

## 7) Entregables minimos que deben salir de este repo

- `manifests/dataset_manifest.json` (hashes + metadatos).
- `notebooks/01_eda_panel.ipynb` con outputs.
- `notebooks/02_train_clip_sae.ipynb` con curvas y metricas.
- `notebooks/03_geo_validation.ipynb` con LOO, Moran y LISA.
- URL de sistema desplegado y URL del repositorio.


