"use client";

import { useCallback, useEffect, useState } from "react";
import { apiCall, asApiError } from "@/lib/client/staff-auth";

type Item = { id: string; state: string; quantity: number; product_name: string; tab_label: string; created_at: string };
const next: Record<string, { state: string; label: string }> = { NEW: { state: "ACCEPTED", label: "Aceitar" }, ACCEPTED: { state: "PREPARING", label: "Preparar" }, PREPARING: { state: "READY", label: "Pronto" } };

export function ProductionBoard({ station, title }: { station: "BAR" | "KITCHEN"; title: string }) {
  const [items, setItems] = useState<Item[]>([]); const [message, setMessage] = useState("");
  const load = useCallback(async () => { const result = await apiCall<{ results: Item[] }>(`/api/pos/production/${station}/`); if (result.response.ok) setItems((result.body as { results: Item[] }).results); else setMessage(asApiError(result.body).message); }, [station]);
  useEffect(() => { void load(); const timer = window.setInterval(() => void load(), 5000); return () => window.clearInterval(timer); }, [load]);
  const advance = async (item: Item) => { const action = next[item.state]; if (!action) return; const result = await apiCall(`/api/pos/order-items/${item.id}/transition/`, { method: "POST", body: JSON.stringify({ state: action.state }) }); if (!result.response.ok) setMessage(asApiError(result.body).message); await load(); };
  return <main className="appShell"><header className="productHeader"><div className="eyebrow">RODADA / PRODUÇÃO</div><h1>{title}</h1><p className="muted">Fila persistida · atualiza a cada 5 segundos</p></header>{message && <div className="notice" data-state="danger">{message}</div>}<section className="panel"><h2>Em produção</h2>{items.filter((item) => item.state !== "READY").map((item) => <article className="dataRow" key={item.id}><span><strong>{item.quantity}× {item.product_name}</strong><br />{item.tab_label || "Sem identificação"} · {item.state}</span><button className="buttonPrimary" onClick={() => void advance(item)}>{next[item.state]?.label || item.state}</button></article>)}{!items.filter((item) => item.state !== "READY").length && <p className="muted">Nenhum item aguardando preparo.</p>}</section><section className="panel"><h2>Pronto</h2>{items.filter((item) => item.state === "READY").map((item) => <div className="dataRow" key={item.id}><span>{item.quantity}× {item.product_name}</span><strong>{item.tab_label || "Sem identificação"}</strong></div>)}{!items.filter((item) => item.state === "READY").length && <p className="muted">Nada no passe.</p>}</section></main>;
}
