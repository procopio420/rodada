"use client";

import { OperationalHeading } from "@/components/operational-heading";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRealtime } from "@/lib/client/use-realtime";
import { projectionCache } from "@/lib/client/projection-cache";
import { ConnectivityNotice } from "./connectivity-notice";
import { apiCall, asApiError } from "@/lib/client/staff-auth";
import { ReceiptPrinting } from "./receipt-printing";
import { QuickCatalog } from "./quick-catalog";
import { ProductIcon, type IconData } from "./product-icon";


import { CustomizationText, type Snapshot, type OrderingProduct } from "./product-customization";
import { CustomizationAvailability } from "./customization-availability";
import { useProductionItemIntents } from "@/lib/client/production-item-intents";
import { useAvailabilityIntents } from "@/lib/client/availability-intents";
import { groupProductionItems, productionConfiguration } from "@/lib/client/production-groups";
import { useProductionBatchIntent } from "@/lib/client/production-batch-intent";
import { ProductionBatchReview } from "./production-batch-review";
type Item = { snapshot_fingerprint?: string; customization_snapshot?: Snapshot; id: string; product_id?: string; order_id?: string; tab_id?: string; ready_at?: string | null; state: string; quantity: number; product_name: string; tab_label: string; created_at: string };
type Product = OrderingProduct & { id: string; name: string; fulfillment_station: "BAR" | "KITCHEN"; availability: "AVAILABLE" | "UNAVAILABLE"; availability_version?: number; icon?: IconData };
const next: Record<string, { state: string; label: string }> = {
  NEW: { state: "PREPARING", label: "Iniciar preparo" },
  ACCEPTED: { state: "PREPARING", label: "Iniciar preparo" },
  PREPARING: { state: "READY", label: "Pronto" },
};
const labels: Record<string, string> = { NEW: "Aguardando preparo", ACCEPTED: "Aguardando preparo", PREPARING: "Em preparo", READY: "Pronto" };
const apiMessage = (body: unknown) => { const error = asApiError(body); return `${error.code} · ${error.message}`; };

export function ProductionBoard({ station, title }: { station: "BAR" | "KITCHEN"; title: string }) {
  const [review, setReview] = useState<{ target: "PREPARING" | "READY"; items: Item[] } | null>(null);
  const reviewRef = useRef(false);
  const [reviewOrigin, setReviewOrigin] = useState<HTMLElement | null>(null);
  const batchReadback = useRef(false);
  const deferredRead = useRef(false);
  const readbackTail = useRef<Promise<void>>(Promise.resolve());
  const [items, setItems] = useState<Item[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [now, setNow] = useState(0);
  const [message, setMessage] = useState("");
  const [changingProductId, setChangingProductId] = useState<string | null>(null);
  const [changingItemId, setChangingItemId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [hasSnapshot, setHasSnapshot] = useState(false);
  const cache = useMemo(() => projectionCache<{ items: Item[]; products: Product[] }>(station), [station]);
  const [cachedAt, setCachedAt] = useState<number>();
  const reading = useRef(false);
  const snapshotVersion = useRef(0);
  const mutating = useRef(false);
  const queueRegion = useRef<HTMLElement>(null);
  const passRegion = useRef<HTMLElement>(null);
  const availabilityRegion = useRef<HTMLElement>(null);
  function visitRegion(region: HTMLElement | null) {
    region?.scrollIntoView({ block: "start" });
    region?.focus({ preventScroll: true });
  }

  const load = useCallback(async (force = false, commandReadback = false) => {
    if (batchReadback.current && !commandReadback) { deferredRead.current = true; return; }
    if (reading.current && !force) return;
    const version = ++snapshotVersion.current;
    reading.current = true;
    try {
      const [queue, catalog] = await Promise.all([
        apiCall<{ results: Item[] }>(`/api/pos/production/${station}/`),
        apiCall<{ results: Product[] }>("/api/pos/catalog/products/"),
      ]);
      if (version !== snapshotVersion.current) throw new Error("Station read superseded");
      if (!queue.response.ok || !catalog.response.ok) {
        setMessage(apiMessage(!queue.response.ok ? queue.body : catalog.body));
        throw new Error("Station snapshot unavailable");
      }
      const nextItems = (queue.body as { results: Item[] }).results;
      const nextProducts = (catalog.body as { results: Product[] }).results.filter(product => product.fulfillment_station === station);
      setItems(previous => JSON.stringify(previous) === JSON.stringify(nextItems) ? previous : nextItems);
      setProducts(previous => JSON.stringify(previous) === JSON.stringify(nextProducts) ? previous : nextProducts);
      cache.save({ items: nextItems.map(item => ({ ...item, tab_label: "" })), products: nextProducts });
      setHasSnapshot(true);
      setMessage("");
    } catch (error) {
      if (version === snapshotVersion.current) setMessage("Não foi possível atualizar a estação. Confira a conexão e tente novamente.");
      throw error;
    } finally {
      if (version === snapshotVersion.current) { reading.current = false; setLoading(false); }
    }
  }, [station, cache]);

  function readback() {
    const next = readbackTail.current.catch(() => {}).then(async () => {
      batchReadback.current = true;
      try { await load(true, true); } finally {
        batchReadback.current = false;
        if (deferredRead.current) { deferredRead.current = false; void load(true).catch(() => {}); }
      }
    });
    readbackTail.current = next; return next;
  }
  const batchIntent = useProductionBatchIntent(station, readback);
  const itemIntents = useProductionItemIntents(station, readback);
  const availabilityIntents = useAvailabilityIntents(station, readback);
  function closeReview() { reviewRef.current = false; setReview(null); }

  useEffect(() => {
    void cache.restore().then(cached => {
      if (cached) { setItems(cached.data.items); setProducts(cached.data.products); setCachedAt(cached.fetchedAt); setHasSnapshot(true); setLoading(false); }
    });
  }, [cache]);
  const connectivity = useRealtime(() => load(true), {
    relevant: event => ["order", "orderitem", "order_item", "product", "producticon"].includes(event.aggregate_type.toLowerCase()),
    onRevoked: (error) => { cache.clear(); setItems([]); setProducts([]); setHasSnapshot(false); setLoading(false); setMessage(apiMessage(error ?? { code: "AUTH_REVOKED", message: "Sessão encerrada." })); },
  });
  useEffect(() => {
    setNow(Date.now());
    // Local age display only; canonical reads are driven by realtime/fallback.
    const timer = window.setInterval(() => setNow(Date.now()), 15000);
    return () => window.clearInterval(timer);
  }, []);

  const change = useCallback(async (path: string, state: string, kind: "product" | "item", id: string) => {
    if (mutating.current || reviewRef.current || batchIntent.locked() || itemIntents.anyPending() || availabilityIntents.anyPending() || message) return;
    mutating.current = true;
    if (kind === "product") setChangingProductId(id); else setChangingItemId(id);
    try {
      const result = await apiCall(path, { method: "POST", body: JSON.stringify({ state }) });
      if (!result.response.ok) { setMessage(apiMessage(result.body)); return; }
      await load(true);
    } catch {
      setMessage("Não foi possível confirmar a alteração. Atualize a estação para conferir o estado antes de tentar novamente.");
    } finally {
      mutating.current = false;
      setChangingProductId(null);
      setChangingItemId(null);
    }
  }, [batchIntent, itemIntents, availabilityIntents, message, load]);

  const openReview = useCallback((origin: HTMLElement, target: "PREPARING" | "READY", candidates: Item[]) => {
    if (mutating.current || batchIntent.locked() || itemIntents.anyPending() || availabilityIntents.anyPending() || reviewRef.current) return;
    setReviewOrigin(origin); reviewRef.current = true;
    setReview({ target, items: candidates.map(item => ({ ...item })) });
  }, [batchIntent, itemIntents, availabilityIntents]);

  const transitionItem = useCallback((item: Item) => {
    if (mutating.current || !availabilityIntents.valid() || availabilityIntents.message || reviewRef.current || batchIntent.locksItem(item.id) || message) return;
    if (verifiedItem(item, station)) void itemIntents.submit(item.id, { station, target_state: next[item.state].state as "PREPARING" | "READY", lines: [{ item_id: item.id, expected_state: item.state, quantity: item.quantity, snapshot_fingerprint: item.snapshot_fingerprint! }] });
    else void change(`/api/pos/order-items/${item.id}/transition/`, next[item.state].state, "item", item.id);
  }, [availabilityIntents, batchIntent, itemIntents, message, station, change]);

  const waiting = items.filter(item => ["NEW", "ACCEPTED", "PREPARING"].includes(item.state));
  const pending = waiting.filter(item => item.state !== "PREPARING");
  const inProgress = waiting.filter(item => item.state === "PREPARING");
  // Group presentation by canonical Order identity; legacy items remain independent.
  const orderGroups = new Map<string, Item[]>();
  for (const item of waiting) {
    const key = item.order_id ? `order:${item.order_id}` : `item:${item.id}`;
    const group = orderGroups.get(key) ?? [];
    group.push(item); orderGroups.set(key, group);
  }
  const ready = items.filter(item => item.state === "READY");
  const inTransit = items.filter(item => item.state === "PICKED_UP");
  const independentDisabled = !availabilityIntents.ready || !!availabilityIntents.message || !itemIntents.ready || !!itemIntents.message || !batchIntent.ready || batchIntent.locksItem("") || !!review || connectivity.state === "OFFLINE" || !!message || changingProductId !== null || changingItemId !== null;
  const disabled = independentDisabled || !!batchIntent.pending || batchIntent.busy || availabilityIntents.pending.length > 0 || availabilityIntents.busy.length > 0;
  const individualDisabled = independentDisabled;
  const versionedProduct = (product: Product) => Number.isSafeInteger(product.availability_version) && product.availability_version! >= 1 && product.availability_version! <= 2147483647;

  const verified = (item: Item) => verifiedItem(item, station);
  const batches = groupProductionItems(waiting, station).map(group => ({ ...group, product: products.find(product => product.id === group.items[0].product_id) }));
  const age = (timestamp?: string | null) => {
    if (!timestamp || !Number.isFinite(Date.parse(timestamp))) return "Tempo não informado";
    const seconds = Math.max(0, Math.floor((now - Date.parse(timestamp)) / 1000));
    return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
  };
  return <main className="appShell productionShell">
    <header className="stationHeader">
      <div className="stationIdentity"><svg aria-hidden="true" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">{station === "KITCHEN" ? <path d="M12 22c4 0 7-2.7 7-6.5 0-4-3-6-4-9.5-2 1.5-3 3.5-3 5.5-1.5-1-2.5-2.5-2.5-4C6.5 9.5 5 12.5 5 15.5 5 19.3 8 22 12 22z" /> : <><path d="M5 4h12v16H5zM17 7h2a3 3 0 0 1 0 6h-2M8 1v4M13 1v4" /></>}</svg><h1>{title}</h1><span>Fila da estação</span></div>
      <div className="stationSummary">{hasSnapshot && <><span><b>{new Set(pending.map(item => item.order_id ?? item.id)).size}</b> pedidos aguardando</span><span><b>{inProgress.length}</b> itens em preparo</span></>}<time>{now ? new Date(now).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) : "—"}</time></div>
    </header>
    <nav className="stationRegionNav" aria-label="Regiões da produção">
      <button className="buttonSecondary" onClick={() => visitRegion(queueRegion.current)}>Fila <span>{hasSnapshot ? waiting.length : "—"}</span></button>
      <button className="buttonSecondary" onClick={() => visitRegion(passRegion.current)}>Prontos <span>{hasSnapshot ? ready.length : "—"}</span></button>
      <button className="buttonSecondary" onClick={() => visitRegion(availabilityRegion.current)}>Disponibilidade <span>{hasSnapshot ? products.length : "—"}</span></button>
    </nav>
    <ConnectivityNotice {...connectivity} syncedAt={connectivity.syncedAt ?? cachedAt} />
    {message && <div className="notice" data-state="danger" role="alert"><p>{message}</p>{hasSnapshot && <p>Último estado confirmado. Ações pausadas até atualizar.</p>}<button className="buttonSecondary" onClick={() => void load(true).catch(() => {})}>Tentar atualizar</button></div>}
    {batchIntent.message && <div className="notice" data-state="warning" role="alert"><p>{batchIntent.message}</p>
      {batchIntent.pending && <><p>{batchIntent.pending.payload.lines.length} linhas · {batchIntent.pending.payload.station === "KITCHEN" ? "Cozinha" : "Bar"}</p>
        {batchIntent.pending.payload.station === station ? <button className="buttonSecondary" disabled={batchIntent.busy || connectivity.state === "OFFLINE"} onClick={() => void batchIntent.submit()}>{batchIntent.busy ? "Verificando…" : "Verificar mesmo lote"}</button>
          : <a className="buttonSecondary" href={batchIntent.pending.payload.station === "KITCHEN" ? "/kitchen" : "/bar"}>Retomar na estação original</a>}</>}
    </div>}
    {itemIntents.message && <p className="notice" data-state="warning" role="alert">{itemIntents.message}</p>}
    {availabilityIntents.message && <p className="notice" data-state="warning" role="alert">{availabilityIntents.message}</p>}
    {availabilityIntents.pending.map(intent => <div className="notice" data-state="warning" role="status" key={intent.product_id}>
      <p>Disponibilidade · {products.find(product => product.id === intent.product_id)?.name ?? intent.product_id.slice(0, 8)} · {availabilityIntents.errors[intent.product_id] || "Aguardando confirmação."}</p>
      {intent.station === station ? <button className="buttonSecondary" disabled={!availabilityIntents.ready || availabilityIntents.busy.includes(intent.product_id) || connectivity.state === "OFFLINE" || !!review || changingItemId !== null || changingProductId !== null}
        aria-label={`Verificar mesma disponibilidade: ${intent.product_id.slice(0, 8)}`} onClick={() => void availabilityIntents.submit(intent.product_id)}>{availabilityIntents.busy.includes(intent.product_id) ? "Verificando…" : "Verificar mesma disponibilidade"}</button>
        : <a className="buttonSecondary" href={intent.station === "KITCHEN" ? "/kitchen" : "/bar"}>Retomar disponibilidade na estação original</a>}
    </div>)}
    {availabilityIntents.result && <p className="notice" role="status">{availabilityIntents.result.status === "APPLIED" ? "Disponibilidade confirmada." : "Disponibilidade não aplicada. Confira o estado atual antes de tentar novamente."} · {availabilityIntents.result.product_id.slice(0, 8)}</p>}
    {itemIntents.pending.map(intent => { const id = intent.payload.lines[0].item_id; return <div className="notice" data-state="warning" key={id} role="status">
      <p>Item {id.slice(0, 8)} · {intent.payload.lines[0].quantity} unidades · {itemIntents.errors[id] || "Aguardando confirmação."}</p>
      {intent.payload.station === station ? <button className="buttonSecondary" disabled={itemIntents.busy.includes(id) || connectivity.state === "OFFLINE" || batchIntent.locksItem(id) || !!review}
        aria-label={`Verificar mesmo item: ${id.slice(0, 8)}`} onClick={() => void itemIntents.submit(id)}>{itemIntents.busy.includes(id) ? "Verificando…" : "Verificar mesmo item"}</button>
        : <a className="buttonSecondary" href={intent.payload.station === "KITCHEN" ? "/kitchen" : "/bar"}>Retomar item na estação original</a>}
    </div>; })}
    {itemIntents.result && <p className="notice" role="status">{itemIntents.result.status === "APPLIED" ? "Item confirmado." : "Item não aplicado. Confira o estado atual antes de tentar novamente."} · {itemIntents.result.lines[0].item_id.slice(0, 8)}</p>}
    {batchIntent.busy && <p role="status">Confirmando lote…</p>}
    {batchIntent.result && <div className="notice" data-state={batchIntent.result.status === "APPLIED" ? "success" : "warning"} role="status">
      <p>{batchIntent.result.status === "APPLIED" ? "Lote confirmado." : "Lote não aplicado. Confira a fila e faça uma nova seleção."}</p>
      <ul>{batchIntent.result.lines.map(line => <li key={line.item_id}>{line.item_id.slice(0, 8)} · {line.status === "APPLIED" ? "Aplicado" : "Não aplicado"}</li>)}</ul>
    </div>}
    <div className="productionWorkspace">
      <section className="stationBatches" aria-labelledby="batch-title" aria-busy={loading}>
        <div className="stationLabel"><h2 id="batch-title"><svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M13 2L4 14h7l-1 8 9-12h-7z" /></svg><span>Fila da estação · por {station === "KITCHEN" ? "prato" : "produto"}</span></h2><span>{station === "KITCHEN" ? "porções" : "lote"}</span></div>
        {loading ? <div className="loadingState" role="status">Carregando produção…</div> : batches.map(batch => <article className="stationDish" key={batch.key}>
          <div className="stationDishHeading"><div><ProductIcon name={batch.name} icon={batch.product?.icon} /><strong>{batch.name}</strong></div><span className="stationQuantity">{batch.quantity}</span></div>
          <span className="stationDishContext">{batch.items.filter(item => item.state !== "PREPARING").length} aguardando · {batch.items.filter(item => item.state === "PREPARING").length} em preparo</span>
          {!!(batch.items[0].customization_snapshot?.variant || batch.items[0].customization_snapshot?.modifiers?.length || batch.items[0].customization_snapshot?.special_instructions) && <CustomizationText snapshot={batch.items[0].customization_snapshot} />}
          {!batch.knownConfiguration && <span className="muted">Configuração não registrada</span>}
          {batch.knownConfiguration && ["PREPARING", "READY"].map(target => {
            const candidates = batch.items.filter(item => /^[a-f0-9]{64}$/.test(item.snapshot_fingerprint ?? "") && (target === "PREPARING" ? ["NEW", "ACCEPTED"].includes(item.state) : item.state === "PREPARING"));
            return candidates.length > 1 && <BatchSelectionButton key={target} name={batch.name} target={target as "PREPARING" | "READY"}
              disabled={disabled || itemIntents.pending.length > 0 || itemIntents.busy.length > 0} candidates={candidates} onSelect={openReview} />;
          })}
          <div className="stationChips">{batch.items.map(item => <span key={item.id}>{item.tab_label || "Sem identificação"}{item.quantity > 1 ? ` ×${item.quantity}` : ""}</span>)}</div>
        </article>)}
        {!loading && hasSnapshot && !batches.length && <div className="emptyState">Nenhum prato aguardando preparo.</div>}
      </section>
      <section className="stationTickets stationRegion" ref={queueRegion} tabIndex={-1} aria-labelledby="queue-title" aria-busy={loading}>
        <div className="stationLabel"><OperationalHeading as="h2" icon="operation" id="queue-title">Fila de pedidos</OperationalHeading>{hasSnapshot && <span>{waiting.length} {waiting.length === 1 ? "item" : "itens"}</span>}</div>
        <p className="stationCaption">O preparo só começa ao tocar em Iniciar preparo · mais antigo primeiro</p>
        {loading ? <div className="loadingState" role="status">Carregando fila…</div> : [...orderGroups].map(([key, group]) => <div className="stationOrder" key={key} role="group" aria-label={`Pedido: ${group[0].tab_label || "Sem identificação"}`}>
          <strong className="stationTab">{group[0].tab_label || "Sem identificação"}</strong>
          <div className="stationOrderItems">{group.map(item => <article className="stationTicket" key={item.id}>
          <div className="stationTicketContent"><strong>{item.quantity} {item.product_name}</strong><CustomizationText snapshot={item.customization_snapshot} /><div className="stationTicketMeta"><span>{labels[item.state] ?? item.state}</span><time aria-label="Tempo desde o pedido">{age(item.created_at)}</time></div></div>
          {next[item.state] && <ItemTransitionButton item={item} label={next[item.state].label}
            disabled={verified(item) ? individualDisabled || batchIntent.locksItem(item.id) || itemIntents.locked(item.id) : disabled || itemIntents.pending.length > 0 || itemIntents.busy.length > 0}
            saving={changingItemId === item.id || itemIntents.busy.includes(item.id)} onTransition={transitionItem} />}
          </article>)}</div>
        </div>)}
        {!loading && hasSnapshot && !waiting.length && <div className="emptyState">Nenhum item aguardando preparo.</div>}
      </section>
      <section className="stationPass stationRegion" ref={passRegion} tabIndex={-1} aria-labelledby="ready-title" aria-busy={loading}>
        <div className="stationLabel"><OperationalHeading as="h2" icon="check" id="ready-title">Pronto para retirada</OperationalHeading>{hasSnapshot && <span>{ready.length} {ready.length === 1 ? "item" : "itens"}</span>}</div>
        <p className="stationCaption">No passe · esperando retirada</p>
        {loading ? <div className="loadingState" role="status">Carregando passe…</div> : ready.map(item => <article className="stationPassRow" key={item.id}><strong className="stationTab">{item.tab_label || "Sem identificação"}</strong><div><strong>{item.quantity} {item.product_name}</strong><CustomizationText snapshot={item.customization_snapshot} /><div className="stationPassMeta">No passe · <time>{age(item.ready_at)}</time></div></div></article>)}
        {!loading && hasSnapshot && !ready.length && <div className="emptyState">Nada no passe.</div>}
        {!!inTransit.length && <div className="stationTransit"><h3>Em entrega</h3>{inTransit.map(item => <article className="stationPassRow" key={item.id}><strong className="stationTab">{item.tab_label || "Sem identificação"}</strong><div><strong>{item.quantity} {item.product_name}</strong><CustomizationText snapshot={item.customization_snapshot} /><div className="stationPassMeta">Retirada registrada</div></div></article>)}</div>}
        <p className="stationFootnote">Estado confirmado pela operação. Atualizações ao vivo.</p>
      </section>
    </div>
    <div className="stationTools">
    <section className="panel"><OperationalHeading as="h2" icon="operation">Tickets de produção</OperationalHeading>{[...new Map(items.filter(i => i.order_id && i.tab_id).map(i => [i.order_id, i])).values()].map(item => <div className="dataRow" key={item.order_id}><strong>{item.tab_label || "Comanda"} · {item.order_id?.slice(0, 8)}</strong><ReceiptPrinting tabId={item.tab_id!} orderId={item.order_id} station={station} /></div>)}</section>
    <section className="panel stationRegion" ref={availabilityRegion} tabIndex={-1} aria-labelledby="availability-title" aria-busy={loading}>
      <div className="eyebrow">Cardápio da estação</div>
      <OperationalHeading as="h2" icon="operation" id="availability-title">Disponibilidade agora</OperationalHeading>
      {loading ? <div className="loadingState" role="status">Carregando disponibilidade…</div> : products.map(product => {
        const available = product.availability === "AVAILABLE";
        return <article className="dataRow productionRow" key={product.id}>
          <div className="productIconRow"><ProductIcon name={product.name} icon={product.icon} /><div><strong>{product.name}</strong><br /><small className="muted">{available ? "Disponível para vender" : "Indisponível em todos os canais"}</small></div></div>
          <div className="actions">
            <span className="statusBadge" data-state={available ? "success" : "danger"}>{available ? "Disponível" : "Indisponível"}</span>
            <button className={available ? "buttonSecondary" : "buttonPrimary"} disabled={versionedProduct(product) ? independentDisabled || availabilityIntents.locked(product.id) : disabled || itemIntents.pending.length > 0 || itemIntents.busy.length > 0}
              aria-label={`${available ? "Indisponibilizar" : "Reativar"} ${product.name}`}
              onClick={() => {
                if (mutating.current || reviewRef.current || independentDisabled) return;
                if (versionedProduct(product)) void availabilityIntents.submit(product.id, { product_id: product.id, station, state: available ? "UNAVAILABLE" : "AVAILABLE", expected_version: product.availability_version! });
                else void change(`/api/pos/catalog/products/${product.id}/availability/`, available ? "UNAVAILABLE" : "AVAILABLE", "product", product.id);
              }}>
              {changingProductId === product.id || availabilityIntents.busy.includes(product.id) ? "Salvando…" : available ? "Indisponibilizar" : "Reativar"}
            </button>
          </div>
        </article>;
      })}
      {!loading && hasSnapshot && !products.length && <div className="emptyState">Nenhum produto roteado para esta estação.</div>}
    </section>
    <div inert={disabled || itemIntents.pending.length > 0 || itemIntents.busy.length > 0}>
      <CustomizationAvailability products={products} onChanged={() => load(true).catch(() => {})} />
      <QuickCatalog station={station} onChanged={() => load(true).catch(() => {})} />
    </div>
    </div>
    {review && <ProductionBatchReview station={station} target={review.target} captured={review.items} current={items}
      returnFocus={reviewOrigin} unavailable={connectivity.state === "OFFLINE" || !!message || batchIntent.locked() || !!changingItemId || !!changingProductId} onClose={closeReview}
      onConfirm={draft => { if (batchIntent.locked() || mutating.current || message) return; void batchIntent.submit(draft); closeReview(); }} />}
  </main>;
}

function verifiedItem(item: Item, station: "BAR" | "KITCHEN") {
  return /^[a-f0-9]{64}$/.test(item.snapshot_fingerprint ?? "") && productionConfiguration(item, station) !== null;
}
function BatchSelectionButton({ name, target, disabled, candidates, onSelect }: {
  name: string; target: "PREPARING" | "READY"; disabled: boolean; candidates: Item[];
  onSelect: (origin: HTMLElement, target: "PREPARING" | "READY", candidates: Item[]) => void;
}) {
  return <button className="buttonSecondary" disabled={disabled} aria-label={`${target === "PREPARING" ? "Selecionar preparo" : "Selecionar prontos"}: ${name}`}
    onClick={event => onSelect(event.currentTarget, target, candidates)}>{target === "PREPARING" ? "Selecionar preparo" : "Selecionar prontos"}</button>;
}
function ItemTransitionButton({ item, label, disabled, saving, onTransition }: {
  item: Item; label: string; disabled: boolean; saving: boolean; onTransition: (item: Item) => void;
}) {
  return <button className="buttonPrimary" disabled={disabled} aria-label={`${label}: ${item.quantity} ${item.product_name}, ${item.tab_label || "sem identificação"}`}
    onClick={() => onTransition(item)}>{saving ? "Salvando…" : label}</button>;
}
