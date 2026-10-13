"use client";

import { useEffect, useRef, useState } from "react";
import { apiCall, asApiError, type StaffSessionView } from "./staff-auth";

const storageKey = "rodada.intent.refund.v1";
export type RefundDraft = {
  tab: string; payment: string; correction: string | null;
  amount_cents: number; cash_point_id: string | null; reason: string;
};
type Intent = RefundDraft & { schema: 1; venue: string; staff: string; session: string; captured_at: string; key: string };
const safeInitialRejections = new Set([
  "INVALID_REFUND", "TAB_CLOSED", "PAYMENT_NOT_CONFIRMED", "PROVIDER_REFUND_REQUIRED", "REFUND_EXCEEDS_PAYMENT",
  "REFUND_AMOUNT_MISMATCH", "REFUND_EXCEEDS_ITEM_VALUE", "CORRECTION_REQUIRES_REVIEW", "CORRECTION_STAGE_REQUIRES_APPROVAL",
  "CASH_POINT_REQUIRED", "ACTIVE_CASH_SHIFT_REQUIRED", "CASH_SHIFT_COUNTING", "CASH_SHIFT_CLOSED",
]);
function readIntent(): Intent | null {
  const raw = sessionStorage.getItem(storageKey);
  if (raw === null) return null;
  const i = JSON.parse(raw) as Intent;
  if (i?.schema !== 1 || ![i.venue, i.staff, i.session, i.tab, i.payment, i.captured_at, i.key, i.reason].every(v => typeof v === "string" && !!v)
    || !Number.isFinite(Date.parse(i.captured_at)) || !Number.isSafeInteger(i.amount_cents) || i.amount_cents <= 0 || i.amount_cents > 2147483647
    || !(i.correction === null || typeof i.correction === "string" && !!i.correction)
    || !(i.cash_point_id === null || typeof i.cash_point_id === "string" && !!i.cash_point_id)
    || Object.keys(i).sort().join() !== "amount_cents,captured_at,cash_point_id,correction,key,payment,reason,schema,session,staff,tab,venue")
    throw new Error("Invalid refund envelope");
  return i;
}
function clearIntent(i: Intent) {
  const saved = sessionStorage.getItem(storageKey);
  if (saved !== null && saved !== JSON.stringify(i)) throw new Error("Refund envelope changed");
  sessionStorage.removeItem(storageKey);
}

export function useManualRefundIntent(onConfirmed: (tabId: string) => Promise<void>) {
  const [ready, setReady] = useState(false);
  const [pending, setPending] = useState<Intent | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const intentRef = useRef<Intent | null>(null);
  const sending = useRef(false);
  function initialize() {
    try {
      const saved = readIntent();
      const probe = `${storageKey}.probe`;
      sessionStorage.setItem(probe, "1"); sessionStorage.removeItem(probe);
      intentRef.current = saved; setPending(saved); setReady(true);
      if (saved) setMessage("Há um estorno aguardando confirmação. Verifique a mesma operação antes de devolver novamente.");
    } catch {
      setReady(false); setMessage("Não foi possível preservar o estorno neste navegador. Confira o histórico com a gerência antes de continuar.");
    }
  }
  useEffect(() => { initialize(); }, []);

  async function submit(draft?: RefundDraft) {
    if (sending.current || !ready || (!intentRef.current && !draft)) return;
    sending.current = true; setBusy(true);
    const recovering = !!intentRef.current;
    try {
      const auth = await apiCall<StaffSessionView>("/api/auth/me");
      if (!auth.response.ok || !auth.body || !("session" in auth.body)) {
        setMessage("Confira sua sessão antes de retomar. O estorno pendente foi preservado."); return;
      }
      const s = auth.body;
      let i = intentRef.current;
      if (i && (i.venue !== s.venue.id || i.staff !== s.staff.id || i.session !== s.session.id)) {
        setMessage("Este estorno pertence à sessão original. Solicite revisão à gerência; ele não será enviado nesta sessão."); return;
      }
      if (!i) {
        i = { ...draft!, schema: 1, venue: s.venue.id, staff: s.staff.id, session: s.session.id,
          captured_at: new Date().toISOString(), key: crypto.randomUUID() };
        sessionStorage.setItem(storageKey, JSON.stringify(i));
        intentRef.current = i; setPending(i);
      }
      const path = i.correction ? `/api/pos/corrections/${i.correction}/settle-refund/` : `/api/pos/payments/${i.payment}/refunds/`;
      const body = { amount_cents: i.amount_cents, cash_point_id: i.cash_point_id, originating_session_id: i.session,
        ...(i.correction ? { payment_id: i.payment, refund_idempotency_key: i.key } : { idempotency_key: i.key, reason: i.reason }) };
      const result = await apiCall<{ id: string; status: string; refund_id?: string; refund_status?: string; amount_cents?: number; payment_id?: string }>(path, {
        method: "POST", body: JSON.stringify(body),
      });
      if (!result.response.ok) {
        const error = asApiError(result.body);
        if (!recovering && [400, 409].includes(result.response.status) && safeInitialRejections.has(error.code)) {
          clearIntent(i); intentRef.current = null; setPending(null);
        }
        setMessage(error.code === "REAUTH_REQUIRED" ? "Confirme o PIN de gerente e verifique este mesmo estorno." : error.message); return;
      }
      const canonical = result.body && "id" in result.body ? result.body : null;
      const refundId = i.correction ? canonical?.refund_id : canonical?.id;
      if (!canonical || !refundId || (i.correction
        ? canonical.id !== i.correction || canonical.status !== "APPLIED" || canonical.refund_status !== "CONFIRMED"
        : canonical.status !== "CONFIRMED" || canonical.payment_id !== i.payment || canonical.amount_cents !== i.amount_cents))
        throw new Error("Missing canonical refund");
      const detail = await apiCall<{ payments: { id: string; refunds: { id: string; amount_cents: number; reason: string; status: string }[] }[];
        refund_required_corrections: { id: string }[] }>(`/api/pos/tabs/${i.tab}/`);
      if (!detail.response.ok || !detail.body || !("payments" in detail.body)
        || !detail.body.payments?.find(p => p.id === i.payment)?.refunds?.some(r => r.id === refundId && r.status === "CONFIRMED" && r.amount_cents === i.amount_cents && r.reason === i.reason)
        || (i.correction && (!Array.isArray(detail.body.refund_required_corrections) || detail.body.refund_required_corrections.some(c => c.id === i.correction))))
        throw new Error("Refund readback unavailable");
      await onConfirmed(i.tab);
      clearIntent(i); intentRef.current = null; setPending(null);
      setMessage("Estorno confirmado. O pagamento original foi preservado no histórico.");
    } catch {
      setMessage(intentRef.current ? "Resultado ainda não confirmado. Não devolva novamente; verifique este mesmo estorno."
        : "Não foi possível preparar o estorno. Verifique a sessão e o armazenamento antes de tentar novamente.");
    } finally { sending.current = false; setBusy(false); }
  }
  return { ready, pending, busy, message, submit, initialize, locked: !ready || !!pending || busy };
}
