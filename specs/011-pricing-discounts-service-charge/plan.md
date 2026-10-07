# Plan — Spec 011

## Recommended sequence

1. **Domain/migrations**
   - expand Adjustment kind/scope/calculation;
   - AdjustmentAllocation;
   - pricing version on Tab if needed;
   - service-charge policy reference.

2. **Canonical calculator**
   - ordering of effects;
   - cents-only percentage;
   - deterministic largest-remainder allocation;
   - net payable invariant.

3. **Authorization**
   - capability + threshold policy;
   - approval-required response;
   - reason codes;
   - privileged reauth integration.

4. **Service charge**
   - assessment;
   - reduce/remove;
   - superseding history.

5. **Discount/courtesy APIs**
   - preview then commit;
   - item/Tab scope;
   - idempotency.

6. **Payment/refund integration**
   - stale payment amount conflict;
   - partial payment safety;
   - item refund preview using allocations.

7. **Surfaces/reporting**
   - Atendimento/Cashier;
   - Guest total;
   - receipts;
   - Gerência daily/monthly definitions.

## Rollout

Introduce read-compatible fields first. Existing Tabs without new adjustments calculate as before.

Do not enable post-payment repricing until refund/reconciliation integration passes end-to-end tests.

## Testing strategy

- table/property tests for rounding;
- allocation sum exactness;
- threshold permissions;
- concurrent edits;
- partial-payment guards;
- refund previews;
- closing metric definitions.

## Dependencies first

Core ledger and Spec 006 payment states; Spec 008 capability checks. Spec 013 can expose policy UI after Billing contracts are stable.
