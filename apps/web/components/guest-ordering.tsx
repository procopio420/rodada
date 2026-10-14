"use client";
import { guestItemStatus } from "@/lib/client/guest-status";
import { tabPrimaryLabel, tabSecondaryLabel } from "@/lib/client/tab-identity";

import { OperationalHeading } from "@/components/operational-heading";

import { BillSummary } from "./bill-summary";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { useRealtime } from "@/lib/client/use-realtime";
import { guestApi } from "@/lib/client/guest-api";
import { guestOrderStorageKey, useGuestOrderIntent, validScope, sameScope, type GuestScope } from "@/lib/client/guest-order-intent";
import { RepeatOrderDialog, reviewRepeatedOrder } from "./repeat-order";
import { ConnectivityNotice } from "./connectivity-notice";
import { ProductIcon, type IconData } from "./product-icon";
import { attendanceCategory, compareAttendanceCategories, normalizeCatalogSearch } from "@/lib/client/attendance-catalog";

import { ProductCustomization, CustomizationText, defaults, selectionError, unitPrice, type OrderingProduct, type Selection, type Snapshot } from "./product-customization";

type Product = OrderingProduct & { category?: string; id: string; name: string; price_cents: number; fulfillment_station: string; available: boolean; icon?: IconData };
type OrderItem = { product_id?: string; unit_price_cents?: number; customization_snapshot?: Snapshot; id: string; product_name: string; quantity: number; line_total_cents: number; state: string; ready_at?: string | null; delivered_at?: string | null };
type Order = { id: string; status: string; items: OrderItem[] };
type Tab = import("./bill-summary").Bill & { id: string; state?: string; display_label: string; table_label?: string | null; last_table_label?: string | null; exposure_cents: number; consumption_blocked: boolean; remaining_capacity_cents: number; orders?: Order[] };
type Context = { session_scope?: GuestScope; guest_policy?: { emergency_blocked: boolean; table_ordering_enabled?: boolean }; table: { label: string }; occupancy_active: boolean; can_start_occupancy: boolean; guest_session_token?: string; tab: Tab | null };
const repeatCatalog = (products: Product[]) => products.map(product => ({ ...product, active: true, availability: product.available ? "AVAILABLE" : "UNAVAILABLE" }));
type RepeatReview = { token: string; scope: GuestScope; tabId: string; orderId: string; review: ReturnType<typeof reviewRepeatedOrder<ReturnType<typeof repeatCatalog>[number]>> };
type ApiError = { code?: string; message?: string };

const money = (value = 0) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value / 100);

const repeatSuccessMessage = "Rodada adicionada ao carrinho. Confira antes de enviar o novo pedido.";
type DraftLine = { product: Product; selection: Selection; quantity: number };
function groupedDraft(lines: DraftLine[]): DraftLine[] | null {
  const result: DraftLine[] = [];
  for (const line of lines) {
    const same = result.find(row => row.product.id === line.product.id && row.selection.variant_id === line.selection.variant_id &&
      row.selection.special_instructions === line.selection.special_instructions &&
      JSON.stringify([...row.selection.modifier_option_ids].sort()) === JSON.stringify([...line.selection.modifier_option_ids].sort()));
    if (same) same.quantity += line.quantity;
    else result.push({ ...line });
  }
  return result.some(line => !Number.isInteger(line.quantity) || line.quantity < 1 || line.quantity > 99) ? null : result;
}
const quantityLimitMessage = "A quantidade agrupada ultrapassa 99. Reduza o item antes de adicionar ou editar; seu carrinho foi preservado.";

function messageFor(error: ApiError, fallback: string) {
  if (error.code === "GUEST_SESSION_REVOKED") return "Esta visita terminou. Escaneie o QR novamente para pedir na nova ocupação.";
  if (error.code === "GUEST_ORDERING_BLOCKED") return "Os pedidos por QR estão pausados. Peça ajuda à equipe.";
  if (error.code === "PRODUCTS_NOT_CONFIRMABLE") return "Um item do carrinho acabou de ficar indisponível. Atualize o pedido.";
  if (error.code === "SPENDING_LIMIT_EXCEEDED") return "Seu consumo precisa de atenção da equipe. Peça um pagamento parcial ou uma aprovação para continuar.";
  return error.message || fallback;
}

export function GuestOrdering({ qrToken }: { qrToken: string }) {
  const [catalogSearch, setCatalogSearch] = useState("");
  const [category, setCategory] = useState("Todos");
  const draftRegion = useRef<HTMLElement | null>(null);
  const catalogRegion = useRef<HTMLElement | null>(null);
  const ordersRegion = useRef<HTMLElement | null>(null);
  const billRegion = useRef<HTMLElement | null>(null);
  function visitRegion(region: HTMLElement | null) {
    region?.scrollIntoView({ block: "start" });
    region?.focus({ preventScroll: true });
  }
  const storageKey = `rodada.guest.session.${qrToken}`;
  const [guestToken, setGuestToken] = useState("");
  const [context, setContext] = useState<Context | null>(null);
  const [catalogCachedAt, setCatalogCachedAt] = useState<number>();
  const [products, setProducts] = useState<Product[]>([]);
  const [cart, setCart] = useState<{ product: Product; quantity: number; selection: Selection }[]>([]);
  const [configuring, setConfiguring] = useState<Product | null>(null);
  const [editing, setEditing] = useState<number | null>(null);
  const [label, setLabel] = useState("");
  const [receipt, setReceipt] = useState("");
  const [receiptError, setReceiptError] = useState("");
  useEffect(() => { setReceipt(""); setReceiptError(""); }, [guestToken, context?.tab?.id]);
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [stale, setStale] = useState(true);
  const [repeatLoading, setRepeatLoading] = useState(false);
  const [repeatReview, setRepeatReview] = useState<RepeatReview | null>(null);
  const repeatReading = useRef(false);
  const repeatConsumed = useRef(false);
  const currentVisit = useRef({ token: guestToken, context });
  useLayoutEffect(() => { currentVisit.current = { token: guestToken, context }; }, [guestToken, context]);
  useEffect(() => { queueMicrotask(() => setRepeatReview(null)); }, [guestToken, context?.tab?.id]);
  const orderIntent = useGuestOrderIntent(qrToken, guestToken, detail => {
    setContext(detail as Context); setCart([]); setNotice("");
  });
  const [requestSending, setRequestSending] = useState(false);
  const [serviceNotice, setServiceNotice] = useState("");
  const [serviceError, setServiceError] = useState(false);

  async function requestService(taskType: "SERVICE_REQUEST" | "BILL_REQUEST") {
    if (!context?.occupancy_active || requestSending || stale || repeatReading.current || repeatReview) return;
    const intentKey = `${storageKey}.request.${guestToken}.${taskType}`;
    let requestId: string;
    try {
      requestId = sessionStorage.getItem(intentKey) || crypto.randomUUID();
      sessionStorage.setItem(intentKey, requestId);
    } catch {
      setServiceError(true);
      setServiceNotice("Não foi possível guardar sua solicitação com segurança. Chame a equipe pessoalmente.");
      return;
    }
    setRequestSending(true);
    setServiceNotice("");
    const result = await guestApi<{ id: string; state: string }>("service-requests/", guestToken, {
      method: "POST", body: JSON.stringify({ request_id: requestId, task_type: taskType }),
    });
    setRequestSending(false);
    setServiceError(!result.ok);
    if (result.ok) {
      sessionStorage.removeItem(intentKey);
      setServiceNotice(taskType === "BILL_REQUEST" ? "Pedido de conta recebido pela equipe." : "Chamada de atendimento recebida pela equipe.");
    } else {
      // Preserve identity after ambiguous network/server outcomes for safe retry.
      if (result.status < 500) sessionStorage.removeItem(intentKey);
      setServiceNotice(messageFor(result.body as ApiError, "Não foi possível enviar sua chamada. Tente novamente ou chame a equipe."));
    }
  }

  const loadCatalog = useCallback(async (token: string) => {
    const result = await guestApi<{ results: Product[] }>("catalog/", token);
    if (result.ok) {
      const next = (result.body as { results: Product[] }).results;
      setProducts(previous => JSON.stringify(previous) === JSON.stringify(next) ? previous : next);
      try { sessionStorage.setItem(`rodada.guest.catalog.${qrToken}`, JSON.stringify({ products: next, fetchedAt: Date.now() })); } catch {}
      return true;
    }
    setNotice(messageFor(result.body as ApiError, "Não foi possível atualizar o cardápio."));
    return false;
  }, [qrToken]);

  const resolve = useCallback(async () => {
    setLoading(true);
    setNotice("");
    try { const cached = JSON.parse(sessionStorage.getItem(`rodada.guest.catalog.${qrToken}`) || "null"); if (cached) { setProducts(cached.products); setCatalogCachedAt(cached.fetchedAt); } } catch {}
    const stored = qrToken;
    let recovering: boolean;
    try { sessionStorage.removeItem(storageKey); recovering = sessionStorage.getItem(guestOrderStorageKey(qrToken)) !== null; }
    catch { setNotice("Não foi possível acessar sua sessão. Peça ajuda à equipe."); setLoading(false); return; }
    const result = recovering ? await guestApi<Context>("context/", stored) : await guestApi<Context>("qr/resolve/", stored, {
      method: "POST", body: JSON.stringify({ token: qrToken }),
    });
    if (!result.ok) {
      if ((result.body as ApiError).code === "GUEST_SESSION_REVOKED") sessionStorage.removeItem(storageKey);
      setNotice(messageFor(result.body as ApiError, "Não foi possível abrir esta mesa."));
      setLoading(false);
      return;
    }
    const body = result.body as Context;
    const token = stored;
    if (!token) {
      setNotice("Não foi possível iniciar sua sessão. Escaneie o QR novamente.");
      setLoading(false);
      return;
    }
    // Authorization stays in a host-only HttpOnly cookie, never sessionStorage.
    setGuestToken(token);
    setContext(body);
    await loadCatalog(token);
    setLoading(false);
  }, [loadCatalog, qrToken, storageKey]);

  useEffect(() => { void resolve(); }, [resolve]);

  const refresh = useCallback(async () => {
    if (!guestToken) return;
    const result = await guestApi<Context>("context/", guestToken);
    if (result.ok) {
      const next = result.body as Context;
      setContext(current => ({ ...next, tab: next.tab ? { ...next.tab, orders: next.tab.orders ?? (current?.tab?.id === next.tab.id ? current.tab.orders : undefined) } : null }));
      setNotice("");
      const healthy = await loadCatalog(guestToken);
      setStale(!healthy);
      if (!healthy) throw new Error("Catalog unavailable");
    }
    else {
      setStale(true); setNotice(messageFor(result.body as ApiError, "Atualize sua comanda antes de continuar."));
      if (["GUEST_SESSION_REVOKED", "GUEST_SESSION_EXPIRED", "GUEST_SESSION_INVALID", "GUEST_SESSION_REQUIRED"].includes((result.body as ApiError).code ?? "")) { setContext(null); sessionStorage.removeItem(storageKey); }
      throw new Error("Context unavailable");
    }
  }, [guestToken, loadCatalog, storageKey]);
  const connectivity = useRealtime(refresh, { guestToken, onRevoked: () => {
    sessionStorage.removeItem(storageKey); setContext(null); setProducts([]); setCart([]); setStale(true);
    setNotice("Esta visita terminou. Escaneie o QR novamente para pedir na nova ocupação.");
  } });

  const rows = useMemo(() => cart.map(row => ({ ...row, product: products.find(p => p.id === row.product.id) ?? { ...row.product, available: false } })), [cart, products]);
  const total = rows.reduce((sum, row) => sum + unitPrice(row.product, row.selection) * row.quantity, 0);
  const cartError = rows.some(row => !row.product.available || !!selectionError(row.product, row.selection));
  const categories = [...new Set(products.map(attendanceCategory))].sort(compareAttendanceCategories);
  const activeCategory = categories.includes(category) ? category : "Todos";
  const query = normalizeCatalogSearch(catalogSearch);
  const visibleProducts = products.filter(product => query ? normalizeCatalogSearch(product.name).includes(query) : activeCategory === "Todos" || attendanceCategory(product) === activeCategory);
  const repeatAllowed = !loading && !sending && !requestSending && !repeatLoading && !stale && !orderIntent.locked && !configuring &&
    !!guestToken && validScope(context?.session_scope) && !!context?.occupancy_active && !!context.tab &&
    !["CLOSED", "CANCELLED"].includes(context.tab.state ?? "") && !context.tab.consumption_blocked &&
    !context.guest_policy?.emergency_blocked && context.guest_policy?.table_ordering_enabled === true;
  const repeatOrder = context?.tab?.orders?.find(order => order.id === repeatReview?.orderId);
  const repeatUnchanged = !!repeatReview && guestToken === repeatReview.token && validScope(context?.session_scope) &&
    sameScope(context.session_scope, repeatReview.scope) && context.tab?.id === repeatReview.tabId && !!repeatOrder &&
    JSON.stringify(reviewRepeatedOrder(repeatOrder, repeatCatalog(products))) === JSON.stringify(repeatReview.review);

  async function readRepeatVisit(expected: Pick<RepeatReview, "token" | "scope" | "tabId">) {
    const [detail, catalog] = await Promise.all([guestApi<Context>("context/", expected.token), guestApi<{ results: Product[] }>("catalog/", expected.token)]);
    if (!detail.ok) throw detail.body;
    if (!catalog.ok) throw catalog.body;
    const next = detail.body as Context, currentProducts = (catalog.body as { results: Product[] }).results;
    const live = currentVisit.current;
    if (live.token !== expected.token ||
      !validScope(live.context?.session_scope) || !sameScope(live.context.session_scope, expected.scope) || live.context.tab?.id !== expected.tabId ||
      !validScope(next.session_scope) || !sameScope(next.session_scope, expected.scope) || next.tab?.id !== expected.tabId || !next.occupancy_active)
      throw { message: "Esta rodada pertence à visita original. Ela não será incluída em outra sessão ou comanda." };
    if (!Array.isArray(currentProducts)) throw { message: "Cardápio indisponível. Atualize antes de repetir." };
    setContext(next); setProducts(currentProducts);
    if (next.guest_policy?.table_ordering_enabled !== true || next.guest_policy.emergency_blocked)
      throw { code: "GUEST_ORDERING_BLOCKED" };
    if (["CLOSED", "CANCELLED"].includes(next.tab.state ?? "") || next.tab.consumption_blocked)
      throw { message: "Sua comanda precisa de atenção da equipe antes de repetir." };
    return { next, currentProducts };
  }
  async function startRepeat(orderId: string) {
    if (!repeatAllowed || repeatReview || repeatReading.current || !validScope(context?.session_scope) || !context.tab) return;
    repeatReading.current = true; repeatConsumed.current = false; setRepeatLoading(true); setNotice("");
    const expected = { token: guestToken, scope: { ...context.session_scope }, tabId: context.tab.id };
    try {
      const { next, currentProducts } = await readRepeatVisit(expected);
      const order = next.tab!.orders?.find(order => order.id === orderId);
      if (!order) throw { message: "Rodada indisponível. Atualize seu histórico." };
      setRepeatReview({ ...expected, orderId, review: reviewRepeatedOrder(order, repeatCatalog(currentProducts)) });
    } catch (error) { setNotice(messageFor(error as ApiError, "Não foi possível conferir a rodada. Seu carrinho foi preservado.")); setStale(true); }
    finally { repeatReading.current = false; setRepeatLoading(false); }
  }
  async function addRepeatedDraft() {
    if (!repeatAllowed || !repeatUnchanged || !repeatReview?.review.canAdd || repeatReading.current || repeatConsumed.current) return;
    repeatReading.current = true; setRepeatLoading(true); setNotice("");
    try {
      const { next, currentProducts } = await readRepeatVisit(repeatReview);
      const order = next.tab!.orders?.find(order => order.id === repeatReview.orderId);
      const current = order && reviewRepeatedOrder(order, repeatCatalog(currentProducts));
      if (!current?.canAdd || JSON.stringify(current) !== JSON.stringify(repeatReview.review))
        throw { message: "A rodada mudou. Feche e abra novamente a revisão." };
      const grouped = groupedDraft([...cart, ...current.lines.map(({ product, quantity, selection }) => ({ product, quantity, selection }))]);
      if (!grouped) throw { message: quantityLimitMessage };
      repeatConsumed.current = true;
      setCart(grouped);
      setRepeatReview(null); setNotice(repeatSuccessMessage);
    } catch (error) { setNotice(messageFor(error as ApiError, "Não foi possível incluir a rodada. Seu carrinho foi preservado.")); setStale(true); }
    finally { repeatReading.current = false; setRepeatLoading(false); }
  }
  function addConfigured(product: Product, selection: Selection) {
    if (repeatReading.current || repeatReview || sending || orderIntent.locked || stale || !product.available || selectionError(product, selection) ||
      !context?.occupancy_active || !context.tab || ["CLOSED", "CANCELLED"].includes(context.tab.state ?? "") || context.tab.consumption_blocked || context.guest_policy?.emergency_blocked || context.guest_policy?.table_ordering_enabled === false) return;
    const grouped = groupedDraft(editing === null ? [...cart, { product, selection, quantity: 1 }] : cart.map((row, index) => index === editing ? { ...row, product, selection } : row));
    if (!grouped) { setNotice(quantityLimitMessage); return; }
    setCart(grouped);
    setNotice("");
    setConfiguring(null); setEditing(null);
  }
  const draftLocked = repeatLoading || !!repeatReview || sending || orderIntent.locked || !!configuring;
  const increaseBlocked = stale || !context?.occupancy_active || !context.tab || ["CLOSED", "CANCELLED"].includes(context.tab.state ?? "") ||
    context.tab.consumption_blocked || context.guest_policy?.emergency_blocked || context.guest_policy?.table_ordering_enabled === false;
  function changeQuantity(index: number, delta: -1 | 1) {
    if (draftLocked || repeatReading.current || (delta === 1 && (increaseBlocked || !rows[index]?.product.available || !!selectionError(rows[index].product, rows[index].selection)))) return;
    setCart(current => current.flatMap((line, i) => i !== index ? [line] : line.quantity + delta === 0 ? [] : [{ ...line, quantity: Math.min(99, line.quantity + delta) }]));
    if (notice === quantityLimitMessage) setNotice("");
  }

  async function createTab() {
    if (sending || stale || orderIntent.locked || repeatReading.current || repeatReview) return;
    setSending(true);
    const result = await guestApi<Tab>("tabs/", guestToken, { method: "POST", body: JSON.stringify({ display_label: label }) });
    setSending(false);
    if (!result.ok) { setNotice(messageFor(result.body as ApiError, "Não foi possível abrir a comanda.")); return; }
    setContext((current) => current ? { ...current, tab: result.body as Tab } : current);
    setLabel("");
  }

  async function submitOrder() {
    if (!context?.tab || !rows.length || draftLocked || increaseBlocked || repeatReading.current || repeatReview) return;
    await orderIntent.submit({ tab: context.tab.id, lines: rows.map(({ product, quantity, selection }) => ({ product_id: product.id, quantity, ...selection })) });
  }
  const recovery = <>{orderIntent.message && <p className="notice" data-state={orderIntent.message === "Pedido confirmado." ? "success" : "warning"} role={orderIntent.message === "Pedido confirmado." ? "status" : "alert"}>{orderIntent.message}</p>}{orderIntent.pending && <section className="panel" aria-label="Pedido pendente"><OperationalHeading as="h2" icon="cart">Pedido aguardando confirmação</OperationalHeading><p>Confira o mesmo pedido antes de enviar outro. Se esta visita terminou, peça ajuda à equipe.</p><button className="buttonPrimary" disabled={repeatLoading || orderIntent.busy} onClick={() => void orderIntent.submit()}>{orderIntent.busy ? "Verificando…" : "Verificar mesmo pedido"}</button></section>}</>;

  if (loading) return <main className="appShell"><p className="muted">Abrindo sua mesa…</p></main>;
  if (!context) return <main className="appShell"><OperationalHeading as="h1" icon="cart">Não foi possível abrir o pedido</OperationalHeading><div className="notice" data-state="danger">{notice}</div>{recovery}{products.length > 0 && <section className="panel"><OperationalHeading as="h2" icon="cart">Cardápio salvo</OperationalHeading><ConnectivityNotice state="OFFLINE" syncedAt={catalogCachedAt} /><p className="muted">Preços e disponibilidade podem ter mudado. Reconecte para abrir sua comanda.</p>{products.map(product => <div className="dataRow" key={product.id}><span>{product.name}</span><strong>{money(product.price_cents)}</strong></div>)}</section>}<button className="buttonPrimary" onClick={() => void resolve()}>Tentar de novo</button></main>;

  return <main className="appShell guestShell">
    <header className="productHeader"><div className="eyebrow">RODADA / PEDIDO</div><OperationalHeading as="h1" icon="table">Mesa {context.table.label}</OperationalHeading><p className="muted">Peça quando quiser. Sua comanda continua separada da mesa.</p></header>
    {context.tab && <nav className="guestRegionNav" aria-label="Navegação do cliente">
      <button className="buttonSecondary" onClick={() => visitRegion(catalogRegion.current)}>Cardápio</button>
      <button className="buttonSecondary" onClick={() => visitRegion(ordersRegion.current)}>Pedidos</button>
      <button className="buttonSecondary" onClick={() => visitRegion(billRegion.current)}>Conta</button>
    </nav>}
    {recovery}
    <ConnectivityNotice {...connectivity} syncedAt={connectivity.syncedAt ?? catalogCachedAt} />
    {notice && <div className="notice" data-state={notice === repeatSuccessMessage ? "success" : "danger"} role={notice === repeatSuccessMessage ? "status" : "alert"}>{notice}</div>}
    {stale && <div className="notice" data-state="warning" role="status">Dados desatualizados. Reconecte para confirmar seu pedido.</div>}
    <button className="buttonQuiet" disabled={repeatLoading || sending} onClick={() => void refresh().catch(() => {})}>Atualizar comanda</button>
    {context.occupancy_active && <section className="panel" aria-labelledby="guest-service-heading">
      <OperationalHeading as="h2" id="guest-service-heading" icon="warning">Precisa da equipe?</OperationalHeading>
      <div className="actions">
        <button className="buttonSecondary" disabled={repeatLoading || requestSending || stale} onClick={() => void requestService("SERVICE_REQUEST")}>Chamar atendimento</button>
        <button className="buttonSecondary" disabled={repeatLoading || requestSending || stale} onClick={() => void requestService("BILL_REQUEST")}>Pedir conta à equipe</button>
      </div>
      {requestSending && <p role="status">Enviando solicitação…</p>}
      {serviceNotice && <p className="notice" data-state={serviceError ? "danger" : "success"} role={serviceError ? "alert" : "status"}>{serviceNotice}</p>}
    </section>}
    {!context.tab ? <section className="panel"><OperationalHeading as="h2" icon="cart">Começar pedido</OperationalHeading><p className="muted">Crie uma comanda para enviar itens ao bar e à cozinha.</p><details><summary>Adicionar nome ou apelido (opcional)</summary><div className="field"><label htmlFor="guest-label">Seu nome ou apelido (opcional)</label><input id="guest-label" value={label} onChange={(event) => setLabel(event.target.value)} placeholder="Ex.: Ana" /></div></details><button className="buttonPrimary" disabled={repeatLoading || sending || stale || orderIntent.locked} onClick={() => void createTab()}>{sending ? "Abrindo…" : "Abrir minha comanda"}</button></section> : <>
      <section className="panel panelGuestBalance" ref={billRegion} tabIndex={-1} aria-label="Conta"><span className="eyebrow">Comanda</span><OperationalHeading as="h2" icon="wallet">{tabPrimaryLabel(context.tab)}</OperationalHeading><p className="muted">{tabSecondaryLabel(context.tab)}</p><BillSummary bill={context.tab} /></section>
      {context.tab.consumption_blocked && <div className="notice" data-state="warning" role="alert">Para continuar consumindo, peça ajuda à equipe. Você pode pagar uma parte da comanda ou solicitar aprovação.</div>}
      <section className="panel" ref={catalogRegion} tabIndex={-1} aria-label="Cardápio"><OperationalHeading as="h2" icon="cart">Cardápio</OperationalHeading><div className="field"><label htmlFor="guest-catalog-search">Buscar item no cardápio</label><input id="guest-catalog-search" type="search" maxLength={120} value={catalogSearch} onChange={event => setCatalogSearch(event.target.value)} /></div><nav className="actions" aria-label="Categorias do cardápio">{["Todos", ...categories.filter(name => name !== "Todos")].map(name => <button key={name} className={activeCategory === name && !query ? "buttonPrimary" : "buttonSecondary"} aria-pressed={activeCategory === name && !query} onClick={() => { setCategory(name); setCatalogSearch(""); }}>{name} ({name === "Todos" ? products.length : products.filter(product => attendanceCategory(product) === name).length})</button>)}</nav><p role="status" className="muted">{query ? `Busca em todas as categorias · ${visibleProducts.length} itens` : `${activeCategory} · ${visibleProducts.length} itens`}</p><button className="buttonSecondary" disabled={!rows.length} onClick={() => { draftRegion.current?.scrollIntoView({ block: "start" }); draftRegion.current?.focus(); }}>Pedido atual · {rows.reduce((sum, row) => sum + row.quantity, 0)} itens</button>{!products.length ? <p>Cardápio vazio. Peça ajuda à equipe.</p> : !visibleProducts.length && <p>Nenhum item encontrado. Tente outro nome ou categoria.</p>}<div className="guestProducts">{visibleProducts.map((product) => <button key={product.id} className="buttonSecondary guestProduct" disabled={draftLocked || increaseBlocked || !product.available} onClick={() => { if (product.variants?.length || product.modifier_groups?.some(group => group.min_selections > 0)) { setEditing(null); setConfiguring(product); } else addConfigured(product, defaults(product)); }}><ProductIcon name={product.name} icon={product.icon} /><span className="guestProductDetails"><strong>{product.name}</strong><small>{product.fulfillment_station === "BAR" ? "Bar" : "Cozinha"}{!product.available ? " · Indisponível" : ""}</small></span><span className="guestProductPrice">{money(product.price_cents)}</span></button>)}</div></section>
      {configuring && <ProductCustomization key={`${configuring.id}-${editing}`} product={products.find(p => p.id === configuring.id) ?? configuring} initial={editing === null ? undefined : cart[editing]?.selection} onCancel={() => { setConfiguring(null); setEditing(null); }} onAdd={selection => addConfigured(configuring, selection)} />}
      {!!rows.length && <section className="panel" aria-label="Pedido atual" ref={draftRegion} tabIndex={-1}><OperationalHeading as="h2" icon="cart">Revisar pedido</OperationalHeading>{rows.map((row, index) => <div key={index} className="attendanceDraftLine" role="group" aria-label={`Item ${index + 1} do pedido`}><div><strong>{row.quantity}× {row.product.name}</strong><CustomizationText snapshot={{ variant: row.product.variants?.find(v => v.id === row.selection.variant_id), modifiers: row.product.modifier_groups?.flatMap(g => g.options.filter(o => row.selection.modifier_option_ids.includes(o.id)).map(o => ({ ...o, group_name: g.name }))), special_instructions: row.selection.special_instructions }} />{(!row.product.available || selectionError(row.product, row.selection)) && <p className="notice" data-state="danger">{!row.product.available ? "Produto indisponível" : selectionError(row.product, row.selection)}</p>}</div><div className="attendanceQuantity"><button className="buttonSecondary" aria-label={`Diminuir quantidade de ${row.product.name}`} disabled={draftLocked} onClick={() => changeQuantity(index, -1)}>−</button><output aria-label={`Quantidade selecionada de ${row.product.name}`} aria-live="polite">{row.quantity}</output><button className="buttonSecondary" aria-label={`Aumentar quantidade de ${row.product.name}`} disabled={draftLocked || increaseBlocked || !row.product.available || !!selectionError(row.product, row.selection) || row.quantity >= 99} onClick={() => changeQuantity(index, 1)}>+</button></div><div className="attendanceDraftControls"><button className="buttonQuiet" disabled={draftLocked} onClick={() => { setEditing(index); setConfiguring(row.product); }}>Editar</button><button className="buttonQuiet" disabled={draftLocked} onClick={() => setCart(c => c.filter((_, i) => i !== index))}>Remover</button></div></div>)}</section>}
      {!configuring && !orderIntent.pending && <section className="guestCart"><span>{rows.length ? `${rows.reduce((sum, row) => sum + row.quantity, 0)} item(ns)` : "Seu carrinho está vazio"}</span><button className="buttonPrimary" disabled={draftLocked || increaseBlocked || !rows.length || (cartError && !orderIntent.pending) || (context.tab.consumption_blocked && !orderIntent.pending)} onClick={() => void submitOrder()}>{sending ? "Enviando…" : `Enviar · ${money(total)}`}</button></section>}
      <section className="panel"><OperationalHeading as="h2" icon="wallet">Conta não fiscal</OperationalHeading><button className="buttonSecondary" disabled={repeatLoading || stale} onClick={() => { setReceiptError(""); void guestApi<{ text: string }>("receipt/", guestToken).then(result => { if (result.ok) setReceipt((result.body as { text: string }).text); else { setReceipt(""); setReceiptError("Conta indisponível. Confira sua sessão e conexão."); } }).catch(() => { setReceipt(""); setReceiptError("Não foi possível consultar a conta."); }); }}>Ver minha conta</button>{receiptError && <p role="alert">{receiptError}</p>}{receipt && <><pre className="receiptText">{receipt}</pre><button className="buttonSecondary" onClick={() => setReceipt("")}>Fechar conta</button></>}</section>
      {repeatLoading && !repeatReview && <p role="status">Conferindo rodada… Seu carrinho está preservado.</p>}<section className="panel" ref={ordersRegion} tabIndex={-1} aria-label="Pedidos"><OperationalHeading as="h2" icon="cart">Meus pedidos</OperationalHeading><p className="muted">Estado registrado pela operação. Atualizações ao vivo da sua comanda.</p>{!context.tab.orders?.length && <p>Nenhum pedido confirmado.</p>}{context.tab.orders?.map((order, index) => <section key={order.id} aria-label={`Rodada ${index + 1}`}><div className="actions"><h3>Rodada {index + 1}</h3><button className="buttonSecondary" aria-label={`Repetir rodada ${index + 1}`} disabled={!repeatAllowed || !!repeatReview} onClick={() => void startRepeat(order.id)}>Repetir rodada</button></div>{order.items.map(item => <div className="dataRow" key={item.id}><span><strong>{item.quantity}× {item.product_name}</strong><CustomizationText snapshot={item.customization_snapshot} /><small className="muted"> · {money(item.line_total_cents)}{item.ready_at ? ` · pronto às ${new Date(item.ready_at).toLocaleTimeString("pt-BR")}` : ""}</small></span><span className="statusBadge" data-state={item.state === "CANCELLED" ? "danger" : ["READY", "DELIVERED"].includes(item.state) ? "success" : "info"}>{guestItemStatus(item.state)}</span></div>)}</section>)}</section>
    </>}{repeatReview && <RepeatOrderDialog review={repeatReview.review} enabled={repeatAllowed && repeatUnchanged} busy={repeatLoading} message={repeatLoading ? "Conferindo visita e cardápio…" : notice} onAdd={() => void addRepeatedDraft()} onClose={() => setRepeatReview(null)} />}
  </main>;
}
