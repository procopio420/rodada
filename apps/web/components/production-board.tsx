"use client";

import { useCallback, useEffect, useState } from "react";
import { apiCall, asApiError } from "@/lib/client/staff-auth";

type Item = { id: string; state: string; quantity: number; product_name: string; tab_label: string; created_at: string };
type Product = { id: string; name: string; fulfillment_station: "BAR" | "KITCHEN"; availability: "AVAILABLE" | "UNAVAILABLE" };

const next: Record<string, { state: string; label: string }> = {
  NEW: { state: "ACCEPTED", label: "Aceitar" },
  ACCEPTED: { state: "PREPARING", label: "Preparar" },
  PREPARING: { state: "READY", label: "Pronto" },
};

function itemState(state: string): "info" | "warning" | "success" {
  if (state === "READY") return "success";
  if (state === "PREPARING") return "warning";
  return "info";
}

function QuickCatalogUnavailable({ station }: { station: string }) {
  return <section className="panel" aria-labelledby="quick-catalog-title">
    <div className="eyebrow">Quick Catalog · {station}</div>
    <h2 id="quick-catalog-title">Adicionar item</h2>
    <div className="formGrid" aria-describedby="quick-catalog-limitation">
      <label className="field"><span className="fieldLabel">Nome</span><input disabled placeholder="Buscar no catálogo" /></label>
      <label className="field"><span className="fieldLabel">Preço</span><input disabled placeholder="R$ 0,00" /></label>
      <div className="productIconRow"><div className="productIcon" aria-hidden="true">Auto</div><div><strong>Ícone automático</strong><p className="muted">Product novo gera um ProductIcon após criar.</p></div></div>
    </div>
    <div id="quick-catalog-limitation" className="notice" data-state="warning">A criação rápida ainda não está conectada ao catálogo nesta superfície. Disponibilidade e fila continuam operacionais.</div>
  </section>;
}

export function ProductionBoard({ station, title }: { station: "BAR" | "KITCHEN"; title: string }) {
  const [items, setItems] = useState<Item[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [message, setMessage] = useState("");
  const [changingProductId, setChangingProductId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const [queue, catalog] = await Promise.all([
      apiCall<{ results: Item[] }>(`/api/pos/production/${station}/`),
      apiCall<{ results: Product[] }>("/api/pos/catalog/products/"),
    ]);
    if (queue.response.ok) setItems((queue.body as { results: Item[] }).results);
    else setMessage(asApiError(queue.body).message);
    if (catalog.response.ok) setProducts((catalog.body as { results: Product[] }).results.filter((product) => product.fulfillment_station === station));
    else setMessage(asApiError(catalog.body).message);
    setLoading(false);
  }, [station]);

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(), 5000);
    return () => window.clearInterval(timer);
  }, [load]);

  const advance = async (item: Item) => {
    const action = next[item.state];
    if (!action) return;
    const result = await apiCall(`/api/pos/order-items/${item.id}/transition/`, { method: "POST", body: JSON.stringify({ state: action.state }) });
    if (!result.response.ok) setMessage(asApiError(result.body).message);
    await load();
  };

  const toggleAvailability = async (product: Product) => {
    const state = product.availability === "AVAILABLE" ? "UNAVAILABLE" : "AVAILABLE";
    setChangingProductId(product.id);
    const result = await apiCall(`/api/pos/catalog/products/${product.id}/availability/`, { method: "POST", body: JSON.stringify({ state }) });
    if (!result.response.ok) setMessage(asApiError(result.body).message);
    await load();
    setChangingProductId(null);
  };

  const waiting = items.filter((item) => item.state !== "READY");
  const ready = items.filter((item) => item.state === "READY");

  return <main className="appShell">
    <header className="productHeader">
      <div className="eyebrow">RODADA / {title.toUpperCase()}</div>
      <h1>{title}</h1>
      <p className="muted">Fila da estação · atualiza a cada 5 segundos</p>
    </header>
    {message && <div className="notice" data-state="danger" role="alert">{message}</div>}

    <section className="panel" aria-labelledby="availability-title">
      <div className="eyebrow">Cardápio da estação</div>
      <h2 id="availability-title">Disponibilidade agora</h2>
      {loading ? <div className="loadingState">Carregando disponibilidade…</div> : products.map((product) => {
        const available = product.availability === "AVAILABLE";
        return <article className="dataRow" key={product.id}>
          <span><strong>{product.name}</strong><br /><small className="muted">{available ? "Disponível para vender" : "Indisponível em todos os canais"}</small></span>
          <div className="actions"><span className="statusBadge" data-state={available ? "success" : "danger"}>{available ? "Disponível" : "Indisponível"}</span><button className={available ? "buttonSecondary" : "buttonPrimary"} disabled={changingProductId === product.id} onClick={() => void toggleAvailability(product)}>{changingProductId === product.id ? "Salvando…" : available ? "Indisponibilizar" : "Reativar"}</button></div>
        </article>;
      })}
      {!loading && !products.length && <div className="emptyState">Nenhum produto roteado para esta estação.</div>}
    </section>

    <QuickCatalogUnavailable station={title} />

    <section className="panel panelWarning" aria-labelledby="queue-title">
      <div className="eyebrow">Fila de produção</div>
      <h2 id="queue-title">Em produção</h2>
      {loading ? <div className="loadingState">Carregando fila…</div> : waiting.map((item) => <article className="dataRow" key={item.id}>
        <span><strong>{item.quantity}× {item.product_name}</strong><br /><small className="muted">{item.tab_label || "Sem identificação"}</small></span>
        <div className="actions"><span className="statusBadge" data-state={itemState(item.state)}>{item.state}</span><button className="buttonPrimary" onClick={() => void advance(item)}>{next[item.state]?.label || item.state}</button></div>
      </article>)}
      {!loading && !waiting.length && <div className="emptyState">Nenhum item aguardando preparo.</div>}
    </section>

    <section className="panel panelSuccess" aria-labelledby="ready-title">
      <div className="eyebrow">Passe</div>
      <h2 id="ready-title">Pronto para retirada</h2>
      {ready.map((item) => <div className="dataRow" key={item.id}><span><strong>{item.quantity}× {item.product_name}</strong></span><span className="statusBadge" data-state="success">{item.tab_label || "Sem identificação"}</span></div>)}
      {!loading && !ready.length && <div className="emptyState">Nada no passe.</div>}
    </section>
  </main>;
}
