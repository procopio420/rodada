# Plan — Spec 017

Partial cancellation: add nullable positive cancelled-unit facts to OrderCorrection with backwards-compatible fingerprints, and a distinct negative partial-cancellation ledger kind so existing whole-line uniqueness stays intact. Derive remaining quantity from applied facts; prefetch corrections on operational projections. Prorate the current canonical net using integers and consume all rounding cents on the final cancellation. Keep Tab/item locking, stage/transfer/paid guards and immutable snapshots. Verify unit/rounding/replay and real PostgreSQL races, then the actual Web/API journey and mobile dialogs. Apply migrations to the preserved local demo only using authorized local authentication and restart matching API/frontend builds.

## Recommended sequence

1. **Domain/migrations**
   - OrderCorrection;
   - WasteMarker;
   - replacement/remake linkage;
   - correction version/idempotency.

2. **Correction policy/preview**
   - stage-aware options;
   - current financial owner via Spec 009;
   - exact financial disposition.

3. **Simple cancellation**
   - NEW/ACCEPTED;
   - open-responsibility reversal;
   - fulfillment/dispatch cancellation.

4. **Preparing/Ready exception**
   - manager approval;
   - waste;
   - station realtime.

5. **Remake/replacement**
   - new OrderItem;
   - copied/edited customization;
   - courtesy replacement integration.

6. **Paid corrections**
   - refund-required orchestration;
   - provider idempotency.

7. **Surfaces/analytics**
   - Atendimento “Corrigir item”;
   - station badges;
   - management timeline/reasons.

## Rollout

Start with unpaid NEW/ACCEPTED cancellation. Do not expose delivered/paid correction until refund/courtesy orchestration passes end-to-end tests.

## Testing strategy

- snapshot immutability;
- state-specific permission matrix;
- concurrent double correction;
- transfer lineage;
- replacement charge+courtesy net;
- dispatch history preservation;
- provider refund idempotency;
- offline no-fake-cancel.

## Dependencies first

Specs 009–011 and payment Refund semantics must be stable before advanced correction.
