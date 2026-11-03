"use client";
import { useEffect, useRef, useState } from "react";
import { apiCall, type StaffSessionView } from "./staff-auth";

export type BatchLine = { item_id: string; expected_state: string; quantity: number; snapshot_fingerprint: string };
export type BatchDraft = { station: "BAR" | "KITCHEN"; target_state: "PREPARING" | "READY"; lines: BatchLine[] };
export type Intent = { schema: 1; venue: string; staff: string; session: string; captured_at: string; payload: BatchDraft & { idempotency_key: string } };
export type BatchReceipt = { command_id: string; idempotency_key: string; station: string; target_state: string; status: "APPLIED" | "REJECTED";
  lines: { item_id: string; status: "APPLIED" | "NOT_APPLIED"; state?: string; conflicts: string[] }[] };
const key = "rodada.intent.production-batch.v1";
const fields = (value: object, names: string) => Object.keys(value).sort().join() === names;
const identified = (value: unknown): value is string => typeof value === "string" && !!value;
export function parseProductionIntent(raw: string): Intent {
  const i = JSON.parse(raw) as Intent;
  if (!i || !fields(i, "captured_at,payload,schema,session,staff,venue") || i.schema !== 1 ||
      ![i.venue, i.staff, i.session, i.captured_at].every(identified) || !Number.isFinite(Date.parse(i.captured_at)) ||
      !i.payload || !fields(i.payload, "idempotency_key,lines,station,target_state") ||
      !identified(i.payload.idempotency_key) || i.payload.idempotency_key.length > 120 ||
      !["BAR", "KITCHEN"].includes(i.payload.station) || !["PREPARING", "READY"].includes(i.payload.target_state) ||
      !Array.isArray(i.payload.lines) || !i.payload.lines.length || i.payload.lines.length > 50 ||
      new Set(i.payload.lines.map(line => line?.item_id)).size !== i.payload.lines.length ||
      !i.payload.lines.every(line => line && fields(line, "expected_state,item_id,quantity,snapshot_fingerprint") &&
        identified(line.item_id) && (i.payload.target_state === "READY" ? ["NEW", "ACCEPTED", "PREPARING"].includes(line.expected_state) : ["NEW", "ACCEPTED"].includes(line.expected_state)) &&
        Number.isSafeInteger(line.quantity) && line.quantity > 0 && line.quantity <= 999 &&
        typeof line.snapshot_fingerprint === "string" && /^[a-f0-9]{64}$/.test(line.snapshot_fingerprint))) throw new Error("Invalid batch envelope");
  return i;
}
function read(): Intent | null { const raw = sessionStorage.getItem(key); return raw === null ? null : parseProductionIntent(raw); }
function assertSaved(i: Intent) { if (sessionStorage.getItem(key) !== JSON.stringify(i)) throw new Error("Batch envelope changed"); }
export function receiptMatches(value: unknown, i: Intent): value is BatchReceipt {
  if (!value || typeof value !== "object") return false;
  const r = value as BatchReceipt;
  const ids = i.payload.lines.map(line => line.item_id).sort();
  return identified(r.command_id) && r.idempotency_key === i.payload.idempotency_key && r.station === i.payload.station &&
    r.target_state === i.payload.target_state && ["APPLIED", "REJECTED"].includes(r.status) && Array.isArray(r.lines) &&
    r.lines.length === ids.length && JSON.stringify(r.lines.map(line => line?.item_id).sort()) === JSON.stringify(ids) &&
    r.lines.every(line => line && Array.isArray(line.conflicts) && line.conflicts.every(identified) &&
      (r.status === "APPLIED" ? line.status === "APPLIED" && line.state === r.target_state && !line.conflicts.length : line.status === "NOT_APPLIED")) &&
    (r.status !== "REJECTED" || r.lines.some(line => line.conflicts.length > 0));
}
export function useProductionBatchIntent(station: "BAR" | "KITCHEN", onReadback: () => Promise<void>) {
  const [ready, setReady] = useState(false), [pending, setPending] = useState<Intent | null>(null);
  const [busy, setBusy] = useState(false), [message, setMessage] = useState("");
  const [result, setResult] = useState<BatchReceipt | null>(null);
  const intent = useRef<Intent | null>(null), sending = useRef(false), usable = useRef(false);
  useEffect(() => {
    let active = true;
    queueMicrotask(() => {
      if (!active) return;
    try {
      const saved = read(); sessionStorage.setItem(`${key}.probe`, "1"); sessionStorage.removeItem(`${key}.probe`);
      intent.current = saved; setPending(saved); usable.current = true; setReady(true);
      if (saved) setMessage("Há um lote aguardando confirmação. Verifique o mesmo lote para liberar suas linhas.");
    } catch { setMessage("Não foi possível preservar o lote neste navegador. Solicite revisão antes de continuar."); }
    });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    const timer = window.setInterval(() => {
      if (!usable.current) return;
      try {
        const expected = intent.current ? JSON.stringify(intent.current) : null;
        if (sessionStorage.getItem(key) !== expected) throw new Error("Batch journal changed");
      } catch {
        usable.current = false; setReady(false);
        setMessage("Não foi possível preservar o lote neste navegador. Solicite revisão antes de continuar.");
      }
    }, 15000);
    return () => window.clearInterval(timer);
  }, []);
  const locked = () => !ready || busy || pending !== null;
  const locksItem = (id: string) => !ready || (busy && !pending) || !!pending?.payload.lines.some(line => line.item_id === id);
  async function submit(draft?: BatchDraft) {
    if (sending.current || !usable.current || (!intent.current && !draft)) return;
    if ((intent.current?.payload.station ?? draft?.station) !== station) return;
    sending.current = true; setBusy(true); setResult(null);
    try {
      const auth = await apiCall<StaffSessionView>("/api/auth/me");
      if (!auth.response.ok || !auth.body || !("session" in auth.body)) {
        setMessage(intent.current ? "Confira sua sessão. A pendência foi preservada." : "Não foi possível conferir sua sessão. Nenhum lote foi enviado."); return;
      }
      const s = auth.body; let i = intent.current;
      if (i && (i.venue !== s.venue.id || i.staff !== s.staff.id || i.session !== s.session.id)) {
        setMessage("Este lote pertence à sessão original. Solicite revisão à gerência; ele não será enviado nesta sessão."); return;
      }
      if (!i) {
        if (sessionStorage.getItem(key) !== null) throw new Error("Another batch exists");
        i = { schema: 1, venue: s.venue.id, staff: s.staff.id, session: s.session.id, captured_at: new Date().toISOString(),
          payload: { ...draft!, lines: draft!.lines.map(line => ({ ...line })), idempotency_key: crypto.randomUUID() } };
        sessionStorage.setItem(key, JSON.stringify(i)); intent.current = i; setPending(i);
      }
      assertSaved(i);
      const response = await apiCall<BatchReceipt>("/api/pos/production/batches/", { method: "POST", body: JSON.stringify(i.payload) });
      if (![200, 409].includes(response.response.status) || !receiptMatches(response.body, i) ||
          (response.response.status === 200) !== (response.body.status === "APPLIED")) throw new Error("Batch result not confirmed");
      await onReadback();
      assertSaved(i); sessionStorage.removeItem(key); intent.current = null; setPending(null);
      setResult(response.body); setMessage("");
    } catch {
      setMessage(intent.current ? "Resultado ainda não confirmado. Verifique este mesmo lote; as linhas selecionadas continuam bloqueadas."
        : "Não foi possível preparar o lote. Confira a sessão e o armazenamento antes de continuar.");
      if (!intent.current) { usable.current = false; setReady(false); }
    } finally { sending.current = false; setBusy(false); }
  }
  return { ready, pending, busy, message, result, locked, locksItem, submit };
}
