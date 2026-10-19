import styles from "./attendance-credit-bar.module.css";

/** Existing financial_position read model; never a local authorization/policy. */
export type AttendanceCreditPosition = {
  effective_limit_cents: number;
  exposure_cents: number;
  remaining_capacity_cents: number;
  relationship_snapshot: string;
};
const relationships: Record<string, string> = {
  VISITOR: "Visitante", KNOWN: "Conhecido", REGULAR: "Regular", HOUSE: "Da casa", RESTRICTED: "Restrito",
};
const money = (cents: number) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(cents / 100);

export function AttendanceCreditBar({ position, draftCents = 0, compact = false, onDetails }: {
  position: AttendanceCreditPosition | null | undefined;
  draftCents?: number;
  compact?: boolean;
  onDetails?: () => void;
}) {
  if (!position || ![position.effective_limit_cents, position.exposure_cents, position.remaining_capacity_cents].every(Number.isSafeInteger)
    || position.effective_limit_cents < 0 || position.remaining_capacity_cents < 0 || !Number.isSafeInteger(draftCents) || draftCents < 0 || !Number.isSafeInteger(position.exposure_cents + draftCents)) {
    return <section className={`${styles.creditbar} ${compact ? styles.compact : ""}`} aria-label="Referência de consumo da comanda"><p>Referência de consumo indisponível. Confira a comanda antes de enviar.</p></section>;
  }
  const limit = position.effective_limit_cents, exposure = position.exposure_cents;
  const projected = exposure + draftCents;
  const usedPct = limit > 0 ? Math.min(100, Math.max(0, 100 * exposure / limit)) : 0;
  const orderPct = limit > 0 ? Math.min(100 - usedPct, 100 * draftCents / limit) : 0;
  const percent = limit > 0 ? Math.round(100 * Math.max(0, exposure) / limit) : null;
  const excess = Math.max(0, projected - limit);
  const level = limit === 0 || exposure >= limit || projected > limit ? "exceeded" : projected >= limit * .8 ? "warning" : "ok";
  const stateLabel = excess > 0 ? `${draftCents > 0 ? "Pedido excede a referência" : "Consumo acima da referência"} em ${money(excess)} · bloqueio ativo`
    : limit === 0 ? "Referência zero · trava ativa" : projected >= limit * .8 ? "Próximo do limite de referência" : "Dentro da referência";
  const label = `Consumo ${money(exposure)} de ${money(limit)}; ${money(position.remaining_capacity_cents)} disponíveis${draftCents > 0 ? `; novo pedido ${money(draftCents)}${excess ? `; excesso ${money(excess)}` : ""}` : ""}. Regra do estabelecimento: Bloquear (ENFORCE).`;
  const bar = limit > 0 ? <div className={styles.progress} role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(usedPct)} aria-valuetext={label}>
    <span className={styles.current} style={{ width: `${usedPct}%` }} />
    {draftCents > 0 && <span className={styles.pending} style={{ width: `${orderPct}%` }} />}
    <span className={styles.threshold} aria-hidden="true" />
  </div> : compact ? <div className={styles.progress} aria-hidden="true" /> : <div className={styles.zero}>Referência de consumo R$ 0,00 · bloqueio ativo</div>;
  return <section className={`${styles.creditbar} ${compact ? styles.compact : ""}`} data-level={level} aria-label="Referência de consumo da comanda">
    {compact ? <>
      <div className={styles.slimHead}><span>Limite · {relationships[position.relationship_snapshot] ?? "Sem perfil"}</span><strong>{money(exposure)} / {money(limit)}</strong></div>
      {bar}
      <div className={styles.slimFoot}><small>{level === "ok" ? `${money(position.remaining_capacity_cents)} disponíveis` : stateLabel}</small>{onDetails && <button type="button" onClick={onDetails}>Detalhes ›</button>}</div>
    </> : <>
      <div className={styles.heading}><span>Referência de consumo</span><span className={styles.relationship}>{relationships[position.relationship_snapshot] ?? "Sem perfil"}</span></div>
      <div className={styles.numbers}><span><strong>{money(exposure)}</strong><small> de {money(limit)} usados</small></span><small>{money(position.remaining_capacity_cents)} disponíveis</small></div>
      {bar}
      <div className={styles.key}><span>{percent === null ? "Limite zero" : `${percent}% utilizado${draftCents > 0 ? " · pedido em listras" : ""}`}</span>{draftCents > 0 && <b className={styles.newOrder}>＋ {money(draftCents)} no pedido</b>}</div>
      <div className={styles.foot}><span>{stateLabel}</span>{onDetails && <button type="button" onClick={onDetails}>Ver detalhes ›</button>}</div>
    </>}
  </section>;
}
