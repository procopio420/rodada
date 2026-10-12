export type Bill = { original_subtotal_cents?: number; charges_cents?: number; discounts_cents?: number; courtesy_cents?: number; corrections_cents?: number; wrong_entry_removals_cents?: number; service_charge_cents?: number; payable_cents?: number; payments_cents?: number; refunds_cents?: number; exposure_cents: number; service_assessment_stale?: boolean };
const money = (value = 0) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value / 100);
export function BillSummary({ bill, compact = false }: { bill: Bill; compact?: boolean }) {
  const mistaken = compact ? bill.wrong_entry_removals_cents ?? 0 : 0;
  const corrections = (bill.corrections_cents ?? 0) - mistaken;
  const rows = [["Subtotal original", bill.original_subtotal_cents ?? bill.charges_cents], ["Descontos", -(bill.discounts_cents ?? 0)], ["Cortesias", -(bill.courtesy_cents ?? 0)], ["Correções", corrections], ["Taxa de serviço", bill.service_charge_cents], ["Total a pagar", bill.payable_cents], ["Pagamentos recebidos", bill.payments_cents], ["Estornos", bill.refunds_cents], ["Saldo restante", bill.exposure_cents]] as const;
  const breakdown = <>{rows.filter(([label, value]) => label === "Correções" ? !compact || value !== 0 : true).map(([label, value]) => <div className={`dataRow ${label === "Saldo restante" ? "billBalance" : label === "Total a pagar" ? "billTotal" : ""}`} key={label}><span>{label}</span><strong>{money(value)}</strong></div>)}{bill.service_assessment_stale && <p className="notice" data-state="warning">Atualize a taxa de serviço antes de receber.</p>}</>;
  return <div className="billSummary" aria-label="Resumo da conta">{compact ? <>
    <div className="dataRow"><span>Subtotal</span><strong>{bill.payable_cents === undefined ? "Indisponível" : money(bill.payable_cents)}</strong></div>
    <details><summary className="buttonQuiet billDetailsToggle">Mais detalhes</summary>{breakdown}</details>
  </> : breakdown}</div>;
}
