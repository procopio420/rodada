"use client";
import { useEffect, useRef, useState } from "react";
import { apiCall, type StaffSessionView } from "./staff-auth";
import { assertAvailabilitySession } from "./availability-intents";
import { parseProductionIntent, receiptMatches, type Intent, type BatchDraft, type BatchReceipt } from "./production-batch-intent";
const key = "rodada.intent.production-items.v1";
type Intents = Record<string, Intent>;
const encoded = (intents: Intents) => Object.keys(intents).length ? JSON.stringify({ schema: 1, entries: Object.keys(intents).sort().map(id => intents[id]) }) : null;
function read(): Intents {
  const raw = sessionStorage.getItem(key); if (raw === null) return {};
  const bag = JSON.parse(raw); const result: Intents = {};
  if (!bag || bag.schema !== 1 || Object.keys(bag).sort().join() !== "entries,schema" || !Array.isArray(bag.entries)) throw new Error("Invalid item journal");
  for (const value of bag.entries) {
    const intent = parseProductionIntent(JSON.stringify(value));
    if (intent.payload.lines.length !== 1) throw new Error("Expected one item");
    const id = intent.payload.lines[0].item_id;
    if (Object.hasOwn(result, id)) throw new Error("Duplicate item intent");
    Object.defineProperty(result, id, { value: intent, enumerable: true, writable: true, configurable: true });
  }
  return result;
}
export function useProductionItemIntents(station: "BAR" | "KITCHEN", onReadback: () => Promise<void>) {
  const intents = useRef<Intents>({}), sending = useRef(new Set<string>()), usable = useRef(false);
  const [ready, setReady] = useState(false), [pending, setPending] = useState<Intent[]>([]), [busy, setBusy] = useState<string[]>([]);
  const [message, setMessage] = useState(""), [errors, setErrors] = useState<Record<string, string>>({});
  const [result, setResult] = useState<BatchReceipt | null>(null);
  const publish = () => { setPending(Object.values(intents.current)); setBusy([...sending.current]); };
  function assertStorage() { if (sessionStorage.getItem(key) !== encoded(intents.current)) throw new Error("Item journal changed"); }
  function save(next: Intents) {
    const raw = encoded(next); if (raw === null) sessionStorage.removeItem(key); else sessionStorage.setItem(key, raw);
    if (sessionStorage.getItem(key) !== raw) throw new Error("Item journal not persisted");
    intents.current = next; publish();
  }
  useEffect(() => {
    try {
      intents.current = read(); sessionStorage.setItem(`${key}.probe`, "1"); sessionStorage.removeItem(`${key}.probe`);
      // Refuse noncanonical storage rather than rewriting an unresolved intent.
      assertStorage(); usable.current = true; setReady(true); publish();
    } catch { setMessage("Não foi possível preservar as ações de produção. Solicite revisão antes de continuar."); }
  }, []);
  const anyPending = () => !usable.current || sending.current.size > 0 || Object.keys(intents.current).length > 0;
  const locked = (id: string) => !usable.current || sending.current.has(id) || Object.hasOwn(intents.current, id);
  async function submit(id: string, draft?: BatchDraft) {
    if (!usable.current || sending.current.has(id)) return;
    const original = intents.current[id];
    if (!original && (!draft || draft.lines.length !== 1 || draft.lines[0].item_id !== id)) return;
    if ((original?.payload.station ?? draft?.station) !== station) return;
    sending.current.add(id); publish();
    try {
      const auth = await apiCall<StaffSessionView>("/api/auth/me");
      if (!auth.response.ok || !auth.body || !("session" in auth.body)) { setMessage("Confira sua sessão. As intenções de produção foram preservadas."); return; }
      const s = auth.body;
      assertAvailabilitySession(s);
      const batchRaw = sessionStorage.getItem("rodada.intent.production-batch.v1");
      if (batchRaw !== null) {
        const batch = parseProductionIntent(batchRaw);
        if (batch.venue !== s.venue.id || batch.staff !== s.staff.id || batch.session !== s.session.id) {
          setMessage("O lote pendente pertence à sessão original. Solicite revisão antes de enviar outro item."); return;
        }
        if (batch.payload.lines.some(line => line.item_id === id)) return;
      }
      if (Object.values(intents.current).some(i => i.venue !== s.venue.id || i.staff !== s.staff.id || i.session !== s.session.id)) {
        setMessage("As ações pendentes pertencem à sessão original. Solicite revisão; não serão adotadas nesta sessão."); return;
      }
      assertStorage(); let intent = intents.current[id];
      if (!intent) {
        intent = { schema: 1, venue: s.venue.id, staff: s.staff.id, session: s.session.id, captured_at: new Date().toISOString(),
          payload: { ...draft!, lines: draft!.lines.map(line => ({ ...line })), idempotency_key: crypto.randomUUID() } };
        parseProductionIntent(JSON.stringify(intent)); save({ ...intents.current, [id]: intent });
      }
      const response = await apiCall<BatchReceipt>("/api/pos/production/batches/", { method: "POST", body: JSON.stringify(intent.payload) });
      if (![200, 409].includes(response.response.status) || !receiptMatches(response.body, intent) ||
          (response.response.status === 200) !== (response.body.status === "APPLIED")) throw new Error("Item not confirmed");
      await onReadback(); assertStorage();
      const next = { ...intents.current }; delete next[id]; save(next);
      setErrors(previous => { const next = { ...previous }; delete next[id]; return next; });
      setResult(response.body); setMessage("");
    } catch {
      if (intents.current[id]) setErrors(previous => ({ ...previous, [id]: "Resultado ainda não confirmado. Verifique este mesmo item." }));
      else { usable.current = false; setReady(false); setMessage("Não foi possível preservar esta ação. Confira armazenamento e sessão antes de continuar."); }
    } finally { sending.current.delete(id); publish(); }
  }
  return { ready, pending, busy, message, errors, result, anyPending, locked, submit };
}
