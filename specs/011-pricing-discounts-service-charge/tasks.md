# Tasks — Spec 011

## Domain/API
- [x] Add immutable item-cancellation reversal adjustment kind.
- [ ] Define AdjustmentAllocation.
- [ ] Implement canonical pricing order.
- [ ] Implement percentage/fixed cents calculator.
- [ ] Implement deterministic allocation.
- [ ] Apply item discount.
- [ ] Apply Tab discount.
- [ ] Grant courtesy.
- [ ] Assess service charge.
- [ ] Reduce/remove service charge.
- [ ] Reverse/supersede adjustment.
- [ ] Pricing preview endpoint/query.
- [ ] Approval-required contract.
- [ ] Post-payment settlement guard.
- [ ] Refund/item net-value helper.

## Persistence
- [ ] Adjustment allocation rows.
- [x] Idempotency constraints for item-cancellation reversals.
- [ ] Pricing version / optimistic lock.
- [ ] Supersedes/reversal links.
- [ ] Reason code/text fields.

## Android
- [ ] Item discount action.
- [ ] Tab discount/courtesy action.
- [ ] Service charge row/reduce/remove.
- [ ] Before/after preview.
- [ ] Approval + reauth flow.
- [ ] Stale total/payment conflict recovery.

## Staff Web/PWA
- [ ] Cashier/manager adjustment flows.
- [ ] Policy-aware controls.
- [ ] Receipt/check presentation.

## Guest
- [ ] Gross/discount/service/final presentation.
- [ ] Optional service-charge opt-out only when policy permits.
- [ ] Never expose internal staff reasons.

## Realtime
- [ ] Invalidate Tab totals/payment screen after adjustment.
- [ ] Emit canonical pricing facts.

## Management
- [ ] Gross/net definitions.
- [ ] Separate discount/courtesy/service/refund metrics.
- [ ] Closing integration.
- [ ] Adjustment drill-down/audit.

## Quality/tests
- [ ] No float anywhere.
- [ ] Allocation sums exactly to Adjustment.
- [ ] Net eligible consumption never negative.
- [ ] Concurrent stale pricing mutation conflicts.
- [ ] Retry cannot duplicate Adjustment.
- [ ] Partial-payment repricing guard.
- [ ] Service charge never calculated on itself/tip/payment/refund.
- [x] Historical OrderItem price snapshot unchanged for cancellation reversal.
