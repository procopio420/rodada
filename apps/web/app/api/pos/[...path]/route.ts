import { NextRequest, NextResponse } from "next/server";
import { forwardAuthenticated } from "@/lib/server/auth-gateway";

async function forward(request: NextRequest, params: Promise<{ path: string[] }>) {
  const { path } = await params;
  if (path[0] === "developer" && process.env.RODADA_DEVELOPER_TOOLS !== "true") {
    return NextResponse.json({ code: "DEVELOPER_TOOLS_DISABLED", message: "Área DEV desabilitada neste ambiente." }, { status: 403 });
  }
  if (path[0] === "printing" && path[1] === "agents" && path[2] === "v1") {
    const resource = path.slice(3).join("/");
    const allowed = (request.method === "GET" && resource === "") || (request.method === "POST" && (
      ["enabled", "pairing/inspect", "pairing/approve"].includes(resource) ||
      /^[0-9a-f-]{36}\/revoke$/.test(resource)
    ));
    if (!allowed) return NextResponse.json({ code: "AGENT_DEVICE_ENDPOINT", message: "Endpoint exclusivo do computador." }, { status: 403 });
  }
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
