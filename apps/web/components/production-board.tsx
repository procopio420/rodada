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

export function ProductionBoard({ station, title }: { station: "BAR" | "KITCHEN"; title: string }) {
  const [items, setItems] = useState<Item[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [message, setMessage] = useState("");
  const [changingProductId, setChangingProductId] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [queue, catalog] = await Promise.all([
      apiCall<{ results: Item[] }>(`/api/pos/production/${station}/`),
      apiCall<{ results: Product[] }>("/api/pos/catalog/products/"),
    ]);
    if (queue.response.ok) setItems((queue.body as { results: Item[] }).results);
    else setMessage(asApiError(queue.body).message);
    if (catalog.response.ok) {
      setProducts((catalog.body as { results: Product[] }).results.filter((product) => product.fulfillment_station === station));
    } else setMessage(asApiError(catalog.body).message);
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

  return <main className="appShell"><header className="productHeader"><div className="eyebrow">RODADA / {title.toUpperCase()}</div><h1>Produção {title}</h1><p className="muted">Fila persistida · atualiza a cada 5 segundos</p></header>{message && <div className="notice" data-state="danger">{message}</div>}<section className="panel"><h2>Disponibilidade agora</h2>{products.map((product) => { const available = product.availability === "AVAILABLE"; return <article className="dataRow" key={product.id}><span><strong>{product.name}</strong><br />{available ? "Disponível para vender" : "Indisponível"}</span><button className={available ? "buttonQuiet" : "buttonPrimary"} disabled={changingProductId === product.id} onClick={() => void toggleAvailability(product)}>{changingProductId === product.id ? "Salvando…" : available ? "Indisponibilizar" : "Reativar"}</button></article>; })}{!products.length && <p className="muted">Nenhum produto roteado para esta estação.</p>}</section><section className="panel"><h2>Em produção</h2>{waiting.map((item) => <article className="dataRow" key={item.id}><span><strong>{item.quantity}× {item.product_name}</strong><br />{item.tab_label || "Sem identificação"} · {item.state}</span><button className="buttonPrimary" onClick={() => void advance(item)}>{next[item.state]?.label || item.state}</button></article>)}{!waiting.length && <p className="muted">Nenhum item aguardando preparo.</p>}</section><section className="panel"><h2>Pronto</h2>{ready.map((item) => <div className="dataRow" key={item.id}><span>{item.quantity}× {item.product_name}</span><strong>{item.tab_label || "Sem identificação"}</strong></div>)}{!ready.length && <p className="muted">Nada no passe.</p>}</section></main>;
}
