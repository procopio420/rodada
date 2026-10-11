# Agent C — DailyClose C1 evidence and limitations

Base: GitHub `main` ddf889af, materialized by connector; isolated branch
`feat/spec007-012-daily-close`, not a clone of repository history.

Implemented: immutable Venue/day/revision snapshots, shared PR71-compatible
receipt summary, multi-drawer snapshots, pending/overdue shift and ambiguous
payment blockers, separate recent-reauth manager review, stale digest rejection,
idempotent generation and separate post-close cash correction projection.
PostgreSQL repeatable-read owns the service transaction; serialization/deadlock/
unique identity races retry three times. Signed snapshot and review rows have
PostgreSQL UPDATE/DELETE guards. Later financial activity is allowed and does
not rewrite the original close.

Contracts: list/create `management/daily-closes/`; detail by UUID; review by UUID
with `expected_version` and `reason`. Routes registered in isolated source. Read permission
is `management.reports.read`; generation/review additionally require `cash.review`
and recent reauthentication. Date-scoped receipt helper preserves PR71 payload.
PR71 inline aggregation now calls that helper, preserving its existing response.
Generation/review lock Venue with NO KEY UPDATE, then only the session row;
membership, staff and device authority share the coherent MVCC snapshot without
inverting admin membership/device-to-session lock order. Access expiry, actor
membership/device provenance, revocation and recent PIN reauthentication are
revalidated. A concurrent observation may linearize before revocation; an
already committed revocation always denies it. Unknown request fields fail validation. Open Tabs explicitly
block review rather than allowing an incomplete service to appear reconciled.

| Spec / AC | Implementation | Validation / actual result | Remaining | Risk |
|---|---|---|---|---|
| 007-007 | cash/daily_close.py, daily_close_models.py, daily_close_views.py | compileall and diff check passed only | PostgreSQL/API CI, manager UI and shift scenario | P0 |
| 012-009 / 012-012 | explicit shift/payment/day blockers, no count mutation | tests written, not executed | PostgreSQL unclosed/multi-drawer tests | P0 |
| 007-008 / 012-011 | original snapshot + separately read late corrections | tests written, not executed | Correction approval workflow, corrected view UI, full append-only ledger projection | P1 |
| 012-013 | coherent MVCC cash/payment snapshot race test | PostgreSQL test written, not executed | Actual PostgreSQL run and integrated SHA | P0 |

Commands actually run in isolated snapshot: `python -m compileall -q` over six
new Python files (success); `git diff --check` (success). Django is absent in this
execution environment; PostgreSQL socket access is blocked as reported by root.
No acceptance criterion is PASS and no production readiness is claimed. No PSP,
production database, physical printer or Railway deployment was used.

Required commands when dependencies/database exist:
`python manage.py makemigrations --check --dry-run`; `python manage.py test
tests.test_daily_close tests.test_cash_management tests.test_payments_concurrency
--settings=rodada_api.settings_payments_postgres`.

Residual software: C2 complete ledger-wide post-close correction event linking;
C3 mobile-first management screen, accessible blockers/timeline and offline state;
execution of cross-Venue API permission, strict-input and recent-reauth tests;
effective-dated calendar integration with B3; recovery-evidence blocker projection
once A2 exposes a canonical model. Existing calendar history-change rejection is
retained. Cash correction delta is explicitly separate from sales/receipts.
