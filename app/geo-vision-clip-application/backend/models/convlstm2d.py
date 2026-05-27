"""Conv3DSit3 — CNN 3D para predicción espacio-temporal.
Arquitectura exacta del checkpoint best.ckpt (531 canales).

    Input:  (B, T=8, C=531, H=5, W=5) → permute(0,2,1,3,4)
    Bottleneck Conv3d(531→32, 1×1×1) + BN + ReLU
    Conv3d(32→64, 3×3×3) + BN + ReLU + MaxPool3d(2)
    Conv3d(64→128, 3×3×3) + BN + ReLU + MaxPool3d(2)
    AdaptiveAvgPool3d(1) → Flatten → Dropout
    3 cabezas Linear(128→3) → stack → (B, 3, 3)
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class Conv3DSit3(nn.Module):
    """3D CNN para series espacio-temporales (Situacion 3)."""

    def __init__(
        self,
        input_channels: int = 531,
        num_horizons: int = 3,
        num_pollutants: int = 3,
        dropout_prob: float = 0.3,
    ):
        super().__init__()
        self.num_horizons = num_horizons
        self.num_pollutants = num_pollutants

        # Bottleneck: reducir 531→32 con 1×1×1
        self.bottleneck = nn.Conv3d(input_channels, 32, kernel_size=1)
        self.bn_bottleneck = nn.BatchNorm3d(32)

        # Bloque 1: 32→64, kernel 3×3×3 + MaxPool
        self.conv1 = nn.Conv3d(32, 64, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm3d(64)
        self.pool1 = nn.MaxPool3d(kernel_size=2)

        # Bloque 2: 64→128, kernel 3×3×3 + MaxPool
        self.conv2 = nn.Conv3d(64, 128, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm3d(128)
        self.pool2 = nn.MaxPool3d(kernel_size=2)

        # Pooling global + dropout
        self.global_pool = nn.AdaptiveAvgPool3d(1)
        self.dropout = nn.Dropout(dropout_prob)

        # 3 cabezas separadas (una por contaminante)
        self.heads = nn.ModuleList([
            nn.Linear(128, num_horizons) for _ in range(num_pollutants)
        ])

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, (nn.Conv3d, nn.Linear)):
                nn.init.xavier_uniform_(m.weight, gain=0.5)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, T, C, H, W) con T=8 timesteps, C=531 canales, H=W=5
        Returns:
            (B, num_pollutants, num_horizons)
        """
        # Permute para Conv3d: (B, T, C, H, W) → (B, C, T, H, W)
        x = x.permute(0, 2, 1, 3, 4)

        # Bottleneck
        x = self.bottleneck(x)
        x = self.bn_bottleneck(x)
        x = F.relu(x)

        # Bloque 1
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.pool1(x)

        # Bloque 2
        x = self.conv2(x)
        x = self.bn2(x)
        x = F.relu(x)
        x = self.pool2(x)

        # Pooling global
        x = self.global_pool(x)   # (B, 128, 1, 1, 1)
        x = x.flatten(1)          # (B, 128)
        x = self.dropout(x)

        # 3 cabezas → (B, 3, 3) = (B, num_pollutants, num_horizons)
        outs = [head(x) for head in self.heads]
        return torch.stack(outs, dim=1)
