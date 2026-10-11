# DailyClose C2 — gerência, correções em duas pessoas e turno simulado

Date: 2026-10-11. This is a **software validation contract**, not PSP/hardware/production certification.

## Source of truth

- `/manage/daily-close` consumes canonical read-only DailyClose revision snapshots via `GET /management/daily-closes/?business_date=YYYY-MM-DD`.
- `POST /management/daily-closes/` generates an immutable as-of revision for a Venue/day; it does **not** reconcile or repair discrepancies automatically. `POST /management/daily-closes/{id}/review/` requires `cash.review`, recent operator PIN, current version, complete blockers and a matching current snapshot digest.
- Cashier physical count is always explicit and never prefilled. Reviewed original `DailyClose.snapshot` and `DailyCloseReview` remain PostgreSQL immutable. Later approved correction movements appear only in `post_close_adjustments` and `corrected_cash_delta_cents`.
- Reported venue receipts per method are not cash drawer expected/actual cash balances. Settlement or Pix/card provider certification is not claimed.

## Two-person correction workflow

- `POST/GET /cash/shifts/{shift_id}/correction-requests/`: `cash.adjustment.create` may propose an amount (signed integer cents), reason and idempotency key **only on CLOSED shifts**. A proposal is **not** a CashMovement and must not affect totals. Exact retry returns the original proposal; a different payload with the same key fails.
- `GET /management/correction-requests/?business_date=YYYY-MM-DD`: manager-only, venue-scoped list.
- `POST /cash/correction-requests/{request_id}/decision/`: `cash.review` and recent PIN, strict fields `expected_version`, `decision` (APPROVED or REJECTED), `reason`. The requesting staff member cannot decide their own proposal, even if they have `cash.review`.
- Approval atomically emits one original `CashMovement(CORRECTION, is_post_close_correction=True)` with a deterministic idempotency key, a linked `CashCorrectionRequest.movement`, reviewer identity, time and audit event. Rejection emits no movement. Replays return the same decision; conflicting/stale versions cannot overwrite it. PostgreSQL trigger rejects updating already-decided proposals and deleting any proposal.
- The legacy `POST /cash/shifts/{shift_id}/late-corrections/` now rejects with `409 CASH_CORRECTION_APPROVAL_REQUIRED` to prevent bypass; its internal service persists only for the approved transition and old domain tests. Earlier direct HTTP consumers must migrate to the request/decision contract.
- Pending correction proposals are daily-close blockers. Generating a new revision after a decision never mutates previous revisions. Reconciliation displays the signed post-close delta separately.

## Test evidence / release gate

- `apps/api/tests/test_cash_correction_approval.py` covers source permission, second-operator approval, PIN, cross-Venue scope, idempotent retry/mismatched replay, rejected/no-money state, stale/reviewed snapshot and PostgreSQL decision immutability.
- `apps/api/tests/test_four_track_shift.py` exercises guest QR → combined order → safe idempotent replay → Bar/Kitchen → money/refund → drawer count and discrepancy → immutable DailyClose review → pending two-person correction → approved movement → preserved snapshot.
- Web `/manage/daily-close` exposes financial summary, immutable revisions, blockers, per-method receipts, drawers, pending requests, decision reason and reauthentication UI. It does not mint a fake backend status.
- **Required to mark this accepted:** GitHub Actions on the final merged main commit must pass PostgreSQL API concurrency, Web TypeScript/integration/visual gates and Railway demo Docker smoke. A successful PR CI run alone does not validate a later merge SHA.
- **Excluded/unverified:** physical drawers, tills and printers, real Pix/card PSP settlement, Android process-death recovery, deployment to pilot Railway or real bar floor walkthrough.

## Operational walkthrough for management

1. Cashier opens a shift, records received cash and movements, counts cash physically, closes it. Any discrepancy remains visible and requires `cash.review` + PIN in `/cash`.
2. Manager picks the operating date in `/manage/daily-close`, generates an immutable revision, resolves blockers, then generates a new version and reviews it.
3. Staff proposes a post-close discrepancy with signed cents and a reason. It remains PENDING and has no monetary effect.
4. **Different** manager enters their own PIN, reviews proof, approves or rejects. Only an approval creates a CashMovement and emits audit evidence.
5. Original revision and original cash drawer counted/expected values remain unmodified; manager views a separate post-close correction delta and new revision as appropriate.
