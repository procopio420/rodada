import { NextRequest } from "next/server";
import { forwardAuthenticated } from "@/lib/server/auth-gateway";

export async function GET(request: NextRequest) {
  return forwardAuthenticated(request, "/manage/access/audit/");
}
