# Spec 025 — Tasks

## P0 — Prerequisites (must land before tenant URL is exposed)

- [ ] [Backend] Registry/migration: public hostname -> immutable Venue UUID; normalization, uniqueness, verified/active state, reserved labels, audit.
- [ ] [Backend] Resolver endpoint/service and negative tests; safe ingress Host trust policy.
- [ ] [Backend + Web BFF] Login host binding; reject mismatched typed venue slug; session verification on every staff endpoint, refresh and operator switch.
- [ ] [Backend] Guest QR/table token and GuestSession host/Venue binding with foreign-token 404.
- [ ] [Security] Review staff + guest + financial route scoping, SSE feeds, async jobs, PSP webhooks, idempotency and offline replay; add isolation tests.

## P1 — Compatible UI and migration

- [ ] [Web] Tenant-path rewrite matrix and navigation, keeping localhost and Railway URLs unchanged.
- [ ] [Web] Contextual login on canonical host; retain typed Venue in legacy/local mode only.
- [ ] [Web] Host-local install manifest/title/start URL and cookie/CSRF validation across two tenant domains.
- [ ] [Data] Seed public alias `bardoaderlan` against existing `bar-do-aderlan`, without mutating slug.
- [ ] [Tests] Two-Venue browser/backend E2E, wrong-host QR/credential/cookie and cross-tenant mutations.
- [ ] [Infra] Preview wildcard DNS + TLS + trusted forwarded headers; rollback plan and synthetic health checks.

## P2 — Release and followups

- [ ] Activate canary only after all P0 safety tests pass and complete a simulated turn in each of two Venues.
- [ ] Migrate customer-facing links/QR and define redirects for legacy hosts after verification; no token-in-URL handoff.
- [ ] Remove compat hosts in a separate reviewed change after usage becomes negligible.
- [ ] Plan Organization/Tenant billing + multi-Venue permissions separately, not as an implicit rename of Venue.
