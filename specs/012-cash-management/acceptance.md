# Acceptance — Spec 012

## Open shift

**Given** CashPoint “Caixa principal” has no active shift  
**When** CASHIER opens with 20000 cents float  
**Then** one OPEN CashShift exists and expected starting cash is 20000 cents.

## Unique active shift

**Given** that CashPoint already has an OPEN shift  
**When** another open request is made  
**Then** backend rejects it without creating a second active shift.

## Cash receipt and change

**Given** Tab cash Payment is 8200 cents and customer tenders 10000  
**When** staff confirms receipt  
**Then** Payment is CONFIRMED, tender detail records 10000/1800 and expected drawer increases by exactly 8200 cents.

## Idempotent receipt

**Given** confirmed CASH Payment movement exists  
**When** payment confirmation/event is retried  
**Then** no duplicate CashMovement is created.

## Supply

**Given** an OPEN shift  
**When** authorized cashier adds 5000 cents supply with required reason  
**Then** expected cash increases by 5000 and actor/reason are audited.

## Sangria

**Given** an OPEN shift  
**When** cashier withdraws 10000 cents with reason  
**Then** expected cash decreases by 10000 and the movement remains immutable.

## Cash refund

**Given** a Refund is confirmed as physically paid in cash  
**When** cash integration processes it  
**Then** expected cash decreases once and movement links the Refund.

## Count and close

**Given** expected cash is 43800 cents  
**When** cashier counts 43500 and closes  
**Then** close snapshot records expected 43800, counted 43500 and discrepancy -300 cents.

## Review threshold

**Given** -300 exceeds configured review threshold  
**When** shift closes  
**Then** review_status=PENDING and Gerência surfaces an exception.

## Manager review

**Given** a pending discrepancy  
**When** MANAGER reviews with note  
**Then** review status changes to REVIEWED but expected/count/discrepancy values are not rewritten.

## Late correction

**Given** a CLOSED shift omitted a real historical 1000-cent withdrawal  
**When** manager records a late correction  
**Then** original close snapshot remains unchanged, corrected position is separately derivable and a post-close exception is emitted.

## Unclosed shift

**Given** a shift remains OPEN after business-date cutoff  
**When** reporting runs  
**Then** no automatic fake count/close is created, CashPoint blocks a second shift by default and closing is marked incomplete.

## Concurrency

**Given** a cash Payment and shift close race  
**When** both transactions execute  
**Then** the Payment is either included before the close boundary or rejected/retried against the CLOSED shift; it cannot be confirmed while omitted from expected cash.

## Permission denial

**Given** STAFF lacks withdrawal capability  
**When** they call withdrawal directly  
**Then** backend rejects it and no movement occurs.

## Degraded behavior

**Given** API is unavailable  
**When** staff handles an emergency physical cash transaction under runbook  
**Then** UI does not label it server-confirmed; reconciliation after reconnect requires an explicit audited recovery action.

## Audit verification

**Given** supply, withdrawal, close, review and late correction  
**When** audit is inspected  
**Then** each includes actor, timestamp, CashPoint/shift, amount and required reason.

## Recorte POS Web CASH — Spec026 T03a

- [x] Duplo envio/perda após commit/reload convergem ao mesmo Payment e movimento.
- [x] Replay divergente de caixa/tender não altera ledger, audit ou snapshots.
- [x] Sessão distinta/revogada/storage falho preservam pendência sem enviar/adotar.
- [x] Readback confirma Payment antes de liberar; rejeição inicial permite revisão.

Evidência local: Spec026/revalidation.md, seção T03a. Não cobre estorno,
fechar aba ou resolução gerencial entre sessões; gates anteriores mantidos.

## T03b — critérios do recorte manual

Evidências em Spec026/revalidation.md; gates externos permanecem abertos.

- [x] Mesmo Refund após duplo toque, resposta perdida, reload e readback falho.
- [x] Payload congelado; PIN recente, sessão divergente/revogada e storage falho
  não descartam nem adotam intenção ambígua. Rejeição inicial segura permite edição.
- [x] Replay divergente rejeitado; saldo/refundable, Payment/snapshots, ledger e
  auditoria preservados; concorrência produz um único efeito em PostgreSQL.
- [x] Jornada real Web/API e mobile360/390/430; visual completo, build/tipos e lint
  registrados sem declarar provider, piloto, aparelho ou deploy homologados.
