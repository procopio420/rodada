"use client";

import { useEffect, useRef, useState } from "react";
import { guestApi, type GuestApiError } from "./guest-api";

export type GuestScope = { venue_id: string; session_id: string; table_id: string; occupancy_id: string | null; generation: number };
type Line = { product_id: string; quantity: number; variant_id: string | null; modifier_option_ids: string[]; special_instructions: string };
type Intent = { schema: 1; scope: GuestScope; tab: string; captured_at: string; payload: { idempotency_key: string; lines: Line[] } };
type Context = { session_scope?: GuestScope; guest_policy?: { emergency_blocked: boolean }; tab: { id: string; orders?: { id: string }[] } | null };
export const guestOrderStorageKey = (qr: string) => `rodada.intent.guest-order.v1.${qr}`;
const safeRejections = new Set(["TAB_NOT_OPEN", "PRODUCTS_NOT_CONFIRMABLE", "STATION_DISABLED", "SPENDING_LIMIT_EXCEEDED", "MODIFIER_UNAVAILABLE", "VARIANT_UNAVAILABLE", "MODIFIER_REQUIRED", "TOO_MANY_MODIFIERS"]);
export function validScope(s: GuestScope | undefined): s is GuestScope {
  return !!s && [s.venue_id, s.session_id, s.table_id, s.occupancy_id].every(v => typeof v === "string" && !!v)
    && Number.isSafeInteger(s.generation) && s.generation >= 0
    && Object.keys(s).sort().join() === "generation,occupancy_id,session_id,table_id,venue_id";
}
export function sameScope(a: GuestScope, b: GuestScope) {
  return a.venue_id === b.venue_id && a.session_id === b.session_id && a.table_id === b.table_id
    && a.occupancy_id === b.occupancy_id && a.generation === b.generation;
}
function read(key: string): Intent | null {
  const raw = sessionStorage.getItem(key);
  if (raw === null) return null;
  const i = JSON.parse(raw) as Intent;
  if (i?.schema !== 1 || !validScope(i.scope) || typeof i.tab !== "string" || !i.tab
    || !Number.isFinite(Date.parse(i.captured_at)) || Object.keys(i).sort().join() !== "captured_at,payload,schema,scope,tab"
    || !i.payload || Object.keys(i.payload).sort().join() !== "idempotency_key,lines" || typeof i.payload.idempotency_key !== "string" || !i.payload.idempotency_key
    || !Array.isArray(i.payload.lines) || !i.payload.lines.length || !i.payload.lines.every(l => l && typeof l.product_id === "string" && !!l.product_id
      && Number.isSafeInteger(l.quantity) && l.quantity > 0 && (l.variant_id === null || typeof l.variant_id === "string")
      && Array.isArray(l.modifier_option_ids) && l.modifier_option_ids.every(v => typeof v === "string") && typeof l.special_instructions === "string"
      && Object.keys(l).sort().join() === "modifier_option_ids,product_id,quantity,special_instructions,variant_id")) throw new Error("Invalid guest order envelope");
  return i;
}

export function useGuestOrderIntent(qr: string, token: string, onConfirmed: (context: unknown) => void) {
  const key = guestOrderStorageKey(qr);
  const [ready, setReady] = useState(false), [pending, setPending] = useState<Intent | null>(null);
  const [busy, setBusy] = useState(false), [message, setMessage] = useState("");
  const intent = useRef<Intent | null>(null), sending = useRef(false);
  useEffect(() => {
    try {
      const saved = read(key);
      sessionStorage.setItem(`${key}.probe`, "1"); sessionStorage.removeItem(`${key}.probe`);
      intent.current = saved; setPending(saved); setReady(true);
    } catch { setMessage("Não foi possível preservar seu pedido neste navegador. Peça ajuda à equipe antes de enviar."); }
  }, [key]);
  function assertSaved(i: Intent) { if (sessionStorage.getItem(key) !== JSON.stringify(i)) throw new Error("Guest envelope changed"); }
  async function submit(draft?: { tab: string; lines: Line[] }) {
    if (sending.current || !ready || (!intent.current && !draft)) return;
    sending.current = true; setBusy(true); setMessage("");
    const recovering = !!intent.current;
    try {
      const current = await guestApi<Context>("context/", token);
      if (!current.ok || !("tab" in current.body) || !validScope(current.body.session_scope)) {
        setMessage("Não foi possível validar esta visita. O pedido pendente foi preservado; peça ajuda à equipe."); return;
      }
      const context = current.body;
      let i = intent.current;
      if (i && (!sameScope(i.scope, context.session_scope!) || i.tab !== context.tab?.id)) {
        setMessage("Este pedido pertence à visita original. Peça ajuda à equipe; ele não será enviado nesta sessão."); return;
      }
      if (context.guest_policy?.emergency_blocked) { setMessage("Os pedidos por QR estão pausados. Peça ajuda à equipe."); return; }
      if (!i) {
        if (context.tab?.id !== draft!.tab || sessionStorage.getItem(key) !== null) throw new Error("Guest destination changed");
        i = { schema: 1, scope: context.session_scope!, tab: draft!.tab, captured_at: new Date().toISOString(),
          payload: { idempotency_key: crypto.randomUUID(), lines: draft!.lines } };
        sessionStorage.setItem(key, JSON.stringify(i)); intent.current = i; setPending(i);
      }
      assertSaved(i);
      const result = await guestApi<{ id: string; tab_id: string }>("orders/confirm/", token, { method: "POST", body: JSON.stringify(i.payload) });
      if (!result.ok) {
        const error = result.body as GuestApiError;
        if (!recovering && [400, 409].includes(result.status) && safeRejections.has(error.code ?? "")) {
          assertSaved(i); sessionStorage.removeItem(key); intent.current = null; setPending(null);
        }
        setMessage(error.message || "Não foi possível confirmar. Verifique o mesmo pedido ou peça ajuda à equipe."); return;
      }
      if (!("id" in result.body) || !result.body.id || result.body.tab_id !== i.tab) throw new Error("Missing canonical guest order");
      const detail = await guestApi<Context>("context/", token);
      if (!detail.ok || !("tab" in detail.body) || !validScope(detail.body.session_scope) || !sameScope(i.scope, detail.body.session_scope)
        || detail.body.tab?.id !== i.tab || !detail.body.tab.orders?.some(o => o.id === (result.body as { id: string }).id)) throw new Error("Guest readback unavailable");
      assertSaved(i); sessionStorage.removeItem(key); intent.current = null; setPending(null);
      onConfirmed(detail.body); setMessage("Pedido confirmado.");
    } catch {
      setMessage(intent.current ? "Resultado ainda não confirmado. Verifique este mesmo pedido; não envie outro."
        : "Não foi possível preservar seu pedido. Peça ajuda à equipe antes de enviar.");
      if (!intent.current) setReady(false);
    } finally { sending.current = false; setBusy(false); }
  }
  return { ready, pending, busy, message, submit, locked: !ready || !!pending || busy };
}
