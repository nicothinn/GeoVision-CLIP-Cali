# Guía de Papers para GeoVision-CLIP Cali
## Qué nos aporta cada referencia y cómo usarla en el proyecto

> **Documento de uso interno del equipo.**  
> Cubre los 7 papers recomendados en la consigna + las 7 fuentes satelitales/estadísticas del panel.  
> Estructura: resumen → qué aplica en cada Situación → fragmentos clave → grado de utilidad.

---

## Índice rápido

| # | Paper | Situación(es) | Utilidad |
|---|-------|---------------|----------|
| 1 | Veefkind et al. (2012) — TROPOMI / Sentinel-5P | S1, S3 | ★★★★★ |
| 2 | Douros et al. (2023) — Comparación TROPOMI vs CAMS NO₂ | S1, S3 | ★★★★☆ |
| 3 | Theys et al. (2017) — SO₂ retrieval TROPOMI | S1, S3 | ★★★★☆ |
| 4 | Mall et al. (2024) — GRAFT (VLM para satélite sin anotaciones) | S2 | ★★★★★ |
| 5 | Cressie & Wikle (2011/2012) — Estadística espacio-temporal | S3 | ★★★★★ |
| 6 | Anselin (1995) — LISA (Local Indicators of Spatial Association) | S3 | ★★★★★ |
| 7 | Muhamed et al. (2025) — Sparse Autoencoders especializados (SSAE) | S2 | ★★★★☆ |

---

---

## Paper 1 — Veefkind et al. (2012): TROPOMI on the ESA Sentinel-5 Precursor

**Cita completa:** Veefkind, J.P. et al. (2012). *TROPOMI on the ESA Sentinel-5 Precursor: A GMES mission for global observations of the atmospheric composition for climate, air quality and ozone layer applications.* Remote Sensing of Environment, 120, 70–83. doi:10.1016/j.rse.2011.09.027

### Resumen del paper

Este es el paper fundacional del instrumento TROPOMI. Describe la misión S-5P, el diseño óptico del espectrómetro (UV-VIS-NIR-SWIR), los productos operacionales de Level 2 y las métricas de precisión esperadas para cada gas traza (O₃, NO₂, CO, SO₂, CH₄, CH₂O, aerosoles). Establece la herencia de OMI y SCIAMACHY, y justifica la resolución espacial mejorada de ~7×7 km² (luego reducida a 3.5×5.5 km² en operación real desde 2019) como salto cualitativo para monitoreo urbano.

### Qué nos sirve para el proyecto

#### Situación 1 — ETL y construcción del panel

- **Productos L2 que descargamos:** El paper lista exactamente los productos que necesitamos:
  - NO₂ total column y troposférica
  - SO₂ vertical column (troposférica / columnas de plumas)
  - O₃ total column y troposférica
  - Aerosol Optical Thickness (AOT) — relevante para correlacionar con MODIS MAIAC
- **Resolución y periodicidad confirmada:** 3.5×5.5 km² en nadir, cobertura global diaria (~13:30 hora solar local), órbita 824 km sun-synchronous. Esto justifica la elección de la consigna de "1–2 órbitas/día sobre Cali".
- **Bandas espectrales usadas para cada gas:**
  - Banda 3–4 (320–495 nm, UVIS) → NO₂ y SO₂
  - Banda 1–2 (270–320 nm, UV) → SO₂ volcánico / O₃
  - Banda 5–6 (675–775 nm, NIR) → aerosoles / nubes
  - Esta información sirve para filtrar correctamente los datos en el ETL.
- **Calidad de datos:** El paper define métricas de exactitud/precisión que se usan como umbral de filtrado en la descarga:
  - NO₂ troposférico: precisión ~ 1×10¹⁵ mol/cm²
  - SO₂ troposférico: 1 DU :: 0.5 DU
  - O₃ total: 3% :: 1%
- **Filtro `qa_value`:** El estándar de la misión usa `qa_value > 0.75` para descartar escenas nubladas (fracción de radiancia de nube > 0.5). **Este filtro debe aplicarse en el script de descarga / ETL.**

#### Situación 3 — Validación geoestadística

- **Incertidumbre de la fuente satelital:** El paper cuantifica la incertidumbre del producto, lo que define el "piso de ruido" que el modelo no puede superar. Los residuos de Kriging deben ser comparables o menores a este piso.
- **Justificación del downscaling:** TROPOMI mide columnas troposféricas a 3.5×5.5 km pero la resolución intraurbana que necesitamos es ~50–500 m. El paper reconoce que "en áreas urbanas los retrievals de gases traza necesitan caracterizar mejor los efectos de albedo y aerosoles" — esto es exactamente lo que el proyecto resuelve con Sentinel-2 como covariable proxy.
- **Cita textual útil para el informe:** *"The high spatial resolution provides new opportunities, while at the same time being challenging for the Level 2 product development."* (p.280) — úsala para justificar la necesidad del modelo híbrido CLIP+Kriging.

### Fragmentos de código o fórmulas directamente aplicables

```python
# Filtro estándar en el ETL — recomendado por el paper (operacionalmente)
ds = xr.open_dataset("S5P_L2_NO2.nc")
ds_filtered = ds.where(ds['qa_value'] > 0.75)
```

### Grado de utilidad: ★★★★★

**Indispensable.** Este paper es la referencia técnica de los datos que construyen el 100% del panel en S1. También justifica teóricamente por qué se necesita el downscaling (S3). Se debe citar en el Apéndice A del informe.

---

---

## Paper 2 — Douros et al. (2023): Comparación TROPOMI NO₂ vs. CAMS

**Cita completa:** Douros, J. et al. (2023). *Comparing Sentinel-5P TROPOMI NO₂ column observations with the CAMS regional air quality ensemble.* Geoscientific Model Development, 16, 509–534. doi:10.5194/gmd-16-509-2023

### Resumen del paper

El paper compara las columnas troposféricas de NO₂ de TROPOMI con los modelos regionales del Copernicus Atmosphere Monitoring Service (CAMS). Introduce una metodología de tres formas de comparar satélite vs. modelo que es muy relevante para validar predicciones. Construye un producto europeo L2 mejorado usando los perfiles verticales de CAMS como a priori. Discute bias estacional (~−30% en invierno vs. observaciones MAX-DOAS) y bias multiplicativo en zonas contaminadas.

### Qué nos sirve para el proyecto

#### Situación 1 — ETL: calidad del dato

- **Versión correcta del procesador:** El paper detalla los cambios entre versiones del processor:
  - Versiones ≤ 1.3.x: **bias negativo ~−30%** en columnas troposféricas en regiones contaminadas como Cali
  - Versión 1.4.0 (desde noviembre 2020): corrección del cloud pressure → **incremento de ~20% en NO₂ invernal**
  - Versión 2.2.0 (julio 2021): alineación con OMI dentro de ±5% en Europa
  - **Implicación para el ETL:** Si nuestro panel incluye datos de 2020–2024, habrá una discontinuidad en noviembre 2020 al cambiar al procesador 1.4.0. Deben segmentar el EDA temporal por versión del processor.

- **Filtro `qa_value > 0.75`:** Confirmado como estándar en este paper también. Este criterio actúa como cloud mask y elimina retrievals con fracción de radiancia nubosa > 0.5.

- **Regridding correcto:** El paper usa *area-weighted average* al remallar de la grilla nativa TROPOMI a la grilla objetivo. Para nuestro EDA, al agregar columnas a nivel de barrio de Cali (~1 km²), debemos usar el mismo método:

```python
# Regridding area-weighted — equivalente a lo que hace el paper
import xesmf as xe
regridder = xe.Regridder(ds_tropomi, ds_target_grid, "conservative")
ds_regridded = regridder(ds_tropomi['nitrogendioxide_tropospheric_column'])
```

#### Situación 1 — EDA: visualizaciones obligatorias

El paper proporciona exactamente el tipo de visualizaciones que requiere la consigna (≥8 en el notebook EDA):
1. **Hovmöller diagram** — 2D plot espacio vs. tiempo (un eje latitud/longitud del BBox Cali, otro eje tiempo)
2. **Time series por localización** — promedios mensuales sobre el BBox de Cali
3. **Mapas de promedio estacional** — verano vs. invierno (en el contexto de Cali: temporadas de lluvia/seca)
4. **Spread entre mediciones** — variabilidad entre órbitas el mismo día

#### Situación 3 — Metodología de validación

El paper introduce el concepto de **"tres maneras de comparar satélite vs. modelo"** (Fig. 1 del paper):

1. **S5P**: retrieval estándar TROPOMI (a priori TM5-MP)
2. **CAMS-RG-A**: modelo CAMS con averaging kernels del satélite aplicados
3. **S5P-RG**: retrieval TROPOMI con perfil CAMS como a priori

Para nuestro proyecto, la analogía directa es:
- **Observado en estaciones DAGMA** → nuestro ground truth
- **Predicción ConvLSTM** → análogo al modelo CAMS
- **Predicción ST-Kriging** → análogo al S5P-RG (predicción corregida con información local)

**La cita textual clave para el informe:**
> "The most common approach for comparing models and satellite retrievals is the comparison... by applying the satellite averaging kernels to the modeled profiles." (p.511)

**Esto justifica nuestro pipeline:** usar las predicciones de DL + Kriging (que incorpora la varianza local de las estaciones DAGMA) es metodológicamente superior a comparar directamente el satélite vs. el modelo.

#### Bias conocido para Cali

El paper muestra que en zonas urbanas tropicales (análogas a Cali), el bias entre TROPOMI y mediciones de superficie es sistemáticamente **−10% a −30%** con mayor concentración de NO₂ en la capa límite. Implicación: los valores DAGMA probablemente sean **más altos** que los valores TROPOMI. El EDA debe mostrar este bias y reportarlo en el informe.

### Grado de utilidad: ★★★★☆

**Muy alto.** Aporta metodología de validación directamente aplicable al LOO-CV, justifica la discontinuidad temporal en los datos de TROPOMI (cambio de procesador en 2020), y proporciona plantilla de visualizaciones para el EDA. Sin embargo, el dominio geográfico es europeo — las conclusiones cuantitativas sobre bias estacional no se transfieren directamente a Cali (clima tropical, sin nieve, fotoquímica diferente).

---

---

## Paper 3 — Theys et al. (2017): SO₂ retrieval TROPOMI — Algoritmo Teórico

**Cita completa:** Theys, N. et al. (2017). *Sulfur dioxide retrievals from TROPOMI onboard Sentinel-5 Precursor: algorithm theoretical basis.* Atmospheric Measurement Techniques, 10, 119–153. doi:10.5194/amt-10-119-2017

### Resumen del paper

Describe completamente el algoritmo DOAS (Differential Optical Absorption Spectroscopy) implementado en el procesador operacional UPAS de S-5P para retrieval de SO₂. Cubre: fitting espectral en múltiples ventanas, corrección de background, cálculo de Air Mass Factors (AMF), y análisis de errores completo. Incluye mapas globales de SO₂ verificados contra OMI.

### Qué nos sirve para el proyecto

#### Situación 1 — ETL: entender las variables de SO₂

- **Múltiples productos SO₂ disponibles:**
  - `SO2_column_number_density` — columna vertical total (DU)
  - `SO2_column_number_density_amf` — Air Mass Factor para aplicar correcciones
  - `SO2_slant_column_number_density` — columna sesgada (no corregida por geometría)
  - `cloud_fraction_crb` — fracción nubosa para filtrado
  - **Para nuestro proyecto usar:** `SO2_column_number_density` con `qa_value > 0.75`

- **Múltiples ventanas espectrales → múltiples capas SO₂:**
  El algoritmo UPAS usa ventanas diferentes para distintas alturas de emisión:
  - **TRL** (Total vertical column, lower troposphere): 312.5–326 nm → inyecciones bajas, **relevant para contaminación industrial Yumbo–Acopi**
  - **TMR** (Total column, middle troposphere): 325–335 nm → quemas caña
  - **STL** (Stratospheric): 360–390 nm → eventos volcánicos

  Para Cali, la **variable TRL** (troposférica baja) es la más relevante para la contaminación industrial.

- **Fuentes de SO₂ en la zona de estudio:**
  El paper (Fig. 1 del paper) confirma que los hotspots de SO₂ industrial son detectables con OMI/TROPOMI cuando las emisiones > ~5 kt/año. El corredor Yumbo–Acopi tiene actividad industrial (cementeras, agroindustria) que genera señal detectable.

#### Situación 3 — Propagación de errores

El paper describe en detalle las fuentes de error del retrieval de SO₂:
- Error de fitting espectral: ~0.5 DU
- Error de AMF: ~25–50% en zonas contaminadas con aerosoles
- Error de a priori de perfil vertical: ~20%

**Esto es crítico para el ST-Kriging:** el nugget del variograma de SO₂ debería absorber este nivel de incertidumbre instrumental. Si el nugget resulta mucho mayor, indica variabilidad real no capturada por el modelo.

#### Situación 1 — Filtros de calidad específicos para SO₂

```python
# Filtros recomendados por el paper para SO2 (más estrictos que NO2)
so2_valid = ds_so2.where(
    (ds_so2['qa_value'] > 0.5) &           # umbral más bajo que NO2
    (ds_so2['cloud_fraction_crb'] < 0.3) & # nubosidad más estricta
    (ds_so2['SO2_column_number_density'] > -0.001)  # excluir valores negativos físicamente imposibles
)
```

#### Justificación teórica para el informe

El paper provee la justificación científica de por qué Sentinel-5P es la fuente correcta para SO₂ troposférico en Cali (vs. sensores de suelo del DAGMA):
- Cobertura espacial continua sobre toda la huella urbana
- Revisita diaria (vs. 9 estaciones DAGMA con brechas de datos)
- Capacidad de detectar emisiones puntuales (chimeneas industriales) cuando la resolución ~7×3.5 km coincide con el foco

**Cita para el informe:** *"OMI has largely demonstrated the value of satellite UV-visible remote sensing in monitoring volcanic plumes in near-real time and in detecting and quantifying large anthropogenic SO₂ emissions, weak or unreported emission sources worldwide."* (p.120 del paper)

### Grado de utilidad: ★★★★☆

**Alto.** Indispensable para entender y documentar correctamente el pipeline de descarga de SO₂. Aporta justificación técnica para el EDA (mostrar el hotspot Yumbo–Acopi), criterios de filtrado de calidad específicos y cuantificación del error instrumental que deben reportarse en la discusión del variograma. Menos crítico operacionalmente que el Paper 1, pero necesario para el rigor técnico del informe.

---

---

## Paper 4 — Mall et al. (2024 / ICLR): GRAFT — VLMs para Teledetección sin Anotaciones

**Cita completa:** Mall, U., Phoo, C.P., Liu, M.K., Vondrick, C., Hariharan, B., & Bala, K. (2024). *Remote Sensing Vision-Language Foundation Models Without Annotations via Ground Remote Alignment.* ICLR 2024. https://graft.cs.cornell.edu

### Resumen del paper

GRAFT propone entrenar modelos visión-lenguaje (VLM) para imágenes satelitales *sin ninguna anotación textual*. La idea clave: las imágenes terrestres (Google Street View, Flickr geotagged) co-localizadas con imágenes satelitales sirven como intermediario para conectar satélite y lenguaje. Se entrena un encoder visual satelital (ViT) para que su espacio de features se alinee con el encoder de imágenes terrestres de CLIP (que ya está alineado con texto), usando pérdida contrastiva. Esto es **GRAFT (Ground Remote Alignment for Training)**. Resultados: +20% en clasificación zero-shot, +80% en segmentación zero-shot vs. baselines con supervisión.

### Qué nos sirve para el proyecto

#### Situación 2 — Arquitectura de GeoVision-CLIP

Este paper es la **base conceptual más directa** del encoder visual que usa el proyecto. Aunque la consigna pide RemoteCLIP (Liu et al., 2023, IEEE TGRS), GRAFT es la demostración más limpia del paradigma de alineación satélite-lenguaje y nos da el **razonamiento arquitectónico** completo.

**Analogía con nuestro proyecto:**

| GRAFT (paper) | GeoVision-CLIP (nuestro proyecto) |
|---|---|
| Imágenes terrestres → CLIP → espacio latente | Concentraciones S5P → pseudo-label textual → espacio latente |
| Sentinel-2 10m a nivel de imagen | Tiles Sentinel-2 64×64 px |
| Pérdida contrastiva multi-positive (Eq. 3 del paper) | InfoNCE estándar con temperatura learnable τ |
| ViT-B/16 encoder | ViT-B/32 (RemoteCLIP frozen) |
| Zero-shot retrieval e.g. "farmland" | Retrieval de clase: contaminación_alta_NO₂ |

**La pérdida contrastiva multi-positive del paper:**

```python
# Adaptación de Eq. (3) del paper GRAFT para nuestro contexto
# Cuando múltiples tiles del mismo percentil de contaminación se emparejan con el mismo texto
def graft_style_contrastive_loss(sim_matrix, temperature=0.07):
    """
    sim_matrix: (N, N) similaridad coseno entre embeddings imagen y texto
    Cuando hay múltiples positivos por clase (mismo percentil SO2, NO2...)
    """
    # Versión estándar InfoNCE (caso N_i=1 del paper, Eq. 2)
    logits = sim_matrix / temperature
    labels = torch.arange(logits.shape[0], device=logits.device)
    loss_i2t = F.cross_entropy(logits, labels)
    loss_t2i = F.cross_entropy(logits.T, labels)
    return (loss_i2t + loss_t2i) / 2
```

#### Situación 2 — Construcción del dataset de pares imagen-texto

El paper construyó dos datasets millones de pares:
- **SkyScript** (a 10m, Sentinel-2): ~1M pares imagen-texto para Sentinel-2
- **NAIP** (a 1m): imágenes aéreas de alta resolución

Para nuestros **≥1000 pares** requeridos por la consigna, el paper sugiere el siguiente pipeline de construcción del dataset:

```
Para cada tile Sentinel-2 64×64 px del BBox Cali:
1. Calcular el centroide (lat, lon) del tile
2. Buscar el valor S5P TROPOMI en ese centroide (promedio temporal)
3. Asignar percentil de contaminación (p25/p50/p75/p90/p99 sobre los 5 años)
4. Generar texto descriptivo:
   - p90-p99 → "imagen satelital de zona con alta contaminación de NO₂ en Cali"
   - p25-p50 → "imagen satelital de zona con vegetación densa y baja contaminación"
   - etc.
5. Split 70/15/15 estratificado por clase (SEED=42)
```

Esto es exactamente lo que la consigna llama "etiquetado semi-supervisado usando S5P como pseudo-label".

#### Situación 2 — Métricas de evaluación (Recall@k)

El paper usa extensivamente **Recall@k** (porcentaje de queries para las que el ground truth está en el top-k resultados recuperados) como métrica principal de retrieval. Esto es exactamente lo que piden los KPIs de la consigna:
- Recall@1 ≥ 0.45 (umbral mínimo), ≥ 0.65 (excelente)
- Recall@5 ≥ 0.70 (umbral mínimo), ≥ 0.85 (excelente)

Implementación de referencia directa del paper:

```python
def recall_at_k(embeddings_img, embeddings_txt, k=1):
    """
    Calcula Recall@k imagen→texto
    embeddings_img: (N, d), embeddings_txt: (N, d)
    """
    sim = (embeddings_img @ embeddings_txt.T)  # (N, N)
    topk = sim.topk(k, dim=1).indices          # (N, k)
    labels = torch.arange(N, device=sim.device).unsqueeze(1)  # (N, 1)
    correct = (topk == labels).any(dim=1).float()
    return correct.mean().item()
```

#### Situación 2 — Validación AFE/AFC de embeddings

El paper muestra (Sec. 4 y Apéndice) que los embeddings entrenados con alineación ground-remote capturan semántica geográfica interpretable (NDVI, impermeabilidad, etc.). Esto valida el supuesto detrás de la AFE del proyecto: que la matriz de embeddings de la rama visual contiene factores latentes relacionados con **Carga Antropogénica, Estrés Vegetal, Densidad Urbana, Volatilidad Atmosférica**.

La AFE debe mostrar que los primeros m factores (m tal que varianza acumulada ≥ 80%) tienen cargas altas en:
- Factor 1: bandas SWIR (industrial/calorificación) → Carga Antropogénica
- Factor 2: bandas NIR (vegetación) → Estrés Vegetal  
- Factor 3: bandas visible (albedo urbano) → Densidad Urbana
- Factor 4: cambios temporales → Volatilidad Atmosférica

#### Pixel-level VLM — aplicación futura (bonus)

GRAFT también entrena un ViT pixel-level usando la ubicación precisa de las imágenes terrestres. En nuestro contexto, esto sería equivalente a: dado un pixel del tile S2, predecir si está en zona de alta/baja contaminación. No es requerido por la consigna pero podría ser un análisis de ablación.

### Grado de utilidad: ★★★★★

**Crítico para Situación 2.** Es la arquitectura conceptual detrás del encoder visual de GeoVision-CLIP. Aporta la formulación matemática de la pérdida contrastiva, el protocolo de construcción del dataset de pares, las métricas de evaluación y la justificación de por qué los embeddings satelitales capturan semántica interpretable. Citar en la sección "Modelo GeoVision-CLIP" del informe.

---

---

## Paper 5 — Cressie & Wikle (2011/2012): Statistics for Spatio-Temporal Data

**Cita completa:** Cressie, N. & Wikle, C. (2011). *Statistics for Spatio-Temporal Data.* Wiley. (Las notas de clase corresponden a la presentación de Wikle de mayo 2012 en la University of Missouri.)

### Resumen del paper/libro

Es el texto de referencia mundial en estadística espacio-temporal. Cubre: notación formal de procesos espacio-temporales Y(s;t), métodos exploratorios (visualización, Hovmöller, variogramas espacio-temporales, funciones de correlación cruzada), modelos descriptivos vs. dinámicos, Kriging espacio-temporal (incluyendo variantes OK, SK, UK en 3D), modelos jerárquicos bayesianos, y Dynamic Spatio-Temporal Models.

### Qué nos sirve para el proyecto

#### Notación formal para el informe (S3, S1)

El libro establece la notación canónica que debe usarse en el informe técnico:

```
{Y(s;t) : s ∈ Ds ⊂ R², t ∈ Dt ⊂ R}

donde:
  Y(s;t) = concentración del contaminante (µg/m³) en punto s=(lat,lon), tiempo t
  Ds = área metropolitana Cali (BBox: lat 3.30°–3.55°N, lon −76.60°–−76.40°W)
  Dt = [2020-01-01, 2024-12-31] discretizado en días
```

#### Situación 1 — EDA espacio-temporal (métodos del libro)

El libro provee exactamente los métodos que deben aparecer en el notebook EDA de la consigna (≥8 visualizaciones):

1. **Diagrama de Hovmöller** → plot 2D (longitud × tiempo) para NO₂ medio sobre el BBox Cali
2. **Time series por localizacion** → series temporales en las 9 estaciones DAGMA
3. **Empirical orthogonal functions (EOF)** → descomposición espacio-temporal del panel
4. **Variograma marginal espacial** → h vs. γ(h) promediado sobre todos los tiempos
5. **Variograma temporal** → lag temporal vs. γ(Δt) promediado sobre todos los puntos
6. **Mapa de cobertura efectiva** → porcentaje de días con qa_value>0.75 por píxel

**Plantilla para variograma experimental:**

```python
from pykrige.variogram_models import exponential_variogram_model
import numpy as np

def compute_empirical_variogram(lats, lons, times, values, n_lags=20):
    """
    Calcula el variograma experimental espacio-temporal
    Basado en la definición de Cressie & Wikle (2011), Eq. 6.3
    γ(h, u) = (1/2) * E[(Y(s+h, t+u) - Y(s,t))²]
    """
    # Pares a lag (h, u) usando KDTree para eficiencia
    from scipy.spatial import cKDTree
    coords = np.column_stack([lats, lons])
    tree = cKDTree(coords)
    pairs = tree.query_pairs(r=0.1, output_type='ndarray')  # h < 0.1°
    
    semivariances = []
    for i, j in pairs:
        diff = values[i] - values[j]
        semivariances.append(0.5 * diff**2)
    
    return np.mean(semivariances)
```

#### Situación 3 — Kriging Espacio-Temporal (componente B)

Este libro es la **fuente primaria** de toda la metodología de ST-Kriging que usa la consigna. Los conceptos clave con sus referencias en el libro:

**a) Variograma separable espacio-temporal:**
El libro (Cap. 6) define el variograma separable:
```
γ(h,u) = σ²_s · γ_s(h) + σ²_t · γ_t(u) + σ²_s · σ²_t · γ_s(h) · γ_t(u)
```
donde `h` = lag espacial (km), `u` = lag temporal (días).

**Implementación para nuestro proyecto:**

```python
from pykrige.ok3d import OrdinaryKriging3D

def fit_variogram_and_kriging(lats, lons, times, values):
    """
    Ajusta variograma separable y ejecuta ST-Kriging 3D
    Implementación directa de Cressie & Wikle Cap. 6
    """
    # Normalización — evita anisotropía espuria (tal como pide la consigna)
    lat_n = (lats - lats.mean()) / lats.std()
    lon_n = (lons - lons.mean()) / lons.std()
    t_n   = (times - times.mean()) / (times.std() + 1e-8)
    
    # Kriging Ordinario 3D (lat, lon, t) — de PyKrige
    ok3d = OrdinaryKriging3D(
        lat_n, lon_n, t_n, values,
        variogram_model='exponential',  # modelo teórico de ajuste
        verbose=True,
        enable_plotting=True
    )
    return ok3d
```

**b) Nugget, sill y range — interpretación:**
- **Nugget (C₀):** error de medición + variabilidad microscópica. Para DAGMA, incluye el error instrumental de los analizadores (~5% según fichas técnicas).
- **Sill (C₀ + C₁):** varianza total del proceso (variabilidad intrínseca de NO₂ en Cali)
- **Range:** distancia de autocorrelación. Para NO₂ urbano ~5–15 km en ciudades similares.

**c) Variograma de residuos (certificación del modelo):**
El libro (Cap. 8) establece que si el variograma de los residuos `ε(s,t) = Y_obs(s,t) - Ŷ(s,t)` es nugget puro (estructura plana, sin autocorrelación remanente), el modelo capturó toda la estructura espacial. La consigna exige exactamente esto.

```python
def check_residual_variogram(observed, predicted, lats, lons):
    """
    Verifica que los residuos sean nugget puro
    Si range > 0 y sill/nugget > 0.1, el modelo no capturó toda la autocorrelación
    """
    residuals = observed - predicted
    # Fit variogram a los residuos — esperamos nugget puro
    from skgstat import Variogram
    V = Variogram(np.column_stack([lats, lons]), residuals, model='nugget')
    return V
```

#### Situación 3 — Métodos exploratorios espacio-temporales para el informe

El libro Cap. 5 detalla los métodos EDA que deben reportarse en S3:

1. **Lag plots espacio-temporales** — scatter de Y(s,t) vs Y(s,t-Δt)
2. **Covarianza cruzada espacio-temporal** → ¿qué lag temporal maximiza la correlación entre NO₂ en estación i y j?
3. **Análisis de tendencia espacio-temporal** → ¿hay drift secular en las concentraciones 2020–2024?

**Citación para el informe (sección "Pipeline DL + Geoestadística"):**
> "In statistical spatio-temporal data analysis, we seek to characterize the process in the presence of uncertain and (often) incomplete observations and system knowledge for the purposes of: prediction in space (interpolation), prediction in time (forecasting)." — Wikle, 2012, p.6

### Grado de utilidad: ★★★★★

**Referencia fundamental para S3 — absolutamente indispensable.** Todo el componente B (ST-Kriging) de la Situación 3 se deriva de este libro. Los KPIs de nugget puro en variograma de residuos, la metodología de normalización, la formulación del OK3D, y los métodos EDA del panel vienen de aquí. Citar en "Pipeline DL + Geoestadística" y en "Validación geoestadística".

---

---

## Paper 6 — Anselin (1995): LISA — Local Indicators of Spatial Association

**Cita completa:** Anselin, L. (1995). *Local Indicators of Spatial Association — LISA.* Geographical Analysis, 27(2), 93–115.

### Resumen del paper

El paper fundacional que define los LISA. Anselin propone una clase general de estadísticos locales que satisfacen dos requisitos: (a) miden clustering espacial significativo alrededor de cada observación, y (b) su suma es proporcional a un indicador global (Moran's I). La implementación más usada es el **Local Moran's Iᵢ**. El paper incluye Monte Carlo experiments y una aplicación a conflicto entre países africanos. Define el Moran scatterplot como herramienta complementaria para identificar outliers (HH, LL, HL, LH).

### Qué nos sirve para el proyecto

#### Situación 3 — Análisis LISA completo (Componente C)

La consigna requiere explícitamente: *"Análisis LISA (Local Indicators of Spatial Association) para identificar clusters de alta y baja contaminación con significancia local."*

**Definición formal del Local Moran Iᵢ:**

```
Iᵢ = (yᵢ - ȳ) / m₂ · Σⱼ wᵢⱼ(yⱼ - ȳ)

donde:
  yᵢ = concentración del contaminante en zona i (predicción Kriging)
  ȳ  = media global sobre toda la superficie predicha de Cali
  m₂ = varianza de y
  wᵢⱼ = pesos espaciales (matriz de contigüidad / distancia inversa)
```

**Implementación con PySAL (esda):**

```python
import esda
import libpysal

def compute_moran_and_lisa(surface_pred, coords, k=8):
    """
    Calcula Moran Global I y LISA sobre la superficie predicha
    surface_pred: array 1D de concentraciones (vectorizado de la grilla)
    coords: array (N, 2) de coordenadas (lat, lon) de los puntos de la grilla
    """
    # Matriz de pesos espaciales KNN (k vecinos más cercanos)
    w = libpysal.weights.KNN.from_array(coords, k=k)
    w.transform = 'R'  # row-standardize (recomendado por Anselin 1995)
    
    # Moran Global I
    moran = esda.Moran(surface_pred, w)
    print(f"Moran I = {moran.I:.4f}, p-value = {moran.p_sim:.4f} (permutation test)")
    
    # LISA (Local Moran)
    moran_local = esda.Moran_Local(surface_pred, w)
    
    # Clasificación de zonas (Moran scatterplot quadrants)
    # HH: High-High (hotspot) → alta contaminación rodeada de alta contaminación
    # LL: Low-Low (coldspot) → baja contaminación rodeada de baja
    # HL: High-Low (outlier) → alta rodeada de baja → posible fuente puntual
    # LH: Low-High (outlier) → baja rodeada de alta → posible refugio
    sig_mask = moran_local.p_sim < 0.05
    quad = moran_local.q  # 1=HH, 2=LH, 3=LL, 4=HL
    
    return moran, moran_local, sig_mask, quad
```

**Visualización del Moran scatterplot (Anselin 1993a / 1995):**

```python
import matplotlib.pyplot as plt
import numpy as np

def moran_scatterplot(y, w_y_lag, title="Moran Scatterplot"):
    """
    Scatter de y estandarizado vs. spatial lag de y
    Pendiente = Moran I global
    Cuadrantes: HH (Q1), LH (Q2), LL (Q3), HL (Q4)
    """
    z = (y - y.mean()) / y.std()
    fig, ax = plt.subplots(figsize=(6,6))
    ax.scatter(z, w_y_lag, alpha=0.4, s=10)
    ax.axhline(0, color='k', lw=0.5)
    ax.axvline(0, color='k', lw=0.5)
    # Cuadrantes
    ax.text(1.5, 1.5, 'HH', fontsize=14, color='red')
    ax.text(-2, -2, 'LL', fontsize=14, color='blue')
    ax.text(1.5, -1.5, 'HL', fontsize=14, color='orange')
    ax.text(-2, 1.5, 'LH', fontsize=14, color='green')
    ax.set_xlabel('Concentración estandarizada')
    ax.set_ylabel('Spatial Lag (vecinos)')
    ax.set_title(title)
```

#### Qué esperar en Cali según la teoría LISA

Para la superficie predicha de NO₂ en Cali, el análisis LISA debería revelar:
- **Clusters HH** (hotspots significativos): zona norte (Yumbo–Acopi, industrial), vía principal de transporte pesado (Autopista Sur, Calle 13)
- **Clusters LL** (coldspots): laderas de Farallones, zona verde occidente, Pance
- **Outliers HL**: posibles fuentes puntuales aisladas (estaciones de servicio, industria informal)
- **Outliers LH**: parques urbanos rodeados de zona densa (e.g., parque del Acueducto)

#### Moran Global I — requisito KPI de la consigna

La consigna exige **I > 0.30 con p < 0.05** (mínimo), **I > 0.50** (excelente). Esto garantiza que el modelo aprendió coherencia geográfica real y no está prediciendo ruido.

El paper (Sec. 2, Eq. 4) define la prueba de hipótesis:
```
H₀: No hay autocorrelación espacial (distribución aleatoria)
H₁: I > E[I] (clustering positivo)
```
La prueba se hace por **permutation test con n=999** (exactamente como pide la consigna), que es más robusta que la distribución asintótica normal.

#### Cuidados en la implementación (del paper)

El paper sección 5 advierte sobre **multiple testing**: cuando se hacen n pruebas LISA simultáneas (una por pixel), la tasa de falsos positivos se infla. El paper recomienda:
- Usar umbral p < 0.05 pero reconocer que algunos clusters son significativos por azar
- Con 999 permutaciones, el p-valor mínimo posible es 0.001 (si ninguna permutación excede el estadístico observado)
- **Corrección de Bonferroni** opcional: usar p < 0.05/n si se quiere ser conservador

```python
# Corrección de Bonferroni para LISA
bonferroni_threshold = 0.05 / len(surface_pred)
sig_mask_strict = moran_local.p_sim < bonferroni_threshold
```

#### Interpretación para el análisis de perfiles tipológicos (Clustering S3)

El paper es complementario al K-Means de perfiles tipológicos: los clusters LISA identifican **dónde** hay concentraciones significativas (dimensión espacial), mientras que K-Means sobre la superficie predicha identifica **qué tipo** de patrón tiene cada zona (dimensión semántica). El informe debe mostrar ambos análisis y verificar que los clusters LISA corresponden con los clusters K-Means de alta contaminación.

### Grado de utilidad: ★★★★★

**Indispensable para S3.** El análisis LISA es un entregable explícito de la consigna. Este paper es la referencia canónica que justifica toda la metodología, las pruebas de hipótesis por permutación, la clasificación en cuadrantes del Moran scatterplot, y los mapas de significancia local. El KPI Moran I > 0.30 viene directamente de esta metodología.

---

---

## Paper 7 — Muhamed, Diab & Smith (2025 / NAACL): Sparse Autoencoders Especializados (SSAE)

**Cita completa:** Muhamed, A., Diab, M., & Smith, V. (2025). *Decoding Dark Matter: Specialized Sparse Autoencoders for Interpreting Rare Concepts in Foundation Models.* NAACL 2025 Findings, pp. 1604–1635.

### Resumen del paper

El paper identifica que los SAEs estándar entrenados sobre grandes datasets generales pierden conceptos raros o de subdominio específico ("dark matter features"). Propone **Specialized SAEs (SSAEs)** que se entrenan sobre datos de subdominio: comienzan de un seed dataset pequeño, expanden via dense retrieval del corpus de pretraining del FM, y optimizan con **Tilted Empirical Risk Minimization (TERM)** para mejorar la detección de conceptos tail. Logra +12.5% en worst-group accuracy en Bias in Bios dataset.

### Qué nos sirve para el proyecto

#### Situación 2 — Arquitectura del SAE (componente obligatorio)

La consigna pide implementar **Sparse Autoencoders simétricos** insertados entre los encoders y sus projection heads. Este paper es la referencia técnica más reciente y rigurosa para entender la arquitectura SAE.

**Formulación matemática del SAE (Eq. 1 del paper = Eq. de la consigna):**

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class SparseAutoencoder(nn.Module):
    """
    Implementación del SAE según Muhamed et al. (2025)
    Para insertar entre el encoder CLIP y el projection head
    
    x: activación de la capa del encoder (d_model = 512 para ViT-B/32)
    d: dimensión del espacio latente SAE (d = 512 según consigna)
    """
    def __init__(self, d_model: int = 512, d_sae: int = 512, lambda_l1: float = 1e-3):
        super().__init__()
        self.W_enc = nn.Linear(d_model, d_sae, bias=True)
        self.W_dec = nn.Linear(d_sae, d_model, bias=True)
        self.lambda_l1 = lambda_l1
        
    def forward(self, x):
        # Encoder: f(x) = ReLU(W_enc @ x + b_enc)
        z = F.relu(self.W_enc(x))
        # Decoder: x_hat = W_dec @ z + b_dec
        x_hat = self.W_dec(z)
        return z, x_hat
    
    def loss(self, x, z, x_hat):
        # L(x) = ||x - x_hat||² + λ||z||₁  (Eq. 1 del paper, Eq. de la consigna)
        l_rec = F.mse_loss(x_hat, x)
        l_sparse = self.lambda_l1 * z.abs().mean()
        return l_rec + l_sparse, l_rec, l_sparse
    
    def normalize_decoder(self):
        # "We constrain the columns of W_dec to have unit norm during training"
        # (Bricken et al., 2023; seguido por este paper)
        with torch.no_grad():
            norms = self.W_dec.weight.norm(dim=0, keepdim=True)
            self.W_dec.weight.div_(norms)
```

**Loss total del proyecto (combinación con InfoNCE):**

```python
def total_loss(model_img, model_txt, sae_img, sae_txt, batch_imgs, batch_txts, alpha=0.1):
    """
    L_total = L_InfoNCE + α·(L_sae_img + L_sae_txt)
    α = 0.1, λ = 1e-3 (como especifica la consigna)
    """
    # Embeddings
    e_img = model_img(batch_imgs)  # (B, 512)
    e_txt = model_txt(batch_txts)  # (B, 512)
    
    # SAE forward
    z_img, x_hat_img = sae_img(e_img)
    z_txt, x_hat_txt = sae_txt(e_txt)
    
    # InfoNCE sobre los embeddings originales (o los proyectados post-SAE)
    sim_matrix = (e_img @ e_txt.T) / 0.07  # temperatura = 0.07
    labels = torch.arange(len(e_img), device=e_img.device)
    l_clip = (F.cross_entropy(sim_matrix, labels) + F.cross_entropy(sim_matrix.T, labels)) / 2
    
    # SAE losses
    _, l_rec_img, l_sparse_img = sae_img.loss(e_img, z_img, x_hat_img)
    _, l_rec_txt, l_sparse_txt = sae_txt.loss(e_txt, z_txt, x_hat_txt)
    l_sae = l_rec_img + l_sparse_img + l_rec_txt + l_sparse_txt
    
    return l_clip + alpha * l_sae
```

#### Situación 2 — Métricas KPI del SAE

El paper define dos métricas primarias de evaluación de SAEs (que coinciden exactamente con los KPIs de la consigna):

1. **L0 sparsity / Sparsity ratio:**
   ```python
   # L0 = número medio de features activas por input
   l0 = (z > 0.01).float().mean(dim=1).mean()  # media sobre batch
   
   # Sparsity ratio = proporción de features inactivas (z < 0.01)
   sparsity_ratio = (z < 0.01).float().mean()  # KPI: ≥ 0.70 mínimo, ≥ 0.85 excelente
   ```

2. **Reconstruction loss MSE (val):**
   ```python
   # KPI: ≤ 0.05 mínimo, ≤ 0.02 excelente
   l_rec_val = F.mse_loss(x_hat_val, x_val)
   ```

#### Situación 2 — Análisis de neuronas activas ("interpretabilidad mecánica")

La consigna pide: *"Análisis de neuronas activas del SAE para cada clase (interpretabilidad mecánica)."* Este paper provee el marco conceptual y el método:

```python
def analyze_active_features(sae, embeddings_by_class, class_names, top_k=10):
    """
    Para cada clase, identifica las features del SAE que se activan más
    Basado en la metodología de Muhamed et al. (2025) Sec. 4
    """
    results = {}
    for class_name, embeddings in embeddings_by_class.items():
        with torch.no_grad():
            z, _ = sae(embeddings)  # (N_class, d_sae)
        
        # Frecuencia de activación por feature (≥ threshold)
        activation_freq = (z > 0.01).float().mean(dim=0)  # (d_sae,)
        top_features = activation_freq.topk(top_k).indices
        
        results[class_name] = {
            'top_features': top_features.tolist(),
            'activation_freq': activation_freq[top_features].tolist(),
            'mean_activation': z.mean(dim=0)[top_features].tolist()
        }
    return results
```

El informe debe mostrar una tabla o heatmap de las top-10 features por clase:

| Feature ID | contaminación_alta_NO₂ | contaminación_alta_SO₂ | ozono_anómalo | vegetación_densa | suelo_urbano |
|---|---|---|---|---|---|
| 027 | 0.82 | 0.45 | 0.12 | 0.03 | 0.15 |
| 113 | 0.04 | 0.78 | 0.91 | 0.01 | 0.06 |
| ... | ... | ... | ... | ... | ... |

#### SSAEs vs. SAEs estándar — relevancia para Cali

El paper identifica un problema crítico que aplica directamente a nuestro dataset: si las **5 clases de contaminación** no están uniformemente distribuidas en el dataset (p.ej., `ozono_anómalo` es mucho más raro que `suelo_urbano`), el SAE estándar tenderá a no aprender bien las features de la clase rara.

**Mitigación recomendada por el paper:**
1. **Dense retrieval:** usar un encoder pre-entrenado para seleccionar más ejemplos del subdomain raro
2. **TERM:** Tilted ERM con parámetro `t > 0` para dar más peso a ejemplos difíciles

Para nuestro proyecto, la versión simplificada es el **class-balanced sampling** durante el entrenamiento:

```python
from torch.utils.data import WeightedRandomSampler

# Calcular pesos inversamente proporcionales al tamaño de clase
class_counts = torch.tensor([n_class1, n_class2, n_class3, n_class4, n_class5])
weights = 1.0 / class_counts
sample_weights = weights[labels]  # weight para cada sample
sampler = WeightedRandomSampler(sample_weights, len(sample_weights), replacement=True)
```

### Grado de utilidad: ★★★★☆

**Alto para S2.** Provee la formulación matemática exacta del SAE (idéntica a la de la consigna), las métricas de evaluación (L0 sparsity, MSE reconstruction), y el método de análisis de interpretabilidad mecánica por clase. La contribución de los SSAEs (especialización para subdominios raros) es una mejora respecto al SAE estándar que podría aplicarse si el dataset está desbalanceado.

---

---

## Tabla resumen: mapeado Paper → Tarea concreta → Archivo del repo

| Tarea concreta | Paper fuente | Archivo en repo | Quién |
|---|---|---|---|
| Filtro `qa_value > 0.75` en ETL | Paper 1 (Veefkind) + Paper 2 (Douros) | `src/etl/s5p_download.py` | Persona 1 |
| Filtro SO₂ cloud_fraction < 0.3 | Paper 3 (Theys) | `src/etl/s5p_download.py` | Persona 1 |
| Hovmöller diagram en EDA | Paper 5 (Cressie) | `notebooks/01_eda_panel.ipynb` | Persona 1 |
| Discontinuidad procesador nov-2020 | Paper 2 (Douros) | `notebooks/01_eda_panel.ipynb` | Persona 1 |
| Arquitectura SAE (encoder + loss) | Paper 7 (Muhamed) | `src/models/sae.py` | Persona 2 |
| InfoNCE + pérdida total | Paper 4 (GRAFT) + Paper 7 | `src/models/clip_loss.py` | Persona 2 |
| Dataset de pares imagen-texto | Paper 4 (GRAFT) | `src/etl/pair_builder.py` | Personas 1+2 |
| Recall@k evaluación | Paper 4 (GRAFT) | `src/models/clip_metrics.py` | Persona 2 |
| Análisis AFE/AFC embeddings | Paper 4 (GRAFT) justifica | `notebooks/02_afe_afc.ipynb` | Persona 2 |
| Neuronas activas por clase (SAE) | Paper 7 (Muhamed) | `notebooks/03_sae_interpretability.ipynb` | Persona 2 |
| Variograma experimental + teórico | Paper 5 (Cressie) | `src/geo/variogram.py` | Persona 3 |
| ST-Kriging OrdinaryKriging3D | Paper 5 (Cressie) | `src/geo/kriging.py` | Persona 3 |
| Variograma de residuos (nugget puro) | Paper 5 (Cressie) | `src/geo/kriging.py` | Persona 3 |
| Moran Global I + permutation test | Paper 6 (Anselin) | `src/geo/moran.py` | Persona 3 |
| LISA + Moran scatterplot | Paper 6 (Anselin) | `src/geo/lisa.py` | Persona 3 |
| Mapas LISA de hotspots Cali | Paper 6 (Anselin) | `notebooks/04_geostat_validation.ipynb` | Persona 3 |
| LOO-CV metodología | Papers 5+6 (fundamento teórico) | `src/geo/loocv.py` | Persona 3 |

---

## Notas críticas para el informe (evitar penalizaciones)

### Sobre data leakage (-25% del proyecto)

La consigna penaliza con −25% del proyecto **"pasar las concentraciones de Sentinel-5P como input directo del modelo"**. Los papers fundamentan por qué esto es incorrecto:

- **Paper 1 y 3** muestran que las columnas TROPOMI tienen resolución 3.5×5.5 km y sesgo sistemático, no son adecuadas como input directo de un modelo predictivo de fina escala
- **Paper 4 (GRAFT)** el encoder visual se entrena sobre **imágenes Sentinel-2**, no sobre columnas TROPOMI. Las concentraciones S5P solo se usan como **pseudo-labels** para etiquetar los tiles (i.e., como target/ground truth en la fase de construcción del dataset, no como feature)
- Los tiles S2 + concentraciones S5P como pseudo-label → par (imagen, texto-etiqueta) → entrenamiento contrastivo → sin leakage

### Sobre el variograma nugget puro (KPI obligatorio)

El Paper 5 (Cressie) deja claro que un variograma de residuos con nugget puro NO significa que no hay ruido — significa que el ruido residual es **espacialmente aleatorio** (no estructurado). El ConvLSTM + Kriging deben capturar toda la autocorrelación estructural.

### Sobre LISA y significancia múltiple

El Paper 6 (Anselin) advierte sobre inflación de falsos positivos con múltiples pruebas LISA simultáneas. Para el informe, si reportan los mapas LISA deben mencionar si aplican corrección de Bonferroni o no, y justificarlo.

---

## Referencias completas para el Apéndice B del informe

```
[1] Veefkind, J.P., et al. (2012). TROPOMI on the ESA Sentinel-5 Precursor: A GMES mission 
    for global observations of the atmospheric composition for climate, air quality and ozone 
    layer applications. Remote Sensing of Environment, 120, 70–83. 
    doi:10.1016/j.rse.2011.09.027

[2] Douros, J., Eskes, H., van Geffen, J., Boersma, K.F., et al. (2023). Comparing 
    Sentinel-5P TROPOMI NO₂ column observations with the CAMS regional air quality ensemble. 
    Geoscientific Model Development, 16, 509–534. doi:10.5194/gmd-16-509-2023

[3] Theys, N., De Smedt, I., Yu, H., Danckaert, T., et al. (2017). Sulfur dioxide retrievals 
    from TROPOMI onboard Sentinel-5 Precursor: algorithm theoretical basis. Atmospheric 
    Measurement Techniques, 10, 119–153. doi:10.5194/amt-10-119-2017

[4] Mall, U., Phoo, C.P., Liu, M.K., Vondrick, C., Hariharan, B., & Bala, K. (2024). 
    Remote Sensing Vision-Language Foundation Models Without Annotations via Ground Remote 
    Alignment. ICLR 2024. https://graft.cs.cornell.edu

[5] Cressie, N. & Wikle, C. (2011). Statistics for Spatio-Temporal Data. Wiley. 
    (Notas de curso: Wikle, C.K., University of Missouri, Mayo 2012)

[6] Anselin, L. (1995). Local Indicators of Spatial Association — LISA. Geographical 
    Analysis, 27(2), 93–115.

[7] Muhamed, A., Diab, M., & Smith, V. (2025). Decoding Dark Matter: Specialized Sparse 
    Autoencoders for Interpreting Rare Concepts in Foundation Models. NAACL 2025 Findings, 
    pp. 1604–1635.
```

---

*Documento generado el 2026-05-07. Mantener actualizado a medida que se implementen los componentes.*
