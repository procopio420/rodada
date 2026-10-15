"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { OperationalHeading } from "@/components/operational-heading";
import { apiCall, asApiError } from "@/lib/client/staff-auth";

type Calendar = { timezone: string; cutoff_hour: number; business_date: string };
type Timing = { eligible: number; observed: number; missing: number; invalid: number; mean_seconds: number | null };
type Orders = { guest: number; staff: number; cancelled: number; unknown_source: number; denominator: number; guest_percent: number | null };
type Metrics = {
  started: number; released: number; ready: number;
  timings: Record<"occupancy" | "wait_to_clean" | "cleaning" | "release_to_ready", Timing>;
  orders: Orders;
};
type TableMetrics = Metrics & { table_id: string; label: string };
type DayMetrics = Metrics & { date: string };
type Report = {
  start: string; end: string; timezone: string; cutoff_hour: number; generated_at: string;
  definitions: Record<string, string>; summary: Metrics; daily: DayMetrics[]; tables: TableMetrics[];
};

const timeLabel = (seconds: number | null): string => {
  if (seconds === null) return "Sem amostras";
  if (seconds < 60) return `${seconds} s`;
  return `${Math.floor(seconds / 60)} min ${String(seconds % 60).padStart(2, "0")} s`;
};
const timingLabels: { key: keyof Metrics["timings"]; label: string }[] = [
  { key: "occupancy", label: "Tempo de ocupação" },
  { key: "wait_to_clean", label: "Saída → início da limpeza" },
  { key: "cleaning", label: "Tempo de limpeza" },
  { key: "release_to_ready", label: "Saída → disponível" },
];

export default function TableTurnoverPage() {
  const [calendar, setCalendar] = useState<Calendar | null>(null);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load(from: string, to: string) {
    setLoading(true);
    setError("");
    try {
      const r = await apiCall<Report>(
        `/api/pos/management/table-turnover/?start=${encodeURIComponent(from)}&end=${encodeURIComponent(to)}`
      );
      if (!r.response.ok) {
        setError(asApiError(r.body).message);
        return;
      }
      setReport(r.body as Report);
    } catch {
      setError("Não foi possível ler o giro de mesas. Confira a conexão.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void (async () => {
      try {
        const r = await apiCall<Calendar>("/api/pos/management/calendar/");
        if (!r.response.ok) {
          setError(asApiError(r.body).message);
          setLoading(false);
          return;
        }
        const next = r.body as Calendar;
        setCalendar(next);
        setStart(next.business_date);
        setEnd(next.business_date);
        await load(next.business_date, next.business_date);
      } catch {
        setError("Não foi possível ler o calendário operacional.");
        setLoading(false);
      }
    })();
  }, []);

  return <main className="appShell">
    <header className="productHeader">
      <div className="eyebrow">RODADA / GERÊNCIA</div>
      <OperationalHeading as="h1" icon="table">Giro e limpeza das mesas</OperationalHeading>
      <p className="muted">Medição direta do ciclo da mesa. Sem estimar presença, limpeza ou disponibilidade que não foi registrada.</p>
      <Link className="backLink" href="/manage#vendas">← Voltar à gerência</Link>
    </header>
    {error && <div className="notice" data-state="danger" role="alert">{error}{report && " Dados anteriores exibidos; atualize antes de tomar decisões."}</div>}
    {loading && <p className="loadingState" role="status">Atualizando métricas…</p>}
    {calendar && <section className="panel">
      <OperationalHeading as="h2" icon="table">Período operacional</OperationalHeading>
      <p className="muted">{calendar.timezone} · corte às {calendar.cutoff_hour}h · até 366 dias</p>
      <form onSubmit={event => { event.preventDefault(); void load(start, end); }}>
        <div className="field"><label htmlFor="turnover-start">De</label><input id="turnover-start" type="date" required value={start} onChange={event => setStart(event.target.value)} /></div>
        <div className="field"><label htmlFor="turnover-end">Até</label><input id="turnover-end" type="date" required value={end} onChange={event => setEnd(event.target.value)} /></div>
        <div className="actions"><button className="buttonPrimary" disabled={loading}>Aplicar período</button></div>
      </form>
    </section>}
    {report && <>
      <section className="panel">
        <OperationalHeading as="h2" icon="table">Movimento registrado</OperationalHeading>
        <p className="muted">{report.start} a {report.end} · dados consultados em {new Date(report.generated_at).toLocaleString("pt-BR")}</p>
        <div className="metricGrid">
          <div className="operationalMetric"><span>Ocupações iniciadas</span><strong>{report.summary.started}</strong></div>
          <div className="operationalMetric"><span>Mesas liberadas (giros)</span><strong>{report.summary.released}</strong></div>
          <div className="operationalMetric"><span>Mesas disponibilizadas</span><strong>{report.summary.ready}</strong></div>
        </div>
        <p className="muted">Inícios, liberações e disponibilizações usam cada um a data de seu próprio evento. Não representam a mesma coorte de mesas.</p>
      </section>
      <section className="panel">
        <OperationalHeading as="h2" icon="now">Duração observada</OperationalHeading>
        {timingLabels.map(({ key, label }) => {
          const metric = report.summary.timings[key];
          return <div className="reportGroup" key={key}>
            <div className="dataRow"><span>{label}</span><strong>{timeLabel(metric.mean_seconds)}</strong></div>
            <p className="muted">{metric.observed} de {metric.eligible} liberações com medição válida · {metric.missing} sem dados · {metric.invalid} inconsistentes</p>
          </div>;
        })}
        <p className="muted">A média exclui eventos incompletos ou com ordem de timestamps inválida. Durações são agrupadas pela data operacional da liberação, mesmo que a limpeza tenha terminado depois.</p>
      </section>
      <section className="panel">
        <OperationalHeading as="h2" icon="cart">Pedidos por origem</OperationalHeading>
        <div className="metricGrid">
          <div className="operationalMetric"><span>Guest</span><strong>{report.summary.orders.guest}</strong></div>
          <div className="operationalMetric"><span>Equipe (inclui caixa)</span><strong>{report.summary.orders.staff}</strong></div>
          <div className="operationalMetric"><span>Participação Guest</span><strong>{report.summary.orders.guest_percent === null ? "Sem dados" : `${report.summary.orders.guest_percent}%`}</strong></div>
        </div>
        <p className="muted">Denominador: {report.summary.orders.denominator} pedidos confirmados Guest + Equipe. {report.summary.orders.cancelled} cancelados e {report.summary.orders.unknown_source} de origem desconhecida não entram no percentual.</p>
      </section>
      <section className="panel">
        <OperationalHeading as="h2" icon="table">Giro por mesa</OperationalHeading>
        <p className="muted">Rótulos atuais. Uma liberação é um giro observado, não um giro por hora.</p>
        {!report.tables.length && <p>Nenhuma mesa cadastrada neste estabelecimento.</p>}
        {report.tables.map(table => <div className="dataRow" key={table.table_id}>
          <span>{table.label}</span>
          <strong>{table.released} {table.released === 1 ? "liberação" : "liberações"}</strong>
        </div>)}
      </section>
      <details className="panel">
        <summary>Detalhamento por dia operacional</summary>
        {report.daily.map(day => <div className="reportGroup" key={day.date}>
          <h3>{day.date}</h3>
          <div className="dataRow"><span>Inícios / liberações / disponíveis</span><strong>{day.started} / {day.released} / {day.ready}</strong></div>
          <div className="dataRow"><span>Guest / Equipe</span><strong>{day.orders.guest} / {day.orders.staff}</strong></div>
        </div>)}
      </details>
      <details className="panel">
        <summary>Como calculamos</summary>
        {Object.entries(report.definitions).map(([key, definition]) => <p className="muted" key={key}>{definition}</p>)}
      </details>
    </>}
  </main>;
}
