import { NextResponse } from "next/server";
export async function GET() {
  return NextResponse.json({ enabled: process.env.RODADA_DEVELOPER_TOOLS === "true" }, { headers: { "Cache-Control": "no-store" } });
}
