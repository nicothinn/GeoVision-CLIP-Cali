# Papers CLIP en teledetección — Guía para Sit.2 (GeoVision-CLIP)

Esta carpeta reúne las referencias que fundamentan el entrenamiento de **GeoVision-CLIP** sobre tiles Sentinel-2 de Cali: pares imagen–texto, InfoNCE, LoRA, diversidad de captions y métricas Recall@k.

| Archivo | Paper / recurso | Año / venue |
|---------|-----------------|-------------|
| [SkyScript.md](./SkyScript.md) | SkyScript (Stanford) | AAAI-24 |
| [RS5M and GeoRSCLIP.md](./RS5M and GeoRSCLIP.md) | RS5M + GeoRSCLIP | arXiv / journal |
| [Rethinking Remote Sensing CLIP.md](./Rethinking%20Remote%20Sensing%20CLIP.md) | RSM-CLIP / RSM-ITD | — |
| [RS-CLIP Zero shot.md](./RS-CLIP%20Zero%20shot.md) | RS-CLIP | JAG 2023 |
| [RESEARCH_NOTES_IMPLEMENTACION.md](./RESEARCH_NOTES_IMPLEMENTACION.md) | Snippets listos para notebooks | proyecto |

**Recursos externos** (no están como `.md` aquí, pero están en las notas de implementación):

- **OpenCLIP Discussion #812** — fine-tuning con CSV, LR, `list_pretrained()`
- **XLM-RoBERTa + open_clip** — modelo `xlm-roberta-base-ViT-B-32` (laion5b) para captions en español

---

## Cómo encaja todo en tu proyecto

```mermaid
flowchart TB
  subgraph datos [Datos Sit.2]
    T[tiles 12 bandas]
    C[captions diversos EN/ES]
    S[split por img_id_s2]
  end
  subgraph train [Entrenamiento]
    L[LoRA ViT + texto]
    I[InfoNCE simétrico]
    R[Recall@1/@5 val]
  end
  subgraph papers [De dónde viene cada pieza]
    SKY[SkyScript]
    GEO[GeoRSCLIP]
    RSM[Rethinking]
    RS[RS-CLIP]
  end
  SKY --> C
  RSM --> C
  RS --> C
  GEO --> L
  GEO --> I
  SKY --> R
  datos --> train
```

| Problema en Sit.2 | Paper que más ayuda |
|-------------------|---------------------|
| Pocos pares (~2k tiles) | **Rethinking** (calidad > escala), **GeoRSCLIP** (LoRA) |
| Captions poco discriminativos | **SkyScript**, **Rethinking** (A2C), **RS-CLIP** (plantillas) |
| Leakage train/val | Split por escena (práctica alineada con estudios de leakage en el notebook) |
| Números mal tokenizados por BPE CLIP | Verbalizar magnitud, estación, NDVI (**Rethinking**, **SkyScript**) |
| Texto en español | **Notebook B** + open_clip XLM-RoBERTa (no es un paper de esta carpeta) |
| Métricas de consigna R@1 / R@5 | **GeoRSCLIP**, **SkyScript**, **Rethinking** |

---

## 1. SkyScript — `SkyScript.md`

### De qué trata

- Construye **SkyScript**: ~**2,6M** pares imagen–texto uniendo imágenes RS abiertas con etiquetas de **OpenStreetMap** (coordenadas → tags key–value).
- Entrena **SkyCLIP** con continual pre-training contrastivo (estilo CLIP) sobre ViT-B/32 y ViT-L/14.
- Demuestra zero-shot en clasificación de escenas, atributos finos y **retrieval** cross-modal.

### Ideas clave

1. **Diversidad semántica** importa más que solo volumen bruto.
2. Captions **ricas en atributos** (no solo nombre de clase):  
   *"power plant, plant source of solar, plant output electricity of 19.9 MW"*.
3. Dos textos por imagen: objeto foco (`title`) y multi-objeto (`title_multi_objects`).
4. **Filtro de calidad**: quedarse con el top 20–50% de pares según similitud CLIP imagen–texto.
5. LR muy bajo en continual PT (orden **1e-9 – 3e-9**), WD alto (~1.0).

### Cómo te ayuda en Sit.2

| Aplicación | En tu pipeline |
|------------|----------------|
| Caption diversity | Celda 27: `MAGNITUDE_LEVELS`, `SEASONS_CALI`, `URBAN_CONTEXTS`, varias plantillas por clase |
| Números en texto | Verbalizar contaminante y NDVI en frases, no solo `NO2=1.23e-4` |
| Métricas | Reportar Recall@1, @5 y opcionalmente mean recall (R@1+R@5+R@10)/3 |
| Filtrado (opcional) | Descartar pares con baja similitud CLIP antes de entrenar si el dataset es ruidoso |

### Cita accionable

> *"Diversity > quantity"* — priorizar redacciones distintas por tile antes de duplicar filas sin variación.

---

## 2. RS5M y GeoRSCLIP — `RS5M and GeoRSCLIP.md`

### De qué trata

- **RS5M**: ~**5 millones** de pares imagen–texto RS (filtrado de LAION + captions sobre datasets solo-etiqueta).
- Marco **GVLM → DVLM → DTM**: el modelo de dominio (GeoRSCLIP) absorbe conocimiento RS y alimenta tareas downstream.
- **GeoRSCLIP**: fine-tune de CLIP (ViT-B/32, B/16, L/16, H/14) con full FT o **PEFT** (LoRA, Pfeiffer, prefix-tuning, UniPELT).
- Benchmarks fuertes en **zero-shot classification**, **retrieval** (RSICD, RSITMD) y localización semántica.

### Ideas clave

1. **LoRA** en CLIP RS es competitivo con full fine-tuning y mucho más barato en GPU.
2. Receta típica: AdamW, **LR ≈ 1e-6**, **WD = 0.5**, batch grande (700 en A100; tú escalas a 32), scheduler coseno, AMP.
3. Retrieval de referencia (CLIP baseline vs GeoRSCLIP+LoRA en RSICD): R@1 i2t sube de ~5% a ~9–11% con adaptación de dominio.
4. Meta-captions con contexto geográfico y temporal (ciudad, país, estación, GSD, nubes…) mejoran alineación.
5. Criterio **rotacional** para elegir la mejor caption entre candidatas (estabilidad bajo rotación de la imagen).

### Cómo te ayuda en Sit.2

| Aplicación | En tu pipeline |
|------------|----------------|
| LoRA | `LORA_RANK=16`, bloques ViT 6–11; en XLM también en capas RoBERTa (`query`, `key`, `value`, `dense`) |
| Hiperparámetros | WD 0.5, LR ~2e-5 (escalado desde guías open_clip para batch pequeño) |
| InfoNCE | Pérdida contrastiva simétrica estándar del notebook |
| KPIs | Comparar tus R@1/R@5 con tablas RSICD/RSITMD como referencia de techo realista |
| Pocos datos | Con <5k pares, LoRA + captions buenos es la combinación recomendada en el paper |

### Cita accionable

> GeoRSCLIP + LoRA en RSITMD: i2t R@1 **16.37** vs baseline CLIP **9.51** — valida que PEFT en dominio RS sí mueve la aguja.

---

## 3. Rethinking Remote Sensing CLIP — `Rethinking Remote Sensing CLIP.md`

### De qué trata

- Critica datasets RS imagen–texto hechos con reglas simples (solo una clase por frase, texto repetitivo).
- Propone **RSM-ITD** (~480k pares / ~476k captions) con:
  - **A2C** (Annotation to Caption): **todas** las categorías en la frase + posición centro/borde.
  - **A2I** + **Kosmos-2** para captions más naturales desde detección/segmentación.
- Entrena **RSM-CLIP** (full fine-tune openCLIP) y supera GeoRSCLIP/SkyCLIP en varios benchmarks **usando ~10× menos datos** que GeoRSCLIP.

### Ideas clave

1. **Calidad de caption > escala del dataset** (mensaje central para Sit.2).
2. Regla **A2C**:  
   *"There are three cars in the center of this image and two trucks at the edge."*
3. Incluir en cada caption: **todos los atributos relevantes** (NDVI, urbano, magnitud del contaminante, estación).
4. InfoNCE + openCLIP; ViT-B-32 con lr ~2e-5, batch 256; ViT-L-14 más conservador.
5. Retrieval zero-shot: RSM-CLIP mejora mean recall en RSITMD/RSICD frente a CLIP y a veces a GeoRSCLIP.

### Cómo te ayuda en Sit.2

| Aplicación | En tu pipeline |
|------------|----------------|
| Diseño de `generar_descripcion_v2` | Una frase con magnitud + contexto urbano + estación + NDVI verbalizado + contaminante |
| Evitar captions ambiguos | No describir solo `"contaminacion_alta_NO2"`; usar plantillas múltiples (A2C spirit) |
| Argumentación académica | Justificar por qué con ~2k tiles enfocas diversidad y split por escena, no “más datos” |
| Métricas | Recall@1/@5 en val como KPI principal del proyecto |

### Cita accionable

> *"Despite using only one-tenth the training data compared to GeoRSCLIP"* — en consigna puedes citar que el diseño de texto importa tanto como el tamaño.

---

## 4. RS-CLIP — `RS-CLIP Zero shot.md`

### De qué trata

- CLIP (ViT, ResNet) para **clasificación de escenas RS** con supervisión contrastiva imagen–texto.
- **Zero-shot** con prompts de clase; **pseudo-labeling** + **curriculum learning** cuando no hay pares etiquetados.
- Matriz de similitud N×N y pérdida **cross-entropy simétrica** (equivalente a InfoNCE).
- No es un paper de retrieval con captions libres, sino de **prompts por clase** y adaptación sin etiquetas.

### Ideas clave

1. Plantilla que funciona en RS:  
   **`"This is an aerial image of a [CLASS]"`**  
   (mejor que *"a photo of"* para datos aéreos).
2. Arquitectura estándar: encoder imagen + encoder texto, **sin fusión temprana**.
3. Pseudo-labels: top-K muestras más confiantes **por clase**, mismo número por clase (balanceado).
4. Curriculum: K crece por etapas (ej. 20 → 40 → 50 por clase en UCM).
5. LR ~1e-5, batch 24, 300 steps por etapa de curriculum.

### Cómo te ayuda en Sit.2

| Aplicación | En tu pipeline |
|------------|----------------|
| Prefijo de caption | Notebook A: `PREFIX_AERIAL = "An aerial Sentinel-2 tile over Cali showing..."` |
| InfoNCE | Justificación teórica de la pérdida del notebook |
| Si faltan pares en el futuro | Estrategia pseudo-label + curriculum (no implementada aún, pero documentada) |
| Zero-shot baseline | Comparar tu modelo fine-tuned vs prompts fijos por clase antes/después del train |

### Cita accionable

> *"This is an aerial image of a [CLASS]"* — patrón RS-CLIP adaptado a descripciones continuas en lugar de solo `[CLASS]`.

---

## 5. Notas de implementación — `RESEARCH_NOTES_IMPLEMENTACION.md`

No es un paper: es el **puente código ↔ papers** con snippets ya alineados a:

- `notebookresultados_Cliptexto.ipynb` (RemoteCLIP + CLIP texto + VisualProj)
- `notebookresultados_XLM-roberta.ipynb` (XLM-RoBERTa multilingüe, sin VisualProj)

Úsalo cuando estés editando celdas 27–32 o exportando FAISS.

---

## Mapa rápido: qué leer según tu duda

| Si te preguntas… | Lee primero |
|------------------|-------------|
| ¿Cómo escribir mejores captions? | SkyScript + Rethinking |
| ¿LoRA, LR, WD, batch? | GeoRSCLIP |
| ¿Por qué InfoNCE y prompts aéreos? | RS-CLIP |
| ¿Qué métricas reportar? | GeoRSCLIP + SkyScript (Recall@k, mean recall) |
| ¿Código concreto del notebook? | RESEARCH_NOTES_IMPLEMENTACION |
| ¿Español en el encoder de texto? | open_clip XLM-RoBERTa (notas §2 Notebook B) |

---

## Notebooks del repo

| Notebook | Encoder texto | Visual | Captions |
|----------|---------------|--------|----------|
| `notebooks/notebookresultados_Cliptexto.ipynb` | RemoteCLIP + CLIP (BPE 77 tok) | ViT + LoRA + **VisualProj** | Inglés, diversidad estructurada |
| `notebooks/notebookresultados_XLM-roberta.ipynb` | XLM-RoBERTa (`xlm-roberta-base-ViT-B-32`) | ViT + LoRA, sin VisualProj | Español, sinónimos |

**KPIs consigna (val):** Recall@1 ≥ 0.45, Recall@5 ≥ 0.70 (excelencia 0.65 / 0.85).

---

## Referencias bibliográficas (resumen)

1. **SkyScript** — Wang et al., AAAI 2024. Dataset OSM + SkyCLIP.  
2. **GeoRSCLIP / RS5M** — Zhang et al. Dataset 5M + DVLM + LoRA.  
3. **Rethinking RS-CLIP (RSM-CLIP)** — He et al. RSM-ITD, A2C, MLLM captions.  
4. **RS-CLIP** — Li et al., *Int. J. Applied Earth Obs.* 2023. Zero-shot + pseudo-label + curriculum.

---

*Última actualización: alineado con implementación Sit.2 sin SAE — GeoVision-CLIP.*
