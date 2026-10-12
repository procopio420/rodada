import { createHash } from "node:crypto";
import { venueHostHeaders } from "@/lib/server/venue-host";
import { NextRequest, NextResponse } from "next/server";

import { rejectCrossOriginMutation } from "@/lib/server/auth-gateway";

const apiBaseUrl = (process.env.RODADA_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

async function forward(request: NextRequest, params: Promise<{ path: string[] }>) {
  if (request.method !== "GET") {
    const rejected = rejectCrossOriginMutation(request);
    if (rejected) return rejected;
  }

  const { path } = await params;
  const upstreamPath = `/guest/${path.join("/")}/`;
  const headers = venueHostHeaders(request, request.method, upstreamPath);
  headers.set("Accept", request.headers.get("accept") ?? "application/json");

  let body: string | undefined;
  if (request.method !== "GET") {
    headers.set("Content-Type", "application/json");
    body = await request.text();
  }

  const resolving = path.join("/") === "qr/resolve";
  let selector = request.headers.get("x-guest-session") ?? "";
  if (resolving) {
    try { selector = JSON.parse(body ?? "{}").token ?? ""; }
    catch { return NextResponse.json({ code: "INVALID_JSON" }, { status: 400 }); }
  }
  if (typeof selector !== "string" || !/^[A-Za-z0-9_-]{1,160}$/.test(selector)) {
    return NextResponse.json({ code: "GUEST_SESSION_REQUIRED" }, { status: 401 });
  }
  const cookieName = `rodada_guest_${createHash("sha256").update(selector).digest("hex").slice(0, 32)}`;
  const guestSession = request.cookies.get(cookieName)?.value;
  if (guestSession) headers.set("X-Guest-Session", guestSession);

  try {
    const upstream = await fetch(`${apiBaseUrl}/guest/${path.join("/")}/${request.nextUrl.search}`, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
      signal: request.signal,
    });
    if (resolving && upstream.ok) {
      const payload = await upstream.json();
      const token = payload.guest_session_token;
      // Only the public selector reaches JS; the opaque authorization stays HttpOnly.
      payload.guest_session_token = selector;
      const response = NextResponse.json(payload, { status: upstream.status });
      response.cookies.set(cookieName, token, { httpOnly: true,
        secure: process.env.NODE_ENV === "production", sameSite: "lax", path: "/",
        maxAge: Math.max(1, Math.floor((Date.parse(payload.expires_at) - Date.now()) / 1000)) });
      return response;
    }
    return new NextResponse(upstream.body, {
      status: upstream.status,
      headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json", "Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no" },
    });
  } catch {
    return NextResponse.json(
      { code: "UPSTREAM_UNAVAILABLE", message: "Não foi possível falar com o Rodada." },
      { status: 503 },
    );
  }
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return forward(request, context.params);
}

export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return forward(request, context.params);
}
