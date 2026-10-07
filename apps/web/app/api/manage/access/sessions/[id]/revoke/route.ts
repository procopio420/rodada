import { NextRequest } from "next/server";
import { forwardAuthenticated } from "@/lib/server/auth-gateway";

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ id: string }> },
) {
  const { id } = await context.params;
  const body = (await request.json()) as Record<string, unknown>;
  return forwardAuthenticated(request, "/manage/access/sessions/" + id + "/revoke/", {
    method: "POST",
    body,
  });
}
