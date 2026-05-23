# Notas de implementación — GeoVision-CLIP Sit.2

Referencia rápida para los notebooks `notebookresultados_Cliptexto.ipynb` (CLIP texto) y `notebookresultados_XLM-roberta.ipynb` (XLM-RoBERTa).

---

## 1. Caption diversity (SkyScript + Rethinking RS-CLIP + RS-CLIP)

### Constantes (Notebook A — inglés)

```python
MAGNITUDE_LEVELS = ["very low", "low", "moderate", "high", "very high"]
SEASONS_CALI = [
    "dry season Dec-Feb",
    "transition March",
    "first rainy season Apr-May",
    "mid-year transition Jun-Aug",
    "second rainy season Sep-Nov",
]
URBAN_CONTEXTS = [
    "dense urban core",
    "industrial belt",
    "mixed residential area",
    "peri-urban interface",
    "green agricultural buffer",
]
NDVI_LABELS = [
    (0.65, "dense green canopy"),
    (0.45, "moderate vegetation cover"),
    (0.25, "sparse vegetation"),
    (0.0,  "bare or built-up surface"),
]
```

### Plantilla base (RS-CLIP)

```python
PREFIX = "An aerial Sentinel-2 tile over Cali showing"
# Ejemplo: "An aerial Sentinel-2 tile over Cali showing very high nitrogen dioxide
# in a dense urban core during second rainy season Sep-Nov with bare built-up surface."
```

### Regla A2C (Rethinking) — incluir TODOS los atributos

```python
# Malo: solo clase + un número
# Bueno: magnitud + contexto + estación + NDVI verbalizado + contaminante
f"{PREFIX} {mag} tropospheric NO2 pollution in a {urban} during {season} with {ndvi_lbl}."
```

### SkyScript — dos variantes por tile (opcional)

```python
# title: objeto foco
# title_multi_objects: foco + entorno ("surrounded by industrial belt")
```

### Filtrado por calidad CLIP (SkyScript)

```python
# Tras generar captions, opcional: quedarse con pares cuyo coseno(img, txt) > percentil 30
```

---

## 2. Arquitectura

### Notebook A — RemoteCLIP + CLIP text + VisualProj

```python
class VisualProj(nn.Module):
    def __init__(self, dim=512):
        super().__init__()
        self.proj = nn.Linear(dim, dim)
    def forward(self, x):
        return self.proj(x)

def encode_image(self, tiles):
    h = self.visual(x)  # 512-d
    e = self.visual_proj(h) if self.use_visual_proj else h
    return {"h": h, "e": e}

def encode_text(self, texts):
    tokens = open_clip.tokenize(texts, context_length=77).to(device)
    h = self.clip_model.encode_text(tokens)
    return {"h": h, "e": h}
```

### Notebook B — open_clip XLM-RoBERTa (pre-alineado)

```python
MODEL_NAME = "xlm-roberta-base-ViT-B-32"
PRETRAINED = "laion5b_s13b_b90k"
model, _, preprocess = open_clip.create_model_and_transforms(MODEL_NAME, pretrained=PRETRAINED)
tokenizer = open_clip.get_tokenizer(MODEL_NAME)

def encode_text(self, texts):
    tokens = tokenizer(texts).to(device)  # hasta ~77-256 tokens según config
    h = self.clip_model.encode_text(tokens)
    return {"h": h, "e": h}
```

### InfoNCE (ambos notebooks)

```python
def clip_infonce(self, e_img, e_txt):
    e_img = F.normalize(e_img, dim=-1)
    e_txt = F.normalize(e_txt, dim=-1)
    scale = self.clip_model.logit_scale.exp().clamp(max=100.0)
    logits = scale * (e_img @ e_txt.T)
    t = torch.arange(logits.size(0), device=logits.device)
    return 0.5 * (F.cross_entropy(logits, t) + F.cross_entropy(logits.T, t))
```

### LoRA (GeoRSCLIP — bloques 6+)

```python
LORA_RANK = 16
LORA_VISUAL_FROM = 6
aplicar_lora(self.visual.transformer.resblocks[LORA_VISUAL_FROM:], rank=LORA_RANK)
aplicar_lora(self.clip_model.transformer.resblocks[LORA_VISUAL_FROM:], rank=LORA_RANK)
```

---

## 3. Training recipe

| Hiperparámetro | Valor | Fuente |
|----------------|-------|--------|
| LR | 2e-5 | open_clip #812 (escalar a batch 32) |
| Weight decay | 0.5 | GeoRSCLIP |
| Batch size | 32 | proyecto |
| Epochs | 40–80 | early stop |
| Early stop | `val/recall_at_1` max | proyecto |
| Warmup | implícito en PL | SkyScript usa 1000 steps |
| FREEZE_VISUAL | False + LoRA | proyecto |
| Split | por `img_id_s2` | informe leakage |
| Train filter | nube≤0.15, claros≥0.50 | informe R-M3 |

### Checkpoint

```python
ModelCheckpoint(monitor="val/recall_at_1", mode="max", save_top_k=1)
ModelCheckpoint(monitor="val/infonce", mode="min", save_top_k=1, filename="best-infonce")
```

---

## 4. Métricas

```python
@torch.no_grad()
def recall_at_k_image_to_text(image_embeds, text_embeds, k=1):
    image_embeds = F.normalize(image_embeds, dim=-1)
    text_embeds = F.normalize(text_embeds, dim=-1)
    sim = image_embeds @ text_embeds.T
    labels = torch.arange(sim.shape[0], device=sim.device)
    topk = sim.topk(min(k, sim.shape[1]), dim=1).indices
    return float((topk == labels.unsqueeze(1)).any(dim=1).float().mean())

# Mean recall (SkyScript): promedio R@1, R@5, R@10 img2txt y txt2img
```

### KPIs consigna (val)

| Métrica | Mínimo | Excelencia |
|---------|--------|------------|
| Recall@1 | 0.45 | 0.65 |
| Recall@5 | 0.70 | 0.85 |

---

## 5. FAISS (inferencia post-entrenamiento)

```python
import faiss
import numpy as np

# Embeddings L2-normalizados -> producto interno = coseno
d = 512
index = faiss.IndexFlatIP(d)
index.add(e_txt_np.astype("float32"))  # N textos

D, I = index.search(e_img_query.astype("float32"), k=5)  # top-5 por imagen
```

---

## 6. Referencias

| Fuente | Uso principal |
|--------|---------------|
| SkyScript (AAAI-24) | Caption diversity, filtro top-%, continual PT |
| GeoRSCLIP / RS5M | LoRA, LR/WD, retrieval benchmarks |
| Rethinking RS-CLIP | A2C multi-atributo, calidad > escala |
| RS-CLIP | Prompt "aerial image of", curriculum |
| open_clip #812 | CSV fine-tune, lr 5e-6, list_pretrained |
| XLM-RoBERTa HF | `xlm-roberta-base-ViT-B-32` en open_clip |

---

*Generado para implementación Sit.2 — sin SAE en loss.*
