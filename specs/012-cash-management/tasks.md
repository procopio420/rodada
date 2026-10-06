# Tasks — Spec 012

## Domain/API
- [ ] CashPoint.
- [ ] Expand CashShift lifecycle.
- [ ] CashMovement kinds and invariants.
- [ ] CashTenderDetail.
- [ ] Active-shift selection for CASH Payment.
- [ ] Supply command.
- [ ] Withdrawal/sangria command.
- [ ] Cash refund movement.
- [ ] Start count.
- [ ] Close with expected/count/discrepancy.
- [ ] Manager discrepancy review.
- [ ] Late correction command.
- [ ] Unclosed/carryover policy.
- [ ] Cash close preview/query.

## Persistence
- [ ] Unique active shift per CashPoint.
- [ ] Unique Payment/Refund cash movement linkage.
- [ ] Movement idempotency.
- [ ] Immutable close snapshot.
- [ ] Review/correction provenance.
- [ ] Legacy migration to default CashPoint.

## Android
- [ ] Select/resolve active CashPoint.
- [ ] Cash received + tender/change UX.
- [ ] Supply/sangria for authorized roles.
- [ ] Count flow.
- [ ] Close/discrepancy flow.
- [ ] Offline/manual contingency messaging.

## Staff Web/PWA
- [ ] Cashier shift view where applicable.
- [ ] Management cash-point configuration entry point.
- [ ] Review late correction details.

## Realtime
- [ ] Cash position invalidation.
- [ ] Close/review events to Gerência.

## Management
- [ ] Active/unclosed shifts.
- [ ] Expected/count/discrepancy.
- [ ] Review action.
- [ ] Daily close integration.
- [ ] Post-close correction indicator.

## Infra/integration
- [ ] Operational runbook for emergency cash capture when API unavailable.

## Quality/tests
- [ ] Opening float applied exactly once.
- [ ] Tender - change = Payment amount.
- [ ] Concurrent payment vs close is consistent.
- [ ] Retry cannot duplicate movement.
- [ ] Closed shift rejects ordinary movement.
- [ ] Late correction preserves original snapshot.
- [ ] Daily close cannot silently claim reconciled with unresolved shift.
