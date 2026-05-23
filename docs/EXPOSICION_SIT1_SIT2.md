# GeoVision-CLIP Cali — Guía de exposición ampliada (Sit. 1 + Sit. 2)

> **Versión pitch (14 diapos):** [`EXPOSICION_SIT1_SIT2_14diapos.md`](EXPOSICION_SIT1_SIT2_14diapos.md) · 12–14 min + demo

**Total:** ~42 diapositivas · **Duración:** 18–22 min + 4 min demo  
**Audiencia:** Analítica de Datos I · UAO · defensa por cualquier integrante  
**Fuentes:** [`consigna_proyecto.md`](papersglobales/consigna_proyecto.md) · [`README.md`](../README.md)

---

## Índice rápido

| Bloque | Diapositivas | Tema |
|--------|--------------|------|
| Apertura | 1–2 | Título y agenda |
| Problema | 3–6 | Cali, DAGMA, resolución satelital, pregunta |
| Arquitectura | 7–10 | 3 situaciones, stack, anti-leakage |
| Sit. 1 — Panel | 11–15 | 50 GB, fuentes, manifest, cloud |
| Pipeline ETL | 16–20 | Módulos, Dask, Zarr, trazabilidad |
| EDAs + DAGMA | 21–26 | Por fuente + regresión + barrios |
| Sit. 2 — Dataset | 27–32 | Tiles, clases, pipeline, secuencias |
| Modelo CLIP+SAE | 33–38 | Arquitectura, loss, entreno, híbrido |
| Resultados | 39–43 | KPIs, causas, mejoras, AFE |
| App y cierre | 44–48 | Frontend, entregables, Sit.3, refs |

---

## Mensaje central (20 s — diapositiva 1 o cierre)

> Integramos ≥66 GB de satélites en GCS, 2 276 pares imagen–texto y GeoVision-CLIP para embeddings; la app Next.js ya muestra Cali con barrios y predicción; Sit. 3 cerrará con ConvLSTM, Kriging y validación DAGMA.

---

# BLOQUE 0 — APERTURA

### Diapositiva 1 — Portada

**Título:** GeoVision-CLIP Cali  
**Subtítulo:** Contaminación atmosférica en puntos no muestreados · DL + geoestadística

**Pie:** Analítica de Datos I · Tercer Corte · UAO · Grupo [nombres]

**Mostrar:** logo UAO + captura mapa app (modo oscuro).

---

### Diapositiva 2 — Agenda

**Título:** Qué vamos a mostrar hoy

| # | Tema | Consigna |
|---|------|----------|
| 1 | Panel cloud ≥50 GB | Sit. 1 · 20% |
| 2 | Dataset + GeoVision-CLIP | Sit. 2 · 20% |
| 3 | App + roadmap Kriging | Sit. 3 + deploy · 40% |

**Mostrar:** lista con iconos (nube · cerebro · mapa).

---

# BLOQUE 1 — PROBLEMA (diapositivas 3–6)

### Diapositiva 3 — Cali y salud ambiental

**Título:** Tercera ciudad de Colombia · presión atmosférica heterogénea

- 564 km² municipio · ~2.8 M hab.
- Fuentes: tráfico · industria Valle · quemas caña · Pacífico
- Res. 2254/2017: límites NO₂, SO₂, O₃

**Mostrar:** mapa regional Valle del Cauca.

**Nota oral:** No es solo “contaminación”: es equidad espacial de exposición.

---

### Diapositiva 4 — Red DAGMA (ground truth)

**Título:** 9 estaciones · mediciones puntuales

- NO₂, SO₂, O₃ troposférico · horario
- Zonas: Sur · Centro · Oeste · Norte (Yumbo)
- IDEAM / SISAIRE: reportes oficiales

**Mostrar:** mapa 9 marcadores (app o figura DAGMA).

**Nota oral:** Validación externa obligatoria en Sit. 3 (LOO-CV).

---

### Diapositiva 5 — Brecha espacial: satélites

**Título:** Dos resoluciones · un mismo problema

| Sensor | Qué mide | Resolución | Límite |
|--------|----------|------------|--------|
| Sentinel-5P | Gases columna | ~3.5×5.5 km | No ve barrios |
| Sentinel-2 | Superficie | 10 m | No ve gases |

**Hipótesis:** fusionar S2 (contexto) + S5P (etiqueta) vía modelo multimodal.

**Mostrar:** diagrama lado a lado S5P grueso vs S2 fino.

---

### Diapositiva 6 — Pregunta del proyecto

**Título:** Pregunta operativa

**Texto grande (1 línea):**  
¿Concentración de NO₂, SO₂ y O₃ en **cualquier** (lat, lon) con **incertidumbre σ**?

**Sub-bullets:**
- Solo datos satelitales gratuitos + 9 estaciones validación
- Horizontes T+1, T+3, T+7 días
- Sin Streamlit · app profesional obligatoria

**Mostrar:** click en mapa → predicción (foto app).

---

# BLOQUE 2 — ARQUITECTURA (diapositivas 7–10)

### Diapositiva 7 — Tres situaciones acumulativas

**Título:** Proyecto en 3 entregas encadenadas

```
SIT.1  Ingeniería datos  →  panel ≥50 GB
SIT.2  Deep Learning     →  CLIP + SAE + AFE/AFC
SIT.3  Geoestadística    →  ConvLSTM + Kriging + Moran
```

**Pesos rúbrica:** 20% + 20% + 30% + 10% frontend + 10% informe + 10% pitch

**Mostrar:** tres cajas con flechas verticales.

---

### Diapositiva 8 — Flujo de datos end-to-end

**Título:** Del satélite al mapa en el navegador

```
GEE/GCS  →  ETL Dask  →  tiles + parquet
         →  entrenamiento GPU  →  checkpoint .pt
         →  API FastAPI  →  Next.js + Leaflet
```

**Mostrar:** diagrama README (sección Arquitectura).

---

### Diapositiva 9 — Stack tecnológico

**Título:** Herramientas por capa

| Capa | Tecnología |
|------|------------|
| Storage | GCS + Zarr |
| ETL | Dask · xarray · GeoPandas |
| ML | PyTorch · Lightning · open-clip RemoteCLIP |
| Geo | PyKrige · PySAL (esda) |
| App | **Next.js** · Leaflet · React Query |

**Nota oral:** PyTorch + GeoPandas + PyKrige exigidos en consigna.

---

### Diapositiva 10 — Regla anti-leakage

**Título:** Diseño que evita trampa −25%

- **Prohibido:** pasar S5P crudo como input del modelo de predicción final
- **Permitido:** S5P solo para **etiquetar** tiles en entrenamiento CLIP
- Sit. 3: embeddings + Kriging · validación solo en DAGMA

**Mostrar:** esquema “S5P → etiqueta → tile” vs “S5P → predicción directa” tachado.

---

# BLOQUE 3 — SITUACIÓN 1: PANEL (diapositivas 11–15)

### Diapositiva 11 — Objetivo Sit. 1

**Título:** Panel espacio-temporal ≥50 GB

**Consigna:**
- 5 años · BBox Cali metropolitana
- S5P + S2 + ERA5 + MODIS + DAGMA
- Zarr/Parquet · manifest MD5 · EDA ≥8 figuras

**Mostrar:** tabla requisitos consigna (checkmarks).

---

### Diapositiva 12 — Resultado: 66.78 GB

**Título:** Umbral cumplido al **133.5%**

- **66.78 GB** · **283 437** archivos
- `umbral_cumplido: true` en manifest
- Proyecto GCP: `proyecto3ia-494900`
- Bucket: `geovision-cali`

**Mostrar:** JSON manifest o gráfico barras por fuente.

---

### Diapositiva 13 — Desglose por fuente

**Título:** ¿Dónde está el volumen?

| Fuente | Archivos | Tamaño |
|--------|----------|--------|
| Sentinel-2 | 19 121 | **66.4 GB** |
| MODIS MCD19A2 | 140 120 | 110 MB |
| ERA5-Land | 43 815 | 99 MB |
| S5P NO₂/SO₂/O₃ | ~80k | ~165 MB |

**Bullet clave:** S2 = 99.4% del peso → obliga cloud + paralelismo.

**Mostrar:** pie chart o barras log-scale.

---

### Diapositiva 14 — BBox y periodo

**Título:** Huella espacial ampliada

```
BBox: [-76.65, 3.30, -76.30, 3.65]
Periodo: 2019–2023 (5 años)
```

- Incluye Yumbo–Acopi industrial
- Incluye zona caña norte Valle
- Más amplio que consigna mínima (−76.60…3.55)

**Mostrar:** rectángulo sobre mapa Cali.

---

### Diapositiva 15 — Entregables Sit. 1 ✓

**Título:** Checklist Sit. 1

- [x] Diagrama arquitectura cloud
- [x] Manifest MD5 global
- [x] **12+ notebooks EDA** ejecutados
- [x] ETL Dask (no secuencial)
- [x] Reporte costos / cuellos de botella (informe)

**Mostrar:** lista con checks verdes.

---

# BLOQUE 4 — PIPELINE ETL (diapositivas 16–20)

### Diapositiva 16 — Visión del pipeline

**Título:** `pipeline/` — 5 etapas

```
exportar.py  →  convertir_zarr.py  →  validar_zarr.py
                    ↓
              manifest.py  (+ MD5)
                    ↓
         generar_dataset_sit2_*.py
```

**Mostrar:** diagrama 5 cajas horizontal.

---

### Diapositiva 17 — `exportar.py`

**Título:** Descarga distribuida GEE → GCS

- **Dask:** 4 workers × 2 threads × 4 GB
- 1 tarea por banda/fecha/tile
- Retry exponencial · MD5 inline por archivo
- `manifest_partial.json` por fuente

**Mostrar:** snippet CLI `--todas` o log Dask dashboard.

---

### Diapositiva 18 — `convertir_zarr.py`

**Título:** GeoTIFF → Zarr espacio-temporal

- xarray + dask.array (esqueleto lazy)
- Chunking `(time, band, y, x)`
- Escritura por **regiones** (sin race conditions)
- Consolidación metadatos al final

**Mostrar:** esquema cubo 4D con ejes etiquetados.

---

### Diapositiva 19 — `manifest.py` + `validar_zarr.py`

**Título:** Trazabilidad y calidad

**Manifest global:**
- ruta · MD5 · dimensiones · fecha · fuente · bbox

**Validación:**
- shape · bandas · %NaN muestreado · chunks

**Mostrar:** 2 líneas ejemplo manifest + salida validador OK.

---

### Diapositiva 20 — Trazabilidad de corridas

**Título:** `runs/` + `eventos.jsonl`

- Cada corrida: `runs/<timestamp>_<nombre>/`
- `log.txt` + eventos estructurados
- Plugin Dask propaga logs a workers
- Reproducibilidad entre integrantes

**Mostrar:** árbol carpeta `runs/` (captura).

---

# BLOQUE 5 — EDAs Y DAGMA (diapositivas 21–26)

### Diapositiva 21 — Por qué EDA masivo

**Título:** Explorar antes de entrenar

- Ver cobertura temporal real (nubes tropicales)
- Calibrar percentiles S5P sobre Cali
- Detectar huecos DAGMA
- Justificar filtros SCL en pipeline

**Mostrar:** collage 4 mini-gráficos.

---

### Diapositiva 22 — EDA Sentinel-5P

**Título:** `EDA_Sentinel5P.ipynb`

- Series NO₂ / SO₂ / O₃ 2018–2022
- Mapas compuestos por contaminante
- Cobertura por órbita · nubes
- Base para **percentiles** del dataset Sit.2

**Mostrar:** serie temporal + mapa calor NO₂.

---

### Diapositiva 23 — EDA Sentinel-2

**Título:** `EDA_Sentinel2.ipynb`

- 13 bandas MSI · filtro nubosidad
- NDVI · texturas urbanas
- SCL: nube / sombra / claro
- Motiva tile 64×64 y filtro train estricto

**Mostrar:** RGB + banda SCL coloreada.

---

### Diapositiva 24 — ERA5 y MODIS

**Título:** Covariables auxiliares del panel

| Notebook | Variables |
|----------|-----------|
| `ERA5_.ipynb` | T2m · viento · BLH · HR |
| `MODIS_MCD19A2_.ipynb` | AOD · proxy material particulado |

**Nota oral:** Contexto meteorológico para Sit. 3 y features futuras.

**Mostrar:** una serie ERA5 + mapa AOD.

---

### Diapositiva 25 — DAGMA: EDA + regresión

**Título:** Ground truth local

**EDAs:** `DAGMANO2` · `DAGMASO2` · `DAGMAO3`
- 9 estaciones · estacionalidad · outliers

**Regresión:** `PrediccionesNO2_SO2.ipynb`
- Huecos en CSV 2019–2023
- **Ensemble:** XGBoost + RF + GBR
- API datos.gov.co · imputación series

**Mostrar:** serie con huecos → serie imputada.

**Nota oral:** Regresión prepara LOO-CV; no es el modelo final de mapas.

---

### Diapositiva 26 — Barrios de Cali (`mc_barrios`)

**Título:** Contexto urbano en la app

- Shapefile oficial: **339 barrios** · **22 comunas**
- CRS EPSG:6249 → GeoJSON WGS84 en app
- EDA: `eda_mc_barrios_cali.ipynb`
- Mapa: polígonos + tooltip hover barrio/comuna

**Mostrar:** mapa app con capas administrativas ON.

---

# BLOQUE 6 — SIT. 2 DATASET (diapositivas 27–32)

### Diapositiva 27 — Objetivo Sit. 2

**Título:** ≥1 000 pares imagen–texto

**Consigna:**
- 5 clases · descripción español
- Split 70/15/15 · SEED=42
- ≥30 secuencias × 8 fechas

**Logrado:** **2 276 pares** (227%) · **30 secuencias**

**Mostrar:** checklist con checks.

---

### Diapositiva 28 — ¿Qué es un tile?

**Título:** Unidad espacial del dataset

- Recorte **64×64 px** (~640 m) de escena S2
- **13 bandas** (B1–B12 + SCL)
- `tile_id = img_id_s2__y####__x####`
- 1 escena → hasta 40 tiles (stride 32)

**Mostrar:** esquema escena grande + recorte rojo.

---

### Diapositiva 29 — Las 5 clases

**Título:** Etiquetado semi-supervisado

| Clase | n | Regla (resumen) |
|-------|---|-----------------|
| NO₂ alto | 500 | Exceso NO₂ vs percentil Cali |
| SO₂ alto | 276 | Score v2: mayor exceso relativo |
| Ozono anómalo | 500 | O₃ vs p90 / p25 |
| Vegetación densa | 500 | NDVI alto · BSI bajo |
| Suelo urbano | 500 | NDVI bajo · NDBI alto |

**Mostrar:** barras balance + 5 thumbnails RGB.

---

### Diapositiva 30 — Percentiles S5P (Cali, 5 años)

**Título:** Umbrales globales · `percentiles.json`

| Pollutant | p50 | p90 | p99 |
|-----------|-----|-----|-----|
| NO₂ | 2.40e-5 | 4.57e-5 | 8.56e-5 |
| SO₂ | 2.04e-4 | 5.90e-4 | 1.28e-3 |
| O₃ | 0.115 | 0.122 | 0.129 |

**Nota oral:** Ventana ±7 días S5P alrededor fecha S2 (`nanmax`).

**Mostrar:** tabla percentiles.

---

### Diapositiva 31 — Pipeline generación dataset

**Título:** `generar_dataset_sit2_*.py`

**Flujo (6 pasos en slide):**
1. Percentiles S5P desde GCS  
2. Barrido escenas S2 (Dask)  
3. Filtro SCL nube/claro  
4. NDVI · BSI · NDBI · `frac_built_up`  
5. `generar_descripcion` ES (+ v2 multilingüe)  
6. Split · `secuencias.json` · flush Zarr  

**v2:** score-based (no prioridad fija NO₂)

**Mostrar:** diagrama flujo simplificado.

---

### Diapositiva 32 — Archivos de salida

**Título:** `dataset_sit2/` + HuggingFace

| Archivo | Contenido |
|---------|-----------|
| `tiles.zarr` | (N, 13, 64, 64) int16 |
| `metadatos.parquet` | clase · texto · coords · exceso_* |
| `percentiles.json` | umbrales |
| `secuencias.json` | 30×8 tile_ids |
| HF `geovision-cali-sit2` | repro Colab/Kaggle |

**Split:** train 1593 · val 341 · test 342

**Mostrar:** `head()` parquet + shape zarr.

---

# BLOQUE 7 — MODELO (diapositivas 33–38)

### Diapositiva 33 — Objetivo Sit. 2 (modelo)

**Título:** GeoVision-CLIP + 2 SAE

- Alinear imagen S2 ↔ texto español
- Espacio contrastivo **256-d**
- SAE **512-d** disperso (interpretabilidad)
- RemoteCLIP = CLIP para teledetección

**Mostrar:** icono dos modales (imagen + texto).

---

### Diapositiva 34 — Arquitectura visual

**Título:** Rama imagen

```
Tile (13,H,W) → Conv 13→3 → ViT-B/32 RemoteCLIP
              → SAE_img (512) → proj → e_img ∈ R^256
```

- Init true-color: B4→R · B3→G · B2→B (SenCLIP)
- ViT mayormente congelado (fine-tune condicional)

**Mostrar:** diagrama rama superior.

---

### Diapositiva 35 — Arquitectura texto

**Título:** Rama texto

```
descripcion ES → MiniLM-L12 (384-d)
               → Linear → SAE_txt (512) → proj → e_txt ∈ R^256
```

- Tokenizer multilingüe · max 256 tokens
- Plantillas v2: ndbi · exceso_* · built-up

**Mostrar:** diagrama rama inferior + ejemplo texto.

---

### Diapositiva 36 — Función de pérdida

**Título:** InfoNCE + regularización SAE

```
L = L_InfoNCE(τ) + α·(L_SAE_img + L_SAE_txt)
L_SAE = MSE(x,x̂) + λ·mean(|z|)
τ learnable · α=0.1 · λ=1e-3
```

- InfoNCE bidireccional (img↔txt)
- Warmup: α=0 primeras épocas (solo contraste)

**Mostrar:** fórmula + pesos en tabla.

---

### Diapositiva 37 — Entrenamiento

**Título:** Cómo entrenamos

| Parámetro | Valor |
|-----------|-------|
| Framework | PyTorch Lightning |
| GPU | Kaggle T4/P100 · Colab A100 |
| Batch | 32–64 |
| Optimizer | AdamW 1e-4 |
| Notebook | `sit2_geovision_clip.ipynb` |
| Código lib | `src/training/lit_geovision.py` |

**Métricas/época:** loss · InfoNCE · sparsity · Recall@1/@5

**Mostrar:** curvas 2×2 del JSON épocas.

---

### Diapositiva 38 — Iteración híbrida (LoRA)

**Título:** Mejora en curso: CLIP híbrido

- **LoRA** rank 16 · bloques 6–11 ViT+texto
- **12 bandas** ópticas · conv1 multiespectral
- Prompts **ES+EN** (~10/clase)
- 2 fases: A solo InfoNCE → B fine-tune visual
- Sin SAE en loss (priorizar Recall)

**Mostrar:** tabla “antes vs después” arquitectura.

---

# BLOQUE 8 — RESULTADOS (diapositivas 39–43)

### Diapositiva 39 — KPIs: tabla honesta

**Título:** Consigna vs logrado (mejor época)

| KPI | Mín | Logrado | ✓/△ |
|-----|-----|---------|-----|
| Recall@1 | 0.45 | 0.11 | △ |
| Recall@5 | 0.70 | 0.24 | △ |
| Sparsity | 0.70 | 0.04 | △ |
| MSE SAE | ≤0.05 | 0.028 | ✓ |
| Pares | 1000 | 2276 | ✓ |

**Mostrar:** tabla semáforo (verde/amarillo).

---

### Diapositiva 40 — Curvas de entrenamiento

**Título:** ¿Qué dicen las curvas?

- **Train loss** → ~0.08: memorización
- **Val loss** mínima época **6** → luego sube (overfit)
- **Recall@1 val** → 0.11 plateau
- **MSE SAE** → cumple umbral desde ép. 7

**Mostrar:** 4 gráficos del notebook diagnóstico.

---

### Diapositiva 41 — Matriz de confusión

**Título:** ¿Qué clase separa mejor?

- **Vegetación:** 52% acierto intra-clase
- **NO₂:** 44% (texto con cifra NO₂ variable)
- **SO₂:** 28% (confunde con NO₂)
- Confusión fuerte: **urbano → NO₂** (15/40)

**Mostrar:** heatmap 5×5 coloreado.

---

### Diapositiva 42 — Tres causas raíz

**Título:** Diagnóstico (`INFORME_DIAGNOSTICO_SIT2.md`)

1. **Textos** casi idénticos por clase → embeddings texto colapsan  
2. **Leakage:** 100 escenas S2 en train∩val → Recall optimista  
3. **SAE lineal** sin ReLU → sparsity techo ~5%  

**Mejoras:** split por escena · filtros SCL · ReLU+λ · LoRA · prompts

**Mostrar:** tres iconos causa → flecha → fix.

---

### Diapositiva 43 — AFE / AFC (psicometría)

**Título:** Validez de constructo en embeddings

- **AFE:** PCA · scree · ≥80% varianza → m factores
- **AFC:** 4 constructos latentes  
  - Carga Antropogénica  
  - Estrés Vegetal  
  - Densidad Urbana  
  - Volatilidad Atmosférica  
- RMSEA · CFI · SRMR (`src/utils/psychometrics_embeddings.py`)

**Mostrar:** scree plot + tabla cargas (si disponible).

---

# BLOQUE 9 — APP Y CIERRE (diapositivas 44–48)

### Diapositiva 44 — Frontend Next.js

**Título:** App profesional (no Streamlit)

**Ruta:** `app/geo-vision-clip-application/`

- Next.js 16 · React 19 · Leaflet
- Modo oscuro (+2 pts bonificación)
- React Query · Zustand

**Mostrar:** screenshot landing + mapa.

---

### Diapositiva 45 — Funciones del mapa

**Título:** Experiencia de usuario

| Acción | Resultado |
|--------|-----------|
| Click mapa | Predicción en (lat, lon) |
| Selector | NO₂ · SO₂ · O₃ |
| Slider | T+1 · T+3 · T+7 |
| Hover polígono | Barrio + comuna |
| Toggle sidebar | Capas administrativas |

**Mostrar:** GIF o 3 capturas secuenciales.

---

### Diapositiva 46 — API y backend

**Título:** Contrato `/predict`

```json
{ "lat": 3.45, "lon": -76.53, "radius_km": 5,
  "pollutants": ["NO2","SO2","O3"],
  "horizons_days": [1,3,7] }
```

- Respuesta: valor · σ Kriging · URI grid
- `checkpoint_md5` en meta · latencia objetivo <8 s

**Mostrar:** snippet JSON request/response.

---

### Diapositiva 47 — Entregables ZIP

**Título:** Qué va en el .ZIP final

- [x] Notebooks ejecutados con outputs
- [x] Manifest MD5 · pipeline · `src/`
- [x] Checkpoint .pt verificable
- [x] Dockerfile · URL repo · URL deploy
- [ ] Informe PDF 15–25 páginas

**Mostrar:** checklist entrega consigna.

---

### Diapositiva 48 — Roadmap Sit. 3 + cierre

**Título:** Próximo paso: geoestadística

```
Embeddings → ConvLSTM → variograma → ST-Kriging
→ LOO-CV DAGMA → Moran + LISA → 9 mapas en app
```

**Cierre (1 frase):**  
Datos masivos listos · modelo multimodal en iteración · producto visible · validación rigurosa en camino.

**Mostrar:** diagrama Sit.3 del README + QR repo/app.

---

# ANEXO — Demo en vivo (4 min)

| Paso | Acción | Diapositiva ref. |
|------|--------|------------------|
| 1 | Abrir `#mapa` zoom Cali | 44–45 |
| 2 | Hover barrio → tooltip | 26, 45 |
| 3 | Click → panel predicción | 6, 45 |
| 4 | Cambiar NO₂→O₃ · T+1→T+7 | 45 |
| 5 | Toggle límites OFF/ON | 45 |
| 6 | Mencionar MD5 checkpoint | 47 |

---

# ANEXO — FAQ (1 diapositiva extra = 49)

| Pregunta | Respuesta (1 línea) |
|----------|-------------------|
| ¿Zarr vs Parquet? | Zarr = cubo ST; Parquet = metadatos por tile |
| ¿Etiqueta sin gas en S2? | Pseudo-label S5P percentiles Cali |
| ¿Recall bajo? | Textos + leakage + ViT congelado; mitigando |
| ¿66 GB cómo se verificó? | manifest.py suma size_bytes + MD5 |
| ¿Por qué regresión DAGMA? | Imputar huecos para validación Sit.3 |

---

# ANEXO — Rúbrica (diapositiva 50)

| Componente | Peso | Nuestro estado |
|------------|------|----------------|
| Panel Sit.1 | 20% | Fuerte |
| CLIP Sit.2 | 20% | Parcial · dataset ✓ |
| Geo Sit.3 | 30% | En desarrollo |
| Frontend | 10% | Avanzado |
| Informe | 10% | Pendiente |
| Pitch | 10% | Esta presentación |

---

## Tabla maestra: diapositiva → archivo a proyectar

| # | Archivo / evidencia |
|---|---------------------|
| 4, 6 | App mapa / DAGMA |
| 12–13 | `manifest.json` |
| 17 | Log Dask o `exportar.py --help` |
| 22–24 | Outputs notebooks Sit.1/EDAs |
| 25 | `PrediccionesNO2_SO2.ipynb` gráfico |
| 26 | `public/geo/barrios_cali.geojson` en app |
| 29–32 | `resumen.json` · tile RGB notebook |
| 37–40 | `metricas_por_epoca.json` · matrices |
| 44–45 | Screenshots app |

---

*42 diapositivas principales + 8 anexo · GeoVision-CLIP Cali · UAO 2026*
