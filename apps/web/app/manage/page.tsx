"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ManagementNav } from "@/components/management-nav";
import { HouseAccount } from "@/components/house-account";
import { apiCall, asApiError } from "@/lib/client/staff-auth";

type Tab = { id: string; display_label: string; state: string; exposure_cents: number };
type TabDetail = Tab & {
  refund_required_corrections?: { id: string; item_name: string; refund_required_cents: number }[];
  payments?: { status: string }[];
};
type Product = { id: string; name: string; availability: string; active: boolean };
type QueueItem = { id: string; product_name: string; state: string; tab_label: string };
type Delivery = { id: string; product_name: string; destination_label: string; age_seconds: number };
type CashPoint = { id: string; label: string; active_shift: { id: string; status: string; expected_cents?: number } | null; pending_review_shift?: { id: string; discrepancy_cents: number } | null };
type Table = { id: string; label: string; status: string; active_occupancy: { id: string } | null };

const money = (value = 0) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value / 100);

async function getResults<T>(path: string): Promise<T[]> {
  const result = await apiCall<{ results: T[] }>(path);
  if (!result.response.ok) throw new Error(asApiError(result.body).message);
  return (result.body as { results: T[] }).results;
}

export default function ManagementPage() {
  const [tabs, setTabs] = useState<Tab[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [bar, setBar] = useState<QueueItem[]>([]);
  const [kitchen, setKitchen] = useState<QueueItem[]>([]);
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [cashPoints, setCashPoints] = useState<CashPoint[]>([]);
  const [tables, setTables] = useState<Table[]>([]);
  const [refunds, setRefunds] = useState<{ tab: string; item: string; cents: number }[]>([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [hasSnapshot, setHasSnapshot] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setMessage("");
    try {
      const [nextTabs, nextProducts, nextBar, nextKitchen, nextDeliveries, nextCash, nextTables] = await Promise.all([
        getResults<Tab>("/api/pos/tabs/"),
        getResults<Product>("/api/pos/catalog/products/"),
        getResults<QueueItem>("/api/pos/production/BAR/"),
        getResults<QueueItem>("/api/pos/production/KITCHEN/"),
        getResults<Delivery>("/api/pos/dispatch/delivery/"),
        getResults<CashPoint>("/api/pos/cash/points/"),
        getResults<Table>("/api/pos/hospitality/tables/"),
      ]);
      const openTabs = nextTabs.filter((tab) => tab.state !== "CLOSED");
      const details = await Promise.all(openTabs.map(async (tab) => {
        const result = await apiCall<TabDetail>(`/api/pos/tabs/${tab.id}/`);
        if (!result.response.ok) throw new Error(asApiError(result.body).message);
        return result.body as TabDetail;
      }));
      setTabs(nextTabs); setProducts(nextProducts); setBar(nextBar); setKitchen(nextKitchen);
      setDeliveries(nextDeliveries); setCashPoints(nextCash); setTables(nextTables);
      setHasSnapshot(true);
      setRefunds(details.flatMap((detail) => {
        if (!detail) return [];
        return (detail.refund_required_corrections ?? []).map((row) => ({
          tab: detail.display_label || "Comanda sem nome", item: row.item_name, cents: row.refund_required_cents,
        }));
      }));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Não foi possível atualizar o painel.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);
  const openTabs = useMemo(() => tabs.filter((tab) => tab.state !== "CLOSED"), [tabs]);
  const exposure = useMemo(() => openTabs.reduce((total, tab) => total + tab.exposure_cents, 0), [openTabs]);
  const unavailable = useMemo(() => products.filter((product) => product.active && product.availability !== "AVAILABLE"), [products]);
  const activeCash = cashPoints.filter((point) => point.active_shift);
  const activeTables = tables.filter((table) => table.status === "OCCUPIED");
  const pendingCash = cashPoints.filter(point => point.pending_review_shift);
  const attentionTabs = openTabs.filter(tab => tab.state === "REQUIRES_ACTION");

  return <main className="appShell managementShell">
    <header className="productHeader">
      <div className="eyebrow">RODADA / GESTÃO</div>
      <h1>O que precisa de atenção</h1>
      <p className="muted">Visão operacional atual, sem números de vaidade.</p>
      <div className="actions"><button className="buttonQuiet" onClick={() => void load()} disabled={loading}>{loading ? "Atualizando…" : "Atualizar"}</button></div>
    </header>
    <ManagementNav />
    {message ? <div className="notice" data-state="danger" role="alert">{message}{hasSnapshot ? " Último estado confirmado; atualize para conferir a operação." : ""}</div> : null}
    {loading && <div className="loadingState" role="status">Atualizando operação…</div>}
    {hasSnapshot && <>
    {pendingCash.length > 0 && <section className="panel panelDanger" aria-labelledby="cash-review-title">
      <h2 id="cash-review-title">Divergências de caixa pendentes</h2>
      {pendingCash.map(point => <div className="movement" key={point.id}><div><strong>{point.label}</strong><small>Fechamento aguardando revisão</small></div><strong className="cashDifference">{money(point.pending_review_shift?.discrepancy_cents)}</strong></div>)}
      <Link className="backLink" href="/cash">Revisar caixa →</Link>
    </section>}
    {refunds.length ? <section className="panel panelDanger"><h2>Estornos pendentes</h2>{refunds.map((refund, index) => <div className="movement" key={`${refund.tab}-${refund.item}-${index}`}><div><strong>{refund.tab}</strong><small>{refund.item}</small></div><strong className="cashDifference">{money(refund.cents)}</strong></div>)}<Link className="backLink" href="/refunds">Resolver estornos →</Link></section> : null}

    {attentionTabs.length > 0 && <section className="panel panelWarning" aria-labelledby="tab-attention-title">
      <h2 id="tab-attention-title">Comandas precisam de atenção</h2>
      {attentionTabs.map(tab => <div className="movement" key={tab.id}><div><strong>{tab.display_label || "Comanda sem nome"}</strong><small>Ação da equipe necessária · em aberto</small></div><strong>{money(tab.exposure_cents)}</strong></div>)}
      <Link className="backLink" href="/manage#gestao">Ver comandas em Gestão →</Link>
    </section>}
    <section className="panel"><h2>Agora</h2>
      <div className="metricGrid">
        <div className="operationalMetric"><span>Comandas abertas</span><strong>{openTabs.length}</strong></div>
        <div className="operationalMetric"><span>Exposição em aberto</span><strong>{money(exposure)}</strong></div>
        <div className="operationalMetric"><span>Estornos aguardando decisão</span><strong className={refunds.length ? "cashDifference" : ""}>{refunds.length}</strong></div>
        <div className="operationalMetric"><span>Itens indisponíveis</span><strong>{unavailable.length}</strong></div>
      </div>
    </section>

    <section className="panel" id="operacao"><h2>Produção e entrega</h2>
      <div className="dataRow"><span>Bar em preparo</span><strong>{bar.filter(item => item.state !== "READY").length}</strong></div>
      <div className="dataRow"><span>Cozinha em preparo</span><strong>{kitchen.filter(item => item.state !== "READY").length}</strong></div>
      <div className="dataRow"><span>Prontos para entrega</span><strong className={deliveries.length ? "cashDifference" : ""}>{deliveries.length}</strong></div>
      {deliveries.slice(0, 5).map((task) => <div className="movement" key={task.id}><div><strong>{task.destination_label || "Sem destino"}</strong><small>{task.product_name}</small></div><strong>{task.age_seconds < 60 ? "agora" : `${Math.floor(task.age_seconds / 60)} min`}</strong></div>)}
      <div className="actions"><Link className="backLink" href="/bar">Abrir Bar</Link><Link className="backLink" href="/kitchen">Abrir Cozinha</Link></div>
    </section>

    <div id="gestao">
    <section className="panel"><h2>Caixa e salão</h2>
      {!activeCash.length ? <p className="muted">Nenhum caixa com turno ativo.</p> : activeCash.map((point) => <div className="dataRow" key={point.id}><span>{point.label} · {point.active_shift?.status === "OPEN" ? "Aberto" : point.active_shift?.status === "COUNTING" ? "Em contagem" : "Fechado"}</span><strong>{point.active_shift?.expected_cents === undefined ? "Ver caixa" : money(point.active_shift.expected_cents)}</strong></div>)}
      <div className="dataRow"><span>Mesas ocupadas</span><strong>{activeTables.length}</strong></div>
      <div className="dataRow"><span>Mesas em limpeza</span><strong>{tables.filter((table) => table.status === "CLEANING").length}</strong></div>
      <div className="actions"><Link className="backLink" href="/cash">Abrir caixa</Link><Link className="backLink" href="/refunds">Estornos</Link></div>
    </section>

    <HouseAccount />
    </div>
    <section className="panel" id="vendas"><h2>Vendas e relatórios</h2><p className="muted">Vendas, recebimentos, produtos, estornos e caixa por período operacional.</p><Link className="backLink" href="/reports">Abrir relatórios →</Link></section>
    {unavailable.length ? <section className="panel"><h2>Indisponíveis</h2>{unavailable.map((product) => <div className="movement" key={product.id}><strong>{product.name}</strong><strong className="cashDifference">Indisponível</strong></div>)}</section> : null}
    <section className="panel" id="mais"><h2>Mais</h2><p className="muted">Consulte o cardápio nas estações e os relatórios em Vendas. Para trocar de operador ou encerrar a sessão, abra Atendimento.</p><Link className="backLink" href="/staff">Abrir sessão de atendimento →</Link></section>
    </>}
  </main>;
}
