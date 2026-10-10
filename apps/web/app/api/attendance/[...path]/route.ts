import { NextRequest } from "next/server";
import { forwardAuthenticated } from "@/lib/server/auth-gateway";

// This companion deliberately has no payment or refund command path.
const reads = /^(tabs|tabs\/[^/]+|catalog\/products|dispatch\/(delivery|requests)|hospitality\/tables|hospitality\/zones|hospitality\/occupancies\/[^/]+\/party-size)$/;
const commands = /^(tabs|tabs\/[^/]+\/(orders\/confirm|close)|dispatch\/delivery\/[^/]+\/complete|dispatch\/requests\/[^/]+\/(claim|complete)|hospitality\/tables\/[^/]+\/(occupy|release|location|cleaning\/(start|complete))|hospitality\/occupancies\/[^/]+\/(tabs|party-size))$/;
async function forward(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  if (path.some(segment => !/^[a-zA-Z0-9_-]+$/.test(segment))) return Response.json({ code: "INVALID_PATH", message: "Rota inválida." }, { status: 400 });
  const route = path.join("/");
  if (!(request.method === "GET" ? reads : commands).test(route)) {
    return Response.json({ code: "ATTENDANCE_OPERATION_DISABLED", message: "Esta operação não está disponível no Atendimento Web sem pagamentos." }, { status: 403 });
  }
  let body: Record<string, unknown> | undefined;
  if (request.method === "POST") {
    try { body = await request.json(); } catch { return Response.json({ code: "INVALID_JSON", message: "Pedido inválido." }, { status: 400 }); }
  }
  return forwardAuthenticated(request, "/" + route + "/" + request.nextUrl.search, { method: request.method as "GET" | "POST", body });
}
export const GET = forward;
export const POST = forward;
