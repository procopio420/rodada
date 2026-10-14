"use client";

import { OperationalIcon, type OperationalIconName } from "@/components/operational-icon";
import { tabPrimaryLabel, tabReference } from "@/lib/client/tab-identity";
import { OperationalHeading } from "@/components/operational-heading";
import { PartySizeEditor } from "@/components/party-size-editor";

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
  const [requestedTab, setRequestedTab] = useState<{ id: string; destination: string } | null>(null);
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
  const [partySizeLocked, setPartySizeLocked] = useState(false);
  const [tableDialog, setTableDialog] = useState<{id: string; release: boolean} | null>(null);
  const [openingAtAvailableTable, setOpeningAtAvailableTable] = useState<{ displayLabel: string } | null>(null);
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
  const refresh = useCallback(async () => {
    try {
      const [tableList, queue, zoneList] = await Promise.all([request<{ results: Table[]; table_service_enabled: boolean }>("hospitality/tables/"), request<{ results: Delivery[] }>("dispatch/delivery/"), request<{ results: { id: string; label: string }[] }>("hospitality/zones/")]);
      const allTabs: Tab[] = [];
      let offset: number | null = 0;
      do { const page: { results: Tab[]; next_offset?: number | null } = await request(`tabs/?active=true&offset=${offset}`); allTabs.push(...page.results); offset = page.next_offset ?? null; } while (offset !== null);
      setServiceEnabled(tableList.table_service_enabled === true); setTables(tableList.results); setDeliveries(queue.results); setZones(zoneList.results); setTabs(allTabs); setOnline(true); setUpdated(new Date().toLocaleTimeString("pt-BR"));
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
  }, [setError]);
  function returnToTable() {
    if (!tableOrigin || busy || moveLocked || pendingOrder || tableOpeningLock.current) return;
    setReturnFocus(tableOrigin.tableId); setScreen("tables");
  }
  useEffect(() => {
    if (screen !== "tables" || !returnFocus) return;
    const heading = document.getElementById(`attendance-table-${returnFocus}`);
    heading?.focus(); heading?.scrollIntoView({ block: "nearest" }); queueMicrotask(() => setReturnFocus(null));
  }, [screen, returnFocus]);
  const normalizeTable = (value: string) => normalizeCatalogSearch(value).replace(/^mesa\s*/, "").replace(/\s+/g, " ");
  const tableQuery = normalizeTable(tableSearch);
  const visibleTables = tables.filter(table => normalizeTable(table.label).includes(tableQuery));
  useRealtime(refresh, { onRevoked: () => setOnline(false) });
  async function command(path: string, payload: object = {}) {
    if (busy || moveLocked || !online || intent || recoveryBlocked || pendingOrder) return;
    setBusy(true); setError(""); setMessage("");
    try { await request(path, payload); setMessage("Operação confirmada."); await refresh(); return true; }
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
      if (result.tab_id) { setRequestedTab({ id: result.tab_id, destination: `Mesa ${result.table_label}` }); setScreen("tabs"); setOpeningAt(null); setOpeningAtAvailableTable(null); }
      else if (result.table_id) { setSelectedTable(result.table_id); setScreen("tables"); }
      setTakeoverAt(null); setMoving(null); await refresh();
    } catch (failure) {
      const status = (failure as { status?: number }).status;
      if (status && [400, 404, 409, 422].includes(status)) { localStorage.removeItem(storageKey); setIntent(null); await refresh(); }
      setError(failure instanceof Error ? failure.message : "Resultado desconhecido. Verifique a mesma intenção.");
    } finally { setBusy(false); }
  }
  function claim(table: Table) {
    const occupancy = table.active_occupancy!;
    if (occupancy.responsible_staff_id && occupancy.responsible_staff_id !== session.staff.id) { setTakeoverAt(table); return; }
    void serviceCommand(`hospitality/occupancies/${occupancy.id}/responsibility/claim/`, { expected_responsibility_version: occupancy.responsibility_version, mode: "CLAIM_UNASSIGNED" });
  }
  const assignedTabs = new Set(tables.flatMap(table => table.active_occupancy?.tabs?.map(tab => tab.id) || []));
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
  return <main className="appShell attendanceShell">
    <header className="productHeader"><div className="eyebrow">RODADA / ATENDIMENTO</div><OperationalHeading as="h1" icon="people">{session.venue.name}</OperationalHeading><p className="muted">{session.staff.display_name} · {loading ? "Atualizando…" : online ? `Atualizado às ${updated}` : "Desatualizado · verifique a conexão"}</p><div className="notice" data-state="warning">Teste sem pagamentos. O saldo das comandas permanece em aberto.</div><div className="actions"><button className="buttonSecondary" disabled={busy} onClick={() => void refresh()}>Atualizar</button><button className="buttonQuiet" disabled={busy || moveLocked || tableOpening || pendingOrder || !!intent || recoveryBlocked} onClick={() => void logout()}>Sair</button></div></header>
    <nav className="attendanceNav" aria-label="Atendimento">{[["now", "Agora"], ["tabs", "Contas"], ["tables", "Mesas"]].map(([id, title]) => <button key={id} className={screen === id ? "buttonPrimary" : "buttonSecondary"} aria-current={screen === id ? "page" : undefined} disabled={busy || moveLocked || tableOpening || pendingOrder || !!intent || recoveryBlocked} onClick={() => { setScreen(id); void refresh(); }}><OperationalIcon name={({ now: "now", tabs: "wallet", tables: "table" } as Record<string, OperationalIconName>)[id]} /><span>{title}</span></button>)}</nav>
    {error && <p className="notice" data-state="danger" role="alert">{error}</p>}{message && <p className="notice" data-state="success" role="status">{message}</p>}
    {intent && !openingAt && !openingAtAvailableTable && !takeoverAt && !moving && <div className="notice" data-state="warning" role="status"><p>Verificando atendimento. A intenção original está preservada.</p><button className="buttonPrimary" disabled={busy || !online || recoveryBlocked || pendingOrder} onClick={() => void serviceCommand()}>Verificar mesma intenção</button></div>}
    {screen === "now" && attention.map(table => <article className="panel" key={table.active_occupancy!.id}><h2>Mesa {table.label} · {table.zone?.label}</h2>{serviceInfo(table)}<button className="buttonSecondary" disabled={busy || pendingOrder || !!intent || recoveryBlocked} onClick={() => { setSelectedTable(table.id); setScreen("tables"); }}>Ver mesa</button></article>)}
    {screen === "now" && <section className="panel"><OperationalHeading as="h2" icon="check">Entregas prontas</OperationalHeading>{loading ? <p>Carregando entregas…</p> : !deliveries.length && online ? <p className="muted">Nenhuma entrega pronta.</p> : deliveries.map(delivery => <article className="attendanceItem" key={delivery.id}><h3>{delivery.quantity || 1}× {delivery.product_name}</h3><p>{delivery.destination_label || "Sem mesa"} · {delivery.tab_label || "Comanda"}</p><p className="muted">Pronto há {Math.floor(delivery.age_seconds / 60)} min</p><button className="buttonPrimary" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onClick={() => void command(`dispatch/delivery/${delivery.id}/complete/`)}>Concluir entrega</button></article>)}</section>}
    <div hidden={screen !== "now"}><ServiceRequestQueue staffId={session.staff.id} /></div>
    <div hidden={screen !== "tabs"}>{tableOrigin && <button className="buttonSecondary" disabled={busy || moveLocked || pendingOrder || tableOpening || !!intent} onClick={returnToTable}>Voltar à mesa {tableOrigin.tableLabel}</button>}<OrderWorkspace onOpenTableRequest={serviceEnabled && session.capabilities.includes("table.manage") && session.capabilities.includes("tab.open") ? displayLabel => setOpeningAtAvailableTable({ displayLabel }) : undefined} tableSelection={tableSelection} onTableSelectionResult={tableSelectionResult} onRecoveryNeeded={() => setScreen("tabs")} withoutPayments recoveryScope={`${session.venue.id}:${session.staff.id}:${session.session.id}`} onPendingChange={setPendingOrder} requestedTabId={requestedTab?.id} destinationLabel={requestedTab?.destination} /></div>
    {screen === "tables" && <section className="panel"><OperationalHeading as="h2" icon="table">Mesas</OperationalHeading><div className="field"><label htmlFor="attendance-table-search">Buscar mesa</label><input id="attendance-table-search" type="search" value={tableSearch} onChange={event => setTableSearch(event.target.value)} /></div>{loading ? <p>Carregando mesas…</p> : !tables.length && online ? <p className="muted">Nenhuma mesa cadastrada.</p> : visibleTables.map(table => <article className="attendanceTable" data-state={table.status} key={table.id}><h3 tabIndex={-1} id={`attendance-table-${table.id}`}><button className="buttonSecondary attendanceTableSummary" aria-expanded={selectedTable === table.id} aria-controls={`table-details-${table.id}`} disabled={busy || !!intent || pendingOrder || tableOpening} onClick={() => setSelectedTable(selectedTable === table.id ? null : table.id)}><span>Mesa {table.label}</span><small>{labels[table.status] || table.status} · {table.active_occupancy?.tabs?.filter(tab => !["CLOSED", "CANCELLED"].includes(tab.state || "")).length || 0} comandas abertas</small><OperationalIcon name="chevron-right" size={20} /></button></h3><div id={`table-details-${table.id}`} hidden={selectedTable !== table.id}>{serviceInfo(table)}{table.active_occupancy && <><p>{table.active_occupancy.tabs?.length || 0} comandas</p>{table.active_occupancy.tabs?.map(tab => <div key={tab.id}><button data-tab-id={tab.id} className="buttonSecondary" key={tab.id} disabled={busy || pendingOrder || !!intent || recoveryBlocked || ["CLOSED", "CANCELLED"].includes(tab.state || "")} onClick={() => openExisting(table, tab.id)}>{tab.display_label || "Comanda sem nome"} · {tab.display_reference || tabReference(tab)}</button>{session.capabilities.includes("tab.move") && <button className="buttonSecondary attendanceMoveButton" disabled={busy || moveLocked || pendingOrder || tableOpening || !online || !!intent || recoveryBlocked} onClick={() => setMoveSelection({ table, tab })}><OperationalIcon name="chevron-right" size={20} />Mover comanda</button>}</div>)}{serviceEnabled && session.capabilities.includes("tab.open") && <button className="buttonPrimary" disabled={busy || pendingOrder || !!intent || recoveryBlocked || !online} onClick={() => { setNewLabel(""); setOpeningAt(table); }}>Nova comanda nesta mesa</button>}</>}<button className="buttonQuiet" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onClick={() => setTableDialog({ id: table.id, release: false })}>Organizar mesa {table.label}</button>{tableDialog?.id === table.id && !tableDialog.release && <ActionDialog title={`Organizar mesa ${table.label}`} locked={busy || partySizeLocked} onClose={() => setTableDialog(null)}>{error && <p className="notice" role="alert" data-state="danger">{error}</p>}{message && <p className="notice" role="status" data-state="success">{message}</p>}{table.active_occupancy && <PartySizeEditor occupancyId={table.active_occupancy.id} onRecoveryLock={setPartySizeLocked} />}<div className="field"><label htmlFor={`zone-${table.id}`}>Localização da mesa {table.label}</label><select id={`zone-${table.id}`} value={table.zone?.id || ""} disabled={partySizeLocked || busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onChange={event => void command(`hospitality/tables/${table.id}/location/`, { zone_id: event.target.value || null })}><option value="">Sem zona</option>{zones.map(zone => <option key={zone.id} value={zone.id}>{zone.label}</option>)}</select></div>{table.active_occupancy && <div className="field"><label htmlFor={`attach-${table.id}`}>Associar comanda à mesa {table.label}</label><select id={`attach-${table.id}`} value="" disabled={partySizeLocked || busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onChange={event => {
  const tab = tabs.find(row => row.id === event.target.value); if (!tab) return;
  const origin = tables.find(row => row.active_occupancy?.tabs?.some(link => link.id === tab.id));
  if (origin) { setTableDialog(null); setMoving({ table, tab, origin: `Mesa ${origin.label}` }); }
  else void command(`hospitality/occupancies/${table.active_occupancy!.id}/tabs/`, { tab_id: tab.id });
}}><option value="">Selecionar comanda</option>{tabs.filter(tab => !table.active_occupancy?.tabs?.some(link => link.id === tab.id) && (!assignedTabs.has(tab.id) || session.capabilities.includes("tab.move"))).map(tab => <option key={tab.id} value={tab.id}>{tabPrimaryLabel(tab)} · {tabReference(tab)}{assignedTabs.has(tab.id) ? ` · Mesa ${tables.find(row => row.active_occupancy?.tabs?.some(link => link.id === tab.id))?.label} · Mover` : " · Sem mesa"}</option>)}</select></div>}</ActionDialog>}
      {table.status === "AVAILABLE" && serviceEnabled && session.capabilities.includes("table.manage") && <button className="buttonPrimary" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onClick={() => void serviceCommand(`hospitality/tables/${table.id}/service/start/`)}>Iniciar atendimento · Mesa {table.label}</button>}
      {table.status === "AVAILABLE" && !serviceEnabled && session.capabilities.includes("table.manage") && <button className="buttonPrimary" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onClick={() => void command(`hospitality/tables/${table.id}/occupy/`)}>Ocupar mesa</button>}
      {table.status === "OCCUPIED" && <><p className="muted">Liberar encerra o acesso por QR. As comandas permanecem abertas.</p><button className="buttonSecondary" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onClick={() => { setError(""); setMessage(""); setTableDialog({id: table.id, release: true}); }}>Liberar mesa {table.label}</button></>}
      {tableDialog?.id === table.id && tableDialog.release && <ActionDialog title={`Liberar mesa ${table.label}?`} locked={busy} onClose={() => setTableDialog(null)}><p>O acesso por QR será encerrado. As comandas permanecem abertas.</p>{error && <p className="notice" role="alert" data-state="danger">{error}</p>}<button className="buttonSecondary" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onClick={() => void command(`hospitality/tables/${table.id}/release/`).then(ok => { if (ok) setTableDialog(null); })}>Confirmar liberação</button></ActionDialog>}
      {table.status === "DIRTY" && <button className="buttonPrimary" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onClick={() => void command(`hospitality/tables/${table.id}/cleaning/start/`)}>Iniciar limpeza</button>}
      {table.status === "CLEANING" && <button className="buttonPrimary" disabled={busy || moveLocked || tableOpening || !online || !!intent || recoveryBlocked || pendingOrder} onClick={() => void command(`hospitality/tables/${table.id}/cleaning/complete/`)}>Concluir limpeza</button>}


    </div></article>)}</section>}
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
    {openingAt?.active_occupancy && <ActionDialog title={`Nova comanda · Mesa ${openingAt.label}`} locked={busy || !!intent} onClose={() => setOpeningAt(null)}><details><summary>Adicionar nome ou apelido (opcional)</summary><div className="field"><label htmlFor="contextual-tab-name">Nome ou apelido (opcional)</label><input id="contextual-tab-name" maxLength={120} value={newLabel} disabled={busy || !!intent} onChange={event => setNewLabel(event.target.value)} /></div></details><button className="buttonPrimary" disabled={busy || !!intent || !online} onClick={() => void serviceCommand(`hospitality/occupancies/${openingAt.active_occupancy!.id}/tabs/open/`, { display_label: newLabel, expected_generation: openingAt.active_occupancy!.generation })}>Abrir e pedir</button>{intent && <button className="buttonPrimary" disabled={busy || !online} onClick={() => void serviceCommand()}>Verificar mesma intenção</button>}</ActionDialog>}

    {openingAtAvailableTable && <ActionDialog title="Qual mesa o cliente está?" locked={busy || !!intent} onClose={() => setOpeningAtAvailableTable(null)}>
      <p>Escolha a mesa da comanda {openingAtAvailableTable.displayLabel}.</p>
      {tables.filter(table => table.status === "AVAILABLE" || (table.status === "OCCUPIED" && table.active_occupancy)).length ? <div className="actions">{tables.filter(table => table.status === "AVAILABLE" || (table.status === "OCCUPIED" && table.active_occupancy)).map(table => <button key={table.id} className="buttonPrimary" disabled={busy || !!intent || !online || pendingOrder || recoveryBlocked} onClick={() => void serviceCommand(table.status === "OCCUPIED" ? `hospitality/occupancies/${table.active_occupancy!.id}/tabs/open/` : `hospitality/tables/${table.id}/service/open-tab/`, { display_label: openingAtAvailableTable.displayLabel, ...(table.status === "OCCUPIED" ? { expected_generation: table.active_occupancy!.generation } : {}) })}>Mesa {table.label}{table.status === "OCCUPIED" ? " · Em uso" : ""}</button>)}</div> : <p className="notice" data-state="warning">Nenhuma mesa pode receber comandas agora. Atualize e tente novamente.</p>}
      {intent && <button className="buttonPrimary" disabled={busy || !online} onClick={() => void serviceCommand()}>Verificar mesma intenção</button>}
    </ActionDialog>}
    {takeoverAt?.active_occupancy && <ActionDialog title="Assumir atendimento?" locked={busy || !!intent} onClose={() => setTakeoverAt(null)}><p>{takeoverAt.active_occupancy.responsible_staff?.display_name} está responsável. Você também pode atender sem assumir.</p><button className="buttonPrimary" disabled={busy || !!intent || !online} onClick={() => void serviceCommand(`hospitality/occupancies/${takeoverAt.active_occupancy!.id}/responsibility/claim/`, { expected_responsibility_version: takeoverAt.active_occupancy!.responsibility_version, mode: "TAKE_OVER" })}>Confirmar transferência de atendimento</button>{intent && <button className="buttonPrimary" disabled={busy || !online} onClick={() => void serviceCommand()}>Verificar mesma intenção</button>}<button className="buttonSecondary" disabled={busy || !!intent} onClick={() => setTakeoverAt(null)}>Atender sem assumir</button></ActionDialog>}
  <TabLocationMove selection={moveSelection} tables={tables} onClose={closeMove} onLockChange={setMoveLocked} onConfirmed={refresh} />
  </main>;
}
