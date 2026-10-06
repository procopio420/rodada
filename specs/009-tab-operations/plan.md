# Plan — Spec 009

## Recommended sequence

1. **Domain/migrations**
   - Tab versioning if needed;
   - TabTransfer + TabTransferLine;
   - balanced ledger transfer effect;
   - merge/reopen provenance.

2. **Transferability service**
   - exact open amount;
   - blockers for confirmed/refunded/in-flight payments;
   - interaction with Adjustments.

3. **Commands**
   - location move;
   - split/move responsibility;
   - merge duplicate Tabs;
   - cancel empty;
   - reopen.

4. **API contracts**
   - preview before commit;
   - normalized conflict/non-transferable errors;
   - idempotency keys.

5. **Atendimento UX**
   - location move;
   - item-based split;
   - merge survivor selection;
   - paid-state blockers;
   - reopen for authorized roles.

6. **Realtime/Management**
   - invalidate affected Tabs;
   - timeline facts;
   - post-close exception.

## Rollout

Ship location move first because it has no ledger effect. Ship financial transfer only after ledger transfer invariants and concurrent tests pass.

Do not silently migrate historical Orders/Payments.

## Testing strategy

- property/invariant tests for balanced transfer;
- concurrent double-transfer;
- split/merge with and without payments;
- idempotent retry;
- identifier/session behavior;
- daily-close reopen behavior;
- E2E Atendimento split of unpaid Tab.

## Dependencies first

Specs 001, 004, 006 and 008 authorization. Spec 011 must define how adjusted lines report transferability before broad rollout of discounted-item moves.
