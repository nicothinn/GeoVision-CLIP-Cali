import { NextRequest, NextResponse } from "next/server";

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ format: string }> }
) {
  const { format } = await params;
  const { searchParams } = new URL(req.url);
  const lat = searchParams.get("lat") ?? "3.4516";
  const lon = searchParams.get("lon") ?? "-76.5320";
  const contaminant = searchParams.get("contaminant") ?? "NO2";

  if (format === "csv") {
    const csv = [
      "lat,lon,value,variance,contaminant,timestamp",
      `${lat},${lon},42.3,8.1,${contaminant},2026-05-18T17:30:00`,
    ].join("\n");

    return new NextResponse(csv, {
      headers: {
        "Content-Type": "text/csv",
        "Content-Disposition": `attachment; filename="geovision_${contaminant}_${lat}_${lon}.csv"`,
      },
    });
  }

  if (format === "geotiff") {
    // Return a minimal placeholder binary for demo (real impl would use GDAL)
    const placeholder = `GeoTIFF placeholder for ${contaminant} at ${lat},${lon}`;
    return new NextResponse(placeholder, {
      headers: {
        "Content-Type": "image/tiff",
        "Content-Disposition": `attachment; filename="geovision_${contaminant}_${lat}_${lon}.tif"`,
      },
    });
  }

  return NextResponse.json({ error: "Invalid format. Use 'csv' or 'geotiff'" }, { status: 400 });
}
