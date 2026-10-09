"use client";

import { OperationalHeading } from "@/components/operational-heading";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiCall, asApiError } from "@/lib/client/staff-auth";

type Calendar = { timezone: string; cutoff_hour: number; business_date: string };
type Daily = { date: string; gross_cents: number; adjustments_cents: number; net_sales_cents: number; paid_cents: number; refunds_cents: number; net_received_cents: number };
type Report = {
  generated_at: string; start: string; end: string; timezone: string; cutoff_hour: number;
  totals: Record<string, number>; daily: Daily[];
  products: { order_item__product_id: string; order_item__product_name_snapshot: string; quantity: number; gross_cents: number }[];
  payment_methods: { method: string; amount_cents: number; count: number }[];
  orders: { source: string; status: string; count: number }[];
  cash_shifts: { id: string; business_date: string; cash_point_label: string; status: string; expected_at_close_cents?: number; corrected_expected_cents?: number; counted_amount_cents?: number | null; discrepancy_cents?: number | null; review_status: string }[];
};
const money = (cents: number | null | undefined) => cents == null ? "—" : new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(cents / 100);
const totalLabels: Record<string, string> = { item_discounts_cents: "Descontos por item", tab_discounts_cents: "Descontos por comanda", courtesy_cents: "Cortesias", service_assessed_cents: "Serviço calculado", service_reductions_cents: "Serviço removido", service_revenue_cents: "Serviço como receita", service_pass_through_cents: "Serviço a repassar", net_consumption_cents: "Consumo líquido", payable_cents: "Total devido", corrections_cents: "Correções", gross_cents: "Vendas brutas", adjustments_cents: "Ajustes", net_sales_cents: "Vendas líquidas", paid_cents: "Recebimentos confirmados", refunds_cents: "Estornos confirmados", net_received_cents: "Recebimento líquido", current_open_exposure_cents: "Exposição em aberto agora", current_open_tabs: "Comandas abertas agora" };
const methodLabels: Record<string, string> = { CASH: "Dinheiro", EXTERNAL_TERMINAL: "Maquininha externa", TAP_TO_PAY: "Tap to Pay", CARD_ONLINE: "Cartão online", CARD: "Cartão", PIX: "Pix", OTHER: "Outro" };

function reportCsv(report: Report): string {
  const cell = (value: unknown) => {
    let text = value == null ? "" : String(value);
    if (typeof value === "string" && /^[\s]*[=+\-@\t\r]/.test(text)) text = "'" + text;
    return '"' + text.replace(/"/g, '""') + '"';
  };
  const rows: unknown[][] = [["Rodada — valores monetários em centavos", report.start, report.end, report.timezone, report.cutoff_hour, report.generated_at], ["Resumo", "Métrica", "Valor"]];
  Object.entries(report.totals).forEach(([key, value]) => rows.push(["Resumo", totalLabels[key] ?? key, value]));
  rows.push(["Diário", "Data", "Bruto", "Ajustes", "Líquido", "Recebido", "Estornos", "Recebimento líquido"]);
  report.daily.forEach(row => rows.push(["Diário", row.date, row.gross_cents, row.adjustments_cents, row.net_sales_cents, row.paid_cents, row.refunds_cents, row.net_received_cents]));
  rows.push(["Produtos", "ID", "Nome histórico", "Quantidade", "Bruto"]);
  report.products.forEach(row => rows.push(["Produtos", row.order_item__product_id, row.order_item__product_name_snapshot, row.quantity, row.gross_cents]));
  rows.push(["Pagamentos", "Método", "Quantidade", "Confirmado"]);
  report.payment_methods.forEach(row => rows.push(["Pagamentos", row.method, row.count, row.amount_cents]));
  rows.push(["Pedidos", "Origem", "Estado", "Quantidade"]);
  report.orders.forEach(row => rows.push(["Pedidos", row.source, row.status, row.count]));
  rows.push(["Caixa", "ID", "Data operacional", "Ponto", "Estado", "Esperado original", "Esperado corrigido", "Contado", "Diferença", "Revisão"]);
  report.cash_shifts.forEach(row => rows.push(["Caixa", row.id, row.business_date, row.cash_point_label, row.status, row.expected_at_close_cents, row.corrected_expected_cents, row.counted_amount_cents, row.discrepancy_cents, row.review_status]));
  return "\uFEFF" + rows.map(row => row.map(cell).join(";")).join("\r\n");
}

export default function ReportsPage() {
  const [calendar, setCalendar] = useState<Calendar | null>(null), [start, setStart] = useState(""), [end, setEnd] = useState("");
  const [zone, setZone] = useState(""), [cutoff, setCutoff] = useState("0");
  const [report, setReport] = useState<Report | null>(null), [loading, setLoading] = useState(true), [error, setError] = useState(""), [notice, setNotice] = useState("");
  async function load(from: string, to: string) {
    setLoading(true); setError("");
    try {
      const r = await apiCall<Report>(`/api/pos/management/reports/?start=${encodeURIComponent(from)}&end=${encodeURIComponent(to)}`);
      if (!r.response.ok) { setError(asApiError(r.body).message); return; }
      setReport(r.body as Report);
    } catch { setError("Não foi possível carregar os relatórios. Confira a conexão."); }
    finally { setLoading(false); }
  }
  useEffect(() => { void (async () => {
    try {
      const r = await apiCall<Calendar>("/api/pos/management/calendar/");
      if (!r.response.ok) { setError(asApiError(r.body).message); setLoading(false); return; }
      const c = r.body as Calendar; setCalendar(c); setZone(c.timezone); setCutoff(String(c.cutoff_hour)); setStart(c.business_date); setEnd(c.business_date);
      await load(c.business_date, c.business_date);
    } catch { setError("Não foi possível ler o calendário operacional."); setLoading(false); }
  })(); }, []);
  function download() {
    if (!report || error || loading) return;
    const url = URL.createObjectURL(new Blob([reportCsv(report)], { type: "text/csv;charset=utf-8" }));
    const anchor = document.createElement("a"); anchor.href = url; anchor.download = `rodada-${report.start}-${report.end}.csv`; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  async function saveCalendar() {
    setLoading(true); setError(""); setNotice("");
    try {
      const r = await apiCall<Calendar>("/api/pos/management/calendar/", { method: "PATCH", body: JSON.stringify({ timezone: zone, cutoff_hour: Number(cutoff) }) });
      if (!r.response.ok) { setError(asApiError(r.body).message); return; }
      setCalendar(r.body as Calendar); setNotice("Calendário salvo. Relatórios são recalculados com o novo corte; datas gravadas nos turnos antigos são preservadas.");
      await load(start, end);
    } catch { setError("Não foi possível salvar o calendário."); }
    finally { setLoading(false); }
  }
  return <main className="appShell">
    <header className="productHeader"><div className="eyebrow">RODADA / GERÊNCIA</div><OperationalHeading as="h1" icon="sales">Relatórios operacionais</OperationalHeading><Link className="backLink" href="/manage">← Voltar à gerência</Link></header>
    {error && <div className="notice" data-state="danger" role="alert">{error}{report && " Último resultado confirmado; atualize antes de usar."}</div>}
    {notice && <p role="status">{notice}</p>}
    {loading && <p className="loadingState" role="status">Carregando relatórios…</p>}
    {calendar && <section className="panel"><OperationalHeading as="h2" icon="sales">Período operacional</OperationalHeading><p className="muted">{calendar.timezone} · corte às {calendar.cutoff_hour}h · até 366 dias</p>
      <form onSubmit={e => { e.preventDefault(); void load(start, end); }}><div className="field"><label htmlFor="report-start">De</label><input id="report-start" type="date" required value={start} onChange={e => setStart(e.target.value)} /></div><div className="field"><label htmlFor="report-end">Até</label><input id="report-end" type="date" required value={end} onChange={e => setEnd(e.target.value)} /></div><div className="actions"><button className="buttonPrimary" disabled={loading}>Aplicar período</button><button type="button" className="buttonSecondary" disabled={loading || !!error || !report} onClick={download}>Exportar CSV</button></div></form>
    </section>}
    {report && <><section className="panel"><OperationalHeading as="h2" icon="sales">Resumo financeiro</OperationalHeading><p className="muted">{report.start} a {report.end} · gerado em {new Date(report.generated_at).toLocaleString("pt-BR")}</p><div className="metricGrid">{Object.entries(report.totals).map(([key, value]) => <div className="operationalMetric" key={key}><span>{totalLabels[key] ?? key}</span><strong>{key.endsWith("_cents") ? money(value) : value}</strong></div>)}</div><p className="muted">Vendas e recebimentos são fatos diferentes. Exposição/comandas são o estado atual, não o saldo histórico do período. Pagamentos pendentes não entram no recebido.</p></section>
      <section className="panel"><OperationalHeading as="h2" icon="sales">Por dia operacional</OperationalHeading>{report.daily.map(row => <div className="reportGroup" key={row.date}><h3>{row.date}</h3><div className="dataRow"><span>Vendas líquidas</span><strong>{money(row.net_sales_cents)}</strong></div><div className="dataRow"><span>Recebimento líquido</span><strong>{money(row.net_received_cents)}</strong></div><div className="dataRow"><span>Ajustes / estornos</span><strong>{money(row.adjustments_cents)} / {money(row.refunds_cents)}</strong></div></div>)}</section>
      <section className="panel"><OperationalHeading as="h2" icon="cart">Produtos vendidos</OperationalHeading><p className="muted">Nomes e preços históricos; bruto antes de cancelamentos e ajustes.</p>{!report.products.length && <p>Nenhuma venda no período.</p>}{report.products.map((row, i) => <div className="dataRow" key={i}><span>{row.quantity}× {row.order_item__product_name_snapshot}</span><strong>{money(row.gross_cents)}</strong></div>)}</section>
      <section className="panel"><OperationalHeading as="h2" icon="wallet">Métodos de pagamento</OperationalHeading>{!report.payment_methods.length && <p>Nenhum pagamento confirmado no período.</p>}{report.payment_methods.map(row => <div className="dataRow" key={row.method}><span>{methodLabels[row.method] ?? row.method} · {row.count}</span><strong>{money(row.amount_cents)}</strong></div>)}</section>
      <section className="panel"><OperationalHeading as="h2" icon="cart">Origem e estado dos pedidos</OperationalHeading>{!report.orders.length && <p>Nenhum pedido no período.</p>}{report.orders.map(row => <div className="dataRow" key={row.source + row.status}><span>{row.source === "GUEST" ? "Cliente" : row.source === "CASHIER" ? "Caixa" : "Equipe"} · {row.status === "CONFIRMED" ? "Confirmado" : "Cancelado"}</span><strong>{row.count}</strong></div>)}</section>
      <section className="panel"><OperationalHeading as="h2" icon="wallet">Fechamentos de caixa</OperationalHeading>{!report.cash_shifts.length && <p>Nenhum turno no período.</p>}{report.cash_shifts.map(row => <div className="reportGroup" key={row.id}><h3>{row.cash_point_label} · {row.business_date}</h3><p>{row.status === "CLOSED" ? "Fechado" : row.status === "OPEN" ? "Aberto" : "Em conferência"} · {row.review_status === "PENDING" ? "Revisão pendente" : row.review_status === "REVIEWED" ? "Revisado" : "Sem revisão pendente"}</p><div className="dataRow"><span>Esperado original / corrigido</span><strong>{money(row.expected_at_close_cents)} / {money(row.corrected_expected_cents)}</strong></div><div className="dataRow"><span>Contado / diferença</span><strong>{money(row.counted_amount_cents)} / {money(row.discrepancy_cents)}</strong></div><Link className="backLink" href="/cash">Abrir histórico do caixa →</Link></div>)}</section>
    </>}
    {calendar && <details className="panel"><summary>Configurar dia operacional</summary><p className="muted">A alteração recalcula a classificação temporal dos relatórios; não modifica lançamentos ou datas de turnos já gravados. Exige permissão de configuração.</p><div className="field"><label htmlFor="report-zone">Fuso horário IANA</label><input id="report-zone" value={zone} onChange={e => setZone(e.target.value)} /></div><div className="field"><label htmlFor="report-cutoff">Hora de corte (0 a 23)</label><input id="report-cutoff" type="number" min="0" max="23" value={cutoff} onChange={e => setCutoff(e.target.value)} /></div><button className="buttonSecondary" disabled={loading || cutoff === ""} onClick={() => void saveCalendar()}>Salvar calendário</button></details>}
  </main>;
}
