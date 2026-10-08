"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiCall, asApiError } from "@/lib/client/staff-auth";

type TabSummary = { id: string; display_label: string; exposure_cents: number; state: string };
type Refund = { id: string; amount_cents: number; status: string; reason: string; confirmed_at: string | null };
type Payment = { id: string; amount_cents: number; method: string; status: string; confirmed_at: string | null; refunded_cents: number; refunds: Refund[] };
type Correction = { id: string; order_item_id: string; item_name: string; reason_code: string; refund_required_cents: number };
type TabDetail = TabSummary & { payments: Payment[]; refund_required_corrections: Correction[] };
type CashPoint = { id: string; label: string; active_shift: { id: string } | null };

const money = (value = 0) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value / 100);

export default function RefundsPage() {
  const [tabs, setTabs] = useState<TabSummary[]>([]);
  const [detail, setDetail] = useState<TabDetail | null>(null);
  const [cashPoints, setCashPoints] = useState<CashPoint[]>([]);
  const [paymentId, setPaymentId] = useState("");
  const [correctionId, setCorrectionId] = useState("");
  const [amount, setAmount] = useState("");
  const [reason, setReason] = useState("");
  const [cashPointId, setCashPointId] = useState("");
  const [pin, setPin] = useState("");
  const [message, setMessage] = useState("");
  const [working, setWorking] = useState(false);
  const intentRef = useRef<string | null>(null);

  const load = useCallback(async () => {
    const [tabsResult, cashResult] = await Promise.all([
      apiCall<{ results: TabSummary[] }>("/api/pos/tabs/"),
      apiCall<{ results: CashPoint[] }>("/api/pos/cash/points/"),
    ]);
    if (tabsResult.response.ok) setTabs((tabsResult.body as { results: TabSummary[] }).results);
    if (cashResult.response.ok) {
      const open = (cashResult.body as { results: CashPoint[] }).results.filter((point) => point.active_shift);
      setCashPoints(open);
      setCashPointId((current) => open.some((point) => point.id === current) ? current : (open[0]?.id || ""));
    }
  }, []);
  useEffect(() => { void load(); }, [load]);

  const selectTab = async (tabId: string) => {
    const result = await apiCall<TabDetail>(`/api/pos/tabs/${tabId}/`);
    if (!result.response.ok) { setMessage(asApiError(result.body).message); return; }
    const next = result.body as TabDetail;
    setDetail(next);
    setPaymentId(next.payments.find((payment) => payment.amount_cents > payment.refunded_cents)?.id || "");
    setCorrectionId(next.refund_required_corrections[0]?.id || "");
    setAmount("");
  };

  const selectedPayment = detail?.payments.find((payment) => payment.id === paymentId) || null;
  const correction = detail?.refund_required_corrections.find((item) => item.id === correctionId) || null;
  const refundable = selectedPayment ? selectedPayment.amount_cents - selectedPayment.refunded_cents : 0;

  const reauthenticate = async () => {
    if (!pin) return;
    const result = await apiCall("/api/auth/reauthenticate", { method: "POST", body: JSON.stringify({ pin }) });
    setPin("");
    if (result.response.ok) setMessage("PIN confirmado. Agora confirme o estorno.");
    else setMessage(asApiError(result.body).message);
  };

  const refund = async () => {
    if (!detail || !selectedPayment || working) return;
    const amountCents = correction?.refund_required_cents || Math.round(Number(amount.replace(",", ".")) * 100);
    if (!amountCents || amountCents <= 0) { setMessage("Informe um valor de estorno válido."); return; }
    if (!correction && !reason.trim()) { setMessage("Informe o motivo do estorno."); return; }
    if (selectedPayment.method === "CASH" && !cashPointId) { setMessage("Selecione o caixa que fará a devolução em dinheiro."); return; }
    setWorking(true);
    const key = intentRef.current || crypto.randomUUID();
    intentRef.current = key;
    const path = correction
      ? `/api/pos/corrections/${correction.id}/settle-refund/`
      : `/api/pos/payments/${selectedPayment.id}/refunds/`;
    const body = correction
      ? { payment_id: selectedPayment.id, amount_cents: amountCents, refund_idempotency_key: key, cash_point_id: cashPointId || undefined }
      : { amount_cents: amountCents, idempotency_key: key, reason: reason.trim(), cash_point_id: cashPointId || undefined };
    try {
      const result = await apiCall(path, { method: "POST", body: JSON.stringify(body) });
      if (result.response.ok) {
        intentRef.current = null;
        setMessage("Estorno registrado. O pagamento original foi preservado no histórico.");
        await selectTab(detail.id);
        await load();
      } else {
        const error = asApiError(result.body);
        setMessage(error.code === "REAUTH_REQUIRED" ? "Confirme o PIN de gerente e tente novamente." : error.message);
        if (result.response.status < 500) intentRef.current = null;
      }
    } catch {
      setMessage("Não foi possível confirmar o estorno. Não tente outro valor: use Confirmar novamente para consultar esta mesma operação.");
    } finally { setWorking(false); }
  };

  return <main className="appShell"><header className="productHeader"><div className="eyebrow">RODADA / GERÊNCIA</div><h1>Estornos</h1><p className="muted">Pagamento, saldo reembolsável e histórico sem apagar a venda original.</p></header>
    {message ? <div className="notice" data-state="danger">{message}</div> : null}
    <section className="panel"><h2>Confirmar gerente</h2><div className="field"><input inputMode="numeric" type="password" value={pin} onChange={(event) => setPin(event.target.value)} placeholder="PIN do gerente" /></div><button className="buttonSecondary" onClick={() => void reauthenticate()}>Confirmar PIN</button></section>
    <section className="panel"><h2>Comanda</h2><div className="field"><select value={detail?.id || ""} onChange={(event) => void selectTab(event.target.value)}><option value="">Selecione uma comanda</option>{tabs.filter((tab) => tab.state !== "CLOSED").map((tab) => <option key={tab.id} value={tab.id}>{tab.display_label || "Sem identificação"} · {money(tab.exposure_cents)}</option>)}</select></div></section>
    {detail ? <section className="panel"><h2>Pagamento elegível</h2><div className="field"><select value={paymentId} onChange={(event) => setPaymentId(event.target.value)}>{detail.payments.map((payment) => <option key={payment.id} value={payment.id}>{payment.method} · {payment.status} · {money(payment.amount_cents - payment.refunded_cents)} disponível</option>)}</select></div>
      {selectedPayment ? <><div className="dataRow"><span>Pagamento original</span><strong>{money(selectedPayment.amount_cents)}</strong></div><div className="dataRow"><span>Já estornado</span><strong>{money(selectedPayment.refunded_cents)}</strong></div><div className="dataRow"><span>Restante reembolsável</span><strong>{money(refundable)}</strong></div>{selectedPayment.refunds.map((item) => <p className="muted" key={item.id}>{money(item.amount_cents)} · {item.status} · {item.reason || "Sem motivo"}</p>)}</> : null}
      {detail.refund_required_corrections.length ? <div className="field"><label>Correção pendente (opcional)</label><select value={correctionId} onChange={(event) => setCorrectionId(event.target.value)}><option value="">Estorno avulso</option>{detail.refund_required_corrections.map((item) => <option key={item.id} value={item.id}>{item.item_name} · exige {money(item.refund_required_cents)}</option>)}</select></div> : null}
      {correction ? <div className="notice">Correção pendente: estorno exato de {money(correction.refund_required_cents)}.</div> : <><div className="field"><input inputMode="decimal" value={amount} onChange={(event) => setAmount(event.target.value)} placeholder="Valor a estornar" /></div><div className="field"><input value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Motivo" /></div></>}
      {selectedPayment?.method === "CASH" ? <div className="field"><select value={cashPointId} onChange={(event) => setCashPointId(event.target.value)}><option value="">Caixa que devolverá o dinheiro</option>{cashPoints.map((point) => <option key={point.id} value={point.id}>{point.label}</option>)}</select></div> : null}
      <button className="buttonPrimary" disabled={working || !selectedPayment || refundable <= 0} onClick={() => void refund()}>{working ? "Confirmando…" : correction ? `Estornar ${money(correction.refund_required_cents)}` : "Confirmar estorno"}</button></section> : null}
  </main>;
}
