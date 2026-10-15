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
  // A second HttpOnly secret is required for Customer identity. Browser headers
  // never grant identity by themselves; backend binds it to GuestSession + Venue.
  const customerCookieName = `rodada_customer_${createHash("sha256").update(selector).digest("hex").slice(0, 32)}`;
  const customerAuth = request.cookies.get(customerCookieName)?.value;
  if (customerAuth) headers.set("X-Customer-Session", customerAuth);
  const enrolling = ["customer/register", "customer/login", "customer/password"].includes(path.join("/"));
  const loggingOut = path.join("/") === "customer/logout";

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
      if (typeof token !== "string" || !token) return NextResponse.json({ code: "UPSTREAM_INVALID_RESPONSE" }, { status: 502 });
      payload.guest_session_token = selector;
      const response = NextResponse.json(payload, { status: upstream.status });
      const expires = Date.parse(payload.expires_at);
      response.cookies.set(cookieName, token, { httpOnly: true, secure: process.env.NODE_ENV === "production", sameSite: "lax", path: "/", maxAge: Number.isFinite(expires) ? Math.max(1, Math.floor((expires - Date.now()) / 1000)) : 8 * 3600 });
      return response;
    }
    if (enrolling && upstream.ok) {
      const payload = await upstream.json();
      const token = payload.customer_auth_token;
      if (typeof token !== "string" || !/^[A-Za-z0-9_-]{32,160}$/.test(token)) {
        return NextResponse.json({ code: "UPSTREAM_INVALID_RESPONSE" }, { status: 502 });
      }
      delete payload.customer_auth_token;
      const response = NextResponse.json(payload, { status: upstream.status });
      response.cookies.set(customerCookieName, token, {
        httpOnly: true, secure: process.env.NODE_ENV === "production",
        sameSite: "lax", path: "/", maxAge: 2 * 3600,
      });
      return response;
    }
    const response = new NextResponse(upstream.body, {
      status: upstream.status,
      headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json", "Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no" },
    });
    if (loggingOut) response.cookies.set(customerCookieName, "", {
      httpOnly: true, secure: process.env.NODE_ENV === "production",
      sameSite: "lax", path: "/", maxAge: 0,
    });
    return response;
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
