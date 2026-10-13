import { NextRequest, NextResponse } from "next/server";
import { tenantHostname } from "@/lib/tenant-host";
import { readVenueContext } from "@/lib/server/venue-context";

export async function GET(request: NextRequest) {
  if (!tenantHostname(request.headers.get("host"))) {
    return NextResponse.json({ mode: "compatibility" }, { headers: { "Cache-Control": "no-store" } });
  }
  const context = await readVenueContext(request.headers);
  if (!context) return NextResponse.json({ code: "VENUE_HOST_NOT_FOUND" }, { status: 421, headers: { "Cache-Control": "no-store" } });
  return NextResponse.json(context, { headers: { "Cache-Control": "private, no-store", Vary: "Host" } });
}
