"use client";

import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { apiCall, asApiError, type StaffSessionView } from "@/lib/client/staff-auth";
import { useRealtime } from "@/lib/client/use-realtime";
import { ConnectivityNotice } from "./connectivity-notice";

type Mode = "ENFORCE" | "WARN_ONLY";
type Policy = { venue_id: string; mode: Mode; version: number | null; fallback: boolean; updated_at: string | null };
type Command = { mode: Mode; expected_version: number; reason: string; idempotency_key: string; expected_venue_id: string; expected_session_id: string };
const endpoint = "/api/pos/house-account/enforcement/";
const scope = (me: StaffSessionView) => `${me.venue.id}:${me.staff.id}:${me.session.id}`;
const storageKey = (context: string) => `rodada.spending-policy.v1:${context}`;
const modeLabel = (mode: Mode) => mode === "WARN_ONLY" ? "Só alertar" : "Bloquear pedidos";
function canonical(value: unknown): Policy {
  const p = value as Policy;
  if (!p || typeof p.fallback !== "boolean" || typeof p.venue_id !== "string" || !["ENFORCE", "WARN_ONLY"].includes(p.mode) ||
    (p.fallback ? p.mode !== "ENFORCE" || p.version !== null : !Number.isSafeInteger(p.version) || p.version! < 1)) throw new Error("Política canônica indisponível. Atualize antes de continuar.");
  return p;
}
async function read<T>(path: string): Promise<T> {
  const result = await apiCall<T>(path);
  if (!result.response.ok) throw new Error(asApiError(result.body).message);
  return result.body as T;
}
function recover(context: string, me: StaffSessionView): Command | null {
  const raw = sessionStorage.getItem(storageKey(context));
  if (!raw) return null;
  const value = JSON.parse(raw) as Command;
  if (!["ENFORCE", "WARN_ONLY"].includes(value.mode) || !Number.isSafeInteger(value.expected_version) || value.expected_version < 1 ||
    typeof value.reason !== "string" || !value.reason.trim() || value.reason.length > 240 || typeof value.idempotency_key !== "string" || !value.idempotency_key ||
    value.expected_venue_id !== me.venue.id || value.expected_session_id !== me.session.id) throw new Error("Não foi possível recuperar a alteração original. Confira a configuração antes de continuar.");
  return value;
}

export function SpendingLimitSettings() {
  const [me, setMe] = useState<StaffSessionView>();
  const [policy, setPolicy] = useState<Policy>();
  const [editor, setEditor] = useState<{ mode: Mode; version: number; reason: string }>();
  const [pending, setPending] = useState<Command | null>(null);
  const [readable, setReadable] = useState(false);
  const [pin, setPin] = useState("");
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const active = useRef(true), generation = useRef(0), readSequence = useRef(0), context = useRef("");
  const busy = useRef(false), intent = useRef<Command | null>(null);
  useEffect(() => { generation.current++; active.current = true; return () => { active.current = false; }; }, []);
  const load = useCallback(async () => {
    const sequence = ++readSequence.current;
    const [session, value] = await Promise.all([read<StaffSessionView>("/api/auth/me"), read<Policy>(endpoint)]);
    if (!active.current || sequence !== readSequence.current) return;
    const next = canonical(value), key = scope(session);
    if (busy.current && context.current === key) return;
    if (next.venue_id !== session.venue.id) throw new Error("A sessão mudou durante a leitura. Atualize a configuração.");
    if (context.current !== key) {
      generation.current++; context.current = key; busy.current = false;
      setSaving(false); setPin(""); setEditor(undefined); setMessage("");
      intent.current = null; setPending(null);
    }
    setMe(session); setPolicy(next);
    try {
      const original = recover(key, session);
      intent.current = original; setPending(original); setReadable(true);
      if (!original && !next.fallback) setEditor(current => current ?? { mode: next.mode, version: next.version!, reason: "" });
    } catch (error) { setReadable(false); setMessage(error instanceof Error ? error.message : "Armazenamento indisponível."); }
  }, []);
  const connectivity = useRealtime(load, { onRevoked: () => {
    generation.current++; readSequence.current++; context.current = ""; busy.current = false;
    setMe(undefined); setPolicy(undefined); setEditor(undefined); setPending(null); intent.current = null;
    setSaving(false); setReadable(false); setPin(""); setMessage("Entre novamente para conferir a política.");
  } });
  const canEdit = !!me && ["MANAGER", "OWNER"].includes(me.membership.role) && me.capabilities.includes("venue.configure");
  async function save(event: FormEvent) {
    event.preventDefault();
    if (!me || !policy || !canEdit || !readable || busy.current || connectivity.state !== "ONLINE" || (!editor && !intent.current)) return;
    if (!intent.current && !editor!.reason.trim()) { setMessage("Informe um motivo para alterar a política."); return; }
    const originalContext = scope(me), epoch = generation.current;
    const current = () => active.current && epoch === generation.current && context.current === originalContext;
    readSequence.current++; busy.current = true; setSaving(true); setMessage("");
    try {
      const command = intent.current ?? { mode: editor!.mode, expected_version: editor!.version, reason: editor!.reason.trim(),
        idempotency_key: crypto.randomUUID(), expected_venue_id: me.venue.id, expected_session_id: me.session.id };
      sessionStorage.setItem(storageKey(originalContext), JSON.stringify(command));
      intent.current = command; setPending(command);
      const reauth = await apiCall("/api/auth/reauthenticate", { method: "POST", body: JSON.stringify({ pin }) });
      if (!current()) return;
      setPin("");
      if (!reauth.response.ok) throw new Error(asApiError(reauth.body).message);
      const before = await read<StaffSessionView>("/api/auth/me");
      if (!current()) return;
      if (scope(before) !== originalContext) { await load(); throw new Error("A sessão mudou. A intenção original está preservada."); }
      const result = await apiCall<Policy>(endpoint, { method: "PUT", body: JSON.stringify(command) });
      if (!current()) return;
      if (!result.response.ok) {
        const error = asApiError(result.body);
        if (error.code === "POLICY_VERSION_CONFLICT") {
          sessionStorage.removeItem(storageKey(originalContext)); intent.current = null; setPending(null); setEditor(undefined);
          await load();
        } else if (error.code === "ACTOR_CONTEXT_CHANGED") await load();
        throw new Error(error.message);
      }
      const receipt = canonical(result.body);
      if (receipt.venue_id !== command.expected_venue_id || receipt.mode !== command.mode || receipt.version === null ||
          receipt.version < command.expected_version || receipt.version > command.expected_version + 1) throw new Error("Resposta divergente. Verifique a mesma alteração.");
      const [after, latestValue] = await Promise.all([read<StaffSessionView>("/api/auth/me"), read<Policy>(endpoint)]);
      if (!current()) return;
      const latest = canonical(latestValue);
      if (scope(after) !== originalContext || latest.venue_id !== command.expected_venue_id) { await load(); throw new Error("A sessão mudou. Confira a configuração atual."); }
      if (latest.version === null || latest.version < receipt.version) throw new Error("Leitura ainda desatualizada. Verifique a mesma alteração.");
      readSequence.current++;
      sessionStorage.removeItem(storageKey(originalContext)); intent.current = null; setPending(null);
      setPolicy(latest); setEditor({ mode: latest.mode, version: latest.version, reason: "" });
      setMessage(`Alteração confirmada pelo servidor. Em vigor: ${modeLabel(latest.mode)}, versão ${latest.version}.`);
    } catch (error) {
      if (current()) setMessage(error instanceof Error ? error.message : "Resultado não confirmado. Verifique a mesma alteração.");
    } finally { if (current()) { busy.current = false; setSaving(false); setPin(""); void load().catch(() => {}); } }
  }
  return <>
    <ConnectivityNotice {...connectivity} />
    {message && <p className="notice" role="status">{message}</p>}
    {policy && <section className="panel" aria-label="Política de consumo atual"><h2>Em vigor: {modeLabel(policy.mode)}</h2><p>Versão {policy.version ?? "indisponível"}. Alterar este modo não muda o consumo ou os pagamentos já registrados.</p>{policy.fallback && <p role="alert">Política ausente. ENFORCE preservado; solicite manutenção.</p>}</section>}
    {me && !canEdit && <p className="notice">Somente a Gerência autorizada pode alterar esta política.</p>}
    {canEdit && policy && !policy.fallback && (editor || pending) && <form className="panel" aria-label="Alterar política de consumo" onSubmit={event => void save(event)}>
      {pending && <p className="notice" role="status">Alteração ainda em verificação. A mesma chave e o contexto original serão reutilizados.</p>}
      <fieldset disabled={saving || !!pending || !readable}>
        <label className="field"><span>Modo do limite operacional</span><select value={pending?.mode ?? editor!.mode} onChange={event => setEditor({ ...editor!, mode: event.target.value as Mode })}><option value="ENFORCE">Bloquear pedidos</option><option value="WARN_ONLY">Só alertar</option></select></label>
        <p className="muted">Só alertar permite exceder a referência; disponibilidade, autorização, saldo e demais regras continuam validados no servidor. Limite não representa garantia financeira.</p>
        <label className="field"><span>Motivo da alteração</span><input maxLength={240} required value={pending?.reason ?? editor!.reason} onChange={event => setEditor({ ...editor!, reason: event.target.value })} /></label>
      </fieldset>
      <label className="field"><span>Confirme seu PIN</span><input type="password" inputMode="numeric" autoComplete="off" maxLength={12} required disabled={saving || !readable} value={pin} onChange={event => setPin(event.target.value)} /></label>
      <button className="buttonPrimary" type="submit" disabled={saving || !readable || connectivity.state !== "ONLINE"}>{saving ? "Verificando…" : pending ? "Verificar mesma alteração" : "Confirmar alteração da política"}</button>
    </form>}
  </>;
}
