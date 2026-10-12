# Tasks — Spec 013

## Initial Web pilot setup — 2026-10-10
- [x] Table/zone setup using existing APIs and ambiguous-create guard.
- [x] Existing staff membership role/status editing with PIN/version/conflict.
- [x] Shared mobile/a11y checks and real API evidence.

## B1 slice — implementation awaiting verification
- [ ] Execute station blocker, stale preview, authorization and audit tests.
- [ ] Execute PostgreSQL concurrent-manager and order/deactivation race tests.
- [ ] Integrate station routes and run migration drift checks on complete source.
- [ ] Add management preview/apply UI with queue links and offline feedback.

## B2 slice — implementation awaiting verification
- [ ] Register management/guest-policy/ query and PATCH routes.
- [ ] Execute global guest-switch tests plus existing guest/service regressions in PostgreSQL.
- [ ] Validate integrated migration drift and CI.
- [ ] Add manager emergency switch UI and guest policy feedback.

## Domain/API
- [ ] Define typed VenueProfile/Operations policy fields.
- [ ] Define safe-change mode contract.
- [ ] Define config version/effective-at response.
- [ ] Staff management orchestration to Spec 008.
- [ ] Station config commands.
- [ ] Zone/ServicePoint/Table/FloorPlan config commands.
- [ ] Guest policy config.
- [ ] Business date cutoff config.
- [ ] Optional operating hours.
- [ ] Service charge policy config.
- [ ] SLA/alert threshold config.
- [ ] Payment provider binding config.
- [ ] Printer endpoint + station binding configuration via Spec 015 contracts.
- [ ] Catalog defaults.
- [ ] Named feature switches only.
- [ ] Validate/preview impacted active resources.

## Persistence
- [ ] Typed policy/version storage.
- [ ] Configuration change/audit projection.
- [ ] Provider binding references without raw secrets.
- [ ] Backward-compatible defaults migration.

## Staff Web/PWA
- [ ] Gerência mobile config IA.
- [ ] Venue profile.
- [ ] Floor/production config.
- [ ] Guest config.
- [ ] Pricing/service config.
- [ ] Alert/SLA config.
- [ ] Payment provider status/setup.
- [ ] Printer endpoints/bindings/status.
- [ ] Staff/device entry points.
- [ ] Effective-now/next-context/blocker messaging.

## Android
- [ ] Consume config/capabilities; no broad admin UI required.
- [ ] Refresh capability/provider availability on invalidation.

## Guest
- [ ] Consume only sanitized published guest policy.
- [ ] Never expose internal thresholds/secrets.

## Realtime
- [ ] Typed config invalidation.
- [ ] Clients re-fetch canonical config.
- [ ] No secret content in events.

## Management
- [ ] Configuration change timeline.
- [ ] Surface pending effective changes.
- [ ] Active blocker drill-down.

## Infra/integration
- [ ] Secret storage/rotation path for payment adapters.
- [ ] Provider connection health/capability check.

## Quality/tests
- [ ] No arbitrary key/value bypass.
- [ ] Concurrent edit conflict.
- [ ] Provider disable blocked by pending payment.
- [ ] Station deactivate blocked by active queue.
- [ ] Historical business dates unchanged after cutoff/timezone change.
- [ ] Secret redaction tests.
- [ ] Manager cannot self-escalate.

