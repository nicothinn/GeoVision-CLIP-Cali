"""Router: GET /api/download/{format} — descarga CSV o GeoTIFF."""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Query
from fastapi.responses import Response

router = APIRouter()


@router.get("/api/download/{fmt}")
async def download(
    fmt: str,
    lat: float = Query(default=3.4516),
    lon: float = Query(default=-76.5320),
    contaminant: str = Query(default="NO2"),
    horizon: str = Query(default="T+1"),
):
    """
    Descarga la predicción en formato CSV o GeoTIFF.

    Args:
        fmt: "csv" o "geotiff"
        lat, lon: coordenadas del punto
        contaminant: NO2, SO2, O3
        horizon: T+1, T+3, T+7
    """
    if fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["lat", "lon", "value", "variance", "contaminant", "horizon", "timestamp"])
        writer.writerow([lat, lon, 42.3, 8.1, contaminant, horizon, "2026-05-18T17:30:00"])
        csv_content = output.getvalue()

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="geovision_{contaminant}_{lat}_{lon}.csv"',
            },
        )

    if fmt == "geotiff":
        # Placeholder: en producción real se genera con rioxarray/GDAL
        placeholder = f"GeoTIFF placeholder for {contaminant} at {lat},{lon} horizon {horizon}"
        return Response(
            content=placeholder,
            media_type="image/tiff",
            headers={
                "Content-Disposition": f'attachment; filename="geovision_{contaminant}_{lat}_{lon}.tif"',
            },
        )

    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=400,
        content={"error": "Invalid format. Use 'csv' or 'geotiff'"},
    )
