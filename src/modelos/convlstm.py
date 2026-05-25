"""Modelo ConvLSTM 1D + MLP para prediccion espacio-temporal (Situacion 3).

Arquitectura:
  X=(N,8,522,5,5) -> AvgPool2d(5) -> X_avg=(N,8,522)
    -> LSTM(2 capas, hidden=256) -> h_N=(N,256)
    -> MLP(256->128->64->9) -> y_pred=(N,3,3)

Uso:
    model = ConvLSTM1DModel(hidden_dim=256, num_layers=2, dropout=0.2)
    y_pred = model(x)  # x: (N, 8, 522, 5, 5)
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class ConvLSTM1DModel(nn.Module):
    """Modelo ConvLSTM 1D con promedio espacial + LSTM + MLP.

    Args:
        input_channels: Canales de entrada (default: 522).
        seq_len: Largos de secuencia temporal (default: 8).
        hidden_dim: Dimension oculta del LSTM (default: 256).
        num_layers: Numero de capas LSTM (default: 2).
        dropout: Dropout entre capas LSTM y en MLP (default: 0.2).
        num_horizons: Horizontes de prediccion (default: 3).
        num_pollutants: Contaminantes a predecir (default: 3).
    """

    def __init__(
        self,
        input_channels: int = 522,
        seq_len: int = 8,
        hidden_dim: int = 256,
        num_layers: int = 2,
        dropout: float = 0.2,
        num_horizons: int = 3,
        num_pollutants: int = 3,
    ):
        super().__init__()

        self.input_channels = input_channels
        self.seq_len = seq_len
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.num_horizons = num_horizons
        self.num_pollutants = num_pollutants

        # 1. Average pooling espacial: (N,8,522,5,5) -> (N,8,522)
        self.avg_pool = nn.AdaptiveAvgPool2d(1)

        # 2. LSTM
        self.lstm = nn.LSTM(
            input_size=input_channels,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
            bidirectional=False,
        )

        # 3. MLP
        self.mlp = nn.Sequential(
            nn.Linear(hidden_dim, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, num_horizons * num_pollutants),
        )

        self._init_weights()

    def _init_weights(self):
        """Inicializa pesos del LSTM y MLP."""
        for name, param in self.lstm.named_parameters():
            if "weight" in name:
                nn.init.orthogonal_(param)
            elif "bias" in name:
                nn.init.zeros_(param)

        for module in self.mlp:
            if isinstance(module, nn.Linear):
                nn.init.kaiming_uniform_(module.weight, mode="fan_in", nonlinearity="relu")
                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Tensor de entrada (N, 8, 522, 5, 5).

        Returns:
            y_pred: Tensor de salida (N, 3, 3).
        """
        # x: (N, 8, C, H, W) -> (N, 8, C)
        N, T, C, H, W = x.shape
        x_reshaped = x.view(N * T, C, H, W)  # (N*8, 522, 5, 5)
        x_pooled = self.avg_pool(x_reshaped).squeeze(-1).squeeze(-1)  # (N*8, 522)
        x_pooled = x_pooled.view(N, T, C)  # (N, 8, 522)

        # LSTM
        lstm_out, (h_n, _) = self.lstm(x_pooled)  # h_n: (num_layers, N, hidden_dim)
        last_hidden = h_n[-1]  # (N, hidden_dim) - ultima capa

        # MLP
        y_flat = self.mlp(last_hidden)  # (N, 9)
        y_pred = y_flat.view(N, self.num_horizons, self.num_pollutants)  # (N, 3, 3)

        return y_pred


def masked_mse_loss(
    y_pred: torch.Tensor,
    y_true: torch.Tensor,
    weights: torch.Tensor | None = None,
) -> torch.Tensor:
    """MSE loss que ignora valores NaN y aplica pesos por contaminante.

    Cada contaminante tiene un peso independiente para balancear la loss.
    Por defecto usa pesos [100, 10, 1] para [NO2, SO2, O3].

    Args:
        y_pred: (N, 3, 3) predicciones del modelo.
        y_true: (N, 3, 3) targets con posibles NaN.
        weights: (3,) pesos por contaminante. Si es None, usa [100, 10, 1].

    Returns:
        loss: Escalar, MSE ponderado sobre valores validos.
    """
    if weights is None:
        weights = torch.tensor([100.0, 10.0, 1.0], device=y_pred.device)

    weights = weights.to(y_pred.device)
    mask = ~torch.isnan(y_true)
    n_valid = mask.sum().float()

    if n_valid < 1.0:
        return torch.tensor(0.0, device=y_pred.device, requires_grad=True)

    # MSE por contaminante (promedio sobre horizontes y batch)
    loss_per_poll = torch.zeros(3, device=y_pred.device)
    for p in range(3):
        pmask = mask[:, :, p]
        if pmask.sum() > 0:
            loss_per_poll[p] = F.mse_loss(
                y_pred[:, :, p][pmask],
                y_true[:, :, p][pmask],
                reduction="mean",
            )

    # Ponderar y promediar
    weighted_loss = (loss_per_poll * weights).sum() / weights.sum()
    return weighted_loss
