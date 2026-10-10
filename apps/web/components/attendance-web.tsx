"use client";

import { OperationalIcon, type OperationalIconName } from "@/components/operational-icon";
import { OperationalHeading } from "@/components/operational-heading";

import { useCallback, useEffect, useState } from "react";
import { StaffAuthScreen } from "@/components/staff-auth-screen";
import { OrderWorkspace } from "@/components/order-workspace";
import { ServiceRequestQueue } from "@/components/service-request-queue";
import { PartySizeEditor } from "@/components/party-size-editor";
import { apiCall, asApiError, type StaffSessionView } from "@/lib/client/staff-auth";

type Table = { id: string; label: string; status: string; zone?: { id: string; label: string }; active_occupancy?: { id: string; tabs?: { id: string; display_label: string }[] } };
type Delivery = { id: string; product_name: string; quantity: number; tab_label: string; destination_label: string; age_seconds: number };
type Tab = { id: string; display_label: string };
const labels: Record<string, string> = { AVAILABLE: "Disponível", OCCUPIED: "Ocupada", DIRTY: "Aguardando limpeza", CLEANING: "Em limpeza", OUT_OF_SERVICE: "Fora de serviço" };
async function request<T>(path: string, payload?: object): Promise<T> {
  const result = await apiCall<T>(`/api/attendance/${path}`, payload === undefined ? undefined : { method: "POST", body: JSON.stringify(payload) });
  if (!result.response.ok) throw new Error(asApiError(result.body).message);
  return result.body as T;
}
export function AttendanceWeb() {
  return <StaffAuthScreen renderSession={(session, logout) => <Workspace key={session.session.id} session={session} logout={logout} />} />;
}
function Workspace({ session, logout }: { session: StaffSessionView; logout: () => Promise<void> }) {
  const [pendingOrder, setPendingOrder] = useState(false);
  const [screen, setScreen] = useState("now"), [busy, setBusy] = useState(false), [online, setOnline] = useState(false), [loading, setLoading] = useState(true);
  const [tables, setTables] = useState<Table[]>([]), [deliveries, setDeliveries] = useState<Delivery[]>([]), [tabs, setTabs] = useState<Tab[]>([]), [zones, setZones] = useState<{ id: string; label: string }[]>([]);
  const [error, setError] = useState(""), [message, setMessage] = useState(""), [updated, setUpdated] = useState("");
  const refresh = useCallback(async () => {
    try {
      const [tableList, queue, zoneList] = await Promise.all([request<{ results: Table[] }>("hospitality/tables/"), request<{ results: Delivery[] }>("dispatch/delivery/"), request<{ results: { id: string; label: string }[] }>("hospitality/zones/")]);
      const allTabs: Tab[] = [];
      let offset: number | null = 0;
      do { const page: { results: Tab[]; next_offset?: number | null } = await request(`tabs/?active=true&offset=${offset}`); allTabs.push(...page.results); offset = page.next_offset ?? null; } while (offset !== null);
      setTables(tableList.results); setDeliveries(queue.results); setZones(zoneList.results); setTabs(allTabs); setOnline(true); setUpdated(new Date().toLocaleTimeString("pt-BR"));
    } catch (failure) { setOnline(false); setError(failure instanceof Error ? failure.message : "Não foi possível atualizar."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void refresh(); const timer = setInterval(() => void refresh(), 15000); return () => clearInterval(timer); }, [refresh]);
  async function command(path: string, payload: object = {}) {
    if (busy || !online) return;
    setBusy(true); setError(""); setMessage("");
    try { await request(path, payload); setMessage("Operação confirmada."); await refresh(); }
    catch (failure) { setError(failure instanceof Error ? failure.message : "Não foi possível concluir."); }
    finally { setBusy(false); }
  }
  return <main className="appShell attendanceShell">
    <header className="productHeader"><div className="eyebrow">RODADA / ATENDIMENTO</div><OperationalHeading as="h1" icon="people">{session.venue.name}</OperationalHeading><p className="muted">{session.staff.display_name} · {loading ? "Atualizando…" : online ? `Atualizado às ${updated}` : "Desatualizado · verifique a conexão"}</p><div className="notice" data-state="warning">Teste sem pagamentos. O saldo das comandas permanece em aberto.</div><div className="actions"><button className="buttonSecondary" disabled={busy} onClick={() => void refresh()}>Atualizar</button><button className="buttonQuiet" disabled={busy || pendingOrder} onClick={() => void logout()}>Sair</button></div></header>
    <nav className="attendanceNav" aria-label="Atendimento">{[["now", "Agora"], ["tabs", "Contas"], ["tables", "Mesas"]].map(([id, title]) => <button key={id} className={screen === id ? "buttonPrimary" : "buttonSecondary"} aria-current={screen === id ? "page" : undefined} disabled={busy || pendingOrder} onClick={() => { setScreen(id); void refresh(); }}><OperationalIcon name={({ now: "now", tabs: "wallet", tables: "table" } as Record<string, OperationalIconName>)[id]} /><span>{title}</span></button>)}</nav>
    {error && <p className="notice" data-state="danger" role="alert">{error}</p>}{message && <p className="notice" data-state="success" role="status">{message}</p>}
    {screen === "now" && <section className="panel"><OperationalHeading as="h2" icon="check">Entregas prontas</OperationalHeading>{loading ? <p>Carregando entregas…</p> : !deliveries.length && online ? <p className="muted">Nenhuma entrega pronta.</p> : deliveries.map(delivery => <article className="attendanceItem" key={delivery.id}><h3>{delivery.quantity || 1}× {delivery.product_name}</h3><p>{delivery.destination_label || "Sem mesa"} · {delivery.tab_label || "Comanda"}</p><p className="muted">Pronto há {Math.floor(delivery.age_seconds / 60)} min</p><button className="buttonPrimary" disabled={busy || !online} onClick={() => void command(`dispatch/delivery/${delivery.id}/complete/`)}>Concluir entrega</button></article>)}</section>}
    <div hidden={screen !== "now"}><ServiceRequestQueue staffId={session.staff.id} /></div>
    <div hidden={screen !== "tabs"}><OrderWorkspace withoutPayments onPendingChange={setPendingOrder} /></div>
    {screen === "tables" && <section className="panel"><OperationalHeading as="h2" icon="table">Mesas</OperationalHeading>{loading ? <p>Carregando mesas…</p> : !tables.length && online ? <p className="muted">Nenhuma mesa cadastrada.</p> : tables.map(table => <article className="attendanceItem" key={table.id}><h3>Mesa {table.label}</h3><p>{labels[table.status] || table.status}</p>{table.active_occupancy?.tabs?.map(tab => <p key={tab.id}>{tab.display_label || "Comanda sem nome"}</p>)}<div className="field"><label htmlFor={`zone-${table.id}`}>Localização da mesa {table.label}</label><select id={`zone-${table.id}`} value={table.zone?.id || ""} disabled={busy || !online} onChange={event => void command(`hospitality/tables/${table.id}/location/`, { zone_id: event.target.value || null })}><option value="">Sem zona</option>{zones.map(zone => <option key={zone.id} value={zone.id}>{zone.label}</option>)}</select></div>
      {table.status === "AVAILABLE" && <button className="buttonPrimary" disabled={busy || !online} onClick={() => void command(`hospitality/tables/${table.id}/occupy/`)}>Ocupar mesa {table.label}</button>}
      {table.status === "OCCUPIED" && <>{table.active_occupancy && <div className="field"><label htmlFor={`attach-${table.id}`}>Associar comanda à mesa {table.label}</label><select id={`attach-${table.id}`} value="" disabled={busy || !online} onChange={event => { if (event.target.value) void command(`hospitality/occupancies/${table.active_occupancy!.id}/tabs/`, { tab_id: event.target.value }); }}><option value="">Selecionar comanda</option>{tabs.filter(tab => !table.active_occupancy?.tabs?.some(attached => attached.id === tab.id)).map(tab => <option key={tab.id} value={tab.id}>{tab.display_label || "Sem identificação"}</option>)}</select></div>}<p className="muted">Liberar encerra o acesso por QR. As comandas permanecem abertas.</p><button className="buttonSecondary" disabled={busy || !online} onClick={() => void command(`hospitality/tables/${table.id}/release/`)}>Liberar mesa {table.label}</button></>}
      {table.status === "DIRTY" && <button className="buttonPrimary" disabled={busy || !online} onClick={() => void command(`hospitality/tables/${table.id}/cleaning/start/`)}>Iniciar limpeza</button>}
      {table.status === "CLEANING" && <button className="buttonPrimary" disabled={busy || !online} onClick={() => void command(`hospitality/tables/${table.id}/cleaning/complete/`)}>Concluir limpeza</button>}
      {table.status === "OCCUPIED" && table.active_occupancy && session.capabilities.includes("table.manage") && <PartySizeEditor key={table.active_occupancy.id} occupancyId={table.active_occupancy.id} />}
    </article>)}</section>}
  </main>;
}
