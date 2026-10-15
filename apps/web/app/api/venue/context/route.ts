import { NextRequest, NextResponse } from "next/server";
import { tenantHostname } from "@/lib/tenant-host";
import { lookupVenueContext } from "@/lib/server/venue-context";

export async function GET(request: NextRequest) {
  if (!tenantHostname(request.headers.get("host"))) {
    return NextResponse.json({ mode: "compatibility" }, { headers: { "Cache-Control": "no-store" } });
  }
  const result = await lookupVenueContext(request.headers);
  if (!result.ok) return NextResponse.json({ code: result.code }, { status: result.status, headers: { "Cache-Control": "no-store" } });
  return NextResponse.json(result.context, { headers: { "Cache-Control": "private, no-store", Vary: "Host" } });
}
