"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { StaffAuthScreen } from "@/components/staff-auth-screen";
import { OperationalHeading } from "@/components/operational-heading";
import { apiCall, asApiError, type StaffSessionView } from "@/lib/client/staff-auth";

type Member = { id: string; staff: { display_name: string; login_identifier: string }; role: string; status: string; version: number };
type Resource = { id: string; label: string };
const roles: Record<string, string> = { STAFF: "Atendente", CASHIER: "Caixa", MANAGER: "Gerente", OWNER: "Proprietário" };
const states: Record<string, string> = { ACTIVE: "Ativo", SUSPENDED: "Suspenso", REVOKED: "Revogado" };
async function call<T>(path: string, body?: object, method = "POST"): Promise<T> {
  const result = await apiCall<T>(path, body === undefined ? undefined : { method, body: JSON.stringify(body) });
  if (!result.response.ok || !result.body) throw new Error(asApiError(result.body).message);
  return result.body as T;
}

export default function SetupPage() {
  return <StaffAuthScreen renderSession={session => <Setup key={session.session.id} session={session} />} />;
}
function Setup({ session }: { session: StaffSessionView }) {
  const canConfigure = session.capabilities.includes("venue.configure"), canManage = session.capabilities.includes("staff.manage");
  const [tables, setTables] = useState<Resource[]>([]), [zones, setZones] = useState<Resource[]>([]), [members, setMembers] = useState<Member[]>([]);
  const [fresh, setFresh] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState(""), [notice, setNotice] = useState("");
  const [label, setLabel] = useState(""), [kind, setKind] = useState("table"), [mode, setMode] = useState("DISABLED"), [uncertainCreate, setUncertainCreate] = useState(false);
  const [selectedId, setSelectedId] = useState(""), [role, setRole] = useState("STAFF"), [status, setStatus] = useState("ACTIVE"), [reason, setReason] = useState(""), [pin, setPin] = useState("");
  const sending = useRef(false);
  const selected = members.find(member => member.id === selectedId);
  const load = useCallback(async (clearError = true) => {
    setFresh(false); if (clearError) setError("");
    try {
      const [tableRows, zoneRows, memberRows] = await Promise.all([
        call<{ results: Resource[] }>("/api/pos/hospitality/tables/"),
        call<{ results: Resource[] }>("/api/pos/hospitality/zones/"),
        canManage ? call<{ results: Member[] }>("/api/pos/manage/access/memberships/") : Promise.resolve({ results: [] as Member[] }),
      ]);
      setTables(tableRows.results); setZones(zoneRows.results); setMembers(memberRows.results); setFresh(true);
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Configuração indisponível."); }
  }, [canManage]);
  useEffect(() => { void load(); }, [load]);
  async function create() {
    if (sending.current || !fresh || uncertainCreate || !label.trim()) return;
    sending.current = true; setBusy(true); setError(""); setNotice("");
    let rejected = false;
    try {
      const result = await apiCall(`/api/pos/hospitality/${kind === "table" ? "tables" : "zones"}/`, { method: "POST", body: JSON.stringify({ label: label.trim(), ...(kind === "table" ? { guest_ordering_mode: mode } : {}) }) });
      if (!result.response.ok) {
        rejected = result.response.status < 500;
        if (result.response.status >= 500) setUncertainCreate(true);
        throw new Error(asApiError(result.body).message);
      }
      setLabel(""); setNotice("Cadastro confirmado.");
    } catch (failure) {
      if (!rejected) setUncertainCreate(true);
      setNotice("Confira a lista atual antes de tentar outro cadastro.");
      setError(failure instanceof Error ? failure.message : "Resultado não confirmado.");
    } finally { await load(false); sending.current = false; setBusy(false); }
  }
  async function saveMember() {
    if (!selected || sending.current || !fresh || !pin) return;
    sending.current = true; setBusy(true); setError(""); setNotice("");
    try {
      await call("/api/auth/reauthenticate", { pin });
      await call(`/api/pos/manage/access/memberships/${selected.id}/`, { expected_version: selected.version, role, status, reason }, "PATCH");
      setNotice("Função e situação confirmadas. Revogações podem exigir novo login."); setSelectedId("");
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Resultado não confirmado."); setNotice("Lista reconsultada. Confira o estado atual antes de aplicar novamente."); }
    finally { setPin(""); await load(false); sending.current = false; setBusy(false); }
  }
  return <main className="appShell managementShell">
    <header className="productHeader"><div className="eyebrow">RODADA / GERÊNCIA</div><OperationalHeading as="h1" icon="settings">Preparar estabelecimento</OperationalHeading><Link className="backLink" href="/manage">Voltar à gerência</Link></header>
    {error && <p className="notice" data-state="danger" role="alert">{error}</p>}{notice && <p className="notice" role="status">{notice}</p>}
    {!fresh && <p className="notice" data-state="warning">Dados ainda não confirmados. Atualize antes de alterar.</p>}
    <button className="buttonSecondary" disabled={busy} onClick={() => void load()}>Atualizar configuração</button>
    <section className="panel"><OperationalHeading as="h2" icon="table">Mesas e zonas</OperationalHeading>
      {fresh && <><p>Mesas: {tables.length ? tables.map(table => table.label).join(" · ") : "nenhuma cadastrada"}</p><p>Zonas: {zones.length ? zones.map(zone => zone.label).join(" · ") : "nenhuma cadastrada"}</p></>}
      {canConfigure ? <>
        <div className="field"><label htmlFor="setup-kind">Cadastrar</label><select id="setup-kind" value={kind} disabled={busy || uncertainCreate} onChange={event => setKind(event.target.value)}><option value="table">Mesa</option><option value="zone">Zona</option></select></div>
        <div className="field"><label htmlFor="setup-label">Nome ou identificação</label><input id="setup-label" maxLength={80} value={label} disabled={busy || uncertainCreate} onChange={event => setLabel(event.target.value)} /></div>
        {kind === "table" && <div className="field"><label htmlFor="setup-guest">Pedidos pelo QR</label><select id="setup-guest" value={mode} disabled={busy || uncertainCreate} onChange={event => setMode(event.target.value)}><option value="DISABLED">Desabilitados</option><option value="DIRECT">Pedido direto</option><option value="JOIN_ACTIVE">Somente ocupação ativa</option></select></div>}
        <button className="buttonPrimary" disabled={busy || !fresh || !label.trim() || uncertainCreate} onClick={() => void create()}>Cadastrar {kind === "table" ? "mesa" : "zona"}</button>
        {uncertainCreate && <div className="notice" data-state="warning"><p>Resultado não confirmado. Verifique os cadastros acima para evitar duplicação.</p><button className="buttonSecondary" disabled={busy || !fresh} onClick={() => { setUncertainCreate(false); setLabel(""); }}>Conferi a lista; liberar novo cadastro</button></div>}
      </> : <p>Seu acesso não permite configurar mesas ou zonas.</p>}
      <Link className="backLink" href="/attendance">Operar mesas e ajustar localização →</Link>
    </section>
    <section className="panel"><OperationalHeading as="h2" icon="people">Equipe existente</OperationalHeading>
      <p className="muted">Novos operadores dependem do provisionamento pela administração. Esta tela altera somente vínculos existentes.</p>
      {canManage ? <>
        <div className="field"><label htmlFor="setup-member">Operador</label><select id="setup-member" value={selectedId} disabled={busy || !fresh} onChange={event => { setSelectedId(event.target.value); const member = members.find(row => row.id === event.target.value); if (member) { setRole(member.role); setStatus(member.status); } }}><option value="">Selecionar operador</option>{members.map(member => <option key={member.id} value={member.id}>{member.staff.display_name} · {states[member.status]}</option>)}</select></div>
        {selected && <><p>Atual: {roles[selected.role]} · {states[selected.status]}</p>
          <div className="field"><label htmlFor="setup-role">Nova função</label><select id="setup-role" value={role} disabled={busy} onChange={event => setRole(event.target.value)}>{Object.entries(roles).map(([value, title]) => <option key={value} value={value}>{title}</option>)}</select></div>
          <div className="field"><label htmlFor="setup-status">Nova situação</label><select id="setup-status" value={status} disabled={busy} onChange={event => setStatus(event.target.value)}>{Object.entries(states).map(([value, title]) => <option key={value} value={value}>{title}</option>)}</select></div>
          <div className="field"><label htmlFor="setup-reason">Motivo (opcional)</label><input id="setup-reason" maxLength={240} value={reason} disabled={busy} onChange={event => setReason(event.target.value)} /></div>
          <div className="field"><label htmlFor="setup-pin">Seu PIN para confirmar</label><input id="setup-pin" type="password" autoComplete="off" value={pin} disabled={busy} onChange={event => setPin(event.target.value)} /></div>
          <p className="muted">Aplicar suspensão ou revogação pode encerrar sessões do operador.</p><button className="buttonPrimary" disabled={busy || !fresh || !pin} onClick={() => void saveMember()}>Aplicar função e situação</button>
        </>}
      </> : <p>Seu acesso não permite administrar a equipe.</p>}
    </section>
  </main>;
}
