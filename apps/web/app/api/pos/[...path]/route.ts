import { NextRequest } from "next/server";
import { forwardAuthenticated } from "@/lib/server/auth-gateway";

async function forward(request: NextRequest, params: Promise<{ path: string[] }>) {
  const { path } = await params;
  let body: Record<string, unknown> | undefined;
  if (request.method !== "GET") {
    try { body = await request.json(); } catch { body = {}; }
  }
  return forwardAuthenticated(request, "/" + path.join("/") + "/" + request.nextUrl.search, {
    method: request.method as "GET" | "POST" | "PATCH" | "PUT",
    body,
  });
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) { return forward(request, context.params); }
export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) { return forward(request, context.params); }
export async function PATCH(request: NextRequest, context: { params: Promise<{ path: string[] }> }) { return forward(request, context.params); }
export async function PUT(request: NextRequest, context: { params: Promise<{ path: string[] }> }) { return forward(request, context.params); }
