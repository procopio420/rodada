# Tasks — Spec 011

- [x] Extend canonical immutable Adjustment and preserve legacy kinds.
- [x] Persist exact per-Charge allocations and historical policy snapshots.
- [x] Integer half-up percentage calculation and deterministic largest remainder.
- [x] Fixed/percentage item and Tab discounts; full/partial courtesy.
- [x] Configurable service preview, assessment, refresh, reduction/removal.
- [x] Compensating reversals with explicit transferred/superseded guards.
- [x] Atomic Tab locks, versions, intent fingerprints and durable replay responses.
- [x] Typed configuration, capability thresholds and recent privileged reauth.
- [x] Exact manager approval request with requester/approver provenance.
- [x] Pending payment/refund and post-payment settlement guards.
- [x] House Account exposure updates and positive-effect limit enforcement.
- [x] Unpaid split/merge commercial component allocation; paid transfers blocked.
- [x] Refund assistance based on net consumption and refundable service.
- [x] Legacy cancellation/refund integration uses remaining discounted value.
- [x] Web and native adjustment previews, approval request and PIN flow.
- [x] Native and Web recovery preserve the original pricing intent.
- [x] Cashier, Android payment and guest commercial bill breakdown.
- [x] Management configuration, approvals, history and gross/net reports.
- [x] Bounded refresh and stale service/payment conflict handling.
- [x] PostgreSQL append-only and deferred allocation-sum guards.
- [x] Legacy upgrade, API, calculator and real PostgreSQL concurrency tests.
- [x] Customized order → discount → service → partial → remake/correction → final → close → reconciliation.
- [x] Web layout/accessibility and adjacent-surface primitive comparisons.
- [x] Native unit tests, debug APK and lint.

Guest service opt-out is performed by authorized staff under venue policy; this
slice does not grant guests unilateral financial mutation. Existing receipt/check
presentation uses the canonical bill. Printing infrastructure remains untouched.

- [x] Bloquear preview antes da leitura canônica; verificar atraso na UI e integração PostgreSQL.
