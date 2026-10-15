"use client";

import { useEffect, useRef, useState } from "react";
import { ActionDialog } from "@/components/action-dialog";
import { apiCall, asApiError, type StaffSessionView } from "@/lib/client/staff-auth";

export type MoveTable = { id: string; label: string; status: string; active_occupancy?: { id: string; tabs?: { id: string; display_label: string }[] } };
export type MoveSelection = { tab: { id: string; display_label: string }; table: MoveTable };
type Payload = { kind: "MOVE_LOCATION"; expected_version: number; occupancy_id?: string; table_id?: string; reason: string; idempotency_key: string };
type Intent = { schema: 1; venue: string; staff: string; session: string; tab: string; label: string; origin: string; destination: string; payload: Payload };
const key = "rodada.intent.tab-location.v1";
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const rejections = new Set(["VERSION_CONFLICT", "TAB_NOT_OPEN", "OCCUPANCY_NOT_ACTIVE", "TAB_NOT_FOUND", "CAPABILITY_REQUIRED", "INVALID_LOCATION"]);
function readIntent(): Intent | null {
  const raw = sessionStorage.getItem(key);
  if (raw === null) return null;
  const i = JSON.parse(raw) as Intent;
  if (!i || i.schema !== 1 || Object.keys(i).sort().join() !== "destination,label,origin,payload,schema,session,staff,tab,venue"
    || ![i.venue, i.staff, i.session, i.tab, i.label, i.origin, i.destination].every(v => typeof v === "string" && !!v)
    || !uuid.test(i.tab) || !i.payload || !["expected_version,idempotency_key,kind,occupancy_id,reason", "expected_version,idempotency_key,kind,reason,table_id"].includes(Object.keys(i.payload).sort().join())
    || i.payload.kind !== "MOVE_LOCATION" || !Number.isSafeInteger(i.payload.expected_version) || i.payload.expected_version < 1
    || !uuid.test(i.payload.occupancy_id || i.payload.table_id || "") || !uuid.test(i.payload.idempotency_key)
    || typeof i.payload.reason !== "string" || i.payload.reason.length > 240) throw new Error("Invalid location intent");
  return i;
}

export function TabLocationMove({ selection, tables, onClose, onLockChange, onConfirmed }: {
  selection: MoveSelection | null; tables: MoveTable[]; onClose: () => void;
  onLockChange: (locked: boolean) => void; onConfirmed: () => Promise<void>;
}) {
  const [ready, setReady] = useState(false), [pending, setPending] = useState<Intent | null>(null);
  const [version, setVersion] = useState<number | null>(null), [destination, setDestination] = useState("");
  const [reason, setReason] = useState(""), [busy, setBusy] = useState(false), [message, setMessage] = useState("");
  const intent = useRef<Intent | null>(null), sending = useRef(false), status = useRef<HTMLParagraphElement>(null);
  useEffect(() => { if (message.startsWith("Movimento confirmado.")) status.current?.focus(); }, [message]);
  useEffect(() => {
    let active = true;
    queueMicrotask(() => {
      if (!active) return;
    try {
      const saved = readIntent(); sessionStorage.setItem(`${key}.probe`, "1"); sessionStorage.removeItem(`${key}.probe`);
      intent.current = saved; setPending(saved); setReady(true);
      if (saved) setMessage("Movimento aguardando confirmação. Verifique a mesma operação.");
    } catch { setMessage("Não foi possível preservar o movimento neste navegador. Solicite revisão antes de continuar."); }
    });
    return () => { active = false; };
  }, []);
  useEffect(() => { onLockChange(!ready || !!pending || !!selection || busy); }, [ready, pending, selection, busy, onLockChange]);
  useEffect(() => {
    if (!selection || intent.current) return;
    let current = true; setVersion(null); setDestination(""); setReason(""); setMessage("");
    const query = new URLSearchParams({ table_id: selection.table.id, occupancy_id: selection.table.active_occupancy!.id });
    void apiCall<{ id: string; version: number }>(`/api/attendance/tabs/${selection.tab.id}/?${query}`).then(result => {
      if (!current) return;
      if (!result.response.ok) { setMessage(asApiError(result.body).message); return; }
      if (result.body && "id" in result.body && result.body.id === selection.tab.id && Number.isSafeInteger(result.body.version) && result.body.version > 0) setVersion(result.body.version);
      else setMessage("Não foi possível conferir a comanda. Volte e atualize as mesas.");
    }).catch(() => { if (current) setMessage("Não foi possível conferir a origem. Volte e atualize as mesas."); });
    return () => { current = false; };
  }, [selection]);

  async function submit() {
    if (!ready || sending.current || (!intent.current && (!selection || !version || !destination))) return;
    sending.current = true; setBusy(true); setMessage(""); const recovering = !!intent.current;
    try {
      const auth = await apiCall<StaffSessionView>("/api/auth/me");
      if (!auth.response.ok || !auth.body || !("session" in auth.body)) throw new Error("Session unavailable");
      const s = auth.body; let i = intent.current;
      if (i && (i.venue !== s.venue.id || i.staff !== s.staff.id || i.session !== s.session.id)) {
        setMessage("Este movimento pertence à sessão original. Solicite revisão à gerência."); return;
      }
      if (!s.capabilities.includes("tab.move")) { setMessage("Seu perfil não pode mover comandas. A intenção foi preservada."); return; }
      if (!i) {
        const target = tables.find(t => (t.status === "AVAILABLE" ? t.id : t.active_occupancy?.id) === destination && ["AVAILABLE", "OCCUPIED"].includes(t.status) && t.id !== selection!.table.id);
        if (!target) { setMessage("Destino mudou. Escolha outra mesa."); return; }
        if (sessionStorage.getItem(key) !== null) throw new Error("Another intent exists");
        i = { schema: 1, venue: s.venue.id, staff: s.staff.id, session: s.session.id, tab: selection!.tab.id,
          label: selection!.tab.display_label || "Sem nome", origin: selection!.table.label, destination: target.label,
          payload: { kind: "MOVE_LOCATION", expected_version: version!, ...(target.status === "AVAILABLE" ? { table_id: target.id } : { occupancy_id: destination }), reason: reason.trim(), idempotency_key: crypto.randomUUID() } };
        sessionStorage.setItem(key, JSON.stringify(i)); intent.current = i; setPending(i);
      }
      const assertSaved = () => { if (sessionStorage.getItem(key) !== JSON.stringify(i)) throw new Error("Intent changed"); };
      assertSaved();
      const result = await apiCall<{ operation_id: string; source: { id: string; occupancy_id: string; version: number } }>(`/api/attendance/tabs/${i.tab}/operations/`, { method: "POST", body: JSON.stringify(i.payload) });
      if (!result.response.ok) {
        const error = asApiError(result.body);
        if (!recovering && [400,403,404,409].includes(result.response.status) && rejections.has(error.code)) {
          assertSaved(); sessionStorage.removeItem(key); intent.current = null; setPending(null); setVersion(null);
        }
        setMessage(error.message); return;
      }
      const body = result.body;
      if (!body || !("operation_id" in body) || !uuid.test(body.operation_id) || body.source?.id !== i.tab
        || (i.payload.occupancy_id ? body.source.occupancy_id !== i.payload.occupancy_id : (body.source.occupancy_id !== null && !uuid.test(body.source.occupancy_id))) || body.source.version !== i.payload.expected_version + 1) throw new Error("Invalid operation response");
      const [tab, locations] = await Promise.all([
        apiCall<{ id: string; version: number }>(`/api/attendance/tabs/${i.tab}/`),
        apiCall<{ results: MoveTable[] }>("/api/attendance/hospitality/tables/"),
      ]);
      if (!tab.response.ok || !tab.body || !("id" in tab.body) || tab.body.id !== i.tab || !Number.isSafeInteger(tab.body.version) || tab.body.version < body.source.version
        || !locations.response.ok || !locations.body || !("results" in locations.body) || !Array.isArray(locations.body.results)) throw new Error("Readback unavailable");
      const current = locations.body.results.find(t => t.active_occupancy?.tabs?.some(t => t.id === i!.tab));
      assertSaved(); sessionStorage.removeItem(key); intent.current = null; setPending(null); onClose();
      if (i.payload.table_id && body.source.occupancy_id === null) {
        setMessage("A versão anterior da API deixou a comanda sem mesa. Operação conferida; selecione novamente a comanda em Contas para vinculá-la à mesa desejada.");
        await onConfirmed();
        return;
      }
      setMessage(`Movimento confirmado. Local atual: ${current ? `mesa ${current.label}` : "sem mesa ativa"}.`);
      await onConfirmed();
    } catch {
      setMessage(intent.current ? "Resultado ainda não confirmado. Verifique o mesmo movimento; não envie outro."
        : "Não foi possível preparar o movimento. Confira a sessão e o armazenamento.");
      if (!intent.current) setReady(false);
    } finally { sending.current = false; setBusy(false); }
  }
  const active = pending || selection;
  const targets = tables.filter(t => (t.status === "AVAILABLE" || (t.status === "OCCUPIED" && t.active_occupancy)) && t.id !== selection?.table.id);
  return <>
    {!active && message && <p ref={status} tabIndex={-1} className="notice" data-state={ready ? "info" : "warning"} role={ready ? "status" : "alert"}>{message}</p>}
    {active && <ActionDialog title="Mover comanda" locked={busy || !!pending} onClose={onClose}>
      <p className="attendanceTabTitle">{pending?.label || selection?.tab.display_label || "Sem nome"} · ID {pending?.tab || selection?.tab.id}</p>
      <p>Origem: mesa {pending?.origin || selection?.table.label}.</p>
      <p>Consumo e pagamentos continuam na mesma comanda. A mesa de origem permanece ocupada.</p>
      {message && <p className="notice" data-state="warning" role="alert">{message}</p>}
      {pending ? <><p>Destino confirmado: mesa {pending.destination}.</p><button className="buttonPrimary" disabled={busy} onClick={() => void submit()}>{busy ? "Verificando…" : "Verificar mesmo movimento"}</button></>
        : <><div className="field"><label htmlFor="move-destination">Mesa de destino</label><select id="move-destination" value={destination} disabled={busy || !version} onChange={e => setDestination(e.target.value)}><option value="">Escolha outra mesa</option>{targets.map(t => <option key={t.id} value={t.status === "AVAILABLE" ? t.id : t.active_occupancy!.id}>Mesa {t.label} · {t.status === "AVAILABLE" ? "Disponível" : "Em uso"}</option>)}</select></div>
          <div className="field"><label htmlFor="move-reason">Motivo (opcional)</label><input id="move-reason" maxLength={240} value={reason} disabled={busy} onChange={event => setReason(event.target.value)} /></div>
          {!targets.length && <p>Nenhuma outra mesa disponível para receber a comanda.</p>}
          {destination && <p>Confirmar: mesa {selection!.table.label} → mesa {targets.find(t => (t.status === "AVAILABLE" ? t.id : t.active_occupancy?.id) === destination)?.label || "indisponível"}.</p>}
          <button className="buttonPrimary" disabled={!ready || busy || !version || !destination} onClick={() => void submit()}>Confirmar movimento</button></>}
    </ActionDialog>}
  </>;
}
