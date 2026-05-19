import { NextRequest, NextResponse } from "next/server";
import { getMockPrediction } from "@/lib/mockData";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { lat, lon, radius_km = 5, contaminant = "NO2", horizon = "T+1" } = body;

  if (!lat || !lon) {
    return NextResponse.json({ error: "lat and lon are required" }, { status: 400 });
  }

  // Simulate model latency
  await new Promise((r) => setTimeout(r, 600 + Math.random() * 400));

  return NextResponse.json(getMockPrediction(lat, lon, radius_km, contaminant, horizon));
}
