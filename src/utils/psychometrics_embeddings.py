"""AFE rápida sobre matriz de embeddings (opcional, KPI varianza explicada)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def scree_accumulated_variance(X: np.ndarray, n_factors: int = 8) -> dict[str, Any]:
    """PCA como AFE exploratorio: varianza acumulada por componente."""
    try:
        from sklearn.decomposition import PCA
    except ImportError as e:  # pragma: no cover
        raise ImportError("pip install scikit-learn") from e

    n = min(n_factors, X.shape[1], X.shape[0])
    pca = PCA(n_components=n)
    pca.fit(X)
    evr = pca.explained_variance_ratio_
    cum = np.cumsum(evr)
    return {
        "explained_variance_ratio": evr.tolist(),
        "cumulative": cum.tolist(),
        "variance_80_at_k": int(np.searchsorted(cum, 0.80) + 1) if len(cum) else None,
        "n_samples": int(X.shape[0]),
    }


def load_embedding_matrix_from_parquet(path: str, columns: list[str]) -> np.ndarray:
    df = pd.read_parquet(path)
    return np.stack([df[c].values for c in columns], axis=1) if columns else np.empty((len(df), 0))
