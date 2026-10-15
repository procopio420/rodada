import { NextRequest } from "next/server";
import { forwardAuthenticated } from "@/lib/server/auth-gateway";

// This companion deliberately has no payment or refund command path.
const reads = /^(tabs|tabs\/[^/]+|catalog\/products|dispatch\/(delivery|requests)|hospitality\/tables|hospitality\/zones|hospitality\/occupancies\/[^/]+\/party-size)$/;
const commands = /^(order-items\/[^/]+\/corrections\/cancel|tabs|tabs\/[^/]+\/(orders\/confirm|close|operations)|dispatch\/delivery\/[^/]+\/complete|dispatch\/requests\/[^/]+\/(claim|complete)|hospitality\/tables\/[^/]+\/(occupy|service\/(start|open-tab)|release|location|cleaning\/(start|complete))|hospitality\/occupancies\/[^/]+\/(tabs|tabs\/open|responsibility\/claim|party-size))$/;
async function forward(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  if (path.some(segment => !/^[a-zA-Z0-9_-]+$/.test(segment))) return Response.json({ code: "INVALID_PATH", message: "Rota inválida." }, { status: 400 });
  const route = path.join("/");
  const locationMove = request.method === "POST" && /^tabs\/[^/]+\/operations$/.test(route);
  if (!locationMove && !(request.method === "GET" ? reads : commands).test(route)) {
    return Response.json({ code: "ATTENDANCE_OPERATION_DISABLED", message: "Esta operação não está disponível no Atendimento Web sem pagamentos." }, { status: 403 });
  }
  let body: Record<string, unknown> | undefined;
  if (request.method === "POST") {
    try { body = await request.json(); } catch { return Response.json({ code: "INVALID_JSON", message: "Pedido inválido." }, { status: 400 }); }
    if (locationMove && (!body || Array.isArray(body) || body.kind !== "MOVE_LOCATION"
      || Object.keys(body).some(key => !["kind", "expected_version", "occupancy_id", "table_id", "reason", "idempotency_key"].includes(key))
      || !Number.isSafeInteger(body.expected_version) || Number(body.expected_version) < 1
      || typeof (body.occupancy_id ?? body.table_id) !== "string" || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(String(body.occupancy_id ?? body.table_id))
      || typeof body.idempotency_key !== "string" || !body.idempotency_key || body.idempotency_key.length > 120
      || (body.reason !== undefined && (typeof body.reason !== "string" || body.reason.length > 240)))) {
      return Response.json({ code: "ATTENDANCE_OPERATION_DISABLED", message: "Informe apenas o movimento de comanda para uma mesa ocupada." }, { status: 403 });
    }
  }
  if (request.method === "POST" && /^tabs\/[^/]+\/operations$/.test(route)) {
    const allowed = new Set(["kind", "expected_version", "occupancy_id", "table_id", "idempotency_key", "reason"]);
    if (body?.kind !== "MOVE_LOCATION" || Object.keys(body).some(key => !allowed.has(key))) {
      return Response.json({ code: "ATTENDANCE_OPERATION_DISABLED", message: "Somente mover a localização da comanda está disponível." }, { status: 403 });
    }
  }
  return forwardAuthenticated(request, "/" + route + "/" + request.nextUrl.search, { method: request.method as "GET" | "POST", body });
}
export const GET = forward;
export const POST = forward;
