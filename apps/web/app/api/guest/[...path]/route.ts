import { NextRequest, NextResponse } from "next/server";

import { rejectCrossOriginMutation } from "@/lib/server/auth-gateway";

const apiBaseUrl = (process.env.RODADA_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

async function forward(request: NextRequest, params: Promise<{ path: string[] }>) {
  if (request.method !== "GET") {
    const rejected = rejectCrossOriginMutation(request);
    if (rejected) return rejected;
  }

  const { path } = await params;
  const headers = new Headers({ Accept: "application/json" });
  const guestSession = request.headers.get("x-guest-session");
  if (guestSession) headers.set("X-Guest-Session", guestSession);

  let body: string | undefined;
  if (request.method !== "GET") {
    headers.set("Content-Type", "application/json");
    body = await request.text();
  }

  try {
    const upstream = await fetch(`${apiBaseUrl}/guest/${path.join("/")}/`, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
    });
    return new NextResponse(upstream.body, {
      status: upstream.status,
      headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json" },
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
