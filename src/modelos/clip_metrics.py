"""Métricas tipo CLIP: Recall@k imagen→texto, sparsity SAE, MSE reconstrucción."""

from __future__ import annotations

import torch


@torch.no_grad()
def recall_at_k_image_to_text(
    image_embeds: torch.Tensor,
    text_embeds: torch.Tensor,
    k: int,
    gallery_text_embeds: torch.Tensor | None = None,
    positive_indices: torch.Tensor | None = None,
) -> float:
    """Recall@k imagen→texto: proporción de imágenes cuyo texto positivo está en top-k.

    Caso batch cuadrado: galería = `text_embeds` y el positivo de la fila i es la
    columna i (`positive_indices` None).

    Si `gallery_text_embeds` tiene M textos y `positive_indices` es LongTensor
    de forma (N,) con el índice de columna del texto correcto por imagen.
    """
    image_embeds = torch.nn.functional.normalize(image_embeds, dim=-1)
    text_embeds = torch.nn.functional.normalize(text_embeds, dim=-1)
    if gallery_text_embeds is None:
        gallery = text_embeds
        n = image_embeds.shape[0]
        labels = torch.arange(n, device=image_embeds.device)
    else:
        gallery = torch.nn.functional.normalize(gallery_text_embeds, dim=-1)
        if positive_indices is None:
            raise ValueError("positive_indices requerido cuando gallery_text_embeds != None")
        labels = positive_indices.to(image_embeds.device).long()

    sim = image_embeds @ gallery.T
    kk = min(k, sim.shape[1])
    topk = sim.topk(kk, dim=1).indices
    hits = (topk == labels.unsqueeze(1)).any(dim=1).float().mean().item()
    return float(hits)


@torch.no_grad()
def sparsity_ratio(z: torch.Tensor, threshold: float = 0.01) -> float:
    """Fracción de activaciones |z| < threshold (KPI consigna)."""
    return float((z.abs() < threshold).float().mean().item())


@torch.no_grad()
def mse_reconstruction(x: torch.Tensor, x_hat: torch.Tensor) -> float:
    return float(torch.nn.functional.mse_loss(x_hat, x).item())
