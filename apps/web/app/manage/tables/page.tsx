"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { StaffAuthScreen } from "@/components/staff-auth-screen";
import { OperationalHeading } from "@/components/operational-heading";
import { ActionDialog } from "@/components/action-dialog";
import { apiCall, asApiError, type StaffSessionView } from "@/lib/client/staff-auth";

type Tab = { id: string; display_label: string; display_reference?: string; state: string };
type Table = { id: string; label: string; status: string; active_occupancy: { id: string; tabs: Tab[] } | null };
type Intent = { path: string; body: object; title: string; description: string };
const states: Record<string, string> = { AVAILABLE: "Disponível", OCCUPIED: "Ocupada", DIRTY: "Aguardando limpeza", CLEANING: "Em limpeza", OUT_OF_SERVICE: "Fora de uso" };
const openTabs = (table: Table) => table.active_occupancy?.tabs.filter(tab => tab.state !== "CLOSED" && tab.state !== "CANCELLED") ?? [];
export default function TablesPage() {
 return <StaffAuthScreen renderSession={session => <Tables key={session.session.id} session={session} />} />;
}
function Tables({ session }: { session: StaffSessionView }) {
 const canConfigure = session.capabilities.includes("venue.configure");
 const [tables, setTables] = useState<Table[]>([]), [fresh, setFresh] = useState(false), [loaded, setLoaded] = useState(false);
 const [error, setError] = useState(""), [notice, setNotice] = useState(""), [busy, setBusy] = useState(false);
 const [target, setTarget] = useState(""), [label, setLabel] = useState(""), [query, setQuery] = useState("");
 const [retireIds, setRetireIds] = useState<string[]>([]), [intent, setIntent] = useState<Intent | null>(null), [uncertain, setUncertain] = useState(false);
 const sending = useRef(false), reading = useRef(0);
 const load = useCallback(async () => {
  const request = ++reading.current;
  try {
   const result = await apiCall<{results: Table[]}>("/api/pos/hospitality/tables/");
   if (request !== reading.current) return;
   if (!result.response.ok) throw new Error(asApiError(result.body).message);
   setTables((result.body as {results: Table[]}).results); setLoaded(true); setFresh(true);
  } catch (failure) { if(request === reading.current) { setFresh(false); setError(failure instanceof Error ? failure.message : "Mesas indisponíveis."); } }
 }, []);
 useEffect(() => { queueMicrotask(() => void load()); const requestRef = reading; const timer = setInterval(() => { if (!sending.current) void load(); }, 15000); return () => { clearInterval(timer); ++requestRef.current; }; }, [load]);
 const working = tables.filter(table => table.status !== "OUT_OF_SERVICE");
 const available = working.filter(table => table.status === "AVAILABLE" && !table.active_occupancy);
 const occupied = tables.filter(table => !!table.active_occupancy);
 const count = Number(target), validCount = /^\d+$/.test(target) && count <= 500;
 const reduction = validCount ? Math.max(0, working.length-count) : 0;
 const disabled = busy || !fresh || uncertain;
 function reviewCount() {
  if (disabled || !validCount || (reduction && retireIds.length !== reduction)) return;
  const selected = tables.filter(table => retireIds.includes(table.id));
  setIntent({path:"/api/pos/hospitality/tables/count/", body:{target_count:count,expected_count:working.length,retire_ids:retireIds},title:"Revisar mesas para trabalhar",description: reduction ? `Retirar de uso: ${selected.map(table=>table.label).join(", ")}. O histórico será preservado.` : `Passar de ${working.length} para ${count} mesas em uso. Mesas fora de uso serão reativadas antes de cadastrar novas.`});
 }
 async function apply() {
  if (!intent || sending.current || disabled) return;
  const current = intent; sending.current = true; ++reading.current; setBusy(true); setFresh(false); setError(""); setNotice("");
  try {
   const result = await apiCall(current.path,{method:"POST",body:JSON.stringify(current.body)});
   if (!result.response.ok) { if(result.response.status >= 500) setUncertain(true); throw new Error(asApiError(result.body).message); }
   setNotice("Alteração confirmada. Lista reconsultada."); setTarget(""); setLabel(""); setRetireIds([]);
  } catch (failure) { setError(failure instanceof Error ? failure.message : "Resultado não confirmado. Confira as mesas antes de repetir."); setUncertain(true); }
  finally { await load(); setIntent(null); sending.current = false; setBusy(false); }
 }
 return <main className="appShell managementShell">
  <header className="productHeader"><div className="eyebrow">RODADA / GERÊNCIA</div><OperationalHeading as="h1" icon="table">Mesas</OperationalHeading><Link className="backLink" href="/manage#gestao">Voltar à Gestão</Link></header>
  {error && <p className="notice" data-state="danger" role="alert">{error}</p>}{notice && <p className="notice" role="status">{notice}</p>}
  <button className="buttonSecondary" disabled={busy} onClick={()=>{setError("");void load();}}>Atualizar mesas</button>
  {!loaded && <p role="status">Carregando mesas…</p>}
  {loaded && <section className="panel" aria-label="Resumo das mesas">
   <div className="dataRow"><span>Cadastradas</span><strong>{tables.length}</strong></div>
   <div className="dataRow"><span>Em uso no salão</span><strong>{working.length}</strong></div>
   <div className="dataRow"><span>Ocupadas</span><strong>{occupied.length}</strong></div>
   <div className="dataRow"><span>Disponíveis</span><strong>{available.length}</strong></div>
   <div className="dataRow"><span>Comandas abertas nas mesas</span><strong>{tables.reduce((sum,table)=>sum+openTabs(table).length,0)}</strong></div>
  </section>}
  {!fresh && loaded && <p className="notice" data-state="warning">Dados desatualizados. Atualize antes de alterar.</p>}
  {uncertain && <section className="notice" data-state="warning"><p>Confira a lista atual antes de fazer outra alteração.</p><button className="buttonSecondary" disabled={busy || !fresh} onClick={()=>{setUncertain(false);setError("");setNotice("");}}>Conferi as mesas</button></section>}
  {canConfigure ? <>
   <section className="panel"><OperationalHeading as="h2" icon="table">Quantas mesas vamos usar?</OperationalHeading>
    <p className="muted">Mesas retiradas ficam fora de uso. Ocupações, comandas e histórico são preservados.</p>
    <div className="field"><label htmlFor="table-count">Quantidade de mesas para trabalhar</label><input id="table-count" type="number" inputMode="numeric" min="0" max="500" value={target} disabled={disabled} onChange={event=>{setTarget(event.target.value);setRetireIds([]);}} /></div>
    {!!reduction && <fieldset disabled={disabled}><legend>Selecione {reduction} mesas disponíveis para retirar</legend>{available.map(table=><label className="tableInventoryChoice" key={table.id}><input type="checkbox" checked={retireIds.includes(table.id)} onChange={event=>setRetireIds(ids=>event.target.checked?[...ids,table.id]:ids.filter(id=>id!==table.id))} />{table.label}</label>)}{reduction>available.length && <p className="notice" data-state="warning">Há mesas ocupadas ou em limpeza. Não é possível atingir essa quantidade agora.</p>}</fieldset>}
    <button className="buttonPrimary" disabled={disabled || !validCount || count===working.length || (reduction>0 && retireIds.length!==reduction)} onClick={reviewCount}>Revisar quantidade</button>
   </section>
   <section className="panel"><OperationalHeading as="h2" icon="table">Adicionar uma mesa</OperationalHeading><div className="field"><label htmlFor="table-label">Nome ou número da mesa</label><input id="table-label" maxLength={80} value={label} disabled={disabled} onChange={event=>setLabel(event.target.value)} /></div><button className="buttonSecondary" disabled={disabled || !label.trim()} onClick={()=>setIntent({path:"/api/pos/hospitality/tables/",body:{label:label.trim(),guest_ordering_mode:"DISABLED"},title:"Adicionar mesa",description:`Cadastrar ${label.trim()} como disponível. Pedidos por QR começam desabilitados.`})}>Adicionar mesa</button></section>
  </> : <p className="notice">Seu acesso permite consultar, mas não configurar mesas.</p>}
  <section className="panel"><OperationalHeading as="h2" icon="table">Mesas do bar</OperationalHeading>
   <div className="field"><label htmlFor="table-filter">Buscar mesa</label><input id="table-filter" type="search" value={query} onChange={event=>setQuery(event.target.value)} /></div>
   {loaded && !tables.length && <p className="muted">Nenhuma mesa cadastrada.</p>}
   {tables.filter(table=>table.label.toLocaleLowerCase("pt-BR").includes(query.toLocaleLowerCase("pt-BR"))).map(table=><section className="tableInventoryRow" key={table.id}>
    <div className="dataRow"><strong>{table.label}</strong><span>{states[table.status] ?? table.status}</span></div>
    <p>{openTabs(table).length} comandas abertas</p>
    {!!openTabs(table).length && <details><summary>Ver comandas de {table.label}</summary>{openTabs(table).map(tab=><div className="dataRow" key={tab.id}><span>{tab.display_label || "Sem nome"}</span><span>{tab.display_reference || `Comanda ${tab.id.slice(0,8)}`}</span></div>)}</details>}
    {canConfigure && <button className={table.status==="OUT_OF_SERVICE"?"buttonSecondary":"buttonQuiet"} disabled={disabled || (table.status!=="OUT_OF_SERVICE" && (table.status!=="AVAILABLE" || !!table.active_occupancy))} onClick={()=>setIntent({path:`/api/pos/hospitality/tables/${table.id}/inventory/`,body:{enabled:table.status==="OUT_OF_SERVICE",expected_status:table.status},title:table.status==="OUT_OF_SERVICE"?"Voltar a usar mesa":"Retirar mesa de uso",description:`${table.label}. O histórico e as comandas serão preservados.`})}>{table.status==="OUT_OF_SERVICE"?"Voltar a usar":"Retirar de uso"}</button>}
   </section>)}
  </section>
  {intent && <ActionDialog title={intent.title} locked={busy} onClose={()=>setIntent(null)}><p>{intent.description}</p><button className="buttonPrimary" disabled={disabled} onClick={()=>void apply()}>{busy?"Aplicando…":"Confirmar"}</button></ActionDialog>}
 </main>;
}
