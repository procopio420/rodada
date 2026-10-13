# Plan — Spec 012

## Recommended sequence

1. **Domain/migrations**
   - CashPoint;
   - expanded CashShift;
   - CashMovement;
   - CashTenderDetail;
   - optional CashShiftParticipant.

2. **Payment integration**
   - confirmed CASH Payment -> idempotent movement;
   - cash Refund -> movement;
   - active-shift requirement.

3. **Manual movements**
   - supply;
   - withdrawal/sangria;
   - reasons/permissions.

4. **Count/close**
   - COUNTING state;
   - expected reconstruction;
   - immutable close snapshot;
   - discrepancy threshold/review.

5. **Late correction / unclosed shift**
   - post-close correction semantics;
   - carryover exception.

6. **Surfaces**
   - cashier/Atendimento cash screen;
   - Gerência position/review;
   - closing integration.

## Rollout

Create a default CashPoint for existing Venues. Legacy CashShift summaries remain viewable; do not invent historical movements.

## Testing strategy

- cash position arithmetic;
- unique active shift;
- payment idempotency;
- tender/change invariants;
- close race with incoming payment;
- discrepancy review;
- late correction preserves original close;
- daily close incomplete when shift remains open.

## Dependencies first

Payment/Refund states (006), authorization (008), and canonical daily-close consumption by 007.

## Recorte POS Web CASH — Spec026 T03a

Implementar contrato de recebimento recuperável da Spec006, envelope
por sessão da014 e fingerprint físico da012. Usar componentes existentes;
validar Web/API e PostgreSQL descartável, sem alterar snapshot ou provider.

## T03b — execução do estorno manual recuperável

1. Envelope antes do POST; guard síncrono, campos congelados e retomada explícita.
2. Validar sessão e fingerprint de replay CASH/correção; preservar locks/auditoria.
3. Testar perda após commit/readback, reload, PIN/sessão/storage, divergência e
   concorrência em PostgreSQL; jornadas Web/API360/390/430, visual completo/build.
