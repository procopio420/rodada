"use client";

import Link from "next/link";
import { use, useCallback, useEffect, useRef, useState } from "react";
import { OperationalHeading } from "@/components/operational-heading";
import { ConnectivityNotice } from "@/components/connectivity-notice";
import { apiCall, asApiError, type StaffSessionView } from "@/lib/client/staff-auth";
import { useRealtime } from "@/lib/client/use-realtime";
import { paymentMethodLabel, paymentStatusLabel } from "@/lib/presentation-labels";

type Payment = { id: string; method: string; status: string; amount_cents: number; refunded_cents: number;
  refunds: { id: string; amount_cents: number; status: string; reason: string }[] };
type Tab = { id: string; display_label: string; state: string; payments: Payment[] };
type Context = { tab: Tab; payment: Payment };
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const money = (value: number) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value / 100);

async function read<T>(path: string): Promise<T> {
  const result = await apiCall<T>(path);
  if (!result.response.ok) throw new Error(asApiError(result.body).message);
  return result.body as T;
}

export default function PaymentContextPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [context, setContext] = useState<Context>();
  const [error, setError] = useState("");
  const [origin, setOrigin] = useState("/manage");
  const [loading, setLoading] = useState(true);
  const generation = useRef(0);
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    const candidate = new URLSearchParams(window.location.search).get("from") ?? "";
    const prefix = "/manage/alerts/";
    setOrigin(candidate.startsWith(prefix) && uuid.test(candidate.slice(prefix.length)) ? candidate : "/manage");
  }, [id]);
  const load = useCallback(async () => {
    const request = ++generation.current;
    setLoading(true); setContext(undefined); setError("");
    try {
      if (!uuid.test(id)) throw new Error("Identificador do pagamento inválido.");
      const before = await read<StaffSessionView>("/api/auth/me");
      const target = await read<{ tab_id: string; payment_id: string }>(`/api/pos/payments/${id}/recovery-context/`);
      if (target.payment_id !== id || !uuid.test(target.tab_id)) throw new Error("O pagamento consultado não corresponde ao contexto original.");
      const tab = await read<Tab>(`/api/pos/tabs/${target.tab_id}/`);
      const payment = tab.payments.find(row => row.id === id);
      if (tab.id !== target.tab_id || !payment) throw new Error("O pagamento original não está nesta comanda.");
      const after = await read<StaffSessionView>("/api/auth/me");
      if (before.session.id !== after.session.id || before.venue.id !== after.venue.id || before.staff.id !== after.staff.id) throw new Error("A sessão mudou. Consulte o pagamento novamente na sessão atual.");
      if (generation.current === request) setContext({ tab, payment });
    } catch (cause) {
      if (generation.current === request) setError(cause instanceof Error ? cause.message : "Não foi possível consultar o pagamento original.");
    } finally { if (generation.current === request) setLoading(false); }
  }, [id]);
  const connectivity = useRealtime(load, { relevant: event => event.type.startsWith("payment.") || event.type.startsWith("tab."),
    onRevoked: () => { ++generation.current; setContext(undefined); setLoading(false); setError("Entre novamente para consultar o pagamento."); } });
  useEffect(() => { if (!loading) heading.current?.focus(); }, [loading]);
  useEffect(() => () => { ++generation.current; }, [id]);
  const { tab, payment } = context ?? {};
  return <main className="appShell">
    <header className="productHeader"><div className="eyebrow">RODADA / GERÊNCIA</div>
      <OperationalHeading as="h1" icon="wallet">Conferir pagamento</OperationalHeading>
      <Link className="backLink" href={origin}>Voltar à revisão de origem →</Link>
    </header>
    <ConnectivityNotice {...connectivity} />
    <section className="panel" aria-labelledby="payment-context-title">
      <h2 id="payment-context-title" ref={heading} tabIndex={-1}>Pagamento original</h2>
      {loading && <p role="status">Consultando pagamento original…</p>}
      {error && <p className="notice" data-state="danger" role="alert">{error}</p>}
      {tab && payment && <>
        <p>{tab.display_label || "Comanda sem identificação"}{tab.state === "CLOSED" ? " · Encerrada" : ""}</p>
        <p>{paymentMethodLabel(payment.method)} · {paymentStatusLabel(payment.status)}</p>
        <div className="dataRow"><span>Valor do pagamento</span><strong>{money(payment.amount_cents)}</strong></div>
        <div className="dataRow"><span>Já estornado</span><strong>{money(payment.refunded_cents)}</strong></div>
        <div className="dataRow"><span>Saldo reembolsável</span><strong>{["CONFIRMED", "PARTIALLY_REFUNDED", "REFUNDED"].includes(payment.status) ? money(payment.amount_cents - payment.refunded_cents) : "Não confirmado"}</strong></div>
        <p className="muted">Esta consulta não confirma recebimento, concilia pagamento nem autoriza devolução.</p>
        <h3>Histórico de estornos</h3>
        {!payment.refunds.length && <p className="muted">Nenhum estorno registrado neste pagamento.</p>}
        {payment.refunds.map(refund => <div className="movement" key={refund.id}><div><strong>{money(refund.amount_cents)} · {paymentStatusLabel(refund.status)}</strong><small>{refund.reason || "Sem motivo registrado"}</small></div></div>)}
        <details><summary>Identificadores para auditoria</summary><p>Pagamento: {payment.id}</p><p>Comanda: {tab.id}</p></details>
      </>}
      <button className="buttonSecondary" disabled={loading} onClick={() => void load()}>Consultar novamente</button>
    </section>
  </main>;
}
