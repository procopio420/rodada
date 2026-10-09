# Tasks — Spec 012

## Domain/API
- [x] CashPoint.
- [x] Expand CashShift lifecycle.
- [x] CashMovement kinds and invariants.
- [x] CashTenderDetail.
- [x] Active-shift selection for CASH Payment.
- [x] Supply command.
- [x] Withdrawal/sangria command.
- [x] Cash refund movement.
- [x] Start count.
- [x] Close with expected/count/discrepancy.
- [x] Manager discrepancy review.
- [x] Late correction command.
- [ ] Unclosed/carryover policy.
- [x] Cash close preview/query.

## Persistence
- [x] Unique active shift per CashPoint.
- [x] Unique Payment/Refund cash movement linkage.
- [x] Movement idempotency.
- [x] Immutable close snapshot.
- [x] Review/correction provenance.
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
- [x] Opening float applied exactly once.
- [x] Tender - change = Payment amount.
- [x] Concurrent payment vs close is consistent.
- [x] Retry cannot duplicate movement.
- [x] Closed shift rejects ordinary movement.
- [x] Late correction preserves original snapshot.
- [ ] Daily close cannot silently claim reconciled with unresolved shift.

## Release verification 2026-10-09

Implementation checkboxes are not release proof. See `docs/development/closure-native-2026-10-09.json` for PostgreSQL custody/concurrency evidence and unresolved manager projection, cutoff, emergency-runbook and device gates. Full-drawer withdrawal retries replay their original movement before validating current funds.
