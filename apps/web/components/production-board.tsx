"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRealtime } from "@/lib/client/use-realtime";
import { projectionCache } from "@/lib/client/projection-cache";
import { ConnectivityNotice } from "./connectivity-notice";
import { apiCall, asApiError } from "@/lib/client/staff-auth";
import { QuickCatalog } from "./quick-catalog";
import { ProductIcon, type IconData } from "./product-icon";


import { CustomizationText, type Snapshot, type OrderingProduct } from "./product-customization";
import { CustomizationAvailability } from "./customization-availability";
type Item = { customization_snapshot?: Snapshot; id: string; product_id?: string; order_id?: string; ready_at?: string | null; state: string; quantity: number; product_name: string; tab_label: string; created_at: string };
type Product = OrderingProduct & { id: string; name: string; fulfillment_station: "BAR" | "KITCHEN"; availability: "AVAILABLE" | "UNAVAILABLE"; icon?: IconData };
const next: Record<string, { state: string; label: string }> = {
  NEW: { state: "ACCEPTED", label: "Aceitar" },
  ACCEPTED: { state: "PREPARING", label: "Preparar" },
  PREPARING: { state: "READY", label: "Pronto" },
};
const labels: Record<string, string> = { NEW: "Novo", ACCEPTED: "Aceito", PREPARING: "Preparando", READY: "Pronto" };
const tone = (state: string) => state === "READY" ? "success" : state === "PREPARING" ? "warning" : "info";
const apiMessage = (body: unknown) => { const error = asApiError(body); return `${error.code} · ${error.message}`; };

export function ProductionBoard({ station, title }: { station: "BAR" | "KITCHEN"; title: string }) {
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

  const load = useCallback(async (force = false) => {
    if (reading.current && !force) return;
    const version = ++snapshotVersion.current;
    reading.current = true;
    try {
      const [queue, catalog] = await Promise.all([
        apiCall<{ results: Item[] }>(`/api/pos/production/${station}/`),
        apiCall<{ results: Product[] }>("/api/pos/catalog/products/"),
      ]);
      if (version !== snapshotVersion.current) return;
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

  async function change(path: string, state: string, kind: "product" | "item", id: string) {
    if (mutating.current || message) return;
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
  }

  const waiting = items.filter(item => ["NEW", "ACCEPTED", "PREPARING"].includes(item.state));
  // Group presentation by canonical Order identity; legacy items remain independent.
  const orderGroups = new Map<string, Item[]>();
  for (const item of waiting) {
    const key = item.order_id ? `order:${item.order_id}` : `item:${item.id}`;
    const group = orderGroups.get(key) ?? [];
    group.push(item); orderGroups.set(key, group);
  }
  const ready = items.filter(item => item.state === "READY");
  const inTransit = items.filter(item => item.state === "PICKED_UP");
  const disabled = connectivity.state === "OFFLINE" || !!message || changingProductId !== null || changingItemId !== null;

  const groups = new Map<string, { name: string; product?: Product; quantity: number; items: Item[] }>();
  for (const item of waiting) {
    // Identity comes from the projection; old snapshots stay separate rather than merging names.
    const key = item.product_id ?? item.id;
    const group = groups.get(key) ?? { name: item.product_name, product: products.find(product => product.id === item.product_id), quantity: 0, items: [] };
    group.quantity += item.quantity; group.items.push(item); groups.set(key, group);
  }
  const batches = [...groups.values()].sort((a, b) => b.quantity - a.quantity);
  const age = (timestamp?: string | null) => {
    if (!timestamp || !Number.isFinite(Date.parse(timestamp))) return "Tempo não informado";
    const seconds = Math.max(0, Math.floor((now - Date.parse(timestamp)) / 1000));
    return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
  };
  return <main className="appShell productionShell">
    <header className="stationHeader">
      <div className="stationIdentity"><svg aria-hidden="true" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">{station === "KITCHEN" ? <path d="M12 22c4 0 7-2.7 7-6.5 0-4-3-6-4-9.5-2 1.5-3 3.5-3 5.5-1.5-1-2.5-2.5-2.5-4C6.5 9.5 5 12.5 5 15.5 5 19.3 8 22 12 22z" /> : <><path d="M5 4h12v16H5zM17 7h2a3 3 0 0 1 0 6h-2M8 1v4M13 1v4" /></>}</svg><h1>{title}</h1><span>Fila da estação</span></div>
      <div className="stationSummary">{hasSnapshot && <><span><b>{new Set(waiting.map(item => item.order_id ?? item.id)).size}</b> pedidos em preparo</span><span><b>{ready.length}</b> no passe</span></>}<time>{now ? new Date(now).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) : "—"}</time></div>
    </header>
    <ConnectivityNotice {...connectivity} syncedAt={connectivity.syncedAt ?? cachedAt} />
    {message && <div className="notice" data-state="danger" role="alert"><p>{message}</p>{hasSnapshot && <p>Último estado confirmado. Ações pausadas até atualizar.</p>}<button className="buttonSecondary" onClick={() => void load(true).catch(() => {})}>Tentar atualizar</button></div>}
    <div className="productionWorkspace">
      <section className="stationBatches" aria-labelledby="batch-title" aria-busy={loading}>
        <div className="stationLabel"><h2 id="batch-title"><svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M13 2L4 14h7l-1 8 9-12h-7z" /></svg><span>Fazer agora · por {station === "KITCHEN" ? "prato" : "produto"}</span></h2><span>{station === "KITCHEN" ? "porções" : "lote"}</span></div>
        {loading ? <div className="loadingState" role="status">Carregando produção…</div> : batches.map(batch => <article className="stationDish" key={batch.items[0].product_id ?? batch.items[0].id}>
          <div className="stationDishHeading"><div><ProductIcon name={batch.name} icon={batch.product?.icon} /><strong>{batch.name}</strong></div><span className="stationQuantity">{batch.quantity}</span></div>
          <span className="stationDishContext">{batch.items.length} {batch.items.length === 1 ? "item em produção" : "itens em produção"}</span>
          <div className="stationChips">{batch.items.map(item => <span key={item.id}>{item.tab_label || "Sem identificação"}{item.quantity > 1 ? ` ×${item.quantity}` : ""}</span>)}</div>
        </article>)}
        {!loading && hasSnapshot && !batches.length && <div className="emptyState">Nenhum prato aguardando preparo.</div>}
      </section>
      <section className="stationTickets" aria-labelledby="queue-title" aria-busy={loading}>
        <div className="stationLabel"><h2 id="queue-title">Em produção</h2>{hasSnapshot && <span>{waiting.length} {waiting.length === 1 ? "item" : "itens"}</span>}</div>
        <p className="stationCaption">Por pedido · mais antigo primeiro</p>
        {loading ? <div className="loadingState" role="status">Carregando fila…</div> : [...orderGroups].map(([key, group]) => <div className="stationOrder" key={key} role="group" aria-label={`Pedido: ${group[0].tab_label || "Sem identificação"}`}>
          <strong className="stationTab">{group[0].tab_label || "Sem identificação"}</strong>
          <div className="stationOrderItems">{group.map(item => <article className="stationTicket" key={item.id}>
          <div className="stationTicketContent"><strong>{item.quantity} {item.product_name}</strong><CustomizationText snapshot={item.customization_snapshot} /><div className="stationTicketMeta"><span>{labels[item.state] ?? item.state}</span><time aria-label="Tempo desde o pedido">{age(item.created_at)}</time></div></div>
          {next[item.state] && <button className="buttonPrimary" disabled={disabled} aria-label={`${next[item.state].label}: ${item.quantity} ${item.product_name}, ${item.tab_label || "sem identificação"}`} onClick={() => void change(`/api/pos/order-items/${item.id}/transition/`, next[item.state].state, "item", item.id)}>{changingItemId === item.id ? "Salvando…" : next[item.state].label}</button>}
          </article>)}</div>
        </div>)}
        {!loading && hasSnapshot && !waiting.length && <div className="emptyState">Nenhum item aguardando preparo.</div>}
      </section>
      <section className="stationPass" aria-labelledby="ready-title" aria-busy={loading}>
        <div className="stationLabel"><h2 id="ready-title">Pronto para retirada</h2>{hasSnapshot && <span>{ready.length} {ready.length === 1 ? "item" : "itens"}</span>}</div>
        <p className="stationCaption">No passe · esperando retirada</p>
        {loading ? <div className="loadingState" role="status">Carregando passe…</div> : ready.map(item => <article className="stationPassRow" key={item.id}><strong className="stationTab">{item.tab_label || "Sem identificação"}</strong><div><strong>{item.quantity} {item.product_name}</strong><CustomizationText snapshot={item.customization_snapshot} /><div className="stationPassMeta">No passe · <time>{age(item.ready_at)}</time></div></div></article>)}
        {!loading && hasSnapshot && !ready.length && <div className="emptyState">Nada no passe.</div>}
        {!!inTransit.length && <div className="stationTransit"><h3>Em entrega</h3>{inTransit.map(item => <article className="stationPassRow" key={item.id}><strong className="stationTab">{item.tab_label || "Sem identificação"}</strong><div><strong>{item.quantity} {item.product_name}</strong><CustomizationText snapshot={item.customization_snapshot} /><div className="stationPassMeta">Retirada registrada</div></div></article>)}</div>}
        <p className="stationFootnote">Estado confirmado pela operação. Atualizações ao vivo.</p>
      </section>
    </div>
    <div className="stationTools">
    <section className="panel" aria-labelledby="availability-title" aria-busy={loading}>
      <div className="eyebrow">Cardápio da estação</div>
      <h2 id="availability-title">Disponibilidade agora</h2>
      {loading ? <div className="loadingState" role="status">Carregando disponibilidade…</div> : products.map(product => {
        const available = product.availability === "AVAILABLE";
        return <article className="dataRow productionRow" key={product.id}>
          <div className="productIconRow"><ProductIcon name={product.name} icon={product.icon} /><div><strong>{product.name}</strong><br /><small className="muted">{available ? "Disponível para vender" : "Indisponível em todos os canais"}</small></div></div>
          <div className="actions">
            <span className="statusBadge" data-state={available ? "success" : "danger"}>{available ? "Disponível" : "Indisponível"}</span>
            <button className={available ? "buttonSecondary" : "buttonPrimary"} disabled={disabled}
              aria-label={`${available ? "Indisponibilizar" : "Reativar"} ${product.name}`}
              onClick={() => void change(`/api/pos/catalog/products/${product.id}/availability/`, available ? "UNAVAILABLE" : "AVAILABLE", "product", product.id)}>
              {changingProductId === product.id ? "Salvando…" : available ? "Indisponibilizar" : "Reativar"}
            </button>
          </div>
        </article>;
      })}
      {!loading && hasSnapshot && !products.length && <div className="emptyState">Nenhum produto roteado para esta estação.</div>}
    </section>
    <CustomizationAvailability products={products} onChanged={() => load(true).catch(() => {})} />
    <QuickCatalog station={station} onChanged={() => load(true).catch(() => {})} />
    </div>
  </main>;
}
