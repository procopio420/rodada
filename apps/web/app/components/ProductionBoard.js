"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const POLL_INTERVAL_MS = 5000;
const stationName = { BAR: "Bar", KITCHEN: "Cozinha" };
const stateName = { NEW: "Recebido", ACCEPTED: "Aceito", PREPARING: "Em preparo", READY: "Pronto" };
const nextState = {
  NEW: { state: "ACCEPTED", label: "Aceitar" },
  ACCEPTED: { state: "PREPARING", label: "Iniciar" },
  PREPARING: { state: "READY", label: "Marcar pronto" },
};

async function api(path, options = {}) {
  const token = typeof window === "undefined" ? "" : localStorage.getItem("rodada-session-token");
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Não foi possível concluir a operação.");
  return data;
}

function secondsSince(value) { return value ? Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000)) : 0; }
function elapsed(seconds) { return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`; }
function itemAge(item) { return secondsSince(item.preparing_at || item.accepted_at || item.created_at); }
function urgency(item) { const age = itemAge(item); return age >= 720 ? "critical" : age >= 480 ? "late" : age >= 180 ? "watch" : "normal"; }

function flattenOrders(tabs, station) {
  return tabs.flatMap((tab) => (tab.orders || [])
    .filter((order) => order.status === "CONFIRMED")
    .flatMap((order) => (order.items || []).map((item) => ({
      ...item, orderId: order.id, tabId: tab.id,
      tabLabel: tab.customer_name || tab.label || `Comanda #${tab.id}`,
      destination: tab.service_point_code || "Sem localização",
    }))))
    .filter((item) => item.fulfillment_station === station)
    .filter((item) => !["CANCELLED", "DELIVERED", "PICKED_UP"].includes(item.state))
    .sort((left, right) => itemAge(right) - itemAge(left));
}

export default function ProductionBoard({ station }) {
  const [tabs, setTabs] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [workingId, setWorkingId] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [, setTick] = useState(0);
  const load = useCallback(async ({ quiet = false } = {}) => {
    if (!quiet) setLoading(true);
    try {
      const [tabRows, productRows] = await Promise.all([api("/tabs/"), api("/products/")]);
      setTabs(tabRows);
      setProducts(productRows.filter((product) => product.fulfillment_station === station));
      setError("");
    } catch (loadError) { setError(loadError.message); }
    finally { if (!quiet) setLoading(false); }
  }, [station]);
  useEffect(() => {
    load();
    const poller = window.setInterval(() => load({ quiet: true }), POLL_INTERVAL_MS);
    const ticker = window.setInterval(() => setTick((tick) => tick + 1), 1000);
    return () => { window.clearInterval(poller); window.clearInterval(ticker); };
  }, [load]);
  const items = useMemo(() => flattenOrders(tabs, station), [tabs, station]);
  const active = items.filter((item) => item.state !== "READY");
  const ready = items.filter((item) => item.state === "READY");
  const grouped = useMemo(() => active.reduce((groups, item) => {
    const value = groups.get(item.product_name) || { quantity: 0, destinations: [] };
    value.quantity += item.quantity;
    if (!value.destinations.includes(item.destination)) value.destinations.push(item.destination);
    groups.set(item.product_name, value); return groups;
  }, new Map()), [active]);
  const transition = async (item) => {
    const transitionTo = nextState[item.state]; if (!transitionTo) return;
    setWorkingId(item.id); setError(""); setNotice("");
    try {
      await api(`/order-items/${item.id}/transition/`, { method: "POST", body: JSON.stringify({ state: transitionTo.state }) });
      setNotice(`${item.product_name}: ${stateName[transitionTo.state].toLowerCase()}.`);
      await load({ quiet: true });
    } catch (transitionError) { setError(transitionError.message); }
    finally { setWorkingId(null); }
  };
  const setAvailability = async (product, available) => {
    setWorkingId(`product-${product.id}`); setError(""); setNotice("");
    try {
      await api(`/products/${product.id}/availability/`, { method: "POST", body: JSON.stringify({ available }) });
      setNotice(`${product.name} está ${available ? "disponível" : "indisponível"}.`);
      await load({ quiet: true });
    } catch (availabilityError) { setError(availabilityError.message); }
    finally { setWorkingId(null); }
  };
  const title = stationName[station];
  return <main className="production-page">
    <header className="production-header"><div><Link className="production-back" href="/">← Atendimento</Link><p className="kicker">FILA DE PRODUÇÃO · ATUALIZA A CADA 5 S</p><h1>{title}</h1><p className="production-subtitle">{active.length} em produção · {ready.length} pronto{ready.length === 1 ? "" : "s"} aguardando retirada</p></div><nav aria-label="Estações de produção" className="production-stations"><Link className={station === "BAR" ? "active" : ""} href="/bar">Bar</Link><Link className={station === "KITCHEN" ? "active" : ""} href="/kitchen">Cozinha</Link></nav></header>
    {error && <p className="production-message error" role="alert">{error}</p>}{notice && <p className="production-message success" role="status">{notice}</p>}
    <section className="production-summary" aria-label="Resumo da produção"><article><b>{active.length}</b><span>Para fazer</span></article><article><b>{active.filter((item) => itemAge(item) >= 720).length}</b><span>Acima de 12 min</span></article><article><b>{ready.length}</b><span>No passe</span></article></section>
    <section className="production-columns">
      <div className="production-totals"><div className="production-section-label">Resumo por item</div>{[...grouped.entries()].map(([name, value]) => <article key={name} className="production-total"><span><b>{name}</b><small>{value.destinations.join(" · ")}</small></span><strong>{value.quantity}</strong></article>)}{!loading && grouped.size === 0 && <Empty>Sem itens aguardando preparo.</Empty>}</div>
      <div className="production-queue"><div className="production-section-label">Pedidos · mais antigo primeiro</div>{loading && <Empty>Carregando fila…</Empty>}{!loading && active.map((item) => <ProductionItem item={item} key={item.id} busy={workingId === item.id} onTransition={transition} />)}{!loading && active.length === 0 && <Empty>Nenhum item para produzir agora.</Empty>}</div>
      <div className="production-ready"><div className="production-section-label">Pronto · aguardando retirada</div>{ready.map((item) => <ReadyItem item={item} key={item.id} />)}{!loading && ready.length === 0 && <Empty>O próximo item pronto aparece aqui.</Empty>}</div>
    </section>
    <section className="availability-panel"><div><p className="kicker">CARDÁPIO OPERACIONAL</p><h2>Disponibilidade do {title.toLowerCase()}</h2><p>Uma alteração aqui usa a disponibilidade canônica do catálogo. O servidor só permite a gestores.</p></div><div className="availability-list">{products.map((product) => <article key={product.id} className={product.available ? "available" : "unavailable"}><span><b>{product.name}</b><small>{product.available ? "Disponível para novos pedidos" : "Indisponível para novos pedidos"}</small></span><button className="availability-toggle" disabled={workingId === `product-${product.id}`} onClick={() => setAvailability(product, !product.available)}>{workingId === `product-${product.id}` ? "Salvando…" : product.available ? "Indisponibilizar" : "Disponibilizar"}</button></article>)}{!loading && products.length === 0 && <Empty>Nenhum produto desta estação.</Empty>}</div></section>
  </main>;
}

function ProductionItem({ item, busy, onTransition }) {
  const action = nextState[item.state];
  return <article className={`production-ticket ${urgency(item)}`}><div className="production-age"><span>{stateName[item.state]}</span><b>{elapsed(itemAge(item))}</b></div><div><p className="production-destination">{item.destination}</p><h2>{item.quantity}× {item.product_name}</h2><small>{item.tabLabel} · Pedido #{item.orderId}</small></div><button className="btn primary" disabled={busy} onClick={() => onTransition(item)}>{busy ? "…" : action.label}</button></article>;
}
function ReadyItem({ item }) { return <article className="production-ready-item"><b>{item.destination}</b><span>{item.quantity}× {item.product_name}<small>{item.tabLabel}</small></span></article>; }
function Empty({ children }) { return <p className="production-empty">{children}</p>; }
