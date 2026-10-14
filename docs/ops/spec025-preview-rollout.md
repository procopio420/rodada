# Spec 025 — Preview, evidence and rollback

Status: prepared, **not activated**. Requires P0 isolation gates and passing CI before exposing wildcard traffic.

## Shared deployment

All venues use one Railway deployment: Next.js (public module URLs) + Django API + one PostgreSQL.
Hostname (verified in `VenueDomain`) resolves to an immutable Venue UUID. Never create a Railway project/database per venue.
Do not equate `Venue.slug` with the hostname label.

## Canary rollout

1. Run API/Web/Docker/isolated-shift CI for PR #116. Run the two-Venue browser+BFF integration suite (`apps/web/tests/integration/tenant-hosts.spec.ts`).
2. Provision the pilot hostname using the existing `0009_pilot_hostname` migration; confirm the row maps to `Venue.slug=bar-do-aderlan`, `is_active=true`, `is_verified=true`. Check that no existing hostname was reassigned.
3. In a **separate preview environment** configure a wildcard CNAME for `*.rodada.bar` to the single app ingress (do not enable Cloudflare proxy until TLS strategy is verified). Configure an eligible wildcard certificate / TLS termination in the ingress. A wildcard DNS entry **does not** provision VenueDomain rows.
4. Configure `RODADA_BFF_HOST_SECRET` in the shared Next/Django runtime (never `NEXT_PUBLIC_*`); configure accepted Host names in Django ingress, preserving localhost and Railway compatibility. Strip incoming `X-Rodada-Bff-*`, `X-Forwarded-Host`, and untrusted forward headers at edge; inject trusted forwarding metadata only. If proxy and app do not agree on Host authority, stop.
5. Set `RODADA_ENABLE_TENANT_HOST_UI=true` **only in preview**, and verify both seeded venues and an unregistered host using `scripts/verify-tenant-host-preview.sh`. Check GET/POST, login/refresh/logout/operator switch, QR/catalog/order, SSE and payments with different identities.
6. Verify host-only Secure/HttpOnly staff and guest cookies, no `Domain=.rodada.bar`, per-host PWA title/manifest and cross-origin CSRF rejection.
7. Activate pilot canary only after complete simulated shift and P0 sign-off; keep `rodada.bar`, original Railway paths, and old mobile behavior intact.

## Backout

- Disable `RODADA_ENABLE_TENANT_HOST_UI` (or set `false`): non-pilot venue hosts return HTTP 421 at the Next edge.
- Remove preview wildcard routing / revoke preview aliases if any isolation anomaly appears. Keep existing hostname records for audit; prefer disabling `VenueDomain.is_active` over deleting/reassigning identity.
- Roll back application deploy to last known stable build, preserving DB schema/migrations (no destructive rollback).
- Validate Railway hostname and /health, /ready, /staff, login and Aderlan staff sessions on the stable deployment.
- Do not redirect guest QR tokens between domains or copy authentication cookies to new hosts.

## Observable evidence

`PREVIEW_TENANT_HOST=e2ea.rodada.bar PREVIEW_UNKNOWN_HOST=unregistered-preview.rodada.bar bash scripts/verify-tenant-host-preview.sh`
requires publicly resolvable HTTPS and valid certificate, otherwise **fails** (does not claim success). Store output, workflow URL and manifest response in release notes. No DNS/TLS provisioning is implied by this document.
