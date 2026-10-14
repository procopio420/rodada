# Spec 025 — Preview, evidence and rollback

Status: prepared, **not activated**. Requires P0 isolation gates and passing CI before exposing wildcard traffic.

Checkpoint 2026-10-14: [audit #130](../../specs/025-tenant-host-routing/audit-130-evidence.md)
has local PostgreSQL/code-review evidence, but actual preview remains **BLOCKED**.
The probe for `e2ea.rodada.bar` returned HTTP421 at the manifest (exit22).
[#151](https://github.com/procopio420/rodada/issues/151) tracks ingress/Host/HMAC
proof and still blocks #130; [#152](https://github.com/procopio420/rodada/issues/152)
tracks later canary/backout. These tickets do not authorize DNS/deployment.

## Shared deployment

All venues use one Railway deployment: Next.js (public module URLs) + Django API + one PostgreSQL.
Hostname (verified in `VenueDomain`) resolves to an immutable Venue UUID. Never create a Railway project/database per venue.
Do not equate `Venue.slug` with the hostname label.

## Canary rollout

1. Run API/Web/Docker/isolated-shift CI for PR #116. Run the two-Venue browser+BFF integration suite (`apps/web/tests/integration/tenant-hosts.spec.ts`).
2. Provision the pilot hostname using the existing `0009_pilot_hostname` migration; confirm the row maps to `Venue.slug=bar-do-aderlan`, `is_active=true`, `is_verified=true`. Check that no existing hostname was reassigned.
3. In a **separate preview environment** configure a wildcard CNAME for `*.rodada.bar` to the single app ingress (do not enable Cloudflare proxy until TLS strategy is verified). Configure an eligible wildcard certificate / TLS termination in the ingress. A wildcard DNS entry **does not** provision VenueDomain rows.
4. Configure `RODADA_BFF_HOST_SECRET` in the shared Next/Django runtime (never `NEXT_PUBLIC_*`); configure accepted Host names in Django ingress, preserving localhost and Railway compatibility. Strip incoming `X-Rodada-Bff-*`, `X-Forwarded-Host`, and untrusted forward headers at edge; inject trusted forwarding metadata only. If proxy and app do not agree on Host authority, stop.
   Production profile and Railway `pilot` preflight now reject absent/short/repetitive
   BFF secrets before DB contact. Generate at least32 characters cryptographically,
   independent of Django secret, provision in secret manager, confirm validation
   without printing values. Railway does not automatically select `settings_production`;
   do not claim its full settings apply just because pilot preflight passed.
5. Set `RODADA_ENABLE_TENANT_HOST_UI=true` **only in preview**, and verify both seeded venues and an unregistered host using `scripts/verify-tenant-host-preview.sh`. Check GET/POST, login/refresh/logout/operator switch, QR/catalog/order, SSE and payments with different identities.
6. Verify host-only Secure/HttpOnly staff and guest cookies, no `Domain=.rodada.bar`, per-host PWA title/manifest and cross-origin CSRF rejection.
7. Activate pilot canary only after complete simulated shift and P0 sign-off; keep `rodada.bar`, original Railway paths, and old mobile behavior intact.

## Required preview evidence

Run the HTTPS script for **both** A and B and the unknown host on the identified
preview deployment SHA. Attach sanitized results for DNS/TLS, actual Host received
at each hop, external-header stripping, BFF signature freshness/path/method rejection,
host-only Secure/HttpOnly cookies, login/refresh/QR/critical commands, SSE reconnect
and active domain/session revocation. Local Host headers plus real PostgreSQL do
not exercise a real ingress. Never record secret/cookie/token values in artifacts.
Published icon GETs and valid shared receipt capabilities remain portable; negative
cross-host auth/financial tests must not treat those intentional public reads as IDOR.

Exercise preview backout and record its SHA, health/legacy/native smoke and
preserved schema/UUID/QR. Disabling a domain must terminate its active streams;
disabling the UI flag alone is not session revocation. Do not delete/reassign domain
identity or reset an operational DB to simulate rollback.

## Backout

- Disable `RODADA_ENABLE_TENANT_HOST_UI` (or set `false`): non-pilot venue hosts return HTTP 421 at the Next edge.
- Remove preview wildcard routing / revoke preview aliases if any isolation anomaly appears. Keep existing hostname records for audit; prefer disabling `VenueDomain.is_active` over deleting/reassigning identity.
- Roll back application deploy to last known stable build, preserving DB schema/migrations (no destructive rollback).
- Validate Railway hostname and /health, /ready, /staff, login and Aderlan staff sessions on the stable deployment.
- Do not redirect guest QR tokens between domains or copy authentication cookies to new hosts.

## Observable evidence

`PREVIEW_TENANT_HOST=e2ea.rodada.bar PREVIEW_UNKNOWN_HOST=unregistered-preview.rodada.bar bash scripts/verify-tenant-host-preview.sh`
requires publicly resolvable HTTPS and valid certificate, otherwise **fails** (does not claim success). Store output, workflow URL and manifest response in release notes. No DNS/TLS provisioning is implied by this document.
