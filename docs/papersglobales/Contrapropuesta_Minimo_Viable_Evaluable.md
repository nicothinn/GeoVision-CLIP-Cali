# Contrapropuesta de Alcance: Mínimo Viable Evaluable (MVE)

## Contexto

Con base en la consigna del proyecto final (`consigna_proyecto.md`), proponemos formalmente ajustar el alcance a un **Mínimo Viable Evaluable (MVE)** que conserve el rigor académico, pero sea ejecutable en 4 semanas por un equipo de 3 estudiantes con disponibilidad parcial.

La propuesta **no elimina** los objetivos del curso; los **prioriza y acota** para garantizar:

- cumplimiento verificable de resultados;
- trazabilidad técnica (evidencia reproducible);
- calidad metodológica en lugar de volumen excesivo de componentes simultáneos.

---

## Objetivo de la contrapropuesta

Solicitar aprobación de un alcance mínimo que permita:

1. demostrar competencias núcleo del curso;
2. entregar un sistema funcional extremo a extremo;
3. sostener defensa técnica consistente por cualquier integrante;
4. evaluar con criterios claros y medibles.

---

## Propuesta MVE por situación

## Situación 1 (Panel de datos + cloud)

### Lo que se mantiene

- Pipeline reproducible de ingesta y transformación.
- Almacenamiento en objeto cloud (GCS/S3/Azure Blob).
- Manifest JSON versionado con hashes MD5.
- EDA con visualizaciones y métricas de calidad de datos.

### Ajuste de alcance propuesto

- Reducir ventana temporal de 5 años a **18-24 meses** para ejecución académica.
- Reducir cobertura geográfica a **bbox Cali urbano + estaciones DAGMA** (sin expansión regional completa).
- Mantener umbral de volumen en **>= 50 GB** usando particionado eficiente (Zarr/Parquet), pero sin exigir descarga de escenarios TB.

### Criterios mínimos evaluables (Sit. 1)

- Dataset final verificable >= 50 GB.
- Manifest con: ruta, fuente, fecha, dimensiones, bbox, MD5.
- Evidencia de ejecución paralela (Dask/Spark) y tiempos de corrida.
- Notebook EDA con al menos 8 visualizaciones.

---

## Situación 2 (Modelo multimodal)

### Lo que se mantiene

- Entrenamiento de modelo multimodal basado en CLIP.
- Inclusión de SAE (al menos en rama visual) y métricas de sparsity.
- Métricas de retrieval y evidencia de entrenamiento.

### Ajuste de alcance propuesto

- Mantener dataset de **>= 1000 pares imagen-texto**.
- Hacer **AFC opcional**; mantener AFE obligatoria para validez exploratoria.
- Reducir calibración extensa de hiperparámetros a una grilla pequeña y justificada.

### Criterios mínimos evaluables (Sit. 2)

- Checkpoint reproducible con MD5.
- Curvas de loss y sparsity por época.
- Reporte AFE completo (scree, cargas, varianza acumulada).
- Cumplir al menos 4/7 KPIs mínimos, justificando técnicamente los no alcanzados.

---

## Situación 3 (Predicción geoestadística)

### Lo que se mantiene

- Predicción para NO2, SO2 y O3 en horizontes T+1, T+3, T+7.
- Integración DL + Kriging.
- Validación externa contra estaciones DAGMA.
- Entrega de mapas de predicción e incertidumbre.

### Ajuste de alcance propuesto

- Usar malla espacial reducida (resolución más gruesa) para garantizar latencia razonable.
- Priorizar **Kriging 2D por horizonte** como mínimo obligatorio; dejar ST-Kriging 3D como componente de excelencia.
- Mantener LOO-CV, pero con protocolo fijo y documentado para evitar sobrecosto experimental.

### Criterios mínimos evaluables (Sit. 3)

- Endpoint funcional que recibe (lat, lon, horizonte) y retorna predicción + incertidumbre.
- 9 mapas (3 contaminantes x 3 horizontes) en frontend.
- LOO-CV reportado por contaminante (RMSE, MAE, R2).
- Moran global obligatorio; LISA como valor agregado.

---

## Frontend, despliegue y reproducibilidad

### Lo que se mantiene

- Frontend profesional (React/Vue/Next) con Leaflet.
- Backend API (FastAPI) con endpoint de inferencia.
- Contenerización Docker.
- URL pública funcional.

### Ajuste de alcance propuesto

- Mantener funcionalidades esenciales:
  - selección de contaminante y horizonte;
  - consulta por clic en mapa;
  - visualización de predicción + incertidumbre.
- Dejar exportación GeoTIFF como opcional (CSV obligatorio).

### Criterios mínimos evaluables

- Demo funcional en vivo.
- Latencia objetivo <= 12 s en entorno free tier (con registro de tiempos).
- Trazabilidad: seeds, hashes, logs, versiones de dependencias.

---

## Distribución sugerida de evaluación (si se aprueba MVE)

- Situación 1: 25%
- Situación 2: 25%
- Situación 3: 30%
- Frontend + despliegue: 10%
- Informe + defensa: 10%

Esta redistribución prioriza competencias técnicas troncales y verificabilidad.

---

## Solicitud formal al docente

Solicitamos aprobar por escrito esta modalidad MVE para nuestro equipo, con rúbrica explícita de cumplimiento mínimo por situación.

Nos comprometemos a:

- entregar evidencia reproducible;
- documentar de forma transparente limitaciones y decisiones;
- implementar extensiones adicionales si el tiempo lo permite.

---

## Texto breve sugerido para enviar al profesor

Profesor(a),  
Con respeto solicitamos acordar un **Mínimo Viable Evaluable (MVE)** del proyecto final, manteniendo los objetivos de aprendizaje y la rigurosidad técnica, pero con un alcance ejecutable en 4 semanas por un equipo de 3 estudiantes con disponibilidad parcial.  

Adjuntamos una propuesta con criterios verificables por situación (datos, modelo, validación geoestadística y despliegue), incluyendo evidencia reproducible (MD5, logs, métricas, notebooks ejecutados).  

Quedamos atentos a su validación o ajustes para trabajar con expectativas claras y asegurar una entrega sólida y defendible.

---

## Cierre

Esta contrapropuesta busca equilibrar **exigencia académica** y **factibilidad real**, enfocando la evaluación en resultados demostrables y replicables.
