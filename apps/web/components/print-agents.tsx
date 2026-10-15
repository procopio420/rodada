"use client";

import { useCallback, useEffect, useState } from "react";
import { apiCall, asApiError } from "@/lib/client/staff-auth";
import { OperationalHeading } from "@/components/operational-heading";

type Agent = { id: string; installation_id: string; label: string; state: string; version: string; last_seen_at: string | null };
type Agents = { enabled: boolean; results: Agent[] };
type Inspection = { installation_id: string; label: string; venue_id: string; venue_name: string };
const prefix = "/api/pos/printing/agents/v1/";
const labels: Record<string, string> = { ONLINE: "Conectado", STALE: "Sem atualização recente", OFFLINE: "Desconectado", REVOKED: "Revogado" };

export function PrintAgents() {
  const [data, setData] = useState<Agents | null>(null);
  const [code, setCode] = useState("");
  const [inspection, setInspection] = useState<Inspection | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [revoking, setRevoking] = useState<Agent | null>(null);
  const [reason, setReason] = useState("");
  const load = useCallback(async () => {
    const result = await apiCall<Agents>(prefix);
    if (!result.response.ok) throw new Error(asApiError(result.body).message);
    const next = result.body as Agents;
    setData(next);
    return next;
  }, []);
  useEffect(() => {
    const refresh = () => { void load().catch(() => setError("Não foi possível atualizar os computadores.")); };
    refresh();
    const timer = window.setInterval(refresh, 10000);
    return () => window.clearInterval(timer);
  }, [load]);

  async function action(path: string, body: object) {
    if (busy) return null;
    setBusy(true); setError(""); setMessage("");
    try {
      const result = await apiCall(prefix + path, { method: "POST", body: JSON.stringify(body) });
      if (!result.response.ok) throw new Error(asApiError(result.body).message);
      await load();
      return result.body;
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Resultado indisponível. Confira os computadores antes de tentar novamente.");
      return null;
    } finally { setBusy(false); }
  }
  async function inspect() {
    const result = await action("pairing/inspect/", { code });
    if (result) setInspection(result as Inspection);
  }
  async function approve() {
    if (!inspection) return;
    const result = await action("pairing/approve/", { code, installation_id: inspection.installation_id });
    if (result) { setCode(""); setInspection(null); setMessage("Computador autorizado. A ativação será concluída no computador."); }
  }
  return <section className="panel" aria-label="Computadores de impressão">
    <OperationalHeading as="h2" icon="printer">Computadores de impressão</OperationalHeading>
    <p className="muted">Instale o Rodada Impressoras no computador e autorize o código abaixo. Não informe seu PIN no computador.</p>
    {message && <p className="notice" role="status">{message}</p>}
    {error && <p className="notice" data-state="danger" role="alert">{error}</p>}
    {!data && !error && <p role="status">Carregando computadores…</p>}
    {data && <>
      {!data.enabled ? <><p>Integração com computadores desativada neste estabelecimento.</p><button className="buttonSecondary" disabled={busy} onClick={() => void action("enabled/", { enabled: true })}>Habilitar computadores de impressão</button></> : <>
        <form onSubmit={event => { event.preventDefault(); void inspect(); }}>
          <div className="field"><label>Código de pareamento<input value={code} maxLength={16} autoComplete="off" autoCapitalize="characters" onChange={event => { setCode(event.target.value.toUpperCase().replace(/[\s-]/g, "")); setInspection(null); }} /></label></div>
          <button className="buttonSecondary" disabled={busy || code.length !== 16}>Adicionar computador</button>
        </form>
        {inspection && <div className="panel"><strong>{inspection.label}</strong><p>Autorizar este computador em {inspection.venue_name}?</p><button className="buttonPrimary" disabled={busy} onClick={() => void approve()}>Autorizar este computador</button><button className="buttonQuiet" disabled={busy} onClick={() => setInspection(null)}>Cancelar</button></div>}
      </>}
      {data.results.length === 0 && <p>Nenhum computador pareado.</p>}
      {data.results.map(agent => <div className="dataRow" key={agent.id}><div><strong>{agent.label}</strong><p>{labels[agent.state] ?? agent.state} · Versão {agent.version || "ainda não informada"}</p><p className="muted">Conexão do computador não confirma disponibilidade da impressora.</p></div>{agent.state !== "REVOKED" && <button className="buttonSecondary" disabled={busy} onClick={() => { setRevoking(agent); setReason(""); }}>Revogar {agent.label}</button>}</div>)}
      {revoking && <form className="panel" onSubmit={event => { event.preventDefault(); void action(`${revoking.id}/revoke/`, { reason }).then(result => { if (result) { setRevoking(null); setMessage("Acesso do computador revogado."); } }); }}><strong>Revogar {revoking.label}?</strong><div className="field"><label>Motivo da revogação<input value={reason} maxLength={240} required onChange={event => setReason(event.target.value)} /></label></div><button className="buttonDanger buttonDangerReadable" disabled={busy || !reason.trim()}>Confirmar revogação</button><button type="button" className="buttonQuiet" disabled={busy} onClick={() => setRevoking(null)}>Cancelar revogação</button></form>}
    </>}
  </section>;
}
