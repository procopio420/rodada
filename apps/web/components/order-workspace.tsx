"use client";

import { attendanceCategory, compareAttendanceCategories, normalizeCatalogSearch } from "@/lib/client/attendance-catalog";

import { OperationalHeading } from "@/components/operational-heading";
import { OperationalIcon } from "@/components/operational-icon";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AttendanceTabHistory } from "@/components/attendance-tab-history";
import { AttendanceDraft } from "@/components/attendance-draft";
import { ActionDialog } from "@/components/action-dialog";
import { ConfirmedItemRemoval } from "@/components/confirmed-item-removal";
import { BillSummary, type Bill } from "@/components/bill-summary";
import { PricingAdjustments } from "@/components/pricing-adjustments";
import Link from "next/link";
import { ReceiptPrinting } from "@/components/receipt-printing";
import { ProductIcon, type IconData } from "@/components/product-icon";
import { apiCall, asApiError } from "@/lib/client/staff-auth";


import { ProductCustomization, CustomizationText, defaults, selectionError, unitPrice, type OrderingProduct, type Selection } from "@/components/product-customization";

type Product = OrderingProduct & { category?: string; icon?: IconData; availability: string; id: string; name: string; price_cents: number; fulfillment_station: string; active: boolean };
type Tab = Bill & { orders?: { id: string; items: { id: string; product_name: string; quantity: number; state: string; customization_snapshot?: import("@/components/product-customization").Snapshot }[] }[]; version: number; id: string; display_label: string; state: string; exposure_cents: number; charges_cents: number; payments_cents: number };
type CashPoint = { id: string; label: string; active_shift: { id: string; status: string } | null };
const money = (value = 0) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value / 100);

export function OrderWorkspace({ withoutPayments = false, onPendingChange, requestedTabId, destinationLabel, recoveryScope }: { recoveryScope?: string; requestedTabId?: string; destinationLabel?: string; withoutPayments?: boolean; onPendingChange?: (pending: boolean) => void }) {
  const apiRoot = withoutPayments ? "/api/attendance" : "/api/pos";
  const [closingDialog, setClosingDialog] = useState(false), [closing, setClosing] = useState(false), [success, setSuccess] = useState("");
  const [tabCollapsed, setTabCollapsed] = useState(false);
  const [catalogCollapsed, setCatalogCollapsed] = useState(false);
  const [removingItem, setRemovingItem] = useState<{ id: string; product_name: string; quantity: number } | null>(null);
  const [itemCorrectionPending, setCorrectionPending] = useState(false);
  const [recoveryBlocked, setRecoveryBlocked] = useState(false);
  const [recoveryReady, setRecoveryReady] = useState(!recoveryScope);
  const correctionPending = itemCorrectionPending || recoveryBlocked || !recoveryReady;
  const recoveryKey = recoveryScope ? `rodada:order-draft:${recoveryScope}` : null;
  const [catalogSearch, setCatalogSearch] = useState("");
  const [category, setCategory] = useState("");
  const [showHistory, setShowHistory] = useState(false);
  const [tabs, setTabs] = useState<Tab[]>([]), [products, setProducts] = useState<Product[]>([]), [cashPoints, setCashPoints] = useState<CashPoint[]>([]), [cashPointId, setCashPointId] = useState(""), [selected, setSelected] = useState<Tab | null>(null), [cart, setCart] = useState<{ product: Product; quantity: number; selection: Selection }[]>([]), [label, setLabel] = useState(""), [payment, setPayment] = useState(""), [message, setMessage] = useState(""), [confirming, setConfirming] = useState(false);
  const [opening, setOpening] = useState(false);
  const [search, setSearch] = useState("");
  const [fresh, setFresh] = useState(false);
  const [configuring, setConfiguring] = useState<Product | null>(null);
  const [editing, setEditing] = useState<number | null>(null);
  const confirmIntentRef = useRef<string | null>(null);
  const pendingPayload = useRef<object | null>(null);
  useEffect(() => {
    if (!recoveryKey) return;
    try {
      const prefix = recoveryKey.slice(0, recoveryKey.lastIndexOf(":") + 1);
      if (Object.keys(localStorage).some(key => key.startsWith(prefix) && key !== recoveryKey)) {
        setRecoveryBlocked(true);
        setMessage("Pedido de outra sessão preservado. Confira o histórico com a gerência antes de repetir.");
      }
      const raw = localStorage.getItem(recoveryKey);
      if (raw) {
        const saved = JSON.parse(raw);
        if (saved.schema !== 1 || !saved.tab?.id || !Array.isArray(saved.cart) ||
            saved.cart.some((line: { product?: Product; quantity?: number; selection?: Selection }) => !line.product?.id || !Number.isInteger(line.quantity) || !line.selection) ||
            (!!saved.key !== !!saved.payload)) throw new Error("Invalid recovery record");
        setSelected(saved.tab); setCart(saved.cart);
        confirmIntentRef.current = saved.key;
        pendingPayload.current = saved.payload;
        setMessage(saved.key ? "Resposta pendente. Verifique o mesmo pedido na comanda original." : "Rascunho recuperado na comanda original.");
        void apiCall<Tab>(`${apiRoot}/tabs/${saved.tab.id}/`).then(result => {
          if (result.response.ok) setSelected(result.body as Tab);
        }).catch(() => {});
      }
    } catch {
      setRecoveryBlocked(true);
      setMessage("Recuperação indisponível. Confira o histórico antes de repetir o pedido.");
    } finally { setRecoveryReady(true); }
  }, [recoveryKey, apiRoot]);
  function persistDraft(tab = selected, draft = cart) {
    if (!recoveryKey) return;
    if (!tab || (!draft.length && !confirmIntentRef.current)) localStorage.removeItem(recoveryKey);
    else localStorage.setItem(recoveryKey, JSON.stringify({ schema: 1, tab, cart: draft, key: confirmIntentRef.current, payload: pendingPayload.current }));
  }
  useEffect(() => {
    if (!recoveryReady || recoveryBlocked) return;
    try { persistDraft(); } catch {
      setRecoveryBlocked(true); setMessage("Não foi possível preservar o rascunho. Confira o histórico antes de enviar.");
    }
  }, [recoveryKey, recoveryReady, recoveryBlocked, selected, cart, confirming]);
  useEffect(() => { if (!recoveryReady) return; onPendingChange?.(cart.length > 0 || !!confirmIntentRef.current || correctionPending); }, [cart.length, confirming, correctionPending, recoveryReady, onPendingChange]);
  const load = useCallback(async () => {
    try {
    setFresh(false);
    const [tabResult, productResult, cashResult] = await Promise.all([apiCall<{ results: Tab[] }>(`${apiRoot}/tabs/`), apiCall<{ results: Product[] }>(`${apiRoot}/catalog/products/`), withoutPayments ? Promise.resolve({ response: { ok: true }, body: { results: [] as CashPoint[] } }) : apiCall<{ results: CashPoint[] }>(`${apiRoot}/cash/points/`)]);
    if (tabResult.response.ok) setTabs((tabResult.body as { results: Tab[] }).results); else setMessage(asApiError(tabResult.body).message);
    if (productResult.response.ok) setProducts((productResult.body as { results: Product[] }).results); else setMessage(asApiError(productResult.body).message);
    if (cashResult.response.ok) {
      const points = (cashResult.body as { results: CashPoint[] }).results.filter((point) => point.active_shift);
      setCashPoints(points);
      setCashPointId((current) => points.some((point) => point.id === current) ? current : (points[0]?.id || ""));
    }
    setFresh(tabResult.response.ok && productResult.response.ok);
    } catch { setFresh(false); setMessage("Não foi possível atualizar. Os dados podem estar desatualizados."); }
  }, [apiRoot, withoutPayments]);
  useEffect(() => { void load(); const timer = setInterval(() => void load(), 15000); return () => clearInterval(timer); }, [load]);
  useEffect(() => { setSelected(current => current ? { ...current, ...(tabs.find(tab => tab.id === current.id) ?? {}) } : null); }, [tabs]);
  useEffect(() => {
    if (!requestedTabId || selected?.id === requestedTabId || cart.length || confirmIntentRef.current || correctionPending) return;
    let active = true;
    void apiCall<Tab>(`${apiRoot}/tabs/${requestedTabId}/`).then(result => {
      if (!active) return;
      if (result.response.ok) { setSelected(result.body as Tab); setTabCollapsed(false); setCatalogCollapsed(false); }
      else setMessage(asApiError(result.body).message);
    }).catch(() => setMessage("Não foi possível abrir esta comanda. Atualize e tente novamente."));
    return () => { active = false; };
  }, [requestedTabId, apiRoot]);
  const rows = useMemo(() => cart.map(row => ({ ...row, product: products.find(p => p.id === row.product.id) ?? { ...row.product, active: false } })), [products, cart]);
  const catalog = withoutPayments ? products.filter(product => product.active) : products;
  const categories = [...new Set(catalog.map(attendanceCategory))].filter(name => name !== "Outros" && name !== "Todos").sort(compareAttendanceCategories).concat("Todos");
  const activeCategory = categories.includes(category) ? category : categories[0] || "";
  const query = normalizeCatalogSearch(catalogSearch);
  const catalogVisible = !catalogCollapsed || !!query;
  const visibleProducts = withoutPayments ? catalog.filter(product => query ? normalizeCatalogSearch(product.name).includes(query) : activeCategory === "Todos" || attendanceCategory(product) === activeCategory)
    .sort((a, b) => compareAttendanceCategories(attendanceCategory(a), attendanceCategory(b)) || a.name.localeCompare(b.name, "pt-BR")) : products;
  const total = rows.reduce((sum, row) => sum + unitPrice(row.product, row.selection) * row.quantity, 0);
  function addDraftLine(product: Product, selection: Selection) {
    setCart(current => {
      const sameSelection = (a: Selection, b: Selection) => a.variant_id === b.variant_id && a.special_instructions === b.special_instructions && JSON.stringify([...a.modifier_option_ids].sort()) === JSON.stringify([...b.modifier_option_ids].sort());
      const index = withoutPayments ? current.findIndex(line => line.product.id === product.id && sameSelection(line.selection, selection)) : -1;
      return index < 0 ? [...current, { product, quantity: 1, selection }] : current.map((line, i) => i === index ? { ...line, quantity: Math.min(99, line.quantity + 1) } : line);
    });
  }
  const createTab = async () => { if (opening || cart.length || confirmIntentRef.current || correctionPending) return; setOpening(true); try { const r = await apiCall<Tab>(`${apiRoot}/tabs/`, { method: "POST", body: JSON.stringify({ display_label: label }) }); if (r.response.ok) { setSelected(r.body as Tab); setTabCollapsed(false); setCart([]); setLabel(""); await load(); } else setMessage(asApiError(r.body).message); } catch { setMessage("Não foi possível abrir a comanda. Atualize a lista antes de tentar novamente."); } finally { setOpening(false); } };
  const confirm = async () => {
    if (!selected || !rows.length || confirming || correctionPending) return;
    setConfirming(true); setSuccess("");
    const idempotencyKey = confirmIntentRef.current ?? crypto.randomUUID();
    confirmIntentRef.current = idempotencyKey;
    try {
      pendingPayload.current ??= { idempotency_key: idempotencyKey, lines: rows.map((row) => ({ product_id: row.product.id, quantity: row.quantity, ...row.selection })) };
      // Persist before sending: storage failure must never create an untracked POST.
      persistDraft();
      const r = await apiCall(`${apiRoot}/tabs/${selected.id}/orders/confirm/`, { method: "POST", body: JSON.stringify(pendingPayload.current) });
      if (r.response.ok) { setSuccess("Pedido confirmado."); setMessage(""); confirmIntentRef.current = null; pendingPayload.current = null; setCart([]); persistDraft(selected, []); await load(); const detail = await apiCall<Tab>(`${apiRoot}/tabs/${selected.id}/`); if (detail.response.ok) setSelected(detail.body as Tab); } else { setMessage(asApiError(r.body).message); if ([400, 404, 409, 422].includes(r.response.status)) { confirmIntentRef.current = null; pendingPayload.current = null; persistDraft(); await load(); } }
    } catch { setMessage("Não foi possível confirmar. Tente novamente para verificar este mesmo pedido."); }
    finally { setConfirming(false); }
  };
  const collect = async () => { if (!selected) return; if (!cashPointId) { setMessage("Abra ou selecione um caixa ativo antes de receber dinheiro."); return; } const amount = Math.round(Number(payment.replace(",", ".")) * 100); const r = await apiCall(`${apiRoot}/tabs/${selected.id}/payments/`, { method: "POST", body: JSON.stringify({ amount_cents: amount, expected_version: selected.version, method: "CASH", cash_point_id: cashPointId, idempotency_key: crypto.randomUUID() }) }); if (r.response.ok) { setPayment(""); const detail = await apiCall<Tab>(`${apiRoot}/tabs/${selected.id}/`); if (detail.response.ok) setSelected(detail.body as Tab); await load(); } else setMessage(asApiError(r.body).message); };
  const closeTabButton = <button className={withoutPayments ? "buttonSecondary attendanceCloseTab" : "buttonQuiet"} style={withoutPayments ? undefined : { width: "100%", marginTop: 8 }} disabled={correctionPending || confirming || !!confirmIntentRef.current || (withoutPayments && selected?.exposure_cents !== 0)} onClick={() => withoutPayments ? setClosingDialog(true) : void close()}>{withoutPayments && <OperationalIcon name="receipt" size={20} />}Fechar comanda</button>;
  const close = async () => { if (!selected || closing) return; setClosing(true); setMessage(""); try { const r = await apiCall(`${apiRoot}/tabs/${selected.id}/close/`, { method: "POST", body: "{}" }); if (r.response.ok) { setClosingDialog(false); setSuccess("Comanda encerrada."); setSelected(null); await load(); } else setMessage(asApiError(r.body).message); } catch { setMessage("Não foi possível confirmar o fechamento. Atualize a comanda antes de continuar."); } finally { setClosing(false); } };
  return <section className={withoutPayments ? "attendanceOrders" : "appShell"}><header className="productHeader"><div className="eyebrow">RODADA / ATENDIMENTO</div><OperationalHeading as="h1" icon="cart">Comandas e pedidos</OperationalHeading><p className="muted">Estado financeiro e operacional persistido.</p>{withoutPayments && !fresh && <p className="notice" data-state="warning">Atualizando ou dados desatualizados. Verifique a conexão.</p>}{!withoutPayments && <div className="actions"><Link className="backLink" href="/cash">Abrir caixa →</Link><Link className="backLink" href="/manage">Gestão →</Link><Link className="backLink" href="/refunds">Estornos →</Link></div>}</header>{success && <p className="notice" role="status" data-state="success">{success}</p>}{message && <div className="notice" role="alert" data-state="danger">{message}</div>}<section className="panel">{withoutPayments ? <div className="attendanceOpenHeading"><OperationalHeading as="h2" icon="cart">Abrir comanda</OperationalHeading><button className="buttonQuiet" aria-label="Histórico" title="Histórico de comandas" aria-haspopup="dialog" disabled={correctionPending || confirming || !!confirmIntentRef.current} onClick={() => setShowHistory(true)}><OperationalIcon name="history" size={20} /></button></div> : <OperationalHeading as="h2" icon="cart">Abrir comanda</OperationalHeading>}<div className="field"><input aria-label="Apelido da comanda (opcional)" value={label} onChange={(event) => setLabel(event.target.value)} placeholder="Apelido opcional" /></div><button className="buttonPrimary" disabled={correctionPending || opening || !fresh || confirming || !!confirmIntentRef.current} onClick={() => void createTab()}>Abrir</button></section><section className="panel"><OperationalHeading as="h2" icon="receipt">Comandas abertas</OperationalHeading>{!withoutPayments && <button className="buttonQuiet" aria-pressed={showHistory} onClick={() => setShowHistory(value => !value)}>{showHistory ? "Ocultar histórico de comandas encerradas" : "Ver histórico de comandas encerradas"}</button>}{withoutPayments && <div className="field"><label htmlFor="attendance-search">Buscar comanda</label><input id="attendance-search" value={search} onChange={e => setSearch(e.target.value)} /></div>}{tabs.filter(tab => ((!withoutPayments && showHistory) || !["CLOSED", "CANCELLED"].includes(tab.state)) && (!withoutPayments || tab.display_label.toLocaleLowerCase().includes(search.toLocaleLowerCase()))).map((tab) => <button className={withoutPayments && selected?.id === tab.id ? "buttonSecondary attendanceTabOption attendanceTabOptionActive" : "buttonSecondary attendanceTabOption"} key={tab.id} disabled={(cart.length > 0 && selected?.id !== tab.id) || correctionPending || confirming || !!confirmIntentRef.current} aria-expanded={withoutPayments ? selected?.id === tab.id && !tabCollapsed : undefined} aria-controls={withoutPayments && selected?.id === tab.id ? "attendance-selected-tab" : undefined} onClick={() => { if (withoutPayments && selected?.id === tab.id) { setTabCollapsed(value => !value); return; } void apiCall<Tab>(`${apiRoot}/tabs/${tab.id}/`).then(r => { if (r.response.ok) { setSelected(r.body as Tab); setTabCollapsed(false); setCart([]); setSuccess(""); } else setMessage(asApiError(r.body).message); }).catch(() => setMessage("Não foi possível abrir a comanda.")); }}>{tab.display_label || "Sem identificação"} · {money(tab.exposure_cents)}</button>)}</section>{withoutPayments && showHistory && <AttendanceTabHistory tabs={tabs.filter(tab => ["CLOSED", "CANCELLED"].includes(tab.state))} apiRoot={apiRoot} onClose={() => setShowHistory(false)} />}{destinationLabel && selected && selected.id === requestedTabId && <p className="notice" data-state="info">{destinationLabel} · {selected.display_label || "Comanda sem nome"}</p>}{selected && ["CLOSED", "CANCELLED"].includes(selected.state) && !!confirmIntentRef.current && <button className="buttonPrimary" disabled={confirming || correctionPending} onClick={() => void confirm()}>Verificar mesmo pedido</button>}{selected && <section className={withoutPayments ? "panel attendanceSelectedTab" : "panel"}>{withoutPayments ? <h2 className="attendanceTabTitle" aria-label={selected.display_label || "Comanda"}><button className="attendanceTabToggle" aria-expanded={!tabCollapsed} aria-controls="attendance-selected-tab" disabled={correctionPending || confirming || !!confirmIntentRef.current || closing} onClick={() => setTabCollapsed(value => !value)}><span className="attendanceTabCaption">Comanda selecionada</span><span>{selected.display_label || "Comanda"}</span><span className="attendanceTabHint">{tabCollapsed ? "Expandir ▾" : "Recolher ▴"}</span></button></h2> : <OperationalHeading as="h2" icon="cart">{selected.display_label || "Comanda"}</OperationalHeading>}<div id={withoutPayments ? "attendance-selected-tab" : undefined} hidden={withoutPayments && tabCollapsed}>{!withoutPayments && <BillSummary bill={selected} />}{withoutPayments && !["CLOSED", "CANCELLED"].includes(selected.state) && <AttendanceDraft rows={rows} locked={correctionPending || confirming || !!confirmIntentRef.current} fresh={fresh} onQuantity={(index, delta) => setCart(current => current.flatMap((line, i) => i !== index ? [line] : line.quantity + delta <= 0 ? [] : [{ ...line, quantity: Math.min(99, line.quantity + delta) }]))} onEdit={index => { setConfiguring(rows[index].product); setEditing(index); }}><button className="buttonPrimary" disabled={correctionPending || !rows.length || confirming || (!confirmIntentRef.current && (!fresh || rows.some(row => !row.product.active || row.product.availability !== "AVAILABLE" || !!selectionError(row.product, row.selection))))} onClick={() => void confirm()}>{confirming ? "Confirmando…" : confirmIntentRef.current ? "Verificar mesmo pedido" : `Confirmar pedido · ${money(total)}`}</button></AttendanceDraft>}{withoutPayments && <section><OperationalHeading as="h2" icon="cart">Pedidos confirmados</OperationalHeading>{selected.orders?.flatMap(order => order.items.filter(item => item.state !== "CANCELLED").map(item => <article className="attendanceConfirmedItem" key={item.id}>
  <div className="attendanceConfirmedDescription"><strong>{item.quantity}× {item.product_name}</strong><CustomizationText snapshot={item.customization_snapshot} />
    {["PREPARING", "READY", "PICKED_UP", "DELIVERED"].includes(item.state) && <small className="muted">Retirada exige revisão da gerência.</small>}
  </div>
  <div className="attendanceConfirmedActions"><span className="attendanceConfirmedStatus">{({ NEW: "Novo", ACCEPTED: "Aceito", PREPARING: "Em preparo", READY: "Pronto", PICKED_UP: "Retirado", DELIVERED: "Entregue", CANCELLED: "Cancelado" } as Record<string, string>)[item.state] || item.state}</span>
    {["NEW", "ACCEPTED"].includes(item.state) && !["CLOSED", "CANCELLED"].includes(selected.state) && <button className="buttonDanger attendanceRemoveItem" aria-label={`Remover ${item.quantity}× ${item.product_name}`} title={`Remover ${item.product_name}`} disabled={correctionPending || confirming || !!confirmIntentRef.current || !fresh} onClick={() => setRemovingItem(item)}><OperationalIcon name="trash" size={20} /></button>}
  </div>
</article>))}</section>}{withoutPayments && removingItem && <ConfirmedItemRemoval item={selected.orders?.flatMap(order => order.items).find(item => item.id === removingItem.id) ?? removingItem} onPendingChange={setCorrectionPending} onClose={() => setRemovingItem(null)} onRefresh={async () => { const detail = await apiCall<Tab>(`${apiRoot}/tabs/${selected.id}/`); if (!detail.response.ok) throw new Error("Falha ao atualizar comanda."); setSelected(detail.body as Tab); await load(); }} />}{!withoutPayments && <ReceiptPrinting key={selected.id} tabId={selected.id} closed={selected.state === "CLOSED"} />}{!["CLOSED", "CANCELLED"].includes(selected.state) && <>{!withoutPayments && <PricingAdjustments key={selected.id} tabId={selected.id} version={selected.version} onChanged={async () => { const detail = await apiCall<Tab>(`${apiRoot}/tabs/${selected.id}/`); if (detail.response.ok) setSelected(detail.body as Tab); await load(); }} />}<OperationalHeading as="h2" icon="cart" className="posSectionTitle">Catálogo</OperationalHeading>{withoutPayments && <>
{<div className="field"><label htmlFor="attendance-catalog-search">Buscar item no cardápio</label><input id="attendance-catalog-search" type="search" value={catalogSearch} onChange={event => setCatalogSearch(event.target.value)} placeholder="Nome da bebida ou comida" /></div>}
<nav className="actions attendanceCategories" aria-label="Categorias do cardápio">{categories.map(name => <button key={name} className={activeCategory === name && !catalogCollapsed && !query ? "buttonPrimary" : "buttonSecondary"} aria-pressed={activeCategory === name && !catalogCollapsed && !query} aria-expanded={activeCategory === name && !catalogCollapsed && !query} onClick={() => { setCatalogCollapsed(activeCategory === name && !query ? !catalogCollapsed : false); setCategory(name); setCatalogSearch(""); }}>{name} ({name === "Todos" ? catalog.length : catalog.filter(product => attendanceCategory(product) === name).length})</button>)}</nav>
{catalogVisible && <p role="status" className="muted">{query ? `Busca em todas as categorias · ${visibleProducts.length} itens` : `${activeCategory || "Cardápio"} · ${visibleProducts.length} itens`}</p>}
{catalogVisible && !visibleProducts.length && <p>Nenhum item encontrado.</p>}
</>}<div className="posProducts" hidden={withoutPayments && !catalogVisible}>{visibleProducts.map((product) => <button key={product.id} className="buttonSecondary posProduct" disabled={correctionPending || !fresh || !product.active || product.availability !== "AVAILABLE" || confirming || !!confirmIntentRef.current} onClick={() => { if (product.variants?.length || product.modifier_groups?.length) { setEditing(null); setConfiguring(product); } else addDraftLine(product, defaults(product)); }}><ProductIcon name={product.name} icon={product.icon} /><span><strong>{product.name}</strong><small>{money(product.price_cents)}{product.availability !== "AVAILABLE" ? " · Indisponível" : ""}</small></span></button>)}</div>{configuring && (withoutPayments ? <ActionDialog title={`Personalizar ${configuring.name}`} onClose={() => { setConfiguring(null); setEditing(null); }}><ProductCustomization key={`${configuring.id}-${editing}`} product={products.find(p => p.id === configuring.id) ?? configuring} initial={editing === null ? undefined : cart[editing]?.selection} onCancel={() => { setConfiguring(null); setEditing(null); }} onAdd={selection => { editing === null ? addDraftLine(configuring, selection) : setCart(c => c.map((r, i) => i === editing ? { ...r, selection } : r)); setConfiguring(null); setEditing(null); }} /></ActionDialog> : <ProductCustomization key={`${configuring.id}-${editing}`} product={products.find(p => p.id === configuring.id) ?? configuring} initial={editing === null ? undefined : cart[editing]?.selection} onCancel={() => { setConfiguring(null); setEditing(null); }} onAdd={selection => { editing === null ? addDraftLine(configuring, selection) : setCart(c => c.map((r, i) => i === editing ? { ...r, selection } : r)); setConfiguring(null); setEditing(null); }} />)}{!withoutPayments && <>{rows.map((row, index) => <div className={withoutPayments ? "dataRow attendanceCartRow" : "dataRow"} key={index}><div><strong>{row.quantity}× {row.product.name}</strong><CustomizationText snapshot={{ variant: row.product.variants?.find(v => v.id === row.selection.variant_id), modifiers: row.product.modifier_groups?.flatMap(g => g.options.filter(o => row.selection.modifier_option_ids.includes(o.id)).map(o => ({ ...o, group_name: g.name }))), special_instructions: row.selection.special_instructions }} />{selectionError(row.product, row.selection) && <p className="notice" data-state="danger">{selectionError(row.product, row.selection)}</p>}</div><div className="actions">{withoutPayments && <div className="field"><label htmlFor={`quantity-${index}`}>Quantidade de {row.product.name}</label><input id={`quantity-${index}`} type="number" min={1} max={99} value={row.quantity} disabled={correctionPending || confirming || !!confirmIntentRef.current} onChange={e => setCart(c => c.map((line, i) => i === index ? { ...line, quantity: Math.max(1, Math.min(99, Math.trunc(Number(e.target.value)) || 1)) } : line))} /></div>}<button className="buttonQuiet" disabled={correctionPending || confirming || !!confirmIntentRef.current} onClick={() => { setConfiguring(row.product); setEditing(index); }}>Editar</button><button className="buttonQuiet" disabled={correctionPending || confirming || !!confirmIntentRef.current} onClick={() => setCart(c => c.filter((_, i) => i !== index))}>Remover</button></div></div>)}<button className="buttonPrimary" disabled={correctionPending || !rows.length || confirming || (!confirmIntentRef.current && (!fresh || rows.some(row => !row.product.active || row.product.availability !== "AVAILABLE" || !!selectionError(row.product, row.selection))))} onClick={() => void confirm()}>{confirming ? "Confirmando…" : confirmIntentRef.current ? "Verificar mesmo pedido" : `Confirmar pedido · ${money(total)}`}</button></>}{!withoutPayments && <><OperationalHeading as="h2" icon="wallet" style={{ marginTop: 22 }}>Receber em dinheiro</OperationalHeading><div className="field"><select aria-label="Caixa aberto" value={cashPointId} onChange={(event) => setCashPointId(event.target.value)}><option value="">Selecionar caixa aberto</option>{cashPoints.map((point) => <option key={point.id} value={point.id}>{point.label}</option>)}</select></div><div className="field"><input aria-label="Valor do pagamento" inputMode="decimal" value={payment} onChange={(event) => setPayment(event.target.value)} placeholder="Valor" /></div><button className="buttonPrimary" onClick={() => void collect()}>Receber em dinheiro</button></>}{!withoutPayments && closeTabButton}</>}{withoutPayments && closingDialog && <ActionDialog title="Fechar comanda?" locked={closing} onClose={() => setClosingDialog(false)}><p>Confirme o encerramento de {selected.display_label || "esta comanda"}.</p>{message && <p className="notice" role="alert" data-state="danger">{message}</p>}<button className="buttonSecondary" disabled={closing || selected.exposure_cents !== 0} onClick={() => void close()}>{closing ? "Verificando…" : "Confirmar fechamento"}</button></ActionDialog>}{withoutPayments && <section aria-label="Valores da comanda"><OperationalHeading as="h2" icon="receipt">Resumo da comanda</OperationalHeading><BillSummary key={selected.id} bill={selected} compact /></section>}{withoutPayments && closeTabButton}</div></section>}</section>;
}
