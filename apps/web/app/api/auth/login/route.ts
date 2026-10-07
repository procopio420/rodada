import { NextRequest } from "next/server";
import { loginThroughGateway } from "@/lib/server/auth-gateway";

export async function POST(request: NextRequest) {
  const body = (await request.json()) as Record<string, unknown>;
  return loginThroughGateway(request, body);
}
