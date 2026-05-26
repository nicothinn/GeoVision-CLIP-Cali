# Contexto Completo: GeoVision-CLIP Cali -- Situacion 3

## Descripcion del proyecto

Prediccion espacio-temporal de NO2, SO2 y O3 en Cali, Colombia usando secuencias de embeddings visuales generados por un modelo CLIP de teledeteccion (RemoteCLIP) fine-tuned con LoRA para clasificacion de cobertura del suelo (Situacion 2). Ahora en Situacion 3 buscamos predecir concentraciones futuras de estos contaminantes a 1, 3 y 7 dias usando redes neuronales.

---

## Parte 1: Situacion 2 (completada) -- Generacion de embeddings

### Que hicimos en Situacion 2

Entrenamos un modelo RemoteCLIP (ViT-B/32) con LoRA para clasificar parches de Sentinel-2 en 5 clases de cobertura del suelo sobre Cali, Colombia.

**Dataset:** 2263 pares imagen-texto (tiles Sentinel-2 de 64x64 con 12 bandas).

**Modelo:**
- RemoteCLIP `chendelong/RemoteCLIP` congelado + LoRA rank=8 desde bloque 6
- `conv1` adaptado de 3 a 12 canales para aceptar las 12 bandas de Sentinel-2
- Label smoothing 0.1, cosine LR scheduler, 20 epochs
- **R@1 final: 47.65%** (KPI >= 45% -- CUMPLIDO)

**SAE (Sparse Autoencoder) post-entrenamiento:**
- Arquitectura: `Linear(512, 2048, bias=False) + ReLU + Linear(2048, 512, bias=False)`
- 2.1M parametros, 8000 epochs, lambda_L1 adaptativo
- **Sparsity: 94.1%, MSE: 1e-6** (ambos KPIs cumplidos)

### Embeddings extraidos para Situacion 3

Del modelo fine-tuneado de Situacion 2 extrajimos dos tipos de embeddings:

#### Embeddings planos (por tile)
- Cada tile Sentinel-2 (64x64) pasa por el visual encoder de RemoteCLIP
- Se obtiene un vector L2-normalizado de **512 dimensiones** por tile
- Shape: **(2263, 512)**
- Guardado como `visual_512.pt` y luego `embeddings_sit2.npz`

#### Grid embeddings (por sub-parche)
- Cada tile de 64x64 se divide en una grilla **5x5 = 25 parches**
- Cada parche se procesa INDEPENDIENTEMENTE por RemoteCLIP
- Se obtienen **25 embeddings de 512-d** por tile
- Shape: **(2263, 25, 512)**
- Guardado como `visual_512_grid.pt` y `embeddings_grid_sit2.npz`

### Archivos de embeddings disponibles localmente

| Archivo | Shape | Descripcion |
|---------|-------|-------------|
| `embeddings/embeddings_sit2.npz` | (2263, 512) | Embeddings planos + labels + splits |
| `embeddings/grid_embeddings_sit2.npz` | (2263, 25, 512) | Grid embeddings 5x5 |
| `embeddings/visual_512.pt` | (2263, 512) | Embeddings raw en torch |
| `embeddings/visual_512_grid.pt` | (2263, 25, 512) | Grid raw en torch |
| `embeddings/sae_latent_512.pt` | (2263, 2048) | Latentes SAE (opcionales) |

---

## Parte 2: Situacion 3 -- Generacion del tensor espacio-temporal

### Pipeline de generacion

Usando el script `pipeline/generar_tensor_convlstm.py`:

**Paso 1: Agrupacion espacial**
- Los 2263 tiles se agrupan por celda de 0.05 grados (~5.6 km en Cali)
- Esto genera ~90-100 celdas espaciales unicas

**Paso 2: Ventanas deslizantes temporales**
- Dentro de cada celda, los tiles se ordenan por fecha
- Ventana deslizante de 8 fechas consecutivas (stride=1)
- Cada ventana produce 1 muestra

**Paso 3: Construccion del tensor X**

```
X shape: (1403, 8, 522, 5, 5)
          ^     ^   ^   ^
          |     |   |   +-- grilla espacial 5x5
          |     |   +------ 522 canales por punto de grilla
          |     +---------- 8 timesteps (secuencia temporal)
          +---------------- 1403 muestras
```

**Desglose de los 522 canales para CADA punto de la grilla 5x5:**

| Canales | Dimension | Contenido |
|---------|-----------|-----------|
| 0-511 | 512 | Embedding CLIP (propio de cada punto de grilla si hay grid embeddings, o replicado) |
| 512 | 1 | `sin(2*pi*doy/365.25)` |
| 513 | 1 | `cos(2*pi*doy/365.25)` |
| 514 | 1 | `sin(2*pi*mes/12)` |
| 515 | 1 | `cos(2*pi*mes/12)` |
| 516 | 1 | `(lat - 3.45) / 0.1` |
| 517 | 1 | `(lon + 76.5) / 0.1` |
| 518 | 1 | gap temporal `(dias/30)` clamp 5.0 |
| 519 | 1 | NDVI |
| 520 | 1 | BSI |
| 521 | 1 | NDBI |

**Nota:** El tensor actual se genero CON grid embeddings, asi que cada punto de la grilla 5x5 tiene su propio embedding de 512-d (25 vectores distintos por tile).

**Paso 4: Construccion del tensor y (targets)**

```
y shape: (1403, 3, 3)
                ^  ^
                |  +-- 3 contaminantes: NO2, SO2, O3
                +----- 3 horizontes: T+1, T+3, T+7
```

- Los targets son valores ABSOLUTOS de Sentinel-5P (no anomalias)
- Se obtienen via busqueda binaria en paneles S5P
- Valores en mol/m2 (luego convertidos a ug/m3 con factores de conversion)

**Estadisticas de y (valores absolutos en mol/m2):**
| Contaminante | Mean | Std |
|-------------|------|-----|
| NO2 | 2.90e-5 | 1.72e-5 |
| SO2 | 2.73e-4 | 2.88e-4 |
| O3 | 1.16e-1 | 5.43e-3 |

**O3 tiene valores ~4000x mas grandes que NO2.** Esto es critico para el entrenamiento.

### Dataset en Hugging Face

**Repo:** `Slucu-0310/geovision-cali-sit3`
**Tamaño:** ~1.77 GB

| Archivo | Descripcion |
|---------|-------------|
| `X_convlstm.npy` | (1403, 8, 522, 5, 5) -- ~585 MB |
| `y_convlstm.npy` | (1403, 3, 3) |
| `embeddings_sit2.npz` | Embeddings originales |

---

## Parte 3: Modelos probados y resultados

### Preprocesamiento comun

- Split 70/15/15 (982/210/211) ANTES de normalizar
- Normalizacion z-score por contaminante usando SOLO estadisticas de TRAIN
- Guardado de copia normalizada (`y_convlstm_norm.npy`)
- Denormalizacion en evaluacion para reportar metricas en escala original

### Modelo 1: ConvLSTM2D (DESCARTADO)

**Arquitectura:**
- hidden_dim=128, 3 capas ConvLSTM, kernel=3
- Una sola Conv2d de salida (9 canales = 3 horizontes * 3 contaminantes)
- **5.4 millones de parametros** (muchisimo para 1403 muestras)

**Training:** AdamW lr=5e-5, ReduceLROnPlateau, early stopping

**Resultados con pesos [10000, 1000, 1] (iteracion 1):**
| Contaminante | RMSE ug/m3 | R2 |
|-------------|------------|----|
| NO2 | ~0.00 | 0.9998 (overfitting) |
| SO2 | ~0.00 | 0.16 |
| O3 | 0.16 | 0.22 |

Problema: los pesos extremos hacian que el modelo solo aprendiera NO2, ignorando SO2 y O3.

**Resultados con pesos [1, 1, 1] (iteracion 2):**
| Contaminante | RMSE ug/m3 | R2 |
|-------------|------------|----|
| NO2 | 0.09 | 0.24 |
| SO2 | 1.93 | -0.06 |
| O3 | 16.41 | 0.76 |

Mejoro O3, pero SO2 quedo negativo y NO2 bajo.

**Resultados con cabezas separadas (iteracion 3):**
- hidden_dim=64, num_layers=2, dropout=0.4
- Cabezas de salida separadas (una Conv2d por contaminante)
- **1.7 millones de parametros**

| Contaminante | RMSE ug/m3 | R2 |
|-------------|------------|----|
| NO2 | 0.09 | 0.24 |
| SO2 | 1.93 | -0.06 |
| O3 | 16.41 | 0.76 |

Mismos resultados. SO2 sigue irremediablemente negativo.

### Modelo 2: Conv3DSit3 (ACTUAL)

**Arquitectura:**
```
Input (B, 8, 522, 5, 5)
  -> Permute a (B, 522, 8, 5, 5)
  -> Bottleneck Conv3d 1x1x1: 522 -> 32 canales
  -> BatchNorm3d + ReLU
  -> Conv3d(32->64, k=3x3x3, pad=1) + BN + ReLU + MaxPool3d(2)
  -> Conv3d(64->128, k=3x3x3, pad=1) + BN + ReLU + MaxPool3d(2)
  -> AdaptiveAvgPool3d(1) -> Flatten -> 128-d
  -> Dropout(0.3)
  -> 3 cabezas lineales separadas (una por contaminante, 3 horizontes c/u)
  -> Output: (B, 3, 3) = (batch, horizonte, contaminante)
```

- **295,017 parametros** (6x menos que ConvLSTM)
- Procesa las 8 timesteps en paralelo (no secuencial como ConvLSTM)
- BatchNorm estabiliza el entrenamiento

**Training:** AdamW lr=5e-5, wd=1e-5, max_epochs=400, early_stopping patience=40

**Resultados Conv3D (ULTIMA CORRIDA):**

```
======================================================================
  TABLA RESUMEN - Conv3D (SIT. 3)
======================================================================
  MSE global:              2.896340e-06
  RMSE global (mol/m2):    0.001702

  Contaminante    RMSE mol/m2    RMSE ug/m3   KPI ug/m3  Cumple   R2
  --------------- -------------- ------------ ---------- -------- --------
  NO2             1.46e-05        0.08 ug/m3     8.0      SI     0.3089
  SO2             2.57e-04        2.06 ug/m3     6.0      SI    -0.1979
  O3              2.86e-03       17.16 ug/m3    12.0      NO     0.7355

  R2 por horizonte y contaminante:
  Horizonte     NO2 R2    SO2 R2    O3 R2
  ----------   --------  --------  --------
  T+1          0.4110   -0.1748    0.7389
  T+3          0.2728   -0.2562    0.7420
  T+7          0.2537   -0.1174    0.7258

  Degradacion T+1 -> T+7 por contaminante:
    NO2: 19.8%
    SO2: -13.6%
    O3:  8.9%
======================================================================
```

### KPIs de la consigna vs resultados actuales

| KPI | Requisito | Conv3D | Cumple? |
|-----|-----------|--------|---------|
| RMSE NO2 (T+1) | <= 8 ug/m3 | 0.08 | **SI** |
| RMSE SO2 (T+1) | <= 6 ug/m3 | 2.06 | **SI** |
| RMSE O3 (T+1) | <= 12 ug/m3 | 17.16 | **NO** |
| R2 promedio | >= 0.55 | (0.31-0.20+0.74)/3 = 0.28 | **NO** |
| Degradacion T+1->T+7 | < 60% | 7-19% | **SI** |

---

## Problemas detectados (lo que necesitamos resolver)

### Problema 1: SO2 R2 negativo en TODAS las arquitecturas

Hemos probado 4 configuraciones distintas (ConvLSTM con pesos extremos, ConvLSTM con pesos iguales, ConvLSTM con cabezas separadas, Conv3D con cabezas separadas) y SO2 siempre da R2 negativo o cercano a cero.

**Causas posibles:**
- SO2 tiene senal muy debil en TROPOMI sobre Cali (emisiones industriales esporadicas)
- Los embeddings CLIP (entrenados en RGB visual) no capturan patrones de SO2
- Hay demasiados NaN en SO2 (menos cobertura que NO2 y O3)
- SO2 troposferico sobre Cali es intrinsicamente ruidoso

**Referencia en papers:** La mayoria de estudios de prediccion de calidad del aire se enfoca solo en NO2. Incluso metodos state-of-the-art como LAPSO (Zhu et al., IEEE TGRS 2023) reportan R2 > 0.8 para NO2 y O3 pero no desglosan SO2 por separado.

### Problema 2: O3 estancado en R2 ~0.74

Tres arquitecturas distintas dan el mismo R2 para O3 (~0.74), lo que sugiere un **techo** con los features actuales.

**Causa posible:** O3 troposferico depende fuertemente de temperatura, radiacion solar y viento (quimica atmosferica). Los embeddings CLIP son features VISUALES (reflectancia de Sentinel-2), no capturan variables meteorologicas.

**Lo que usan los papers exitosos:** LAPSO, S-MESH y el estudio de Mexico City TODOS integran datos meteorologicos (temperatura, humedad, viento, presion) ademas de las imagenes satelitales. El pipeline `generar_tensor_convlstm.py` ya tiene soporte para `--covariables-path` que agrega ERA5 como canales extra. Los datos de ERA5 ya estan descargados en `dataset_sit2/ERA-5_panel/`.

### Problema 3: NO2 mejora pero aun bajo

NO2 paso de R2=0.24 (ConvLSTM) a 0.31 (Conv3D), y en T+1 alcanza 0.41. Sigue siendo bajo comparado con papers que reportan R2 > 0.8.

### Problema 4: R2 promedio no cumple KPI

Calculo: (0.3089 + (-0.1979) + 0.7355) / 3 = **0.282**.
El KPI exige >= 0.55, que es muy exigente para las predicciones actuales.

### Problema 5: O3 no cumple KPI de RMSE

17.16 ug/m3 contra un KPI de 12.0 ug/m3. Fallo por ~5 ug/m3.

---

## Datos disponibles NO utilizados

El pipeline `generar_tensor_convlstm.py` tiene capacidad de agregar covariables, pero NO se usaron en la generacion actual del tensor:

| Dato | Ubicacion | Formato |
|------|-----------|---------|
| ERA5 (temp, viento, humedad) | `dataset_sit2/ERA-5_panel/` | Panel zarr |
| MODIS MCD19A2 (AOD) | `dataset_sit2/MODIS_MCD_panel/` | Panel zarr |
| Latentes SAE (2048-d sparse) | `embeddings/sae_latent_512.pt` | Tensor torch |

**Que nos ensenan los papers:**
- LAPSO (Zhu et al. 2023): R2 > 0.8 para NO2, SO2, O3 usando TROPOMI + ERA5 + Deep Learning
- S-MESH (Shetty et al. 2024): R2 0.5-0.8 para NO2 con XGBoost + TROPOMI + meteorologia + ~900 estaciones
- Mexico City (Hernandez et al. 2025): R2=0.972 para NO2 con Random Forest + TROPOMI + ERA5 + downscaling
- BREATH-Net (Verma et al. 2024): Transformer para NO2 desde Sentinel-5P

---

## Pendientes inmediatos

1. **XGBoost** (codigo listo en notebook, celdas 17-19, sin ejecutar): features planas (pool 5x5 + flatten a 4176), un modelo XGBoost por contaminante con MultiOutputRegressor.
2. **Re-generar tensor con covariables de ERA5**: agregar temperatura, viento, humedad como canales extra (el pipeline ya lo soporta via `--covariables-path`).
3. **LOO-CV** (Leave-One-Out Cross Validation): entrenar dejando fuera una estacion DAGMA por vez, predecir en la estacion omitida. Los datos de estaciones DAGMA estan en `1Situacion/DagmaDATA/`.
4. **ST-Kriging** como baseline geoestadistico.
5. **Indice de Moran I** para autocorrelacion espacial de residuos.
6. **Informe final** con tablas de metricas, mapas de residuos y conclusiones.

---

## Repositorio y archivos clave

| Recurso | Ruta |
|---------|------|
| Repo GitHub | `https://github.com/nicothinn/GeoVision-CLIP-Cali` |
| Ruta local | `C:\Users\Samuel\Desktop\FINALPROYECTO3\GeoVision-CLIP-Cali` |
| Notebook principal | `notebooks/Situacion_3/sit3-entrenar-convlstm3.ipynb` |
| Modelo Conv3D | `src/modelos/conv3d_sit3.py` |
| Lightning Module | `src/training/lit_conv3d.py` |
| Pipeline tensor | `pipeline/generar_tensor_convlstm.py` |
| Dataset HF | `Slucu-0310/geovision-cali-sit3` |
| Datos DAGMA | `1Situacion/DagmaDATA/` |
| Paper referencia | LAPSO: `10.1109/TGRS.2023.3248180` |
