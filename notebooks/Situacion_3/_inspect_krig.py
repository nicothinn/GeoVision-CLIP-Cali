"""Inspecciona el notebook de kriging."""
import json, sys
from pathlib import Path

p = Path(__file__).with_name("03-convlstm-guia.ipynb")
nb = json.loads(p.read_text(encoding="utf-8"))
sys.stdout.reconfigure(encoding="utf-8")
print("Total cells:", len(nb["cells"]))
for i, c in enumerate(nb["cells"]):
    src = "".join(c.get("source", []))
    head = src[:280].replace("\n", " | ")
    print(f"--- CELL {i} [{c['cell_type']}] len={len(src)} ---")
    print(head)
