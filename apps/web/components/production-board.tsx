"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRealtime } from "@/lib/client/use-realtime";
import { projectionCache } from "@/lib/client/projection-cache";
import { ConnectivityNotice } from "./connectivity-notice";
import { apiCall, asApiError } from "@/lib/client/staff-auth";
import { QuickCatalog } from "./quick-catalog";
import { ProductIcon, type IconData } from "./product-icon";


type Item = { id: string; state: string; quantity: number; product_name: string; tab_label: string; created_at: string; ready_at?: string | null };
type Product = { id: string; name: string; fulfillment_station: "BAR" | "KITCHEN"; availability: "AVAILABLE" | "UNAVAILABLE"; icon?: IconData };
const next: Record<string, { state: string; label: string }> = {
  NEW: { state: "ACCEPTED", label: "Aceitar" },
  ACCEPTED: { state: "PREPARING", label: "Preparar" },
  PREPARING: { state: "READY", label: "Pronto" },
};
const labels: Record<string, string> = { NEW: "Novo", ACCEPTED: "Aceito", PREPARING: "Preparando", READY: "Pronto" };
const tone = (state: string) => state === "READY" ? "success" : state === "PREPARING" ? "warning" : "info";
const apiMessage = (body: unknown) => { const error = asApiError(body); return `${error.code} · ${error.message}`; };

export function ProductionBoard({ station, title }: { station: "BAR" | "KITCHEN"; title: string }) {
  const [now, setNow] = useState(() => Date.now());
  const [items, setItems] = useState<Item[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
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

  const waiting = items.filter(item => Object.hasOwn(next, item.state));
  const ready = items.filter(item => item.state === "READY");
  const disabled = connectivity.state === "OFFLINE" || !!message || changingProductId !== null || changingItemId !== null;

  const totals = new Map<string, number>();
  for (const item of waiting) totals.set(item.product_name, (totals.get(item.product_name) ?? 0) + item.quantity);
  function age(timestamp?: string | null) {
    if (!timestamp || !Number.isFinite(Date.parse(timestamp))) return "Tempo não informado";
    const seconds = Math.max(0, Math.floor((now - Date.parse(timestamp)) / 1000));
    return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
  }

  return <main className="appShell productionShell">
    <header className="productHeader">
      <div className="eyebrow">RODADA / {title.toUpperCase()}</div>
      <h1>{title}</h1>
      <p className="muted">Fila da estação · atualizações ao vivo</p>
    </header>
    <ConnectivityNotice {...connectivity} syncedAt={connectivity.syncedAt ?? cachedAt} />
    {message && <div className="notice" data-state="danger" role="alert">
      <p>{message}</p>
      {hasSnapshot && <p>Último estado confirmado. Ações pausadas até atualizar.</p>}
      <button className="buttonSecondary" onClick={() => void load(true).catch(() => {})}>Tentar atualizar</button>
    </div>}
    <div className="productionWorkspace">
    <section className="panel productionSummary" aria-labelledby="summary-title" aria-busy={loading}>
      <div className="eyebrow">Total para preparar</div>
      <h2 id="summary-title">Por produto</h2>
      {loading ? <div className="loadingState" role="status">Carregando resumo…</div> : Array.from(totals, ([name, quantity]) => <div className="dataRow" key={name}>
        <strong>{name}</strong><span className="productionQuantity" aria-label={`${quantity} unidades`}>×{quantity}</span>
      </div>)}
      {!loading && hasSnapshot && !totals.size && <div className="emptyState">Tudo em dia.</div>}
    </section>
    <section className="panel panelWarning" aria-labelledby="queue-title" aria-busy={loading}>
      <div className="eyebrow">Fila de produção</div>
      <h2 id="queue-title">Em produção</h2>
      {loading ? <div className="loadingState" role="status">Carregando fila…</div> : waiting.map(item => <article className="dataRow productionRow" key={item.id}>
        <div><strong>{item.quantity}× {item.product_name}</strong><br /><small className="muted">{item.tab_label || "Sem identificação"}</small><br /><span className="productionAge">Desde o pedido · {age(item.created_at)}</span></div>
        <div className="actions">
          <span className="statusBadge" data-state={tone(item.state)}>{labels[item.state] ?? item.state}</span>
          {next[item.state] && <button className="buttonPrimary buttonWork" disabled={disabled}
            aria-label={`${next[item.state].label}: ${item.quantity} ${item.product_name}, ${item.tab_label || "sem identificação"}`}
            onClick={() => void change(`/api/pos/order-items/${item.id}/transition/`, next[item.state].state, "item", item.id)}>
            {changingItemId === item.id ? "Salvando…" : next[item.state].label}
          </button>}
        </div>
      </article>)}
      {!loading && hasSnapshot && !waiting.length && <div className="emptyState">Nenhum item aguardando preparo.</div>}
    </section>
    <section className="panel panelSuccess" aria-labelledby="ready-title" aria-busy={loading}>
      <div className="eyebrow">Passe</div>
      <h2 id="ready-title">Pronto para retirada</h2>
      {loading ? <div className="loadingState" role="status">Carregando passe…</div> : ready.map(item => <div className="dataRow productionRow" key={item.id}>
        <div><strong>{item.quantity}× {item.product_name}</strong><br /><small className="muted">{item.tab_label || "Sem identificação"}</small><br /><span className="productionAge">No passe · {age(item.ready_at)}</span></div>
        <span className="statusBadge" data-state="success">Pronto</span>
      </div>)}
      {!loading && hasSnapshot && !ready.length && <div className="emptyState">Nada no passe.</div>}
    </section>
    </div>
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
    <QuickCatalog station={station} onChanged={() => load(true).catch(() => {})} />
  </main>;
}
