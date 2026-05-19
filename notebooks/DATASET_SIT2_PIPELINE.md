# Guía del pipeline — `pipeline/generar_dataset_sit2_par_imagen_texto.py`

Este documento describe el script que construye el **dataset de pares imagen–texto** para la Situación 2 del proyecto (GeoVision-CLIP / Cali), incluyendo entradas, salidas, flujo de ejecución, conceptos fundamentales y las lecciones aprendidas tras el análisis diagnóstico.

---

## 0. Conceptos fundamentales antes de leer el código

Antes de entender cómo funciona el pipeline, es necesario tener claros tres conceptos que se usan en todo el documento: **escena**, **tile** y **muestra**. También es crucial entender la cadencia temporal de los satélites involucrados, porque de ella depende si el dataset tiene la variedad temporal necesaria para la Situación 3.

### 0.1 ¿Qué es una escena Sentinel-2?

Sentinel-2 es una constelación de dos satélites (S2A y S2B) en órbita polar a 786 km. Cada pasada captura una franja de 290 km de ancho. La **escena** (o *timestamp*) es una única imagen completa de la región de Cali tomada en un instante específico.

**Cadencia de revisita sobre Cali:**

| Combinación | Cada cuánto pasa |
|------------|-----------------|
| Solo S2A | ~10 días |
| Solo S2B | ~10 días |
| S2A + S2B combinados | **~5 días** (incluso 2–3 días en latitudes bajas) |

En el cubo Zarr del proyecto hay **1 463 timestamps** S2 que cubren el período 2019–2023 (~5 años). Eso es aproximadamente 290 escenas por año, o una cada 1.26 días hábiles en promedio. Sin embargo, **muchos de esos timestamps tienen alta cobertura de nubes** sobre Cali (zona tropical, lluvias frecuentes), por lo que el número real de escenas útiles (con menos del 30% de nubes) es bastante menor.

**Implicación para el dataset:** si el pipeline visita 450 escenas y extrae tiles de ellas, esas 450 escenas se distribuyen a lo largo de 5 años con repetición espacial en las mismas ubicaciones. Varios tiles distintos pueden venir de la misma escena (misma fecha, misma imagen satelital).

### 0.2 ¿Qué es un tile?

Un **tile** es un recorte de **64×64 píxeles** (= 640×640 m a la resolución de 10 m de las bandas principales de S2) extraído de una escena. Contiene las **13 bandas** de S2 L2A (B1–B12 + SCL).

La posición del recorte dentro de la escena se define por `(yi, xi)`: los píxeles de origen en la grilla original. El identificador único del tile es:

```
tile_id = "{img_id_s2}__y{yi:04d}__x{xi:04d}"
```

Por ejemplo: `20210617T152639_20210617T153208_T18NUJ__y2848__x3104`

Un solo tile representa un área de ~0.41 km². La región metropolitana de Cali tiene aproximadamente 564 km², lo que significa que caben ~1 376 tiles sin solapamiento. Con el stride de 32 píxeles (no 64), hay solapamiento del 50% entre tiles vecinos, lo que aumenta la densidad de muestras por escena.

**Relación tile–escena:**
- 1 escena → muchos tiles (hasta 40 en el pipeline con `--max-tiles-por-escena 40`).
- 1 tile → pertenece exactamente a 1 escena.
- El mismo **lugar geográfico** en diferentes fechas → tiles distintos con el mismo `(yi, xi)` pero diferente `img_id_s2`.

### 0.3 ¿Qué es una "muestra" en el dataset?

En el contexto de GeoVision-CLIP (Situación 2), una **muestra** es un **par (imagen, texto)**:

- **Imagen:** el array NumPy del tile, shape `(13, 64, 64)`, normalizado al cargar.
- **Texto:** la `descripcion` en español generada por `generar_descripcion()`.

La **clase** del par (NO2, SO2, ozono, vegetación, suelo) se asigna según las reglas de `asignar_clase()` usando los valores S5P del centroide del tile en la fecha de la escena.

Un par es **válido** si pasa el filtro SCL de nubes y si `asignar_clase()` retorna una clase (no `None`).

### 0.4 ¿Los tiles deben ser de tiempos parecidos?

**Depende del uso:**

**Para Situación 2 (GeoVision-CLIP, retrieval imagen–texto):**
No es estrictamente necesario que los tiles vengan de períodos cercanos entre sí. Lo que importa es que cada par (imagen, texto) sea coherente: la imagen muestre lo que el texto describe. La variedad temporal es incluso deseable para que el modelo aprenda a distinguir la clase independientemente de la estación del año.

**Para Situación 3 (ConvLSTM, predicción temporal):**
Aquí sí importa la coherencia temporal. El ConvLSTM recibe secuencias de 8 embeddings consecutivos del **mismo lugar geográfico** en fechas sucesivas. Para que la secuencia tenga sentido físico:
- Los 8 tiles deben cubrir el **mismo centroide** (mismo `(yi, xi)` aproximado).
- Las fechas deben estar **ordenadas temporalmente** con saltos razonables (el pipeline permite hasta 90 días entre fechas consecutivas de la secuencia, definido como `max_gap_dias`).
- No tiene sentido mezclar en una secuencia un tile de enero de 2019 con uno de agosto de 2022 sin los intermedios.

El pipeline ya genera estas secuencias en `generar_secuencias_temporales()` y las guarda en `secuencias.json`. Son exactamente lo que Situación 3 necesita como input.

### 0.5 Cadencia de Sentinel-5P

Sentinel-5P (TROPOMI) tiene resolución temporal diaria y cobertura global. Sin embargo:

- La resolución **espacial** es ~3.5 × 5.5 km (mucho más gruesa que S2).
- Puede haber días sin datos sobre Cali por nubes densas a nivel estratosférico o problemas de la órbita.
- El pipeline agrega todas las órbitas de una ventana de ±7 días alrededor de la fecha S2 y toma el `nanmax` espacial para componer un mapa 2D por fecha S2 (`_AccesoS5P.mapas_2d_para_fecha`).

**Consecuencia importante:** un tile de S2 del 15 de julio de 2021 usa el valor S5P más alto encontrado entre el 8 y el 22 de julio de ese año sobre ese centroide. Eso maximiza la cobertura (menos NaN) pero puede introducir sesgo: el valor S5P puede no corresponder exactamente al día de la imagen.

---

## 1. Objetivo del script

Generar un conjunto de **pares (imagen, texto)** donde:

- **Imagen**: recorte (*tile*) de Sentinel-2 L2A de **64×64 píxeles** y **13 bandas** (incluye SCL).
- **Texto**: descripción en español derivada de la clase pseudo-supervisada y de magnitudes (NO₂, SO₂, O₃, NDVI, BSI, fecha, coordenadas).

Además:

- Pseudo-etiquetas con **percentiles globales** de Sentinel-5P (NO₂, SO₂, O₃) sobre la región.
- **Split** 70% train / 15% val / 15% test.
- **Secuencias temporales** de longitud configurable (8 fechas por defecto) para forecasting (Situación 3).

---

## 2. Entradas (input)

### 2.1 Configuración y credenciales

- `pipeline/config.py`: define `PROJECT_GCP`, `BUCKET` (p. ej. `geovision-cali`), `FUENTES` y el prefijo Zarr de cada fuente.
- **Google Cloud**: el script lee Zarr en GCS mediante `gcsfs`. Hace falta autenticación ADC con permisos de lectura al bucket.

### 2.2 Datos remotos (Zarr en GCS)

| Uso en el script | Prefijo (`config.FUENTES`) | Contenido relevante |
|-----------------|---------------------------|---------------------|
| Escenas Sentinel-2 | `Sentinel2` | Variable `data`: `(time, band, y, x)` con 13 bandas. |
| NO₂ | `Sentinel5P/NO2` | `data` banda 0: columna troposférica L3. |
| SO₂ | `Sentinel5P/SO2` | Igual, banda 0. |
| O₃ | `Sentinel5P/O3` | Igual, banda 0. |

### 2.3 Parámetros de línea de comandos (CLI)

| Flag | Default | Descripción |
|------|---------|-------------|
| `--meta-objetivo` | 1500 | Número objetivo de pares aceptados. |
| `--max-timestamps-s2` | 1463 | Máximo de índices temporales S2 a visitar. |
| `--max-tiles-por-escena` | 40 | Máximo de tiles candidatos por escena. |
| `--stride-pix` | 32 | Paso en píxeles entre orígenes de tiles. |
| `--cap-por-clase` | 250 | Tope de pares por clase. |
| `--min-por-clase` | 10 | Mínimo de pares por clase para parar. |
| `--paciencia-escenas` | 80 | Escenas seguidas sin par nuevo antes de abortar. |
| `--n-secuencias` | 30 | Objetivo de secuencias temporales. |
| `--longitud-secuencia` | 8 | Longitud de cada secuencia (fechas). |
| `--salida-local` | `dataset_sit2` | Directorio local de salida. |
| `--dask-workers` | 0 | Si > 0, evalúa tiles en paralelo con Dask. |
| `--zarr-flush-every` | 128 | Tiles entre volcados a disco. |
| `--max-frac-nubes` | 0.30 | Máxima fracción SCL nube/sombra/cirrus. |
| `--min-frac-claros` | 0.10 | Mínima fracción SCL "claros". |
| `--sin-filtro-scl` | off | Desactiva el filtro SCL. |

**Constantes en código** (no son flags): `SEED=42`, `TILE_PIX=64`, `MAX_DT_DIAS=7`, umbrales NDVI/BSI.

---

## 3. Salidas (output)

| Archivo | Descripción |
|---------|-------------|
| `tiles.zarr/` | Array `(N, 13, 64, 64)`, `dtype=int16`. Atributos: `bandas`, `tile_pix`, `tile_ids`. |
| `metadatos.parquet` | Una fila por par; columnas detalladas en §7. |
| `percentiles.json` | Umbrales p25/p50/p75/p90/p99 por contaminante. |
| `secuencias.json` | Lista de secuencias temporales para Sit. 3. |
| `resumen.json` | Metadatos agregados: conteos, balance, bandas, percentiles. |

---

## 4. Flujo de ejecución

```
inicio
  └─ calcular percentiles globales (NO2, SO2, O3 sobre toda la región)
  └─ construir_dataset
       └─ por cada escena S2 (orden aleatorio, SEED=42):
            └─ cargar cubo S2 (time, band, y, x)
            └─ componer mapas S5P 2D para esa fecha (±7 días)
            └─ por cada tile candidato (stride, max_tiles):
                 └─ filtrar por SCL (nubes, claros)
                 └─ calcular NDVI, BSI (solo píxeles claros)
                 └─ obtener NO2, SO2, O3 del centroide
                 └─ asignar_clase → registro o descarte
  └─ split_estratificado (70/15/15)
  └─ generar_secuencias_temporales
  └─ guardar_dataset_local
```

---

## 5. Alineación imagen–metadatos

La fila `i` de `metadatos.parquet` corresponde exactamente a la fila `i` del eje `N` en `tiles.zarr`. El orden está garantizado por la variable `tile_ids` en los atributos del Zarr, que se construye en el mismo orden que el DataFrame.

---

## 6. El problema del split actual y por qué importa

### 6.1 Split por tile (comportamiento actual)

La función `split_estratificado()` aplica `train_test_split` directamente sobre las filas del DataFrame, estratificando por **clase**. El resultado es:

```
total filas → 70% train, 15% val, 15% test
```

El problema es que esta división no tiene en cuenta que **múltiples tiles pueden provenir de la misma escena S2** (misma imagen satelital, misma fecha). Cuando eso ocurre, parte de los tiles de esa escena van a train y parte van a val.

**Ejemplo concreto (dataset 1 350 tiles verificado):**
- Fechas compartidas train ∩ val: **98 fechas**.
- Escenas S2 compartidas train ∩ val: **100 escenas**.

Esto significa que el 100% de las escenas del val también tienen tiles en train. El modelo puede memorizar la apariencia visual de esa escena (iluminación del día, distribución de nubes residuales, estación del año) durante el entrenamiento y recuperarla en validación. El Recall@1 observado (11.4%) puede estar inflado respecto al rendimiento real en escenas completamente nuevas.

### 6.2 ¿Por qué ocurre?

El pipeline procesa escenas en orden aleatorio y extrae hasta 40 tiles por escena. Cuando hay tiles de diferentes clases dentro de la misma escena (lo cual es frecuente: una imagen puede tener zonas verdes, zonas urbanas y zonas afectadas por NO2 simultáneamente), `train_test_split` puede poner algunos de esos tiles en train y otros en val.

### 6.3 Split por escena (R-D1 del informe — recomendado)

La corrección lógica es asignar el split **antes de dividir tiles**, a nivel de escena:

```
1. Obtener lista única de img_id_s2 (todas las escenas del dataset).
2. Separar esas escenas en: train_escenas (70%), val_escenas (15%), test_escenas (15%).
3. Cada tile hereda el split de la escena a la que pertenece.
```

Con este enfoque, **ninguna imagen satelital aparece en dos splits**. El modelo en validación siempre evalúa sobre fechas e imágenes que nunca vio durante el entrenamiento.

**¿Cuándo es aceptable el split actual?**
Si el propósito es solo cumplir la consigna académica y el diagnóstico indica que el modelo aprende (Recall 25× sobre el azar), el split por tile es funcional. La inflación es parcial y el modelo sí aprende algo. Sin embargo, para publicar o comparar con otros modelos, el split por escena es el estándar correcto en visión por satélite.

**¿Se pierde balance de clases con el split por escena?**
Sí, algo. Si una escena tiene solo tiles de vegetacion y cae entera en val, esa clase tendrá menos tiles en val. Esto se mitiga con más escenas diversas (`--cap-por-clase` más alto, más `--paciencia-escenas`). En el dataset actual (1 350 tiles de 450 escenas), con ~3 tiles por escena en promedio, el impacto es moderado.

---

## 7. Esquema de columnas en `metadatos.parquet`

| Columna | Tipo | Significado |
|---------|------|-------------|
| `tile_id` | string | ID único: `{img_id_s2}__y{yi}__x{xi}` |
| `clase` | string | Una de `CLASES`. |
| `descripcion` | string | Texto del par (español). |
| `fecha` | string | Fecha de la escena S2 (YYYY-MM-DD). |
| `img_id_s2` | string | Identificador crudo del timestamp S2. |
| `centroide_lat`, `centroide_lon` | float | Centro del tile en grados. |
| `yi`, `xi` | int | Origen del recorte en la grilla S2. |
| `valid_ratio` | float | Fracción de valores finitos en el tile bruto. |
| `frac_nubes_scl`, `frac_claros_scl`, `frac_nodata_scl` | float | Métricas SCL del tile. |
| `ndvi`, `bsi` | float | Índices espectrales (medias sobre píxeles claros). |
| `no2`, `so2`, `o3` | float | Valores S5P en el centroide. |
| `split` | string | `train` / `val` / `test`. |

La columna `img_id_s2` permite implementar el **split por escena** (R-D1) en postproceso sobre el parquet ya generado, sin necesidad de volver a descargar las imágenes.

---

## 8. Relación con Situación 3 (ConvLSTM)

La Situación 3 requiere predicción espacio-temporal de contaminantes. El pipeline Sit. 2 sienta las bases en dos formas:

### 8.1 Las secuencias de `secuencias.json`

El archivo contiene listas de tiles del mismo **lugar geográfico** (misma celda espacial de ~0.1° × 0.1°) en fechas consecutivas. Cada entrada tiene:

```json
{
  "celda_lat": 3.40,
  "celda_lon": -76.30,
  "longitud": 8,
  "tile_ids": ["20190104...", "20190112...", ...],
  "fechas": ["2019-01-04", "2019-01-12", ...]
}
```

El ConvLSTM de Sit. 3 consumes estas secuencias: pasa los 8 tiles por GeoVision-CLIP+SAE para obtener embeddings de 256D por tile, los reorganiza en grilla espacial y los procesa temporalmente.

**Por eso la cadencia de S2 importa:** si entre dos fechas consecutivas de la secuencia hay más de 90 días (`max_gap_dias=90`), el pipeline no las conecta. Con la revisita de ~5 días de S2, en teoría hay ~18 tiles disponibles por lugar en 90 días. En la práctica, las nubes sobre Cali reducen esto a 4–8 tiles claros por trimestre.

### 8.2 ¿Los tiles deben ser de tiempos parecidos para entrenar el modelo de Sit. 2?

**No necesariamente.** Para el contrastive learning de Sit. 2, la diversidad temporal es buena: el modelo aprende que "vegetación densa" se ve verde independientemente de si la imagen es de enero o de agosto. Lo que importa es que **cada par individual** (tile, descripción) sea coherente, no que los pares entre sí sean de fechas cercanas.

Sin embargo, hay un caso donde la temporalidad sí importa en Sit. 2: si la clase es `ozono_anomalo` o `contaminacion_alta_NO2`, los valores S5P son estacionales. El ozono troposférico en Cali tiene variaciones anuales de ~10%, lo que significa que un valor "anómalo" en enero puede ser "normal" en agosto. Los percentiles globales del pipeline (`percentiles_globales_cali.json`) se calculan sobre 2019–2023, por lo que capturan la variación anual y son un umbral robusto.

### 8.3 Pipeline de inferencia en Sit. 3

```
INPUT: (lat, lon) + radio + contaminante
  └─ Generar grilla N×N de puntos
  └─ Por cada punto: recuperar tile S2 (última imagen clara disponible)
                     + serie S5P histórica (últimas 8 fechas con datos)
  └─ Pasar cada tile por GeoVision-CLIP+SAE → embedding 256D
  └─ Organizar secuencia (8 × 256D) por punto → tensor (N×N, 8, 256)
  └─ Reshape a grilla espacial → (8, H, W, 256)
  └─ ConvLSTM bidireccional → predicción (3 horizontes × 3 contaminantes)
  └─ ST-Kriging sobre residuos → superficie + incertidumbre
OUTPUT: 9 mapas de gradiente + mapas de varianza Kriging
```

El GeoVision-CLIP entrenado en Sit. 2 actúa como **extractor de características** para Sit. 3. Por eso la calidad del modelo de Sit. 2 tiene impacto directo en la capacidad predictiva de Sit. 3.

---

## 9. Lecciones del análisis diagnóstico (estado actual del dataset)

Tras ejecutar los estudios del EDA (§2b del notebook), los hallazgos relevantes para quien regenere el dataset son:

| Hallazgo | Causa en el pipeline | Cómo mitigarlo |
|----------|---------------------|----------------|
| 100 escenas S2 en train Y val (leakage) | `split_estratificado` opera sobre tiles, no escenas | Agrupar por `img_id_s2` antes de dividir |
| ~4.5% tiles con imagen casi negra | `max_frac_nubes=0.30` demasiado permisivo | Bajar a 0.15, subir `min_frac_claros` a 0.50 |
| `ozono_anomalo` alto y bajo tienen texto idéntico | `generar_descripcion` usa base fija por clase | Añadir subtipo en `asignar_clase` y texto diferenciado |
| ~38 tiles con clase inconsistente con visual | Resolución S5P 3.5 km > tile 640 m | Inherente al sensor; documentar, no corregir |
| Textos no discriminativos entre instancias | `generar_descripcion` solo varía números | Añadir cobertura `frac_built_up`, magnitud relativa |

---

## 10. Flujo de construcción por secciones del código

### 10.1 `calcular_percentiles_globales`

1. Por cada contaminante, abre el Zarr y muestrea espacialmente.
2. Filtra valores finitos; para NO₂ y SO₂ usa solo valores **> 0** (los ceros son "sin retrieval", no físicos).
3. Calcula percentiles 25, 50, 75, 90, 99 y los escribe en `percentiles.json`.

### 10.2 `asignar_clase`

Prioridad estricta (la primera regla que se cumple determina la clase):

1. `contaminacion_alta_NO2` si NO₂ ≥ p90(NO₂).
2. `contaminacion_alta_SO2` si SO₂ ≥ umbral SO₂.
3. `ozono_anomalo` si O₃ ≥ p90(O₃) **o** O₃ ≤ p25(O₃).
4. `vegetacion_densa` si NDVI ≥ 0.45 y `frac_built_up` < 0.15.
5. `suelo_urbano` si NDVI ≤ 0.35 y BSI ≥ 0.02, o `frac_built_up` ≥ 0.15.
6. `None` → tile descartado.

### 10.3 `generar_descripcion`

Texto fijo por clase con interpolación de fecha, lat/lon, NDVI, BSI, NO₂, SO₂, O₃. La descripción base es idéntica para todos los tiles de la misma clase; la única variación son los valores numéricos.

### 10.4 `split_estratificado`

- 70% train / 30% temporal → 15% val + 15% test.
- `stratify=clase` en ambos pasos si hay suficientes ejemplos; fallback sin estratificar.
- **Limitación conocida (R-D1):** no agrupa por `img_id_s2`; ver §6.

### 10.5 `generar_secuencias_temporales`

- Agrupa tiles por celda espacial (redondeada a 0.10°).
- Busca ventanas deslizantes de longitud `longitud` donde las fechas estén en orden y con salto ≤ 90 días.
- No reutiliza un `tile_id` en más de una secuencia.
- Objetivo: 30 secuencias de 8 tiles.

---

## 11. Comandos de referencia

Solo percentiles:
```powershell
python -u pipeline\generar_dataset_sit2_par_imagen_texto.py --solo-percentiles --salida-local dataset_sit2
```

Dataset v2 (filtro SCL más estricto, recomendado):
```powershell
python -u pipeline\generar_dataset_sit2_par_imagen_texto.py `
  --meta-objetivo 1500 `
  --max-timestamps-s2 1463 `
  --max-tiles-por-escena 40 `
  --stride-pix 32 `
  --cap-por-clase 500 `
  --min-por-clase 20 `
  --paciencia-escenas 120 `
  --dask-workers 4 `
  --max-frac-nubes 0.15 `
  --min-frac-claros 0.50 `
  --zarr-flush-every 128 `
  --salida-local dataset_sit2_v2
```

Dataset original (usado en el entrenamiento actual):
```powershell
python -u pipeline\generar_dataset_sit2_par_imagen_texto.py `
  --meta-objetivo 1500 `
  --max-timestamps-s2 1463 `
  --max-tiles-por-escena 40 `
  --stride-pix 32 `
  --cap-por-clase 1000 `
  --min-por-clase 20 `
  --paciencia-escenas 80 `
  --dask-workers 4 `
  --max-frac-nubes 0.30 `
  --min-frac-claros 0.10 `
  --zarr-flush-every 128
```

Con subida al bucket:
```powershell
python -u pipeline\generar_dataset_sit2_par_imagen_texto.py `
  --salida-local dataset_sit2 `
  --subir-a-gcs `
  --prefijo-gcs datasets/sit2
```

---

## 12. Referencia rápida de símbolos del código

| Símbolo | Rol |
|---------|-----|
| `_abrir_zarr` | Lectura remota de paneles desde GCS. |
| `calcular_percentiles_globales` | Umbrales pseudo-supervisados. |
| `_AccesoS5P` | Mapas 2D compuestos por fecha S2 (±7 días, nanmax). |
| `asignar_clase` | Reglas de pseudo-etiqueta con prioridad. |
| `generar_descripcion` | Texto en español por par. |
| `_procesar_tile_candidato` | Evalúa un tile: filtros → índices → clase → registro. |
| `IncrementalTilesZarr` | Escritura incremental de tiles sin acumular en RAM. |
| `iter_tiles_escena` | Muestreo espacial con stride dentro de una escena. |
| `construir_dataset` | Bucle principal: escenas → tiles → pares. |
| `split_estratificado` | Divide el DataFrame en train/val/test (por tile actualmente). |
| `generar_secuencias_temporales` | Secuencias ordenadas por lugar y fecha para Sit. 3. |
| `guardar_dataset_local` | Escribe parquet, Zarr, JSON. |
| `subir_dataset_gcs` | Copia opcional a GCS. |

---

*Documento actualizado: 2026-05-18. Refleja el análisis diagnóstico del entrenamiento GeoVision-CLIP Sit. 2 y las recomendaciones de regeneración del dataset.*
