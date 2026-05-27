"""Sparse Autoencoder con expansión 4x: 512 → 2048 → 512 con ReLU."""

from __future__ import annotations

import torch
import torch.nn as nn


class SparseAutoencoder(nn.Module):
    """
    SAE con expansión 4x: Linear(512, 2048) → ReLU → Linear(2048, 512).
    Coincide con sae_best.pt entrenado en visual_512.pt.
    """

    def __init__(self, d_model: int = 512, d_hidden: int = 2048):
        super().__init__()
        # Sin bias en encoder ni decoder (coincide con sae_best.pt)
        self.encoder = nn.Linear(d_model, d_hidden, bias=False)
        self.decoder = nn.Linear(d_hidden, d_model, bias=False)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        z = torch.relu(self.encoder(x))
        x_hat = self.decoder(z)
        return x_hat, z


def sae_loss(
    x: torch.Tensor,
    x_hat: torch.Tensor,
    z: torch.Tensor,
    lambda_l1: float = 1e-3,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    mse = nn.functional.mse_loss(x_hat, x)
    l1 = z.abs().mean()
    total = mse + lambda_l1 * l1
    return total, mse, l1
