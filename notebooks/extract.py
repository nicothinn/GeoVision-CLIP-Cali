import json

with open('sit2_geovision_clip.ipynb', encoding='utf-8') as f:
    nb = json.load(f)

with open('sit2_geovision_clip_code.py', 'w', encoding='utf-8') as f:
    for c in nb['cells']:
        if c['cell_type'] == 'code':
            f.write("".join(c['source']) + "\n\n# ---\n\n")
