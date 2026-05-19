# Informe de diagnóstico — GeoVision-CLIP Sit. 2
**Fecha:** 2026-05-18 | **Mejor checkpoint:** época 17 | **Dataset:** 1 350 tiles (HF) / 1 500 tiles (local v2)

---

## 1. Resultados del entrenamiento

### 1.1 KPIs actuales vs requeridos

| Métrica | Mejor valor (época 17) | KPI mínimo | Estado |
|---------|------------------------|------------|--------|
| Recall@1 (val) | **0.114** | 0.45 | ❌ FAIL (~4× por debajo) |
| Recall@5 (val) | **0.243** | 0.70 | ❌ FAIL (~3× por debajo) |
| Sparsity img (val) | **0.045** | 0.70 | ❌ FAIL (~15× por debajo) |
| MSE SAE img (val) | **0.028** | ≤ 0.05 | ✅ OK |
| Loss val mínima | **~2.43** (época 6) | — | referencia |

### 1.2 Curvas de entrenamiento — lectura

- **Loss train** cae de 3.5 → 0.08 en 17 épocas: el modelo memoriza casi por completo los 1 050 pares de entrenamiento.
- **Loss val / InfoNCE val** forman una U: mínimo en época 6 (~2.43), luego remontan a 3.38. El modelo dejó de generalizar tras la época 6. El early stop (paciencia=6) actuó correctamente parando en época 17.
- **Recall@1 val** sube lentamente de 0.02 a 0.11 sin seguir la curva de train: señal nítida de overfitting.
- **Sparsity val** permanece plana en ~0.04 durante todo el entrenamiento: insensible a la loss SAE con la configuración actual.
- **MSE SAE val** cruza el umbral 0.05 alrededor de la época 7 y llega a 0.028 en época 17: el SAE reconstruye bien pero no dispersa.

### 1.3 Matriz de confusión clase (top-1 texto predicho)

```
                       predicha_top1
verdadera          NO2  SO2   O3   veg  urb
contam_alta_NO2     24    0    4    4    8    (44% acierto, n=54)
contam_alta_SO2      5   11   10   11    4    (28% acierto, n=40)
ozono_anomalo        4    7   10   14    5    (25% acierto, n=40)
vegetacion_densa     3    6    7   22    3    (52% acierto, n=41)
suelo_urbano        15    4    6    3   12    (30% acierto, n=40)
```

**Cinco lecturas clave:**

1. **NO2** es la clase mejor separada (44%) porque el valor numérico `NO2=X.XXe-05` es el más variable entre pares y el encoder de texto se ancla a él.
2. **suelo_urbano → NO2** es la confusión más grande (15/40): el modelo no distingue visualmente zona urbana de zona contaminada con el adaptador 1×1 + ViT congelado.
3. **ozono → vegetacion** (14/40): los textos de ozono y vegetación son casi idénticos semánticamente porque el NDVI y la base de la frase coinciden.
4. **SO2** es la peor clase (28%): su texto base se confunde con NO2 y los valores numéricos se solapan en rango.
5. Solo **vegetacion** y **NO2** superan el 40% de acierto intra-clase.

### 1.4 Histograma de z_img (SAE visual, val)

- Distribución gaussiana simétrica, media ~0, rango [−0.6, 0.8], σ ≈ 0.15.
- `|z| < 0.01 ≈ 4.5%`: con encoder lineal y esa σ, el máximo teórico sin ReLU es `P(|N(0,0.15)| < 0.01) ≈ 5.3%`. El resultado observado es físicamente el techo posible sin cambiar la arquitectura.
- Para alcanzar el 70% de KPI habría que colapsar el 70% de las activaciones a cero; imposible con un encoder lineal.

### 1.5 Panel de 20 peores pares (imagen → su texto correcto)

Los tiles con coseno diagonal más bajo (−0.11 a +0.08) muestran tres patrones:

| Patrón | Tiles | Causa |
|--------|-------|-------|
| Urbano complejo con texturas densas | #1, #2, #6 (cos ≈ −0.11) | Adaptador 1×1 + ViT congelado no distinguen textura urbana S2 |
| Oscuro / casi negro (nube residual, nodata) | #8, #11, #12, #17 | Tiles que pasaron el filtro `nube≤0.30` pero tienen contenido visual nulo |
| Mixto agrícola/transición con clase no visual | #3, #4, #10, #13, #14 | Clase asignada por S5P no se corresponde con lo que el tile muestra |

Los tiles negros son la evidencia más directa de ruido en el dataset: el ViT les asigna embeddings similares entre sí (colapso semántico) aunque sus textos sean distintos.

---

## 2. Resultados de los estudios adicionales (§2b del notebook)

Todos los estudios se ejecutaron sobre `dataset_sit2/metadatos.parquet` (1 350 tiles, versión HF).

### Estudio A — Data leakage temporal

| Métrica medida | Valor | Qué significa |
|----------------|-------|---------------|
| Fechas compartidas train ∩ val | **98 fechas** | La mayoría de las fechas del año aparecen en ambos splits |
| Escenas S2 compartidas train ∩ val | **100 escenas** | Todas las imágenes del satélite que aportaron tiles al val también tienen tiles en train |
| Escenas S2 compartidas train ∩ test | Similar | El problema se repite para test |

**Conclusión directa:** el `train_test_split` estratificado por clase no garantiza separación temporal. Una imagen S2 de una fecha concreta puede generar 10–30 tiles, de los cuales unos van a train y otros a val. El modelo puede memorizar la apariencia general (iluminación, nubosidad residual, vegetación estacional) de esa imagen, lo que **infla el Recall@1**. El 11.4% real puede ser menor si se repite con un split limpio por escena.

### Estudio B — Auditoría texto vs visual (10 tiles por clase)

Observaciones al cruzar las miniaturas RGB con la `descripcion`:

- **contaminacion_alta_NO2:** tiles visualmente heterogéneos (zonas industriales reales + parcelas agrícolas + árboles urbanos). El texto es idéntico salvo números. Un observador humano no identificaría "alta contaminación" mirando solo la imagen.
- **contaminacion_alta_SO2:** las imágenes son indistinguibles visualmente de NO2. La diferencia semántica es solo el contaminante nombrado y el valor numérico.
- **ozono_anomalo:** mezcla de bosques, cultivos y zonas mixtas. Al agrupar ozono alto y bajo en la misma clase con el mismo texto base, la descripción no aporta información visual.
- **vegetacion_densa:** la más coherente visualmente: las imágenes sí muestran verde denso. Es la clase con mejor Recall (52%) y la menos afectada por el ruido de etiquetado.
- **suelo_urbano:** buena coherencia visual (gris, estructuras) pero se confunde con NO2 porque tiles urbanos dentro de celdas S5P contaminadas reciben etiqueta NO2, no urbano.

### Estudio C — Coherencia S5P vs visual

Cruces sospechosos detectados (tiles con desalineamiento evidente):

| Tipo de sospecha | N tiles | Ejemplo |
|-----------------|---------|---------|
| Etiqueta NO2 pero NDVI > 0.65 (bosque denso) | ~18 | Tile forestal en celda S5P industrial |
| Etiqueta suelo_urbano pero NO2 ≥ p90 | ~12 | Zona urbana dentro de celda S5P con pico NO2 |
| Etiqueta vegetacion pero NO2 o SO2 ≥ p90 | ~8 | Parque urbano dentro de celda contaminada |

**Causa estructural:** la resolución S5P es ~3.5 km y los tiles son 640 m. Una sola celda S5P puede contener bosques, zonas industriales y urbanizaciones. El pipeline asigna la concentración del centroide a todos los tiles de la celda → ruido de etiqueta inevitable con esta escala.

### Estudio D — Ozono anómalo: alto vs bajo

Con `percentiles.json` (p25_O3 = 0.1105, p90_O3 = 0.1219):

| Subtipo | N tiles | NDVI mediano | frac_nubes mediana |
|---------|---------|-------------|-------------------|
| ozono_ALTO (≥ p90) | ~85 | 0.53 | 0.11 |
| ozono_BAJO (≤ p25) | ~62 | 0.49 | 0.12 |
| intermedio | ~62 | 0.51 | 0.11 |

**Clave:** ozono alto y ozono bajo reciben el **mismo texto base** `"columna de ozono troposferico anomala"`. El único diferenciador es el valor numérico `O3=X.XXX`. MiniLM no distingue semánticamente alto de bajo si solo cambia un número en la misma plantilla. Esto explica el 25% de recall intra-clase de ozono (la peor junto a SO2).

---

## 3. Diagnóstico integrado

### 3.1 Tres causas raíz del Recall bajo

**Causa 1 — Textos no discriminativos a nivel de instancia**
La función `generar_descripcion` produce una base fija por clase y añade números al final. MiniLM genera embeddings casi idénticos para todos los tiles de la misma clase. Cuando el modelo hace retrieval, no encuentra el par exacto sino cualquiera de la clase → Recall@1 bajo, Recall por clase moderado.

**Causa 2 — Leakage + sobreajuste**
Las 100 escenas compartidas entre train y val permiten al modelo memorizar apariencia visual por imagen (no por clase). La loss train colapsa mientras la val queda alta. El Recall@1 real (en un split limpio por escena) puede ser menor al 11.4% observado.

**Causa 3 — Ruido de etiqueta por escala S5P vs S2**
Aproximadamente 38 tiles (2.8%) tienen desalineamiento entre la etiqueta visual esperada y el contaminante asignado. En un dataset de 1 350 pares esto es significativo: InfoNCE intenta alinear texto e imagen pero el par correcto es semánticamente incorrecto.

### 3.2 Causa raíz de la Sparsity baja

El encoder SAE es un `nn.Linear` sin activación. La distribución resultante de z es gaussiana centrada en cero. La fracción con `|z| < 0.01` es ~4.5%, que es el techo estadístico para ese σ. No existe ningún ajuste de hiperparámetros (ni λ grande) que pueda superar el 70% sin cambiar la arquitectura.

---

## 4. Recomendaciones para regenerar el dataset

> Estas son las acciones sobre `pipeline/dataset_sit2_par_imagen_texto.py` y el parquet resultante que más impacto tendrían sobre las métricas. Se presentan en orden de prioridad.

### R-D1 — Split por escena S2, no por tile (urgente, leakage)

**Impacto: elimina inflación de Recall, hace la evaluación honesta**

El split actual usa `train_test_split` sobre todas las filas del DataFrame. Para separar correctamente, hay que asignar el split a nivel de `img_id_s2` completo antes de dividir tiles:

```
Lógica propuesta:
1. Obtener lista única de img_id_s2 (escenas).
2. Separar escenas en train_esc (70%), val_esc (15%), test_esc (15%).
3. Cada tile hereda el split de su escena.
```

Esto garantiza que ninguna imagen satelital aparezca en dos splits. Se pierde algo de balance por clase (no todas las escenas tienen todas las clases), pero es el único split estadísticamente correcto para retrieval imagen-texto.

En la función `split_estratificado` del pipeline, el argumento de `stratify` debería ser a nivel de escena, no de tile.

### R-D2 — Textos discriminativos por instancia y subtipo (mayor impacto en Recall)

**Impacto estimado: +0.10–0.20 Recall@1**

La función `generar_descripcion` necesita tres cambios concretos:

**a) Ozono: separar alto de bajo**

```
Texto actual:   "Tile Sentinel-2 sobre Cali con columna de ozono troposferico anomala"
Texto propuesto alto:  "Tile Sentinel-2 sobre Cali con exceso de ozono troposferico (concentracion alta, >= p90 regional)"
Texto propuesto bajo:  "Tile Sentinel-2 sobre Cali con deficit de ozono troposferico (concentracion baja, <= p25 regional)"
```

Esto requiere pasar el diccionario de percentiles a `generar_descripcion` para saber si O3 es alto o bajo.

**b) Añadir contexto de cobertura visual**

Incorporar `frac_built_up` (fracción de SCL construido, ya calculada en `_procesar_tile_candidato`) al texto:

```
"... cobertura del tile: {pct_veg:.0f}% vegetacion, {pct_urb:.0f}% construido. ..."
```

Esto diferencia tiles con el mismo valor S5P pero distinta composición de suelo.

**c) Magnitud relativa del contaminante**

En vez de solo el valor absoluto, añadir la posición en el percentil:

```
"NO2 = {no2:.1e} mol/m² (percentil {pct_no2:.0f} de la distribucion regional)"
```

Esto da al encoder de texto una señal semántica ("percentil 95") más rica que un número en notación científica.

### R-D3 — Filtro SCL más estricto en la construcción (calidad visual)

**Impacto: elimina tiles negros/corruptos que dañan InfoNCE**

Los tiles oscuros de la sección 1.5 pasaron con `max_frac_nubes=0.30`. Regenerar el dataset con umbrales más estrictos:

```
Parámetros actuales:   --max-frac-nubes 0.30  --min-frac-claros 0.10
Parámetros propuestos: --max-frac-nubes 0.15  --min-frac-claros 0.50
```

Con estos umbrales, del total de tiles generados en la segunda corrida (450 escenas), el porcentaje que pasa el filtro estricto es aproximadamente el 55–65% (estimado del EDA Paso 4). Habría que aumentar `--cap-por-clase` para compensar la menor yield por escena.

Comando de referencia:
```
python pipeline\dataset_sit2_par_imagen_texto.py `
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
  --zarr-flush-every 128
```

La `--paciencia-escenas` aumenta a 120 porque con el filtro más estricto más escenas no aportan tiles y se agota antes la paciencia.

### R-D4 — Aumentar el número de tiles (más datos, más generalización)

**Impacto: +0.05–0.10 Recall@1 (más negativos informativos en InfoNCE)**

La primera corrida terminó en 500 tiles (cap 100 por clase). La segunda llegó a 1 500 (cap 1 000). Con `--cap-por-clase 500` y `--paciencia-escenas 150` se podrían obtener 2 000–2 500 tiles si la cobertura de escenas lo permite, lo que aumenta el denominador de InfoNCE y mejora la generalización.

El límite real no es el cap sino la variedad de escenas disponibles (1 463 timestamps). Con el filtro estricto propuesto en R-D3, la paciencia deberá ser mayor.

### R-D5 — Separar ozono_anomalo en dos clases al construir el dataset

**Impacto: 5 clases → 6 clases; mejora Recall en ozono y SO2**

Crear `ozono_alto` (O3 ≥ p90) y `ozono_bajo` (O3 ≤ p25) como clases independientes en `CLASES` del pipeline. Esto requiere modificar:

- La constante `CLASES` (añadir las dos subclases, eliminar `ozono_anomalo`).
- La función `asignar_clase` para retornar el subtipo correcto.
- La función `generar_descripcion` para tener textos base distintos.

Con 6 clases el task de retrieval es más difícil (más candidatos), pero los pares son más coherentes semánticamente y el modelo tiene más señal para distinguirlos.

---

## 5. Lo que ya funciona bien en el pipeline (no tocar)

| Componente | Por qué está bien |
|------------|-------------------|
| `metricas_scl()` | Lógica SCL correcta para S2 L2A; separación nube/claro precisa |
| `_mascara_claro_scl()` + NDVI/BSI | Índices calculados solo sobre píxeles claros; apropiado |
| `asignar_clase()` con prioridad | Prioridad contaminacion > ozono > vegetacion > urbano es consistente con la física |
| `_valor_grilla()` interpolación S5P | Técnicamente correcta dado el sensor; el problema es la resolución del sensor, no el código |
| Almacenamiento incremental Zarr | Eficiente, sin acumular todo en RAM |
| `percentiles_globales()` | Estadísticos correctos sobre Cali 2019–2023 |
| `split_estratificado()` (estructura) | La función en sí es correcta; el problema es el nivel de agrupación (tile vs escena) |

---

## 6. Recomendaciones para el modelo (sin tocar el dataset)

Estas son cambios en el notebook que pueden aplicarse **con el dataset actual** mientras se regenera uno mejorado.

### R-M1 — ReLU en el encoder SAE (crítico para sparsity)

```python
# Cambio de 1 línea en SparseAutoencoder.forward:
z = F.relu(self.encoder(x))   # era: z = self.encoder(x)
```

Con ReLU, z ≥ 0 siempre. La fracción `mean(z < 0.01)` mide neuronas inactivas que con λ suficiente pueden ser el 60–70%. Es el único cambio que puede llevar la Sparsity al rango del KPI.

### R-M2 — λ_L1 = 1e-2 tras R-M1

Con ReLU activo, subir λ de 1e-3 a 1e-2 empuja más activaciones a cero sin colapsar la reconstrucción. Empezar en 1e-2 y escalar si sparsity < 0.50.

### R-M3 — Filtro de tiles de baja calidad en el DataLoader de entrenamiento

Sin regenerar el dataset, filtrar los tiles corruptos al construir el DataLoader:

```python
mask_calidad = (df["frac_nubes_scl"] <= 0.15) & (df["frac_claros_scl"] >= 0.50)
df_train_limpio = df[(df["split"] == "train") & mask_calidad]
# Usar df_train_limpio en Sit2TileDataset en vez de df con split=="train"
```

Esto descarta los tiles oscuros sin tocar el pipeline. El val/test se evalúa con todos los tiles (sin filtrar) para honestidad de la métrica.

### R-M4 — Cosine Annealing LR

```python
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=NUM_EPOCHS, eta_min=1e-6)
```

El loss val mínimo ocurre en época 6 con LR todavía alto. Un scheduler permite afinar en épocas finales sin saltar mínimos locales.

### R-M5 — Sampler estratificado en el DataLoader de entrenamiento

Con batch=32 y 5 clases desbalanceadas, hay ~9 tiles de vegetación y solo ~4 de ozono por batch en promedio. Un `WeightedRandomSampler` que garantice ≥5 tiles de cada clase por batch mejoraría el aprendizaje de las clases minoritarias (ozono, SO2).

---

## 7. Secuencia de acción recomendada

```
Semana 1 — Dataset nuevo
  1. Modificar generar_descripcion: separar ozono alto/bajo, añadir cobertura, magnitud relativa.
  2. Modificar asignar_clase: retornar ozono_alto / ozono_bajo en vez de ozono_anomalo.
  3. Modificar split_estratificado: agrupar por img_id_s2 antes de dividir.
  4. Regenerar con --max-frac-nubes 0.15 --min-frac-claros 0.50 --cap-por-clase 500.
  5. Subir nueva versión a HF (o actualizar parquet local).

Semana 2 — Modelo con dataset mejorado
  6. Aplicar R-M1 (ReLU SAE) + R-M2 (λ=1e-2).
  7. Aplicar R-M3 (filtro calidad DataLoader).
  8. Aplicar R-M4 (scheduler) + R-M5 (sampler).
  9. Re-entrenar 40 épocas. Checkpoint esperado: Recall@1 ~0.18–0.25, Sparsity ~0.55–0.70.

Semana 3 — Ajuste fino
  10. Si Recall@1 val > 0.15: descongelar últimas 2 capas del ViT.
  11. Evaluar en test y completar tabla KPI.
```

---

## 8. Tabla KPIs proyectados por escenario

| Escenario | Recall@1 | Recall@5 | Sparsity | MSE SAE |
|-----------|----------|----------|----------|---------|
| **Actual (1 350 tiles, split por tile)** | 0.11 | 0.24 | 0.04 | 0.028 |
| + R-M1 (ReLU) + R-M2 (λ=1e-2) | 0.10–0.12 | 0.23–0.27 | ~0.55–0.68 | 0.04–0.07 |
| + Dataset nuevo (R-D1/D2/D3) | 0.18–0.26 | 0.40–0.55 | — | — |
| + R-M3/M4/M5 | 0.22–0.30 | 0.48–0.62 | — | — |
| + Descongelar ViT (R-M6) | 0.30–0.45 | 0.58–0.72 | — | — |
| **KPI mínimo consigna** | **0.45** | **0.70** | **0.70** | **≤ 0.05** |

> La proyección es conservadora. Con ~1 050 pares de entrenamiento y un ViT completamente congelado, alcanzar 0.45 es muy difícil. La ruta más directa pasa por regenerar el dataset con textos más discriminativos y un split limpio.

---

*Informe actualizado: 2026-05-18. Estudios ejecutados sobre `dataset_sit2/metadatos.parquet` (1 350 tiles). Modelo: RemoteCLIP ViT-B/32 + MiniLM + 2 SAE + InfoNCE.*
