# Tasks — Spec 010

## Domain/API
- [x] ProductVariant model and validation.
- [x] ModifierGroup / ModifierOption.
- [x] ProductModifierGroup association.
- [x] Variant vs modifier rules in domain service.
- [x] Server-side customization validator.
- [x] Server-side price calculator in cents.
- [x] OrderItem customization snapshot.
- [x] Normalized ordering errors.
- [x] Product ordering-schema query.
- [x] Variant/option availability commands.

## Persistence
- [x] Constraints for one default variant.
- [x] Modifier min/max constraints.
- [x] Active/availability separation.
- [x] Snapshot persistence without mutable joins for history.
- [x] Availability versioning.

## Android
- [x] Quick-add no-choice products.
- [x] Compact variant/modifier sheet.
- [x] Required-choice validation.
- [x] Price delta/total preview.
- [x] Removal/add-on semantics.
- [x] Stale choice recovery.
- [x] Repeat previous configuration with revalidation.

## Staff Web/PWA
- [x] Bar/Kitchen availability controls.
- [x] Catalog configuration screens for manager.
- [x] Production rendering of structured customization.
- [x] Exceptional note visual separation.

## Guest
- [x] Published ordering schema.
- [x] Required/optional group UX.
- [x] Disabled unavailable choices.
- [x] Defaults visible/editable.
- [x] Price preview.
- [x] Notes secondary to structured choices.

## Realtime
- [x] Variant availability invalidation.
- [x] Modifier option availability invalidation.
- [x] Mark affected open carts stale (on shared catalog refresh or server rejection).

## Management
- [ ] Basic variant/modifier sales mix projection (follow-up analytics, outside this ordering delivery).
- [x] Availability history where relevant.

## Quality/tests
- [x] Existing product without modifiers remains valid.
- [x] Single-select max one.
- [x] min/max enforced server-side.
- [x] Unavailable option rejected despite stale UI.
- [x] Product unavailable blocks all choices.
- [x] Confirmed snapshot never changes after catalog edit.
- [x] Integer-cent calculation only.
- [x] Same idempotency key cannot duplicate customized OrderItem/Charge.
- [x] Guest and staff calculate same server-authoritative total.

## Delivery boundaries

Availability refresh reuses existing polling: Web 5s, native 15s/resume/reconnect.
SSE integration remains owned by the separate realtime branch; availability rejection
at confirmation is immediate. Availability history is retained in AuditEvent;
no separate analytics/history dashboard is added. Item corrections preserve remakes;
configured replacements use cancellation plus a new configured order.
