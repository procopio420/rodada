# Spec 025 — Tasks

## P0 — Prerequisites (must land before tenant URL is exposed)

- [x] [Backend] Registry/migration: public hostname -> immutable Venue UUID; normalization, uniqueness, verified/active state, reserved labels, audit.
- [x] [Backend] Resolver endpoint/service and negative tests; safe ingress Host trust policy.
- [x] [Backend + Web BFF] Login host binding; reject mismatched typed venue slug; session verification on every staff endpoint, refresh and operator switch.
- [x] [Backend] Guest QR/table token and GuestSession host/Venue binding with foreign-token 404.
- [x] [Security] Review staff + guest + financial route scoping, SSE feeds, async jobs, PSP webhooks, idempotency and offline replay; add isolation tests.

## P1 — Compatible UI and migration

- [ ] [Web] Tenant-path rewrite matrix and navigation, keeping localhost and Railway URLs unchanged.
- [ ] [Web] Contextual login on canonical host; retain typed Venue in legacy/local mode only.
- [ ] [Web] Host-local install manifest/title/start URL and cookie/CSRF validation across two tenant domains.
- [x] [Data] Seed public alias `bardoaderlan` against existing `bar-do-aderlan`, without mutating slug.
- [ ] [Tests] Two-Venue browser/backend E2E, wrong-host QR/credential/cookie and cross-tenant mutations.
- [ ] [Infra] Preview wildcard DNS + TLS + trusted forwarded headers; rollback plan and synthetic health checks.

## P2 — Release and followups

- [ ] Activate canary only after all P0 safety tests pass and complete a simulated turn in each of two Venues.
- [ ] Migrate customer-facing links/QR and define redirects for legacy hosts after verification; no token-in-URL handoff.
- [ ] Remove compat hosts in a separate reviewed change after usage becomes negligible.
- [ ] Plan Organization/Tenant billing + multi-Venue permissions separately, not as an implicit rename of Venue.


## P0 evidence — 2026-10-12

Registry/migrations, fail-closed resolver, HMAC BFF boundary, staff/guest/SSE guards and two-Venue negative tests are delivered. Full PostgreSQL validation: **577 passed**, plus **43 passed** in the final focused security/migration run, including the migration callable and new/repeated demo seed. Web typecheck/build, refresh/realtime unit checks and relevant real API integrations passed; see [acceptance.md](acceptance.md) for exact commands/results.

The browser/backend test task under P1 is **PARTIAL**: real BFF requests and local browser workflows are tested, but actual sibling-domain HTTPS, preview ingress and live Railway promotion are not. Metadata/login UI and Portuguese public path rewrite tasks remain **MISSING** in this P0. Infrastructure promotion is **EXTERNAL_BLOCKED**. No wildcard, canonical redirects or QR migration were activated.
