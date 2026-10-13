"use client";
import { useEffect, useRef, useState } from "react";
import { apiCall, type StaffSessionView } from "./staff-auth";
import { parseProductionIntent } from "./production-batch-intent";

type State = "AVAILABLE" | "UNAVAILABLE";
type Draft = { product_id: string; station: "BAR" | "KITCHEN"; state: State; expected_version: number };
export type AvailabilityIntent = { schema: 1; venue: string; staff: string; session: string; captured_at: string;
  product_id: string; station: "BAR" | "KITCHEN"; payload: { state: State; expected_version: number; idempotency_key: string } };
type Receipt = { command_id: string; product_id: string; idempotency_key: string; requested_state: State; expected_version: number;
  state: State; version: number; status: "APPLIED" | "REJECTED"; changed: boolean; conflicts: string[] };
type Journal = Record<string, AvailabilityIntent>;
const key = "rodada.intent.availability.v1";
const fields = (v: object, names: string) => Object.keys(v).sort().join() === names;
const identified = (v: unknown): v is string => typeof v === "string" && v.trim().length > 0;
const versioned = (v: unknown): v is number => Number.isSafeInteger(v) && Number(v) >= 1 && Number(v) <= 2147483647;
const state = (v: unknown) => v === "AVAILABLE" || v === "UNAVAILABLE";
function parse(raw: string): Journal {
  const bag = JSON.parse(raw);
  if (!bag || !fields(bag, "entries,schema") || bag.schema !== 1 || !Array.isArray(bag.entries)) throw new Error("Invalid availability journal");
  const journal: Journal = Object.create(null);
  for (const i of bag.entries) {
    if (!i || !fields(i, "captured_at,payload,product_id,schema,session,staff,station,venue") || i.schema !== 1 ||
        ![i.product_id, i.venue, i.staff, i.session, i.captured_at].every(identified) || !Number.isFinite(Date.parse(i.captured_at)) ||
        !["BAR", "KITCHEN"].includes(i.station) || !i.payload || !fields(i.payload, "expected_version,idempotency_key,state") ||
        !state(i.payload.state) || !versioned(i.payload.expected_version) || !identified(i.payload.idempotency_key) ||
        i.payload.idempotency_key.length > 120 || Object.hasOwn(journal, i.product_id)) throw new Error("Invalid availability intent");
    journal[i.product_id] = i;
  }
  return journal;
}
const encoded = (bag: Journal) => Object.keys(bag).length ? JSON.stringify({ schema: 1, entries: Object.keys(bag).sort().map(id => bag[id]) }) : null;
function matches(r: unknown, i: AvailabilityIntent): r is Receipt {
  if (!r || typeof r !== "object") return false;
  const v = r as Receipt, p = i.payload;
  return identified(v.command_id) && v.product_id === i.product_id && v.idempotency_key === p.idempotency_key &&
    v.requested_state === p.state && v.expected_version === p.expected_version && state(v.state) && versioned(v.version) &&
    typeof v.changed === "boolean" && Array.isArray(v.conflicts) &&
    (v.status === "APPLIED" ? v.state === p.state && v.version === p.expected_version + (v.changed ? 1 : 0) && !v.conflicts.length :
      v.status === "REJECTED" && !v.changed && v.version !== p.expected_version && v.conflicts.length === 1 && v.conflicts[0] === "VERSION_CONFLICT");
}
// Cross-scope commands may coexist, but unresolved journals must belong to this actor.
export function assertAvailabilitySession(s: StaffSessionView) {
  const raw = sessionStorage.getItem(key);
  if (raw !== null && Object.values(parse(raw)).some(i => i.venue !== s.venue.id || i.staff !== s.staff.id || i.session !== s.session.id)) throw new Error("Availability session changed");
}
export function useAvailabilityIntents(station: "BAR" | "KITCHEN", onReadback: () => Promise<void>) {
  const intents = useRef<Journal>(Object.create(null)), sending = useRef(new Set<string>()), usable = useRef(false);
  const [ready, setReady] = useState(false), [pending, setPending] = useState<AvailabilityIntent[]>([]), [busy, setBusy] = useState<string[]>([]);
  const [message, setMessage] = useState(""), [errors, setErrors] = useState<Record<string, string>>({}), [result, setResult] = useState<Receipt | null>(null);
  const publish = () => { setPending(Object.values(intents.current)); setBusy([...sending.current]); };
  function assertStorage() { if (sessionStorage.getItem(key) !== encoded(intents.current)) throw new Error("Availability journal changed"); }
  function save(bag: Journal) {
    const raw = encoded(bag); if (raw === null) sessionStorage.removeItem(key); else sessionStorage.setItem(key, raw);
    if (sessionStorage.getItem(key) !== raw) throw new Error("Availability journal not persisted");
    intents.current = bag; publish();
  }
  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(key); intents.current = raw === null ? Object.create(null) : parse(raw);
      sessionStorage.setItem(`${key}.probe`, "1"); sessionStorage.removeItem(`${key}.probe`); assertStorage();
      usable.current = true; setReady(true); publish();
    } catch { setMessage("Não foi possível preservar a disponibilidade. Solicite revisão antes de continuar."); }
  }, []);
  const valid = () => { try { assertStorage(); return usable.current; } catch { return false; } };
  const anyPending = () => !valid() || sending.current.size > 0 || Object.keys(intents.current).length > 0;
  const locked = (id: string) => !valid() || sending.current.has(id) || Object.hasOwn(intents.current, id);
  async function submit(id: string, draft?: Draft) {
    if (!usable.current || sending.current.has(id) || (!intents.current[id] && !draft)) return;
    if ((intents.current[id]?.station ?? draft?.station) !== station || (draft && draft.product_id !== id)) return;
    sending.current.add(id); publish();
    try {
      const auth = await apiCall<StaffSessionView>("/api/auth/me");
      if (!auth.response.ok || !auth.body || !("session" in auth.body)) throw new Error("Session unavailable");
      const s = auth.body;
      assertStorage(); assertAvailabilitySession(s);
      const batch = sessionStorage.getItem("rodada.intent.production-batch.v1");
      const items = sessionStorage.getItem("rodada.intent.production-items.v1");
      const other = batch === null ? [] : [parseProductionIntent(batch)];
      if (items !== null) {
        const bag = JSON.parse(items);
        if (!bag || !fields(bag, "entries,schema") || bag.schema !== 1 || !Array.isArray(bag.entries)) throw new Error("Invalid item journal");
        other.push(...bag.entries.map((i: unknown) => parseProductionIntent(JSON.stringify(i))));
      }
      if (other.some(i => i.venue !== s.venue.id || i.staff !== s.staff.id || i.session !== s.session.id)) throw new Error("Original session required");
      let intent = intents.current[id];
      if (!intent) {
        intent = { schema: 1, venue: s.venue.id, staff: s.staff.id, session: s.session.id, captured_at: new Date().toISOString(),
          product_id: id, station, payload: { state: draft!.state, expected_version: draft!.expected_version, idempotency_key: crypto.randomUUID() } };
        const bag = { ...intents.current, [id]: intent }; parse(encoded(bag)!); save(bag);
      }
      const response = await apiCall<Receipt>(`/api/pos/catalog/products/${encodeURIComponent(id)}/availability/`, { method: "POST", body: JSON.stringify(intent.payload) });
      if (![200, 409].includes(response.response.status) || !matches(response.body, intent) ||
          (response.response.status === 200) !== (response.body.status === "APPLIED")) throw new Error("Receipt not confirmed");
      await onReadback(); assertStorage();
      const bag = { ...intents.current }; delete bag[id]; save(bag);
      setErrors(previous => { const next = { ...previous }; delete next[id]; return next; }); setResult(response.body);
    } catch {
      // Storage/session failures block every new command; a retry never adopts a new actor.
      try {
        assertStorage();
        setErrors(previous => ({ ...previous, [id]: "Resultado ainda não confirmado. Verifique a mesma disponibilidade e a sessão original." }));
      } catch { usable.current = false; setReady(false); setMessage("Disponibilidade preservada sem confirmação. Confira armazenamento e sessão antes de continuar."); }
      if (!intents.current[id]) { usable.current = false; setReady(false); setMessage("Não foi possível preservar esta disponibilidade. Confira armazenamento e sessão antes de continuar."); }
    } finally { sending.current.delete(id); publish(); }
  }
  return { ready, pending, busy, message, errors, result, anyPending, locked, valid, submit };
}
