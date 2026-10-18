"use client";

import { useEffect, useRef, useState } from "react";
import { ActionDialog } from "@/components/action-dialog";
import { type Bill } from "@/components/bill-summary";
import { OperationalIcon } from "@/components/operational-icon";
import { apiCall, asApiError } from "@/lib/client/staff-auth";
import { tabPrimaryLabel, tabSecondaryLabel } from "@/lib/client/tab-identity";

type HistoryTab = Bill & {
  id: string; display_label: string; state: string; table_label?: string | null; last_table_label?: string | null; transfers_cents?: number;
  orders?: { id: string; items: { id: string; product_name: string; quantity: number; line_total_cents: number; state: string }[] }[];
  payments?: { id: string; method: string; status: string; amount_cents: number; simulated?: boolean }[];
};
type HistoryPage = { results: HistoryTab[]; next_offset: number | null; history_business_date: string };
const money = (cents: number) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(cents / 100);
const paymentMethods: Record<string, string> = { CASH: "Dinheiro", PIX: "Pix", CARD: "Cartão", EXTERNAL_TERMINAL: "Cartão", TAP_TO_PAY: "Aproximação", CARD_ONLINE: "Cartão online", OTHER: "Outro meio" };
const paymentStates: Record<string, string> = { CONFIRMED: "Confirmado", REFUNDED: "Estornado", PARTIALLY_REFUNDED: "Estornado parcialmente", FAILED: "Falhou", CANCELLED: "Cancelado", EXPIRED: "Expirado" };

export function ManagementTabHistory() {
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState<HistoryTab[]>([]);
  const [day, setDay] = useState("");
  const [search, setSearch] = useState("");
  const [loaded, setLoaded] = useState({ day: "current", search: "", offset: 0 });
  const [nextOffset, setNextOffset] = useState<number | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<HistoryTab | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const panel = useRef<HTMLDivElement>(null);
  const controller = useRef<AbortController | null>(null);
  const generation = useRef(0);
  useEffect(() => () => { generation.current++; controller.current?.abort(); }, []);
  useEffect(() => { if (open) panel.current?.focus(); }, [open, selected]);

  function beginRead() {
    controller.current?.abort();
    controller.current = new AbortController();
    const id = ++generation.current;
    setLoading(true); setError("");
    return { id, signal: controller.current.signal };
  }
  function invalidate() { generation.current++; controller.current?.abort(); setLoading(false); setError(""); }
  async function loadList(query: typeof loaded) {
    const { id, signal } = beginRead();
    setSelected(null); setDetail(null); setRows([]); setNextOffset(null);
    setLoaded(query);
    try {
      const params = new URLSearchParams({ history_day: query.day, offset: String(query.offset), q: query.search });
      const result = await apiCall<HistoryPage>(`/api/pos/tabs/?${params}`, { signal });
      if (id !== generation.current) return;
      if (!result.response.ok) throw new Error(asApiError(result.body).message);
      const page = result.body as HistoryPage;
      setRows(page.results); setNextOffset(page.next_offset);
      setDay(page.history_business_date); setLoaded({ ...query, day: page.history_business_date });
    } catch (failure) {
      if (id === generation.current) setError(failure instanceof Error ? failure.message : "Não foi possível carregar o histórico.");
    } finally { if (id === generation.current) setLoading(false); }
  }
  async function inspect(tabId: string) {
    const { id, signal } = beginRead();
    setSelected(tabId); setDetail(null);
    try {
      const result = await apiCall<HistoryTab>(`/api/pos/tabs/${encodeURIComponent(tabId)}/`, { signal });
      if (id !== generation.current) return;
      if (!result.response.ok) {
        if ([401, 403].includes(result.response.status)) { setRows([]); setNextOffset(null); setSelected(null); }
        throw new Error(asApiError(result.body).message);
      }
      setDetail(result.body as HistoryTab);
    } catch (failure) {
      if (id === generation.current) setError(failure instanceof Error ? failure.message : "Não foi possível consultar a comanda.");
    } finally { if (id === generation.current) setLoading(false); }
  }
  function back() {
    invalidate();
    if (selected) { setSelected(null); setDetail(null); }
    else setOpen(false);
  }

  return <>
    <button className="buttonQuiet managementHistoryTrigger" aria-label="Histórico de comandas" title="Histórico de comandas" aria-haspopup="dialog"
      onClick={() => { setOpen(true); setSearch(""); setDay(""); void loadList({ day: "current", search: "", offset: 0 }); }}>
      <OperationalIcon name="history" size={20} />
    </button>
    {open && <ActionDialog title={selected ? "Detalhes da comanda" : "Histórico de comandas"} onClose={back} closeButtonClassName="buttonSecondary dialogReturn">
      <div ref={panel} tabIndex={-1}>
      <p className="muted">{selected ? "Somente consulta." : "Comandas encerradas por dia operacional do estabelecimento."}</p>
      {!selected && <form onSubmit={event => { event.preventDefault(); void loadList({ day: day || "current", search: search.trim(), offset: 0 }); }}>
        <div className="field"><label htmlFor="management-history-day">Dia operacional</label><input id="management-history-day" type="date" value={day} onChange={event => setDay(event.target.value)} /></div>
        <div className="field"><label htmlFor="management-history-search">Buscar comanda</label><input id="management-history-search" type="search" value={search} onChange={event => setSearch(event.target.value)} /></div>
        <button className="buttonSecondary" disabled={loading}>Consultar</button>
      </form>}
      {loading && <p role="status">{selected ? "Carregando comanda…" : "Carregando histórico…"}</p>}
      {error && <div className="notice" data-state="danger" role="alert"><p>{error}</p><button className="buttonSecondary" onClick={() => void (selected ? inspect(selected) : loadList(loaded))}>Tentar novamente</button></div>}
      {!selected && !loading && !error && <>
        {!rows.length && <p>Nenhuma comanda encerrada para esta consulta.</p>}
        {rows.map(tab => <button className="buttonQuiet" key={tab.id} onClick={() => void inspect(tab.id)}>
          <span>{tabPrimaryLabel(tab, true)} · {tabSecondaryLabel(tab, true)} · {tab.state === "CANCELLED" ? "Cancelada" : "Concluída"}</span>
        </button>)}
        <nav className="actions" aria-label="Páginas do histórico">
          {loaded.offset > 0 && <button className="buttonSecondary" onClick={() => void loadList({ ...loaded, offset: Math.max(0, loaded.offset - 200) })}>Página anterior</button>}
          {nextOffset !== null && <button className="buttonSecondary" onClick={() => void loadList({ ...loaded, offset: nextOffset })}>Próxima página</button>}
        </nav>
      </>}
      {detail && <section aria-label="Detalhes da comanda encerrada">
        <h3>{tabPrimaryLabel(detail, true)}</h3><p className="muted">{tabSecondaryLabel(detail, true)} · {detail.state === "CLOSED" ? "Concluída" : detail.state === "CANCELLED" ? "Cancelada" : "Comanda reaberta"}</p>
        <HistoryStatement tab={detail} />
        <h3>Pedidos</h3>
        {!detail.orders?.length && <p>Sem pedidos registrados.</p>}
        {detail.orders?.map((order, index) => <section key={order.id} aria-label={`Pedido ${index + 1}`}>
          <h4>Pedido {index + 1}</h4>{order.items.map(item => <div className="dataRow" key={item.id}><span>{item.quantity}× {item.product_name}{item.state === "CANCELLED" && " · Cancelado"}</span><strong>{money(item.line_total_cents)}</strong></div>)}
        </section>)}
        <h3>Pagamentos</h3>
        {!detail.payments?.length && <p>Sem pagamentos registrados.</p>}
        {detail.payments?.map(payment => <div className="dataRow" key={payment.id}><span>{paymentMethods[payment.method] ?? "Outro meio"} · {paymentStates[payment.status] ?? "Pendente de confirmação"}{payment.simulated && " · Simulação"}</span><strong>{money(payment.amount_cents)}</strong></div>)}
      </section>}
      </div>
    </ActionDialog>}
  </>;
}


function HistoryStatement({ tab }: { tab: HistoryTab }) {
  const confirmed = tab.payments?.filter(payment => ["CONFIRMED", "PARTIALLY_REFUNDED", "REFUNDED"].includes(payment.status) && payment.amount_cents > 0) ?? [];
  const paid = tab.state === "CLOSED" && !tab.service_assessment_stale && tab.exposure_cents === 0 && (tab.payable_cents ?? 0) > 0
    && (tab.payments_cents ?? 0) - (tab.refunds_cents ?? 0) >= (tab.payable_cents ?? 0) && confirmed.length > 0;
  const simulated = confirmed.some(payment => payment.simulated);
  const adjustments = [
    ["Descontos", -(tab.discounts_cents ?? 0)], ["Cortesias", -(tab.courtesy_cents ?? 0)],
    ["Correções", tab.corrections_cents ?? 0], ["Taxa de serviço", tab.service_charge_cents ?? 0],
    ["Responsabilidade transferida", tab.transfers_cents ?? 0],
  ] as const;
  return <section className="billSummary" aria-label="Extrato da conta">
    {tab.service_assessment_stale && <p className="notice" data-state="warning">Taxa de serviço desatualizada; confira a conta.</p>}
    {paid && <p className="notice" data-state="success"><strong><OperationalIcon name="check" size={20} /> {simulated ? "Paga · simulação" : "Paga"}</strong><br />{simulated ? "Recebimento confirmado em ambiente de simulação." : "Pagamento confirmado."}</p>}
    {adjustments.some(([, cents]) => cents !== 0) && <div className="dataRow"><span>Subtotal original</span><strong>{money(tab.original_subtotal_cents ?? tab.charges_cents ?? 0)}</strong></div>}
    {adjustments.filter(([, cents]) => cents !== 0).map(([label, cents]) => <div className="dataRow" key={label}><span>{label}</span><strong>{money(cents)}</strong></div>)}
    <div className="dataRow billTotal"><span>Total da conta</span><strong>{tab.payable_cents === undefined ? "Indisponível" : money(tab.payable_cents)}</strong></div>
    {!!tab.payments_cents && <div className="dataRow"><span>Pagamentos confirmados</span><strong>{money(tab.payments_cents)}</strong></div>}
    {!!tab.refunds_cents && <div className="dataRow"><span>Estornos</span><strong>{money(tab.refunds_cents)}</strong></div>}
    {tab.exposure_cents !== 0 && <div className="dataRow"><span>Saldo da conta</span><strong>{money(tab.exposure_cents)}</strong></div>}
  </section>;
}
