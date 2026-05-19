import { NextResponse } from "next/server";
import { getMockStations } from "@/lib/mockData";

export async function GET() {
  await new Promise((r) => setTimeout(r, 200));
  return NextResponse.json(getMockStations());
}
