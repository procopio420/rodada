"use client";

import "./attendance-ux2.css";
import Image from "next/image";
import { money } from "./product-customization";
import { currentTaskTarget, type StaffTask } from "@/lib/client/dispatch-target";
import { OperationalIcon } from "@/components/operational-icon";
import { tabPrimaryLabel, tabReference } from "@/lib/client/tab-identity";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRealtime } from "@/lib/client/use-realtime";
import { StaffAuthScreen } from "@/components/staff-auth-screen";
import { normalizeCatalogSearch } from "@/lib/client/attendance-catalog";
import { AttendanceTaskContext } from "@/components/attendance-task-context";
import { OrderWorkspace, type TableTabSelection } from "@/components/order-workspace";
import { ServiceRequestQueue } from "@/components/service-request-queue";
import { ActionDialog } from "@/components/action-dialog";
import { TabLocationMove, type MoveSelection } from "@/components/tab-location-move";

import { apiCall, asApiError, type StaffSessionView } from "@/lib/client/staff-auth";

type Occupancy = { id: string; generation: number; responsibility_version: number; responsible_staff_id: string | null; responsible_staff?: { id: string; display_name: string }; unassigned_service_attention?: string; unassigned_guest_order_count?: number; oldest_unassigned_guest_order_at?: string; tabs?: { id: string; display_label: string; display_reference?: string; opened_at?: string; state?: string }[] };
type Table = { id: string; label: string; status: string; zone?: { id: string; label: string }; active_occupancy?: Occupancy };
type ServiceIntent = { path: string; payload: Record<string, unknown> };
type Delivery = StaffTask & { id: string; product_name: string; quantity: number; tab_label: string; destination_label: string; age_seconds: number };
type Tab = { id: string; display_label: string; table_label?: string | null; last_table_label?: string | null; exposure_cents?: number };
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
  const [operatorMenu, setOperatorMenu] = useState(false);
  const storageKey = `rodada:table-service:${session.venue.id}:${session.staff.id}:${session.session.id}`;
  const [serviceEnabled, setServiceEnabled] = useState(false);
  const [orderContext, setOrderContext] = useState<{tabId: string; surface: string} | null>(null);
  const contextChanged = useCallback((context: {tabId: string; surface: string} | null) => setOrderContext(context), []);
  const [requestedSurface, setRequestedSurface] = useState<"tab" | "bill" | "catalog">("tab");
  const [originTaskType, setOriginTaskType] = useState<string | null>(null);
  const [pickingOrder, setPickingOrder] = useState(false);
  const [moving, setMoving] = useState<{ table: Table; tab: Tab; origin: string } | null>(null);
  const [recoveryBlocked, setRecoveryBlocked] = useState(false);
  const [intent, setIntent] = useState<ServiceIntent | null>(null);
  const tableReturnFocus = useRef<HTMLElement | null>(null);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  useEffect(() => { if (selectedTable) document.getElementById(`ux2-table-title-${selectedTable}`)?.focus(); }, [selectedTable]);
  function leaveTable() { clearTaskOrigin(); setSelectedTable(null); requestAnimationFrame(() => tableReturnFocus.current?.focus()); }
  const [requestedTab, setRequestedTab] = useState<{ id: string; sequence: number; destination: string } | null>(null);
  const [createRequest, setCreateRequest] = useState(0);
  const [destinationPicker, setDestinationPicker] = useState(false);
  const [nowMode, setNowMode] = useState<"service" | "delivery">("service");
  const orderOrigin = useRef<{ screen: "now" | "tables"; tableId: string | null }>({ screen: "tables", tableId: null });
  const [originTaskId, setOriginTaskId] = useState<string | null>(null);
  const [originTabId, setOriginTabId] = useState<string | null>(null);
  const clearTaskOrigin = useCallback(() => { setOriginTaskId(null); setOriginTabId(null); setOriginTaskType(null); }, []);
  const [closeContextRequest, setCloseContextRequest] = useState(0);
  const [activeTask, setActiveTask] = useState<StaffTask | null>(null);
  const [serviceCount, setServiceCount] = useState<number | null>(null);
  const [historyRequest, setHistoryRequest] = useState(0);
  const [openingAt, setOpeningAt] = useState<Table | null>(null);
  const [newLabel, setNewLabel] = useState("");
  const [takeoverAt, setTakeoverAt] = useState<Table | null>(null);
  const [error, setError] = useState(""), [message, setMessage] = useState(""), [, setUpdated] = useState("");
  const failOrderOpen = useCallback((failure: string) => { setOriginTaskId(null); setOriginTabId(null); setOriginTaskType(null); setError(failure); }, [setError]);
  useEffect(() => {
    let active = true;
    queueMicrotask(() => {
    if (!active) return;
    try {
      const prefix = `rodada:table-service:${session.venue.id}:${session.staff.id}:`;
      if (Object.keys(localStorage).some(key => key.startsWith(prefix) && key !== storageKey)) {
        setRecoveryBlocked(true); setError("Atendimento pendente de outra sessão preservado. Peça à gerência para conferir o histórico antes de repetir.");
      }
      const stored = localStorage.getItem(storageKey); if (stored) setIntent(JSON.parse(stored));
    }
    catch { setRecoveryBlocked(true); setError("Recuperação indisponível. Confira o histórico antes de repetir."); }
    });
    return () => { active = false; };
  }, [storageKey, session.venue.id, session.staff.id]);
  const [tableDialog, setTableDialog] = useState<{id: string; release: boolean; occupancyId?: string; generation?: number} | null>(null);
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
  }, [setError]);
  useEffect(() => { void refresh(); const timer = setInterval(() => void refresh(), 15000); return () => clearInterval(timer); }, [refresh]);
  function openTableTab(table: Table, tab: Tab) {
    if (tableOpeningLock.current || busy || moveLocked || pendingOrder || !online || !table.active_occupancy) return;
    if (originTaskId && orderOrigin.current.screen === "now") { setOriginTabId(tab.id); setRequestedSurface(originTaskType === "BILL_REQUEST" ? "bill" : "tab"); }
    else { clearTaskOrigin(); setRequestedSurface(pickingOrder ? "catalog" : "tab"); orderOrigin.current = {screen:"tables",tableId:table.id}; }
    setPickingOrder(false);
    setWorkspaceReturnFocus(document.activeElement as HTMLElement | null);
    tableOpeningLock.current = true; setTableOpening(true); setError(""); setMessage("");
    setTableSelection({ requestId: ++openingTableRequest.current, tabId: tab.id, tableId: table.id, tableLabel: table.label, occupancyId: table.active_occupancy.id });
  }
  const tableSelectionResult = useCallback((failure: string | null, selection: TableTabSelection) => {
    if (selection.requestId !== openingTableRequest.current) return;
    tableOpeningLock.current = false; setTableOpening(false);
    if (failure) { failOrderOpen(failure); return; }
    setScreen("tables");
  }, [failOrderOpen, setScreen]);
  const revealOrder = useCallback(() => setScreen("tables"), [setScreen]);
  const closeOrder = useCallback(() => { clearTaskOrigin(); setScreen(orderOrigin.current.screen); setSelectedTable(orderOrigin.current.tableId); void refresh(); }, [refresh, clearTaskOrigin]);
  const normalizeTable = (value: string) => normalizeCatalogSearch(value).replace(/^mesa\s*/, "").replace(/\s+/g, " ");
  const tableQuery = normalizeTable(tableSearch);
  const visibleTables = tables.filter(table => (normalizeTable(table.label).includes(tableQuery) || table.active_occupancy?.tabs?.some(tab => normalizeCatalogSearch(`${tab.display_label} ${tab.display_reference || tabReference(tab)}`).includes(normalizeCatalogSearch(tableSearch)))));
  const displayedTables = selectedTable ? tables.filter(table => table.id === selectedTable) : visibleTables;
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
      if (result.tab_id) { clearTaskOrigin(); setRequestedSurface("tab"); orderOrigin.current = {screen:"tables",tableId:result.table_id || null}; setRequestedTab(current => ({ id: result.tab_id!, sequence: (current?.sequence ?? 0) + 1, destination: result.table_label ? `Mesa ${result.table_label}` : "Comanda" })); setScreen("tables"); if (result.table_id) setSelectedTable(result.table_id); setOpeningAt(null); }
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
      if (task.id !== id) throw new Error("Identidade da tarefa divergente. Atualize a fila.");
      if (!["OPEN", "CLAIMED"].includes(task.state)) throw new Error("Esta tarefa já mudou. Atualize a fila.");
      if (task.task_type === "DELIVERY") { setActiveTask(task); return; }
      const list = await request<{results: Table[]}>("hospitality/tables/");
      setTables(list.results);
      const target = currentTaskTarget(task, list.results);
      if (!target) throw new Error("Vínculo desatualizado. Atualize a fila e confira o destino.");
      orderOrigin.current = { screen: "now", tableId: null };
      setOriginTaskId(task.id); setOriginTaskType(task.task_type); setPickingOrder(false); setRequestedSurface(task.task_type === "BILL_REQUEST" ? "bill" : "tab");
      setOriginTabId(target.kind === "TAB" ? target.tab_id : null);
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
  const [tableBalances, setTableBalances] = useState<Record<string, number>>({});
  useEffect(() => {
    let cancelled = false;
    const table = tables.find(value => value.id === selectedTable);
    const ids = table?.active_occupancy?.tabs?.map(tab => tab.id) || [];
    const context = table?.active_occupancy ? `?${new URLSearchParams({ table_id: table.id, occupancy_id: table.active_occupancy.id })}` : "";
    queueMicrotask(() => { if (!cancelled) setTableBalances({}); });
    // Financial reads only for the selected table, never every Tab in the venue.
    void Promise.all(ids.map(async id => {
      try { const detail = await request<Tab & { id: string }>(`tabs/${id}/${context}`); return detail.id === id && typeof detail.exposure_cents === "number" && Number.isSafeInteger(detail.exposure_cents) ? [id, detail.exposure_cents] as const : null; }
      catch { return null; }
    })).then(values => { if (!cancelled) setTableBalances(Object.fromEntries(values.filter(value => value !== null))); });
    return () => { cancelled = true; };
  }, [selectedTable, tables]);
  function sameReleaseOccupancy(table: Table) {
    return table.status === "OCCUPIED" && !!table.active_occupancy && tableDialog?.occupancyId === table.active_occupancy.id && tableDialog.generation === table.active_occupancy.generation;
  }
  function readyForTable(table: Table) {
    return deliveries.filter(delivery => {
      const target = currentTaskTarget(delivery, tables);
      return target?.table_id === table.id && target.occupancy_id === table.active_occupancy?.id && target.generation === table.active_occupancy?.generation;
    });
  }
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
    <header className="ux2Header"><Image src="/brand/wordmark.svg" alt="Rodada" width="113" height="42" /><button className="ux2Meta ux2OperatorButton" aria-label="Opções do atendimento" aria-haspopup="dialog" disabled={busy || moveLocked || pendingOrder || !!intent} onClick={() => setOperatorMenu(true)}><b>{session.venue.name}</b><span>{loading ? "Atualizando…" : online ? session.staff.display_name : "Desatualizado · verifique a conexão"}</span></button></header>
    <div className={`ux2Content${orderContext ? " ux2ContentWorkspace" : ""}`}>
    {error && !selectedTable && <p className="notice" data-state="danger" role="alert">{error}</p>}{message && !selectedTable && <p className="notice" data-state="success" role="status">{message}</p>}
    {intent && !openingAt && !takeoverAt && !moving && <div className="notice" data-state="warning" role="status"><p>Verificando atendimento. A intenção original está preservada.</p><button className="buttonPrimary" disabled={busy || !online || recoveryBlocked || pendingOrder} onClick={() => void serviceCommand()}>Verificar mesma intenção</button></div>}
    {screen === "now" && !orderContext && <section className="ux2Now">
      <div className="ux2Eyebrow">Fila operacional</div><h1>Agora</h1>
      <div className="ux2NowSwitch" role="group" aria-label="Tipo de trabalho"><button aria-pressed={nowMode === "service"} onClick={() => setNowMode("service")}>Atendimentos <span>{serviceCount ?? "—"}</span></button><button aria-pressed={nowMode === "delivery"} onClick={() => setNowMode("delivery")}>Entregas <span>{online ? deliveries.length : "—"}</span></button></div>
      <div hidden={nowMode !== "service"}><ServiceRequestQueue staffId={session.staff.id} ux2 onCountChange={setServiceCount} onOpenTask={id => void openTask(id)} />
      {attention.map(table => <article className="ux2Attention" key={table.active_occupancy!.id}><h3>Mesa {table.label}</h3>{serviceInfo(table)}<button className="buttonSecondary" disabled={busy || pendingOrder || !!intent || recoveryBlocked} onClick={() => { setSelectedTable(table.id); setScreen("tables"); }}>Ver mesa</button></article>)}</div>
      <div hidden={nowMode !== "delivery"}><div className="ux2QueueHead"><h2>Prontos para levar</h2></div><p className="ux2Summary">Fila separada do atendimento. Itens confirmados pelo Bar e pela Cozinha.</p>{loading ? <p role="status">Carregando entregas…</p> : !deliveries.length && online ? <div className="ux2Empty">Nenhuma tarefa nesta fila. Selecione a outra categoria para conferir.</div> : deliveries.map(delivery => <article className="ux2QueueItem" key={delivery.id}><div className="ux2QueueTop"><span className="ux2Delivery">PEDIDO PRONTO</span><span>· {Math.floor(delivery.age_seconds / 60)} min</span></div><strong className="ux2QueueTitle">{delivery.quantity || 1}× {delivery.product_name}</strong><div className="ux2QueueDetail"><span>{delivery.destination_label || "Sem mesa"} · {delivery.tab_label || "Comanda"}</span></div><button className="ux2QueueOpen" disabled={busy || pendingOrder || !!intent || recoveryBlocked || !online} onClick={() => void openTask(delivery.id)}>Ver entrega ›</button></article>)}</div>
    </section>}
    {originTaskId && selectedTable && !orderContext && <AttendanceTaskContext key={originTaskId} taskId={originTaskId} staffId={session.staff.id} recoveryScope={`${session.venue.id}:${session.staff.id}:${session.session.id}`} navigationLocked={pendingOrder} onBack={() => { if (!pendingOrder) { setSelectedTable(null); setScreen("now"); clearTaskOrigin(); } }} />}
    <OrderWorkspace presentation="ux2" requestedSurface={requestedSurface} onContextChange={contextChanged} closeContextRequest={closeContextRequest} contextualTaskNode={originTaskId && originTabId === orderContext?.tabId ? <AttendanceTaskContext key={originTaskId} taskId={originTaskId} staffId={session.staff.id} recoveryScope={`${session.venue.id}:${session.staff.id}:${session.session.id}`} navigationLocked={pendingOrder} onBack={() => { if (!pendingOrder) { setCloseContextRequest(value => value + 1); setSelectedTable(null); setScreen("now"); clearTaskOrigin(); } }} /> : undefined} returnFocus={workspaceReturnFocus} tableMode onOpenFailure={failOrderOpen} tableSelection={tableSelection} onTableSelectionResult={tableSelectionResult} onRecoveryNeeded={revealOrder} onDialogClose={closeOrder} withoutPayments recoveryScope={`${session.venue.id}:${session.staff.id}:${session.session.id}`} onPendingChange={setPendingOrder} requestedTabId={requestedTab?.id} requestedTabSequence={requestedTab?.sequence} destinationLabel={requestedTab?.destination} createRequest={createRequest} historyRequest={historyRequest} />
    {screen === "tables" && !orderContext && <section className="panel ux2TablesPanel"><div className="ux2TableListIntro" hidden={!!selectedTable}><div className="ux2Eyebrow">Encontrar destino</div><h1>Mesas e<br />comandas.</h1><p className="ux2Lede">Uma busca, sem filtros de status nem formulários na lista.</p></div><div className="attendanceUnifiedHeading" hidden={!!selectedTable}><h2>Mesas</h2><button className="buttonQuiet" aria-label="Histórico" disabled={busy || pendingOrder || !!intent || recoveryBlocked} onClick={() => setHistoryRequest(current => current + 1)}><OperationalIcon name="history" size={20} /></button></div><div className="field ux2TableSearch" hidden={!!selectedTable}><label htmlFor="attendance-table-search" className="ux2SrOnly">Buscar mesa ou comanda</label><span aria-hidden="true">⌕</span><input id="attendance-table-search" type="search" placeholder="Mesa, nome ou comanda" value={tableSearch} onChange={event => setTableSearch(event.target.value)} /></div><div className="attendanceTableGrid" data-context={!!selectedTable}>{loading ? <p role="status">Carregando mesas…</p> : !tables.length && online ? <p className="muted">Nenhuma mesa cadastrada.</p> : !online && !tables.length ? <p className="muted" role="status">Mesas indisponíveis. Atualize para tentar novamente.</p> : !displayedTables.length ? <div className="ux2Empty" role="status">{selectedTable ? "Mesa indisponível. Atualize a lista e confira o destino." : "Nenhuma mesa encontrada. Ajuste a busca."}{selectedTable && <button className="ux2Inline" onClick={() => setSelectedTable(null)}>Voltar às mesas</button>}</div> : displayedTables.map(table => <article className="attendanceTable" data-selected={selectedTable === table.id} data-state={table.status} key={table.id}><h3 tabIndex={-1} id={`attendance-table-${table.id}`}><button className="buttonSecondary attendanceTableSummary" disabled={busy || !!intent || pendingOrder || tableOpening} onClick={event => { tableReturnFocus.current = event.currentTarget; setSelectedTable(table.id); }}><span className="attendanceTableNumber"><OperationalIcon name="table" /><span>Mesa {table.label}</span></span><small className="ux2TableStatus"><i aria-hidden="true" />{labels[table.status] || table.status}</small>{!!table.active_occupancy?.tabs?.filter(tab => !["CLOSED", "CANCELLED"].includes(tab.state || "")).length && <span className="ux2TableCount">{table.active_occupancy.tabs.filter(tab => !["CLOSED", "CANCELLED"].includes(tab.state || "")).length} conta(s)</span>}<OperationalIcon name="chevron-right" size={20} /></button></h3>{selectedTable === table.id && <section className="ux2TablePage" aria-labelledby={`ux2-table-title-${table.id}`}><button className="ux2Back" disabled={busy || tableOpening || !!intent || pendingOrder} onClick={leaveTable}><span aria-hidden="true">‹</span> Voltar</button><div className="ux2Eyebrow">{table.zone?.label || "Salão"}</div><div className="ux2TableContext"><h1 tabIndex={-1} id={`ux2-table-title-${table.id}`}>Mesa {table.label}</h1><span>{table.active_occupancy?.tabs?.filter(tab => !["CLOSED", "CANCELLED"].includes(tab.state || "")).length || 0} aberta(s)</span></div><p className="muted">{labels[table.status] || table.status}{table.zone && <> · {table.zone.label}</>}</p>{error && <p className="notice" data-state="danger" role="alert">{error}</p>}{message && <p className="notice" data-state="success" role="status">{message}</p>}{["DIRTY", "CLEANING"].includes(table.status) && <div className="ux2Lifecycle"><strong>{table.status === "DIRTY" ? "Aguardando limpeza" : "Em limpeza"}</strong><p>{table.status === "DIRTY" ? "A mesa está liberada, mas ainda não está pronta para outro grupo." : "Quando terminar, marque a mesa como pronta."}</p><button className="ux2Button ghost block" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onClick={() => void command(`hospitality/tables/${table.id}/cleaning/${table.status === "DIRTY" ? "start" : "complete"}/`, {}, { tableId: table.id, status: table.status === "DIRTY" ? "CLEANING" : "AVAILABLE" }).then(ok => { if (ok && table.status === "CLEANING") setSelectedTable(null); })}>{table.status === "DIRTY" ? "Iniciar limpeza" : "Mesa limpa · Disponibilizar"}</button></div>}
<div className="ux2SectionHead"><h2>{pickingOrder ? "Qual comanda recebe o pedido?" : "Comandas desta mesa"}</h2></div>
{!table.active_occupancy?.tabs?.length && <p className="ux2Empty">Nenhuma comanda ativa nesta ocupação.</p>}
{table.active_occupancy?.tabs?.filter(tab => tab.state !== "CANCELLED").map(tab => <button data-tab-id={tab.id} className="ux2TabRow" key={tab.id} disabled={busy || pendingOrder || tableOpening || !online || !!intent || recoveryBlocked} onClick={() => openExisting(table, tab.id)}><span><strong>{tab.display_label || "Comanda sem nome"}</strong><small>{tab.display_reference || tabReference(tab)} · Mesa {table.label}{tab.state === "CLOSED" ? " · Encerrada" : ""}</small></span><span className="ux2TabRowAmount">{typeof tableBalances[tab.id] === "number" ? money(tableBalances[tab.id]) : "Ver conta"}<span aria-hidden="true">›</span></span></button>)}
{table.status === "OCCUPIED" && <><div className="ux2SectionHead"><h2>Saída do grupo</h2></div>{table.active_occupancy?.tabs?.some(tab => !["CLOSED", "CANCELLED"].includes(tab.state || "")) ? <div className="ux2Notice" data-state="warning"><strong>{table.active_occupancy.tabs.filter(tab => !["CLOSED", "CANCELLED"].includes(tab.state || "")).length} comanda(s) abertas.</strong> Encerre cada uma para liberar a mesa.</div> : readyForTable(table).length ? <div className="ux2Notice" data-state="warning"><strong>{readyForTable(table).length} entrega(s) ainda prontas.</strong> Resolva as entregas antes de liberar.<button className="ux2Button ghost block" disabled={busy || pendingOrder || !!intent} onClick={() => { setSelectedTable(null); setNowMode("delivery"); setScreen("now"); }}>Ver entregas prontas</button></div> : <><button className="ux2Button primary block" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder || !session.capabilities.includes("table.manage")} onClick={() => { setError(""); setMessage(""); setTableDialog({id: table.id, release: true, occupancyId: table.active_occupancy?.id, generation: table.active_occupancy?.generation}); }}>Grupo saiu · Liberar mesa</button><p className="ux2PaymentHelp">A mesa passará para Aguardando limpeza e o QR desta ocupação perderá o acesso.</p></>}</>}
{serviceEnabled && session.capabilities.includes("tab.open") && (table.status === "OCCUPIED" || session.capabilities.includes("table.manage")) && <button className="ux2Button ghost block ux2NewTableTab" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder || !["AVAILABLE", "OCCUPIED"].includes(table.status)} onClick={event => { setWorkspaceReturnFocus(event.currentTarget); clearTaskOrigin(); setRequestedSurface("tab"); orderOrigin.current = {screen:"tables",tableId:table.id}; setNewLabel(""); setOpeningAt(table); }}>＋ Abrir nova comanda</button>}
<details className="ux2TableOptions"><summary>Opções da mesa</summary>{table.status === "AVAILABLE" && !serviceEnabled && session.capabilities.includes("table.manage") && <button className="buttonPrimary" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onClick={() => void command(`hospitality/tables/${table.id}/occupy/`)}>Ocupar mesa</button>}{serviceInfo(table)}{table.active_occupancy?.tabs?.filter(tab => !["CLOSED", "CANCELLED"].includes(tab.state || "")).map(tab => session.capabilities.includes("tab.move") && <button key={tab.id} className="buttonSecondary attendanceMoveButton" disabled={busy || moveLocked || pendingOrder || tableOpening || !online || !!intent || recoveryBlocked} onClick={() => setMoveSelection({ table, tab })}>Mover comanda · {tab.display_label || tabReference(tab)}</button>)}<button className="buttonQuiet" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onClick={() => setTableDialog({ id: table.id, release: false })}>Organizar mesa {table.label}</button></details>
{tableDialog?.id === table.id && !tableDialog.release && <ActionDialog title={`Organizar mesa ${table.label}`} locked={busy} onClose={() => setTableDialog(null)}>{error && <p className="notice" role="alert" data-state="danger">{error}</p>}{message && <p className="notice" role="status" data-state="success">{message}</p>}<div className="field"><label htmlFor={`zone-${table.id}`}>Localização da mesa {table.label}</label><select id={`zone-${table.id}`} value={table.zone?.id || ""} disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onChange={event => void command(`hospitality/tables/${table.id}/location/`, { zone_id: event.target.value || null })}><option value="">Sem zona</option>{zones.map(zone => <option key={zone.id} value={zone.id}>{zone.label}</option>)}</select></div>{table.active_occupancy && <div className="field"><label htmlFor={`attach-${table.id}`}>Associar comanda à mesa {table.label}</label><select id={`attach-${table.id}`} value="" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onChange={event => {
  const tab = tabs.find(row => row.id === event.target.value); if (!tab) return;
  const origin = tables.find(row => row.active_occupancy?.tabs?.some(link => link.id === tab.id));
  if (origin) { setTableDialog(null); setMoving({ table, tab, origin: `Mesa ${origin.label}` }); }
  else void command(`hospitality/occupancies/${table.active_occupancy!.id}/tabs/`, { tab_id: tab.id });
}}><option value="">Selecionar comanda</option>{tabs.filter(tab => !table.active_occupancy?.tabs?.some(link => link.id === tab.id) && (!assignedTabs.has(tab.id) || session.capabilities.includes("tab.move"))).map(tab => <option key={tab.id} value={tab.id}>{tabPrimaryLabel(tab)} · {tabReference(tab)}{assignedTabs.has(tab.id) ? ` · Mesa ${tables.find(row => row.active_occupancy?.tabs?.some(link => link.id === tab.id))?.label} · Mover` : " · Sem mesa"}</option>)}</select></div>}</ActionDialog>}
      {tableDialog?.id === table.id && tableDialog.release && <ActionDialog title={`Liberar mesa ${table.label}?`} locked={busy} onClose={() => setTableDialog(null)}>{!sameReleaseOccupancy(table) && <p role="alert">A ocupação mudou. Cancele e confira a mesa novamente.</p>}<p>O acesso por QR será encerrado. A mesa passará para Aguardando limpeza.</p>{(table.active_occupancy?.tabs?.some(tab => !["CLOSED", "CANCELLED"].includes(tab.state || "")) || readyForTable(table).length > 0) && <p role="alert">Há comandas abertas ou entregas prontas. Cancele e confira a mesa.</p>}{error && <p className="notice" role="alert" data-state="danger">{error}</p>}<button className="buttonSecondary" disabled={!sameReleaseOccupancy(table) || busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder || !session.capabilities.includes("table.manage") || table.active_occupancy?.tabs?.some(tab => !["CLOSED", "CANCELLED"].includes(tab.state || "")) || readyForTable(table).length > 0} onClick={() => { if (!sameReleaseOccupancy(table)) return; void command(`hospitality/tables/${table.id}/release/`, { expected_occupancy_id: tableDialog.occupancyId, expected_generation: tableDialog.generation }, { tableId: table.id, status: "DIRTY" }).then(ok => { if (ok) { setTableDialog(null); setSelectedTable(null); } }); }}>Confirmar liberação</button></ActionDialog>}
</section>}</article>)}</div></section>}
    {screen === "tables" && !orderContext && !selectedTable && <section className="panel ux2OtherTabs" aria-label="Outras comandas"><h2>Comandas sem mesa</h2>{!otherTabs.length && <p className="ux2Empty">Nenhuma comanda sem mesa encontrada.</p>}{otherTabs.map(tab => <button className="ux2TabRow" data-tab-id={tab.id} key={tab.id} disabled={busy || moveLocked || pendingOrder || !online || !!intent || recoveryBlocked} onClick={event => { clearTaskOrigin(); setRequestedSurface(pickingOrder ? "catalog" : "tab"); setPickingOrder(false); orderOrigin.current = {screen:"tables",tableId:null}; setWorkspaceReturnFocus(event.currentTarget); setRequestedTab(current => ({ id: tab.id, sequence: (current?.sequence ?? 0) + 1, destination: "Sem mesa" })); }}><span><strong>{tab.display_label || tabReference(tab)}</strong><small>{tabReference(tab)} · Sem mesa</small></span><span aria-hidden="true">›</span></button>)}{session.capabilities.includes("tab.open") && <button className="buttonSecondary ux2NewLooseTab" disabled={busy || moveLocked || pendingOrder || !online || !!intent || recoveryBlocked} onClick={event => { setWorkspaceReturnFocus(event.currentTarget); clearTaskOrigin(); setRequestedSurface("tab"); orderOrigin.current = {screen:"tables",tableId:null}; setCreateRequest(current => current + 1); }}>Abrir comanda sem mesa</button>}</section>}
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
    </div><nav hidden={!!orderContext || !!selectedTable} className="ux2BottomNav" aria-label="Navegação principal"><button aria-current={screen === "now" ? "page" : undefined} disabled={busy || tableOpening || pendingOrder || !!intent} onClick={() => setScreen("now")}><span className="ux2Glyph" aria-hidden="true">◷</span>Agora</button><button className="ux2Middle" disabled={busy || moveLocked || tableOpening || pendingOrder || !!intent || recoveryBlocked} onClick={() => { clearTaskOrigin(); setPickingOrder(true); setRequestedSurface("catalog"); setDestinationPicker(true); }}><span className="ux2Glyph" aria-hidden="true">＋</span>Pedir</button><button aria-current={screen === "tables" ? "page" : undefined} disabled={busy || tableOpening || pendingOrder || !!intent} onClick={() => { clearTaskOrigin(); setPickingOrder(false); setRequestedSurface("tab"); setScreen("tables"); }}><span className="ux2Glyph" aria-hidden="true">▦</span>Mesas</button></nav>
    {activeTask && <ActionDialog title="Entrega pronta" onClose={() => setActiveTask(null)}><p>{activeTask.quantity}× {activeTask.product_name}</p><p>{activeTask.fulfillment_station === "BAR" ? "Bar" : activeTask.fulfillment_station === "KITCHEN" ? "Cozinha" : "Estação não informada"} · {activeTask.destination_label || "Sem mesa"}</p><p>Abrir esta entrega não altera o estado do pedido.</p><button className="buttonSecondary" disabled={busy || !online || !!intent || pendingOrder} onClick={() => void command(`dispatch/delivery/${activeTask.id}/complete/`).then(ok => { if (ok) setActiveTask(null); })}>Registrar entrega por exceção</button></ActionDialog>}
    {operatorMenu && <ActionDialog title="Opções do atendimento" onClose={() => setOperatorMenu(false)}><button className="buttonSecondary" disabled={busy || loading} onClick={() => { setOperatorMenu(false); void refresh(); }}>Atualizar</button><button className="buttonSecondary" disabled={busy || pendingOrder || !!intent} onClick={() => void logout()}>Sair</button></ActionDialog>}
    {destinationPicker && <ActionDialog title="Onde vamos pedir?" onClose={() => setDestinationPicker(false)}><p>Selecione uma mesa ou comanda para adicionar itens.</p><button className="buttonPrimary" onClick={() => { setDestinationPicker(false); setScreen("tables"); }}>Escolher mesa ou comanda</button>{session.capabilities.includes("tab.open") && <button className="buttonSecondary" onClick={event => { setWorkspaceReturnFocus(event.currentTarget); setDestinationPicker(false); clearTaskOrigin(); setRequestedSurface("tab"); orderOrigin.current = {screen:"tables",tableId:null}; setCreateRequest(current => current + 1); }}>Nova comanda sem mesa</button>}</ActionDialog>}
  </main>;
}
