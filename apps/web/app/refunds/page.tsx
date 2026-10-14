"use client";

import { paymentMethodLabel, paymentStatusLabel } from "@/lib/presentation-labels";

import { OperationalHeading } from "@/components/operational-heading";
import { CorrectionWithoutRefund } from "@/components/correction-without-refund";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useManualRefundIntent } from "@/lib/client/manual-refund-intent";
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
  const [loading, setLoading] = useState(true);
  const [reviewLocked, setReviewLocked] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
    const [tabsResult, cashResult] = await Promise.all([
      apiCall<{ results: TabSummary[] }>("/api/pos/tabs/"),
      apiCall<{ results: CashPoint[] }>("/api/pos/cash/points/"),
    ]);
    if (tabsResult.response.ok) setTabs((tabsResult.body as { results: TabSummary[] }).results);
    else setMessage(asApiError(tabsResult.body).message);
    if (cashResult.response.ok) {
      const open = (cashResult.body as { results: CashPoint[] }).results.filter((point) => point.active_shift);
      setCashPoints(open);
      setCashPointId((current) => open.some((point) => point.id === current) ? current : (open[0]?.id || ""));
    } else setMessage(asApiError(cashResult.body).message);
    } catch { setMessage("Não foi possível atualizar os estornos. Confira a conexão."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  const selectTab = async (tabId: string, requireSuccess = false) => {
    const result = await apiCall<TabDetail>(`/api/pos/tabs/${tabId}/`);
    if (!result.response.ok) { setMessage(asApiError(result.body).message); if (requireSuccess) throw new Error("Refresh failed"); return; }
    const next = result.body as TabDetail;
    setDetail(next);
    setTabs(current => current.map(tab => tab.id === next.id ? { ...tab, exposure_cents: next.exposure_cents, state: next.state } : tab));
    setPaymentId(next.payments.find((payment) => payment.amount_cents > payment.refunded_cents)?.id || "");
    setCorrectionId(next.refund_required_corrections.find(item => item.refund_required_cents > 0)?.id || "");
    setAmount("");
  };

  const selectedPayment = detail?.payments.find((payment) => payment.id === paymentId) || null;
  const correction = detail?.refund_required_corrections.find((item) => item.id === correctionId) || null;
  const refundable = selectedPayment ? selectedPayment.amount_cents - selectedPayment.refunded_cents : 0;

  const reauthenticate = async () => {
    if (!pin) return;
    const result = await apiCall("/api/auth/reauthenticate", { method: "POST", body: JSON.stringify({ pin }) });
    setPin("");
    if (result.response.ok) setMessage("PIN confirmado. Agora confirme a decisão.");
    else setMessage(asApiError(result.body).message);
  };

  const refundIntent = useManualRefundIntent(async tabId => { await selectTab(tabId, true); await load(); });
  const locked = reviewLocked || refundIntent.locked;
  const refund = () => {
    if (!detail || !selectedPayment || locked) return;
    const normalized = amount.trim().replace(",", ".");
    const [whole, fraction = ""] = normalized.split(".");
    const amountCents = correction?.refund_required_cents || Number(whole) * 100 + Number(fraction.padEnd(2, "0"));
    if ((!correction && !/^\d+(\.\d{1,2})?$/.test(normalized)) || !Number.isSafeInteger(amountCents) || amountCents <= 0 || amountCents > 2147483647) {
      setMessage("Informe um valor de estorno válido com até duas casas decimais."); return;
    }
    if (!correction && (!reason.trim() || reason.trim().length > 240)) { setMessage("Informe o motivo do estorno com até 240 caracteres."); return; }
    if (selectedPayment.method === "CASH" && !cashPointId) { setMessage("Selecione o caixa que fará a devolução em dinheiro."); return; }
    setMessage("");
    void refundIntent.submit({ tab: detail.id, payment: selectedPayment.id, correction: correction?.id || null,
      amount_cents: amountCents, reason: correction ? `correction:${correction.reason_code}` : reason.trim(),
      cash_point_id: selectedPayment.method === "CASH" ? cashPointId : null });
  };

  return <main className="appShell"><header className="productHeader"><div className="eyebrow">RODADA / GERÊNCIA</div><OperationalHeading as="h1" icon="wallet">Estornos</OperationalHeading><p className="muted">Pagamento, saldo reembolsável e histórico sem apagar a venda original.</p></header>
    {message ? <div className="notice" data-state="danger" role="alert">{message}</div> : null}
    {loading && <div className="loadingState" role="status">Carregando estornos…</div>}
    <section className="panel"><OperationalHeading as="h2" icon="wallet">Confirmar gerente</OperationalHeading><div className="field"><input aria-label="PIN do gerente" inputMode="numeric" type="password" value={pin} onChange={(event) => setPin(event.target.value)} placeholder="PIN do gerente" /></div><button className="buttonSecondary" onClick={() => void reauthenticate()}>Confirmar PIN</button></section>
    {refundIntent.message ? <p className="notice" role="status" data-state={refundIntent.pending || !refundIntent.ready ? "warning" : "info"}>{refundIntent.message}</p> : null}
    {refundIntent.pending ? <section className="panel" aria-label="Estorno pendente"><p>Estorno de {money(refundIntent.pending.amount_cents)} no pagamento original.</p><p className="muted">Confira esta operação antes de devolver qualquer outro valor.</p><button className="buttonPrimary" disabled={refundIntent.busy || reviewLocked} onClick={() => void refundIntent.submit()}>{refundIntent.busy ? "Verificando…" : "Verificar mesmo estorno"}</button></section> : null}
    {!refundIntent.ready ? <button className="buttonSecondary" onClick={refundIntent.initialize}>Verificar armazenamento</button> : null}
    <fieldset className="workspaceLock" disabled={refundIntent.locked}>
    <section className="panel"><OperationalHeading as="h2" icon="wallet">Comanda</OperationalHeading><div className="field"><select aria-label="Comanda" value={detail?.id || ""} disabled={locked} onChange={(event) => void selectTab(event.target.value)}><option value="">Selecione uma comanda</option>{tabs.filter((tab) => tab.state !== "CLOSED").map((tab) => <option key={tab.id} value={tab.id}>{tab.display_label || "Sem identificação"} · {money(tab.exposure_cents)}</option>)}</select></div></section>
    {detail && detail.refund_required_corrections.some(item => item.refund_required_cents === 0) ? <section className="panel" aria-label="Revisões sem devolução"><OperationalHeading as="h2" icon="wallet">Revisar correções sem estorno</OperationalHeading>{detail.refund_required_corrections.filter(item => item.refund_required_cents === 0).map(item => <CorrectionWithoutRefund key={item.id} correction={item} locked={locked} onPending={setReviewLocked} onRefresh={() => selectTab(detail.id, true)} />)}</section> : null}
    {detail ? <section className="panel"><fieldset className="workspaceLock" disabled={locked}><OperationalHeading as="h2" icon="wallet">Pagamento elegível</OperationalHeading><div className="field"><select aria-label="Pagamento elegível" value={paymentId} onChange={(event) => setPaymentId(event.target.value)}>{detail.payments.map((payment) => <option key={payment.id} value={payment.id}>{paymentMethodLabel(payment.method)} · {paymentStatusLabel(payment.status)} · {money(payment.amount_cents - payment.refunded_cents)} disponível</option>)}</select></div>
      {selectedPayment ? <><div className="dataRow"><span>Pagamento original</span><strong>{money(selectedPayment.amount_cents)}</strong></div><div className="dataRow"><span>Já estornado</span><strong>{money(selectedPayment.refunded_cents)}</strong></div><div className="dataRow"><span>Restante reembolsável</span><strong>{money(refundable)}</strong></div>{selectedPayment.refunds.map((item) => <p className="muted" key={item.id}>{money(item.amount_cents)} · {paymentStatusLabel(item.status)} · {item.reason || "Sem motivo"}</p>)}</> : null}
      {detail.refund_required_corrections.length ? <div className="field"><label>Correção pendente (opcional)</label><select aria-label="Correção pendente (opcional)" value={correctionId} onChange={(event) => setCorrectionId(event.target.value)}><option value="">Estorno avulso</option>{detail.refund_required_corrections.filter(item => item.refund_required_cents > 0).map((item) => <option key={item.id} value={item.id}>{item.item_name} · exige {money(item.refund_required_cents)}</option>)}</select></div> : null}
      {correction ? <div className="notice">Correção pendente: estorno exato de {money(correction.refund_required_cents)}.{selectedPayment && <><br /><Link className="backLink" href={`/manage/corrections/${encodeURIComponent(correction.id)}?payment=${encodeURIComponent(selectedPayment.id)}&from=${encodeURIComponent("/refunds")}`}>Conferir correção original →</Link></>}</div> : <><div className="field"><input aria-label="Valor a estornar" inputMode="decimal" value={amount} onChange={(event) => setAmount(event.target.value)} placeholder="Valor a estornar" /></div><div className="field"><input aria-label="Motivo do estorno" value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Motivo" /></div></>}
      {selectedPayment?.method === "CASH" ? <div className="field"><select aria-label="Caixa que devolverá o dinheiro" value={cashPointId} onChange={(event) => setCashPointId(event.target.value)}><option value="">Caixa que devolverá o dinheiro</option>{cashPoints.map((point) => <option key={point.id} value={point.id}>{point.label}</option>)}</select></div> : null}
      <button className="buttonPrimary" disabled={locked || !selectedPayment || refundable <= 0} onClick={() => void refund()}>{refundIntent.busy ? "Confirmando…" : correction ? `Estornar ${money(correction.refund_required_cents)}` : "Confirmar estorno"}</button></fieldset></section> : null}
    </fieldset>
  </main>;
}
