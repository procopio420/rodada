"use client";

import { useEffect, useRef, useState } from "react";
import { apiCall, asApiError, type StaffSessionView } from "./staff-auth";

const storageKey = "rodada.intent.staff-order.v1";
type Line = { product_id: string; quantity: number; variant_id: string | null; modifier_option_ids: string[]; special_instructions: string };
type Intent = { schema: 1; api_root: "/api/attendance" | "/api/pos"; venue: string; staff: string; session: string; tab: string; captured_at: string;
  payload: { idempotency_key: string; lines: Line[] } };
const initialRejections = new Set(["EMPTY_ORDER", "INVALID_ORDER_LINE", "TAB_NOT_OPEN", "PRODUCTS_NOT_CONFIRMABLE", "STATION_DISABLED", "SPENDING_LIMIT_EXCEEDED"]);
function readIntent(): Intent | null {
  const raw = sessionStorage.getItem(storageKey);
  if (raw === null) return null;
  const i = JSON.parse(raw) as Intent;
  if (i?.schema !== 1 || ![i.venue, i.staff, i.session, i.tab, i.captured_at, i.payload?.idempotency_key].every(v => typeof v === "string" && !!v)
    || !Number.isFinite(Date.parse(i.captured_at)) || !["/api/attendance", "/api/pos"].includes(i.api_root) || Object.keys(i).sort().join() !== "api_root,captured_at,payload,schema,session,staff,tab,venue"
    || Object.keys(i.payload).sort().join() !== "idempotency_key,lines" || !Array.isArray(i.payload.lines) || !i.payload.lines.length
    || !i.payload.lines.every(l => l && typeof l.product_id === "string" && !!l.product_id && Number.isSafeInteger(l.quantity) && l.quantity > 0
      && (l.variant_id === null || typeof l.variant_id === "string") && Array.isArray(l.modifier_option_ids)
      && l.modifier_option_ids.every(v => typeof v === "string") && typeof l.special_instructions === "string"
      && Object.keys(l).sort().join() === "modifier_option_ids,product_id,quantity,special_instructions,variant_id"))
    throw new Error("Invalid order envelope");
  return i;
}
function assertSaved(i: Intent) {
  if (sessionStorage.getItem(storageKey) !== JSON.stringify(i)) throw new Error("Order envelope changed");
}

export function useOrderIntent(onConfirmed: (tab: string, order: string) => Promise<() => void>) {
  const [ready, setReady] = useState(false), [pending, setPending] = useState<Intent | null>(null);
  const [busy, setBusy] = useState(false), [message, setMessage] = useState("");
  const intentRef = useRef<Intent | null>(null), sending = useRef(false);
  useEffect(() => {
    try {
      const saved = readIntent();
      sessionStorage.setItem(`${storageKey}.probe`, "1"); sessionStorage.removeItem(`${storageKey}.probe`);
      intentRef.current = saved; setPending(saved); setReady(true);
      if (saved) setMessage("Há um pedido aguardando confirmação. Verifique o mesmo pedido antes de enviar outro.");
    } catch { setMessage("Não foi possível preservar o pedido neste navegador. Confira o histórico antes de continuar."); }
  }, []);
  async function submit(draft?: { tab: string; lines: Line[] }, apiRoot: "/api/attendance" | "/api/pos" = "/api/pos") {
    if (sending.current || !ready || (!intentRef.current && !draft)) return;
    sending.current = true; setBusy(true);
    const recovering = !!intentRef.current;
    try {
      const auth = await apiCall<StaffSessionView>("/api/auth/me");
      if (!auth.response.ok || !auth.body || !("session" in auth.body)) {
        setMessage("Confira sua sessão antes de retomar. O pedido pendente foi preservado."); return;
      }
      const s = auth.body;
      let i = intentRef.current;
      if (i && (i.venue !== s.venue.id || i.staff !== s.staff.id || i.session !== s.session.id)) {
        setMessage("Este pedido pertence à sessão original. Solicite revisão à gerência; ele não será enviado nesta sessão."); return;
      }
      if (!i) {
        if (sessionStorage.getItem(storageKey) !== null) throw new Error("Another order envelope exists");
        i = { schema: 1, api_root: apiRoot, venue: s.venue.id, staff: s.staff.id, session: s.session.id, tab: draft!.tab,
          captured_at: new Date().toISOString(), payload: { idempotency_key: crypto.randomUUID(), lines: draft!.lines } };
        sessionStorage.setItem(storageKey, JSON.stringify(i));
        intentRef.current = i; setPending(i);
      }
      assertSaved(i);
      const result = await apiCall<{ id: string; tab_id: string }>(`${i.api_root}/tabs/${i.tab}/orders/confirm/`, { method: "POST", body: JSON.stringify(i.payload) });
      if (!result.response.ok) {
        const error = asApiError(result.body);
        if (!recovering && [400, 409].includes(result.response.status) && initialRejections.has(error.code)) {
          assertSaved(i); sessionStorage.removeItem(storageKey); intentRef.current = null; setPending(null);
        }
        setMessage(error.message); return;
      }
      if (!result.body || !("id" in result.body) || !result.body.id || result.body.tab_id !== i.tab) throw new Error("Missing canonical order");
      const applyConfirmed = await onConfirmed(i.tab, result.body.id);
      assertSaved(i); sessionStorage.removeItem(storageKey); intentRef.current = null; setPending(null);
      applyConfirmed(); setMessage("");
    } catch {
      setMessage(intentRef.current ? "Resultado ainda não confirmado. Verifique este mesmo pedido; não envie outro."
        : "Não foi possível preparar o pedido. Verifique a sessão e o armazenamento antes de continuar.");
      if (!intentRef.current) setReady(false);
    } finally { sending.current = false; setBusy(false); }
  }
  return { ready, pending, busy, message, submit };
}
