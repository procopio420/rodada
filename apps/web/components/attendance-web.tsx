"use client";

import { OperationalIcon, type OperationalIconName } from "@/components/operational-icon";
import { OperationalHeading } from "@/components/operational-heading";

import { useCallback, useEffect, useRef, useState } from "react";
import { StaffAuthScreen } from "@/components/staff-auth-screen";
import { normalizeCatalogSearch } from "@/lib/client/attendance-catalog";
import { OrderWorkspace, type TableTabSelection } from "@/components/order-workspace";
import { ServiceRequestQueue } from "@/components/service-request-queue";
import { ActionDialog } from "@/components/action-dialog";
import { TabLocationMove, type MoveSelection } from "@/components/tab-location-move";
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
  const [tableDialog, setTableDialog] = useState<{id: string; release: boolean} | null>(null);
  const [moveSelection, setMoveSelection] = useState<MoveSelection | null>(null);
  const [moveLocked, setMoveLocked] = useState(true);
  const closeMove = useCallback(() => setMoveSelection(null), []);
  const [pendingOrder, setPendingOrder] = useState(false);
  const [tableSearch, setTableSearch] = useState("");
  const [tableSelection, setTableSelection] = useState<TableTabSelection | null>(null);
  const [tableOrigin, setTableOrigin] = useState<TableTabSelection | null>(null);
  const [tableOpening, setTableOpening] = useState(false);
  const openingTableRequest = useRef(0);
  const tableOpeningLock = useRef(false);
  const [returnFocus, setReturnFocus] = useState<string | null>(null);

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
  function openTableTab(table: Table, tab: Tab) {
    if (tableOpeningLock.current || busy || moveLocked || pendingOrder || !online || !table.active_occupancy) return;
    tableOpeningLock.current = true; setTableOpening(true); setError(""); setMessage("");
    setTableSelection({ requestId: ++openingTableRequest.current, tabId: tab.id, tableId: table.id, tableLabel: table.label, occupancyId: table.active_occupancy.id });
  }
  const tableSelectionResult = useCallback((failure: string | null, selection: TableTabSelection) => {
    if (selection.requestId !== openingTableRequest.current) return;
    tableOpeningLock.current = false; setTableOpening(false);
    if (failure) { setError(failure); return; }
    setTableOrigin(selection); setScreen("tabs");
  }, []);
  function returnToTable() {
    if (!tableOrigin || busy || moveLocked || pendingOrder || tableOpeningLock.current) return;
    setReturnFocus(tableOrigin.tableId); setScreen("tables");
  }
  useEffect(() => {
    if (screen !== "tables" || !returnFocus) return;
    const heading = document.getElementById(`attendance-table-${returnFocus}`);
    heading?.focus(); heading?.scrollIntoView({ block: "nearest" }); setReturnFocus(null);
  }, [screen, returnFocus]);
  const normalizeTable = (value: string) => normalizeCatalogSearch(value).replace(/^mesa\s*/, "").replace(/\s+/g, " ");
  const tableQuery = normalizeTable(tableSearch);
  const visibleTables = tables.filter(table => normalizeTable(table.label).includes(tableQuery));
  async function command(path: string, payload: object = {}) {
    if (busy || moveLocked || !online) return;
    setBusy(true); setError(""); setMessage("");
    try { await request(path, payload); setMessage("Operação confirmada."); await refresh(); return true; }
    catch (failure) { setError(failure instanceof Error ? failure.message : "Não foi possível concluir."); return false; }
    finally { setBusy(false); }
  }
  return <main className="appShell attendanceShell">
    <header className="productHeader"><div className="eyebrow">RODADA / ATENDIMENTO</div><OperationalHeading as="h1" icon="people">{session.venue.name}</OperationalHeading><p className="muted">{session.staff.display_name} · {loading ? "Atualizando…" : online ? `Atualizado às ${updated}` : "Desatualizado · verifique a conexão"}</p><div className="notice" data-state="warning">Teste sem pagamentos. O saldo das comandas permanece em aberto.</div><div className="actions"><button className="buttonSecondary" disabled={busy || moveLocked} onClick={() => void refresh()}>Atualizar</button><button className="buttonQuiet" disabled={busy || moveLocked || pendingOrder || tableOpening} onClick={() => void logout()}>Sair</button></div></header>
    <nav className="attendanceNav" aria-label="Atendimento">{[["now", "Agora"], ["tabs", "Contas"], ["tables", "Mesas"]].map(([id, title]) => <button key={id} className={screen === id ? "buttonPrimary" : "buttonSecondary"} aria-current={screen === id ? "page" : undefined} disabled={busy || moveLocked || pendingOrder || tableOpening} onClick={() => { setScreen(id); void refresh(); }}><OperationalIcon name={({ now: "now", tabs: "wallet", tables: "table" } as Record<string, OperationalIconName>)[id]} /><span>{title}</span></button>)}</nav>
    {error && <p className="notice" data-state="danger" role="alert">{error}</p>}{message && <p className="notice" data-state="success" role="status">{message}</p>}
    <fieldset className="workspaceLock" disabled={moveLocked}>{screen === "now" && <section className="panel"><OperationalHeading as="h2" icon="check">Entregas prontas</OperationalHeading>{loading ? <p>Carregando entregas…</p> : !deliveries.length && online ? <p className="muted">Nenhuma entrega pronta.</p> : deliveries.map(delivery => <article className="attendanceItem" key={delivery.id}><h3>{delivery.quantity || 1}× {delivery.product_name}</h3><p>{delivery.destination_label || "Sem mesa"} · {delivery.tab_label || "Comanda"}</p><p className="muted">Pronto há {Math.floor(delivery.age_seconds / 60)} min</p><button className="buttonPrimary" disabled={busy || moveLocked || pendingOrder || tableOpening || !online} onClick={() => void command(`dispatch/delivery/${delivery.id}/complete/`)}>Concluir entrega</button></article>)}</section>}
    <div hidden={screen !== "now"}><ServiceRequestQueue staffId={session.staff.id} /></div>
    <div hidden={screen !== "tabs"}>{tableOrigin && <button className="buttonSecondary" disabled={busy || moveLocked || pendingOrder || tableOpening} onClick={returnToTable}>Voltar à mesa {tableOrigin.tableLabel}</button>}<OrderWorkspace tableSelection={tableSelection} onTableSelectionResult={tableSelectionResult} withoutPayments onPendingChange={setPendingOrder} onRecoveryNeeded={() => setScreen("tabs")} /></div>
    {screen === "tables" && <section className="panel"><OperationalHeading as="h2" icon="table">Mesas</OperationalHeading><div className="field"><label htmlFor="attendance-table-search">Buscar mesa</label><input id="attendance-table-search" type="search" value={tableSearch} maxLength={80} onChange={event => setTableSearch(event.target.value)} placeholder="Nome ou número da mesa" /></div>{tableOpening && <p role="status">Abrindo comanda da mesa…</p>}{loading ? <p>Carregando mesas…</p> : !tables.length && online ? <p className="muted">Nenhuma mesa cadastrada.</p> : !visibleTables.length && online ? <p className="muted">Nenhuma mesa encontrada.</p> : visibleTables.map(table => <article className="attendanceItem" key={table.id}><h3 tabIndex={-1} id={`attendance-table-${table.id}`}>Mesa {table.label}</h3><p>{labels[table.status] || table.status}</p>{table.active_occupancy?.tabs?.map(tab => <div key={tab.id}><button className="buttonSecondary attendanceTabOption" disabled={busy || moveLocked || pendingOrder || tableOpening || !online} onClick={() => openTableTab(table, tab)}>Abrir comanda {tab.display_label || "sem nome"} · ID {tab.id}</button>{session.capabilities.includes("tab.move") && <button className="buttonQuiet attendanceTabOption" disabled={busy || moveLocked || pendingOrder || tableOpening || !online} onClick={() => setMoveSelection({ table, tab })}>Mover comanda {tab.display_label || "sem nome"} · ID {tab.id}</button>}</div>)}<button className="buttonQuiet" disabled={busy || moveLocked || pendingOrder || tableOpening || !online} onClick={() => setTableDialog({ id: table.id, release: false })}>Organizar mesa {table.label}</button>{tableDialog?.id === table.id && !tableDialog.release && <ActionDialog title={`Organizar mesa ${table.label}`} locked={busy} onClose={() => setTableDialog(null)}>{error && <p className="notice" role="alert" data-state="danger">{error}</p>}{message && <p className="notice" role="status" data-state="success">{message}</p>}<div className="field"><label htmlFor={`zone-${table.id}`}>Localização da mesa {table.label}</label><select id={`zone-${table.id}`} value={table.zone?.id || ""} disabled={busy || moveLocked || pendingOrder || tableOpening || !online} onChange={event => void command(`hospitality/tables/${table.id}/location/`, { zone_id: event.target.value || null })}><option value="">Sem zona</option>{zones.map(zone => <option key={zone.id} value={zone.id}>{zone.label}</option>)}</select></div>{table.active_occupancy && <div className="field"><label htmlFor={`attach-${table.id}`}>Associar comanda à mesa {table.label}</label><select id={`attach-${table.id}`} value="" disabled={busy || moveLocked || pendingOrder || tableOpening || !online} onChange={event => { if (event.target.value) void command(`hospitality/occupancies/${table.active_occupancy!.id}/tabs/`, { tab_id: event.target.value }); }}><option value="">Selecionar comanda</option>{tabs.filter(tab => !table.active_occupancy?.tabs?.some(attached => attached.id === tab.id)).map(tab => <option key={tab.id} value={tab.id}>{tab.display_label || "Sem identificação"}</option>)}</select></div>}</ActionDialog>}
      {table.status === "AVAILABLE" && <button className="buttonPrimary" disabled={busy || moveLocked || pendingOrder || tableOpening || !online} onClick={() => void command(`hospitality/tables/${table.id}/occupy/`)}>Ocupar mesa {table.label}</button>}
      {table.status === "OCCUPIED" && <><p className="muted">Liberar encerra o acesso por QR. As comandas permanecem abertas.</p><button className="buttonSecondary" disabled={busy || moveLocked || pendingOrder || tableOpening || !online} onClick={() => { setError(""); setMessage(""); setTableDialog({id: table.id, release: true}); }}>Liberar mesa {table.label}</button></>}
      {tableDialog?.id === table.id && tableDialog.release && <ActionDialog title={`Liberar mesa ${table.label}?`} locked={busy} onClose={() => setTableDialog(null)}><p>O acesso por QR será encerrado. As comandas permanecem abertas.</p>{error && <p className="notice" role="alert" data-state="danger">{error}</p>}<button className="buttonSecondary" disabled={busy || moveLocked || pendingOrder || tableOpening || !online} onClick={() => void command(`hospitality/tables/${table.id}/release/`).then(ok => { if (ok) setTableDialog(null); })}>Confirmar liberação</button></ActionDialog>}
      {table.status === "DIRTY" && <button className="buttonPrimary" disabled={busy || moveLocked || pendingOrder || tableOpening || !online} onClick={() => void command(`hospitality/tables/${table.id}/cleaning/start/`)}>Iniciar limpeza</button>}
      {table.status === "CLEANING" && <button className="buttonPrimary" disabled={busy || moveLocked || pendingOrder || tableOpening || !online} onClick={() => void command(`hospitality/tables/${table.id}/cleaning/complete/`)}>Concluir limpeza</button>}

{table.status === "OCCUPIED" && table.active_occupancy && session.capabilities.includes("table.manage") && <PartySizeEditor key={table.active_occupancy.id} occupancyId={table.active_occupancy.id} />}
    </article>)}</section>}
  </fieldset><TabLocationMove selection={moveSelection} tables={tables} onClose={closeMove} onLockChange={setMoveLocked} onConfirmed={refresh} />
  </main>;
}
