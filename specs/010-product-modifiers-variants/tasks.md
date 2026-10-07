# Tasks — Spec 010

## Domain/API
- [ ] ProductVariant model and validation.
- [ ] ModifierGroup / ModifierOption.
- [ ] ProductModifierGroup association.
- [ ] Variant vs modifier rules in domain service.
- [ ] Server-side customization validator.
- [ ] Server-side price calculator in cents.
- [ ] OrderItem customization snapshot.
- [ ] Normalized ordering errors.
- [ ] Product ordering-schema query.
- [ ] Variant/option availability commands.

## Persistence
- [ ] Constraints for one default variant.
- [ ] Modifier min/max constraints.
- [ ] Active/availability separation.
- [ ] Snapshot persistence without mutable joins for history.
- [ ] Availability versioning.

## Android
- [ ] Quick-add no-choice products.
- [ ] Compact variant/modifier sheet.
- [ ] Required-choice validation.
- [ ] Price delta/total preview.
- [ ] Removal/add-on semantics.
- [ ] Stale choice recovery.
- [ ] Repeat previous configuration with revalidation.

## Staff Web/PWA
- [ ] Bar/Kitchen availability controls.
- [ ] Catalog configuration screens for manager.
- [ ] Production rendering of structured customization.
- [ ] Exceptional note visual separation.

## Guest
- [ ] Published ordering schema.
- [ ] Required/optional group UX.
- [ ] Disabled unavailable choices.
- [ ] Defaults visible/editable.
- [ ] Price preview.
- [ ] Notes secondary to structured choices.

## Realtime
- [ ] Variant availability invalidation.
- [ ] Modifier option availability invalidation.
- [ ] Mark affected open carts stale.

## Management
- [ ] Basic variant/modifier sales mix projection.
- [ ] Availability history where relevant.

## Quality/tests
- [ ] Existing product without modifiers remains valid.
- [ ] Single-select max one.
- [ ] min/max enforced server-side.
- [ ] Unavailable option rejected despite stale UI.
- [ ] Product unavailable blocks all choices.
- [ ] Confirmed snapshot never changes after catalog edit.
- [ ] Integer-cent calculation only.
- [ ] Same idempotency key cannot duplicate customized OrderItem/Charge.
- [ ] Guest and staff calculate same server-authoritative total.
