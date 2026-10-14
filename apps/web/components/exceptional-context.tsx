"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { OperationalHeading } from "@/components/operational-heading";
import { ConnectivityNotice } from "@/components/connectivity-notice";
import { apiCall, asApiError, type StaffSessionView } from "@/lib/client/staff-auth";
import { useRealtime } from "@/lib/client/use-realtime";
import { paymentMethodLabel, paymentStatusLabel } from "@/lib/presentation-labels";

type Payment = { id: string; method: string; status: string; amount_cents: number; refunded_cents: number;
  refunds: { id: string; amount_cents: number; status: string; reason: string }[] };
type Item = { id: string; product_name: string; state: string; quantity: number; original_quantity: number; original_line_total_cents: number };
type Tab = { id: string; display_label: string; state: string; payments: Payment[]; orders: { items: Item[] }[] };
type Target = { tab_id: string; order_item_id: string; payment_id?: string; correction_id?: string; correction_status?: string };
type Context = { tab: Tab; item: Item; payment?: Payment; target: Target };
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const money = (value: number) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value / 100);

async function read<T>(path: string): Promise<T> {
  const result = await apiCall<T>(path);
  if (!result.response.ok) throw new Error(asApiError(result.body).message);
  return result.body as T;
}

export function ExceptionalContext({ id, kind }: { id: string; kind: "item" | "correction" }) {
  const [context, setContext] = useState<Context>();
  const [error, setError] = useState("");
  const [origin, setOrigin] = useState("/manage");
  const [loading, setLoading] = useState(true);
  const generation = useRef(0);
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    const candidate = new URLSearchParams(window.location.search).get("from") ?? "";
    const prefix = "/manage/alerts/";
    queueMicrotask(() => setOrigin(candidate === "/refunds" ? candidate : candidate.startsWith(prefix) && uuid.test(candidate.slice(prefix.length)) ? candidate : "/manage"));
  }, [id, kind]);
  const load = useCallback(async () => {
    const request = ++generation.current;
    setLoading(true); setContext(undefined); setError("");
    try {
      if (!uuid.test(id)) throw new Error("Identificador do registro inválido.");
      const before = await read<StaffSessionView>("/api/auth/me");
      const paymentId = new URLSearchParams(window.location.search).get("payment") ?? "";
      if (kind === "correction" && !uuid.test(paymentId)) throw new Error("Informe o pagamento original da correção.");
      const path = kind === "item" ? `/api/pos/order-items/${id}/recovery-context/` : `/api/pos/corrections/${id}/recovery-context/?payment_id=${paymentId}`;
      const target = await read<Target>(path);
      if (!uuid.test(target.tab_id) || !uuid.test(target.order_item_id) || (kind === "item" ? target.order_item_id !== id : target.correction_id !== id || target.payment_id !== paymentId || !["REQUESTED", "APPLIED", "REJECTED"].includes(target.correction_status ?? ""))) throw new Error("O registro consultado não corresponde ao contexto original.");
      const tab = await read<Tab>(`/api/pos/tabs/${target.tab_id}/`);
      const item = tab.orders.flatMap(order => order.items).find(row => row.id === target.order_item_id);
      const payment = tab.payments.find(row => row.id === target.payment_id);
      if (tab.id !== target.tab_id || !item || kind === "correction" && !payment) throw new Error("Os registros originais não estão nesta comanda.");
      const after = await read<StaffSessionView>("/api/auth/me");
      if (before.session.id !== after.session.id || before.venue.id !== after.venue.id || before.staff.id !== after.staff.id) throw new Error("A sessão mudou. Consulte o registro novamente na sessão atual.");
      if (generation.current === request) setContext({ tab, item, payment, target });
    } catch (cause) {
      if (generation.current === request) setError(cause instanceof Error ? cause.message : "Não foi possível consultar o registro original.");
    } finally { if (generation.current === request) setLoading(false); }
  }, [id, kind]);
  const connectivity = useRealtime(load, { relevant: event => event.type.startsWith("order.") || event.type.startsWith("correction.") || event.type.startsWith("payment.") || event.type.startsWith("tab."),
    onRevoked: () => { ++generation.current; setContext(undefined); setLoading(false); setError("Entre novamente para consultar o registro."); } });
  useEffect(() => { if (!loading) heading.current?.focus(); }, [loading]);
  useEffect(() => () => { ++generation.current; }, [id, kind]);
  const { tab, item, payment, target } = context ?? {};
  return <main className="appShell">
    <header className="productHeader"><div className="eyebrow">RODADA / GERÊNCIA</div>
      <OperationalHeading as="h1" icon="wallet">{kind === "item" ? "Conferir item" : "Conferir correção"}</OperationalHeading>
      <Link className="backLink" href={origin}>Voltar à revisão de origem →</Link>
    </header>
    <ConnectivityNotice {...connectivity} />
    <section className="panel" aria-labelledby="payment-context-title">
      <h2 id="payment-context-title" ref={heading} tabIndex={-1}>Registro original</h2>
      {loading && <p role="status">Consultando registro original…</p>}
      {error && <p className="notice" data-state="danger" role="alert">{error}</p>}
      {tab && item && target && <>
        <p>{tab.display_label || "Comanda sem identificação"}{tab.state === "CLOSED" ? " · Encerrada" : ""}</p>
        <h3>{item.product_name}</h3>
        <p>{({ NEW: "Novo", ACCEPTED: "Aceito", PREPARING: "Em preparo", READY: "Pronto", PICKED_UP: "Retirado", DELIVERED: "Entregue", CANCELLED: "Cancelado" } as Record<string, string>)[item.state] ?? "Estado não reconhecido"}</p>
        <div className="dataRow"><span>Quantidade original</span><strong>{item.original_quantity}</strong></div>
        <div className="dataRow"><span>Valor original do item</span><strong>{money(item.original_line_total_cents)}</strong></div>
        {kind === "correction" && <p>Correção: {({ REQUESTED: "Aguardando decisão", APPLIED: "Aplicada", REJECTED: "Rejeitada" } as Record<string, string>)[target.correction_status!]}</p>}
        {payment && <><h3>Pagamento vinculado</h3><p>{paymentMethodLabel(payment.method)} · {paymentStatusLabel(payment.status)}</p>
          <div className="dataRow"><span>Valor do pagamento</span><strong>{money(payment.amount_cents)}</strong></div>
          <div className="dataRow"><span>Já estornado</span><strong>{money(payment.refunded_cents)}</strong></div>
        </>}
        <p className="muted">Esta consulta não cancela item, aprova correção nem autoriza devolução.</p>
        <details><summary>Identificadores para auditoria</summary><p>Item: {item.id}</p><p>Comanda: {tab.id}</p>{target.correction_id && <p>Correção: {target.correction_id}</p>}{payment && <p>Pagamento: {payment.id}</p>}</details>
      </>}
      <button className="buttonSecondary" disabled={loading} onClick={() => void load()}>Consultar novamente</button>
    </section>
  </main>;
}
