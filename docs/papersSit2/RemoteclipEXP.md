# 🛰️ RemoteCLIP — Explicación para principiantes

> **Paper original:** *"RemoteCLIP: A Vision Language Foundation Model for Remote Sensing"*
> Autores: Fan Liu, Delong Chen, y otros (2023-2024)
> Publicado en: arXiv:2306.11029

---

## 📌 Índice

1. [¿Qué problema intenta resolver este paper?](#1-qué-problema-intenta-resolver-este-paper)
2. [Glosario: todas las palabras técnicas explicadas](#2-glosario-todas-las-palabras-técnicas-explicadas)
3. [La idea central: explicada con una analogía](#3-la-idea-central-explicada-con-una-analogía)
4. [¿Cómo funciona RemoteCLIP? — Paso a paso](#4-cómo-funciona-remoteclip--paso-a-paso)
5. [El truco secreto: Data Scaling (escalar los datos)](#5-el-truco-secreto-data-scaling-escalar-los-datos)
6. [Resultados: ¿qué tan bueno es?](#6-resultados-qué-tan-bueno-es)
7. [Conexión con nuestro proyecto GeoVision-CLIP-Cali](#7-conexión-con-nuestro-proyecto-geovision-clip-cali)
8. [Resumen en una sola frase](#8-resumen-en-una-sola-frase)

---

## 1. ¿Qué problema intenta resolver este paper?

### El problema antes de RemoteCLIP

Imagina que tienes miles de fotos satelitales y quieres que una computadora las entienda. Antes de este paper, los modelos de inteligencia artificial para imágenes satelitales funcionaban más o menos así:

| Método antiguo | Cómo funciona | Problema |
|---------------|---------------|----------|
| **Masked Image Modeling (MIM)** | Se tapa un pedazo de la imagen y el modelo intenta adivinarlo | Solo aprende texturas y formas básicas, no entiende el significado |
| **Self-Supervised Learning (SSL)** | El modelo aprende solo, sin necesidad de etiquetas humanas | Necesita que luego alguien le enseñe con datos etiquetados (fine-tuning) |

**El gran problema:** Estos modelos NO podían:
- ❌ Entender lenguaje humano ("muéstrame fotos de aeropuertos")
- ❌ Hacer zero-shot (clasificar algo que nunca antes habían visto)
- ❌ Relacionar imágenes con texto automáticamente

### Lo que RemoteCLIP propone

> **"Hagamos un modelo que entienda TANTO las imágenes satelitales COMO el lenguaje humano, y que pueda relacionarlos entre sí."**

Básicamente, es como crear un traductor universal entre **fotos de satélite** y **texto en español/inglés**.

---

## 2. Glosario: todas las palabras técnicas explicadas

Antes de seguir, vamos a definir cada término técnico que aparece en el paper:

### Conceptos básicos de IA

| Término técnico | Significado en lenguaje simple | Analogía |
|----------------|-------------------------------|----------|
| **Foundation Model** (Modelo Fundacional) | Un modelo de IA gigante que se entrena una sola vez con muchísimos datos, y luego sirve para muchas tareas distintas sin volver a entrenarlo desde cero. | Como un médico general que estudió 10 años: después puede especializarse en cardiología, pediatría, o cirugía sin volver a estudiar medicina desde cero. |
| **Fine-tuning** (Ajuste fino) | Tomar un modelo ya entrenado y darle un "cursito rápido" con datos específicos de tu tarea. | Como el médico general que hace una especialidad de 2 años en cardiología. |
| **Pre-training** (Pre-entrenamiento) | El entrenamiento inicial masivo con millones de datos. | Los 10 años de carrera de medicina. |
| **Continual Pretraining** | Seguir entrenando un modelo ya pre-entrenado con datos nuevos de un área específica (en este caso, imágenes satelitales). | Como si después de la carrera de medicina, el médico hiciera una maestría en "medicina aeroespacial". |

### Conceptos sobre cómo aprende la IA

| Término | Significado simple | Analogía |
|---------|-------------------|----------|
| **Self-Supervised Learning (SSL)** | La máquina aprende sola, sin que un humano le diga "esto es un avión, esto es un bosque". Ella misma se inventa la tarea. | Como un niño que aprende a distinguir perros de gatos solo viendo muchos, sin que nadie le explique. |
| **Masked Image Modeling (MIM)** | Se tapa una parte de la imagen y la IA intenta reconstruir lo que falta. | Como un rompecabezas: te dan la imagen con un hueco y tienes que adivinar qué va ahí. |
| **Contrastive Learning** (Aprendizaje Contrastivo) | La IA aprende comparando: "estas dos cosas son parecidas" vs "estas dos son diferentes". | Como jugar "encuentra las diferencias" pero al revés: la IA aprende qué hace que dos cosas sean similares. |
| **Zero-shot** (Cero ejemplos) | Capacidad de reconocer algo NUNCA antes visto en el entrenamiento. | Como si nunca has visto un ornitorrinco, pero alguien te dice "es un animal con pico de pato, cola de castor y pone huevos", y cuando lo ves por primera vez, lo reconoces. |
| **Few-shot** (Pocos ejemplos) | Aprender a reconocer algo viendo solo 1, 2, 4, 8 o 16 ejemplos. | Como si te muestran 4 fotos de un edificio específico y ya puedes identificarlo en otras imágenes. |

### Conceptos sobre la arquitectura del modelo

| Término | Significado simple | Analogía |
|---------|-------------------|----------|
| **Encoder** (Codificador) | La parte del modelo que convierte algo (una imagen o un texto) en una lista de números que la computadora puede procesar. | Como un traductor que convierte una frase en español a código morse. |
| **Image Encoder** | El encoder específico para imágenes. Convierte una foto en un vector de números. | Una cámara que en vez de sacar una foto, saca una lista de 512 números que describen la foto. |
| **Text Encoder** | El encoder específico para texto. Convierte una frase en un vector de números. | Un escáner de texto que produce una lista de 512 números que capturan el significado de la frase. |
| **ViT (Vision Transformer)** | Un tipo específico de encoder para imágenes. Divide la imagen en cuadraditos (patches) y los procesa como si fueran palabras. | Como leer un periódico: tus ojos no ven cada píxel, ven palabras (patches) y entienden el significado general. |
| **ResNet (Residual Network)** | Otro tipo de encoder para imágenes, más antiguo que ViT pero aún muy usado. Procesa la imagen con capas de convoluciones. | Como un filtro de Instagram con muchas capas: cada capa detecta algo (bordes, texturas, formas). |
| **Transformer** | La arquitectura base de los modelos modernos de IA. Procesa secuencias (de palabras o de parches de imagen) prestando atención a las relaciones entre todos los elementos. | Como un equipo de editores: cada editor lee todo el texto, pero cada uno se fija en algo distinto (gramática, estilo, contenido). |
| **Backbone** (Columna vertebral) | La estructura principal del modelo. El "esqueleto" sobre el que se construye todo lo demás. | Como el chasis de un carro: puedes ponerle diferentes motores, llantas o pintura, pero la estructura base es la misma. |

### Conceptos sobre el entrenamiento

| Término | Significado simple | Analogía |
|---------|-------------------|----------|
| **InfoNCE Loss** (Función de pérdida InfoNCE) | La fórmula matemática que le dice al modelo qué tan bien o mal lo está haciendo. Mide: ¿qué tan cerca están las imágenes de sus textos correctos? | Como un profesor que califica exámenes: si la respuesta correcta está cerca de lo que escribiste, buena nota. Si está lejos, mala nota. |
| **Temperatura (τ)** | Un número que controla qué tan "estricto" es el modelo al decidir si dos cosas son parecidas. | Como ajustar la sensibilidad de un detector de metales: si está muy sensible, todo suena; si está muy bajo, no detecta nada. |
| **Batch Size** (Tamaño del lote) | Cuántas imágenes procesa el modelo al mismo tiempo durante el entrenamiento. | Como cuántos exámenes califica el profesor a la vez antes de tomar un descanso. |
| **Epoch** (Época) | Una pasada completa por todos los datos de entrenamiento. | Como leer un libro completo de principio a fin. |
| **Learning Rate** (Tasa de aprendizaje) | Qué tan rápido aprende el modelo. Muy alto = aprende rápido pero puede equivocarse. Muy bajo = aprende lento pero más preciso. | Como la velocidad a la que lees un libro: muy rápido y no entiendes nada, muy lento y tardas años. |
| **Cosine Learning Rate Scheduler** | Una estrategia para ir bajando la velocidad de aprendizaje gradualmente, como una ola que va y viene suavemente. | Como cuando empiezas a correr rápido y vas bajando el ritmo poco a poco hasta caminar. |
| **Linear Warm-up** | Los primeros pasos del entrenamiento se hacen con velocidad baja, y se va subiendo gradualmente. | Como calentar antes de hacer ejercicio: empiezas suave y luego aumentas la intensidad. |
| **Adam Optimizer** | Un algoritmo específico para ajustar los "pesos" del modelo durante el entrenamiento. Es uno de los más populares. | Como un GPS que te va corrigiendo la ruta poco a poco en vez de mandarte por un camino completamente nuevo cada vez. |
| **Automatic Mixed Precision (AMP)** | Técnica que usa números menos precisos (16 bits en vez de 32 bits) para ahorrar memoria y acelerar el entrenamiento, sin perder mucha calidad. | Como mandar una foto por WhatsApp: la comprime un poco para que llegue más rápido, pero casi ni se nota la diferencia. |

### Conceptos sobre evaluación

| Término | Significado simple | Analogía |
|---------|-------------------|----------|
| **Recall@K (R@K)** | De todas las respuestas correctas que existen, ¿cuántas aparecen entre las primeras K predicciones del modelo? | Imagina que hay 10 libros correctos para tu búsqueda. Si el modelo te muestra 5 resultados y 3 son correctos, el Recall@5 es 3/10 = 30%. |
| **Mean Recall** (Recall promedio) | El promedio de R@1, R@5 y R@10. Da una idea general del rendimiento. | Como sacar el promedio de tus notas en 3 exámenes. |
| **Linear Probing** | Congelar el modelo principal y solo entrenar una capa adicional muy simple para una tarea específica. | Como ponerle una lupa a una cámara ya existente en vez de construir una cámara nueva. |
| **k-NN Classification** (k Vecinos más Cercanos) | Clasificar algo viendo a qué grupo pertenecen sus K vecinos más cercanos. | Como adivinar de qué país es una persona viendo el acento de sus 20 vecinos más cercanos. |
| **SOTA (State Of The Art)** | "Lo mejor que existe actualmente". El récord mundial en esa tarea. | Como el récord olímpico actual en 100 metros planos. |
| **Overfitting** (Sobre-ajuste) | Cuando el modelo se aprende los datos de entrenamiento DE MEMORIA en vez de aprender patrones generales. Luego falla con datos nuevos. | Como un estudiante que se memoriza las respuestas del examen del año pasado pero no entiende la materia: si le cambian las preguntas, truena. |
| **Ablation Study** (Estudio de ablación) | Experimento donde se quita una parte del modelo para ver qué tan importante era. | Como quitarle una llanta al carro para ver si aún funciona: así sabes qué tan importante era esa llanta. |

### Conceptos de datos

| Término | Significado simple | Analogía |
|---------|-------------------|----------|
| **Bounding Box** (Caja delimitadora) | Un rectángulo que encierra un objeto en una imagen. Se define con 4 números: (x, y) de la esquina superior izquierda y (x, y) de la esquina inferior derecha. | Como cuando encierras una cara en un círculo en una foto de Instagram, pero con rectángulo. |
| **Semantic Segmentation** (Segmentación Semántica) | Clasificar CADA píxel de una imagen en una categoría (edificio, carretera, vegetación, agua...). | Como colorear un mapa: cada país de un color distinto. Pero aquí cada píxel de la imagen es de un color según lo que representa. |
| **Annotation** (Anotación) | La información que un humano agrega a los datos para decir "esto es X". | Como cuando etiquetas a tus amigos en una foto de Facebook: estás "anotando" quién es quién. |
| **Caption** (Leyenda/Descripción) | Un texto que describe lo que hay en una imagen. | Como el pie de foto en un periódico: "Aviones estacionados en un aeropuerto cerca de árboles verdes." |
| **Data Augmentation** (Aumentación de datos) | Crear versiones modificadas de las imágenes originales (rotadas, volteadas, recortadas) para que el modelo vea más variedad sin necesidad de conseguir más datos reales. | Como si tuvieras una sola foto tuya y con Photoshop creas 10 versiones: rotada, en espejo, recortada, etc. |
| **P-Hash** (Perceptual Hash) | Una "huella digital" de una imagen. Un código corto que identifica imágenes visualmente similares. | Como el código de barras de un producto: dos productos iguales tienen el mismo código. |
| **De-duplication** (Eliminación de duplicados) | Borrar imágenes repetidas del dataset para que el modelo no vea lo mismo dos veces. | Como quitar las fotos repetidas de tu álbum antes de imprimirlo. |
| **T-SNE (t-Distributed Stochastic Neighbor Embedding)** | Una técnica para visualizar datos de muchas dimensiones (como vectores de 512 números) en un plano 2D que podamos ver. | Como hacer un mapa plano de una ciudad 3D: pierdes algo de información, pero puedes ver todo de un vistazo. |

### Otros términos importantes

| Término | Significado simple |
|---------|-------------------|
| **Downstream Task** (Tarea derivada) | Cualquier tarea específica para la que uses el modelo DESPUÉS de entrenarlo: clasificar imágenes, buscar imágenes por texto, contar objetos, etc. |
| **Cross-modal Retrieval** (Recuperación entre modalidades) | Buscar imágenes usando texto como consulta, o buscar texto usando imágenes. Cruzar de un "modo" (visual) a otro (texto). |
| **Multi-modality** (Multi-modalidad) | Que un modelo trabaje con varios tipos de datos a la vez: imágenes + texto + sonido + etc. |
| **Representation** (Representación) | El vector de números que produce el encoder. Es la "huella digital" de una imagen o texto en el espacio matemático del modelo. |
| **L-2 Normalization** | Ajustar un vector para que tenga longitud = 1. Esto permite comparar direcciones sin que la magnitud afecte. |
| **Cosine Similarity** (Similitud Coseno) | Una medida de qué tan parecidos son dos vectores, basada en el ángulo entre ellos (no en su tamaño). -1 = opuestos, 0 = no relacionados, 1 = idénticos. |
| **UAV (Unmanned Aerial Vehicle)** | Vehículo aéreo no tripulado. Básicamente: drones. |

---

## 3. La idea central: explicada con una analogía

### Imagina que quieres enseñarle a un niño sobre animales...

**Enfoque antiguo (MIM/SSL):**
Le muestras miles de fotos de animales con pedazos tapados, y le pides que adivine qué falta. El niño aprende texturas y formas ("esto es peludo", "esto tiene escamas"), pero NO aprende los nombres de los animales ni puede decirte "eso es un león".

**Enfoque de RemoteCLIP:**
Le muestras al niño una foto de un león Y le dices "esto es un león, el rey de la selva, un felino grande con melena". Ahora el niño:
- ✅ Reconoce al león en cualquier foto (incluso si nunca había visto esa foto exacta)
- ✅ Si le dices "muéstrame un felino con melena", te señala la foto del león
- ✅ Si le pides que cuente cuántos leones hay en una foto, puede hacerlo
- ✅ Aprendió el CONCEPTO de "león", no solo su textura

### La frase clave del paper

> **"Data scaling es más importante que arquitectura compleja."**

Traducción: Tener MUCHOS datos diversos es mejor que tener un modelo super complicado con pocos datos. RemoteCLIP triunfa porque encontró una forma ingeniosa de crear muchísimos datos sin contratar un ejército de humanos para etiquetar.

---

## 4. ¿Cómo funciona RemoteCLIP? — Paso a paso

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA REMOTECLIP                       │
│                                                                 │
│                         ┌──────────┐                            │
│    IMAGEN SATELITAL ──► │  IMAGE   │ ──► vector de 512 números  │
│    (256×256 píxeles)    │ ENCODER  │     (representación visual) │
│                         │ ViT-B/32 │                            │
│                         └──────────┘                            │
│                                          ↘                      │
│                              InfoNCE Loss ←  ¿Qué tan cerca     │
│                                          ↗   están estos dos    │
│                         ┌──────────┐        vectores?           │
│    TEXTO DESCRIPTIVO ──► │  TEXT    │ ──► vector de 512 números  │
│    ("edificios blancos") │ ENCODER  │     (representación texto) │
│                         │Transformer│                            │
│                         └──────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

### Explicación detallada de cada paso

#### Paso 1: Preparar los datos (lo más importante)

RemoteCLIP se entrena con **165,745 imágenes satelitales**, y cada imagen tiene **5 descripciones de texto** (captions). En total son **828,725 pares imagen-texto**.

¿Cómo consiguieron tantos datos? Esa es la genialidad del paper. Pero eso lo explicamos en detalle en la [sección 5](#5-el-truco-secreto-data-scaling-escalar-los-datos).

#### Paso 2: El Image Encoder (el que "ve")

La imagen entra al modelo. Pero las computadoras no "ven" imágenes: necesitan convertirlas a números.

**¿Cómo funciona un ViT (Vision Transformer)?**

1. La imagen de 256×256 píxeles se divide en cuadraditos de 32×32 píxeles llamados **patches**. Una imagen de 256×256 dividida en patches de 32×32 da 64 patches (8×8).
2. Cada patch se "aplana" en una lista de números (32 × 32 × 3 colores = 3072 números por patch).
3. El Transformer procesa todos los patches SIMULTÁNEAMENTE, prestando atención a cómo se relacionan entre sí. Por ejemplo: "este patch que parece un ala está al lado de este otro que parece un fuselaje → probablemente es un avión".
4. Al final, produce un solo vector de 512 números que representa TODA la imagen.

**Los modelos usados en el paper:**

| Modelo | Tamaño | Significado |
|--------|--------|-------------|
| ResNet-50 | 38 millones de parámetros | Modelo pequeño, rápido, menos preciso |
| ViT-Base-32 | 87 millones de parámetros | Modelo mediano, balance velocidad/precisión |
| ViT-Large-14 | 304 millones de parámetros | Modelo grande, más lento pero el más preciso |

> **¿Qué son los "parámetros"?** Son los números que el modelo ajusta durante el entrenamiento. Imagina que el modelo es una calculadora gigante con millones de perillas: cada perilla es un parámetro. Más parámetros = más capacidad de aprender cosas complejas, pero también más lento y más costoso de entrenar.

#### Paso 3: El Text Encoder (el que "lee")

El texto descriptivo (por ejemplo: "White buildings and tennis courts are beside the gray road") entra al Text Encoder.

**¿Cómo funciona el Transformer para texto?**

1. El texto se divide en **tokens** (palabras o partes de palabras). "White buildings and tennis courts" → ["White", "buildings", "and", "tennis", "courts"]
2. Cada token se convierte en un vector de números (embedding).
3. El Transformer procesa todos los tokens y presta atención a las relaciones: "buildings" está relacionado con "white", "tennis" con "courts".
4. Produce un vector de 512 números que captura el SIGNIFICADO de la frase completa.

El Text Encoder de RemoteCLIP tiene 12 capas y 8 "cabezas de atención" (attention heads). El texto máximo es de 77 tokens (aproximadamente 77 palabras).

#### Paso 4: La pérdida InfoNCE (el "profesor")

Esta es la parte MÁS importante del entrenamiento. Así es como el modelo aprende:

**Dentro de un lote (batch) de 256 pares imagen-texto:**

1. Para cada imagen, se calcula qué tan parecida es a:
   - Su propio texto correcto → debe ser MUY parecida (alta similitud)
   - Los textos de las otras 255 imágenes → debe ser POCO parecida (baja similitud)

2. Lo mismo al revés: cada texto debe ser muy parecido a SU imagen correcta y poco parecido a las otras 255 imágenes.

3. La fórmula InfoNCE convierte esto en un número (la "pérdida"). El objetivo es MINIMIZAR ese número.

**¿Por qué se llama "temperatura" (τ)?**

La temperatura controla qué tan "exigente" es el modelo:
- τ baja (ej. 0.07) → el modelo es muy estricto: pequeñas diferencias importan mucho
- τ alta (ej. 1.0) → el modelo es más relajado

RemoteCLIP aprende la temperatura durante el entrenamiento (es un parámetro más que se ajusta solo). Empieza en 0.07.

#### Paso 5: Dos propiedades mágicas que emergen

Al optimizar la pérdida InfoNCE, el modelo desarrolla dos capacidades automáticamente:

| Propiedad | Qué significa | Para qué sirve |
|-----------|---------------|----------------|
| **Alignment** (Alineación) | Imagen y su texto correcto terminan en el mismo lugar del espacio matemático | Buscar imágenes con texto (retrieval) |
| **Grouping** (Agrupación) | Imágenes parecidas entre sí terminan juntas, aunque no tengan texto | Clasificar imágenes sin necesidad de texto (linear probing) |

> **Analogía:** Es como una biblioteca donde el bibliotecario (el modelo) aprende a poner cada libro junto a su ficha correcta (alignment), y además agrupa todos los libros de ciencia ficción juntos aunque no tengan fichas (grouping).

---

## 5. El truco secreto: Data Scaling (escalar los datos)

### El problema original

Solo existían 3 datasets con imágenes satelitales que tuvieran descripciones de texto escritas por humanos (RET-3: RSICD, RSITMD, UCM). En total: apenas **13,000 pares imagen-texto**.

Para que un modelo grande (CLIP) funcione bien, necesita MILLONES de pares. Con solo 13,000, el modelo sufre **overfitting**: se memoriza los datos de entrenamiento y no aprende a generalizar.

### La solución ingeniosa de RemoteCLIP

En vez de contratar humanos para escribir descripciones de más imágenes (muy caro y lento), los investigadores encontraron una mina de oro: ya existían muchísimos datasets satelitales con **otro tipo de anotaciones**:

| Tipo de dataset | Qué tienen anotado | Ejemplos | Cantidad de imágenes |
|----------------|-------------------|----------|---------------------|
| **Detección (DET-10)** | Bounding boxes con etiquetas: "avión", "barco", "edificio"... | DOTA, DIOR, VisDrone | ~126,000 |
| **Segmentación (SEG-4)** | Cada píxel etiquetado con su categoría | iSAID, LoveDA, Potsdam | ~41,000 |
| **Retrieval (RET-3)** | Descripciones de texto escritas por humanos | RSICD, RSITMD, UCM | ~13,000 |

El truco fue convertir TODAS esas anotaciones a un formato común: **imagen + texto descriptivo**.

### Técnica 1: B2C — Box-to-Caption (De caja a descripción)

**Problema:** Los datasets de detección tienen bounding boxes (rectángulos) con etiquetas como "avión", "barco", etc. Pero el Text Encoder de CLIP solo entiende lenguaje natural, no coordenadas de rectángulos.

**Solución:** Crear un programa que convierta las cajas en frases descriptivas.

**Así funciona el programa B2C:**

```
Imagen satelital con bounding boxes:
┌─────────────────────────────────┐
│                                 │
│   ┌──────┐          ┌──────┐    │
│   │ AVION│          │AVION │    │
│   │  1   │          │  2   │    │
│   └──────┘          └──────┘    │
│                                 │
│        ┌────────────┐           │
│        │   TORRE DE  │           │
│        │   CONTROL   │           │
│        └────────────┘           │
└─────────────────────────────────┘
```

Para esta imagen, B2C genera **5 descripciones distintas**:

1. **Caption 1 (objetos en el centro):** "An airplane in the middle of the picture."
2. **Caption 2 (objetos fuera del centro):** "Some planes are parked in an airport near a piece of green trees."
3. **Caption 3 (objetos aleatorios):** "4 large vehicles, a small vehicle and 5 planes at the edge of the picture."
4. **Caption 4 (objetos aleatorios variación):** "A crowd of cars are located in this remote sensing picture."
5. **Caption 5 (objetos aleatorios otra variación):** "Lots of airplanes are located in the picture."

**Reglas del programa:**
- Si hay más de 10 objetos del mismo tipo, en vez de decir "15 aviones" dice "muchos aviones" (suena más natural).
- Los primeros dos captions siempre distinguen centro vs bordes (agrega información espacial).
- Los otros tres captions seleccionan objetos aleatoriamente para dar variedad.

### Técnica 2: M2B — Mask-to-Box (De máscara a caja)

**Problema:** Los datasets de segmentación tienen CADA PÍXEL etiquetado (este píxel es "edificio", este otro es "carretera"). Pero B2C solo funciona con bounding boxes.

**Solución intermedia:** Convertir las máscaras de segmentación en bounding boxes.

**Así funciona M2B:**

```
Máscara de segmentación:          Bounding boxes resultantes:
┌────────────────────┐            ┌────────────────────┐
│ ░░░░░░░░░░░░░░░░░░ │            │ ┌──────┐           │
│ ░░░░████░░░░░░░░░░ │            │ │EDIF. │           │
│ ░░░░████░░░░░░░░░░ │    →       │ └──────┘           │
│ ░░░░░░░░░░▓▓▓▓▓░░░ │            │        ┌────┐     │
│ ░░░░░░░░░░▓▓▓▓▓░░░ │            │        │CAR.│     │
│ ░░░░░░░░░░░░░░░░░░ │            │        └────┘     │
└────────────────────┘            └────────────────────┘
 ████ = edificio, ▓▓▓ = carretera
```

**Paso a paso del algoritmo:**

1. Separar la máscara por categorías: una imagen binaria solo con los píxeles "edificio", otra solo con "carretera", etc.
2. Para cada categoría, encontrar el **contorno** (la frontera de la mancha) usando el algoritmo de Suzuki (un método clásico de procesamiento de imágenes).
3. Del contorno, sacar el rectángulo mínimo que lo contiene: (x_min, y_min) y (x_max, y_max).
4. ¡Listo! Ya tenemos bounding boxes. Ahora aplicar B2C para generar las descripciones.

### Resultado del data scaling

| Fuente | Tipo de anotación original | Cuántas imágenes | Método de conversión |
|--------|---------------------------|-----------------|---------------------|
| RET-3 (3 datasets) | Descripciones humanas | 13,000 | Usadas directamente |
| DET-10 (10 datasets) | Bounding boxes | 126,000 | B2C |
| SEG-4 (4 datasets) | Máscaras de segmentación | 41,000 | M2B → B2C |
| **TOTAL** | | **165,745 imágenes** | **× 5 captions = 828,725 pares** |

**12 veces más datos** que todos los datasets de texto-imagen satelital existentes combinados.

### Control de calidad: eliminación de duplicados

Como los datos vienen de muchas fuentes distintas, algunas imágenes podrían estar repetidas. Para evitar que el modelo "haga trampa" (vea la misma imagen en entrenamiento y en evaluación), usan una técnica llamada **P-Hash**:

- Cada imagen se convierte en un código único (hash) basado en su contenido visual.
- Si dos imágenes tienen códigos muy parecidos (distancia de Hamming < 2), son duplicadas.
- Se eliminan entre 40 y 3,000 imágenes duplicadas por dataset.

---

## 6. Resultados: ¿qué tan bueno es?

RemoteCLIP se evaluó en muchísimas tareas diferentes para demostrar que es versátil. Aquí los resultados principales:

### 6.1 Recuperación de imágenes por texto (Cross-modal Retrieval)

**La tarea:** Dado un texto como "un avión en un aeropuerto", encontrar la imagen correcta entre cientos.

**Resultados en RSITMD (el dataset más difícil):**

| Modelo | Recall@1 | Recall@5 | Recall@10 | Mean Recall |
|--------|----------|----------|-----------|-------------|
| Mejor modelo ANTERIOR (Rahhal 2022) | 19.69% | 40.26% | 54.42% | 41.38% |
| CLIP original (ViT-L-14) | - | - | - | 35.60% |
| **RemoteCLIP (ViT-B-32)** | **27.88%** | **50.66%** | **65.71%** | **49.38%** |
| **RemoteCLIP (ViT-L-14)** | **28.76%** | **52.43%** | **63.94%** | **50.52%** |

> **¿Qué significa Recall@1 = 28.76%?** De cada 100 búsquedas, en 29 de ellas la imagen correcta fue la PRIMERA que mostró el modelo. Puede parecer bajo, pero para imágenes satelitales con descripciones complejas, es un resultado excelente.

**Mejora:** +9.14% sobre el mejor modelo anterior. 🎉

### 6.2 Clasificación Zero-shot (reconocer sin haber visto nunca)

**La tarea:** Clasificar imágenes satelitales en categorías que el modelo NUNCA vio durante el entrenamiento.

**Cómo se hace:** Se crea un texto para cada categoría posible ("a satellite photo of airport", "a satellite photo of forest", etc.) y se calcula cuál es más parecido a la imagen.

**Resultados en 12 datasets diferentes (promedio, ViT-B-32):**

| CLIP original | RemoteCLIP | Mejora |
|---------------|------------|--------|
| 56.02% | **62.41%** | **+6.39%** |

En algunos datasets la mejora es ESPECTACULAR:
- WHU-RS19: CLIP = 80.61%, RemoteCLIP = **96.12%** (+15.51%)
- AID: CLIP = 65.65%, RemoteCLIP = **91.30%** (+25.65%)

### 6.3 Clasificación Few-shot (aprender con poquitos ejemplos)

**La tarea:** Clasificar imágenes teniendo solo 1, 2, 4, 8, 16 o 32 ejemplos por categoría.

**Resultado:** Con solo 32 ejemplos por clase, RemoteCLIP superó a TODOS los demás modelos en TODOS los 12 datasets evaluados.

> **Dato curioso:** Incluso con solo 32 ejemplos, RemoteCLIP superó a modelos que se entrenaron con TODOS los datos de entrenamiento disponibles (full-shot). Esto demuestra lo poderoso que es el pre-entrenamiento.

### 6.4 Conteo de objetos (RemoteCount)

Los investigadores crearon un NUEVO benchmark para probar si RemoteCLIP puede contar objetos en imágenes satelitales.

**La tarea:** Dada una imagen con varios aviones y el texto "there are 3 planes", ¿puede el modelo identificar cuántos aviones hay realmente? (respuestas del 1 al 10)

**Resultado:** RemoteCLIP demostró una capacidad de conteo mucho mejor que CLIP original, especialmente para números del 1 al 6. La matriz de confusión de RemoteCLIP muestra una diagonal mucho más clara (la mayoría de predicciones correctas caen en la diagonal).

### 6.5 Linear Probing y k-NN (con todos los datos)

**Linear Probing:** Se congela el modelo (no se modifica) y solo se entrena una capa adicional súper simple para clasificar.

**Resultado promedio en 12 datasets (ViT-B-32):**

| Modelo | Linear Probing | k-NN (k=20) |
|--------|---------------|-------------|
| CLIP original | 92.31% | 92.15% |
| RemoteCLIP | **93.93%** | **93.77%** |

### 6.6 Hallazgos de los estudios de ablación (¿qué partes son importantes?)

Los investigadores hicieron experimentos quitando partes del sistema para ver qué era esencial:

1. **Pre-entrenamiento de ambos encoders:** Si quitas el pre-entrenamiento del Image Encoder o del Text Encoder, el rendimiento cae drásticamente. Ambos son necesarios.

2. **Rotación de imágenes:** Aplicar rotaciones aleatorias (0°, 90°, 180°, 270°) durante el entrenamiento SÍ mejora los resultados en recuperación de imágenes.

3. **InfoNCE es la mejor pérdida:** Compararon InfoNCE contra otras 4 funciones de pérdida y InfoNCE fue la mejor por mucho.

4. **Cada grupo de datos aporta:** Los datasets de detección (DET-10) son los que más contribuyen, pero la combinación de los tres grupos (RET-3 + DET-10 + SEG-4) es la que da los mejores resultados.

---

## 7. Conexión con nuestro proyecto GeoVision-CLIP-Cali

### ¿Qué usa nuestro proyecto de RemoteCLIP?

Nuestro modelo **GeoVisionCLIP** usa RemoteCLIP de la siguiente manera:

```
┌────────────────────────────────────────────────────────────┐
│              ARQUITECTURA GeoVision-CLIP-Cali               │
│                                                            │
│  Imagen Sentinel-2    BandAdapter    RemoteCLIP ViT-B/32   │
│  (13 bandas, 64×64) ──► (13→3) ──► Image Encoder (FROZEN)│
│                                                   │        │
│                                          vector 512d       │
│                                                   │        │
│                                        ┌── SAE (entrenable) │
│                                        │   │                │
│                                        │   ▼                │
│                                        │ vector 256d        │
│                                        │                    │
│  Texto descriptivo    MiniLM          │                    │
│  ("contaminacion     Text Encoder ──► vector 512d           │
│   alta NO2")          (entrenable)           │              │
│                                        ┌── SAE (entrenable) │
│                                        │   │                │
│                                        │   ▼                │
│                                        │ vector 256d        │
│                                        │                    │
│                              InfoNCE Loss ◄─────────────────│
│                              (misma que RemoteCLIP)         │
└────────────────────────────────────────────────────────────┘
```

**Componentes que tomamos prestados de RemoteCLIP:**
- ✅ **ViT-B/32 como Image Encoder** — pero lo dejamos CONGELADO (no lo entrenamos, usamos los pesos que RemoteCLIP ya aprendió)
- ✅ **Pérdida InfoNCE** — exactamente la misma fórmula
- ✅ **Temperatura aprendible (τ)** — el modelo ajusta τ solo durante el entrenamiento
- ✅ **Estrategia de alineación imagen-texto** — mismo concepto de acercar pares correctos y alejar incorrectos

**Componentes que son NUESTROS (no vienen de RemoteCLIP):**
- 🆕 **BandAdapter (13→3):** RemoteCLIP espera imágenes RGB de 3 canales. Nosotros tenemos 13 bandas de Sentinel-2. El BandAdapter convierte inteligentemente 13 bandas a 3.
- 🆕 **MiniLM como Text Encoder:** RemoteCLIP usa un Transformer genérico. Nosotros usamos MiniLM, que es multilingüe y más ligero.
- 🆕 **SAE (Sparse Autoencoder):** RemoteCLIP no tiene esto. Es nuestra contribución: comprimimos los vectores de 512 a 256 dimensiones forzando que sean "sparse" (muchos ceros), lo que hace el modelo más interpretable.
- 🆕 **Clases de contaminación:** Nuestras 5 categorías (contaminacion_alta_NO2, contaminacion_alta_SO2, ozono_anomalo, vegetacion_densa, suelo_urbano) son únicas de nuestro proyecto.

### Lecciones de RemoteCLIP que aplican a nuestro proyecto

1. **Los datos son MÁS importantes que la arquitectura.** RemoteCLIP triunfó porque expandió sus datos 12×, no porque inventó una arquitectura complicada. Nuestros 1350 pares están bien balanceados, y la diversidad de contaminantes + bandas espectrales es una ventaja que pocos datasets tienen.

2. **El pre-entrenamiento es PODEROSO.** El hecho de que RemoteCLIP ya haya aprendido a "ver" imágenes satelitales nos da una ventaja ENORME. Estamos parados sobre hombros de gigante.

3. **La pérdida InfoNCE es suficiente.** No necesitamos funciones de pérdida complicadas. InfoNCE, bien implementada, hace el trabajo.

4. **La temperatura aprendible importa.** τ = 0.07 es un buen punto de partida, pero dejar que el modelo la ajuste puede mejorar el rendimiento.

5. **Las rotaciones como data augmentation ayudan.** En imágenes satelitales (vista cenital), rotar 90°, 180°, 270° es válido porque no hay un "arriba" fijo.

---

## 8. Resumen en una sola frase

> **RemoteCLIP tomó el modelo CLIP original (entrenado con millones de fotos de internet), lo re-entrenó con 828,725 pares de imágenes satelitales + texto (creados ingeniosamente a partir de anotaciones ya existentes), y obtuvo un modelo que entiende imágenes de satélite y lenguaje humano simultáneamente, superando todo lo que existía antes.**

---

## 📚 Para profundizar

- **Código oficial de RemoteCLIP:** https://github.com/ChenDelong1999/RemoteCLIP
- **Pesos pre-entrenados disponibles:** ViT-B/32, ViT-L/14, ResNet-50
- **Paper original de CLIP (OpenAI):** ["Learning Transferable Visual Models from Natural Language Supervision"](https://arxiv.org/abs/2103.00020) — Es el paper que inventó todo esto. Si quieres entender de dónde viene CLIP, empieza aquí.

---

*Este documento fue creado como guía de estudio para el proyecto GeoVision-CLIP-Cali. Explica el paper RemoteCLIP en lenguaje accesible para personas sin formación técnica avanzada en inteligencia artificial.*
