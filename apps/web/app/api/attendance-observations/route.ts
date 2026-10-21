import { NextRequest, NextResponse } from "next/server";
import { forwardAttendanceObservation } from "@/lib/server/auth-gateway";

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
      if (size > 8192) { await reader.cancel(); return new NextResponse(null, { status: 413 }); }
      chunks.push(value);
    }
    const bytes = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
    const body: unknown = JSON.parse(new TextDecoder().decode(bytes));
    if (!body || typeof body !== "object" || Array.isArray(body)) return new NextResponse(null, { status: 400 });
    return forwardAttendanceObservation(request, body as Record<string, unknown>);
  } catch { return new NextResponse(null, { status: 400 }); }
  finally { reader.releaseLock(); }
}
