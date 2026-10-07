# Tasks — Spec 017

## Domain/API
- [ ] OrderCorrection model/kinds/status.
- [ ] FinancialDisposition contract.
- [ ] WasteMarker.
- [ ] Replacement/remake linkage.
- [ ] Correction options/preview.
- [ ] Stage-aware authorization.
- [ ] Cancel confirmed item command.
- [ ] Current financial-owner resolution.
- [ ] Open responsibility reversal integration.
- [ ] Create remake.
- [ ] Create replacement.
- [ ] Comped replacement via Spec 011.
- [ ] Paid/refund-required orchestration.
- [ ] Structured reason codes.

## Persistence
- [ ] Correction idempotency.
- [ ] Original/replacement indexes.
- [ ] Waste provenance.
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
- [ ] Confirmed snapshot never edited.
- [ ] Original fulfillment history preserved.
- [ ] Double correction idempotent/conflicted.
- [ ] Replacement is new OrderItem.
- [ ] Comped replacement net effect correct.
- [ ] Transferred financial responsibility corrected on current owner.
- [ ] Paid item requires refund/courtesy semantics.
- [ ] Offline correction not treated canonical.
