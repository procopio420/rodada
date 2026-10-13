# Spec 025 — Acceptance criteria

All items below are **PENDING**, not implementation claims. Evidence: test command + file + CI/deploy result when available.

## Host mapping and DNS

- [ ] A `VenueDomain`-equivalent, unique and audited registry resolves `bardoaderlan.rodada.bar` to the seeded Venue ID whose slug remains `bar-do-aderlan`.
- [ ] Reserved hostnames cannot be claimed; unrecognized/disabled/lookalike/invalid hostnames fail closed (404 or 421), with no default/demo fallback.
- [ ] Reverse proxy and application agree on the normalized trusted Host. Browser-supplied `X-Forwarded-Host`, `X-Rodada-*` or `?venue=` cannot choose a different Venue.

## Navigation

- [ ] `/cozinha`, `/gerencia`, `/caixa`, `/bar`, `/atendimento`, `/relatorios`, and `/m/:token` resolve to existing modules on the same Venue hostname; paths, subpaths, query strings, methods, assets and SSE survive.
- [ ] Per-host app manifest/title/start URL is correct; authenticated navigation never changes hostname unexpectedly.
- [ ] Root/legacy hosts and Railway/local demonstration paths continue functioning; existing Android flows remain intact.

## Authorization and isolation

- [ ] Login on host A cannot authenticate venue B even with a valid B operator/PIN, and never sets B's staff cookie on A.
- [ ] Staff session from host A replayed on B yields 403 `VENUE_HOST_MISMATCH`; both reads and writes fail before any B data is returned/changed.
- [ ] Token refresh, operator switch and restored browser session cannot bypass host/session Venue binding.
- [ ] Cookies are host-only, secure in production, httpOnly (where applicable), and cannot be read/reused by sibling tenant host through domain scope.
- [ ] Guest QR/guest session valid on A is rejected on B without exposing the existence of the token (404); stale QR remains invalid after occupancy generation changes.
- [ ] Guessed foreign IDs on ordering, payments, refunds, cash, catalog, management and table endpoints cannot read or mutate another Venue.
- [ ] SSE/cursor/outbox, retry/idempotency/offline replay, audit and provider callbacks show tenant partitioning in positive and negative tests.
- [ ] Two independently seeded Venues can run end-to-end in parallel, without cross-tenant state leakage.

## Operational

- [ ] Wildcard HTTPS, Host routing, explicit app/DB trust boundaries and logging are configured in preview and verified (not inferred).
- [ ] Switch-on is behind a documented rollback gate; no unsupported production readiness claim.

## Staged P1 evidence (not release approval)

- [ ] `npm run test:tenant` — path/host unit regression, `apps/web/tests/tenant-routing.test.mjs` (CI result required).
- [ ] `npm run test:integration` — independent Venues in `start_api.py`, BFF + Django assertions in `tenant-hosts.spec.ts` (CI result required).
- [ ] `bash scripts/verify-tenant-host-preview.sh` — preview wildcard HTTPS, manifest, reserved/unknown host and health (real DNS/TLS not yet configured).
- [ ] Aderlan shift and P0 safety gates on PR #116, followed by manual operator/QR browser verification and canary approval.
