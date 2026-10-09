"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ProductIcon, type IconData } from "./product-icon";

import { ProductCustomization, CustomizationText, defaults, selectionError, unitPrice, type OrderingProduct, type Selection, type Snapshot } from "./product-customization";

type Product = OrderingProduct & { id: string; name: string; price_cents: number; fulfillment_station: string; available: boolean; icon?: IconData };
type OrderItem = { customization_snapshot?: Snapshot; id: string; product_name: string; quantity: number; line_total_cents: number; state: string; ready_at?: string | null; delivered_at?: string | null };
type Order = { id: string; status: string; items: OrderItem[] };
type Tab = { id: string; display_label: string; exposure_cents: number; consumption_blocked: boolean; remaining_capacity_cents: number; orders?: Order[] };
type Context = { table: { label: string }; occupancy_active: boolean; can_start_occupancy: boolean; guest_session_token?: string; tab: Tab | null };
type ApiError = { code?: string; message?: string };

const money = (value = 0) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value / 100);
const itemStates: Record<string, string> = { NEW: "Confirmado", ACCEPTED: "Aceito", PREPARING: "Em preparo", READY: "Pronto", PICKED_UP: "Retirado", DELIVERED: "Entregue", CANCELLED: "Cancelado" };

function messageFor(error: ApiError, fallback: string) {
  if (error.code === "GUEST_SESSION_REVOKED") return "Esta visita terminou. Escaneie o QR novamente para pedir na nova ocupação.";
  if (error.code === "GUEST_ORDERING_BLOCKED") return "Os pedidos por QR estão pausados. Peça ajuda à equipe.";
  if (error.code === "PRODUCTS_NOT_CONFIRMABLE") return "Um item do carrinho acabou de ficar indisponível. Atualize o pedido.";
  if (error.code === "SPENDING_LIMIT_EXCEEDED") return "Seu consumo precisa de atenção da equipe. Peça um pagamento parcial ou uma aprovação para continuar.";
  return error.message || fallback;
}

async function guestApi<T>(path: string, token: string, init: RequestInit = {}): Promise<{ ok: boolean; status: number; body: T | ApiError }> {
  try {
  const response = await fetch(`/api/guest/${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { "X-Guest-Session": token } : {}),
    },
  });
  const body = await response.json().catch(() => ({}));
  return { ok: response.ok, status: response.status, body };
  } catch { return { ok: false, status: 503, body: { code: "OFFLINE", message: "Sem conexão. Os dados podem estar desatualizados. Atualize antes de continuar." } }; }
}

export function GuestOrdering({ qrToken }: { qrToken: string }) {
  const storageKey = `rodada.guest.session.${qrToken}`;
  const [guestToken, setGuestToken] = useState("");
  const [context, setContext] = useState<Context | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [cart, setCart] = useState<{ product: Product; quantity: number; selection: Selection }[]>([]);
  const [configuring, setConfiguring] = useState<Product | null>(null);
  const [editing, setEditing] = useState<number | null>(null);
  const [label, setLabel] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [stale, setStale] = useState(true);
  const orderIntent = useRef<string | null>(null);

  const loadCatalog = useCallback(async (token: string) => {
    const result = await guestApi<{ results: Product[] }>("catalog/", token);
    if (result.ok) { setProducts((result.body as { results: Product[] }).results); return true; }
    setNotice(messageFor(result.body as ApiError, "Não foi possível atualizar o cardápio."));
    return false;
  }, []);

  const resolve = useCallback(async () => {
    setLoading(true);
    setNotice("");
    const stored = sessionStorage.getItem(storageKey) || "";
    const result = await guestApi<Context>("qr/resolve/", stored, {
      method: "POST",
      body: JSON.stringify({ token: qrToken }),
    });
    if (!result.ok) {
      if ((result.body as ApiError).code === "GUEST_SESSION_REVOKED") sessionStorage.removeItem(storageKey);
      setNotice(messageFor(result.body as ApiError, "Não foi possível abrir esta mesa."));
      setLoading(false);
      return;
    }
    const body = result.body as Context;
    const token = body.guest_session_token || stored;
    if (!token) {
      setNotice("Não foi possível iniciar sua sessão. Escaneie o QR novamente.");
      setLoading(false);
      return;
    }
    sessionStorage.setItem(storageKey, token);
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
      setNotice(""); setStale(!(await loadCatalog(guestToken)));
    }
    else {
      setStale(true); setNotice(messageFor(result.body as ApiError, "Atualize sua comanda antes de continuar."));
      if (["GUEST_SESSION_REVOKED", "GUEST_SESSION_EXPIRED", "GUEST_SESSION_INVALID", "GUEST_SESSION_REQUIRED"].includes((result.body as ApiError).code ?? "")) { setContext(null); sessionStorage.removeItem(storageKey); }
    }
  }, [guestToken, loadCatalog, storageKey]);
  useEffect(() => {
    void refresh();
    const offline = () => setStale(true);
    const timer = window.setInterval(() => { if (document.visibilityState === "visible") void refresh(); }, 5000);
    window.addEventListener("online", refresh); window.addEventListener("focus", refresh); window.addEventListener("offline", offline);
    return () => { clearInterval(timer); window.removeEventListener("online", refresh); window.removeEventListener("focus", refresh); window.removeEventListener("offline", offline); };
  }, [refresh]);

  const rows = useMemo(() => cart.map(row => ({ ...row, product: products.find(p => p.id === row.product.id) ?? { ...row.product, available: false } })), [cart, products]);
  const total = rows.reduce((sum, row) => sum + unitPrice(row.product, row.selection) * row.quantity, 0);
  const cartError = rows.some(row => !row.product.available || !!selectionError(row.product, row.selection));
  function addConfigured(product: Product, selection: Selection) {
    setCart(current => editing === null ? [...current, { product, selection, quantity: 1 }] : current.map((row, index) => index === editing ? { ...row, product, selection } : row));
    setConfiguring(null); setEditing(null);
  }

  async function createTab() {
    if (sending || stale) return;
    setSending(true);
    const result = await guestApi<Tab>("tabs/", guestToken, { method: "POST", body: JSON.stringify({ display_label: label }) });
    setSending(false);
    if (!result.ok) { setNotice(messageFor(result.body as ApiError, "Não foi possível abrir a comanda.")); return; }
    setContext((current) => current ? { ...current, tab: result.body as Tab } : current);
    setLabel("");
  }

  async function submitOrder() {
    if (!context?.tab || !rows.length || sending) return;
    setSending(true);
    const idempotencyKey = orderIntent.current || crypto.randomUUID();
    orderIntent.current = idempotencyKey;
    const result = await guestApi<Order>("orders/confirm/", guestToken, {
      method: "POST",
      body: JSON.stringify({ idempotency_key: idempotencyKey, lines: rows.map(({ product, quantity, selection }) => ({ product_id: product.id, quantity, ...selection })) }),
    });
    if (result.ok) {
      const confirmed = result.body as Order;
      setContext(current => current?.tab ? { ...current, tab: { ...current.tab, orders: [...(current.tab.orders ?? []).filter(order => order.id !== confirmed.id), confirmed] } } : current);
      orderIntent.current = null;
      setCart([]);
      const contextResult = await guestApi<{ tab: Tab | null }>("context/", guestToken);
      if (contextResult.ok) setContext((current) => {
        const tab = (contextResult.body as { tab: Tab | null }).tab;
        return current ? { ...current, tab: tab ? { ...tab, orders: tab.orders ?? current.tab?.orders } : null } : current;
      });
      else setNotice("Pedido confirmado. Não foi possível atualizar o saldo da comanda agora.");
      await loadCatalog(guestToken);
    } else {
      setNotice(messageFor(result.body as ApiError, "Não foi possível enviar o pedido."));
      if (result.status < 500) orderIntent.current = null;
      if (result.status >= 500) setStale(true);
      if (["MODIFIER_UNAVAILABLE", "VARIANT_UNAVAILABLE", "PRODUCTS_NOT_CONFIRMABLE", "MODIFIER_REQUIRED", "TOO_MANY_MODIFIERS"].includes((result.body as ApiError).code ?? "")) await loadCatalog(guestToken);
      if ((result.body as ApiError).code === "SPENDING_LIMIT_EXCEEDED") await refresh();
    }
    setSending(false);
  }

  if (loading) return <main className="appShell"><p className="muted">Abrindo sua mesa…</p></main>;
  if (!context) return <main className="appShell"><h1>Não foi possível abrir o pedido</h1><div className="notice" data-state="danger">{notice}</div><button className="buttonPrimary" onClick={() => void resolve()}>Tentar de novo</button></main>;

  return <main className="appShell guestShell">
    <header className="productHeader"><div className="eyebrow">RODADA / PEDIDO</div><h1>Mesa {context.table.label}</h1><p className="muted">Peça quando quiser. Sua comanda continua separada da mesa.</p></header>
    {notice && <div className="notice" data-state="danger" role="alert">{notice}</div>}
    {stale && <div className="notice" data-state="warning" role="status">Dados desatualizados. Reconecte para confirmar seu pedido.</div>}
    <button className="buttonQuiet" disabled={sending} onClick={() => void refresh()}>Atualizar comanda</button>
    {!context.tab ? <section className="panel"><h2>Começar pedido</h2><p className="muted">Crie uma comanda para enviar itens ao bar e à cozinha.</p><div className="field"><label htmlFor="guest-label">Seu nome ou apelido (opcional)</label><input id="guest-label" value={label} onChange={(event) => setLabel(event.target.value)} placeholder="Ex.: Ana" /></div><button className="buttonPrimary" disabled={sending || stale} onClick={() => void createTab()}>{sending ? "Abrindo…" : "Abrir minha comanda"}</button></section> : <>
      <section className="panel panelGuestBalance"><span className="eyebrow">Comanda</span><h2>{context.tab.display_label || "Minha comanda"}</h2><div className="guestBalance"><span>Em aberto</span><strong>{money(context.tab.exposure_cents)}</strong></div></section>
      {context.tab.consumption_blocked && <div className="notice" data-state="warning" role="alert">Para continuar consumindo, peça ajuda à equipe. Você pode pagar uma parte da comanda ou solicitar aprovação.</div>}
      <section className="panel"><h2>Cardápio</h2><div className="guestProducts">{products.map((product) => <button key={product.id} className="guestProduct" disabled={!product.available || stale || sending || !!orderIntent.current} onClick={() => { if (product.variants?.length || product.modifier_groups?.length) { setEditing(null); setConfiguring(product); } else addConfigured(product, defaults(product)); }}><ProductIcon icon={product.icon} /><span><strong>{product.name}</strong><small>{product.fulfillment_station === "BAR" ? "Bar" : "Cozinha"}{!product.available ? " · Indisponível" : ""}</small></span><span>{money(product.price_cents)}</span></button>)}</div></section>
      {configuring && <ProductCustomization key={`${configuring.id}-${editing}`} product={products.find(p => p.id === configuring.id) ?? configuring} initial={editing === null ? undefined : cart[editing]?.selection} onCancel={() => { setConfiguring(null); setEditing(null); }} onAdd={selection => addConfigured(configuring, selection)} />}
      {!!rows.length && <section className="panel"><h2>Revisar pedido</h2>{rows.map((row, index) => <div key={index} className="dataRow"><div><strong>{row.quantity}× {row.product.name}</strong><CustomizationText snapshot={{ variant: row.product.variants?.find(v => v.id === row.selection.variant_id), modifiers: row.product.modifier_groups?.flatMap(g => g.options.filter(o => row.selection.modifier_option_ids.includes(o.id)).map(o => ({ ...o, group_name: g.name }))), special_instructions: row.selection.special_instructions }} />{(!row.product.available || selectionError(row.product, row.selection)) && <p className="notice" data-state="danger">{!row.product.available ? "Produto indisponível" : selectionError(row.product, row.selection)}</p>}</div><div className="actions"><button className="buttonQuiet" disabled={sending || !!orderIntent.current} onClick={() => { setEditing(index); setConfiguring(row.product); }}>Editar</button><button className="buttonQuiet" disabled={sending || !!orderIntent.current} onClick={() => setCart(c => c.filter((_, i) => i !== index))}>Remover</button></div></div>)}</section>}
      {!configuring && <section className="guestCart"><span>{rows.length ? `${rows.reduce((sum, row) => sum + row.quantity, 0)} item(ns)` : "Seu carrinho está vazio"}</span><button className="buttonPrimary" disabled={!rows.length || sending || stale || (cartError && !orderIntent.current) || (context.tab.consumption_blocked && !orderIntent.current)} onClick={() => void submitOrder()}>{sending ? "Enviando…" : `Enviar · ${money(total)}`}</button></section>}
      <section className="panel"><h2>Meus pedidos</h2><p className="muted">Estado registrado pela operação. Atualiza a cada 5 segundos enquanto esta tela estiver aberta.</p>{!context.tab.orders?.length && <p>Nenhum pedido confirmado.</p>}{context.tab.orders?.map(order => <div key={order.id}>{order.items.map(item => <div className="dataRow" key={item.id}><span><strong>{item.quantity}× {item.product_name}</strong><CustomizationText snapshot={item.customization_snapshot} /><small className="muted"> · {money(item.line_total_cents)}{item.ready_at ? ` · pronto às ${new Date(item.ready_at).toLocaleTimeString("pt-BR")}` : ""}</small></span><span className="statusBadge" data-state={item.state === "CANCELLED" ? "danger" : ["READY", "DELIVERED"].includes(item.state) ? "success" : "info"}>{itemStates[item.state] ?? item.state}</span></div>)}</div>)}</section>
    </>}
  </main>;
}
