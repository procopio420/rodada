# Spec 025 — Implementation plan

**Current state (2026-10-12): contract only.** Current Web entrypoints use `surfaceForHost` selecting module on `cozinha.rodada.ai` / `gerencia.rodada.ai`. Next proxy rewrites legacy root/guest paths. Django Venue has unique `slug`, but no public host mapping; sessions are scoped by Venue and Web login still accepts a typed venue slug.

## Slice 1 — Identity and host registry (backend first)

- Create `venue.VenueDomain` or an equivalent registry: unique normalized hostname, FK Venue, primary/canonical marker, active/verified status, audited lifecycle; reserve platform/legacy labels. No automatic Venue creation from a Host.
- Implement trusted hostname resolution in API/BFF, with explicit development/Railway compatibility mode. Unknown/invalid/disabled host yields fail-closed response, not `public` or seed fallback.
- Add migrations and negative unit tests including DNS lookalikes, header spoof, reserved labels, aliases and conflicts.
- Seed the pilot public host `bardoaderlan.rodada.ai` as alias to existing `bar-do-aderlan`; **do not rename Venue.slug**.

## Slice 2 — Security binding (blocker for enabling new routing)

- Bind authenticated staff requests, login, refresh and switch-operator to resolved Venue; API rechecks membership/capability. Reject cross-host session with `VENUE_HOST_MISMATCH` 403.
- Preserve BFF server-only bearer handling and host-only session cookies. Verify logout/refresh deletes only the originating host cookies.
- Bind guest QR, active guest session and table generation to the resolved Venue; foreign QR -> not found.
- Verify SSE, offline replay/idempotency, report queries, cash/payment handlers and workers remain venue-scoped. Fix any discovered cross-tenant access before deployment.

## Slice 3 — Public path routing and tenant UI context

- In Next `proxy.ts`, translate public PT-BR paths to internal routes only after trusted host resolution; keep current local entrypoints. Preserve nested paths, query parameters, POST semantics, static assets and BFF endpoints.
- Make tenant app manifest/title and navigation context-aware. Avoid a generic role-only frontend and avoid exposing unimplemented links.
- Login on a canonical tenant hostname identifies the Venue automatically, removing the editable establishment field there; legacy localhost/Railway keeps it while migrating.
- Android retains explicit authorized Venue selection (not a browser Host).

## Slice 4 — E2E rollout

- Two-Venue matrix: staff A/B, guest A/B, all modules, reads and mutations, concurrent shifts, SSE reconnect, token rotation, guessed IDs, idempotency and payment boundaries.
- Canary in preview behind rollout flag; confirm HTTPS wildcard/routing and logs. Do not modify existing Railway demo until the canary passes.
- Refresh public links and QR only after safe host binding; monitor failures, retain rollback to legacy paths.
- Later: custom verified domains and real multi-venue Organization/Tenant billing under separate spec.

## Release gates

- **NO-GO** if host can choose another Venue, if guest token works under another host, if staff cookies are domain-wide, or if a new hostname routes to default demo.
- **NO-GO** if DNS, HTTPS, payments, SSE or data isolation are only assumed instead of tested.
- Feature complete != production-ready. Keep a separate audit trail for any preexisting cross-tenant issues discovered.
