import { NextRequest } from "next/server";
import { forwardAuthenticated } from "@/lib/server/auth-gateway";

export async function POST(request: NextRequest) {
  return forwardAuthenticated(request, "/auth/logout/", {
    method: "POST",
    body: {},
    clearAfter: true,
  });
}
