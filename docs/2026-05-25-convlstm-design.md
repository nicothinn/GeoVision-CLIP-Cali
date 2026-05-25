# Diseno: Modelo ConvLSTM 1D + MLP para Situacion 3

## Fecha
2026-05-25

## Problema
Predecir concentraciones de NO2, SO2 y O3 en 3 horizontes temporales (T+1, T+3, T+7)
a partir de secuencias de 8 tiles Sentinel-2 (procesados por RemoteCLIP+LoRA)
cuyos targets son columnas de NO2, SO2 y O3 del Sentinel-5P.

## Datos de entrada
- `dataset_sit3/X_convlstm.npy`: (1403, 8, 522, 5, 5)
- `dataset_sit3/y_convlstm.npy`: (1403, 3, 3), 94.4% valores validos
- Fuente S5P: HuggingFace (Slucu-0310/geovision-cali-panel)

## Arquitectura

```
X = (N, 8, 522, 5, 5)
         |
  AvgPool2d(5) -> (N, 8, 522)
         |
    LSTM(2 capas, hidden=256)
         |
     h_N = (N, 256)   <- ultimo output
         |
  MLP: Linear(256,128) -> ReLU -> Dropout(0.2) -> Linear(128,64) -> ReLU -> Linear(64,9)
         |
  y_pred = (N, 3, 3)  [reshape a 3 horizontes x 3 contaminantes]
```

### Justificacion de decisiones

1. **AvgPool2d(5)**: La grilla 5x5 es artificial (embedding replicado 25 veces).
   Promediar reduce ruido y mantiene la informacion relevante. Los 512 canales
   del embedding CLIP ya codifican el contenido del tile.

2. **LSTM 2 capas, hidden=256**: Suficiente capacidad para 8 pasos temporales
   con 522 features. Sin bidireccionalidad (no aporta en secuencias cortas).

3. **MLP final**: Proyecta de 256 dimensiones latentes a 9 salidas.
   Dropout(0.2) para regularizar.

4. **No ConvLSTM 2D**: La grilla 5x5 no justifica convoluciones 2D.
   La informacion espacial relevante esta en el embedding, no en la grilla.

## Manejo de NaN

Loss MSE enmascarada: solo computa sobre valores no-NaN de y_true.

## Entrenamiento

| Parametro | Valor |
|---|---|
| Optimizer | AdamW |
| Learning rate | 1e-3 |
| Weight decay | 1e-5 |
| Batch size | 32 |
| Epochs max | 200 |
| Early stopping | patience=20 |
| Scheduler | ReduceLROnPlateau (factor=0.5, patience=10) |
| Gradient clipping | 1.0 |
| Split | 70/15/15 (mismo que Sit2, heredado por secuencia) |
| Framework | PyTorch Lightning |

## Metricas

- Loss MSE enmascarada (validacion)
- RMSE por contaminante y horizonte (validacion y test)
- R2 score por contaminante
- RMSE promedio global (KPI de la consigna)

## Implementacion

### Archivos a crear/modificar

1. `src/modelos/convlstm.py` -> `ConvLSTM1DModel` (modelo PyTorch)
2. `src/training/lit_convlstm.py` -> `LitConvLSTM` (LightningModule)
3. `notebooks/Situacion_3/sit3_entrenar_convlstm.ipynb` (notebook de entrenamiento)
4. Opcional: `pipeline/entrenar_convlstm.py` (script CLI)

### Flujo de datos

```
dataset_sit3/X_convlstm.npy  -->  Sit3ConvLSTMDataset  -->  DataLoader
dataset_sit3/y_convlstm.npy                                    |
                                                               v
                                                        LitConvLSTM
                                                               |
                                                               v
                                                    y_pred = (N, 3, 3)
```

## Referencias
- Tensor generado por: `pipeline/generar_tensor_convlstm.py`
- Embeddings CLIP: `sit2_sae_posttrain.ipynb`
