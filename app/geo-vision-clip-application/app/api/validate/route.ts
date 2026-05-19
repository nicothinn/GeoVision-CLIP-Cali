import { NextResponse } from "next/server";
import { getMockValidation } from "@/lib/mockData";

export async function GET() {
  await new Promise((r) => setTimeout(r, 150));
  return NextResponse.json(getMockValidation());
}
