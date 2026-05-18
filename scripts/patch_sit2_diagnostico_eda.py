"""Inserta celdas EDA calidad + diagnóstico post-entrenamiento en sit2_geovision_clip.ipynb."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "sit2_geovision_clip.ipynb"


def _md(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "id": uuid.uuid4().hex[:8],
        "metadata": {},
        "source": [line + "\n" for line in text.strip().split("\n")],
    }


def _code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": uuid.uuid4().hex[:8],
        "metadata": {"trusted": True},
        "outputs": [],
        "source": [line + "\n" for line in text.strip().split("\n")],
    }


EDA_QUALITY_CELLS = [
    _md(
        """## 2. EDA — calidad para entrenamiento

Informe complementario: nubes (SCL), claridad y NDVI por **split** y **clase**.
Salidas en `EDA_DIR` (`resumen_calidad_split_clase.csv`, `tiles_baja_calidad.csv`, paneles PNG)."""
    ),
    _md(
        """### Paso 1 — Tabla resumen por split y clase

Mediana de `frac_nubes_scl`, `frac_claros_scl` y `ndvi` para detectar desbalance de calidad entre clases y splits."""
    ),
    _code(
        """# @title EDA calidad — Paso 1: mediana nubes / claros / NDVI
CALIDAD_COLS = ["frac_nubes_scl", "frac_claros_scl", "ndvi"]
rows = []
for split, gsp in df.groupby("split"):
    for clase in CLASES:
        sub = gsp[gsp["clase"] == clase]
        if sub.empty:
            continue
        row = {"split": split, "clase": clase, "n": len(sub)}
        for c in CALIDAD_COLS:
            row[f"mediana_{c}"] = float(sub[c].median())
        rows.append(row)
tab_calidad = pd.DataFrame(rows)
out_csv = EDA_DIR / "resumen_calidad_split_clase.csv"
tab_calidad.to_csv(out_csv, index=False)
print(tab_calidad.round(4).to_string(index=False))
print("\\nGuardado:", out_csv)"""
    ),
    _md(
        """### Paso 2 — Tiles a revisar (baja calidad)

- Top **5%** con mayor `frac_nubes_scl` (peor nube).
- Outliers de NDVI por clase (|z-score| > 2.5).
Unión → `tiles_baja_calidad.csv`."""
    ),
    _code(
        """# @title EDA calidad — Paso 2: lista tiles_baja_calidad.csv
work = df.copy()
n_top = max(1, int(np.ceil(0.05 * len(work))))
top_nube = work.nlargest(n_top, "frac_nubes_scl").copy()
top_nube["motivo"] = "top5pct_frac_nubes"

outliers = []
for clase in CLASES:
    sub = work[work["clase"] == clase]
    if len(sub) < 8:
        continue
    mu, sig = sub["ndvi"].mean(), sub["ndvi"].std()
    if sig < 1e-9:
        continue
    z = (sub["ndvi"] - mu) / sig
    bad = sub.loc[z.abs() > 2.5].copy()
    bad["motivo"] = "outlier_ndvi_clase"
    outliers.append(bad)

lista = pd.concat([top_nube, *outliers], ignore_index=True)
lista = lista.drop_duplicates(subset=["tile_id"], keep="first")
cols_out = [
    "tile_id", "split", "clase", "motivo",
    "frac_nubes_scl", "frac_claros_scl", "ndvi", "valid_ratio", "descripcion",
]
lista = lista[[c for c in cols_out if c in lista.columns]]
out_lista = EDA_DIR / "tiles_baja_calidad.csv"
lista.to_csv(out_lista, index=False)
print(f"Tiles a revisar: {len(lista)} (top nube={len(top_nube)}, outliers NDVI={sum(len(o) for o in outliers)})")
print(lista.head(10).to_string(index=False))
print("\\nGuardado:", out_lista)"""
    ),
    _md(
        """### Paso 3 — Panel visual (RGB + SCL + histograma)

Muestra hasta **N** tiles de la lista de baja calidad (3 columnas: RGB, mapa SCL, histograma de bandas)."""
    ),
    _code(
        """# @title EDA calidad — Paso 3: panel RGB + SCL + histograma
from matplotlib.colors import ListedColormap, BoundaryNorm

SCL_LABELS = {
    0: "nodata", 1: "saturado", 2: "sombra", 3: "nube", 4: "veg",
    5: "no_veg", 6: "agua", 7: "sin_clas", 8: "nube_med", 9: "cirrus",
    10: "nube_thin", 11: "nieve",
}
SCL_COLORS = [
    "#000000", "#ff0000", "#654321", "#cccccc", "#00aa00",
    "#ffff00", "#0000ff", "#808080", "#bbbbbb", "#00ffff",
    "#dddddd", "#ffffff",
]
_scl_cmap = ListedColormap(SCL_COLORS)
_scl_norm = BoundaryNorm(np.arange(-0.5, 12.5, 1), _scl_cmap.N)

def tile_scl_map(tile_13hw):
    scl = np.rint(tile_13hw[_IDX_SCL]).astype(np.int16)
    return scl

def plot_tile_panel(tile_13hw, title="", ax_rgb=None, ax_scl=None, ax_hist=None):
    if ax_rgb is not None:
        ax_rgb.imshow(tile_to_rgb_uint8(tile_13hw))
        ax_rgb.set_title("RGB", fontsize=8)
        ax_rgb.axis("off")
    if ax_scl is not None:
        scl = tile_scl_map(tile_13hw)
        im = ax_scl.imshow(scl, cmap=_scl_cmap, norm=_scl_norm, interpolation="nearest")
        ax_scl.set_title("SCL", fontsize=8)
        ax_scl.axis("off")
    if ax_hist is not None:
        vals = tile_13hw[:12].astype(np.float32).ravel()
        vals = vals[np.isfinite(vals)]
        ax_hist.hist(vals, bins=40, color="steelblue", alpha=0.85)
        ax_hist.set_title("hist bandas (sin SCL)", fontsize=8)
        ax_hist.set_xlabel("DN")
    if title and ax_rgb is not None:
        ax_rgb.set_ylabel(title, fontsize=7, rotation=0, labelpad=40, va="center")

N_PANEL = min(8, len(lista))
if N_PANEL == 0:
    print("Sin tiles en lista; ejecuta el Paso 2.")
else:
    fig, axes = plt.subplots(N_PANEL, 3, figsize=(9, 2.2 * N_PANEL))
    if N_PANEL == 1:
        axes = axes.reshape(1, -1)
    for r, (_, row) in enumerate(lista.head(N_PANEL).iterrows()):
        j = int(df.index[df["tile_id"] == row["tile_id"]][0])
        tile = np.asarray(tiles_z[j])
        ttl = f"{row['tile_id'][:12]}… | {row['clase'][:12]}"
        plot_tile_panel(tile, ttl, axes[r, 0], axes[r, 1], axes[r, 2])
    plt.suptitle("Tiles baja calidad — RGB / SCL / histograma", y=1.01)
    plt.tight_layout()
    out_png = EDA_DIR / "06_panel_calidad_rgb_scl_hist.png"
    plt.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.show()
    print("Guardado:", out_png)"""
    ),
    _md(
        """### Paso 4 — Reglas de calidad “estricta”

Criterio estricto (más exigente que el pipeline por defecto):
- `frac_nubes_scl` ≤ 0.15
- `frac_claros_scl` ≥ 0.90

Se reporta el % de tiles que pasan, global y por split."""
    ),
    _code(
        """# @title EDA calidad — Paso 4: % pasa filtro estricto
UMBRAL_NUBE_ESTRICTO = 0.15
UMBRAL_CLAROS_ESTRICTO = 0.90

df["_pasa_estricto"] = (
    (df["frac_nubes_scl"] <= UMBRAL_NUBE_ESTRICTO)
    & (df["frac_claros_scl"] >= UMBRAL_CLAROS_ESTRICTO)
)
pct_global = 100.0 * df["_pasa_estricto"].mean()
resumen_estricto = {"ambito": ["global"], "n": [len(df)], "pct_pasa_estricto": [pct_global]}
for sp, g in df.groupby("split"):
    resumen_estricto["ambito"].append(sp)
    resumen_estricto["n"].append(len(g))
    resumen_estricto["pct_pasa_estricto"].append(100.0 * g["_pasa_estricto"].mean())

tab_estricto = pd.DataFrame(resumen_estricto)
print(tab_estricto.round(2).to_string(index=False))
print(f"\\nPipeline actual (ref.): nube≤0.30, claros≥0.10 → pasa {100*df['frac_nubes_scl'].le(0.30).mul(df['frac_claros_scl'].ge(0.10)).mean():.1f}%")
tab_estricto.to_csv(EDA_DIR / "pct_filtro_estricto.csv", index=False)
print("Guardado:", EDA_DIR / "pct_filtro_estricto.csv")"""
    ),
]

POST_TRAIN_CELLS = [
    _md(
        """## 3. Diagnóstico post-entrenamiento

Análisis tras `trainer.fit`: curvas desde `metricas_por_epoca.json`, Recall global vs por clase,
histograma de `z_img`, inspección de peores pares y notas de ablación (α, λ).

**Requisito:** haber ejecutado la celda de entrenamiento (y preferiblemente tener `embeddings_val_mejor.npz`)."""
    ),
    _md(
        """### Curvas de validación desde JSON

Lee `RUN_DIR/metricas_por_epoca.json` y grafica Recall@1/@5, InfoNCE val, sparsity y MSE SAE imagen."""
    ),
    _code(
        """# @title Diagnóstico — curvas val (recall, infonce, sparsity, MSE)
import json
import matplotlib.pyplot as plt

def _col_train_loss(dfm):
    if "train/loss" in dfm.columns:
        return "train/loss"
    if "train/loss_epoch" in dfm.columns:
        return "train/loss_epoch"
    return None

hist = json.loads(Path(METRICS_JSON).read_text(encoding="utf-8"))
rows = hist.get("epochs", [])
if not rows:
    raise ValueError(f"No hay épocas en {METRICS_JSON}. Ejecuta primero el entrenamiento.")

dfm = pd.DataFrame(rows)
col_tl = _col_train_loss(dfm)
print("Mejor época (JSON):", hist.get("best"))
cols_show = ["epoch", "val/recall_at_1", "val/recall_at_5", "val/loss", "val/infonce",
             "val/sparsity_img", "val/mse_sae_img"]
if col_tl:
    cols_show.insert(4, col_tl)
cols_show = [c for c in cols_show if c in dfm.columns]
print(dfm[cols_show].round(4).to_string(index=False))

fig, axes = plt.subplots(2, 3, figsize=(14, 8))
plot_specs = [
    (axes[0, 0], col_tl, "Loss train"),
    (axes[0, 1], "val/loss", "Loss val"),
    (axes[0, 2], "val/infonce", "InfoNCE val"),
    (axes[1, 0], "val/recall_at_1", "Recall@1 val", KPI_RECALL1_MIN),
    (axes[1, 1], "val/recall_at_5", "Recall@5 val", KPI_RECALL5_MIN),
    (axes[1, 2], "val/sparsity_img", "Sparsity img val", KPI_SPARSITY_MIN),
]
for ax, col, title, *kpi in plot_specs:
    if col and col in dfm.columns:
        ax.plot(dfm["epoch"], dfm[col], "o-", ms=4, lw=1.5)
    if kpi:
        ax.axhline(kpi[0], color="red", ls="--", alpha=0.6, label=f"KPI {kpi[0]}")
        ax.legend(fontsize=7)
    ax.set_title(title)
    ax.set_xlabel("época")
    ax.grid(True, alpha=0.3)

fig2, ax2 = plt.subplots(figsize=(6, 4))
if "val/mse_sae_img" in dfm.columns:
    ax2.plot(dfm["epoch"], dfm["val/mse_sae_img"], "o-", color="darkorange", lw=1.5)
    ax2.axhline(KPI_MSE_SAE_MAX, color="red", ls="--", alpha=0.6, label=f"max {KPI_MSE_SAE_MAX}")
    ax2.legend()
ax2.set_title("MSE SAE imagen (val)")
ax2.set_xlabel("época")
ax2.grid(True, alpha=0.3)
plt.tight_layout()

out_png = RUN_DIR / "curvas_diagnostico_val.png"
fig.savefig(out_png, dpi=150, bbox_inches="tight")
fig2.savefig(RUN_DIR / "curva_mse_sae_val.png", dpi=150)
plt.show()
print("Guardado:", out_png, "|", RUN_DIR / "curva_mse_sae_val.png")"""
    ),
    _md(
        """### Recall@1 global vs misma clase + matriz de confusión

- **Global:** texto correcto entre todos los de val (protocolo consigna).
- **Misma clase:** el texto correcto solo compite con textos de la **misma** clase (diagnóstico: ¿el modelo distingue clase o solo parecidos globales?).

Usa `embeddings_val_mejor.npz` del mejor Recall@1."""
    ),
    _code(
        """# @title Diagnóstico — Recall global vs misma clase + matriz confusión
import torch.nn.functional as F

def recall_at_k_masked(e_img, e_txt, k=1, mask=None):
    e_img = F.normalize(torch.as_tensor(e_img), dim=-1)
    e_txt = F.normalize(torch.as_tensor(e_txt), dim=-1)
    sim = e_img @ e_txt.T
    n = sim.shape[0]
    labels = torch.arange(n)
    if mask is not None:
        sim = sim.masked_fill(~mask, float("-inf"))
    kk = min(k, sim.shape[1])
    topk = sim.topk(kk, dim=1).indices
    return float((topk == labels.unsqueeze(1)).any(dim=1).float().mean().item())

def confusion_top1(e_img, e_txt, clases):
    e_img = F.normalize(torch.as_tensor(e_img), dim=-1)
    e_txt = F.normalize(torch.as_tensor(e_txt), dim=-1)
    pred_idx = (e_img @ e_txt.T).argmax(dim=1).numpy()
    pred_clase = [clases[int(j)] for j in pred_idx]
    mat = pd.crosstab(
        pd.Categorical(clases, categories=CLASES, ordered=True),
        pd.Categorical(pred_clase, categories=CLASES, ordered=True),
        rownames=["verdadera"], colnames=["predicha_top1"],
    ).reindex(index=CLASES, columns=CLASES, fill_value=0)
    return mat

emb_path = Path(EMBEDDINGS_BEST)
if not emb_path.is_file():
    raise FileNotFoundError(f"No existe {emb_path}. Entrena primero o ajusta EMBEDDINGS_BEST.")

emb = np.load(emb_path, allow_pickle=True)
e_img, e_txt = emb["e_img"], emb["e_txt"]
tile_ids = emb["tile_ids"].astype(str)
id2clase = df.set_index("tile_id")["clase"].to_dict()
clases_val = np.array([id2clase.get(tid, "") for tid in tile_ids])

r1_global = recall_at_k_image_to_text(torch.from_numpy(e_img), torch.from_numpy(e_txt), 1)
r5_global = recall_at_k_image_to_text(torch.from_numpy(e_img), torch.from_numpy(e_txt), 5)

r1_cls, n_eval = [], 0
clases_t = torch.as_tensor([CLASES.index(c) if c in CLASES else -1 for c in clases_val])
for ci, cname in enumerate(CLASES):
    idx = torch.where(clases_t == ci)[0]
    if len(idx) < 2:
        continue
    mask = torch.zeros(len(clases_val), len(clases_val), dtype=torch.bool)
    for i in idx:
        mask[i, idx] = True
    r1_cls.append(recall_at_k_masked(e_img, e_txt, 1, mask))
    n_eval += len(idx)
r1_misma_clase = float(np.mean(r1_cls)) if r1_cls else float("nan")

print(f"Recall@1 global (val, n={len(tile_ids)}): {r1_global:.4f}")
print(f"Recall@5 global:                  {r5_global:.4f}")
print(f"Recall@1 misma clase (promedio):  {r1_misma_clase:.4f}  (por clase con n>=2)")
print(f"  → Si misma clase >> global: textos muy parecidos entre clases.")

cm = confusion_top1(e_img, e_txt, clases_val)
print("\\nMatriz confusión (clase verdadera × predicha por similitud img→txt):")
print(cm)

fig, ax = plt.subplots(figsize=(7, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax)
ax.set_title("Top-1 texto predicho vs clase verdadera")
plt.tight_layout()
out_cm = RUN_DIR / "matriz_confusion_clase.png"
plt.savefig(out_cm, dpi=150)
plt.show()
pd.DataFrame({
    "metrica": ["recall_at_1_global", "recall_at_5_global", "recall_at_1_misma_clase"],
    "valor": [r1_global, r5_global, r1_misma_clase],
}).to_csv(RUN_DIR / "recall_global_vs_clase.csv", index=False)
print("Guardado:", out_cm, "|", RUN_DIR / "recall_global_vs_clase.csv")"""
    ),
    _md(
        """### Histograma de `z_img` (val, mejor checkpoint)

Distribución de activaciones del SAE visual. Si casi no hay masa cerca de 0, subir λ no alcanzará sparsity 0.70 sin ReLU/top-k."""
    ),
    _code(
        """# @title Diagnóstico — histograma z_img (val)
emb = np.load(EMBEDDINGS_BEST, allow_pickle=True)
z = emb["z_img"].astype(np.float64).ravel()
thr = 0.01
frac_below = float((np.abs(z) < thr).mean())
print(f"|z| < {thr}: {frac_below:.4f}  (KPI sparsity ≈ {frac_below:.2%}, meta ≥ {KPI_SPARSITY_MIN})")
print(f"z: mean={z.mean():.4f} std={z.std():.4f} min={z.min():.4f} max={z.max():.4f}")

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].hist(z, bins=80, color="steelblue", alpha=0.85, density=True)
axes[0].axvline(-thr, color="red", ls="--", lw=1)
axes[0].axvline(thr, color="red", ls="--", lw=1)
axes[0].set_title("Histograma z_img (todas las dims)")
axes[0].set_xlabel("z")

axes[1].hist(np.abs(z), bins=80, color="darkorange", alpha=0.85, density=True)
axes[1].axvline(thr, color="red", ls="--", label=f"umbral {thr}")
axes[1].set_title("|z_img|")
axes[1].set_xlabel("|z|")
axes[1].legend()
plt.tight_layout()
out_h = RUN_DIR / "histograma_z_img_val.png"
plt.savefig(out_h, dpi=150)
plt.show()

# Porcentaje bajo umbral vs lambda (teórico, sin re-entrenar)
for lam in [1e-4, 1e-3, 1e-2, 1e-1]:
    print(f"  λ={lam:.0e} → sparsity actual ~{frac_below:.3f} (subir λ empuja |z|→0 solo si re-entrenas)")

print("Guardado:", out_h)"""
    ),
    _md(
        """### 20 tiles con peor similitud imagen → su texto correcto

Ordenados por coseno entre `e_img[i]` y `e_txt[i]`. Ayuda a separar **error de dato** (nube, NDVI raro) vs **error de modelo**."""
    ),
    _code(
        """# @title Diagnóstico — 20 peores pares img→txt (val)
import torch.nn.functional as F

emb = np.load(EMBEDDINGS_BEST, allow_pickle=True)
e_img = F.normalize(torch.from_numpy(emb["e_img"]), dim=-1)
e_txt = F.normalize(torch.from_numpy(emb["e_txt"]), dim=-1)
tile_ids = emb["tile_ids"].astype(str)
diag = (e_img * e_txt).sum(dim=1).numpy()

meta_val = df[df["split"] == "val"].set_index("tile_id")
rows_worst = []
for rank, i in enumerate(np.argsort(diag)[:20]):
    tid = tile_ids[i]
    m = meta_val.loc[tid] if tid in meta_val.index else None
    rows_worst.append({
        "rank": rank + 1,
        "tile_id": tid,
        "cos_diag": float(diag[i]),
        "clase": str(m["clase"]) if m is not None else "",
        "frac_nubes_scl": float(m["frac_nubes_scl"]) if m is not None else np.nan,
        "frac_claros_scl": float(m["frac_claros_scl"]) if m is not None else np.nan,
        "ndvi": float(m["ndvi"]) if m is not None else np.nan,
        "descripcion": (str(m["descripcion"])[:120] + "…") if m is not None else "",
    })
worst_df = pd.DataFrame(rows_worst)
out_w = RUN_DIR / "peores_20_pares_val.csv"
worst_df.to_csv(out_w, index=False)
print(worst_df.to_string(index=False))
print("\\nGuardado:", out_w)

# Panel visual 4x5
fig, axes = plt.subplots(4, 5, figsize=(12, 10))
for k, ax in enumerate(axes.ravel()):
    if k >= len(worst_df):
        ax.axis("off")
        continue
    tid = worst_df.iloc[k]["tile_id"]
    j = int(df.index[df["tile_id"] == tid][0])
    tile = np.asarray(tiles_z[j])
    ax.imshow(tile_to_rgb_uint8(tile))
    ax.set_title(f"#{worst_df.iloc[k]['rank']} cos={worst_df.iloc[k]['cos_diag']:.2f}", fontsize=7)
    ax.axis("off")
plt.suptitle("20 peores similitudes diagonales (val)", y=1.01)
plt.tight_layout()
out_p = RUN_DIR / "panel_peores_20_val.png"
plt.savefig(out_p, dpi=150, bbox_inches="tight")
plt.show()
print("Guardado:", out_p)"""
    ),
    _md(
        """### Ablación mental: α (SAE) y λ (L1)

Tabla de referencia **sin re-entrenar** aquí. Para experimentos reales, duplica hiperparámetros en la celda de configuración y vuelve a entrenar.

| Escenario | Efecto esperado |
|-----------|-----------------|
| α = 0 (solo InfoNCE) | Techo de Recall; MSE/sparsity SAE dejan de optimizarse en el loss total |
| λ ↑ (p. ej. 1e-2) | Más \|z\| pequeños → sube sparsity; suele bajar Recall y subir MSE reconstrucción |
| α = 0.1, λ = 1e-3 (actual) | Compromiso actual: buen Recall relativo, sparsity ~4% |"""
    ),
    _code(
        """# @title Diagnóstico — tabla ablacion (referencia + estado actual)
ablacion = pd.DataFrame([
    {"escenario": "actual", "alpha_sae": ALPHA_SAE, "lambda_l1": LAMBDA_L1,
     "nota": "Config en celda de entrenamiento"},
    {"escenario": "solo_infonce", "alpha_sae": 0.0, "lambda_l1": LAMBDA_L1,
     "nota": "Techo Recall; desactiva peso SAE en loss"},
    {"escenario": "lambda_alto", "alpha_sae": ALPHA_SAE, "lambda_l1": 1e-2,
     "nota": "Más sparsity, Recall suele caer"},
    {"escenario": "lambda_muy_alto", "alpha_sae": ALPHA_SAE, "lambda_l1": 1e-1,
     "nota": "Sparsity alta; riesgo MSE > 0.05"},
])
print(ablacion.to_string(index=False))

if Path(METRICS_JSON).is_file():
    best = json.loads(Path(METRICS_JSON).read_text(encoding="utf-8")).get("best", {})
    print("\\nMejor época registrada:")
    for k in ["epoch", "val/recall_at_1", "val/recall_at_5", "val/sparsity_img", "val/mse_sae_img"]:
        if k in best:
            print(f"  {k}: {best[k]}")
else:
    print("\\n(Sin metricas_por_epoca.json aún)")

ablacion.to_csv(RUN_DIR / "tabla_ablacion_referencia.csv", index=False)
print("\\nPara correr ablación real: cambia ALPHA_SAE / LAMBDA_L1 y re-ejecuta entrenamiento.")"""
    ),
]


def _fix_training_callback(nb: dict) -> None:
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell.get("source", []))
        if "# @title Entrenamiento + validación" not in src:
            continue
        src = src.replace('"train/loss_epoch"', '"train/loss"')
        src = src.replace("row.get('train/loss_epoch'", "row.get('train/loss'")
        cell["source"] = [line + "\n" for line in src.split("\n")]
        if cell["source"] and cell["source"][-1] == "\n":
            cell["source"].pop()
        break


def _replace_old_graphics_cell(nb: dict) -> None:
    """Elimina celda gráficos antigua (se reemplaza por bloque diagnóstico)."""
    to_remove = []
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] == "code":
            src = "".join(cell.get("source", []))
            if "# @title Gráficos desde metricas_por_epoca.json" in src:
                to_remove.append(i)
        if cell["cell_type"] == "markdown":
            src = "".join(cell.get("source", []))
            if "## Gráficos de línea (después del entrenamiento)" in src:
                to_remove.append(i)
    for i in sorted(to_remove, reverse=True):
        del nb["cells"][i]


def main() -> None:
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    _fix_training_callback(nb)

    # Insertar EDA calidad después de celda EDA (índice 5)
    insert_at = 6
    for offset, cell in enumerate(EDA_QUALITY_CELLS):
        nb["cells"].insert(insert_at + offset, cell)

    # Tras insertar 8 celdas, localizar y quitar gráficos viejos; insertar diagnóstico antes de KPIs
    _replace_old_graphics_cell(nb)

    kpi_idx = None
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] == "markdown" and "KPIs consigna" in "".join(cell.get("source", [])):
            kpi_idx = i
            break
    if kpi_idx is None:
        kpi_idx = len(nb["cells"])

    for offset, cell in enumerate(POST_TRAIN_CELLS):
        nb["cells"].insert(kpi_idx + offset, cell)

    NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Actualizado: {NOTEBOOK}")
    print(f"Celdas totales: {len(nb['cells'])}")


if __name__ == "__main__":
    main()
