# Tasks — Spec 016

## Domain/API
- [ ] PartySizeObservation model.
- [ ] Target exactly one of TableOccupancy/Tab.
- [ ] Record current count command.
- [ ] Correction/supersedes semantics.
- [ ] Guest authorization.
- [ ] Post-release manager correction.
- [ ] Current/history queries.
- [ ] Normalized errors.

## Persistence
- [ ] Current version/observation pointer.
- [ ] Idempotency key.
- [ ] Release snapshot/reference.
- [ ] No fake historical backfill.

## Android
- [ ] Unknown “—” display.
- [ ] Fast 1–8/manual selector.
- [ ] Active correction.
- [ ] Conflict refresh.

## Staff Web/PWA
- [ ] Table/occupancy party-size display/edit.
- [ ] Manager historical correction.
- [ ] Provenance indicator when useful.

## Guest
- [ ] Optional party-size prompt.
- [ ] Skip when optional.
- [ ] Stale conflict handling.
- [ ] Own-context only.

## Realtime
- [ ] Party-size invalidation to occupancy/management.

## Management
- [ ] Known/unknown coverage.
- [ ] Revenue/ticket per cover formula.
- [ ] Exclude ambiguous attribution.
- [ ] Post-release correction rebuild.

## Quality/tests
- [ ] Two Tabs in one occupancy do not double covers.
- [ ] Unknown is not zero/one.
- [ ] Guest and staff race resolves with version conflict.
- [ ] Closing Tab does not finalize occupancy count.
- [ ] Post-release correction preserves prior observation.
- [ ] Ratio-of-sums calculation exact.
- [ ] Reports expose coverage percentage.
