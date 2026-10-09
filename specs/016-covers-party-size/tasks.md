# Tasks — Spec 016

## Domain/API
- [x] PartySizeObservation model.
- [x] Target exactly one of TableOccupancy/Tab.
- [x] Record current count command.
- [x] Correction/supersedes semantics.
- [x] Guest authorization.
- [x] Post-release manager correction.
- [x] Current/history queries.
- [x] Normalized errors.

## Persistence
- [x] Current version/observation pointer.
- [x] Idempotency key.
- [x] Release snapshot/reference.
- [x] No fake historical backfill.

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
- [x] Party-size invalidation to occupancy/management.

## Management
- [ ] Known/unknown coverage.
- [ ] Revenue/ticket per cover formula.
- [ ] Exclude ambiguous attribution.
- [ ] Post-release correction rebuild.

## Quality/tests
- [x] Two Tabs in one occupancy do not double covers.
- [x] Unknown is not zero/one.
- [x] Guest and staff race resolves with version conflict.
- [ ] Closing Tab does not finalize occupancy count.
- [x] Post-release correction preserves prior observation.
- [x] Ratio-of-sums calculation exact.
- [ ] Reports expose coverage percentage.

Backend release evidence: `apps/api/tests/test_party_size.py` (9 PostgreSQL tests). Current version derives from locked observation history; release snapshot/reference is preserved in release AuditEvent. Metrics helper remains unintegrated with canonical management reporting, and all operational chooser/offline UX stays open.
