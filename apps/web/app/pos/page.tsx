"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { BillSummary, type Bill } from "@/components/bill-summary";
import { PricingAdjustments } from "@/components/pricing-adjustments";
import Link from "next/link";
import { apiCall, asApiError } from "@/lib/client/staff-auth";

import { ProductIcon, IconReference } from "@/components/product-icon";

import { ProductCustomization, CustomizationText, defaults, selectionError, unitPrice, type OrderingProduct, type Selection } from "@/components/product-customization";

type Product = OrderingProduct & { icon: IconReference; availability: string; id: string; name: string; price_cents: number; fulfillment_station: string; active: boolean };
type Tab = Bill & { version: number; id: string; display_label: string; state: string; exposure_cents: number; charges_cents: number; payments_cents: number };
type CashPoint = { id: string; label: string; active_shift: { id: string; status: string } | null };
const money = (value = 0) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value / 100);

export default function PosPage() {
  const [tabs, setTabs] = useState<Tab[]>([]), [products, setProducts] = useState<Product[]>([]), [cashPoints, setCashPoints] = useState<CashPoint[]>([]), [cashPointId, setCashPointId] = useState(""), [selected, setSelected] = useState<Tab | null>(null), [cart, setCart] = useState<{ product: Product; quantity: number; selection: Selection }[]>([]), [label, setLabel] = useState(""), [payment, setPayment] = useState(""), [message, setMessage] = useState(""), [confirming, setConfirming] = useState(false);
  const [configuring, setConfiguring] = useState<Product | null>(null);
  const [editing, setEditing] = useState<number | null>(null);
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
  useEffect(() => { void load(); const timer = setInterval(() => void load(), 15000); return () => clearInterval(timer); }, [load]);
  useEffect(() => { setSelected(current => current ? tabs.find(tab => tab.id === current.id) ?? current : null); }, [tabs]);
  const rows = useMemo(() => cart.map(row => ({ ...row, product: products.find(p => p.id === row.product.id) ?? { ...row.product, active: false } })), [products, cart]);
  const total = rows.reduce((sum, row) => sum + unitPrice(row.product, row.selection) * row.quantity, 0);
  const createTab = async () => { const r = await apiCall<Tab>("/api/pos/tabs/", { method: "POST", body: JSON.stringify({ display_label: label }) }); if (r.response.ok) { setSelected(r.body as Tab); setLabel(""); await load(); } else setMessage(asApiError(r.body).message); };
  const confirm = async () => {
    if (!selected || !rows.length || confirming) return;
    setConfirming(true);
    const idempotencyKey = confirmIntentRef.current ?? crypto.randomUUID();
    confirmIntentRef.current = idempotencyKey;
    try {
      const r = await apiCall(`/api/pos/tabs/${selected.id}/orders/confirm/`, { method: "POST", body: JSON.stringify({ idempotency_key: idempotencyKey, lines: rows.map((row) => ({ product_id: row.product.id, quantity: row.quantity, ...row.selection })) }) });
      if (r.response.ok) { confirmIntentRef.current = null; setCart([]); await load(); const detail = await apiCall<Tab>(`/api/pos/tabs/${selected.id}/`); if (detail.response.ok) setSelected(detail.body as Tab); } else { setMessage(asApiError(r.body).message); if (r.response.status < 500) { confirmIntentRef.current = null; await load(); } }
    } catch { setMessage("Não foi possível confirmar. Tente novamente para verificar este mesmo pedido."); }
    finally { setConfirming(false); }
  };
  const collect = async () => { if (!selected) return; if (!cashPointId) { setMessage("Abra ou selecione um caixa ativo antes de receber dinheiro."); return; } const amount = Math.round(Number(payment.replace(",", ".")) * 100); const r = await apiCall(`/api/pos/tabs/${selected.id}/payments/`, { method: "POST", body: JSON.stringify({ amount_cents: amount, expected_version: selected.version, method: "CASH", cash_point_id: cashPointId, idempotency_key: crypto.randomUUID() }) }); if (r.response.ok) { setPayment(""); const detail = await apiCall<Tab>(`/api/pos/tabs/${selected.id}/`); if (detail.response.ok) setSelected(detail.body as Tab); await load(); } else setMessage(asApiError(r.body).message); };
  const close = async () => { if (!selected) return; const r = await apiCall(`/api/pos/tabs/${selected.id}/close/`, { method: "POST", body: "{}" }); if (r.response.ok) { setSelected(null); await load(); } else setMessage(asApiError(r.body).message); };
  return <main className="appShell"><header className="productHeader"><div className="eyebrow">RODADA / ATENDIMENTO</div><h1>Comandas e pedidos</h1><p className="muted">Estado financeiro e operacional persistido.</p><div className="actions"><Link className="backLink" href="/cash">Abrir caixa →</Link><Link className="backLink" href="/manage">Gestão →</Link><Link className="backLink" href="/refunds">Estornos →</Link></div></header>{message && <div className="notice" data-state="danger">{message}</div>}<section className="panel"><h2>Abrir comanda</h2><div className="field"><input aria-label="Apelido da comanda (opcional)" value={label} onChange={(event) => setLabel(event.target.value)} placeholder="Apelido opcional" /></div><button className="buttonPrimary" onClick={() => void createTab()}>Abrir</button></section><section className="panel"><h2>Comandas abertas</h2>{tabs.filter((tab) => tab.state !== "CLOSED").map((tab) => <button className="buttonSecondary" style={{ width: "100%", marginBottom: 8, textAlign: "left" }} key={tab.id} disabled={confirming || !!confirmIntentRef.current} onClick={() => { setSelected(tab); setCart([]); }}>{tab.display_label || "Sem identificação"} · {money(tab.exposure_cents)}</button>)}</section>{selected && <section className="panel"><h2>{selected.display_label || "Comanda"}</h2><BillSummary bill={selected} /><PricingAdjustments key={selected.id} tabId={selected.id} version={selected.version} onChanged={async () => { const detail = await apiCall<Tab>(`/api/pos/tabs/${selected.id}/`); if (detail.response.ok) setSelected(detail.body as Tab); await load(); }} /><h2 style={{ marginTop: 22 }}>Catálogo</h2>{products.map((product) => <button key={product.id} className="buttonSecondary" style={{ width: "100%", marginBottom: 8, textAlign: "left" }} disabled={product.availability !== "AVAILABLE" || confirming || !!confirmIntentRef.current} onClick={() => { if (product.variants?.length || product.modifier_groups?.length) { setEditing(null); setConfiguring(product); } else setCart(c => [...c, { product, quantity: 1, selection: defaults(product) }]); }}><ProductIcon icon={product.icon} />{product.name} · {money(product.price_cents)} </button>)}{configuring && <ProductCustomization key={`${configuring.id}-${editing}`} product={products.find(p => p.id === configuring.id) ?? configuring} initial={editing === null ? undefined : cart[editing]?.selection} onCancel={() => { setConfiguring(null); setEditing(null); }} onAdd={selection => { setCart(c => editing === null ? [...c, { product: configuring, selection, quantity: 1 }] : c.map((r, i) => i === editing ? { ...r, selection } : r)); setConfiguring(null); setEditing(null); }} />}{rows.map((row, index) => <div className="dataRow" key={index}><div><strong>{row.quantity}× {row.product.name}</strong><CustomizationText snapshot={{ variant: row.product.variants?.find(v => v.id === row.selection.variant_id), modifiers: row.product.modifier_groups?.flatMap(g => g.options.filter(o => row.selection.modifier_option_ids.includes(o.id)).map(o => ({ ...o, group_name: g.name }))), special_instructions: row.selection.special_instructions }} />{selectionError(row.product, row.selection) && <p className="notice" data-state="danger">{selectionError(row.product, row.selection)}</p>}</div><div className="actions"><button className="buttonQuiet" disabled={confirming || !!confirmIntentRef.current} onClick={() => { setConfiguring(row.product); setEditing(index); }}>Editar</button><button className="buttonQuiet" disabled={confirming || !!confirmIntentRef.current} onClick={() => setCart(c => c.filter((_, i) => i !== index))}>Remover</button></div></div>)}<button className="buttonPrimary" disabled={!rows.length || confirming || (!confirmIntentRef.current && rows.some(row => !row.product.active || row.product.availability !== "AVAILABLE" || !!selectionError(row.product, row.selection)))} onClick={() => void confirm()}>{confirming ? "Confirmando…" : `Confirmar pedido · ${money(total)}`}</button><h2 style={{ marginTop: 22 }}>Receber em dinheiro</h2><div className="field"><select aria-label="Caixa aberto" value={cashPointId} onChange={(event) => setCashPointId(event.target.value)}><option value="">Selecionar caixa aberto</option>{cashPoints.map((point) => <option key={point.id} value={point.id}>{point.label}</option>)}</select></div><div className="field"><input aria-label="Valor do pagamento" inputMode="decimal" value={payment} onChange={(event) => setPayment(event.target.value)} placeholder="Valor" /></div><button className="buttonPrimary" onClick={() => void collect()}>Receber em dinheiro</button><button className="buttonQuiet" style={{ width: "100%", marginTop: 8 }} onClick={() => void close()}>Fechar comanda</button></section>}</main>;
}
