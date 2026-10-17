"use client";

import { useEffect, useRef, useState } from "react";
import { tabReference } from "@/lib/client/tab-identity";
import { OperationalHeading } from "@/components/operational-heading";
import { apiCall, asApiError, type StaffSessionView } from "@/lib/client/staff-auth";

const storageKey = "rodada.intent.pos-cash.v1";
type Tab = { id: string; display_label: string; table_label?: string | null; version: number; state: string; exposure_cents?: number };
type CashPoint = { id: string; label: string };
type LegacyIntent = {
  schema: 1; venue: string; staff: string; session: string; tab: string; captured_at: string;
  payload: { amount_cents: number; expected_version: number; method: "CASH"; cash_point_id: string; idempotency_key: string; originating_session_id: string };
};
type Intent = LegacyIntent | (Omit<LegacyIntent, "schema"> & {
  schema: 2; api_root: "/api/pos" | "/api/attendance";
  phase: "PAYMENT_PENDING" | "PAYMENT_CONFIRMED"; payment_id: string | null;
  close_requested: boolean;
});
const money = (value: number) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value / 100);
const positiveInteger = (value: unknown) => Number.isSafeInteger(value) && Number(value) > 0 && Number(value) <= 2147483647;
const safeInitialRejections = new Set([
  "INVALID_PAYMENT", "VERSION_CONFLICT", "TAB_CLOSED", "PAYMENT_EXCEEDS_EXPOSURE", "PAYMENT_ALREADY_PENDING",
  "CASH_POINT_REQUIRED", "ACTIVE_CASH_SHIFT_REQUIRED", "CASH_SHIFT_COUNTING", "CASH_SHIFT_CLOSED", "INVALID_CASH_TENDER",
  "SERVICE_REASSESSMENT_REQUIRED",
]);

function readIntent(): Intent | null {
  const raw = sessionStorage.getItem(storageKey);
  if (raw === null) return null;
  const intent = JSON.parse(raw) as Intent;
  const p = intent?.payload;
  if (![1, 2].includes(intent?.schema) || !p || ![intent.venue, intent.staff, intent.session, intent.tab, intent.captured_at, p.cash_point_id, p.idempotency_key].every(v => typeof v === "string" && !!v)
    || !Number.isFinite(Date.parse(intent.captured_at)) || !positiveInteger(p.amount_cents) || !positiveInteger(p.expected_version)
    || p.method !== "CASH" || p.originating_session_id !== intent.session
    || Object.keys(intent).sort().join() !== (intent.schema === 1
      ? "captured_at,payload,schema,session,staff,tab,venue"
      : "api_root,captured_at,close_requested,payload,payment_id,phase,schema,session,staff,tab,venue")
    || (intent.schema === 2 && (!["/api/pos", "/api/attendance"].includes(intent.api_root)
      || typeof intent.close_requested !== "boolean"
      || !["PAYMENT_PENDING", "PAYMENT_CONFIRMED"].includes(intent.phase)
      || (intent.phase === "PAYMENT_PENDING" ? intent.payment_id !== null : typeof intent.payment_id !== "string" || !intent.payment_id)))
    || Object.keys(p).sort().join() !== "amount_cents,cash_point_id,expected_version,idempotency_key,method,originating_session_id")
    throw new Error("Invalid cash receipt envelope");
  return intent;
}

function clearIntent(intent: Intent) {
  const saved = sessionStorage.getItem(storageKey);
  if (saved !== null && saved !== JSON.stringify(intent)) throw new Error("Receipt envelope changed");
  sessionStorage.removeItem(storageKey);
}

export function PosCashReceipt({ tab, points, locked, onPendingChange, onConfirmed,
  apiRoot = "/api/pos", presentation = "pos", allowCloseAfterReceipt = false, onClosed, onPaymentSurfaceChange }: {
  tab: Tab | null; points: CashPoint[]; locked: boolean;
  apiRoot?: "/api/pos" | "/api/attendance"; presentation?: "pos" | "attendance";
  onPaymentSurfaceChange?: (open: boolean) => void;
  allowCloseAfterReceipt?: boolean; onClosed?: (tabId: string) => Promise<void>;
  onPendingChange: (pending: boolean) => void; onConfirmed: (tabId: string) => Promise<void>;
}) {
  const [amount, setAmount] = useState("");
  const [paymentOpen, setPaymentOpen] = useState(false);
  const [pointId, setPointId] = useState("");
  const [ready, setReady] = useState(false);
  const [pending, setPending] = useState<Intent | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [canKeepOpen, setCanKeepOpen] = useState(false);
  const intentRef = useRef<Intent | null>(null);
  const sending = useRef(false);

  async function initialize() {
    try {
      // Probe writes too: a readable store may still refuse persistence.
      const saved = readIntent();
      const probe = `${storageKey}.probe`;
      sessionStorage.setItem(probe, "1"); sessionStorage.removeItem(probe);
      intentRef.current = saved; setPending(saved); setReady(true);
      if (saved) setMessage(saved.schema === 2 && saved.payment_id && saved.close_requested
        ? "Há um recebimento registrado e encerramento pendente. Verifique a mesma operação sem receber novamente."
        : "Há um recebimento aguardando confirmação. Verifique a mesma operação antes de receber novamente.");
    } catch {
      setReady(false);
      setMessage("Não foi possível preservar o recebimento neste navegador. Confira o histórico com a gerência antes de continuar.");
    }
  }
  useEffect(() => { queueMicrotask(() => void initialize()); }, []);
  useEffect(() => { onPendingChange(!ready || !!pending || busy || paymentOpen); }, [ready, pending, busy, paymentOpen, onPendingChange]);

  const activePoint = pointId || points[0]?.id || "";
  async function collect(fullAndClose = false, keepOpen = false) {
    if (sending.current || !ready || (!intentRef.current && locked)) return;
    sending.current = true; setBusy(true); setCanKeepOpen(false);
    let attempted = false;
    const recovering = !!intentRef.current;
    try {
      const auth = await apiCall<StaffSessionView>("/api/auth/me");
      if (!auth.response.ok || !auth.body || !("session" in auth.body)) {
        setMessage("Confira sua sessão antes de retomar. O recebimento pendente foi preservado."); return;
      }
      const session = auth.body;
      let intent = intentRef.current;
      if (intent && (intent.venue !== session.venue.id || intent.staff !== session.staff.id || intent.session !== session.session.id)) {
        setMessage("Este recebimento pertence à sessão original. Solicite revisão à gerência; ele não será enviado nesta sessão."); return;
      }
      if (!intent) {
        const normalized = fullAndClose && tab && positiveInteger(tab.exposure_cents)
          ? (tab.exposure_cents! / 100).toFixed(2) : amount.trim().replace(",", ".");
        if (fullAndClose && (!allowCloseAfterReceipt || !positiveInteger(tab?.exposure_cents))) return;
        if (!tab || ["CLOSED", "CANCELLED"].includes(tab.state) || !activePoint || !/^\d+(\.\d{1,2})?$/.test(normalized)) {
          setMessage("Selecione uma comanda, um caixa aberto e um valor válido com até duas casas decimais."); return;
        }
        const [whole, fraction = ""] = normalized.split(".");
        const cents = Number(whole) * 100 + Number(fraction.padEnd(2, "0"));
        if (!positiveInteger(cents) || !positiveInteger(tab.version)) {
          setMessage("Confira o valor e atualize a comanda antes de receber."); return;
        }
        intent = { schema: 1, venue: session.venue.id, staff: session.staff.id, session: session.session.id,
          tab: tab.id, captured_at: new Date().toISOString(), payload: { amount_cents: cents, expected_version: tab.version,
            method: "CASH", cash_point_id: activePoint, idempotency_key: crypto.randomUUID(), originating_session_id: session.session.id } };
        if (presentation === "attendance") intent = { ...intent, schema: 2, api_root: apiRoot,
          phase: "PAYMENT_PENDING", payment_id: null, close_requested: fullAndClose };
        // Persistence must succeed before any money-changing request.
        sessionStorage.setItem(storageKey, JSON.stringify(intent));
        intentRef.current = intent; setPending(intent);
      }
      // Recovery always uses the original gateway, including legacy POS intents.
      const root = intent.schema === 1 ? "/api/pos" : intent.api_root;
      const saveProgress = (next: Intent) => {
        if (sessionStorage.getItem(storageKey) !== JSON.stringify(intent)) throw new Error("Receipt envelope changed");
        sessionStorage.setItem(storageKey, JSON.stringify(next));
        intent = next; intentRef.current = next; setPending(next);
      };
      if (sessionStorage.getItem(storageKey) !== JSON.stringify(intent)) throw new Error("Receipt envelope changed");
      attempted = true;
      const settledStatuses = ["CONFIRMED", "PARTIALLY_REFUNDED", "REFUNDED"];
      let paymentId = intent.schema === 2 ? intent.payment_id : null;
      if (!paymentId) {
        const result = await apiCall<{ id: string; status: string }>(`${root}/tabs/${intent.tab}/payments/`, {
          method: "POST", body: JSON.stringify(intent.payload),
        });
        if (!result.response.ok) {
          const error = asApiError(result.body);
          if (!recovering && [400, 409].includes(result.response.status) && safeInitialRejections.has(error.code)) {
            clearIntent(intent); intentRef.current = null; setPending(null);
          }
          setMessage(error.message); return;
        }
        if (!result.body || !("id" in result.body) || !result.body.id || !settledStatuses.includes(result.body.status))
          throw new Error("Missing canonical payment");
        paymentId = result.body.id;
        // Commit this phase before readback/close: a failed close never posts Payment again.
        if (intent.schema === 2) saveProgress({ ...intent, phase: "PAYMENT_CONFIRMED", payment_id: paymentId });
      }
      type Bill = { id: string; state: string; version: number; exposure_cents: number;
        payments: { id: string; method: string; amount_cents: number; status: string }[] };
      const expectedAmount = intent.payload.amount_cents;
      const detail = await apiCall<Bill>(`${root}/tabs/${intent.tab}/`);
      if (!detail.response.ok || !detail.body || !("payments" in detail.body)
        || (intent.schema === 2 && detail.body.id !== intent.tab)
        || !detail.body.payments?.some(p => p.id === paymentId && p.method === "CASH" && p.amount_cents === expectedAmount && settledStatuses.includes(p.status)))
        throw new Error("Receipt readback unavailable");
      if (keepOpen) {
        if (intent.schema !== 2 || !intent.close_requested || !intent.payment_id || detail.body.state === "CLOSED")
          throw new Error("Receipt cannot remain open");
        // An explicit operator decision can withdraw the unexecuted close;
        // preserve the confirmed Payment identity until canonical refresh finishes.
        saveProgress({ ...intent, close_requested: false });
      }
      if (intent.schema === 2 && intent.close_requested) {
        if (detail.body.state !== "CLOSED") {
          if (detail.body.exposure_cents !== 0) {
            setCanKeepOpen(true);
            setMessage("Recebimento confirmado; encerramento pendente. O saldo mudou. Confira a conta antes de encerrar."); return;
          }
          const closed = await apiCall<{ id: string; state: string }>(`${root}/tabs/${intent.tab}/close/`, {
            method: "POST", body: JSON.stringify({}),
          });
          if (!closed.response.ok) {
            setCanKeepOpen(true);
            setMessage(`Recebimento confirmado; encerramento pendente. ${asApiError(closed.body).message}`); return;
          }
          const readback = await apiCall<Bill>(`${root}/tabs/${intent.tab}/`);
          if (!readback.response.ok || !readback.body || !("id" in readback.body)
            || readback.body.id !== intent.tab || readback.body.state !== "CLOSED" || readback.body.exposure_cents !== 0)
            throw new Error("Close readback unavailable");
        } else if (detail.body.exposure_cents !== 0) throw new Error("Closed account balance mismatch");
      }
      await onConfirmed(intent.tab);
      if (intent.schema === 2 && intent.close_requested) await onClosed?.(intent.tab);
      clearIntent(intent); intentRef.current = null; setPending(null); setAmount("");
      setPaymentOpen(false); onPaymentSurfaceChange?.(false);
      setMessage(intent.schema === 2 && intent.close_requested ? "Recebimento e encerramento confirmados." : "Recebimento confirmado. Saldo atualizado.");
    } catch {
      if (!attempted && !intentRef.current) {
        setMessage("Não foi possível preparar o recebimento. Verifique a sessão e o armazenamento antes de tentar novamente.");
      } else {
        setMessage(intentRef.current?.schema === 2 && intentRef.current.payment_id
          ? "Recebimento registrado; verificação ou encerramento pendente. Retome a mesma operação sem receber novamente."
          : "Resultado ainda não confirmado. Não receba novamente; verifique este mesmo recebimento.");
      }
    } finally { sending.current = false; setBusy(false); }
  }

  if (ready && !pending && !paymentOpen && (!tab || ["CLOSED", "CANCELLED"].includes(tab.state))) return null;
  if (presentation === "attendance") {
    const terminal = !tab || ["CLOSED", "CANCELLED"].includes(tab.state);
    const normalized = amount.trim().replace(",", ".");
    const full = !!tab && allowCloseAfterReceipt && /^\d+(\.\d{1,2})?$/.test(normalized) && Math.round(Number(normalized)*100) === tab.exposure_cents && positiveInteger(tab.exposure_cents);
    if (ready && !pending && !paymentOpen) return <section aria-label="Recebimento em dinheiro" className="ux2ReceiptEntry">
      {message && <p className="ux2Notice" role="status">{message}</p>}
      <button className="ux2Button primary block" disabled={locked || !positiveInteger(tab?.exposure_cents)} onClick={() => { setAmount(((tab?.exposure_cents??0)/100).toFixed(2).replace(".",",")); setPaymentOpen(true); onPaymentSurfaceChange?.(true); }}>Receber {money(tab?.exposure_cents??0)}</button>
    </section>;
    return <section className="ux2Workspace ux2Payment" aria-label="Recebimento em dinheiro">
      <button className="ux2Back" disabled={busy || !!pending || !ready} onClick={() => {setPaymentOpen(false);onPaymentSurfaceChange?.(false);}}><span aria-hidden="true">‹</span> Voltar</button>
      <div className="ux2Eyebrow">Recebimento manual</div><h1>Receber conta.</h1><p className="ux2Lede">{tab ? `${tab.display_label || "Comanda"} · ${tabReference(tab)} · ${tab.table_label ? `Mesa ${tab.table_label}` : "Sem mesa"}` : "Comanda original"}</p>
      {message && <p className="ux2Notice" role="status">{message}</p>}
      {terminal && !pending && <p className="ux2Notice" role="status">A comanda não está aberta para recebimento. Volte para conferir a conta atualizada.</p>}
      {pending ? <><p className="ux2Notice">Recebimento de {money(pending.payload.amount_cents)} na comanda original.</p>{canKeepOpen && <button className="ux2Button ghost block" disabled={busy} onClick={()=>void collect(false,true)}>Manter comanda aberta</button>}<button className="ux2Button primary block" disabled={busy} onClick={()=>void collect()}>{busy?"Verificando…":"Verificar mesmo recebimento"}</button></> : ready && tab ? <>
        <div className="ux2Settlement"><small>Valor ainda a receber</small><strong>{money(tab.exposure_cents??0)}</strong><small>Pode receber só uma parte</small></div>
        <div className="ux2SectionHead"><h2>Como foi recebido?</h2></div>
        <div className="ux2PaymentMethods" role="group" aria-label="Meio de recebimento"><button type="button" aria-pressed="true">Dinheiro</button><button type="button" aria-label="Pix indisponível" disabled>Pix</button><button type="button" aria-label="Cartão indisponível" disabled>Cartão</button></div>
        <form onSubmit={event=>{event.preventDefault();if(!terminal)void collect(full);}}>
          {!(points.length === 1 && points[0].id === activePoint) && <div className="field"><label htmlFor="attendance-cash-point">Caixa aberto</label><select id="attendance-cash-point" value={activePoint} disabled={busy || locked} onChange={e=>setPointId(e.target.value)}><option value="">Selecionar caixa aberto</option>{points.map(point=><option key={point.id} value={point.id}>{point.label}</option>)}</select></div>}
          <div className="field"><label htmlFor="attendance-cash-amount">Valor recebido (R$)</label><input id="attendance-cash-amount" inputMode="decimal" autoComplete="off" value={amount} disabled={busy || locked} onChange={e=>setAmount(e.target.value)} aria-describedby="attendance-cash-help" /></div>
          <p id="attendance-cash-help" className="ux2PaymentHelp">Informe o valor recebido, sem incluir troco.</p>
          <button type="submit" className="ux2Button primary block" disabled={busy || locked || terminal || !activePoint || !amount}>{busy?"Verificando…":full?"Receber e encerrar comanda":"Registrar recebimento"}</button>
          {full && <button type="button" className="ux2Button ghost block" disabled={busy || locked || !activePoint} onClick={()=>void collect()}>Só registrar; manter comanda aberta</button>}
        </form>{points.length === 1 && points[0].id === activePoint && <p className="ux2PaymentHelp" aria-label="Caixa do recebimento">Caixa: {points[0].label}</p>}<p className="ux2Notice">Registre somente dinheiro efetivamente recebido. O servidor confirma o recebimento antes do encerramento.</p>
      </> : <button className="ux2Button ghost block" onClick={()=>void initialize()}>Verificar armazenamento</button>}
    </section>;
  }
  return <section className="panel" aria-label="Recebimento em dinheiro">
    <OperationalHeading as="h2" icon="wallet">Receber em dinheiro</OperationalHeading>
    {message && <p className="notice" role="status" data-state={pending || !ready ? "warning" : "info"}>{message}</p>}
    {pending ? <>
      <p>Recebimento de {money(pending.payload.amount_cents)} na comanda original.</p>
      {canKeepOpen && <button className="buttonSecondary" disabled={busy} onClick={() => void collect(false, true)}>Manter comanda aberta</button>}
      <button className="buttonPrimary" disabled={busy} onClick={() => void collect()}>{busy ? "Verificando…" : "Verificar mesmo recebimento"}</button>
    </> : ready && tab ? <>
      <p>{tab.display_label || "Comanda selecionada"}</p>
      <div className="field"><label htmlFor="pos-cash-point">Caixa aberto</label><select id="pos-cash-point" value={activePoint} disabled={busy || locked} onChange={e => setPointId(e.target.value)}>
        <option value="">Selecionar caixa aberto</option>{points.map(point => <option key={point.id} value={point.id}>{point.label}</option>)}
      </select></div>
      <div className="field"><label htmlFor="pos-cash-amount">Valor do pagamento</label><input id="pos-cash-amount" inputMode="decimal" value={amount} disabled={busy || locked} onChange={e => setAmount(e.target.value)} placeholder="Valor" /></div>
      <button className="buttonPrimary" disabled={busy || locked || !activePoint || !amount || ["CLOSED", "CANCELLED"].includes(tab.state)} onClick={() => void collect()}>{busy ? "Verificando…" : "Receber em dinheiro"}</button>
    </> : <button className="buttonSecondary" onClick={() => void initialize()}>Verificar armazenamento</button>}
  </section>;
}
