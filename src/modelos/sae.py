"""Sparse Autoencoder con reconstrucción L2 y regularización L1 sobre z."""

from __future__ import annotations

import torch
import torch.nn as nn


class SparseAutoencoder(nn.Module):
    """SAE lineal: x -> z -> x_hat, con z de dimensión `dim_latent`."""

    def __init__(self, dim_in: int, dim_latent: int = 512) -> None:
        super().__init__()
        self.dim_in = dim_in
        self.dim_latent = dim_latent
        self.encoder = nn.Linear(dim_in, dim_latent)
        self.decoder = nn.Linear(dim_latent, dim_in)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        z = self.encoder(x)
        x_hat = self.decoder(z)
        return x_hat, z


def sae_loss(
    x: torch.Tensor,
    x_hat: torch.Tensor,
    z: torch.Tensor,
    lambda_l1: float = 1e-3,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Devuelve (loss_total, mse, l1)."""
    mse = torch.nn.functional.mse_loss(x_hat, x)
    l1 = z.abs().mean()
    total = mse + lambda_l1 * l1
    return total, mse, l1
