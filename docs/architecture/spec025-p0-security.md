# Spec 025 P0 — authoritative Venue hosts

Implementation record, 2026-10-12. Production hostname routing remains **NO-GO** pending the preview and infrastructure acceptance gates. This change neither changes DNS nor introduces Portuguese path rewrites or migrates existing QR codes.

## Identity and lifecycle

`Venue.id` remains the operational partition. `VenueDomain.hostname` is an exact, lower-case ASCII hostname; resolution does not derive a slug or create a Venue. Only one-label `*.rodada.ai` establishment names are supported. Platform/legacy labels are reserved, and unknown, malformed, inactive and unverified mappings fail with 421. The existing `bar-do-aderlan` slug is retained. Migration 0009 maps the existing pilot when present; `seed_demo` provisions the same mapping for a newly seeded demo and never re-enables a disabled alias.

Database uniqueness, lower-case, supported-host, reserved-host, and conditional-primary constraints enforce mapping identity. A primary must be active and verified. Zero primary aliases is intentional when a Venue is disabled or not provisioned; resolution still requires a specific active, verified alias. `configure_domain` locks the Venue before changing the primary, preserving one primary under concurrent provisioning and recording before/after, actor (or system), and reason in existing AuditEvent records. Renaming/reassigning an alias is forbidden; disable it and provision a new alias. No onboarding endpoint is exposed.

Production PostgreSQL migration 0010 also audits inserts and updates (including bulk/raw SQL), rejects reassignment/rename and deletion, and rolls audit writes back with failed mutations. Database lifecycle events supplement the attributed provisioning events. SQLite retains the explicit service and model guards for local development; it does not implement this PostgreSQL trigger. Database owners can alter triggers/audit tables; restrict production database administration and retain backups/logs.

Future custom-domain verification has an explicit `is_verified` field and defaults inactive/unverified. Supporting additional domains requires a reviewed validation/constraint migration and verification workflow; setting a flag alone cannot introduce custom domains today.

## Request boundary

Django `VenueHostMiddleware` validates actual Host via `get_host`, with `USE_X_FORWARDED_HOST=False`. Next signs the actual incoming `Host` using a dedicated server secret. The assertion consists of timestamp, HTTP method, API path (without query), and original host, separated by newlines, HMAC-SHA256. Django verifies the signature with constant-time comparison and a 60-second clock window before consulting the registry. Client `X-Forwarded-Host`, `X-Rodada-Venue`, query venue IDs and slug-shaped hostname labels do not choose scope. An invalid/partial internal assertion fails with 403.

Assertions add a routing restriction, not authentication. They carry no staff or guest credential. Staff still authenticate through the existing opaque-token session and membership/device/capability mechanisms. The BFF creates headers itself and never forwards arbitrary browser identity headers. Secure the BFF/API network with private transport or HTTPS, synchronize clocks, provision a dedicated high-entropy `RODADA_BFF_HOST_SECRET` in both services and rotate it together. The assertion is not a single-use authorization token: replay within 60 seconds does not grant any credential or capability.

A request-scoped ContextVar supplies the additional Venue restriction to existing authentication and guest authorization services and is reset even on failure. `_session_failure` enforces `VENUE_HOST_MISMATCH` (403) before token rotation, operator switch and protected commands. Login verifies the selected Venue before issuing a session. SSE captures the resolved hostname and re-resolves it on every authorization poll beyond middleware teardown; disabling an alias or revoking a session terminates the feed. Cursors remain Venue-qualified.

## Explicit compatibility

`RODADA_HOST_COMPATIBILITY_HOSTS` is an exact comma-separated infrastructure/legacy-host allowlist, not a default Venue. Default local development permits `localhost` and `127.0.0.1` (ports allowed); tests explicitly add Django's `testserver`. Establishment subdomains and wildcards cannot enter this allowlist. Production settings require this variable explicitly, even if empty, and require a separate BFF secret. Use `api.rodada.ai` as an explicitly provisioned native/API transport: Android keeps authorized `venue_slug` selection and membership scoping.

The isolated Railway demonstration startup explicitly permits its actual `RAILWAY_PUBLIC_DOMAIN` (existing fixed demo hostname as fallback), plus loopback transport, and generates an internal per-start secret if none was provisioned. It still uses the demo profile and existing paths. No Railway deployment was performed by this PR. A multi-process/multi-replica production deployment must provision a common secret; independently generated secrets are only suitable for the existing single-container demonstration.

Ingress must preserve original Host and sanitize forwarding headers. The existing Railway nginx preserves Host, overwrites forwarded host/proto, and exposes only Next. Host itself does not authenticate an establishment: callers can select a host, but only that host's authorized credentials can access its data. Next validates establishment page hosts through the signed public `/venue/host/` endpoint and rejects unknown/unsupported page hosts. Static infrastructure paths remain exempt; their business-data BFF endpoints still enforce the Django boundary. Next's legacy surface selection remains unchanged; canonical path rewrites are deliberately deferred.

## Browser credentials

Existing staff cookies remain host-only, HttpOnly, Secure in production and SameSite=Lax. Refresh coordination keys now include Host as well as the refresh credential so a cached rotation from host A cannot satisfy host B. CSRF compares Origin against actual Host and rejects cross-origin Fetch Metadata; forwarded host is not used.

Guest BFF authorization moves out of sessionStorage into host-only, HttpOnly, SameSite=Lax cookies, Secure in production, keyed by a hash of the public QR selector. Multiple QR contexts on one host do not overwrite each other's credentials. Browser `X-Guest-Session` contains only the public QR selector; Django receives the secret from the matching cookie. Resolve responses substitute the selector for the opaque authorization, and the component removes legacy sessionStorage credentials. Existing request-intent IDs and cached public menu data are not credentials. No staff/guest credentials are transferred in redirect query parameters.

Foreign QR and GuestSession credentials are rejected with indistinguishable 404 responses. Existing occupancy generation, release/revocation and Tab ownership checks remain authoritative. Anonymous receipt and published-icon routes also enforce resolved Venue restrictions.

## Scope audit

| Area | Existing authoritative scope reviewed | P0 enforcement/evidence |
| --- | --- | --- |
| Access | membership/session/device Venue, capabilities, recovery originating session | common session guard, login/refresh/switch/reauth/invalidation tests |
| Ordering / Catalog | actor Venue, Tab ownership, Product Venue and customization ownership before confirmation/replay | foreign IDs, products and offline/idempotency tests; icon host scoping added |
| Hospitality / Guest | table Venue, active occupancy, access generation and session Tab | common guest guard; foreign QR/session and real release tests |
| Ledger / Payments | scoped locked Tab/Payment/Refund; financial idempotency per resource; PSP account/signature/evidence | foreign payment/refund tests; financial rules/provider integration unchanged |
| Cash | scoped cash point/shift/movements and replay recovery | foreign drawer/shift reads and supply mutations tested |
| Management / Audit | reports by request session Venue; alerts/policies scoped; events by Venue | foreign session/membership mutation and audit filtering tested |
| Realtime / Recovery | Venue-qualified cursor/outbox; replay authorization reloads current session capabilities | foreign cursor reset, host mismatch and open-feed domain revocation tests |
| Jobs / callbacks | existing explicit Venue/account references, not HTTP browser tenant headers | reviewed existing ports; live PSP/worker multi-merchant E2E not claimed |

There is no PostgreSQL row-level security or platform cross-Venue authority added. Service/background-job callers must continue providing an authorized ActorContext or authenticated provider evidence. Existing provider callbacks are infrastructure flows scoped by verified provider account/event and are not authorized by a browser Host.

## Rollout and rollback

Keep the canonical-path/wildcard rollout gate closed. Before a separate promotion: deploy the reviewed commit to disposable two-Venue preview; provision explicit ingress/API/compatibility hosts and shared secret; verify DNS/TLS/Host preservation, browser host-only behavior on actual sibling HTTPS domains, Android native flows and a full independent shift on each Venue. CI and local application tests do not certify DNS, TLS or live payment-provider onboarding.

Rollback routing by retaining current URLs and disabling the affected domain through `configure_domain` with a reason. Do not rename Venue slugs or delete audit/domain identity. Migration 0009 reverse is intentionally a no-op, preserving provisioned identity/audit; a full schema rollback requires reviewing dependencies and disabling routing first. Migration 0010 reverses its trigger/function. Existing session revocation and refresh coordination remain authoritative.
