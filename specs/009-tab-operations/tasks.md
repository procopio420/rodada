# Tasks — Spec 009

## Domain/API

- [x] Define TabTransfer and TabTransferLine.
- [x] Define balanced ledger transfer effect.
- [x] Implement transferability calculation.
- [x] Implement move_tab_location.
- [x] Implement split/move open responsibility.
- [x] Implement merge duplicate Tabs.
- [x] Implement cancel_empty_tab.
- [x] Implement reopen_tab.
- [ ] Define explicit TabIdentifier reassignment — deferred until Guest Access persists TabIdentifier; no identifiers are inherited or rebound by operations.
- [x] Normalize blocked-by-payment and stale-version errors.
- [x] Require idempotency key on structural mutations.

## Persistence

- [x] Tab optimistic version.
- [x] Transfer unique/idempotency constraints.
- [x] Source/destination provenance indexes.
- [x] Merge pointer / cancel reason.
- [x] Reopen audit metadata.

## Android

- [x] Separate Mover local from Dividir/Mover consumo.
- [x] Item/quantity selection split UI.
- [x] Destination Tab create/search.
- [x] Transfer preview totals.
- [x] Merge survivor UI.
- [x] Paid/ambiguous blocker UX.
- [x] Manager reopen flow.

## Staff Web/PWA

- [ ] Tab structural operations where relevant to cashier/manager surfaces.
- [ ] Conflict refresh behavior.
- [ ] Provenance display for transferred responsibility.

## Guest

- [x] No guest structural mutation.
- [x] Preserve GuestSession on location move.
- [x] Rejoin guidance in Android merge confirmation; source GuestSessions are revoked, never rebound.

## Realtime

- [x] Emit source/destination invalidation metadata through durable AuditEvent; transport consumer integration belongs to Spec 019.
- [x] Refresh Dispatch destination on location move.
- [x] Emit canonical transfer/merge/reopen facts.

## Management

- [ ] Timeline rendering.
- [ ] Related Tabs drill-down.
- [x] Avoid double-counting balanced transfers as sales; include responsibility transfers in current open exposure.
- [x] Expose durable post-close reopen exception with original closure timestamp in operation history/audit. Daily-close-specific policy awaits the DailyClose owner.

## Quality/tests

- [x] Total Venue receivable unchanged by transfer.
- [x] Confirmed Orders/Payments never change historical tab_id.
- [x] Concurrent transfer cannot overdraw transferable amount.
- [x] Retry does not duplicate transfer.
- [x] Confirmed Payment/Refund blocks financial move.
- [x] In-flight ambiguous Payment blocks financial move.
- [x] Location move remains ledger-neutral.
- [x] Merge preserves source history.
- [x] Closing/reopening never changes TableOccupancy.

## Verified delivery

The original persistence/API/Android slice shipped in PR #47. The follow-up on
`feat/tab-operations` validates current main payment adapters and corrects expired-payment
blocking, peak-service responsibility queries, canonical operation reads, management exposure,
and Android rejection recovery. See [validation.md](validation.md) for exact test evidence.

Unchecked Web/Gerência rendering tasks are adjacent-surface integrations outside this delivery's
Android ownership. They do not imply that a transport or DailyClose policy is implemented.
