# Tasks — Spec 009

## Domain/API
- [ ] Define TabTransfer and TabTransferLine.
- [ ] Define balanced ledger transfer effect.
- [ ] Implement transferability calculation.
- [ ] Implement move_tab_location.
- [ ] Implement split/move open responsibility.
- [ ] Implement merge duplicate Tabs.
- [ ] Implement cancel_empty_tab.
- [ ] Implement reopen_tab.
- [ ] Define explicit TabIdentifier reassignment.
- [ ] Normalize blocked-by-payment and stale-version errors.
- [ ] Require idempotency key on structural mutations.

## Persistence
- [ ] Tab optimistic version.
- [ ] Transfer unique/idempotency constraints.
- [ ] Source/destination provenance indexes.
- [ ] Merge pointer / cancel reason.
- [ ] Reopen audit metadata.

## Android
- [ ] Separate Mover local from Dividir/Mover consumo.
- [ ] Item/quantity selection split UI.
- [ ] Destination Tab create/search.
- [ ] Transfer preview totals.
- [ ] Merge survivor UI.
- [ ] Paid/ambiguous blocker UX.
- [ ] Manager reopen flow.

## Staff Web/PWA
- [ ] Tab structural operations where relevant to cashier/manager surfaces.
- [ ] Conflict refresh behavior.
- [ ] Provenance display for transferred responsibility.

## Guest
- [ ] No guest structural mutation.
- [ ] Preserve GuestSession on location move.
- [ ] Rejoin guidance after merge/source cancellation.

## Realtime
- [ ] Invalidate source and destination Tab.
- [ ] Refresh Dispatch destination on location move.
- [ ] Emit canonical transfer/merge/reopen facts.

## Management
- [ ] Timeline rendering.
- [ ] Related Tabs drill-down.
- [ ] Avoid double-counting balanced transfers as sales.
- [ ] Surface post-close reopen exception.

## Quality/tests
- [ ] Total Venue receivable unchanged by transfer.
- [ ] Confirmed Orders/Payments never change historical tab_id.
- [ ] Concurrent transfer cannot overdraw transferable amount.
- [ ] Retry does not duplicate transfer.
- [ ] Confirmed Payment/Refund blocks financial move.
- [ ] In-flight ambiguous Payment blocks financial move.
- [ ] Location move remains ledger-neutral.
- [ ] Merge preserves source history.
- [ ] Closing/reopening never changes TableOccupancy.
