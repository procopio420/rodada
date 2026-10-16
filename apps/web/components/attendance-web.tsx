"use client";

import "./attendance-ux2.css";
import { currentTaskTarget, type StaffTask } from "@/lib/client/dispatch-target";
import { OperationalIcon } from "@/components/operational-icon";
import { tabPrimaryLabel, tabReference } from "@/lib/client/tab-identity";
import { OperationalHeading } from "@/components/operational-heading";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRealtime } from "@/lib/client/use-realtime";
import { StaffAuthScreen } from "@/components/staff-auth-screen";
import { normalizeCatalogSearch } from "@/lib/client/attendance-catalog";
import { OrderWorkspace, type TableTabSelection } from "@/components/order-workspace";
import { ServiceRequestQueue } from "@/components/service-request-queue";
import { ActionDialog } from "@/components/action-dialog";
import { TabLocationMove, type MoveSelection } from "@/components/tab-location-move";

import { apiCall, asApiError, type StaffSessionView } from "@/lib/client/staff-auth";

type Occupancy = { id: string; generation: number; responsibility_version: number; responsible_staff_id: string | null; responsible_staff?: { id: string; display_name: string }; unassigned_service_attention?: string; unassigned_guest_order_count?: number; oldest_unassigned_guest_order_at?: string; tabs?: { id: string; display_label: string; display_reference?: string; opened_at?: string; state?: string }[] };
type Table = { id: string; label: string; status: string; zone?: { id: string; label: string }; active_occupancy?: Occupancy };
type ServiceIntent = { path: string; payload: Record<string, unknown> };
type Delivery = { id: string; product_name: string; quantity: number; tab_label: string; destination_label: string; age_seconds: number };
type Tab = { id: string; display_label: string; table_label?: string | null; last_table_label?: string | null };
const labels: Record<string, string> = { AVAILABLE: "Disponível", OCCUPIED: "Ocupada", DIRTY: "Aguardando limpeza", CLEANING: "Em limpeza", OUT_OF_SERVICE: "Fora de serviço" };
async function request<T>(path: string, payload?: object): Promise<T> {
  const result = await apiCall<T>(`/api/attendance/${path}`, payload === undefined ? undefined : { method: "POST", body: JSON.stringify(payload) });
  if (!result.response.ok) throw Object.assign(new Error(asApiError(result.body).message), { status: result.response.status });
  return result.body as T;
}
export function AttendanceWeb() {
  return <StaffAuthScreen renderSession={(session, logout) => <Workspace key={session.session.id} session={session} logout={logout} />} />;
}
function Workspace({ session, logout }: { session: StaffSessionView; logout: () => Promise<void> }) {
  const storageKey = `rodada:table-service:${session.venue.id}:${session.staff.id}:${session.session.id}`;
  const [serviceEnabled, setServiceEnabled] = useState(false);
  const [moving, setMoving] = useState<{ table: Table; tab: Tab; origin: string } | null>(null);
  const [recoveryBlocked, setRecoveryBlocked] = useState(false);
  const [intent, setIntent] = useState<ServiceIntent | null>(null);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [requestedTab, setRequestedTab] = useState<{ id: string; sequence: number; destination: string } | null>(null);
  const [createRequest, setCreateRequest] = useState(0);
  const [destinationPicker, setDestinationPicker] = useState(false);
  const [nowMode, setNowMode] = useState<"service" | "delivery">("service");
  const [activeTask, setActiveTask] = useState<StaffTask | null>(null);
  const [serviceCount, setServiceCount] = useState<number | null>(null);
  const [historyRequest, setHistoryRequest] = useState(0);
  const [openingAt, setOpeningAt] = useState<Table | null>(null);
  const [newLabel, setNewLabel] = useState("");
  const [takeoverAt, setTakeoverAt] = useState<Table | null>(null);
  const [error, setError] = useState(""), [message, setMessage] = useState(""), [updated, setUpdated] = useState("");
  useEffect(() => {
    try {
      const prefix = `rodada:table-service:${session.venue.id}:${session.staff.id}:`;
      if (Object.keys(localStorage).some(key => key.startsWith(prefix) && key !== storageKey)) {
        setRecoveryBlocked(true); setError("Atendimento pendente de outra sessão preservado. Peça à gerência para conferir o histórico antes de repetir.");
      }
      const stored = localStorage.getItem(storageKey); if (stored) setIntent(JSON.parse(stored));
    }
    catch { setRecoveryBlocked(true); setError("Recuperação indisponível. Confira o histórico antes de repetir."); }
  }, [storageKey]);
  const [tableDialog, setTableDialog] = useState<{id: string; release: boolean} | null>(null);
  const [moveSelection, setMoveSelection] = useState<MoveSelection | null>(null);
  const [moveLocked, setMoveLocked] = useState(true);
  const closeMove = useCallback(() => setMoveSelection(null), []);
  const [pendingOrder, setPendingOrder] = useState(false);
  const [tableSearch, setTableSearch] = useState("");
  const [tableSelection, setTableSelection] = useState<TableTabSelection | null>(null);
  const [tableOpening, setTableOpening] = useState(false);
  const openingTableRequest = useRef(0);
  const [workspaceReturnFocus, setWorkspaceReturnFocus] = useState<HTMLElement | null>(null);
  const tableOpeningLock = useRef(false);

  const [screen, setScreen] = useState("now"), [busy, setBusy] = useState(false), [online, setOnline] = useState(false), [loading, setLoading] = useState(true);
  const [tables, setTables] = useState<Table[]>([]), [deliveries, setDeliveries] = useState<Delivery[]>([]), [tabs, setTabs] = useState<Tab[]>([]), [zones, setZones] = useState<{ id: string; label: string }[]>([]);
  const refreshInFlight = useRef<Promise<void> | null>(null);
  const refresh = useCallback(async (expected?: { tableId: string; status: string }, afterMutation = false) => {
    while (refreshInFlight.current) {
      await refreshInFlight.current.catch(() => {});
      if (!expected && !afterMutation) return;
    }
    const pending = (async () => {
    try {
      const [tableList, queue, zoneList] = await Promise.all([request<{ results: Table[]; table_service_enabled: boolean }>("hospitality/tables/"), request<{ results: Delivery[] }>("dispatch/delivery/"), request<{ results: { id: string; label: string }[] }>("hospitality/zones/")]);
      const allTabs: Tab[] = [];
      let offset: number | null = 0;
      do { const page: { results: Tab[]; next_offset?: number | null } = await request(`tabs/?active=true&summary=true&offset=${offset}`); allTabs.push(...page.results); offset = page.next_offset ?? null; } while (offset !== null);
      setServiceEnabled(tableList.table_service_enabled === true); setTables(tableList.results); setDeliveries(queue.results); setZones(zoneList.results); setTabs(allTabs); setOnline(true); setUpdated(new Date().toLocaleTimeString("pt-BR"));
      if (expected && !tableList.results.some(table => table.id === expected.tableId && table.status === expected.status)) throw new Error("O estado da mesa mudou. Atualize antes de continuar.");
    } catch (failure) { setOnline(false); setError(failure instanceof Error ? failure.message : "Não foi possível atualizar."); if (expected) throw failure; }
    finally { setLoading(false); }
    })();
    refreshInFlight.current = pending;
    try { await pending; } finally { if (refreshInFlight.current === pending) refreshInFlight.current = null; }
  }, []);
  useEffect(() => { void refresh(); const timer = setInterval(() => void refresh(), 15000); return () => clearInterval(timer); }, [refresh]);
  function openTableTab(table: Table, tab: Tab) {
    if (tableOpeningLock.current || busy || moveLocked || pendingOrder || !online || !table.active_occupancy) return;
    setWorkspaceReturnFocus(document.activeElement as HTMLElement | null);
    tableOpeningLock.current = true; setTableOpening(true); setError(""); setMessage("");
    setTableSelection({ requestId: ++openingTableRequest.current, tabId: tab.id, tableId: table.id, tableLabel: table.label, occupancyId: table.active_occupancy.id });
  }
  const tableSelectionResult = useCallback((failure: string | null, selection: TableTabSelection) => {
    if (selection.requestId !== openingTableRequest.current) return;
    tableOpeningLock.current = false; setTableOpening(false);
    if (failure) { setError(failure); return; }
    setScreen("tables");
  }, [setError]);
  const revealOrder = useCallback(() => setScreen("tables"), []);
  const closeOrder = useCallback(() => { void refresh(); }, [refresh]);
  const normalizeTable = (value: string) => normalizeCatalogSearch(value).replace(/^mesa\s*/, "").replace(/\s+/g, " ");
  const tableQuery = normalizeTable(tableSearch);
  const visibleTables = tables.filter(table => (normalizeTable(table.label).includes(tableQuery) || table.active_occupancy?.tabs?.some(tab => normalizeCatalogSearch(`${tab.display_label} ${tab.display_reference || tabReference(tab)}`).includes(normalizeCatalogSearch(tableSearch)))));
  useRealtime(refresh, { onRevoked: () => setOnline(false) });
  async function command(path: string, payload: object = {}, expected?: { tableId: string; status: string }) {
    if (busy || moveLocked || !online || intent || recoveryBlocked || pendingOrder) return;
    setBusy(true); setError(""); setMessage("");
    try { await request(path, payload); await refresh(expected, true); setMessage("Operação confirmada."); return true; }
    catch (failure) { setError(failure instanceof Error ? failure.message : "Não foi possível concluir."); return false; }
    finally { setBusy(false); }
  }
  function openExisting(table: Table, tabId: string) {
    const tab = table.active_occupancy?.tabs?.find(row => row.id === tabId);
    if (tab) openTableTab(table, tab);
  }
  async function serviceCommand(path?: string, payload: Record<string, unknown> = {}) {
    if (busy || !online || pendingOrder || recoveryBlocked) return;
    const next = intent ?? { path: path!, payload: { ...payload, idempotency_key: crypto.randomUUID() } };
    setBusy(true); setError(""); setMessage("");
    try {
      localStorage.setItem(storageKey, JSON.stringify(next)); setIntent(next);
      const result = await request<{ tab_id?: string; table_id?: string; table_label?: string }>(next.path, next.payload);
      localStorage.removeItem(storageKey); setIntent(null); setMessage("Operação confirmada.");
      if (result.tab_id) { setRequestedTab(current => ({ id: result.tab_id!, sequence: (current?.sequence ?? 0) + 1, destination: result.table_label ? `Mesa ${result.table_label}` : "Comanda" })); setScreen("tables"); if (result.table_id) setSelectedTable(result.table_id); setOpeningAt(null); }
      else if (result.table_id) { setSelectedTable(result.table_id); setScreen("tables"); }
      setTakeoverAt(null); setMoving(null); await refresh(undefined, true);
    } catch (failure) {
      const status = (failure as { status?: number }).status;
      if (status && [400, 404, 409, 422].includes(status)) { localStorage.removeItem(storageKey); setIntent(null); await refresh(undefined, true); }
      setError(failure instanceof Error ? failure.message : "Resultado desconhecido. Verifique a mesma intenção.");
    } finally { setBusy(false); }
  }
  async function openTask(id: string) {
    if (busy || pendingOrder || intent || recoveryBlocked) return;
    setBusy(true); setError("");
    try {
      const task = await request<StaffTask>(`dispatch/tasks/${id}/`);
      if (!["OPEN", "CLAIMED"].includes(task.state)) throw new Error("Esta tarefa já mudou. Atualize a fila.");
      if (task.task_type === "DELIVERY") { setActiveTask(task); return; }
      const list = await request<{results: Table[]}>("hospitality/tables/");
      setTables(list.results);
      const target = currentTaskTarget(task, list.results);
      if (!target) throw new Error("Vínculo desatualizado. Atualize a fila e confira o destino.");
      if (target.kind === "TABLE") { setSelectedTable(target.table_id); setScreen("tables"); return; }
      if (target.table_id) {
        const table = list.results.find(row => row.id === target.table_id)!;
        setWorkspaceReturnFocus(document.activeElement as HTMLElement | null);
        tableOpeningLock.current = true; setTableOpening(true);
        setTableSelection({requestId: ++openingTableRequest.current, tabId: target.tab_id!, tableId: table.id, tableLabel: table.label, occupancyId: target.occupancy_id!});
      } else setRequestedTab(current => ({id: target.tab_id!, sequence: (current?.sequence ?? 0) + 1, destination: "Sem mesa"}));
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Não foi possível abrir a tarefa."); }
    finally { setBusy(false); }
  }
  function claim(table: Table) {
    const occupancy = table.active_occupancy!;
    if (occupancy.responsible_staff_id && occupancy.responsible_staff_id !== session.staff.id) { setTakeoverAt(table); return; }
    void serviceCommand(`hospitality/occupancies/${occupancy.id}/responsibility/claim/`, { expected_responsibility_version: occupancy.responsibility_version, mode: "CLAIM_UNASSIGNED" });
  }
  const assignedTabs = new Set(tables.flatMap(table => table.active_occupancy?.tabs?.map(tab => tab.id) || []));
  const otherTabs = tabs.filter(tab => !assignedTabs.has(tab.id) &&
    (!tableSearch.trim() || normalizeCatalogSearch(`${tab.display_label} ${tabReference(tab)} ${tab.table_label || ""}`).includes(normalizeCatalogSearch(tableSearch))));
  const attention = tables.filter(table => ["UNASSIGNED_GUEST_ORDER", "UNASSIGNED_READY"].includes(table.active_occupancy?.unassigned_service_attention || "")).sort((a, b) => Number(b.active_occupancy?.unassigned_service_attention === "UNASSIGNED_READY") - Number(a.active_occupancy?.unassigned_service_attention === "UNASSIGNED_READY") || (a.active_occupancy?.oldest_unassigned_guest_order_at || "").localeCompare(b.active_occupancy?.oldest_unassigned_guest_order_at || ""));
  function serviceInfo(table: Table) {
    const occupancy = table.active_occupancy;
    if (!occupancy) return null;
    const urgent = ["UNASSIGNED_GUEST_ORDER", "UNASSIGNED_READY"].includes(occupancy.unassigned_service_attention || "");
    return <div className={urgent ? "notice" : "muted"} data-state={urgent ? "warning" : undefined}>
      <p>{urgent ? "Pedido via QR · Sem responsável" : occupancy.responsible_staff ? `Atendimento: ${occupancy.responsible_staff_id === session.staff.id ? "você" : occupancy.responsible_staff.display_name}` : "Sem responsável"}</p>
      {urgent && <p>{occupancy.unassigned_guest_order_count} pedido(s) · {occupancy.unassigned_service_attention === "UNASSIGNED_READY" ? "Pedido pronto · " : ""}{occupancy.oldest_unassigned_guest_order_at ? `Desde ${new Date(occupancy.oldest_unassigned_guest_order_at).toLocaleTimeString("pt-BR")}` : ""}</p>}
      {occupancy.responsible_staff_id !== session.staff.id && serviceEnabled && session.capabilities.includes("table.manage") && <button className="buttonSecondary" disabled={busy || !online || !!intent || recoveryBlocked || pendingOrder} onClick={() => claim(table)}>Assumir atendimento{occupancy.responsible_staff ? ` de ${occupancy.responsible_staff.display_name}` : ""}</button>}
    </div>;
  }
  return <main className="appShell attendanceShell ux2Shell">
    <header className="ux2Header"><img src="/brand/wordmark.svg" alt="Rodada" width="113" height="42" /><div className="ux2Meta"><b>{session.venue.name}</b><span>{loading ? "Atualizando…" : online ? session.staff.display_name : "Desatualizado · verifique a conexão"}</span></div></header>
    <div className="ux2Content">
    {error && !selectedTable && <p className="notice" data-state="danger" role="alert">{error}</p>}{message && !selectedTable && <p className="notice" data-state="success" role="status">{message}</p>}
    {intent && !openingAt && !takeoverAt && !moving && <div className="notice" data-state="warning" role="status"><p>Verificando atendimento. A intenção original está preservada.</p><button className="buttonPrimary" disabled={busy || !online || recoveryBlocked || pendingOrder} onClick={() => void serviceCommand()}>Verificar mesma intenção</button></div>}
    {screen === "now" && <section className="ux2Now">
      <div className="ux2Eyebrow">Fila operacional</div><h1>Agora</h1>
      <div className="ux2NowSwitch" role="group" aria-label="Tipo de trabalho"><button aria-pressed={nowMode === "service"} onClick={() => setNowMode("service")}>Atendimentos <span>{serviceCount ?? "—"}</span></button><button aria-pressed={nowMode === "delivery"} onClick={() => setNowMode("delivery")}>Entregas <span>{online ? deliveries.length : "—"}</span></button></div>
      <div hidden={nowMode !== "service"}><ServiceRequestQueue staffId={session.staff.id} ux2 onCountChange={setServiceCount} onOpenTask={id => void openTask(id)} />
      {attention.map(table => <article className="ux2Attention" key={table.active_occupancy!.id}><h3>Mesa {table.label}</h3>{serviceInfo(table)}<button className="buttonSecondary" disabled={busy || pendingOrder || !!intent || recoveryBlocked} onClick={() => { setSelectedTable(table.id); setScreen("tables"); }}>Ver mesa</button></article>)}</div>
      <div hidden={nowMode !== "delivery"}><div className="ux2QueueHead"><h2>Prontos para levar</h2></div><p className="ux2Summary">Fila separada do atendimento. Itens confirmados pelo Bar e pela Cozinha.</p>{loading ? <p role="status">Carregando entregas…</p> : !deliveries.length && online ? <div className="ux2Empty">Nenhuma tarefa nesta fila. Selecione a outra categoria para conferir.</div> : deliveries.map(delivery => <article className="ux2QueueItem" key={delivery.id}><div className="ux2QueueTop"><span className="ux2Delivery">PEDIDO PRONTO</span><span>· {Math.floor(delivery.age_seconds / 60)} min</span></div><strong className="ux2QueueTitle">{delivery.quantity || 1}× {delivery.product_name}</strong><div className="ux2QueueDetail"><span>{delivery.destination_label || "Sem mesa"} · {delivery.tab_label || "Comanda"}</span></div><button className="ux2QueueOpen" disabled={busy || pendingOrder || !!intent || recoveryBlocked || !online} onClick={() => void openTask(delivery.id)}>Ver entrega ›</button></article>)}</div>
    </section>}
    <OrderWorkspace returnFocus={workspaceReturnFocus} tableMode onOpenFailure={setError} tableSelection={tableSelection} onTableSelectionResult={tableSelectionResult} onRecoveryNeeded={revealOrder} onDialogClose={closeOrder} withoutPayments recoveryScope={`${session.venue.id}:${session.staff.id}:${session.session.id}`} onPendingChange={setPendingOrder} requestedTabId={requestedTab?.id} requestedTabSequence={requestedTab?.sequence} destinationLabel={requestedTab?.destination} createRequest={createRequest} historyRequest={historyRequest} />
    {screen === "tables" && <section className="panel"><div className="attendanceUnifiedHeading"><OperationalHeading as="h2" icon="table">Mesas e comandas</OperationalHeading><button className="buttonQuiet" aria-label="Histórico" disabled={busy || pendingOrder || !!intent || recoveryBlocked} onClick={() => setHistoryRequest(current => current + 1)}><OperationalIcon name="history" size={20} /></button></div><div className="field"><label htmlFor="attendance-table-search">Buscar mesa ou comanda</label><input id="attendance-table-search" type="search" value={tableSearch} onChange={event => setTableSearch(event.target.value)} /></div><div className="attendanceTableGrid">{loading ? <p role="status">Carregando mesas…</p> : !tables.length && online ? <p className="muted">Nenhuma mesa cadastrada.</p> : !online && !tables.length ? <p className="muted" role="status">Mesas indisponíveis. Atualize para tentar novamente.</p> : !visibleTables.length ? <p className="muted" role="status">Nenhuma mesa encontrada. Ajuste a busca.</p> : visibleTables.map(table => <article className="attendanceTable" data-state={table.status} key={table.id}><h3 tabIndex={-1} id={`attendance-table-${table.id}`}><button className="buttonSecondary attendanceTableSummary" aria-haspopup="dialog" disabled={busy || !!intent || pendingOrder || tableOpening} onClick={() => setSelectedTable(table.id)}><span className="attendanceTableNumber"><OperationalIcon name="table" /><span>Mesa {table.label}</span></span><small>{labels[table.status] || table.status} · {table.active_occupancy?.tabs?.filter(tab => !["CLOSED", "CANCELLED"].includes(tab.state || "")).length || 0} comandas abertas{table.zone && <> · {table.zone.label}</>}</small><OperationalIcon name="chevron-right" size={20} /></button></h3>{selectedTable === table.id && <ActionDialog title={`Mesa ${table.label}`} dialogClassName="attendanceTableDialog" dismissOnBackdrop locked={busy || moveLocked || tableOpening || !!intent || pendingOrder} onClose={() => setSelectedTable(null)}><p className="muted">{labels[table.status] || table.status}{table.zone && <> · {table.zone.label}</>}</p>{error && <p className="notice" data-state="danger" role="alert">{error}</p>}{message && <p className="notice" data-state="success" role="status">{message}</p>}{["DIRTY", "CLEANING"].includes(table.status) ? <button className="buttonPrimary" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onClick={() => void command(`hospitality/tables/${table.id}/cleaning/complete/`, {}, { tableId: table.id, status: "AVAILABLE" }).then(ok => { if (ok) setSelectedTable(null); })}>Concluir limpeza</button> : <>
{serviceInfo(table)}{table.active_occupancy && <><p>{table.active_occupancy.tabs?.length || 0} comandas</p>{table.active_occupancy.tabs?.filter(tab => !["CLOSED", "CANCELLED"].includes(tab.state || "")).map(tab => <div key={tab.id}><button data-tab-id={tab.id} className="buttonSecondary" key={tab.id} disabled={busy || pendingOrder || !!intent || recoveryBlocked || ["CLOSED", "CANCELLED"].includes(tab.state || "")} onClick={() => openExisting(table, tab.id)}>{tab.display_label || "Comanda sem nome"} · {tab.display_reference || tabReference(tab)}</button>{session.capabilities.includes("tab.move") && <button className="buttonSecondary attendanceMoveButton" disabled={busy || moveLocked || pendingOrder || tableOpening || !online || !!intent || recoveryBlocked} onClick={() => setMoveSelection({ table, tab })}><OperationalIcon name="chevron-right" size={20} />Mover comanda</button>}</div>)}{serviceEnabled && session.capabilities.includes("tab.open") && <button className="buttonPrimary" disabled={busy || pendingOrder || !!intent || recoveryBlocked || !online} onClick={event => { setWorkspaceReturnFocus(event.currentTarget); setNewLabel(""); setOpeningAt(table); }}>Nova comanda nesta mesa</button>}</>}<button className="buttonQuiet" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onClick={() => setTableDialog({ id: table.id, release: false })}>Organizar mesa {table.label}</button>{tableDialog?.id === table.id && !tableDialog.release && <ActionDialog title={`Organizar mesa ${table.label}`} locked={busy} onClose={() => setTableDialog(null)}>{error && <p className="notice" role="alert" data-state="danger">{error}</p>}{message && <p className="notice" role="status" data-state="success">{message}</p>}<div className="field"><label htmlFor={`zone-${table.id}`}>Localização da mesa {table.label}</label><select id={`zone-${table.id}`} value={table.zone?.id || ""} disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onChange={event => void command(`hospitality/tables/${table.id}/location/`, { zone_id: event.target.value || null })}><option value="">Sem zona</option>{zones.map(zone => <option key={zone.id} value={zone.id}>{zone.label}</option>)}</select></div>{table.active_occupancy && <div className="field"><label htmlFor={`attach-${table.id}`}>Associar comanda à mesa {table.label}</label><select id={`attach-${table.id}`} value="" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onChange={event => {
  const tab = tabs.find(row => row.id === event.target.value); if (!tab) return;
  const origin = tables.find(row => row.active_occupancy?.tabs?.some(link => link.id === tab.id));
  if (origin) { setTableDialog(null); setMoving({ table, tab, origin: `Mesa ${origin.label}` }); }
  else void command(`hospitality/occupancies/${table.active_occupancy!.id}/tabs/`, { tab_id: tab.id });
}}><option value="">Selecionar comanda</option>{tabs.filter(tab => !table.active_occupancy?.tabs?.some(link => link.id === tab.id) && (!assignedTabs.has(tab.id) || session.capabilities.includes("tab.move"))).map(tab => <option key={tab.id} value={tab.id}>{tabPrimaryLabel(tab)} · {tabReference(tab)}{assignedTabs.has(tab.id) ? ` · Mesa ${tables.find(row => row.active_occupancy?.tabs?.some(link => link.id === tab.id))?.label} · Mover` : " · Sem mesa"}</option>)}</select></div>}</ActionDialog>}
      {table.status === "AVAILABLE" && serviceEnabled && session.capabilities.includes("tab.open") && session.capabilities.includes("table.manage") && <button className="buttonPrimary" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onClick={event => { setWorkspaceReturnFocus(event.currentTarget); setNewLabel(""); setOpeningAt(table); }}>Nova comanda nesta mesa</button>}
      {table.status === "AVAILABLE" && !serviceEnabled && session.capabilities.includes("table.manage") && <button className="buttonPrimary" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onClick={() => void command(`hospitality/tables/${table.id}/occupy/`)}>Ocupar mesa</button>}
      {table.status === "OCCUPIED" && <><p className="muted">Liberar encerra o acesso por QR. As comandas permanecem abertas.</p><button className="buttonSecondary" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onClick={() => { setError(""); setMessage(""); setTableDialog({id: table.id, release: true}); }}>Liberar mesa {table.label}</button></>}
      {tableDialog?.id === table.id && tableDialog.release && <ActionDialog title={`Liberar mesa ${table.label}?`} locked={busy} onClose={() => setTableDialog(null)}><p>O acesso por QR será encerrado. As comandas permanecem abertas.</p>{error && <p className="notice" role="alert" data-state="danger">{error}</p>}<button className="buttonSecondary" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onClick={() => void command(`hospitality/tables/${table.id}/release/`, {}, { tableId: table.id, status: "DIRTY" }).then(ok => { if (ok) { setTableDialog(null); setSelectedTable(null); } })}>Confirmar liberação</button></ActionDialog>}
      {table.status === "DIRTY" && <button className="buttonPrimary" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onClick={() => void command(`hospitality/tables/${table.id}/cleaning/start/`)}>Iniciar limpeza</button>}
      {table.status === "CLEANING" && <button className="buttonPrimary" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onClick={() => void command(`hospitality/tables/${table.id}/cleaning/complete/`)}>Concluir limpeza</button>}


    </>}</ActionDialog>}</article>)}</div></section>}
    {screen === "tables" && <section className="panel" aria-label="Outras comandas"><details open={tableSearch.trim() ? true : undefined}><summary>Outras comandas ({otherTabs.length})</summary><p className="muted">Comandas fora das ocupações listadas acima.</p>{tableSearch.trim() && !otherTabs.length && <p>Nenhuma outra comanda corresponde à busca.</p>}{otherTabs.map(tab => <button className="buttonSecondary attendanceTabOption" data-tab-id={tab.id} key={tab.id} disabled={busy || moveLocked || pendingOrder || !online || !!intent || recoveryBlocked} onClick={event => { setWorkspaceReturnFocus(event.currentTarget); setRequestedTab(current => ({ id: tab.id, sequence: (current?.sequence ?? 0) + 1, destination: tab.table_label ? `Mesa ${tab.table_label}` : "Comanda" })); }}>{tab.display_label || tabReference(tab)} · {tabReference(tab)}</button>)}{!serviceEnabled && session.capabilities.includes("tab.open") && <button className="buttonPrimary" disabled={busy || moveLocked || pendingOrder || !online || !!intent || recoveryBlocked} onClick={event => { setWorkspaceReturnFocus(event.currentTarget); setCreateRequest(current => current + 1); }}>Abrir comanda sem mesa</button>}</details></section>}
    {moving?.table.active_occupancy && <ActionDialog title="Mover comanda?" locked={busy || !!intent} onClose={() => setMoving(null)}>
      <p>{tabPrimaryLabel(moving.tab)} · {tabReference(moving.tab)}: {moving.origin} → Mesa {moving.table.label}. O saldo permanece nesta comanda.</p>
      <button className="buttonPrimary" disabled={busy || !!intent || !online} onClick={() => {
        setBusy(true);
        void request<{ version: number }>(`tabs/${moving.tab.id}/`).then(detail => {
          setBusy(false);
          return serviceCommand(`tabs/${moving.tab.id}/operations/`, { kind: "MOVE_LOCATION", expected_version: detail.version, occupancy_id: moving.table.active_occupancy!.id });
        }).catch(failure => { setBusy(false); setError(failure.message); });
      }}>Confirmar mudança de mesa</button>
      {intent && <button className="buttonPrimary" disabled={busy || !online} onClick={() => void serviceCommand()}>Verificar mesma intenção</button>}
    </ActionDialog>}
    {openingAt && <ActionDialog title={`Nova comanda · Mesa ${openingAt.label}`} locked={busy || !!intent} onClose={() => setOpeningAt(null)}>
      <div className="field"><label htmlFor="contextual-tab-name">Nome ou apelido</label><input id="contextual-tab-name" required maxLength={120} value={newLabel} disabled={busy || !!intent} onChange={event => setNewLabel(event.target.value)} /></div>
      {error && <p className="notice" role="alert" data-state="danger">{error}</p>}
      <button className="buttonPrimary" disabled={busy || !!intent || !online || recoveryBlocked || pendingOrder || !newLabel.trim()} onClick={() => void serviceCommand(openingAt.active_occupancy ? `hospitality/occupancies/${openingAt.active_occupancy.id}/tabs/open/` : `hospitality/tables/${openingAt.id}/service/open-tab/`, { display_label: newLabel.trim(), ...(openingAt.active_occupancy ? { expected_generation: openingAt.active_occupancy.generation } : {}) })}>Abrir e pedir</button>
      {intent && <button className="buttonPrimary" disabled={busy || !online || recoveryBlocked || pendingOrder} onClick={() => void serviceCommand()}>Verificar mesma intenção</button>}
    </ActionDialog>}
    {takeoverAt?.active_occupancy && <ActionDialog title="Assumir atendimento?" locked={busy || !!intent} onClose={() => setTakeoverAt(null)}><p>{takeoverAt.active_occupancy.responsible_staff?.display_name} está responsável. Você também pode atender sem assumir.</p><button className="buttonPrimary" disabled={busy || !!intent || !online} onClick={() => void serviceCommand(`hospitality/occupancies/${takeoverAt.active_occupancy!.id}/responsibility/claim/`, { expected_responsibility_version: takeoverAt.active_occupancy!.responsibility_version, mode: "TAKE_OVER" })}>Confirmar transferência de atendimento</button>{intent && <button className="buttonPrimary" disabled={busy || !online} onClick={() => void serviceCommand()}>Verificar mesma intenção</button>}<button className="buttonSecondary" disabled={busy || !!intent} onClick={() => setTakeoverAt(null)}>Atender sem assumir</button></ActionDialog>}
  <TabLocationMove selection={moveSelection} tables={tables} onClose={closeMove} onLockChange={setMoveLocked} onConfirmed={() => refresh(undefined, true)} />
    </div><nav className="ux2BottomNav" aria-label="Navegação principal"><button aria-current={screen === "now" ? "page" : undefined} disabled={busy || tableOpening || pendingOrder || !!intent} onClick={() => setScreen("now")}><span className="ux2Glyph">◷</span>Agora</button><button className="ux2Middle" disabled={busy || moveLocked || tableOpening || pendingOrder || !!intent || recoveryBlocked} onClick={() => setDestinationPicker(true)}><span className="ux2Glyph">＋</span>Pedir</button><button aria-current={screen === "tables" ? "page" : undefined} disabled={busy || tableOpening || pendingOrder || !!intent} onClick={() => setScreen("tables")}><span className="ux2Glyph">▦</span>Mesas</button></nav>
    {activeTask && <ActionDialog title="Entrega pronta" onClose={() => setActiveTask(null)}><p>{activeTask.quantity}× {activeTask.product_name}</p><p>{activeTask.fulfillment_station === "BAR" ? "Bar" : activeTask.fulfillment_station === "KITCHEN" ? "Cozinha" : "Estação não informada"} · {activeTask.destination_label || "Sem mesa"}</p><p>Abrir esta entrega não altera o estado do pedido.</p><button className="buttonSecondary" disabled={busy || !online || !!intent || pendingOrder} onClick={() => void command(`dispatch/delivery/${activeTask.id}/complete/`).then(ok => { if (ok) setActiveTask(null); })}>Registrar entrega por exceção</button></ActionDialog>}
    {destinationPicker && <ActionDialog title="Onde vamos pedir?" onClose={() => setDestinationPicker(false)}><p>Selecione uma mesa ou comanda para adicionar itens.</p><button className="buttonPrimary" onClick={() => { setDestinationPicker(false); setScreen("tables"); }}>Escolher mesa ou comanda</button>{session.capabilities.includes("tab.open") && <button className="buttonSecondary" onClick={event => { setWorkspaceReturnFocus(event.currentTarget); setDestinationPicker(false); setCreateRequest(current => current + 1); }}>Nova comanda sem mesa</button>}</ActionDialog>}
  </main>;
}
