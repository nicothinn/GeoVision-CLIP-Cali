# GeoVision-CLIP Cali — Exposición 14 diapositivas

**Duración sugerida:** 12–14 min + 3 min demo  
**Versión corta de:** [`EXPOSICION_SIT1_SIT2.md`](EXPOSICION_SIT1_SIT2.md) (guía ampliada ~42 diapos)

---

## Diapositiva 1 — Portada

**GeoVision-CLIP Cali**  
Contaminación atmosférica en puntos no muestreados · Deep Learning + geoestadística

Analítica de Datos I · Tercer Corte · UAO · Grupo [nombres]

**Mostrar:** logo UAO + captura mapa app (modo oscuro).

---

## Diapositiva 2 — Mensaje y agenda

**En 20 segundos:**  
Integramos **≥66 GB** de satélites en la nube, **2 276** pares imagen–texto y **GeoVision-CLIP**; la app **Next.js** ya muestra Cali con barrios; **Sit. 3** cerrará con ConvLSTM, Kriging y validación DAGMA.

| # | Tema | Peso consigna |
|---|------|---------------|
| 1 | Panel cloud ≥50 GB | Sit. 1 · 20% |
| 2 | Dataset + CLIP multimodal | Sit. 2 · 20% |
| 3 | App + roadmap geoestadística | Sit. 3 + deploy · 50% |

---

## Diapositiva 3 — Problema: Cali y DAGMA

**Cali:** ~2.8 M hab. · tráfico · industria Valle · quemas · Res. 2254/2017 (NO₂, SO₂, O₃)

**DAGMA — ground truth:** 9 estaciones · mediciones horarias · Sur / Centro / Oeste / Norte

**Brecha:** los sensores son **puntuales**; necesitamos estimar en **cualquier** (lat, lon) con **σ**.

**Mostrar:** mapa 9 estaciones + región Valle.

---

## Diapositiva 4 — Satélites y pregunta

| Sensor | Rol | Resolución |
|--------|-----|------------|
| **Sentinel-5P** | Gases columna (etiqueta) | ~3.5×5.5 km |
| **Sentinel-2** | Contexto superficie (imagen) | 10 m |

**Pregunta:** ¿NO₂, SO₂ y O₃ en cualquier punto con incertidumbre, horizontes T+1/3/7, solo datos gratuitos + validación DAGMA?

**Regla anti-leakage:** S5P **etiqueta** tiles en entrenamiento; **no** entra crudo al predictor final (−25% si se viola).

**Mostrar:** S5P grueso vs S2 fino + click mapa en app.

---

## Diapositiva 5 — Arquitectura del proyecto

```
SIT.1  Ingeniería datos   →  panel ≥50 GB · EDA · manifest
SIT.2  Deep Learning      →  GeoVision-CLIP · retrieval
SIT.3  Geoestadística     →  ConvLSTM · Kriging · Moran · LOO-CV DAGMA
```

**Flujo:** `GEE/GCS → ETL Dask → tiles + parquet → GPU → checkpoint → FastAPI → Next.js`

**Stack:** GCS · Zarr · Dask · PyTorch Lightning · open_clip · **Next.js** · Leaflet

**Mostrar:** diagrama tres cajas + flecha end-to-end.

---

## Diapositiva 6 — Sit. 1: panel cloud cumplido

| Requisito consigna | Logrado |
|--------------------|---------|
| ≥50 GB · 5 años · BBox Cali | **66.78 GB** (133.5%) |
| S5P + S2 + ERA5 + MODIS + DAGMA | **283 437** archivos |
| Manifest MD5 · EDA ≥8 figuras | ✓ · 12+ notebooks |

**Volumen:** Sentinel-2 ≈ **99.4%** del peso → cloud + Dask obligatorios.

**GCP:** `proyecto3ia-494900` · bucket `geovision-cali`

**Mostrar:** barras por fuente o `manifest.json`.

---

## Diapositiva 7 — Pipeline y trazabilidad

```
exportar.py → convertir_zarr.py → validar_zarr.py → manifest.py
                              ↓
                    generar_dataset_sit2_v2.py
```

- **Dask:** descarga paralela GEE → GCS · retry · MD5 por archivo  
- **Zarr:** cubo `(time, band, y, x)` lazy · chunks por región  
- **`runs/`:** cada corrida con `log.txt` + `eventos.jsonl`

**Mostrar:** diagrama 5 cajas + captura carpeta `runs/`.

---

## Diapositiva 8 — EDAs y contexto urbano

**Exploración antes de entrenar:** cobertura nubes · percentiles S5P Cali · huecos DAGMA · filtros SCL

| Notebook | Aporte |
|----------|--------|
| S5P | Series · mapas · **percentiles.json** |
| S2 | NDVI · SCL · motiva tiles 64×64 |
| ERA5 / MODIS | Meteo · AOD (Sit. 3) |
| DAGMA | 9 estaciones · imputación series |

**App:** **339 barrios** · 22 comunas · GeoJSON en mapa

**Mostrar:** collage 2 gráficos + mapa con polígonos.

---

## Diapositiva 9 — Sit. 2: dataset multimodal

| Métrica | Consigna | Logrado |
|---------|----------|---------|
| Pares imagen–texto | ≥1 000 | **2 276** |
| Secuencias 8 fechas | ≥30 | **30** |
| Clases | 5 | 5 balanceadas |

**Tile:** 64×64 px · **13 bandas** · `tile_id` por escena S2  
**Clases:** NO₂ alto · SO₂ alto · ozono anómalo · vegetación densa · suelo urbano  
**Split:** train 1593 · val 341 · test 342 · **por `img_id_s2`** (sin leakage)

**Salida:** `tiles.zarr` · `metadatos.parquet` · HF `geovision-cali-sit2`

**Mostrar:** tabla clases + thumbnail RGB.

---

## Diapositiva 10 — GeoVision-CLIP (Sit. 2 modelo)

**Objetivo:** alinear imagen Sentinel-2 ↔ texto rico en **español/inglés** (InfoNCE)

**Dos experimentos en paralelo:**

| Notebook | Texto | Visual |
|----------|-------|--------|
| `notebookresultados_Cliptexto` | RemoteCLIP + CLIP nativo | ViT + LoRA + **VisualProj** |
| `notebookresultados_XLM-roberta` | **XLM-RoBERTa** (open_clip, ES) | ViT + LoRA |

**Común:** conv1 **12 bandas** · LoRA rank 16 · captions con magnitud + estación + contexto urbano + NDVI verbalizado  
**Pérdida:** InfoNCE simétrico · checkpoint por **val/recall_at_1**

**Papers guía:** SkyScript · GeoRSCLIP · Rethinking RS-CLIP · RS-CLIP → [`sit_2_clip/README.md`](papersglobales/sit_2_clip/README.md)

**Mostrar:** diagrama imagen ↔ texto (sin SAE).

---

## Diapositiva 11 — Resultados y diagnóstico

| KPI (val) | Meta | Mejor corrida |
|-----------|------|---------------|
| Recall@1 | 0.45 | **~0.11** △ |
| Recall@5 | 0.70 | **~0.24** △ |
| Pares dataset | 1000 | **2276** ✓ |

**Causas raíz (mitigadas en notebooks nuevos):**
1. Textos poco discriminativos → **diversidad de captions** (MAGNITUDE, estación, urbano)  
2. Leakage por escena → **split por `img_id_s2`**  
3. ViT muy congelado → **LoRA** + descongelado condicional  

**Mostrar:** tabla semáforo + curva Recall@1.

---

## Diapositiva 12 — App Next.js (no Streamlit)

**Ruta:** `app/geo-vision-clip-application/`

- Next.js · Leaflet · modo oscuro  
- Click mapa → predicción (lat, lon) · selector NO₂/SO₂/O₃  
- Horizontes T+1 · T+3 · T+7 · hover **barrio/comuna**

**API:** `POST /predict` → valor · σ · grid URI · `checkpoint_md5`

**Mostrar:** 2 screenshots (mapa + panel predicción).

---

## Diapositiva 13 — Sit. 3 y entregables

**Próximo paso:**
```
Embeddings → ConvLSTM → variograma → ST-Kriging
→ LOO-CV en 9 estaciones DAGMA → Moran/LISA → mapas en app
```

**ZIP consigna:** notebooks con outputs · manifest · pipeline · `src/` · checkpoint · Dockerfile · URL deploy  
**Pendiente:** informe PDF 15–25 páginas

**Mostrar:** diagrama Sit. 3 + checklist entrega.

---

## Diapositiva 14 — Cierre y rúbrica

**Una frase:**  
Datos masivos listos · modelo multimodal en iteración activa · producto visible en producción · validación geoestadística rigurosa en camino.

| Componente | Peso | Estado |
|------------|------|--------|
| Panel Sit. 1 | 20% | **Fuerte** |
| CLIP Sit. 2 | 20% | Dataset ✓ · métricas en mejora |
| Geo Sit. 3 | 30% | En desarrollo |
| Frontend | 10% | **Avanzado** |
| Informe + pitch | 20% | En curso |

**Demo (3 min):** mapa → hover barrio → click predicción → cambiar contaminante y horizonte.

**Mostrar:** QR repo / URL app + logo UAO.

---

## Anexo — qué proyectar por diapositiva

| # | Evidencia |
|---|-----------|
| 1, 12 | Screenshots app |
| 4 | Mapa DAGMA o demo click |
| 6 | `manifest.json` / gráfico fuentes |
| 7 | Diagrama pipeline · `runs/` |
| 8 | Outputs EDA · barrios GeoJSON |
| 9 | `resumen.json` · tile RGB |
| 10 | Diagrama CLIP · captura Colab entrenando |
| 11 | `metricas_por_epoca.json` |
| 13 | README roadmap Sit. 3 |

---

*14 diapositivas · GeoVision-CLIP Cali · UAO 2026*
