# Informe de diagnóstico — GeoVision-CLIP Sit. 2
**Fecha:** 2026-05-17 | **Mejor checkpoint:** época 17

---

## 1. Resumen de outputs observados

### 1.1 Curvas de entrenamiento

| Métrica | Mejor valor (época 17) | KPI mínimo | Estado |
|---------|------------------------|------------|--------|
| Recall@1 (val) | **0.114** | 0.45 | ❌ FAIL (~4× por debajo) |
| Recall@5 (val) | **0.243** | 0.70 | ❌ FAIL (~3× por debajo) |
| Sparsity img (val) | **0.045** | 0.70 | ❌ FAIL (~15× por debajo) |
| MSE SAE img (val) | **0.028** | ≤ 0.05 | ✅ OK |
| Loss val (mínima) | **~2.43** (época 6) | — | — |

**Lo que dicen las curvas:**

- `Loss train` cae monotónicamente de 3.5 → 0.08 en 17 épocas: **memorización casi total del set de entrenamiento**.
- `Loss val` e `InfoNCE val` tienen forma de U: mínimo en época 6 (~2.43) y luego remontan hasta ~3.38 en época 17. El modelo dejó de generalizar después de la época 6; el early stop con paciencia=6 detuvo correctamente en la época 17 (9 épocas sin mejora neta en Recall@1).
- `Recall@1 val` y `Recall@5 val` suben lentamente pero NO siguen a la mejora del loss train: señal clara de **overfitting** y de que el modelo no aprende representaciones generalizables de los tiles.
- `Sparsity img val` permanece plana en ~0.04, completamente insensible al entrenamiento.
- `MSE SAE img val` desciende continuamente y cruza el umbral 0.05 en la época 6, llegando a 0.028 en época 17: **el SAE reconstruye bien pero no es disperso**.

### 1.2 Curva MSE SAE imagen

- Cruza el umbral KPI 0.05 alrededor de la época 6–7, el mismo punto donde `val/loss` era mínima.
- Esto indica que **el SAE prioriza reconstrucción** (MSE bajo) sobre dispersión (sparsity alta): el gradiente total está dominado por el término de reconstrucción.

### 1.3 Matriz de confusión de clase (top-1 texto predicho)

```
                   predicha_top1
verdadera          NO2  SO2  O3  veg  urb
contam_alta_NO2     24    0   4    4    8   (44% acierto en clase, n=54)
contam_alta_SO2      5   11  10   11    4   (28% acierto,           n=41)
ozono_anomalo        4    7  10   14    5   (31% acierto,           n=40)
vegetacion_densa     3    6   7   22    3   (52% acierto,           n=41)
suelo_urbano        15    4   6    3   12   (30% acierto,           n=40)
```

**Lecturas clave:**

1. **NO2 → NO2** es la clase con mayor recall de clase (~44%). La descripción de NO2 contiene el valor numérico `NO2=X.XXe-05` que varía más que las otras clases → el encoder de texto se "ancla" a ese número.
2. **suelo_urbano** se confunde masivamente con **NO2** (15 de 40): el adaptador 13→3 + ViT congelado no captura suficiente señal visual urbana vs contaminada.
3. **ozono_anomalo** se confunde con **vegetacion_densa** (14 de 40): el texto de ozono y vegetación no son discriminativos (ambos mencionan Cali, NDVI alto, sin S5P contrastante en la descripción).
4. **SO2** es la peor clase (28%): textos SO2 parecen muy similares a NO2 en el espacio de embeddings de texto.
5. Solo **vegetacion_densa** y **NO2** están por encima del 40% de recall intra-clase.

### 1.4 Histograma de `z_img` (SAE visual, val)

- Distribución simétrica normal centrada en ~0, rango [-0.6, 0.8].
- La densidad es máxima entre -0.05 y +0.05.
- **|z| < 0.01 ≈ 4.5%**: la gran masa está entre 0.01 y 0.5 → imposible alcanzar 70% con λ=1e-3 y sin ReLU.
- El umbral 0.01 (línea roja) corta solo la punta del pico central; para que 70% de las activaciones caigan ahí haría falta que **casi toda la distribución colapsara al cero**, lo que requeriría ReLU/top-k en el encoder SAE más λ mucho mayor.

### 1.5 Panel de los 20 peores pares imagen → texto correcto

Los tiles con coseno diagonal más bajo (−0.11 a +0.08) muestran **3 patrones distintos**:

| Patrón | Ejemplos | Causa probable |
|--------|----------|----------------|
| **Urbano complejo** (#1, #2, #6): zona densa con edificios, calles, estructuras | Coseno ~−0.11 | Adaptador 1×1 no distingue textura urbana; ViT congelado no vio esa distribución espectral |
| **Oscuro / nube / artefacto** (#8, #11, #12, #18): imágenes casi negras o con gris uniforme | Coseno ~−0.01 | Tiles con nube residual o SCL incorrecto que pasó el filtro nube≤0.30 |
| **Campo agrícola / mixto** (#3, #4, #7, #10, #13, #14): parcelas geométricas o transición bosque/cultivo | Coseno ~−0.10 a +0.05 | Clase asignada (p. ej. ozono_anomalo) no corresponde visualmente a lo que se ve |

**Tiles negros/oscuros** (#8, #11, #12, #17) son la evidencia más directa de **ruido en el dataset**: tiles que pasaron el filtro SCL pero tienen poco contenido visual recuperable (nube delgada, sombra de cirrus o nodata enmascarado como 0).

---

## 2. Diagnóstico por componente

### 2.1 Calidad del dataset

#### 2.1.1 Filtro SCL demasiado permisivo
El pipeline usa `max_frac_nubes=0.30` y `min_frac_claros=0.10`. Esto permite tiles donde:
- Hasta el 30% de píxeles son nube/cirrus/sombra.
- Solo el 10% debe ser "claro" (vegetación, suelo, agua).

El resultado: **tiles #8, #11, #12 del panel son casi negros** → el adaptador recibe señal casi nula en B4/B3/B2 y el ViT genera embeddings similares entre sí (colapso semántico).

#### 2.1.2 Textos con baja discriminación intra-clase
La función `generar_descripcion` produce textos de la forma:

```
"Tile Sentinel-2 sobre Cali con concentracion alta de NO2 troposferico
 (2019-07-14, lat=3.4500, lon=-76.5300, NDVI=0.12, BSI=0.08,
  NO2=4.72e-05, SO2=1.23e-04, O3=0.114)."
```

**Problemas:**
- **La descripción base es idéntica** para todos los tiles de una misma clase: la única variación son los números (lat, lon, fecha, índices).
- Para SO2, la descripción base es siempre `"concentracion alta de SO2"` aunque el valor varíe ×10 dentro de los tiles que superan el p90.
- Para **ozono_anomalo**, la descripción no distingue ozono **alto** (≥ p90) de ozono **bajo** (≤ p25): dos tiles con O3 opuesto reciben el mismo texto `"columna de ozono troposferico anomala"`.
- Los valores numéricos (NO2=X.XXe-05) son codificados correctamente por MiniLM pero el modelo de texto se ancla a ellos en vez de aprender el concepto de "alta contaminación".

#### 2.1.3 Etiquetas de clase basadas en grilla S5P de baja resolución
- Sentinel-5P tiene resolución ~3.5 km; los tiles son de 64×64 píxeles (~640×640 m a 10 m/píx).
- El valor S5P se asigna interpolando en grilla al centroide del tile (`_valor_grilla`).
- Un tile con latitud 3.45, lon -76.53 tiene **el mismo valor S5P** que cualquier otro tile dentro de esa celda de 3.5 km, aunque visualmente sean muy distintos.
- Resultado: tiles visualmente dispares (zona urbana, campo, bosque) dentro de una celda S5P reciben **la misma clase** (p. ej. todos "contaminacion_alta_NO2") con descripciones casi idénticas.

#### 2.1.4 Desbalance de clases
- Vegetación densa: 441 tiles (29.4%)
- NO2: 356 (23.7%)
- SO2: 271 (18.1%)
- Suelo urbano: 223 (14.9%)
- Ozono anómalo: 209 (13.9%)

InfoNCE trata todos los pares del batch simétricamente: los negativos de vegetacion_densa son 29% del batch, lo que favorece al modelo a orientar hacia vegetacion → consistent con que ozono/suelo se confunden con vegetación.

### 2.2 Arquitectura del modelo

#### 2.2.1 Adaptador ms_adapter (13→3) con 1×1 Conv
- Un Conv2d(13→3) aprende solo **combinaciones lineales** de bandas, sin capturar estructura espacial (sin receptive field > 1).
- Los índices de banda son B1–B12 + SCL; la conversión a "pseudo-RGB" pierde información espectral de bandas en el infrarrojo (B8, B8A, B11, B12) que son cruciales para NDVI y urbano.
- El resultado de `ms_adapter` se redimensiona de 64×64 a 224×224: **upscaling ×3.5** que introduce artefactos de interpolación bicubica.

#### 2.2.2 RemoteCLIP congelado
- Con `FREEZE_VISUAL=True`, el ViT-B/32 recibe pseudo-RGB 224×224 sin actualizar sus pesos.
- RemoteCLIP fue preentrenado en RGB natural (imágenes de resolución variable); las bandas Sentinel-2 a 10 m tienen distribución muy distinta.
- El adaptador lineal 13→3 no puede compensar esta brecha de distribución sin ajuste del ViT.

#### 2.2.3 SAE sin activación no lineal
```python
def forward(self, x):
    z = self.encoder(x)          # lineal — z puede ser cualquier real
    return self.decoder(z), z
```
- `z` es un vector de números reales sin restricción de signo ni sparsidad estructural.
- `sparsity_ratio = mean(|z| < 0.01)` mide cuántas activaciones tienen magnitud casi nula.
- Con una distribución normal de z (observada en histograma), la fracción con |z| < 0.01 es: `P(|N(0,σ)| < 0.01) = 2·Φ(0.01/σ) - 1 ≈ 0.8/100·σ` para σ≈0.15 → ~5.3%, consistente con el 4.5% observado.
- **El 4.5% observado es teóricamente el máximo que puede dar un encoder lineal sin regularización fuerte**; aumentar λ a 1e-2 empujaría la masa hacia 0 pero requeriría σ→0, lo que colapsaría la reconstrucción.

#### 2.2.4 Conflicto entre objetivos
La loss total es `L = L_InfoNCE + 0.1·(L_sae_img + L_sae_txt)`.
- `L_InfoNCE` quiere `e_img` y `e_txt` ricos y discriminativos → z no puede colapsar a 0.
- `L_sae` con L1 quiere |z| → 0 → sparsity 100%.
- Con α=0.1 y λ=1e-3, **InfoNCE domina** (pérdida informativa ~3.3 vs SAE ~0.03×0.1 = 0.003) → sparsity permanece baja.

### 2.3 Evaluación

- Recall@1 global evalúa si el texto *i* es el #1 entre **225 candidatos** → muy exigente.
- La línea de base aleatoria es 1/225 = 0.44%; el modelo logra 11.4%: **25× sobre el azar**, señal de aprendizaje real.
- La tarea es de **retrieval abierto** (no clasificación de 5 clases): el modelo debe devolver el par exacto, no solo la clase correcta.

---

## 3. Recomendaciones — qué hacer para subir las métricas

> Las siguientes recomendaciones están ordenadas de **mayor impacto estimado** a menor, considerando el estado actual del código y los datos.

### 3.1 Dataset y pipeline (máximo impacto)

#### R1 — Textos más discriminativos por instancia
**Impacto estimado: +0.10–0.20 Recall@1**

La descripción actual usa **una base fija por clase**. Cambiar a textos que **diferencien la instancia** dentro de la clase:

```python
# Actual (igual para todos los tiles NO2 de la misma clase):
"Tile Sentinel-2 sobre Cali con concentracion alta de NO2 troposferico (fecha, lat, NDVI=0.12...)"

# Propuesto (contexto específico):
"Sector industrial-urbano de Cali: concentración elevada de dióxido de nitrógeno 
 (NO2={no2:.1e} mol/m²), superior al percentil 90 regional. 
 Cobertura: {pct_urban:.0f}% construido, NDVI={ndvi:.2f}. Fecha: {fecha}."

# Para ozono alto vs bajo (actualmente idénticos):
"Ozono troposférico anómalo ALTO (O3={o3:.4f} DU, p90={p90:.4f})" 
# vs
"Ozono troposférico anómalo BAJO (O3={o3:.4f} DU, p25={p25:.4f})"
```

Para aplicar esto **sin cambiar el pipeline ya construido**: editar los textos en el parquet de metadatos (`metadatos.parquet`) post-generación, o agregar una columna `descripcion_v2` al parquet existente.

#### R2 — Filtro SCL más estricto para entrenamiento
**Impacto estimado: +0.05–0.10 Recall@1 (menos ruido de tiles negros/corruptos)**

Los tiles oscuros (#8, #11, #12, #17 en el panel de peores pares) pasaron con `frac_nubes≤0.30`. Aplicar un sub-filtro **solo para el entrenamiento** (no cambiar el pipeline):

```python
# En el DataLoader de entrenamiento, agregar:
mask = (df["frac_nubes_scl"] <= 0.15) & (df["frac_claros_scl"] >= 0.50)
df_train_limpio = df_train[mask]
```

Esto reduce el train set (~20-30% menos tiles) pero los restantes tienen señal visual real. El val/test se mantiene igual para comparación justa.

#### R3 — Verificar alineamiento S5P–S2 por fecha
**Impacto: diagnóstico obligatorio**

El pipeline interpola valores S5P al centroide del tile usando el día exacto de la imagen S2. Verificar que:
- Las fechas S5P y S2 coincidan (diferencia ≤ 1 día).
- El valor S5P del centroide no sea `nan` o 0 para tiles con clase "contaminacion_alta_NO2" (si el valor es nan, el tile podría clasificarse mal).

```python
# Verificar en el parquet:
df[(df["clase"]=="contaminacion_alta_NO2") & (df["no2"].isna())]  # debería ser 0
```

### 3.2 Arquitectura del modelo

#### R4 — ReLU en el encoder SAE (crítico para sparsity)
**Impacto: sparsity 0.04 → ~0.60–0.75 con λ adecuada**

Cambio mínimo sin tocar el entrenamiento previo:

```python
class SparseAutoencoder(nn.Module):
    def __init__(self, dim_in, dim_latent=512):
        super().__init__()
        self.encoder = nn.Linear(dim_in, dim_latent)
        self.decoder = nn.Linear(dim_latent, dim_in)

    def forward(self, x):
        z = F.relu(self.encoder(x))   # ← ÚNICA LÍNEA QUE CAMBIA
        return self.decoder(z), z
```

Con ReLU:
- `z` ≥ 0 siempre.
- `mean(z < 0.01)` mide neuronas **muertas o inactivas**, que con L1 suficiente pueden ser la mayoría.
- L1 en z positivo penaliza exactamente las activaciones grandes: gradiente constante = -λ para z>0.

**Trade-off:** con ReLU, el MSE reconstrucción puede subir (el decoder tiene menos rango). Aumentar `dim_latent` (p. ej. 1024) ayuda a compensar.

#### R5 — Aumentar λ_L1 solo del SAE imagen
**Solo relevante DESPUÉS de R4 (ReLU)**

Con ReLU, escalonar λ:
- λ=1e-2: sparsity ~0.30–0.40 (estimado)
- λ=5e-2: sparsity ~0.60–0.70 (estimado, según los histogramas)

Sin afectar el Recall más del necesario, empezar en λ=1e-2.

#### R6 — Descongelar las últimas 2 capas del ViT (solo si Recall@1 > 0.15)
**Impacto potencial: +0.05–0.15 Recall@1**

Con el adaptador 13→3 fijo, el ViT no ve la distribución espectral Sentinel-2. Descongelar solo `visual.transformer.resblocks[-2:]` (2 bloques) al inicio reduce el riesgo de "catastrophic forgetting":

```python
# En GeoVisionClipSAEModel.__init__:
for name, p in self.visual.named_parameters():
    if "resblocks.11" in name or "resblocks.10" in name:
        p.requires_grad = True
```

**Hacer esto solo si primero se estabiliza el Recall con los cambios R1–R2**, para tener un baseline correcto.

### 3.3 Hiperparámetros de entrenamiento

#### R7 — Aumentar temperatura de calentamiento
El loss val mínimo ocurre en época 6 pero el Recall@1 sigue subiendo hasta la época 17. Esto sugiere que el **learning rate 1e-4 es alto** para las últimas épocas:

```python
# Añadir scheduler cosine annealing:
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=NUM_EPOCHS, eta_min=1e-6)
```

#### R8 — Pesos diferenciados por clase en InfoNCE
Las clases más frecuentes (vegetación 441, NO2 356) dominan los negativos en el batch. Con batch=32, en promedio hay ~9 vegetación y ~7 NO2 por batch → el modelo aprende a separar esas dos clases bien pero confunde las minoritarias (ozono 209, urbano 223).

Estrategia: **sampler estratificado** para garantizar ≥4 tiles de cada clase por batch.

### 3.4 Evaluación

#### R9 — Separar Recall@1 por clase en el log de validación
Actualmente solo se reporta el Recall@1 global. Añadir por clase ayudaría a detectar si alguna clase colapsa y cuáles mejoran primero.

---

## 4. Priorización resumida

| # | Acción | Dificultad | Impacto en KPI |
|---|--------|------------|----------------|
| R4 | ReLU en SAE | Muy baja (1 línea) | Sparsity ❌→✅ |
| R1 | Textos más discriminativos | Media (editar parquet) | Recall ❌→⚠️ |
| R2 | Filtro SCL más estricto en train | Baja (1 mask en DataLoader) | Recall ⚠️→⚠️ |
| R5 | λ=1e-2 (tras R4) | Muy baja (1 número) | Sparsity ⚠️→✅ |
| R7 | Cosine LR scheduler | Baja | Recall ⚠️→⚠️ |
| R8 | Sampler estratificado | Media | Recall SO2/O3 |
| R6 | Descongelar ViT (tras baseline) | Media | Recall ⚠️→? |
| R3 | Verificar fechas S5P–S2 | Diagnóstico | Calidad etiquetas |

**Secuencia mínima recomendada para cumplir los KPIs:**

1. Aplicar **R4** (ReLU SAE) + **R5** (λ=1e-2): resolverá la sparsity y probablemente mantendrá o mejorará MSE.
2. Aplicar **R1** (textos nuevos) + **R2** (filtro SCL train): elimina el ruido principal que limita el Recall.
3. Re-entrenar con la configuración base (40 épocas, LR=1e-4, batch=32).
4. Solo si Recall@1 val > 0.15: aplicar **R6** (descongelar ViT) + **R7** (scheduler).

---

## 5. ¿Es necesario más estudio del dataset o del pipeline?

### Lo que ya funciona bien en el pipeline

- División estratificada 70/15/15 por clase: correcta, reproducible.
- Filtro SCL con `metricas_scl()`: lógica sólida, implementación correcta.
- NDVI/BSI sobre píxeles claros solo (`_mascara_claro_scl`): apropiado para S2 L2A.
- Reglas de clasificación con prioridad (`asignar_clase`): consistentes con la física de los contaminantes.
- Interpolación S5P en grilla al centroide: técnicamente correcta (más allá de la resolución del sensor).
- Almacenamiento incremental en Zarr: eficiente y reproducible.

### Lo que sí requiere estudio adicional

| Aspecto | Por qué | Acción concreta |
|---------|---------|-----------------|
| **Calidad real de tiles** | Panel de peores pares muestra tiles oscuros/corruptos que pasaron el filtro | Ejecutar EDA Paso 2–3 en Colab, exportar `tiles_baja_calidad.csv` |
| **Discriminación de textos** | Matriz confusión muestra mezcla entre clases que comparten descripción base | Auditar 10 tiles por clase y comparar descripción vs visual |
| **Coherencia S5P–visual** | Tiles urbanos con "contaminacion_alta_NO2" que visualmente no parecen contaminados | Verificar si `no2` del parquet es plausible para esos tiles |
| **Representatividad del split** | ¿Los tiles de val son de fechas distintas a train o del mismo día? | Cruzar fechas: si hay data leakage temporal, el Recall está inflado |
| **Ozono alto vs bajo** | `ozono_anomalo` agrupa percentil 90 Y percentil 25 en la misma clase | Considerar separar en dos etiquetas o enriquecer la descripción |

### Diagnóstico de data leakage temporal (urgente)

El pipeline usa `train_test_split` estratificado por clase pero **no por fecha**. Si una imagen S2 de 2019-07-14 genera 20 tiles y algunos van a train y otros a val, el modelo puede "memorizar" la apariencia general de esa imagen → Recall inflado en val. Verificar:

```python
# En el parquet descargado:
train_fechas = set(df[df["split"]=="train"]["fecha"])
val_fechas   = set(df[df["split"]=="val"]["fecha"])
solapamiento = train_fechas & val_fechas
print(f"Fechas compartidas train/val: {len(solapamiento)}")  # debería ser ~0 idealmente
```

Si hay solapamiento alto, el 11.4% de Recall@1 podría estar **sobreestimando** la capacidad real del modelo.

---

## 6. Tabla de KPIs proyectados por escenario

| Escenario | Recall@1 | Recall@5 | Sparsity | MSE SAE |
|-----------|----------|----------|----------|---------|
| **Actual** | 0.11 | 0.24 | 0.04 | 0.028 |
| +R4 (ReLU) +R5 (λ=1e-2) | 0.09–0.12 | 0.22–0.27 | ~0.50–0.65 | 0.04–0.07 |
| +R1 (textos) +R2 (filtro SCL) | 0.15–0.22 | 0.35–0.48 | — | — |
| Todo anterior + R7 (LR scheduler) | 0.20–0.30 | 0.45–0.60 | — | — |
| Todo anterior + R6 (descongelar ViT) | 0.30–0.45 | 0.55–0.70 | — | — |
| **KPI mínimo** | **0.45** | **0.70** | **0.70** | **≤ 0.05** |

> Las proyecciones son estimaciones conservadoras basadas en el comportamiento de CLIP/RemoteCLIP en otros datasets de teledetección con ~1000–5000 pares. Alcanzar exactamente 0.45 con solo ~1050 pares de entrenamiento es ambicioso; la consigna puede asumir que se llegará con más datos o con el descongelamiento del ViT.

---

*Generado a partir de: `metricas_por_epoca.json`, `embeddings_val_mejor.npz`, `pipeline/dataset_sit2_par_imagen_texto.py`, `dataset_sit2/resumen.json`, `dataset_sit2/percentiles.json`.*
