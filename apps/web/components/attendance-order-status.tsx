import type { HistoricalOrder } from "./repeat-order";

const states: Record<string, string> = {
  NEW: "Na fila", ACCEPTED: "Aceito", PREPARING: "Em preparo", READY: "Pronto",
  PICKED_UP: "Retirado", DELIVERED: "Entregue", CANCELLED: "Cancelado",
};
const stations: Record<string, string> = { BAR: "Bar", KITCHEN: "Cozinha" };

/** Read model only: current catalog and optimistic submit responses never supply routes or states. */
export function AttendanceOrderStatus({ orders, fresh }: { orders: HistoricalOrder[]; fresh: boolean }) {
  const order = orders.filter(value => value.status === "CONFIRMED").reduce<HistoricalOrder | null>((latest, value) => {
    if (!latest) return value;
    const previous = Date.parse(latest.confirmed_at ?? ""), current = Date.parse(value.confirmed_at ?? "");
    return Number.isFinite(current) && (!Number.isFinite(previous) || current > previous) ? value : latest;
  }, null);
  if (!order) return null;
  const routes = [...new Set(order.items.map(item => `${stations[item.fulfillment_station_snapshot ?? ""] ?? "Destino não informado"} · ${states[item.state] ?? "Estado não informado"}`))];
  return <section className="attendanceOrderStatus" aria-label="Último pedido confirmado">
    <strong>Pedido #{order.id} confirmado</strong>
    <p>{order.items.map(item => `${item.quantity}× ${item.product_name}`).join(" · ") || "Itens não informados"}</p>
    <div className="attendanceOrderRoutes">{routes.map(route => <span key={route}>{route}</span>)}</div>
    {!fresh && <p role="status">Estado desatualizado. Confira a conexão para acompanhar a produção.</p>}
  </section>;
}
