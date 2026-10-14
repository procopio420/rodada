# Spec 025 — Tasks

## P0 — Prerequisites (must land before tenant URL is exposed)

- [ ] [Backend] Registry/migration: public hostname -> immutable Venue UUID; normalization, uniqueness, verified/active state, reserved labels, audit.
- [ ] [Backend] Resolver endpoint/service and negative tests; safe ingress Host trust policy.
- [ ] [Backend + Web BFF] Login host binding; reject mismatched typed venue slug; session verification on every staff endpoint, refresh and operator switch.
- [ ] [Backend] Guest QR/table token and GuestSession host/Venue binding with foreign-token 404.
- [ ] [Security] Review staff + guest + financial route scoping, SSE feeds, async jobs, PSP webhooks, idempotency and offline replay; add isolation tests.

## P1 — Compatible UI and migration

- [x] [Web] Tenant-path rewrite matrix and navigation, keeping localhost and Railway URLs unchanged (PR #116 code; CI pending).
- [x] [Web] Contextual login on canonical host; retain typed Venue in legacy/local mode only (PR #116 code; CI pending).
- [x] [Web] Host-local install manifest/title/start URL and cookie/CSRF tests for two venue domains (PR #116 code; CI pending).
- [x] [Data] Migration added to map public alias `bardoaderlan.rodada.bar` to existing `bar-do-aderlan`; applying/validating on Railway is pending.
- [x] [Tests] Automated two-Venue Next BFF/Django HTTP E2E added: wrong-host QR, credentials, cookies, refresh and mutation (CI green still required).
- [ ] [Infra] Actual preview wildcard DNS + TLS and trusted ingress headers not yet provisioned/verified. Rollback runbook and synthetic health script implemented in `docs/ops/spec025-preview-rollout.md` and `scripts/verify-tenant-host-preview.sh`.

## P2 — Release and followups

- [ ] Activate canary only after all P0 safety tests pass and complete a simulated turn in each of two Venues.
- [ ] Migrate customer-facing links/QR and define redirects for legacy hosts after verification; no token-in-URL handoff.
- [ ] Remove compat hosts in a separate reviewed change after usage becomes negligible.
- [ ] Plan Organization/Tenant billing + multi-Venue permissions separately, not as an implicit rename of Venue.

## Visual follow-up — Establishment home

- [x] [Web branch] Build approved-brand header and icon-based launcher with 2 mobile / 3 tablet / 4 desktop columns.
- [x] [Web branch] Add two-Venue browser integration assertions for branding, links, breakpoints and overflow.
- [ ] [QA] Run Web CI and inspect rendered browser screenshots at 360/390/430, 768 and 1280+ before merge/deploy.
