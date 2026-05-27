"""Exporta comunas y barrios de Cali a GeoJSON WGS84 para la app Next.js.

Requisito: shapefile en data/mc_barrios/mc_barrios.shp (carpeta data/ local).

Uso (desde la raíz del repo):
    python scripts/export_mc_barrios_geojson.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SHP_PATH = REPO_ROOT / "data" / "mc_barrios" / "mc_barrios.shp"
OUT_DIR = REPO_ROOT / "app" / "geo-vision-clip-application" / "public" / "geo"

# Simplificación ~15 m en CRS métrico local (EPSG:6249)
SIMPLIFY_M = 15.0


def main() -> int:
    try:
        import geopandas as gpd
    except ImportError:
        print("Instala geopandas: pip install geopandas", file=sys.stderr)
        return 1

    if not SHP_PATH.is_file():
        print(f"No encontrado: {SHP_PATH}", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    gdf = gpd.read_file(SHP_PATH)
    print(f"Leídos {len(gdf)} barrios | CRS: {gdf.crs}")

    # Simplificar en CRS métrico antes de WGS84
    gdf_metric = gdf.to_crs(gdf.crs)
    gdf_metric["geometry"] = gdf_metric.geometry.simplify(SIMPLIFY_M, preserve_topology=True)

    cols_barrio = ["id_barrio", "barrio", "comuna", "geometry"]
    cols_barrio = [c for c in cols_barrio if c in gdf_metric.columns]
    barrios = gdf_metric[cols_barrio].to_crs(4326)

    comunas = (
        barrios.dissolve(by="comuna", as_index=False)[["comuna", "geometry"]]
        .to_crs(4326)
    )

    barrios_path = OUT_DIR / "barrios_cali.geojson"
    comunas_path = OUT_DIR / "comunas_cali.geojson"

    barrios.to_file(barrios_path, driver="GeoJSON")
    comunas.to_file(comunas_path, driver="GeoJSON")

    bounds = barrios.total_bounds  # minx, miny, maxx, maxy = lon/lat
    summary = {
        "barrios": len(barrios),
        "comunas": len(comunas),
        "bounds_wgs84": {
            "lon_min": round(float(bounds[0]), 4),
            "lat_min": round(float(bounds[1]), 4),
            "lon_max": round(float(bounds[2]), 4),
            "lat_max": round(float(bounds[3]), 4),
        },
        "files": [str(barrios_path.relative_to(REPO_ROOT)), str(comunas_path.relative_to(REPO_ROOT))],
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Barrios -> {barrios_path} ({barrios_path.stat().st_size // 1024} KB)")
    print(f"Comunas -> {comunas_path} ({comunas_path.stat().st_size // 1024} KB)")
    print(f"Extensión WGS84: lon [{bounds[0]:.4f}, {bounds[2]:.4f}] lat [{bounds[1]:.4f}, {bounds[3]:.4f}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
