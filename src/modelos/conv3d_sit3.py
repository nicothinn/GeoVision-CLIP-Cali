import torch
import torch.nn as nn
import torch.nn.functional as F


class Conv3DSit3(nn.Module):
    '''3D CNN para series de tiempo espacio-temporales (Situacion 3).

    Arquitectura:
      Input: (B, T=8, C=522, H=5, W=5)
      -> Permute a (B, C, T, H, W)
      -> Bottleneck 1x1x1: 522 -> 32
      -> Conv3D(32->64, k=3) + BN + ReLU + MaxPool3d(2)
      -> Conv3D(64->128, k=3) + BN + ReLU + MaxPool3d(2)
      -> AdaptiveAvgPool3d(1) -> Flatten -> (B, 128)
      -> Dropout
      -> 3 cabezas lineales separadas (una por contaminante)
      -> Output: (B, 3 horizontes, 3 contaminantes)
    '''
    def __init__(self, input_channels=522, num_timesteps=8,
                 hidden_dim=64, num_horizons=3, num_pollutants=3,
                 dropout_prob=0.3):
        super().__init__()
        self.num_horizons = num_horizons
        self.num_pollutants = num_pollutants

        # Bottleneck: reducir 522 canales a 32
        self.bottleneck = nn.Conv3d(input_channels, 32, kernel_size=1)
        self.bn_bottleneck = nn.BatchNorm3d(32)

        # Bloque 1: (B, 32, 8, 5, 5) -> (B, 64, 4, 3, 3)
        self.conv1 = nn.Conv3d(32, 64, kernel_size=(3, 3, 3), padding=(1, 1, 1))
        self.bn1 = nn.BatchNorm3d(64)
        self.pool1 = nn.MaxPool3d(kernel_size=(2, 2, 2))

        # Bloque 2: (B, 64, 4, 3, 3) -> (B, 128, 2, 2, 2)
        self.conv2 = nn.Conv3d(64, 128, kernel_size=(3, 3, 3), padding=(1, 1, 1))
        self.bn2 = nn.BatchNorm3d(128)
        self.pool2 = nn.MaxPool3d(kernel_size=(2, 2, 2))

        # Pooling global y dropout
        self.global_pool = nn.AdaptiveAvgPool3d(1)
        self.dropout = nn.Dropout(dropout_prob)

        # Cabezas separadas por contaminante
        # Cada cabeza: 128 features -> 3 horizontes
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

    def forward(self, x):
        '''Forward pass.

        Args:
            x: (B, T, C, H, W) con T=8 timesteps, C=522 canales, H=W=5
        Returns:
            (B, num_horizons, num_pollutants)
        '''
        # Permute: (B, T, C, H, W) -> (B, C, T, H, W) para Conv3d
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
        x = self.global_pool(x)          # (B, 128, 1, 1, 1)
        x = x.flatten(1)                  # (B, 128)
        x = self.dropout(x)

        # Cabezas separadas
        outs = [head(x) for head in self.heads]  # cada una: (B, 3)

        # Stack: (B, num_horizons, num_pollutants)
        return torch.stack(outs, dim=-1)
