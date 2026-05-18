"""Divide entrenamiento en celdas por fase y corrige bug _val_z_img."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks" / "sit2_geovision_clip.ipynb"
CELLS = ROOT / "scripts" / "nb_cells"


def _lines(text: str) -> list[str]:
    if not text.endswith("\n"):
        text += "\n"
    return [ln if ln.endswith("\n") else ln + "\n" for ln in text.splitlines(keepends=True)]


def _md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": _lines(text)}


def _code(name: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "source": _lines((CELLS / name).read_text(encoding="utf-8")),
        "outputs": [],
        "execution_count": None,
    }


def main():
    nb = json.loads(NB.read_text(encoding="utf-8"))
    head = nb["cells"][:10]
    tail = nb["cells"][11:]

    # Asegurar fix en celda modelo (índice 9)
    m9 = "".join(head[9]["source"])
    m9 = m9.replace("self._val_z_img, self._val_z_txt = [], [], []", "self._val_z_img, self._val_z_txt = [], []")
    m9 = m9.replace("self._val_z_img, self._val_z_txt = []", "self._val_z_img, self._val_z_txt = [], []")
    head[9]["source"] = _lines(m9)
    head[9]["outputs"] = []

    md0 = "".join(head[0]["source"])
    if "celdas por fase" not in md0:
        head[0]["source"] = _lines(
            md0.replace(
                "| Train |",
                "| Train | **4 celdas** (Fase 1→2→3→4) |",
            ).replace(
                "60 épocas (4 fases)",
                "60 épocas en 3 celdas + eval test",
            )
        )

    new_train = [
        _code("cell10_train_setup.py"),
        _md(
            "## Fase 1 (épocas 0–19)\n\n"
            "Visual **congelado**, augment + captions múltiples, α_SAE 0→0.05.\n"
        ),
        _code("cell11_fase1.py"),
        _md(
            "## Fase 2 (épocas 20–39)\n\n"
            "Descongela **últimos 2 bloques** ViT-B/32. Requiere `fase1_best.ckpt`.\n"
        ),
        _code("cell13_fase2.py"),
        _md(
            "## Fase 3 (épocas 40–59)\n\n"
            "α_SAE **0.1** (consigna), λ_L1=3e-3. Requiere `fase2_best.ckpt`.\n"
        ),
        _code("cell15_fase3.py"),
        _md(
            "## Fase 4 — evaluación test\n\n"
            "Recall@k en **test** + prompt ensemble (SenCLIP).\n"
        ),
        _code("cell17_fase4.py"),
    ]

    nb["cells"] = head + new_train + tail

    for c in nb["cells"]:
        if c["cell_type"] == "code":
            c["outputs"] = []
            c["execution_count"] = None

    NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("OK:", NB, "| celdas:", len(nb["cells"]))


if __name__ == "__main__":
    main()
