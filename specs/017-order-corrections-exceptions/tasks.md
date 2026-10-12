# Tasks — Spec 017

- [x] Append cancelled-unit facts and partial ledger kind without editing confirmed snapshots.
- [x] Canonical remaining-unit projections for staff/guest/kitchen/dispatch/new production tickets.
- [x] Quantity selector with bounded touch controls and exact retry intent; closing action after bill.
- [x] PostgreSQL financial/replay/concurrency regression, real Web/API journey and visual validation.
- [x] Authorized migration/restart of preserved local demo.

Validation (2026-10-12): 108 PostgreSQL tests, two real Web/API/PostgreSQL journeys and 226 visual cases passed. Production build and TypeScript passed. No visual baseline changes. Local demo schema migrations applied after a verified backup; all 16 existing Payments and their total were preserved.

## Domain/API
- [x] OrderCorrection model/kinds/status.
- [x] FinancialDisposition contract.
- [x] WasteMarker.
- [x] Replacement/remake linkage.
- [ ] Correction options/preview.
- [x] Stage-aware authorization.
- [x] Cancel confirmed item command for unpaid NEW/ACCEPTED work.
- [ ] Current financial-owner resolution.
- [x] Open responsibility reversal integration.
- [x] Create remake.
- [x] Create replacement.
- [x] Comped replacement via Spec 011.
- [x] Paid/refund-required orchestration with reauthenticated manager settlement.
- [x] Structured reason codes.

## Persistence
- [x] Correction idempotency.
- [x] Original/replacement indexes.
- [x] Waste provenance.
- [ ] Legacy cancelled-item compatibility.

## Android
- [ ] Corrigir item entry point.
- [ ] Stage-aware consequence preview.
- [ ] Manager approval/reauth.
- [ ] Wrong item -> cancel + replacement flow.
- [ ] Complaint/refund outcome UI.
- [ ] Offline local note only, no fake success.

## Staff Web/PWA
- [ ] Bar/Kitchen cancellation display.
- [ ] Remake/replacement badge/link.
- [ ] Waste marker action.
- [ ] Historical correction detail.

## Guest
- [ ] Policy-limited cancellation request.
- [ ] “Chamar atendimento” fallback.
- [ ] Outcome without internal blame metadata.

## Realtime
- [ ] Cancellation/remake/replacement facts.
- [ ] Dispatch task resolution.
- [ ] Station queue invalidation.

## Management
- [ ] Correction timeline.
- [ ] Reason/stage metrics.
- [ ] Reversed/courtesy/refund amounts.
- [ ] No simplistic staff leaderboard.

## Quality/tests
- [x] Confirmed snapshot never edited.
- [x] Original fulfillment history preserved.
- [x] Double correction idempotent/conflicted.
- [x] Replacement is new OrderItem.
- [x] Comped replacement net effect correct.
- [ ] Transferred financial responsibility corrected on current owner.
- [x] Paid item requires refund/courtesy semantics.
- [ ] Offline correction not treated canonical.

## Release verification 2026-10-09

Checkboxes above track implementation only. Per-criterion evidence and remaining modifier/transfer/device gaps are in `docs/development/closure-native-2026-10-09.json`. Served-item corrections preserve PICKED_UP/DELIVERED facts; remake/replacement creates separate work. Corrected modifier selections and allocation-aware transferred responsibility remain open.
