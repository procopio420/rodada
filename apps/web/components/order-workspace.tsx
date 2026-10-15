"use client";

import { tabPrimaryLabel, tabSecondaryLabel, tabReference } from "@/lib/client/tab-identity";
import { attendanceCategory, compareAttendanceCategories, normalizeCatalogSearch } from "@/lib/client/attendance-catalog";

import { OperationalHeading } from "@/components/operational-heading";
import { OperationalIcon } from "@/components/operational-icon";

import { useCallback, useEffect, useEffectEvent, useMemo, useRef, useState } from "react";
import { AttendanceTabHistory } from "@/components/attendance-tab-history";
import { AttendanceCatalogCard } from "@/components/attendance-catalog-card";
import { AttendanceDraft } from "@/components/attendance-draft";
import { RepeatOrderDialog, reviewRepeatedOrder, selectedRepeatedLines, type HistoricalOrder, type RepeatQuantities } from "@/components/repeat-order";
import { ActionDialog } from "@/components/action-dialog";
import { PosCashReceipt } from "@/components/pos-cash-receipt";
import { ConfirmedItemRemoval } from "@/components/confirmed-item-removal";
import { BillSummary, type Bill } from "@/components/bill-summary";
import { PricingAdjustments } from "@/components/pricing-adjustments";
import Link from "next/link";
import { ReceiptPrinting } from "@/components/receipt-printing";
import { ProductIcon, type IconData } from "@/components/product-icon";
import { useOrderIntent } from "@/lib/client/order-intent";
import { apiCall, asApiError } from "@/lib/client/staff-auth";


import { ProductCustomization, CustomizationText, defaults, selectionError, unitPrice, type OrderingProduct, type Selection } from "@/components/product-customization";

type Product = OrderingProduct & { category?: string; icon?: IconData; availability: string; id: string; name: string; price_cents: number; fulfillment_station: string; active: boolean };
type Tab = Bill & { orders?: HistoricalOrder[]; version: number; id: string; display_label: string; table_label?: string | null; last_table_label?: string | null; state: string; exposure_cents: number; charges_cents: number; payments_cents: number };
type DraftLine = { product: Product; quantity: number; selection: Selection };
type CashPoint = { id: string; label: string; active_shift: { id: string; status: string } | null };
const money = (value = 0) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value / 100);

export type TableTabSelection = { requestId: number; tabId: string; occupancyId: string; tableId: string; tableLabel: string };
export function OrderWorkspace({ tableMode = false, requestedTabSequence = 0, createRequest = 0, historyRequest = 0, onDialogClose, onOpenFailure, withoutPayments = false, onPendingChange, onRecoveryNeeded, onOpenTableRequest, tableSelection, onTableSelectionResult, requestedTabId, destinationLabel, recoveryScope }: { tableMode?: boolean; requestedTabSequence?: number; createRequest?: number; historyRequest?: number; onDialogClose?: () => void; onOpenFailure?: (message: string) => void; requestedTabId?: string; destinationLabel?: string; recoveryScope?: string; withoutPayments?: boolean; onPendingChange?: (pending: boolean) => void; onRecoveryNeeded?: () => void; onOpenTableRequest?: (displayLabel: string) => void; tableSelection?: TableTabSelection | null; onTableSelectionResult?: (error: string | null, selection: TableTabSelection) => void }) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [standaloneCreate, setStandaloneCreate] = useState(false);
  const [dialogView, setDialogView] = useState("catalog");
  const tabPageSize = withoutPayments ? 10 : 200;
  const apiRoot = withoutPayments ? "/api/attendance" : "/api/pos";
  const [closingDialog, setClosingDialog] = useState(false), [closing, setClosing] = useState(false), [success, setSuccess] = useState("");
  const [tabCollapsed, setTabCollapsed] = useState(false);
  const [catalogCollapsed, setCatalogCollapsed] = useState(false);
  const [removingItem, setRemovingItem] = useState<{ id: string; product_name: string; quantity: number } | null>(null);
  const [cashPending, setCashPending] = useState(!withoutPayments);
  const [itemCorrectionPending, setCorrectionPending] = useState(false);
  const [recoveryBlocked, setRecoveryBlocked] = useState(false);
  const [recoveryReady, setRecoveryReady] = useState(!recoveryScope);
  const correctionPending = itemCorrectionPending || recoveryBlocked || !recoveryReady;
  const recoveryKey = recoveryScope ? `rodada:order-draft:${recoveryScope}` : null;
  const [draftFeedback, setDraftFeedback] = useState("");
  const [catalogSearch, setCatalogSearch] = useState("");
  const [category, setCategory] = useState("");
  const [showHistory, setShowHistory] = useState(false);
  const [tabs, setTabs] = useState<Tab[]>([]), [products, setProducts] = useState<Product[]>([]), [cashPoints, setCashPoints] = useState<CashPoint[]>([]), [selected, setSelected] = useState<Tab | null>(null), [label, setLabel] = useState(""), [message, setMessage] = useState(""), [confirming, setConfirming] = useState(false);
  const [opening, setOpening] = useState(false);
  const [selecting, setSelecting] = useState(false);
  const [discardDialog, setDiscardDialog] = useState(false);
  const [repeatLoading, setRepeatLoading] = useState(false);
  const repeatReading = useRef(false);
  const repeatConsumed = useRef(false);
  const [repeatReview, setRepeatReview] = useState<{ tabId: string; orderId: string; review: ReturnType<typeof reviewRepeatedOrder<Product>> } | null>(null);
  const [drafts, setDrafts] = useState<Record<string, DraftLine[]>>({});
  const cart = useMemo(() => selected ? drafts[selected.id] ?? [] : [], [selected, drafts]);
  function setCart(update: DraftLine[] | ((current: DraftLine[]) => DraftLine[])) {
    if (!selected) return;
    const tabId = selected.id;
    setDrafts(current => ({ ...current, [tabId]: typeof update === "function" ? update(current[tabId] ?? []) : update }));
  }
  const switching = useRef(false);
  const selectedSection = useRef<HTMLElement | null>(null);
  const [selectionFocus, setSelectionFocus] = useState(0);
  useEffect(() => { if (selectionFocus) selectedSection.current?.querySelector("h2")?.focus(); }, [selectionFocus]);
  const [search, setSearch] = useState("");
  const appliedQuery = useRef("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const pageOffset = useRef(0);
  const listRequest = useRef(0);
  const pageSwitching = useRef(false);
  const [paging, setPaging] = useState(false);
  const [offset, setOffset] = useState(0);
  const [nextOffset, setNextOffset] = useState<number | null>(null);
  const [fresh, setFresh] = useState(false);
  const [configuring, setConfiguring] = useState<Product | null>(null);
  const [editing, setEditing] = useState<number | null>(null);
  const load = useCallback(async (targetOffset = pageOffset.current, targetSearch = appliedQuery.current) => {
    const request = ++listRequest.current;
    const params = new URLSearchParams();
    if (targetOffset) params.set("offset", String(targetOffset));
    if (targetSearch.trim()) params.set("q", targetSearch.trim());
    const listUrl = `${apiRoot}/tabs/${params.size ? `?${params}` : ""}`;
    try {
    setFresh(false);
    // Unified table attendance selects Tabs from the table surface and reads each
    // selected Tab canonically by ID. The expensive 200-Tab financial list is only
    // needed when the operator explicitly opens history.
    const listRequest = tableMode && !showHistory
      ? Promise.resolve({ response: { ok: true }, body: { results: [] as Tab[], next_offset: null } })
      : apiCall<{ results: Tab[]; next_offset: number | null }>(listUrl);
    const [tabResult, productResult, cashResult] = await Promise.all([listRequest, apiCall<{ results: Product[] }>(`${apiRoot}/catalog/products/`), withoutPayments ? Promise.resolve({ response: { ok: true }, body: { results: [] as CashPoint[] } }) : apiCall<{ results: CashPoint[] }>(`${apiRoot}/cash/points/`)]);
    if (request !== listRequest.current) return;
    if (tabResult.response.ok) {
      const page = tabResult.body as { results: Tab[]; next_offset: number | null };
      setTabs(page.results.slice(0, tabPageSize)); setNextOffset(page.results.length > tabPageSize ? targetOffset + tabPageSize : page.next_offset ?? null);
      pageOffset.current = targetOffset; setOffset(targetOffset);
      appliedQuery.current = targetSearch.trim(); setAppliedSearch(targetSearch.trim());
    } else setMessage(asApiError(tabResult.body).message);
    if (productResult.response.ok) setProducts((productResult.body as { results: Product[] }).results); else setMessage(asApiError(productResult.body).message);
    if (cashResult.response.ok) {
      const points = (cashResult.body as { results: CashPoint[] }).results.filter((point) => point.active_shift);
      setCashPoints(points);
    }
    setFresh(tabResult.response.ok && productResult.response.ok);
    } catch { if (request === listRequest.current) { setFresh(false); setMessage("Não foi possível atualizar. Os dados podem estar desatualizados."); } }
  }, [apiRoot, withoutPayments, tableMode, showHistory, tabPageSize, setFresh, setTabs, setNextOffset, setOffset, setAppliedSearch, setMessage, setProducts, setCashPoints]);
  const orderIntent = useOrderIntent(async (tabId, orderId, origin) => {
    const detail = await apiCall<Tab>(`${apiRoot}/tabs/${tabId}/`);
    if (!detail.response.ok || !detail.body || !("orders" in detail.body) || detail.body.id !== tabId
      || !detail.body.orders?.some(order => order.id === orderId)) throw new Error("Order readback unavailable");
    await load();
    return () => {
      setSelected(detail.body as Tab); setTabCollapsed(false);
      if (origin === "draft") setDrafts(current => ({ ...current, [tabId]: [] }));
      setSuccess("Pedido confirmado."); setMessage("");
    };
  });
  const revealRecoveredDraft = useEffectEvent(() => { if (tableMode) { setDialogOpen(true); setStandaloneCreate(false); setDialogView("draft"); } onRecoveryNeeded?.(); });
  useEffect(() => { onPendingChange?.(!orderIntent.ready || orderIntent.busy || !!orderIntent.pending || correctionPending || cashPending || selecting || opening || repeatLoading || !!repeatReview); }, [confirming, orderIntent.pending, orderIntent.busy, orderIntent.ready, correctionPending, cashPending, selecting, opening, repeatLoading, repeatReview, onPendingChange]);
  useEffect(() => { if ((!orderIntent.ready && orderIntent.message) || orderIntent.pending) queueMicrotask(() => revealRecoveredDraft()); }, [orderIntent.ready, orderIntent.message, orderIntent.pending, selected, onRecoveryNeeded]);
  useEffect(() => {
    if (!recoveryKey) return;
    let active = true;
    queueMicrotask(() => {
    if (!active) return;
    try {
      const prefix = recoveryKey.slice(0, recoveryKey.lastIndexOf(":") + 1);
      if (Object.keys(localStorage).some(key => key.startsWith(prefix) && key !== recoveryKey)) {
        setRecoveryBlocked(true);
        setMessage("Pedido de outra sessão preservado. Confira o histórico com a gerência antes de repetir.");
      }
      const raw = localStorage.getItem(recoveryKey);
      if (raw) {
        const saved = JSON.parse(raw);
        const savedDrafts = saved.schema === 1 ? { [saved.tab?.id]: saved.cart } : saved.drafts;
        if (![1, 2].includes(saved.schema) || !saved.tab?.id || !savedDrafts ||
            typeof savedDrafts !== "object" || Array.isArray(savedDrafts) ||
            !Object.values(savedDrafts).every(value => Array.isArray(value) && value.every((line: DraftLine) =>
              line.product?.id && Number.isSafeInteger(line.quantity) && line.quantity > 0 && line.quantity <= 99 && line.selection)) ||
            saved.key || saved.payload) throw new Error("Invalid or ambiguous legacy recovery record");
        setSelected(saved.tab); setDrafts(savedDrafts); revealRecoveredDraft();
        setMessage("Rascunho recuperado na comanda original.");
        void apiCall<Tab>(`${apiRoot}/tabs/${saved.tab.id}/`).then(result => {
          if (result.response.ok) setSelected(result.body as Tab);
        }).catch(() => {});
      }
    } catch {
      setRecoveryBlocked(true);
      setMessage("Recuperação indisponível. Confira o histórico antes de repetir o pedido.");
    } finally { setRecoveryReady(true); }
    });
    return () => { active = false; };
  }, [recoveryKey, apiRoot]);
  const persistDraft = useCallback((tab = selected, draft = cart) => {
    if (!recoveryKey) return;
    const retained = tab ? { ...drafts, [tab.id]: draft } : drafts;
    if (!Object.values(retained).some(lines => lines.length) && !orderIntent.pending) localStorage.removeItem(recoveryKey);
    else if (tab) localStorage.setItem(recoveryKey, JSON.stringify({ schema: 2, tab, drafts: retained, key: null, payload: null }));
  }, [recoveryKey, selected, cart, drafts, orderIntent.pending]);
  useEffect(() => {
    if (!recoveryReady || recoveryBlocked) return;
    queueMicrotask(() => {
    try { persistDraft(); } catch {
      setRecoveryBlocked(true); setMessage("Não foi possível preservar o rascunho. Confira o histórico antes de enviar.");
    }
    });
  }, [recoveryReady, recoveryBlocked, persistDraft]);
  useEffect(() => { queueMicrotask(() => void load()); const timer = setInterval(() => { if (!pageSwitching.current) void load(); }, 15000); return () => clearInterval(timer); }, [load]);
  useEffect(() => { queueMicrotask(() => setSelected(current => current ? { ...current, ...(tabs.find(tab => tab.id === current.id) ?? {}) } : null)); }, [tabs]);
  const changePage = useCallback(async (targetOffset: number, targetSearch?: string) => {
    if (pageSwitching.current || switching.current || correctionPending || cashPending || orderIntent.pending) return;
    pageSwitching.current = true; setPaging(true); setMessage("");
    try { await load(targetOffset, targetSearch ?? appliedQuery.current); } finally { pageSwitching.current = false; setPaging(false); }
  }, [load, correctionPending, cashPending, orderIntent.pending]);
  const searchControls = (inputId: string) => <form onSubmit={event => { event.preventDefault(); void changePage(0, search); }}>
    <div className="field"><label htmlFor={inputId}>Buscar comanda por apelido</label><input id={inputId} type="search" maxLength={120} value={search} disabled={paging || correctionPending || confirming || !!orderIntent.pending} onChange={event => setSearch(event.target.value)} /></div>
    <button className="buttonSecondary" disabled={paging || correctionPending || confirming || !!orderIntent.pending}>Buscar</button>
    <p className="muted" role="status">{appliedSearch ? `Resultados para “${appliedSearch}” · busca em todas as comandas` : "Todas as comandas · apague o apelido e busque para limpar o filtro"}</p>
  </form>;
  const pagination = <nav className="tabPagination" aria-label="Páginas de comandas">
    <button className="buttonSecondary tabPaginationButton" aria-label="Página anterior" title="Página anterior" disabled={paging || offset === 0 || correctionPending || confirming || !!orderIntent.pending} onClick={() => void changePage(Math.max(0, offset - tabPageSize))}><OperationalIcon name="chevron-left" /></button>
    <span role="status">{paging ? "Carregando página…" : `Página ${Math.floor(offset / tabPageSize) + 1}`}</span>
    <button className="buttonSecondary tabPaginationButton" aria-label="Próxima página" title="Próxima página" disabled={paging || nextOffset === null || correctionPending || confirming || !!orderIntent.pending} onClick={() => { if (nextOffset !== null) void changePage(nextOffset); }}><OperationalIcon name="chevron-right" /></button>
  </nav>;
  const rows = useMemo(() => cart.map(row => ({ ...row, product: products.find(p => p.id === row.product.id) ?? { ...row.product, active: false } })), [products, cart]);
  const catalog = withoutPayments ? products.filter(product => product.active) : products;
  const categories = [...new Set(catalog.map(attendanceCategory))].filter(name => name !== "Outros" && name !== "Todos").sort(compareAttendanceCategories).concat("Todos");
  const activeCategory = categories.includes(category) ? category : categories[0] || "";
  const query = normalizeCatalogSearch(catalogSearch);
  const catalogVisible = !catalogCollapsed || !!query;
  const visibleProducts = withoutPayments ? catalog.filter(product => query ? normalizeCatalogSearch(product.name).includes(query) : activeCategory === "Todos" || attendanceCategory(product) === activeCategory)
    .sort((a, b) => compareAttendanceCategories(attendanceCategory(a), attendanceCategory(b)) || a.name.localeCompare(b.name, "pt-BR")) : products;
  const total = rows.reduce((sum, row) => sum + unitPrice(row.product, row.selection) * row.quantity, 0);
  const repeatAllowed = fresh && !!selected && !["CLOSED", "CANCELLED"].includes(selected.state) &&
    !repeatLoading && !configuring && !selecting && !opening && !closing && !cashPending && !correctionPending && !confirming &&
    orderIntent.ready && !orderIntent.busy && !orderIntent.pending;
  const repeatCurrent = selected?.orders?.find(order => order.id === repeatReview?.orderId);
  const repeatUnchanged = !!repeatReview && selected?.id === repeatReview.tabId && !!repeatCurrent &&
    JSON.stringify(reviewRepeatedOrder(repeatCurrent, products)) === JSON.stringify(repeatReview.review);
  async function startRepeat(orderId: string) {
    if (!repeatAllowed || repeatReview || repeatReading.current || !selected) return;
    repeatReading.current = true; repeatConsumed.current = false; setRepeatLoading(true); setMessage("");
    const tabId = selected.id;
    try {
      const [detail, catalog] = await Promise.all([apiCall<Tab>(`${apiRoot}/tabs/${tabId}/`), apiCall<{ results: Product[] }>(`${apiRoot}/catalog/products/`)]);
      if (!detail.response.ok || !catalog.response.ok) throw new Error("Falha de leitura");
      const tab = detail.body as Tab, currentProducts = (catalog.body as { results: Product[] }).results;
      const order = tab.orders?.find(value => value.id === orderId);
      if (tab.id !== tabId || ["CLOSED", "CANCELLED"].includes(tab.state) || !order || !Array.isArray(currentProducts)) throw new Error("Contexto alterado");
      setSelected(tab); setProducts(currentProducts);
      setRepeatReview({ tabId, orderId, review: reviewRepeatedOrder(order, currentProducts) });
    } catch { setMessage("Não foi possível conferir a rodada. Atualize e tente novamente; o rascunho está preservado."); }
    finally { repeatReading.current = false; setRepeatLoading(false); }
  }
  async function confirmRepeatedOrder(quantities: RepeatQuantities) {
    if (!repeatAllowed || !repeatUnchanged || !repeatReview?.review.canAdd || repeatReading.current || repeatConsumed.current) return;
    const selectedLines = selectedRepeatedLines(repeatReview.review, quantities);
    if (!selectedLines) return;
    const tabId = repeatReview.tabId;
    repeatConsumed.current = true;
    repeatReading.current = true;
    setRepeatLoading(true); setSuccess(""); setMessage("");
    // This new Order contains only selected historical lines, never any manual draft.
    setRepeatReview(null);
    try {
      await orderIntent.submit({ tab: tabId, lines: selectedLines.map(({ product, quantity, selection }) =>
        ({ product_id: product.id, quantity, ...selection })) }, apiRoot, "repeat");
    } finally {
      repeatReading.current = false;
      setRepeatLoading(false);
    }
  }
  function jumpTo(region: string) {
    if (tableMode) {
      setDialogView(region);
      requestAnimationFrame(() => selectedSection.current?.querySelector<HTMLElement>(`[data-attendance-region="${region}"]`)?.focus());
      return;
    }
    const target = selectedSection.current?.querySelector<HTMLElement>(`[data-attendance-region="${region}"]`);
    target?.focus({ preventScroll: true }); target?.scrollIntoView({ block: "start" });
  }
  function addDraftLine(product: Product, selection: Selection) {
    // Recheck the current catalog at insertion: a customization dialog can outlive a refresh.
    const currentProduct = products.find(item => item.id === product.id);
    if (!fresh || !currentProduct?.active || currentProduct.availability !== "AVAILABLE") {
      setDraftFeedback("Produto indisponível ou catálogo desatualizado. Atualize antes de adicionar.");
      return;
    }
    product = currentProduct;
    if (withoutPayments) setDraftFeedback(`${product.name} selecionado. Confira a quantidade no pedido atual.`);
    setCart(current => {
      const sameSelection = (a: Selection, b: Selection) => a.variant_id === b.variant_id && a.special_instructions === b.special_instructions && JSON.stringify([...a.modifier_option_ids].sort()) === JSON.stringify([...b.modifier_option_ids].sort());
      const index = withoutPayments ? current.findIndex(line => line.product.id === product.id && sameSelection(line.selection, selection)) : -1;
      return index < 0 ? [...current, { product, quantity: 1, selection }] : current.map((line, i) => i === index ? { ...line, quantity: Math.min(99, line.quantity + 1) } : line);
    });
  }
  const selectTab = async (tab: Pick<Tab, "id">, context?: TableTabSelection): Promise<string | null> => {
    if (switching.current || cashPending || correctionPending || orderIntent.pending || closing || discardDialog || configuring || repeatReading.current || repeatReview) return "Resolva a operação atual antes de abrir outra comanda.";
    if (!context && selected?.id === tab.id) { if (tableMode) { setStandaloneCreate(false); setDialogView("catalog"); setDialogOpen(true); } setTabCollapsed(false); setSelectionFocus(n => n + 1); return null; }
    switching.current = true; setSelecting(true);
    try {
      const params = context ? `?${new URLSearchParams({ occupancy_id: context.occupancyId, table_id: context.tableId })}` : "";
      const result = await apiCall<Tab>(`${apiRoot}/tabs/${tab.id}/${params}`);
      if (!result.response.ok) { const error = asApiError(result.body).message; setMessage(error); return error; }
      if (!result.body || !("id" in result.body) || result.body.id !== tab.id) throw new Error("Invalid tab detail");
      setSelected(result.body as Tab); setTabCollapsed(false); setCatalogCollapsed(false); if (tableMode) { setStandaloneCreate(false); setDialogView("catalog"); setDialogOpen(true); } setDraftFeedback(""); setSuccess(""); setMessage(""); setSelectionFocus(n => n + 1); return null;
    } catch { const error = "Não foi possível abrir a comanda. O rascunho anterior foi preservado."; setMessage(error); return error; }
    finally { switching.current = false; setSelecting(false); }
  };
  const handledTableRequest = useRef<number | null>(null);
  const performTableSelection = useEffectEvent((selection: TableTabSelection) => {
    void selectTab({ id: selection.tabId }, selection).then(error => onTableSelectionResult?.(error, selection));
  });
  useEffect(() => {
    if (!tableSelection || handledTableRequest.current === tableSelection.requestId) return;
    handledTableRequest.current = tableSelection.requestId;
    performTableSelection(tableSelection);
  }, [tableSelection]);
  const handledExternalRequest = useRef("");
  const selectRequestedTab = useEffectEvent((id: string) => { void selectTab({ id }).then(failure => { if (failure) onOpenFailure?.(failure); }); });
  useEffect(() => {
    const request = `${requestedTabId}:${requestedTabSequence}`;
    // Don't consume an external selection while a previous selection is still completing:
    // selectTab would reject it and the request ID would otherwise be lost forever.
    if (!requestedTabId || handledExternalRequest.current === request
      || switching.current || selecting || opening || closing || cashPending
      || correctionPending || orderIntent.pending || discardDialog || configuring
      || repeatReading.current || repeatReview) return;
    handledExternalRequest.current = request;
    selectRequestedTab(requestedTabId);
  }, [requestedTabId, requestedTabSequence, selecting, opening, closing, cashPending, correctionPending, orderIntent.pending, discardDialog, configuring, repeatReview]);
  useEffect(() => { if (createRequest) queueMicrotask(() => { setStandaloneCreate(true); setDialogOpen(true); }); }, [createRequest]);
  useEffect(() => { if (historyRequest) queueMicrotask(() => { setDialogOpen(true); requestAnimationFrame(() => setShowHistory(true)); }); }, [historyRequest]);
  const createTab = async () => {
    if (switching.current || cashPending || correctionPending || orderIntent.pending || closing || discardDialog || configuring || repeatReading.current || repeatReview) return;
    if (withoutPayments && onOpenTableRequest) {
      const displayLabel = label.trim();
      if (!displayLabel) { setMessage("Informe o nome da comanda."); return; }
      onOpenTableRequest(displayLabel);
      return;
    }
    switching.current = true; setOpening(true);
    try {
      const result = await apiCall<Tab>(`${apiRoot}/tabs/`, { method: "POST", body: JSON.stringify({ display_label: label }) });
      if (result.response.ok) { setSelected(result.body as Tab); setTabCollapsed(false); setStandaloneCreate(false); setDialogView("catalog"); setLabel(""); setSelectionFocus(n => n + 1); await load(); }
      else setMessage(asApiError(result.body).message);
    } catch { setMessage("Não foi possível abrir a comanda. Atualize a lista antes de tentar novamente."); }
    finally { switching.current = false; setOpening(false); }
  };
  const confirm = async () => {
    if (!selected || (!rows.length && !orderIntent.pending) || confirming || cashPending || switching.current || discardDialog || configuring || correctionPending || repeatReading.current || repeatReview) return;
    setConfirming(true); setSuccess("");
    try { await orderIntent.submit({ tab: selected.id, lines: rows.map(row => ({ product_id: row.product.id, quantity: row.quantity, ...row.selection })) }, apiRoot); }
    finally { setConfirming(false); }
  };
  const close = async () => { if (!selected || closing || cashPending || cart.length || switching.current || orderIntent.pending || correctionPending) return; setClosing(true); setMessage(""); try { const r = await apiCall(`${apiRoot}/tabs/${selected.id}/close/`, { method: "POST", body: "{}" }); if (r.response.ok) { setClosingDialog(false); setSuccess("Comanda encerrada."); setSelected(null); await load(); } else setMessage(asApiError(r.body).message); } catch { setMessage("Não foi possível confirmar o fechamento. Atualize a comanda antes de continuar."); } finally { setClosing(false); } };
  const closeTabButton = <button className={withoutPayments ? "buttonSecondary attendanceCloseTab" : "buttonQuiet"} style={withoutPayments ? undefined : { width: "100%", marginTop: 8 }} disabled={correctionPending || confirming || !!orderIntent.pending || !!cart.length || (withoutPayments && selected?.exposure_cents !== 0)} onClick={() => withoutPayments ? setClosingDialog(true) : void close()}>{withoutPayments && <OperationalIcon name="receipt" size={20} />}Fechar comanda</button>;
  const workspace = <section className={withoutPayments ? "attendanceOrders" : "appShell"}>{!tableMode && <header className="productHeader"><div className="eyebrow">RODADA / ATENDIMENTO</div><OperationalHeading as="h1" icon="cart">Comandas e pedidos</OperationalHeading><p className="muted">Estado financeiro e operacional persistido.</p>{withoutPayments && !fresh && <p className="notice" data-state="warning">Atualizando ou dados desatualizados. Verifique a conexão.</p>}{!withoutPayments && <div className="actions"><Link className="backLink" href="/cash">Abrir caixa →</Link><Link className="backLink" href="/manage">Gestão →</Link><Link className="backLink" href="/refunds">Estornos →</Link></div>}</header>}{tableMode && !fresh && <p className="notice" data-state="warning">Dados desatualizados. Atualize antes de confirmar.</p>}{tableMode && !standaloneCreate && <button className="buttonQuiet" aria-label="Histórico" title="Histórico de comandas" disabled={correctionPending || confirming || !!orderIntent.pending} onClick={() => setShowHistory(true)}><OperationalIcon name="history" size={20} /></button>}{success && <p className="notice" role="status" data-state="success">{success}</p>}{message && <div className="notice" role="alert" data-state="danger">{message}</div>}{orderIntent.message && <p className="notice" role="alert" data-state="warning">{orderIntent.message}</p>}{orderIntent.pending && (!selected || ["CLOSED", "CANCELLED"].includes(selected.state)) && <section className="panel" aria-label="Pedido pendente"><OperationalHeading as="h2" icon="cart">Pedido aguardando confirmação</OperationalHeading><p>Comanda original · Itens: {orderIntent.pending.payload.lines.reduce((n, l) => n + l.quantity, 0)}. Confira a mesma operação antes de enviar outro pedido.</p><button className="buttonPrimary" disabled={orderIntent.busy || cashPending} onClick={() => void orderIntent.submit(undefined, apiRoot)}>{orderIntent.busy ? "Verificando…" : "Verificar mesmo pedido"}</button></section>}{(selecting || opening) && <p className="notice" role="status">Abrindo comanda… O rascunho atual está preservado.</p>}<fieldset className="workspaceLock" disabled={repeatLoading || cashPending || selecting || opening || !orderIntent.ready || orderIntent.busy || (!!orderIntent.pending && !selected)}>{(!tableMode || standaloneCreate) && <section className="panel">{withoutPayments ? <div className="attendanceOpenHeading"><OperationalHeading as="h2" icon="cart">Abrir comanda</OperationalHeading><button className="buttonQuiet" aria-label="Histórico" title="Histórico de comandas" aria-haspopup="dialog" disabled={correctionPending || confirming || !!orderIntent.pending} onClick={() => setShowHistory(true)}><OperationalIcon name="history" size={20} /></button></div> : <OperationalHeading as="h2" icon="cart">Abrir comanda</OperationalHeading>}{withoutPayments ? <div className="field"><label htmlFor="attendance-tab-name">Nome da Comanda</label><input id="attendance-tab-name" aria-label="Nome da Comanda" maxLength={120} required value={label} onChange={(event) => setLabel(event.target.value)} placeholder="Ex.: João" /></div> : <details><summary>Identificar por nome (opcional)</summary><div className="field"><input aria-label="Apelido da comanda (opcional)" value={label} onChange={(event) => setLabel(event.target.value)} placeholder="Apelido opcional" /></div></details>}<button className="buttonPrimary" disabled={correctionPending || opening || !fresh || confirming || !!orderIntent.pending || (withoutPayments && !label.trim())} onClick={() => void createTab()}>{withoutPayments ? "Abrir comanda" : "Abrir"}</button></section>}{!tableMode && <section className="panel"><OperationalHeading as="h2" icon="receipt">Comandas abertas</OperationalHeading>{!withoutPayments && <button className="buttonQuiet" aria-pressed={showHistory} onClick={() => setShowHistory(value => !value)}>{showHistory ? "Ocultar histórico de comandas encerradas" : "Ver histórico de comandas encerradas"}</button>}{searchControls("tab-search")}{pagination}{tabs.filter(tab => ((!withoutPayments && showHistory) || !["CLOSED", "CANCELLED"].includes(tab.state))).map((tab) => <button className={withoutPayments && selected?.id === tab.id ? "buttonSecondary attendanceTabOption attendanceTabOptionActive" : "buttonSecondary attendanceTabOption"} key={tab.id} disabled={correctionPending || confirming || !!orderIntent.pending} aria-expanded={withoutPayments ? selected?.id === tab.id && !tabCollapsed : undefined} aria-controls={withoutPayments && selected?.id === tab.id ? "attendance-selected-tab" : undefined} onClick={() => void selectTab(tab)}>{tabPrimaryLabel(tab)} · {tabSecondaryLabel(tab)} · {money(tab.exposure_cents)}</button>)}</section>}{withoutPayments && showHistory && <AttendanceTabHistory searchControls={searchControls("history-tab-search")} pagination={pagination} tabs={tabs.filter(tab => ["CLOSED", "CANCELLED"].includes(tab.state))} apiRoot={apiRoot} onClose={() => setShowHistory(false)} />}{selected && !standaloneCreate && <section ref={selectedSection} className={withoutPayments ? "panel attendanceSelectedTab" : "panel"}>{withoutPayments ? tableMode ? <h2 tabIndex={-1} className="attendanceDialogBalance" aria-label={tabPrimaryLabel(selected)}>Saldo aberto <strong>{money(selected.exposure_cents)}</strong></h2> : <h2 tabIndex={-1} className="attendanceTabTitle" aria-label={tabPrimaryLabel(selected)}><button className="attendanceTabToggle" aria-expanded={!tabCollapsed} aria-controls="attendance-selected-tab" disabled={correctionPending || confirming || !!orderIntent.pending || closing} onClick={() => setTabCollapsed(value => !value)}><span className="attendanceTabCaption">Comanda selecionada</span><span>{tabPrimaryLabel(selected)}</span><small className="muted">{tabSecondaryLabel(selected)}</small><span className="attendanceSelectedBalance">Saldo aberto · {money(selected.exposure_cents)}</span><span className="attendanceTabHint">{tabCollapsed ? "Expandir ▾" : "Recolher ▴"}</span></button></h2> : <OperationalHeading tabIndex={-1} as="h2" icon="cart">{tabPrimaryLabel(selected)}</OperationalHeading>}<div id={withoutPayments ? "attendance-selected-tab" : undefined} hidden={withoutPayments && tabCollapsed}>
{withoutPayments && <nav className="attendanceOrderShortcuts" aria-label="Nesta comanda">{tableMode && <span className="attendanceOrderDestination">{selected.table_label ? `Mesa ${selected.table_label} · ` : ""}{selected.display_label || tabReference(selected)} · {tabReference(selected)}</span>}<button className="buttonSecondary" aria-pressed={tableMode ? dialogView === "catalog" : undefined} onClick={() => jumpTo("catalog")}><OperationalIcon name="cart" size={20} />Cardápio</button><button className="buttonSecondary" aria-pressed={tableMode ? dialogView === "draft" : undefined} onClick={() => jumpTo("draft")}><OperationalIcon name="receipt" size={20} /><span>Pedido atual · {rows.reduce((sum, row) => sum + row.quantity, 0)} itens<small>{money(total)} · não enviado</small></span></button><button className="buttonSecondary" aria-pressed={tableMode ? dialogView === "bill" : undefined} onClick={() => jumpTo("bill")}><OperationalIcon name="wallet" size={20} />Conta</button></nav>}
<div hidden={tableMode && dialogView !== "draft"}>
{cart.length > 0 && <><p className="muted">Este rascunho pertence a esta comanda. Confirme ou descarte antes de fechar.</p><button className="buttonQuiet" disabled={correctionPending || confirming || !!orderIntent.pending} onClick={() => setDiscardDialog(true)}>Descartar rascunho</button></>}
{discardDialog && <ActionDialog title="Descartar rascunho?" onClose={() => setDiscardDialog(false)}><p>Descartar somente os itens não enviados de {selected.display_label || "esta comanda"}?</p><button className="buttonDanger buttonDangerReadable" onClick={() => { if (orderIntent.pending || cashPending || correctionPending || switching.current) return; setCart([]); setDiscardDialog(false); }}>Confirmar descarte</button></ActionDialog>}
{!withoutPayments && <><BillSummary bill={selected} />{!!selected.orders?.length && <section aria-label="Histórico de pedidos"><OperationalHeading as="h2" icon="cart">Pedidos confirmados</OperationalHeading>{repeatLoading && <p role="status">Conferindo rodada… O rascunho está preservado.</p>}{selected.orders.map((order, index) => <section key={order.id} aria-label={`Rodada ${index + 1}`}><div className="actions"><h3>Rodada {index + 1}</h3><button className="buttonSecondary" aria-label={`Repetir rodada ${index + 1}`} disabled={!repeatAllowed || !!repeatReview} onClick={() => void startRepeat(order.id)}>Mais uma rodada</button></div>{order.items.filter(item => item.state !== "CANCELLED").map(item => <div className="dataRow" key={item.id}><div><strong>{item.quantity}× {item.product_name}</strong><CustomizationText snapshot={item.customization_snapshot} /></div></div>)}</section>)}</section>}</>}{withoutPayments && !["CLOSED", "CANCELLED"].includes(selected.state) && <AttendanceDraft rows={rows} locked={!orderIntent.ready || orderIntent.busy || correctionPending || confirming || !!orderIntent.pending} fresh={fresh} onQuantity={(index, delta) => setCart(current => current.flatMap((line, i) => i !== index ? [line] : line.quantity + delta <= 0 ? [] : [{ ...line, quantity: Math.min(99, line.quantity + delta) }]))} onEdit={index => { setConfiguring(rows[index].product); setEditing(index); }}><button className="buttonPrimary" disabled={correctionPending || !rows.length || confirming || (!orderIntent.pending && (!fresh || rows.some(row => !row.product.active || row.product.availability !== "AVAILABLE" || !!selectionError(row.product, row.selection))))} onClick={() => void confirm()}>{confirming ? "Confirmando…" : orderIntent.pending ? "Verificar mesmo pedido" : `Confirmar pedido · ${money(total)}`}</button></AttendanceDraft>}</div>{withoutPayments && <section hidden={tableMode && dialogView !== "bill"}><OperationalHeading as="h2" icon="cart">Pedidos confirmados</OperationalHeading>{repeatLoading && <p role="status">Conferindo rodada… O rascunho está preservado.</p>}{selected.orders?.map((order, index) => <section key={order.id} aria-label={`Rodada ${index + 1}`}><div className="actions"><h3>Rodada {index + 1}</h3><button className="buttonSecondary" aria-label={`Repetir rodada ${index + 1}`} disabled={!repeatAllowed || !!repeatReview} onClick={() => void startRepeat(order.id)}>Mais uma rodada</button></div>{order.items.filter(item => item.state !== "CANCELLED").map(item => <article className="attendanceConfirmedItem" key={item.id}>
  <div className="attendanceConfirmedDescription"><strong>{item.quantity}× {item.product_name}</strong><CustomizationText snapshot={item.customization_snapshot} /><small className="attendanceConfirmedPrice">{typeof item.unit_price_cents !== "number" ? "Preço histórico não informado" : `${money(item.unit_price_cents)} un. · ${money(item.unit_price_cents * item.quantity)}`}</small>
    {["PREPARING", "READY", "PICKED_UP", "DELIVERED"].includes(item.state) && <small className="muted">Retirada exige revisão da gerência.</small>}
  </div>
  <div className="attendanceConfirmedActions"><span className="attendanceConfirmedStatus">{({ NEW: "Novo", ACCEPTED: "Aceito", PREPARING: "Em preparo", READY: "Pronto", PICKED_UP: "Retirado", DELIVERED: "Entregue", CANCELLED: "Cancelado" } as Record<string, string>)[item.state] || item.state}</span>
    {["NEW", "ACCEPTED"].includes(item.state) && !["CLOSED", "CANCELLED"].includes(selected.state) && <button className="buttonDanger attendanceRemoveItem" aria-label={`Remover ${item.quantity}× ${item.product_name}`} title={`Remover ${item.product_name}`} disabled={correctionPending || confirming || !!orderIntent.pending || !fresh} onClick={() => setRemovingItem(item)}><OperationalIcon name="trash" size={20} /></button>}
  </div>
</article>)}</section>)}</section>}{withoutPayments && configuring && <ActionDialog title={`Personalizar ${configuring.name}`} onClose={() => { setConfiguring(null); setEditing(null); }}><ProductCustomization key={`${configuring.id}-${editing}`} product={products.find(p => p.id === configuring.id) ?? configuring} canSubmit={editing !== null || (fresh && products.some(p => p.id === configuring.id && p.active && p.availability === "AVAILABLE"))} initial={editing === null ? undefined : cart[editing]?.selection} onCancel={() => { setConfiguring(null); setEditing(null); }} onAdd={selection => { if (editing === null) addDraftLine(configuring, selection); else setCart(c => c.map((r, i) => i === editing ? { ...r, selection } : r)); setConfiguring(null); setEditing(null); }} /></ActionDialog>}{withoutPayments && removingItem && <ConfirmedItemRemoval item={selected.orders?.flatMap(order => order.items).find(item => item.id === removingItem.id) ?? removingItem} onPendingChange={setCorrectionPending} onClose={() => setRemovingItem(null)} onRefresh={async () => { const detail = await apiCall<Tab>(`${apiRoot}/tabs/${selected.id}/`); if (!detail.response.ok) throw new Error("Falha ao atualizar comanda."); setSelected(detail.body as Tab); await load(); }} />}{!withoutPayments && <ReceiptPrinting key={selected.id} tabId={selected.id} closed={selected.state === "CLOSED"} />}<div hidden={tableMode && dialogView !== "catalog"}>{!["CLOSED", "CANCELLED"].includes(selected.state) && <>{!withoutPayments && <PricingAdjustments key={selected.id} tabId={selected.id} version={selected.version} onChanged={async () => { const detail = await apiCall<Tab>(`${apiRoot}/tabs/${selected.id}/`); if (detail.response.ok) setSelected(detail.body as Tab); await load(); }} />}<div tabIndex={withoutPayments ? -1 : undefined} data-attendance-region={withoutPayments ? "catalog" : undefined}><OperationalHeading as="h2" icon="cart" className="posSectionTitle">Catálogo</OperationalHeading></div>{withoutPayments && <>
{<div className="field"><label htmlFor="attendance-catalog-search">Buscar item no cardápio</label><input id="attendance-catalog-search" type="search" value={catalogSearch} onChange={event => setCatalogSearch(event.target.value)} placeholder="Nome da bebida ou comida" /></div>}
<nav className="actions attendanceCategories" aria-label="Categorias do cardápio">{categories.map(name => <button key={name} className={activeCategory === name && !catalogCollapsed && !query ? "buttonPrimary" : "buttonSecondary"} aria-pressed={activeCategory === name && !catalogCollapsed && !query} aria-expanded={activeCategory === name && !catalogCollapsed && !query} onClick={() => { setCatalogCollapsed(activeCategory === name && !query ? !catalogCollapsed : false); setCategory(name); setCatalogSearch(""); }}>{name} ({name === "Todos" ? catalog.length : catalog.filter(product => attendanceCategory(product) === name).length})</button>)}</nav>
{catalogVisible && <p role="status" className="muted">{query ? `Busca em todas as categorias · ${visibleProducts.length} itens` : `${activeCategory || "Cardápio"} · ${visibleProducts.length} itens`}</p>}
{catalogVisible && !visibleProducts.length && <p>Nenhum item encontrado.</p>}
</>}{withoutPayments && <p className="attendanceDraftFeedback" role="status">{draftFeedback}</p>}<div className="posProducts" hidden={withoutPayments && !catalogVisible}>{visibleProducts.map((product) => tableMode ? <AttendanceCatalogCard key={product.id} product={product} quantity={rows.filter(row => row.product.id === product.id).reduce((sum, row) => sum + row.quantity, 0)} configurations={rows.filter(row => row.product.id === product.id).length} locked={correctionPending || confirming || !!orderIntent.pending} fresh={fresh} onAdd={() => { if (product.variants?.length || product.modifier_groups?.length) { setEditing(null); setConfiguring(product); } else addDraftLine(product, defaults(product)); }} onReduce={() => { const matches = rows.flatMap((row, index) => row.product.id === product.id ? [index] : []); if (matches.length !== 1) { jumpTo("draft"); return; } setCart(current => current.flatMap((line, index) => index !== matches[0] ? [line] : line.quantity <= 1 ? [] : [{ ...line, quantity: line.quantity - 1 }])); }} onCustomize={() => { setEditing(null); setConfiguring(product); }} /> : <button key={product.id} className="buttonSecondary posProduct" data-selected={withoutPayments && rows.some(row => row.product.id === product.id)} disabled={correctionPending || !fresh || !product.active || product.availability !== "AVAILABLE" || confirming || !!orderIntent.pending} onClick={() => { if (product.variants?.length || product.modifier_groups?.length) { setEditing(null); setConfiguring(product); } else addDraftLine(product, defaults(product)); }}><ProductIcon name={product.name} icon={product.icon} /><span><strong>{product.name}</strong><small>{money(product.price_cents)}{product.availability !== "AVAILABLE" ? " · Indisponível" : ""}</small></span>{withoutPayments && <span className="attendanceProductAction" aria-hidden="true">{product.availability !== "AVAILABLE" ? "Indisponível" : rows.some(row => row.product.id === product.id) ? `${rows.filter(row => row.product.id === product.id).reduce((sum, row) => sum + row.quantity, 0)} no pedido · +` : "+ Adicionar"}</span>}</button>)}</div>{!withoutPayments && configuring && (withoutPayments ? <ActionDialog title={`Personalizar ${configuring.name}`} onClose={() => { setConfiguring(null); setEditing(null); }}><ProductCustomization key={`${configuring.id}-${editing}`} product={products.find(p => p.id === configuring.id) ?? configuring} canSubmit={editing !== null || (fresh && products.some(p => p.id === configuring.id && p.active && p.availability === "AVAILABLE"))} initial={editing === null ? undefined : cart[editing]?.selection} onCancel={() => { setConfiguring(null); setEditing(null); }} onAdd={selection => { if (editing === null) addDraftLine(configuring, selection); else setCart(c => c.map((r, i) => i === editing ? { ...r, selection } : r)); setConfiguring(null); setEditing(null); }} /></ActionDialog> : <ProductCustomization key={`${configuring.id}-${editing}`} product={products.find(p => p.id === configuring.id) ?? configuring} canSubmit={editing !== null || (fresh && products.some(p => p.id === configuring.id && p.active && p.availability === "AVAILABLE"))} initial={editing === null ? undefined : cart[editing]?.selection} onCancel={() => { setConfiguring(null); setEditing(null); }} onAdd={selection => { if (editing === null) addDraftLine(configuring, selection); else setCart(c => c.map((r, i) => i === editing ? { ...r, selection } : r)); setConfiguring(null); setEditing(null); }} />)}{!withoutPayments && <section aria-label="Pedido atual">{rows.map((row, index) => <div className={withoutPayments ? "dataRow attendanceCartRow" : "dataRow"} key={index}><div><strong>{row.quantity}× {row.product.name}</strong><CustomizationText snapshot={{ variant: row.product.variants?.find(v => v.id === row.selection.variant_id), modifiers: row.product.modifier_groups?.flatMap(g => g.options.filter(o => row.selection.modifier_option_ids.includes(o.id)).map(o => ({ ...o, group_name: g.name }))), special_instructions: row.selection.special_instructions }} />{selectionError(row.product, row.selection) && <p className="notice" data-state="danger">{selectionError(row.product, row.selection)}</p>}</div><div className="actions">{withoutPayments && <div className="field"><label htmlFor={`quantity-${index}`}>Quantidade de {row.product.name}</label><input id={`quantity-${index}`} type="number" min={1} max={99} value={row.quantity} disabled={correctionPending || confirming || !!orderIntent.pending} onChange={e => setCart(c => c.map((line, i) => i === index ? { ...line, quantity: Math.max(1, Math.min(99, Math.trunc(Number(e.target.value)) || 1)) } : line))} /></div>}<button className="buttonQuiet" disabled={correctionPending || confirming || !!orderIntent.pending} onClick={() => { setConfiguring(row.product); setEditing(index); }}>Editar</button><button className="buttonQuiet" disabled={correctionPending || confirming || !!orderIntent.pending} onClick={() => setCart(c => c.filter((_, i) => i !== index))}>Remover</button></div></div>)}<button className="buttonPrimary" disabled={correctionPending || !rows.length || confirming || (!orderIntent.pending && (!fresh || rows.some(row => !row.product.active || row.product.availability !== "AVAILABLE" || !!selectionError(row.product, row.selection))))} onClick={() => void confirm()}>{confirming ? "Confirmando…" : orderIntent.pending ? "Verificar mesmo pedido" : `Confirmar pedido · ${money(total)}`}</button></section>}{!withoutPayments && closeTabButton}</>}</div>{withoutPayments && closingDialog && <ActionDialog title="Fechar comanda?" locked={closing} onClose={() => setClosingDialog(false)}><p>Confirme o encerramento de {tabPrimaryLabel(selected)}.</p>{message && <p className="notice" role="alert" data-state="danger">{message}</p>}<button className="buttonSecondary" disabled={closing || selected.exposure_cents !== 0} onClick={() => void close()}>{closing ? "Verificando…" : "Confirmar fechamento"}</button></ActionDialog>}{withoutPayments && <section hidden={tableMode && dialogView !== "bill"} aria-label="Valores da comanda" tabIndex={-1} data-attendance-region="bill"><OperationalHeading as="h2" icon="receipt">Resumo da comanda</OperationalHeading><BillSummary key={selected.id} bill={selected} compact /></section>}{withoutPayments && (!tableMode || dialogView === "bill") && closeTabButton}</div></section>}</fieldset>{repeatReview && <RepeatOrderDialog review={repeatReview.review} enabled={repeatAllowed && repeatUnchanged} onAdd={quantities => void confirmRepeatedOrder(quantities)} onClose={() => setRepeatReview(null)} />}{!withoutPayments && <PosCashReceipt tab={selected} points={cashPoints} locked={!orderIntent.ready || orderIntent.busy || correctionPending || confirming || !!orderIntent.pending || closing || selecting || opening || repeatLoading || !!repeatReview} onPendingChange={setCashPending} onConfirmed={async tabId => {
  const detail = await apiCall<Tab>(`${apiRoot}/tabs/${tabId}/`);
  if (!detail.response.ok) throw new Error("Não foi possível atualizar o saldo.");
  setSelected(detail.body as Tab); await load();
}} />}</section>;
  const dialogLocked = correctionPending || cashPending || !orderIntent.ready || orderIntent.busy || !!orderIntent.pending || confirming || selecting || opening || closing || repeatLoading || !!repeatReview || !!configuring || discardDialog || closingDialog || !!removingItem || showHistory;
  return tableMode ? <ActionDialog open={dialogOpen} dialogClassName="attendanceOrderDialog" title={selected && !standaloneCreate ? `${selected.table_label ? `Mesa ${selected.table_label}` : destinationLabel || "Comanda"} · ${selected.display_label || tabReference(selected)} · ${tabReference(selected)}` : "Comandas"} locked={dialogLocked} onClose={() => { if (dialogLocked) return; setDialogOpen(false); onDialogClose?.(); }}>{workspace}</ActionDialog> : workspace;
}
