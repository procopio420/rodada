"use client";

import { OperationalHeading } from "@/components/operational-heading";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { apiCall, asApiError, type ApiError, type StaffSessionView } from "@/lib/client/staff-auth";

type CashShift = {
  id: string;
  business_date?: string;
  cash_point_id?: string;
  status: "OPEN" | "COUNTING" | "CLOSED";
  opening_float_cents?: number;
  expected_cents?: number | null;
  expected_at_close_cents?: number | null;
  corrected_expected_cents?: number | null;
  counted_amount_cents?: number | null;
  discrepancy_cents?: number | null;
  review_status?: "NOT_REQUIRED" | "PENDING" | "REVIEWED";
  version: number;
  movements?: CashMovement[];
};

type CashPoint = { id: string; label: string; active_shift: CashShift | null; pending_review_shift?: CashShift | null; current_business_date?: string };
type CashMovement = {
  id: string;
  kind: string;
  amount_cents: number;
  reason: string;
  occurred_at: string;
  is_post_close_correction: boolean;
};

const money = (value: number | null | undefined) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format((value ?? 0) / 100);

function cents(value: string): number | null {
  const normalized = value.trim().replace(/\./g, "").replace(",", ".");
  if (!normalized || !/^\d+(\.\d{1,2})?$/.test(normalized)) return null;
  return Math.round(Number(normalized) * 100);
}

function movementLabel(kind: string) {
  return {
    OPENING_FLOAT: "Fundo inicial",
    CASH_PAYMENT: "Recebimento em dinheiro",
    CASH_REFUND: "Estorno em dinheiro",
    SUPPLY: "Suprimento",
    WITHDRAWAL: "Sangria",
    CORRECTION: "Correção tardia",
  }[kind] ?? kind;
}

export default function CashPage() {
  const [session, setSession] = useState<StaffSessionView | null>(null);
  const [points, setPoints] = useState<CashPoint[]>([]);
  const [pointId, setPointId] = useState("");
  const [shift, setShift] = useState<CashShift | null>(null);
  const [openingFloat, setOpeningFloat] = useState("");
  const [movementAmount, setMovementAmount] = useState("");
  const [movementReason, setMovementReason] = useState("");
  const [movementKind, setMovementKind] = useState<"SUPPLY" | "WITHDRAWAL">("SUPPLY");
  const [counted, setCounted] = useState("");
  const [reviewReason, setReviewReason] = useState("");
  const [notice, setNotice] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [confirmation, setConfirmation] = useState("");
  const [pendingReauth, setPendingReauth] = useState<(() => Promise<void>) | null>(null);
  const [reauthPin, setReauthPin] = useState("");
  const openKey = useRef<string | null>(null);
  const movementKey = useRef<string | null>(null);
  const currentPointId = useRef("");
  const [history, setHistory] = useState<CashShift[]>([]);
  const [historyOffset, setHistoryOffset] = useState<number | null>(null);

  const load = useCallback(async (preferredPointId?: string, preferredShiftId?: string) => {
    setLoading(true);
    setNotice(null);
    setConfirmation("");
    try {
    const [me, pointsResult] = await Promise.all([
      apiCall<StaffSessionView>("/api/auth/me"),
      apiCall<{ results: CashPoint[] }>("/api/pos/cash/points/"),
    ]);
    if (me.response.ok && me.body) setSession(me.body as StaffSessionView);
    if (!pointsResult.response.ok || !pointsResult.body) {
      setNotice(asApiError(pointsResult.body));
      return;
    }
    const result = (pointsResult.body as { results: CashPoint[] }).results;
    setPoints(result);
    const nextPointId = preferredPointId && result.some((point) => point.id === preferredPointId)
      ? preferredPointId
      : currentPointId.current && result.some((point) => point.id === currentPointId.current)
        ? currentPointId.current
        : result[0]?.id ?? "";
    setPointId(nextPointId);
    currentPointId.current = nextPointId;
    const selected = result.find((point) => point.id === nextPointId);
    if (selected) {
      const rows = await apiCall<{ results: CashShift[]; next_offset: number | null }>(`/api/pos/cash/shifts/history/?cash_point_id=${nextPointId}`);
      if (!rows.response.ok) { setNotice(asApiError(rows.body)); return; }
      const body = rows.body as { results: CashShift[]; next_offset: number | null };
      setHistory(body.results); setHistoryOffset(body.next_offset);
    } else { setHistory([]); setHistoryOffset(null); }
    const active = selected?.active_shift ?? selected?.pending_review_shift ?? null;
    if (!active && !preferredShiftId) {
      setShift(null);
      return;
    }
    const detail = await apiCall<CashShift>(`/api/pos/cash/shifts/${preferredShiftId ?? active?.id}/`);
    if (detail.response.ok && detail.body) {
      const loaded = detail.body as CashShift; setShift(loaded);
      setHistory(rows => rows.some(row => row.id === loaded.id) ? rows : [...rows, loaded]);
    }
    else setNotice(asApiError(detail.body));
    } catch { setNotice({ code: "NETWORK_ERROR", message: "Não foi possível atualizar o caixa. Confira a conexão." }); }
    finally { setLoading(false); }
  // pointId is deliberately read as the current selection when no preference is supplied.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => { void load(); }, [load]);

  const handleError = useCallback((body: unknown, retry?: () => Promise<void>) => {
    const error = asApiError(body);
    if (error.code === "REAUTH_REQUIRED" && retry) {
      setPendingReauth(() => retry);
      setNotice({ code: error.code, message: "Confirme seu PIN para concluir esta ação." });
      return;
    }
    setNotice(error);
  }, []);

  const openShift = async () => {
    const amount = cents(openingFloat);
    if (!pointId || amount === null) {
      setNotice({ code: "INVALID_OPENING_FLOAT", message: "Informe o fundo inicial em reais." });
      return;
    }
    setBusy(true);
    openKey.current ??= crypto.randomUUID();
    const result = await apiCall<CashShift>("/api/pos/cash/shifts/", {
      method: "POST",
      body: JSON.stringify({ cash_point_id: pointId, opening_float_cents: amount, idempotency_key: openKey.current }),
    });
    setBusy(false);
    if (result.response.ok) {
      openKey.current = null;
      setOpeningFloat("");
      await load(pointId);
    } else handleError(result.body, openShift);
  };

  const recordMovement = async () => {
    if (!shift) return;
    const amount = cents(movementAmount);
    if (amount === null || amount <= 0 || !movementReason.trim()) {
      setNotice({ code: "INVALID_CASH_MOVEMENT", message: "Informe valor positivo e motivo." });
      return;
    }
    setBusy(true);
    movementKey.current ??= crypto.randomUUID();
    const endpoint = movementKind === "SUPPLY" ? "supply" : "withdrawal";
    const result = await apiCall(`/api/pos/cash/shifts/${shift.id}/${endpoint}/`, {
      method: "POST",
      body: JSON.stringify({ amount_cents: amount, reason: movementReason.trim(), idempotency_key: movementKey.current }),
    });
    setBusy(false);
    if (result.response.ok) {
      movementKey.current = null;
      setMovementAmount("");
      setMovementReason("");
      await load(pointId);
    } else handleError(result.body, recordMovement);
  };

  const startCount = async () => {
    if (!shift) return;
    setBusy(true);
    const result = await apiCall(`/api/pos/cash/shifts/${shift.id}/count/start/`, { method: "POST", body: "{}" });
    setBusy(false);
    if (result.response.ok) await load(pointId);
    else handleError(result.body, startCount);
  };

  const closeShift = async () => {
    if (!shift) return;
    const amount = cents(counted);
    if (amount === null) {
      setNotice({ code: "INVALID_CASH_COUNT", message: "Digite o valor contado. Ele não é preenchido pelo valor esperado." });
      return;
    }
    setBusy(true);
    const result = await apiCall<CashShift>(`/api/pos/cash/shifts/${shift.id}/close/`, {
      method: "POST",
      body: JSON.stringify({ counted_amount_cents: amount, expected_version: shift.version }),
    });
    setBusy(false);
    if (result.response.ok) {
      setCounted("");
      await load(pointId);
    } else {
      const error = asApiError(result.body);
      if (error.code === "CASH_SHIFT_VERSION_CONFLICT") await load(pointId);
      handleError(result.body, closeShift);
    }
  };

  const review = async () => {
    if (!shift || !reviewReason.trim()) {
      setNotice({ code: "CASH_REVIEW_REASON_REQUIRED", message: "Registre o motivo da revisão." });
      return;
    }
    setBusy(true);
    const result = await apiCall(`/api/pos/cash/shifts/${shift.id}/review/`, {
      method: "POST",
      body: JSON.stringify({ reason: reviewReason.trim() }),
    });
    setBusy(false);
    if (result.response.ok) {
      setReviewReason("");
      await load(pointId);
      setConfirmation("Divergência revisada.");
    } else handleError(result.body, review);
  };

  const confirmReauth = async () => {
    if (!reauthPin || !pendingReauth) return;
    setBusy(true);
    const result = await apiCall("/api/auth/reauthenticate", { method: "POST", body: JSON.stringify({ pin: reauthPin }) });
    setBusy(false);
    if (!result.response.ok) {
      setNotice(asApiError(result.body));
      return;
    }
    setReauthPin("");
    const retry = pendingReauth;
    setPendingReauth(null);
    await retry();
  };

  const selectedPoint = points.find((point) => point.id === pointId);
  const expected = shift?.expected_cents ?? shift?.expected_at_close_cents ?? null;
  const countedCents = cents(counted);
  const liveDifference = countedCents === null || expected === null ? null : countedCents - expected;
  const canOperate = session?.capabilities.includes("cash.adjustment.create") ?? false;
  const canOpenOrClose = session?.capabilities.includes("cash.shift.open") ?? false;
  const canReview = session?.capabilities.includes("cash.review") ?? false;

  return <main className="appShell">
    <header className="productHeader">
      <div className="eyebrow">RODADA / CAIXA</div>
      <OperationalHeading as="h1" icon="wallet">Turno de caixa</OperationalHeading>
      <p className="muted">{session ? `${session.staff.display_name} · ${session.membership.role}` : "Carregando operador…"}</p>
      <Link className="backLink" href="/pos">← Voltar ao atendimento</Link>
    </header>

    {notice ? <div className="notice" data-state="danger" role="alert"><strong>{notice.code}</strong><br />{notice.message}</div> : null}
    {loading && <div className="loadingState" role="status">Carregando caixa…</div>}
    {confirmation && <div className="notice" data-state="success" role="status">{confirmation}</div>}

    <section className="panel">
      <div className="field">
        <label htmlFor="cash-point">Ponto de caixa</label>
        <select id="cash-point" value={pointId} onChange={(event) => void load(event.target.value)} disabled={busy || loading}>
          {!points.length ? <option value="">Nenhum ponto disponível</option> : null}
          {points.map((point) => <option value={point.id} key={point.id}>{point.label}{point.active_shift ? " · turno ativo" : ""}</option>)}
        </select>
      </div>
      {!loading && !notice && !selectedPoint ? <p className="muted">Sem ponto de caixa ativo para este operador.</p> : null}
    </section>

    {selectedPoint && <section className="panel"><OperationalHeading as="h2" icon="receipt">Histórico de turnos</OperationalHeading>
      <div className="field"><label htmlFor="cash-history">Selecionar turno atual ou fechamento antigo</label><select id="cash-history" value={shift?.id ?? ""} disabled={busy || loading} onChange={e => void load(pointId, e.target.value)}>
        <option value="">Selecione um turno</option>{history.map(row => <option key={row.id} value={row.id}>{row.business_date ?? "Data não informada"} · {row.status === "CLOSED" ? "Fechado" : row.status === "COUNTING" ? "Em conferência" : "Aberto"}{row.review_status === "PENDING" ? " · revisão pendente" : ""} · {row.id.slice(0, 8)}</option>)}
      </select></div>
      {historyOffset !== null && <button className="buttonSecondary" disabled={busy || loading} onClick={() => void (async () => {
        setLoading(true);
        try { const r = await apiCall<{ results: CashShift[]; next_offset: number | null }>(`/api/pos/cash/shifts/history/?cash_point_id=${pointId}&offset=${historyOffset}`);
          if (!r.response.ok) { setNotice(asApiError(r.body)); return; }
          const body = r.body as { results: CashShift[]; next_offset: number | null }; setHistory(rows => [...new Map([...rows, ...body.results].map(row => [row.id, row])).values()]); setHistoryOffset(body.next_offset);
        } catch { setNotice({ code: "NETWORK_ERROR", message: "Não foi possível carregar turnos antigos." }); } finally { setLoading(false); }
      })()}>Carregar turnos mais antigos</button>}
      {selectedPoint.active_shift && shift?.id !== selectedPoint.active_shift.id && <button className="buttonQuiet" disabled={busy || loading} onClick={() => void load(pointId)}>Voltar ao turno ativo</button>}
    </section>}

    {!shift && selectedPoint ? <section className="panel">
      <OperationalHeading as="h2" icon="wallet">Abrir turno</OperationalHeading>
      <p className="muted">{selectedPoint.label} · {selectedPoint.current_business_date ?? "Data operacional definida pelo estabelecimento"}</p>
      <div className="field"><label htmlFor="opening">Fundo inicial</label><input id="opening" inputMode="decimal" value={openingFloat} onChange={(event) => setOpeningFloat(event.target.value)} placeholder="Ex.: 200,00" /></div>
      <p className="muted">Você está abrindo o caixa com este valor físico. Confirme somente depois de conferir.</p>
      <button className="buttonPrimary" style={{ width: "100%" }} disabled={busy || !canOpenOrClose} onClick={() => void openShift()}>{busy ? "Abrindo…" : "Confirmar abertura"}</button>
      {!canOpenOrClose ? <p className="muted">Seu perfil não pode abrir turno de caixa.</p> : null}
    </section> : null}

    {shift ? <>
      <section className="panel cashPosition">
        <div><div className="eyebrow">{selectedPoint?.label ?? "Caixa"}</div><OperationalHeading as="h2" icon="wallet">{shift.status === "OPEN" ? "Caixa aberto" : shift.status === "COUNTING" ? "Em conferência" : "Turno fechado"}</OperationalHeading></div>
        <span className="statusBadge" data-state={shift.status === "CLOSED" ? "success" : shift.status === "COUNTING" ? "warning" : "info"}>{shift.status}</span>
        <div className="cashExpected"><span>Esperado</span><strong>{money(expected)}</strong></div>
        <div className="dataRow"><span>Fundo inicial</span><strong>{money(shift.movements?.find((movement) => movement.kind === "OPENING_FLOAT")?.amount_cents ?? shift.opening_float_cents)}</strong></div>
        <div className="dataRow"><span>Recebimentos em dinheiro</span><strong>{money((shift.movements ?? []).filter((movement) => movement.kind === "CASH_PAYMENT").reduce((sum, movement) => sum + movement.amount_cents, 0))}</strong></div>
        <div className="dataRow"><span>Suprimentos</span><strong>{money((shift.movements ?? []).filter((movement) => movement.kind === "SUPPLY").reduce((sum, movement) => sum + movement.amount_cents, 0))}</strong></div>
        <div className="dataRow"><span>Sangrias</span><strong>{money((shift.movements ?? []).filter((movement) => movement.kind === "WITHDRAWAL").reduce((sum, movement) => sum + movement.amount_cents, 0))}</strong></div>
      </section>

      {shift.status === "OPEN" ? <section className="panel">
        <OperationalHeading as="h2" icon="wallet">Movimentar caixa</OperationalHeading>
        <div className="segmented" role="group" aria-label="Tipo de movimento">
          <button className={movementKind === "SUPPLY" ? "buttonPrimary" : "buttonSecondary"} onClick={() => setMovementKind("SUPPLY")}>Suprimento</button>
          <button className={movementKind === "WITHDRAWAL" ? "buttonPrimary" : "buttonSecondary"} onClick={() => setMovementKind("WITHDRAWAL")}>Sangria</button>
        </div>
        <div className="field"><label htmlFor="movement-amount">Valor</label><input id="movement-amount" inputMode="decimal" value={movementAmount} onChange={(event) => setMovementAmount(event.target.value)} placeholder="Ex.: 50,00" /></div>
        <div className="field"><label htmlFor="movement-reason">Motivo</label><input id="movement-reason" value={movementReason} onChange={(event) => setMovementReason(event.target.value)} placeholder={movementKind === "SUPPLY" ? "Ex.: reforço de troco" : "Ex.: envio ao cofre"} /></div>
        <button className="buttonPrimary" style={{ width: "100%" }} disabled={busy || !canOperate} onClick={() => void recordMovement()}>{busy ? "Registrando…" : movementKind === "SUPPLY" ? "Registrar suprimento" : "Registrar sangria"}</button>
        {!canOperate ? <p className="muted">Seu perfil não pode registrar movimentos de caixa.</p> : null}
      </section> : null}

      {shift.status === "OPEN" ? <section className="panel">
        <OperationalHeading as="h2" icon="wallet">Fechar turno</OperationalHeading>
        <p className="muted">Ao iniciar a conferência, recebimentos e movimentos ficam bloqueados até o fechamento.</p>
        <button className="buttonSecondary" style={{ width: "100%" }} disabled={busy || !canOpenOrClose} onClick={() => void startCount()}>Conferir caixa</button>
      </section> : null}

      {shift.status === "COUNTING" ? <section className="panel">
        <OperationalHeading as="h2" icon="wallet">Contagem e revisão</OperationalHeading>
        <p className="muted">Conte o dinheiro físico. O campo começa vazio para que a diferença continue visível.</p>
        <div className="field"><label htmlFor="counted">Contado</label><input id="counted" inputMode="decimal" value={counted} onChange={(event) => setCounted(event.target.value)} placeholder="Digite o total contado" /></div>
        <div className="dataRow"><span>Esperado</span><strong>{money(expected)}</strong></div>
        <div className="dataRow"><span>Contado</span><strong>{countedCents === null ? "—" : money(countedCents)}</strong></div>
        <div className="dataRow"><span>Diferença</span><strong className={liveDifference ? "cashDifference" : ""}>{liveDifference === null ? "—" : money(liveDifference)}</strong></div>
        {liveDifference !== null && liveDifference !== 0 ? <div className="notice" data-state="danger">A diferença será gravada como divergência; nenhum movimento será inventado para zerá-la.</div> : null}
        <button className="buttonPrimary" style={{ width: "100%" }} disabled={busy || !canOpenOrClose || countedCents === null} onClick={() => void closeShift()}>{busy ? "Fechando…" : "Confirmar fechamento"}</button>
      </section> : null}

      {shift.status === "CLOSED" ? <section className="panel">
        <OperationalHeading as="h2" icon="wallet">Resultado do fechamento</OperationalHeading>
        <div className="dataRow"><span>Esperado</span><strong>{money(shift.expected_at_close_cents ?? expected)}</strong></div>
        <div className="dataRow"><span>Contado</span><strong>{money(shift.counted_amount_cents)}</strong></div>
        <div className="dataRow"><span>Diferença</span><strong className={shift.discrepancy_cents ? "cashDifference" : ""}>{money(shift.discrepancy_cents)}</strong></div>
        {shift.review_status === "PENDING" ? <><div className="notice" data-state="danger">Divergência aguardando revisão de gerente.</div><div className="field"><label htmlFor="review-reason">Motivo da revisão</label><input id="review-reason" value={reviewReason} onChange={(event) => setReviewReason(event.target.value)} placeholder="Explique a divergência" /></div><button className="buttonPrimary" style={{ width: "100%" }} disabled={busy || !canReview} onClick={() => void review()}>Revisar divergência</button>{!canReview ? <p className="muted">A revisão exige perfil de gerente.</p> : null}</> : <p className="muted">{shift.review_status === "REVIEWED" ? "Divergência revisada." : "Fechamento sem revisão pendente."}</p>}
      </section> : null}

      <section className="panel">
        <OperationalHeading as="h2" icon="receipt">Histórico de movimentos</OperationalHeading>
        {!shift.movements?.length ? <p className="muted">Nenhum movimento registrado.</p> : <div className="movementList">{shift.movements.slice().reverse().map((movement) => <div className="movement" key={movement.id}><div><strong>{movementLabel(movement.kind)}</strong><small>{new Date(movement.occurred_at).toLocaleString("pt-BR")}{movement.reason ? ` · ${movement.reason}` : ""}</small></div><strong className={movement.amount_cents < 0 ? "cashNegative" : "cashPositive"}>{movement.amount_cents < 0 ? "−" : "+"}{money(Math.abs(movement.amount_cents))}</strong></div>)}</div>}
      </section>
    </> : null}

    {pendingReauth ? <section className="panel reauthPanel"><OperationalHeading as="h2" icon="lock">Confirme seu PIN</OperationalHeading><p className="muted">Esta ação exige confirmação recente do gerente atual.</p><div className="field"><label htmlFor="reauth-pin">Seu PIN</label><input id="reauth-pin" type="password" inputMode="numeric" value={reauthPin} onChange={(event) => setReauthPin(event.target.value)} autoComplete="current-password" /></div><button className="buttonPrimary" style={{ width: "100%" }} disabled={busy || !reauthPin} onClick={() => void confirmReauth()}>Confirmar e continuar</button></section> : null}
  </main>;
}
