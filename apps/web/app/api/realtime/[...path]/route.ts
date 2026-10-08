import { NextRequest } from "next/server";
import { forwardAuthenticated } from "@/lib/server/auth-gateway";
export const dynamic = "force-dynamic";
export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  if (path.length !== 1 || !["stream", "snapshot"].includes(path[0])) return new Response(null, { status: 404 });
  return forwardAuthenticated(request, `/realtime/${path[0]}/${request.nextUrl.search}`, { stream: path[0] === "stream" });
}
