"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { OperationalHeading } from "@/components/operational-heading";
import { apiCall, asApiError, type StaffSessionView } from "@/lib/client/staff-auth";

type Method = { method: string; paid_cents: number; refunds_cents: number; net_received_cents: number };
type Drawer = {
  id: string; label: string; status: string; review_status: string;
  expected_at_close_cents?: number | null; counted_amount_cents?: number | null;
  discrepancy_cents?: number | null; corrected_expected_cents?: number | null;
};
type Blocker = { kind: string; id?: string; status?: string; review_status?: string; amount_cents?: number };
type Snapshot = {
  financial: { gross_cents: number; net_sales_cents: number; adjustments_cents: number };
  receipts: { paid_cents: number; refunds_cents: number; net_received_cents: number; methods: Method[] };
  cash_shifts: Drawer[];
  blockers: Blocker[];
  calendar: { timezone: string; lower: string; upper: string };
};
type Close = {
  id: string; business_date: string; version: number; status: string; fingerprint: string;
  generated_at: string; original: Snapshot;
  review: null | { reviewed_at: string; reviewed_by: string; reason: string };
  corrected_cash_delta_cents: number;
  post_close_adjustments: { id: string; shift_id: string; amount_cents: number; reason: string }[];
};
type Proposal = {
  id: string; shift_id: string; cash_point_label: string; amount_cents: number;
  reason: string; status: "PENDING" | "APPROVED" | "REJECTED"; version: number;
  requested_by: string; requested_at: string; decided_by: string | null;
  decision_reason: string; movement_id: string | null;
};
type Report = { cash_shifts: { id: string; business_date: string; cash_point_label: string; status: string }[] };
type ErrorWithCode = Error & { code?: string };
const money = (n: number | null | undefined) =>
  n == null ? "—" : new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(n / 100);
const stamp = (s: string) => new Date(s).toLocaleString("pt-BR");
const methodName = (name: string) => ({
  CASH: "Dinheiro", PIX: "Pix", CARD: "Cartão", TAP_TO_PAY: "Tap to Pay",
  EXTERNAL_TERMINAL: "Maquininha externa", OTHER: "Outro",
} as Record<string, string>)[name] ?? name;
const blockerName = (kind: string) => ({
  OPEN_TAB: "Comanda ainda aberta", CASH_SHIFT: "Caixa aberto ou sem revisão",
  OVERDUE_CASH_SHIFT: "Caixa de outro dia em aberto",
  UNRESOLVED_PAYMENT: "Pagamento não conciliado",
  BUSINESS_DAY_NOT_ENDED: "Dia operacional ainda em andamento",
  PENDING_CASH_CORRECTION: "Correção de caixa aguardando aprovação",
} as Record<string, string>)[kind] ?? kind;

async function call<T>(url: string, payload?: unknown): Promise<T> {
  const result = await apiCall<T>(url, payload === undefined ? undefined : {
    method: "POST", body: JSON.stringify(payload),
  });
  if (!result.response.ok) {
    const error = asApiError(result.body);
    throw Object.assign(new Error(error.message), { code: error.code }) as ErrorWithCode;
  }
  return result.body as T;
}

function parseSignedCents(value: string): number | null {
  const text = value.trim().replace(/\./g, "").replace(",", ".");
  if (!/^[+-]?\d+(\.\d{1,2})?$/.test(text)) return null;
  const result = Math.round(Number(text) * 100);
  return Number.isSafeInteger(result) && result !== 0 ? result : null;
}

export default function DailyCloseManagement() {
  const [session, setSession] = useState<StaffSessionView | null>(null);
  const [day, setDay] = useState("");
  const [closes, setCloses] = useState<Close[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [shifts, setShifts] = useState<Report["cash_shifts"]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [reviewReason, setReviewReason] = useState("");
  const [decisionReason, setDecisionReason] = useState("");
  const [requestShift, setRequestShift] = useState("");
  const [requestAmount, setRequestAmount] = useState("");
  const [requestReason, setRequestReason] = useState("");
  const [pendingAction, setPendingAction] = useState<null | (() => Promise<void>)>(null);
  const [pin, setPin] = useState("");

  const canReview = session?.capabilities.includes("cash.review") ?? false;
  const canRequest = session?.capabilities.includes("cash.adjustment.create") ?? false;
  const selected = closes.find(close => close.id === selectedId) ?? closes[0] ?? null;
  const closedShifts = shifts.filter(shift => shift.status === "CLOSED");
  const pending = proposals.filter(item => item.status === "PENDING");

  async function load(targetDay: string) {
    setLoading(true); setError("");
    try {
      const [history, corrections, report] = await Promise.all([
        call<{ results: Close[] }>(`/api/pos/management/daily-closes/?business_date=${targetDay}`),
        call<{ results: Proposal[] }>(`/api/pos/management/correction-requests/?business_date=${targetDay}`),
        call<Report>(`/api/pos/management/reports/?start=${targetDay}&end=${targetDay}`),
      ]);
      setCloses(history.results); setProposals(corrections.results); setShifts(report.cash_shifts);
      setSelectedId(previous => history.results.some(close => close.id === previous) ? previous : history.results[0]?.id ?? "");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível carregar o fechamento.");
    } finally { setLoading(false); }
  }

  useEffect(() => {
    void (async () => {
      try {
        const [me, calendar] = await Promise.all([
          call<StaffSessionView>("/api/auth/me"),
          call<{ business_date: string }>("/api/pos/management/calendar/"),
        ]);
        setSession(me); setDay(calendar.business_date);
        await load(calendar.business_date);
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : "Sessão indisponível.");
        setLoading(false);
      }
    })();
  }, []);

  async function submit(action: () => Promise<void>) {
    if (busy) return;
    setBusy(true); setError(""); setNotice("");
    try { await action(); }
    catch (cause) {
      const problem = cause as ErrorWithCode;
      if (problem.code === "REAUTH_REQUIRED") setPendingAction(() => action);
      else {
        setError(problem.message ?? "Operação não concluída.");
        if (problem.code === "STALE_VERSION" || problem.code === "STALE_SNAPSHOT") await load(day);
      }
    } finally { setBusy(false); }
  }

  async function reauthenticate() {
    if (!pin || !pendingAction) return;
    setBusy(true); setError("");
    try {
      await call("/api/auth/reauthenticate", { pin });
      setPin("");
      const action = pendingAction;
      setPendingAction(null);
      await action();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "PIN não confirmado.");
    } finally { setBusy(false); }
  }

  function generate() {
    const key = crypto.randomUUID();
    void submit(async () => {
      const result = await call<Close>("/api/pos/management/daily-closes/", {
        business_date: day, idempotency_key: key,
      });
      setSelectedId(result.id); setNotice("Revisão imutável gerada. Confira os bloqueios antes de aprovar.");
      await load(day);
    });
  }

  function review() {
    if (!selected || !reviewReason.trim()) { setError("Explique a revisão antes de confirmar."); return; }
    const close = selected, reason = reviewReason.trim();
    void submit(async () => {
      await call(`/api/pos/management/daily-closes/${close.id}/review/`, {
        expected_version: close.version, reason,
      });
      setReviewReason(""); setNotice("Fechamento diário revisado e registrado.");
      await load(day);
    });
  }

  function propose() {
    const amount = parseSignedCents(requestAmount);
    if (!requestShift || amount === null || !requestReason.trim()) {
      setError("Selecione um caixa fechado, informe o valor assinado e o motivo.");
      return;
    }
    const shiftId = requestShift, reason = requestReason.trim(), key = crypto.randomUUID();
    void submit(async () => {
      await call(`/api/pos/cash/shifts/${shiftId}/correction-requests/`, {
        amount_cents: amount, reason, idempotency_key: key,
      });
      setRequestAmount(""); setRequestReason("");
      setNotice("Correção solicitada. Outro gerente deverá aprovar ou rejeitar.");
      await load(day);
    });
  }

  function decide(proposal: Proposal, decision: "APPROVED" | "REJECTED") {
    if (!decisionReason.trim()) { setError("Justifique a aprovação ou rejeição."); return; }
    const reason = decisionReason.trim();
    void submit(async () => {
      await call(`/api/pos/cash/correction-requests/${proposal.id}/decision/`, {
        expected_version: proposal.version, decision, reason,
      });
      setDecisionReason(""); setNotice(decision === "APPROVED"
        ? "Correção aprovada: novo movimento auditado, histórico original preservado."
        : "Correção rejeitada: nenhum movimento criado.");
      await load(day);
    });
  }

  return <main className="appShell">
    <header className="productHeader">
      <div className="eyebrow">RODADA / GERÊNCIA / CAIXA</div>
      <OperationalHeading as="h1" icon="wallet">Fechamento diário</OperationalHeading>
      <p className="muted">Recebimentos, gavetas e correções são fatos distintos. Revisões antigas nunca são reescritas.</p>
      <Link className="backLink" href="/manage">← Voltar à Gerência</Link>
    </header>

    <section className="panel">
      <OperationalHeading as="h2" icon="sales">Dia operacional</OperationalHeading>
      <div className="field"><label htmlFor="daily-close-date">Data do fechamento</label>
        <input id="daily-close-date" type="date" value={day} onChange={event => setDay(event.target.value)} /></div>
      <div className="actions">
        <button className="buttonSecondary" disabled={!day || busy || loading} onClick={() => void load(day)}>Consultar</button>
        <button className="buttonPrimary" disabled={!canReview || !day || busy || loading} onClick={generate}>Gerar revisão do dia</button>
      </div>
      {!canReview && <p className="muted">Gerar e revisar exige a permissão de gerente e confirmação recente do PIN.</p>}
    </section>

    {error && <div className="notice" role="alert" data-state="danger">{error}</div>}
    {notice && <div className="notice" role="status" data-state="success">{notice}</div>}
    {loading && <p role="status">Carregando dados canônicos…</p>}

    {!loading && <section className="panel">
      <OperationalHeading as="h2" icon="receipt">Revisões imutáveis</OperationalHeading>
      {!closes.length && <p className="muted">Nenhuma revisão gerada para esta data.</p>}
      {!!closes.length && <>
        <div className="field"><label htmlFor="daily-close-version">Histórico de revisões</label>
          <select id="daily-close-version" value={selected?.id ?? ""} onChange={event => setSelectedId(event.target.value)}>
            {closes.map(close => <option key={close.id} value={close.id}>Versão {close.version} · {close.status} · {stamp(close.generated_at)}</option>)}
          </select></div>
        {selected && <>
          <span className="statusBadge" data-state={selected.status === "REVIEWED" ? "success" : selected.status === "INCOMPLETE" ? "danger" : "warning"}>{selected.status}</span>
          <div className="dataRow"><span>Vendas líquidas</span><strong>{money(selected.original.financial.net_sales_cents)}</strong></div>
          <div className="dataRow"><span>Recebimentos confirmados</span><strong>{money(selected.original.receipts.paid_cents)}</strong></div>
          <div className="dataRow"><span>Estornos confirmados</span><strong>{money(selected.original.receipts.refunds_cents)}</strong></div>
          <div className="dataRow"><span>Recebimento líquido</span><strong>{money(selected.original.receipts.net_received_cents)}</strong></div>
          <p className="muted">Recebimentos totais do estabelecimento não equivalem ao saldo físico do caixa.</p>
          <h3>Métodos de recebimento</h3>
          {selected.original.receipts.methods.map(row => <div className="dataRow" key={row.method}><span>{methodName(row.method)}</span><strong>{money(row.net_received_cents)}</strong></div>)}
          <h3>Caixas físicos</h3>
          {selected.original.cash_shifts.map(shift => <div className="reportGroup" key={shift.id}>
            <strong>{shift.label}</strong><p className="muted">{shift.status} · {shift.review_status}</p>
            <div className="dataRow"><span>Contado</span><strong>{money(shift.counted_amount_cents)}</strong></div>
            <div className="dataRow"><span>Diferença</span><strong>{money(shift.discrepancy_cents)}</strong></div>
          </div>)}
          <h3>Bloqueios da revisão</h3>
          {!selected.original.blockers.length ? <p className="muted">Nenhum bloqueio no snapshot.</p>
            : selected.original.blockers.map((blocker, index) => <p key={`${blocker.kind}-${blocker.id ?? index}`} className="notice" data-state="danger">{blockerName(blocker.kind)}{blocker.id ? ` · ${blocker.id.slice(0, 8)}` : ""}</p>)}
          {selected.status === "READY_FOR_REVIEW" && !selected.review && <div className="field">
            <label htmlFor="daily-close-review-reason">Justificativa da revisão</label>
            <textarea id="daily-close-review-reason" value={reviewReason} maxLength={240} onChange={event => setReviewReason(event.target.value)} />
            <button className="buttonPrimary" disabled={!canReview || busy || !reviewReason.trim()} onClick={review}>Confirmar revisão com PIN</button>
          </div>}
          {selected.review && <p className="notice" data-state="success">Revisado em {stamp(selected.review.reviewed_at)} · {selected.review.reason}</p>}
          {selected.status === "INCOMPLETE" && <p className="muted">Resolva os bloqueios e gere uma nova versão. Esta revisão permanecerá preservada.</p>}
          <p className="muted">Fingerprint: <code>{selected.fingerprint}</code></p>
          <div className="dataRow"><span>Correções posteriores aprovadas</span><strong>{money(selected.corrected_cash_delta_cents)}</strong></div>
        </>}
      </>}
    </section>}

    {!loading && <section className="panel">
      <OperationalHeading as="h2" icon="wallet">Correções depois do fechamento</OperationalHeading>
      <p className="muted">O solicitante não pode aprovar a própria correção. A proposta não altera valores até outra pessoa autorizada decidir.</p>
      {canRequest && <div className="field">
        <label htmlFor="correction-shift">Caixa fechado</label>
        <select id="correction-shift" value={requestShift} onChange={event => setRequestShift(event.target.value)}>
          <option value="">Selecione o caixa</option>
          {closedShifts.map(shift => <option key={shift.id} value={shift.id}>{shift.cash_point_label} · {shift.id.slice(0, 8)}</option>)}
        </select>
        <label htmlFor="correction-amount">Ajuste em R$ (positivo ou negativo)</label>
        <input id="correction-amount" value={requestAmount} onChange={event => setRequestAmount(event.target.value)} placeholder="Ex.: -10,00" inputMode="decimal" />
        <label htmlFor="correction-reason">Justificativa da proposta</label>
        <textarea id="correction-reason" value={requestReason} onChange={event => setRequestReason(event.target.value)} maxLength={240} />
        <button className="buttonSecondary" onClick={propose} disabled={busy || !requestShift || !requestReason.trim()}>Solicitar correção</button>
      </div>}
      {!canRequest && <p className="muted">Este operador não pode propor movimentos de caixa.</p>}
      <h3>Pendentes ({pending.length})</h3>
      {!proposals.length && <p className="muted">Nenhuma proposta nesta data.</p>}
      {proposals.map(row => <div className="reportGroup" key={row.id}>
        <div className="dataRow"><strong>{row.cash_point_label}</strong><strong>{money(row.amount_cents)}</strong></div>
        <p>{row.reason}</p>
        <p className="muted">Solicitada em {stamp(row.requested_at)} · {row.status}</p>
        {row.status === "PENDING" && canReview && <>
          {session?.staff.id === row.requested_by
            ? <p className="notice" data-state="warning">Solicitação própria: outro gerente precisa decidir.</p>
            : <div className="field">
              <label htmlFor={`decision-${row.id}`}>Motivo da decisão</label>
              <textarea id={`decision-${row.id}`} value={decisionReason} onChange={event => setDecisionReason(event.target.value)} maxLength={240} />
              <div className="actions"><button className="buttonPrimary" disabled={busy || !decisionReason.trim()} onClick={() => decide(row, "APPROVED")}>Aprovar</button>
                <button className="buttonSecondary" disabled={busy || !decisionReason.trim()} onClick={() => decide(row, "REJECTED")}>Rejeitar</button></div>
            </div>}
        </>}
        {row.status !== "PENDING" && <p className="muted">Decisão: {row.decision_reason}{row.movement_id ? ` · Movimento ${row.movement_id.slice(0, 8)}` : ""}</p>}
      </div>)}
    </section>}

    {pendingAction && <section className="panel reauthPanel">
      <OperationalHeading as="h2" icon="lock">Confirmar PIN do gerente</OperationalHeading>
      <p className="muted">Confirmação de segurança necessária; a mesma operação será repetida com a chave original.</p>
      <div className="field"><label htmlFor="daily-close-pin">Seu PIN</label>
        <input id="daily-close-pin" type="password" inputMode="numeric" autoComplete="current-password" value={pin} onChange={event => setPin(event.target.value)} /></div>
      <div className="actions"><button className="buttonPrimary" disabled={!pin || busy} onClick={() => void reauthenticate()}>Confirmar e continuar</button>
        <button className="buttonSecondary" onClick={() => { setPendingAction(null); setPin(""); }}>Cancelar</button></div>
    </section>}
    <p><Link className="backLink" href="/cash">Abrir turnos individuais de caixa →</Link></p>
  </main>;
}
