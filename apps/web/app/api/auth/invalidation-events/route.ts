import { NextRequest } from "next/server";
import { forwardAuthenticated } from "@/lib/server/auth-gateway";

export async function GET(request: NextRequest) {
  const after = request.nextUrl.searchParams.get("after") ?? "0";
  const normalized = /^\d+$/.test(after) ? after : "0";
  return forwardAuthenticated(
    request,
    "/auth/invalidation-events/?after=" + normalized,
  );
}
