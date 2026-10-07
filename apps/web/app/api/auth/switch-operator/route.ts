import { NextRequest } from "next/server";
import { forwardAuthenticated } from "@/lib/server/auth-gateway";

export async function POST(request: NextRequest) {
  const body = (await request.json()) as Record<string, unknown>;
  return forwardAuthenticated(request, "/auth/switch-operator/", {
    method: "POST",
    body,
  });
}
