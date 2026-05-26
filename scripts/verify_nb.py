import json
path = r"C:\Users\Samuel\Desktop\FINALPROYECTO3\GeoVision-CLIP-Cali\notebooks\Situacion_3\sit3-kriging-eval.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)
print("JSON OK")
print(f"Cells: {len(nb['cells'])}")
print(f"nbformat: {nb['nbformat']}")
for i, c in enumerate(nb["cells"]):
    src = "".join(c["source"])[:100].replace("\n", " ")
    print(f"  [{i}] [{c['cell_type']}] {src}...")
