import { NextRequest, NextResponse } from "next/server";
import { forwardPassiveAttendanceTelemetry } from "@/lib/server/auth-gateway";

// Passive first-visible receipt: bounded request, no staff auth refresh/cookie mutation.
export async function POST(request: NextRequest) {
  const reader = request.body?.getReader();
  if (!reader) return new NextResponse(null, { status: 400 });
  let size = 0;
  const chunks: Uint8Array[] = [];
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > 8192) {
        await reader.cancel();
        return new NextResponse(null, { status: 413 });
      }
      chunks.push(value);
    }
    const bytes = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
    const parsed: unknown = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed))
      return new NextResponse(null, { status: 400 });
    return forwardPassiveAttendanceTelemetry(request, parsed as Record<string, unknown>, "/production/screen-observations/");
  } catch {
    return new NextResponse(null, { status: 400 });
  }
}
