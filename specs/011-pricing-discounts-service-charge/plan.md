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

## Implemented architecture

The existing ledger owns the calculator, policy, allocation and approval services.
All pricing mutations serialize on Tab and lock the typed policy snapshot. The
venue policy is live for new adjustments; applied facts retain the old policy.
Service removal allocates revenue/pass-through components from active assessments,
so policy changes do not retrospectively reclassify collections.

Service is explicitly assessed/refreshed rather than implicitly added by UI or a
payment provider. New consumption/discounts invalidate its per-Charge basis, even
when the total basis happens to remain the same. Settlement requires refresh.

Native recovery saves the exact pricing command and original payment version;
Web saves the pricing intent in session storage scoped to venue, operator and Tab.
Both reauthorize server-side and retry the same key after an ambiguous response.
Daily/monthly reports share business-date range queries; transfer components do
not create sales. Optional fiscal/GL integration remains outside this slice.
