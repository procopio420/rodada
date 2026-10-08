"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { apiCall, asApiError } from "@/lib/client/staff-auth";

type Product = { id: string; name: string; price_cents: number; fulfillment_station: string; active: boolean; availability: "AVAILABLE" | "UNAVAILABLE" };
type Tab = { id: string; display_label: string; state: string; exposure_cents: number; charges_cents: number; payments_cents: number };
type CashPoint = { id: string; label: string; active_shift: { id: string; status: string } | null };
const money = (value = 0) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value / 100);

export default function PosPage() {
  const [tabs, setTabs] = useState<Tab[]>([]), [products, setProducts] = useState<Product[]>([]), [cashPoints, setCashPoints] = useState<CashPoint[]>([]), [cashPointId, setCashPointId] = useState(""), [selected, setSelected] = useState<Tab | null>(null), [cart, setCart] = useState<Record<string, number>>({}), [label, setLabel] = useState(""), [payment, setPayment] = useState(""), [message, setMessage] = useState(""), [confirming, setConfirming] = useState(false);
  const confirmIntentRef = useRef<string | null>(null);
  const load = useCallback(async () => {
    const [tabResult, productResult, cashResult] = await Promise.all([apiCall<{ results: Tab[] }>("/api/pos/tabs/"), apiCall<{ results: Product[] }>("/api/pos/catalog/products/"), apiCall<{ results: CashPoint[] }>("/api/pos/cash/points/")]);
    if (tabResult.response.ok) setTabs((tabResult.body as { results: Tab[] }).results); else setMessage(asApiError(tabResult.body).message);
    if (productResult.response.ok) setProducts((productResult.body as { results: Product[] }).results); else setMessage(asApiError(productResult.body).message);
    if (cashResult.response.ok) {
      const points = (cashResult.body as { results: CashPoint[] }).results.filter((point) => point.active_shift);
      setCashPoints(points);
      setCashPointId((current) => points.some((point) => point.id === current) ? current : (points[0]?.id || ""));
    }
  }, []);
  useEffect(() => { void load(); }, [load]);
  const rows = useMemo(() => products.filter((product) => cart[product.id]).map((product) => ({ product, quantity: cart[product.id] })), [products, cart]);
  const total = rows.reduce((sum, row) => sum + row.product.price_cents * row.quantity, 0);
  const createTab = async () => { const r = await apiCall<Tab>("/api/pos/tabs/", { method: "POST", body: JSON.stringify({ display_label: label }) }); if (r.response.ok) { setSelected(r.body as Tab); setLabel(""); await load(); } else setMessage(asApiError(r.body).message); };
  const confirm = async () => {
    if (!selected || !rows.length || confirming) return;
    setConfirming(true);
    const idempotencyKey = confirmIntentRef.current ?? crypto.randomUUID();
    confirmIntentRef.current = idempotencyKey;
    try {
      const r = await apiCall(`/api/pos/tabs/${selected.id}/orders/confirm/`, { method: "POST", body: JSON.stringify({ idempotency_key: idempotencyKey, lines: rows.map((row) => ({ product_id: row.product.id, quantity: row.quantity })) }) });
      if (r.response.ok) { confirmIntentRef.current = null; setCart({}); await load(); const detail = await apiCall<Tab>(`/api/pos/tabs/${selected.id}/`); if (detail.response.ok) setSelected(detail.body as Tab); } else { setMessage(asApiError(r.body).message); if (r.response.status < 500) confirmIntentRef.current = null; }
    } catch { setMessage("Não foi possível confirmar. Tente novamente para verificar este mesmo pedido."); }
    finally { setConfirming(false); }
  };
  const collect = async () => { if (!selected) return; if (!cashPointId) { setMessage("Abra ou selecione um caixa ativo antes de receber dinheiro."); return; } const amount = Math.round(Number(payment.replace(",", ".")) * 100); const r = await apiCall(`/api/pos/tabs/${selected.id}/payments/`, { method: "POST", body: JSON.stringify({ amount_cents: amount, method: "CASH", cash_point_id: cashPointId, idempotency_key: crypto.randomUUID() }) }); if (r.response.ok) { setPayment(""); const detail = await apiCall<Tab>(`/api/pos/tabs/${selected.id}/`); if (detail.response.ok) setSelected(detail.body as Tab); await load(); } else setMessage(asApiError(r.body).message); };
  const close = async () => { if (!selected) return; const r = await apiCall(`/api/pos/tabs/${selected.id}/close/`, { method: "POST", body: "{}" }); if (r.response.ok) { setSelected(null); await load(); } else setMessage(asApiError(r.body).message); };
  return <main className="appShell"><header className="productHeader"><div className="eyebrow">RODADA / ATENDIMENTO</div><h1>Comandas e pedidos</h1><p className="muted">Estado financeiro e operacional persistido.</p><div className="actions"><Link className="backLink" href="/cash">Abrir caixa →</Link><Link className="backLink" href="/manage">Gestão →</Link><Link className="backLink" href="/refunds">Estornos →</Link></div></header>{message && <div className="notice" data-state="danger">{message}</div>}<section className="panel"><h2>Abrir comanda</h2><div className="field"><input aria-label="Apelido da comanda (opcional)" value={label} onChange={(event) => setLabel(event.target.value)} placeholder="Apelido opcional" /></div><button className="buttonPrimary" onClick={() => void createTab()}>Abrir</button></section><section className="panel"><h2>Comandas abertas</h2>{tabs.filter((tab) => tab.state !== "CLOSED").map((tab) => <button className="buttonSecondary" style={{ width: "100%", marginBottom: 8, textAlign: "left" }} key={tab.id} onClick={() => setSelected(tab)}>{tab.display_label || "Sem identificação"} · {money(tab.exposure_cents)}</button>)}</section>{selected && <section className="panel"><h2>{selected.display_label || "Comanda"}</h2><div className="dataRow"><span>Consumo</span><strong>{money(selected.charges_cents)}</strong></div><div className="dataRow"><span>Recebido</span><strong>{money(selected.payments_cents)}</strong></div><div className="dataRow"><span>Em aberto</span><strong>{money(selected.exposure_cents)}</strong></div><h2 style={{ marginTop: 22 }}>Catálogo</h2>{products.map((product) => <button key={product.id} className="buttonSecondary" disabled={product.availability !== "AVAILABLE"} style={{ width: "100%", marginBottom: 8, textAlign: "left" }} onClick={() => setCart((value) => ({ ...value, [product.id]: (value[product.id] || 0) + 1 }))}>{product.name} · {money(product.price_cents)}{product.availability !== "AVAILABLE" ? " · Indisponível" : ""} {cart[product.id] ? `×${cart[product.id]}` : ""}</button>)}<button className="buttonPrimary" disabled={!rows.length || confirming} onClick={() => void confirm()}>{confirming ? "Confirmando…" : `Confirmar pedido · ${money(total)}`}</button><h2 style={{ marginTop: 22 }}>Receber em dinheiro</h2><div className="field"><select aria-label="Caixa aberto" value={cashPointId} onChange={(event) => setCashPointId(event.target.value)}><option value="">Selecionar caixa aberto</option>{cashPoints.map((point) => <option key={point.id} value={point.id}>{point.label}</option>)}</select></div><div className="field"><input aria-label="Valor do pagamento" inputMode="decimal" value={payment} onChange={(event) => setPayment(event.target.value)} placeholder="Valor" /></div><button className="buttonPrimary" onClick={() => void collect()}>Receber em dinheiro</button><button className="buttonQuiet" style={{ width: "100%", marginTop: 8 }} onClick={() => void close()}>Fechar comanda</button></section>}</main>;
}
