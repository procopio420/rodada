"use client";

import { paymentMethodLabel, paymentStatusLabel } from "@/lib/presentation-labels";

import { OperationalHeading } from "@/components/operational-heading";
import { OperationalIcon } from "@/components/operational-icon";
import styles from "./refunds.module.css";
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

function readRefundResources() {
  return Promise.all([
    apiCall<{ results: TabSummary[] }>("/api/pos/tabs/"),
    apiCall<{ results: CashPoint[] }>("/api/pos/cash/points/"),
  ]);
}

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

  const applyResources = useCallback(([tabsResult, cashResult]: Awaited<ReturnType<typeof readRefundResources>>) => {
    if (tabsResult.response.ok) setTabs((tabsResult.body as { results: TabSummary[] }).results);
    else setMessage(asApiError(tabsResult.body).message);
    if (cashResult.response.ok) {
      const open = (cashResult.body as { results: CashPoint[] }).results.filter((point) => point.active_shift);
      setCashPoints(open);
      setCashPointId((current) => open.some((point) => point.id === current) ? current : (open[0]?.id || ""));
    } else setMessage(asApiError(cashResult.body).message);
  }, []);
  const load = useCallback(async () => {
    setLoading(true);
    try { applyResources(await readRefundResources()); }
    catch { setMessage("Não foi possível atualizar os estornos. Confira a conexão."); }
    finally { setLoading(false); }
  }, [applyResources]);
  useEffect(() => {
    let active = true;
    void readRefundResources().then(results => { if (active) applyResources(results); }).catch(() => {
      if (active) setMessage("Não foi possível atualizar os estornos. Confira a conexão.");
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [applyResources]);

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

  return <main className="appShell"><header className="productHeader managementSubpageHeader"><Link className="backLink managementSubpageBack" href="/manage#financeiro"><OperationalIcon name="chevron-left" size={20} />Voltar ao Financeiro</Link><div className="eyebrow">RODADA / GERÊNCIA</div><OperationalHeading as="h1" icon="wallet">Estornos</OperationalHeading><p className="muted">Pagamento, saldo reembolsável e histórico sem apagar a venda original.</p></header>
    {message ? <div className="notice" data-state="danger" role="alert">{message}</div> : null}
    {loading && <div className="loadingState" role="status">Carregando estornos…</div>}
    <section className={`panel ${styles.entry}`} id="refund-manager" aria-labelledby="refund-manager-title"><OperationalHeading as="h2" icon="wallet" id="refund-manager-title">Confirmar gerente</OperationalHeading><fieldset className={styles.identity}><legend>Confirmar identidade</legend><div className="field"><label htmlFor="refund-manager-pin">PIN do gerente</label><input id="refund-manager-pin" aria-label="PIN do gerente" inputMode="numeric" type="password" value={pin} onChange={(event) => setPin(event.target.value)} placeholder="PIN do gerente" /></div><button className="buttonSecondary" onClick={() => void reauthenticate()}>Confirmar PIN</button></fieldset></section>
    {refundIntent.message ? <p className="notice" role="status" data-state={refundIntent.pending || !refundIntent.ready ? "warning" : "info"}>{refundIntent.message}</p> : null}
    {refundIntent.pending ? <section className={`panel ${styles.pending}`} id="refund-pending" aria-label="Estorno pendente"><OperationalHeading as="h2" icon="warning">Estorno pendente</OperationalHeading><p>Estorno de {money(refundIntent.pending.amount_cents)} no pagamento original.</p><p className="muted">Confira esta operação antes de devolver qualquer outro valor.</p><button className="buttonPrimary" disabled={refundIntent.busy || reviewLocked} onClick={() => void refundIntent.submit()}>{refundIntent.busy ? "Verificando…" : "Verificar mesmo estorno"}</button></section> : null}
    {!refundIntent.ready ? <button className="buttonSecondary" onClick={refundIntent.initialize}>Verificar armazenamento</button> : null}
    <fieldset className="workspaceLock" disabled={refundIntent.locked}>
    <section className={`panel ${styles.entry}`} id="refund-tab" aria-labelledby="refund-tab-title"><OperationalHeading as="h2" icon="wallet" id="refund-tab-title">Selecionar comanda</OperationalHeading><div className="field"><label htmlFor="refund-tab-select">Comanda</label><select id="refund-tab-select" aria-label="Comanda" value={detail?.id || ""} disabled={locked} onChange={(event) => void selectTab(event.target.value)}><option value="">Selecione uma comanda</option>{tabs.filter((tab) => tab.state !== "CLOSED").map((tab) => <option key={tab.id} value={tab.id}>{tab.display_label || "Sem identificação"} · {money(tab.exposure_cents)}</option>)}</select></div></section>
    {detail && detail.refund_required_corrections.some(item => item.refund_required_cents === 0) ? <section className="panel" aria-label="Revisões sem devolução"><OperationalHeading as="h2" icon="wallet">Revisar correções sem estorno</OperationalHeading>{detail.refund_required_corrections.filter(item => item.refund_required_cents === 0).map(item => <CorrectionWithoutRefund key={item.id} correction={item} locked={locked} onPending={setReviewLocked} onRefresh={() => selectTab(detail.id, true)} />)}</section> : null}
    {detail ? <section className="panel" aria-labelledby="refund-payment-title"><fieldset className="workspaceLock" disabled={locked}><OperationalHeading as="h2" icon="wallet" id="refund-payment-title">Consultar pagamento</OperationalHeading><div className="field"><label htmlFor="refund-payment-select">Pagamento elegível</label><select id="refund-payment-select" aria-label="Pagamento elegível" value={paymentId} onChange={(event) => setPaymentId(event.target.value)}>{detail.payments.map((payment) => <option key={payment.id} value={payment.id}>{paymentMethodLabel(payment.method)} · {paymentStatusLabel(payment.status)} · {money(payment.amount_cents - payment.refunded_cents)} disponível</option>)}</select></div>
      {selectedPayment ? <><div className={styles.summary} id="refund-payment-summary" role="group" aria-labelledby="refund-balance-title"><h3 id="refund-balance-title">Saldo do pagamento</h3><div className="dataRow"><span>Pagamento original</span><strong>{money(selectedPayment.amount_cents)}</strong></div><div className="dataRow"><span>Já estornado</span><strong>{money(selectedPayment.refunded_cents)}</strong></div><div className="dataRow"><span>Restante reembolsável</span><strong>{money(refundable)}</strong></div></div>{!!selectedPayment.refunds.length && <div className={styles.history} id="refund-history"><h3 id="refund-history-title">Histórico de estornos</h3><ul aria-labelledby="refund-history-title">{selectedPayment.refunds.map((item) => <li key={item.id}><p className="muted">{money(item.amount_cents)} · {paymentStatusLabel(item.status)} · {item.reason || "Sem motivo"}</p></li>)}</ul></div>}</> : null}
      <fieldset className={styles.command} id="refund-command-fields"><legend>Preparar estorno</legend>{detail.refund_required_corrections.length ? <div className="field"><label htmlFor="refund-correction">Correção pendente (opcional)</label><select id="refund-correction" aria-label="Correção pendente (opcional)" value={correctionId} onChange={(event) => setCorrectionId(event.target.value)}><option value="">Estorno avulso</option>{detail.refund_required_corrections.filter(item => item.refund_required_cents > 0).map((item) => <option key={item.id} value={item.id}>{item.item_name} · exige {money(item.refund_required_cents)}</option>)}</select></div> : null}
      {correction ? <div className="notice">Correção pendente: estorno exato de {money(correction.refund_required_cents)}.{selectedPayment && <><br /><Link className="backLink" href={`/manage/corrections/${encodeURIComponent(correction.id)}?payment=${encodeURIComponent(selectedPayment.id)}&from=${encodeURIComponent("/refunds")}`}>Conferir correção original →</Link></>}</div> : <><div className="field"><label htmlFor="refund-amount">Valor a estornar</label><input id="refund-amount" aria-label="Valor a estornar" inputMode="decimal" value={amount} onChange={(event) => setAmount(event.target.value)} placeholder="Valor a estornar" /></div><div className="field"><label htmlFor="refund-reason">Motivo do estorno</label><input id="refund-reason" aria-label="Motivo do estorno" value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Motivo" /></div></>}
      {selectedPayment?.method === "CASH" ? <div className="field"><label htmlFor="refund-cash-point">Caixa que devolverá o dinheiro</label><select id="refund-cash-point" aria-label="Caixa que devolverá o dinheiro" value={cashPointId} onChange={(event) => setCashPointId(event.target.value)}><option value="">Caixa que devolverá o dinheiro</option>{cashPoints.map((point) => <option key={point.id} value={point.id}>{point.label}</option>)}</select></div> : null}
      <button className="buttonPrimary" disabled={locked || !selectedPayment || refundable <= 0} onClick={() => void refund()}>{refundIntent.busy ? "Confirmando…" : correction ? `Estornar ${money(correction.refund_required_cents)}` : "Confirmar estorno"}</button></fieldset></fieldset></section> : null}
    </fieldset>
  </main>;
}
