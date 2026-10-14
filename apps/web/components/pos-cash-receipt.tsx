"use client";

import { useEffect, useRef, useState } from "react";
import { OperationalHeading } from "@/components/operational-heading";
import { apiCall, asApiError, type StaffSessionView } from "@/lib/client/staff-auth";

const storageKey = "rodada.intent.pos-cash.v1";
type Tab = { id: string; display_label: string; version: number; state: string };
type CashPoint = { id: string; label: string };
type Intent = {
  schema: 1; venue: string; staff: string; session: string; tab: string; captured_at: string;
  payload: { amount_cents: number; expected_version: number; method: "CASH"; cash_point_id: string; idempotency_key: string; originating_session_id: string };
};
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
  if (intent?.schema !== 1 || !p || ![intent.venue, intent.staff, intent.session, intent.tab, intent.captured_at, p.cash_point_id, p.idempotency_key].every(v => typeof v === "string" && !!v)
    || !Number.isFinite(Date.parse(intent.captured_at)) || !positiveInteger(p.amount_cents) || !positiveInteger(p.expected_version)
    || p.method !== "CASH" || p.originating_session_id !== intent.session
    || Object.keys(intent).sort().join() !== "captured_at,payload,schema,session,staff,tab,venue"
    || Object.keys(p).sort().join() !== "amount_cents,cash_point_id,expected_version,idempotency_key,method,originating_session_id")
    throw new Error("Invalid cash receipt envelope");
  return intent;
}

function clearIntent(intent: Intent) {
  const saved = sessionStorage.getItem(storageKey);
  if (saved !== null && saved !== JSON.stringify(intent)) throw new Error("Receipt envelope changed");
  sessionStorage.removeItem(storageKey);
}

export function PosCashReceipt({ tab, points, locked, onPendingChange, onConfirmed }: {
  tab: Tab | null; points: CashPoint[]; locked: boolean;
  onPendingChange: (pending: boolean) => void; onConfirmed: (tabId: string) => Promise<void>;
}) {
  const [amount, setAmount] = useState("");
  const [pointId, setPointId] = useState("");
  const [ready, setReady] = useState(false);
  const [pending, setPending] = useState<Intent | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const intentRef = useRef<Intent | null>(null);
  const sending = useRef(false);

  async function initialize() {
    try {
      // Probe writes too: a readable store may still refuse persistence.
      const saved = readIntent();
      const probe = `${storageKey}.probe`;
      sessionStorage.setItem(probe, "1"); sessionStorage.removeItem(probe);
      intentRef.current = saved; setPending(saved); setReady(true);
      if (saved) setMessage("Há um recebimento aguardando confirmação. Verifique a mesma operação antes de receber novamente.");
    } catch {
      setReady(false);
      setMessage("Não foi possível preservar o recebimento neste navegador. Confira o histórico com a gerência antes de continuar.");
    }
  }
  useEffect(() => { queueMicrotask(() => void initialize()); }, []);
  useEffect(() => { onPendingChange(!ready || !!pending || busy); }, [ready, pending, busy, onPendingChange]);

  const activePoint = pointId || points[0]?.id || "";
  async function collect() {
    if (sending.current || !ready || (!intentRef.current && locked)) return;
    sending.current = true; setBusy(true);
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
        const normalized = amount.trim().replace(",", ".");
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
        // Persistence must succeed before any money-changing request.
        sessionStorage.setItem(storageKey, JSON.stringify(intent));
        intentRef.current = intent; setPending(intent);
      }
      attempted = true;
      const result = await apiCall<{ id: string; status: string }>(`/api/pos/tabs/${intent.tab}/payments/`, {
        method: "POST", body: JSON.stringify(intent.payload),
      });
      if (!result.response.ok) {
        const error = asApiError(result.body);
        // Never abandon an ambiguous or conflicting identity on a subsequent rejection.
        if (!recovering && [400, 409].includes(result.response.status) && safeInitialRejections.has(error.code)) {
          clearIntent(intent); intentRef.current = null; setPending(null);
        }
        setMessage(error.message); return;
      }
      const settledStatuses = ["CONFIRMED", "PARTIALLY_REFUNDED", "REFUNDED"];
      if (!result.body || !("id" in result.body) || !result.body.id || !settledStatuses.includes(result.body.status))
        throw new Error("Missing canonical payment");
      const paymentId = result.body.id;
      const detail = await apiCall<{ payments: { id: string; method: string; amount_cents: number; status: string }[] }>(`/api/pos/tabs/${intent.tab}/`);
      if (!detail.response.ok || !detail.body || !("payments" in detail.body)
        || !detail.body.payments?.some(p => p.id === paymentId && p.method === "CASH" && p.amount_cents === intent.payload.amount_cents && settledStatuses.includes(p.status)))
        throw new Error("Receipt readback unavailable");
      await onConfirmed(intent.tab);
      clearIntent(intent); intentRef.current = null; setPending(null); setAmount("");
      setMessage("Recebimento confirmado. Saldo atualizado.");
    } catch {
      if (!attempted && !intentRef.current) {
        setMessage("Não foi possível preparar o recebimento. Verifique a sessão e o armazenamento antes de tentar novamente.");
      } else {
        setMessage("Resultado ainda não confirmado. Não receba novamente; verifique este mesmo recebimento.");
      }
    } finally { sending.current = false; setBusy(false); }
  }

  if (!tab && !pending && ready) return null;
  return <section className="panel" aria-label="Recebimento em dinheiro">
    <OperationalHeading as="h2" icon="wallet">Receber em dinheiro</OperationalHeading>
    {message && <p className="notice" role="status" data-state={pending || !ready ? "warning" : "info"}>{message}</p>}
    {pending ? <>
      <p>Recebimento de {money(pending.payload.amount_cents)} na comanda original.</p>
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
