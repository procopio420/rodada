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
