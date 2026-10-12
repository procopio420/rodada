"use client";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { StaffAuthScreen } from "./staff-auth-screen";
import { OperationalHeading } from "./operational-heading";
import { apiCall, asApiError, type StaffSessionView } from "@/lib/client/staff-auth";

type Member = { id: string; staff: { id: string; display_name: string; login_identifier: string }; role: string; status: string; version: number };
const roles: Record<string, string> = { STAFF: "Atendente", CASHIER: "Caixa", MANAGER: "Gerente", OWNER: "Proprietário" };
const states: Record<string, string> = { ACTIVE: "Ativo", SUSPENDED: "Suspenso", REVOKED: "Removido" };
type Intent = { path: string; method: string; body: object };
export function DeveloperStaff() {
  return <StaffAuthScreen renderSession={session => <StaffTools key={session.session.id} session={session} />} />;
}
function StaffTools({ session }: { session: StaffSessionView }) {
  const [members, setMembers] = useState<Member[]>([]);
  const [fresh, setFresh] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState(""), [notice, setNotice] = useState("");
  const [name, setName] = useState(""), [login, setLogin] = useState(""), [newPin, setNewPin] = useState(""), [role, setRole] = useState("STAFF"), [actorPin, setActorPin] = useState("");
  const [selectedId, setSelectedId] = useState(""), [editRole, setEditRole] = useState("STAFF"), [editStatus, setEditStatus] = useState("ACTIVE"), [showRemoved, setShowRemoved] = useState(false), [confirmRemove, setConfirmRemove] = useState(false), [uncertain, setUncertain] = useState(false);
  const intent = useRef<Intent | null>(null), sending = useRef(false);
  const allowed = session.capabilities.includes("staff.manage");
  const selected = members.find(member => member.id === selectedId);
  const load = useCallback(async () => {
    setFresh(false);
    try {
      const result = await apiCall<{ results: Member[] }>("/api/pos/developer/staff/");
      if (!result.response.ok || !result.body || !("results" in result.body)) throw new Error(asApiError(result.body).message);
      setMembers(result.body.results); setFresh(true);
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Equipe indisponível."); }
  }, []);
  useEffect(() => { if (allowed) void load(); }, [allowed, load]);
  async function send(next: Intent) {
    if (sending.current || !fresh || !actorPin) return;
    sending.current = true; setBusy(true); setError(""); setNotice("");
    let commandStarted = false;
    try {
      const auth = await apiCall("/api/auth/reauthenticate", { method: "POST", body: JSON.stringify({ pin: actorPin }) });
      if (!auth.response.ok) throw new Error(asApiError(auth.body).message);
      intent.current = next; commandStarted = true;
      const result = await apiCall<Member>(next.path, { method: next.method, body: JSON.stringify(next.body) });
      if (!result.response.ok) {
        if (result.response.status < 500) { intent.current = null; setUncertain(false); commandStarted = false; }
        throw new Error(result.response.status === 400 ? "Confira nome, login e PIN (4 a 12 dígitos)." : asApiError(result.body).message);
      }
      intent.current = null; setUncertain(false); setConfirmRemove(false); setSelectedId(""); setName(""); setLogin(""); setNewPin("");
      setNotice("Alteração confirmada. A lista mostra o estado atual.");
    } catch (failure) {
      if (commandStarted) setUncertain(true);
      setError(failure instanceof Error ? failure.message : "Resultado não confirmado.");
    } finally { setActorPin(""); await load(); setBusy(false); sending.current = false; }
  }
  return <main className="appShell managementShell">
    <header className="productHeader"><div className="eyebrow">RODADA / DEV · {session.venue.name}</div><OperationalHeading as="h1" icon="people">Administrar equipe</OperationalHeading><p className="muted">Ferramenta local de desenvolvimento. Alterações valem somente para este estabelecimento.</p><Link className="backLink" href="/manage#mais">Voltar à Gerência →</Link></header>
    {!allowed ? <p className="notice" role="alert">Seu acesso não permite administrar a equipe.</p> : <>
      {error && <p className="notice" data-state="danger" role="alert">{error}</p>}{notice && <p className="notice" role="status">{notice}</p>}
      <button className="buttonSecondary" disabled={busy} onClick={() => { setError(""); void load(); }}>Atualizar equipe</button>
      <section className="panel"><OperationalHeading as="h2" icon="people">Equipe cadastrada</OperationalHeading>
        {!fresh && <p role="status">Lista ainda não confirmada. Atualize antes de alterar.</p>}
        <button className="buttonQuiet" aria-pressed={showRemoved} onClick={() => setShowRemoved(value => !value)}>{showRemoved ? "Ocultar acessos removidos" : "Mostrar acessos removidos"}</button>
        {fresh && members.filter(member => showRemoved || member.status !== "REVOKED").map(member => <div className="dataRow" key={member.id}><div><strong>{member.staff.display_name}</strong><small>{member.staff.login_identifier} · {roles[member.role]} · {states[member.status]}</small></div><button className="buttonQuiet" disabled={busy || uncertain} onClick={() => { setSelectedId(member.id); setEditRole(member.role); setEditStatus(member.status); setConfirmRemove(false); }}>Gerenciar {member.staff.display_name}</button></div>)}
      </section>
      <section className="panel"><OperationalHeading as="h2" icon="people">Criar operador</OperationalHeading>
        <div className="field"><label htmlFor="dev-name">Nome do operador</label><input id="dev-name" maxLength={120} value={name} disabled={busy || uncertain} onChange={event => setName(event.target.value)} /></div>
        <div className="field"><label htmlFor="dev-login">Login do novo operador</label><input id="dev-login" maxLength={120} autoCapitalize="none" value={login} disabled={busy || uncertain} onChange={event => setLogin(event.target.value)} /></div>
        <div className="field"><label htmlFor="dev-new-pin">PIN do novo operador</label><input id="dev-new-pin" type="password" inputMode="numeric" autoComplete="new-password" maxLength={12} value={newPin} disabled={busy || uncertain} onChange={event => setNewPin(event.target.value)} /></div>
        <div className="field"><label htmlFor="dev-role">Função do novo operador</label><select id="dev-role" value={role} disabled={busy || uncertain} onChange={event => setRole(event.target.value)}>{Object.entries(roles).map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select></div>
        <button className="buttonPrimary" disabled={busy || uncertain || !fresh || !actorPin || !name.trim() || !/^[a-zA-Z0-9_.-]+$/.test(login.trim()) || !/^\d{4,12}$/.test(newPin)} onClick={() => void send({path:"/api/pos/developer/staff/",method:"POST",body:{display_name:name.trim(),login_identifier:login.trim(),pin:newPin,role,idempotency_key:crypto.randomUUID()}})}>Criar operador</button>
      </section>
      {selected && <section className="panel"><OperationalHeading as="h2" icon="settings">Acesso de {selected.staff.display_name}</OperationalHeading>
        <div className="field"><label htmlFor="dev-edit-role">Função</label><select id="dev-edit-role" value={editRole} disabled={busy || uncertain} onChange={event => setEditRole(event.target.value)}>{Object.entries(roles).map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select></div>
        <div className="field"><label htmlFor="dev-edit-status">Situação</label><select id="dev-edit-status" value={editStatus} disabled={busy || uncertain} onChange={event => setEditStatus(event.target.value)}><option value="ACTIVE">Ativo</option><option value="SUSPENDED">Suspenso</option>{selected.status === "REVOKED" && <option value="REVOKED">Removido</option>}</select></div>
        <button className="buttonSecondary" disabled={busy || uncertain || !fresh || !actorPin || selected.staff.id===session.staff.id} onClick={() => void send({path:`/api/pos/developer/staff/${selected.id}/`,method:"PATCH",body:{expected_version:selected.version,role:editRole,status:editStatus,reason:"Alteração pela área DEV"}})}>Salvar acesso</button>
        {selected.status!=="REVOKED" && selected.staff.id!==session.staff.id && <><button className="buttonDanger buttonDangerReadable" disabled={busy || uncertain} onClick={() => setConfirmRemove(true)}>Remover acesso</button>{confirmRemove && <div className="notice" data-state="warning"><p>Remover acesso de {selected.staff.display_name}? Suas sessões serão encerradas e o histórico será preservado.</p><button className="buttonDanger buttonDangerReadable" disabled={busy || !fresh || !actorPin || uncertain} onClick={() => void send({path:`/api/pos/developer/staff/${selected.id}/`,method:"POST",body:{expected_version:selected.version}})}>Confirmar remoção do acesso</button><button className="buttonQuiet" disabled={busy} onClick={() => setConfirmRemove(false)}>Cancelar</button></div>}</>}
      </section>}
      <section className="panel"><div className="field"><label htmlFor="dev-actor-pin">Seu PIN para confirmar</label><input id="dev-actor-pin" type="password" inputMode="numeric" autoComplete="off" value={actorPin} disabled={busy} onChange={event => setActorPin(event.target.value)} /></div><p className="muted">Informe seu PIN antes de criar, salvar ou remover um acesso.</p>
        {uncertain && <div className="notice" data-state="warning"><p>Resposta não confirmada. Os dados estão preservados para repetir a mesma tentativa. Confira também a lista.</p><button className="buttonSecondary" disabled={busy || !fresh || !actorPin} onClick={() => intent.current && void send(intent.current)}>Verificar mesma tentativa</button></div>}
      </section>
    </>}
  </main>;
}
