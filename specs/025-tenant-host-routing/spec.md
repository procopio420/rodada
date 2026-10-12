# Spec 025 — Tenant hostname and module paths

**Status:** P0 implemented and security-tested; canonical paths and production routing gated
**Date:** 2026-10-12
**Architecture:** [ADR 0016](../../docs/adr/0016-tenant-hostname-module-paths.md)

## Problem / Outcome

Public URLs currently encode the surface (`cozinha.rodada.ai`), but Rodada must expose many establishments from one deployment with the establishment encoded in hostname and the module in pathname.

Expected pilot URL: `https://bardoaderlan.rodada.ai/cozinha`. The existing seed's `Venue.slug` is `bar-do-aderlan`; their equality is explicitly **not** assumed.

## Scope

- A persistent, authoritative, unique mapping from normalized public hostname to Venue ID; reserved host registry and lifecycle.
- Safe Host resolution at a trusted boundary; unknown host fails closed.
- Web same-origin URLs `/`, `/atendimento`, `/bar`, `/cozinha`, `/gerencia`, `/caixa`, `/relatorios`, `/m/:token`.
- Host-aware login, staff session, refresh, protected BFF/HTTP, SSE and guest flows.
- Host-only browser cookies and per-Venue install metadata.
- Single shared deployment, staged rollout, two-Venue isolation verification.
- Compatibility of current Railway / localhost paths, existing Android identity selection, all canonical backend domain commands and local-demo credentials.

## Non-goals in this slice

- Introducing real multi-Venue Organization/Tenant billing or cross-unit permissions.
- Rewriting Bar/Cozinha/Gerência React UI, or replacing native Android.
- Splitting into per-tenant infrastructure or databases.
- Enabling custom domains, but preserve model space for verified domains.
- Changing payment providers or any financial rules.
- Publishing a new route merely because a pathname appears in this spec (e.g. `/configuracoes`).

## Domain contract

`Venue.id` (UUID) is the authoritative operational partition key. A distinct public host alias maps to one Venue; many host aliases may exist per Venue only when intentional, canonical URL selected and audited. `Venue.slug` remains internal/stable. A hostname is *never* used directly as database filter on business tables. Unknown or disabled venue/alias returns 404/421 without falling back to first/default venue.

A future `Tenant/Organization` can own multiple Venues, but each financial, fulfillment and permission boundary stays explicit on Venue until a separately accepted contract changes it.

## Public routing

| Public path | Existing route | Access |
| --- | --- | --- |
| `/` | `/staff` | staff landing/login |
| `/atendimento` | `/attendance` | staff |
| `/bar` | `/bar` | staff with capability |
| `/cozinha` | `/kitchen` | staff with capability |
| `/gerencia` | `/manage` | staff/manager capabilities |
| `/caixa` | `/cash` | staff with capability |
| `/relatorios` | `/reports` | reporting capability |
| `/m/:opaqueToken` | `/guest/:opaqueToken` | scoped guest authorization |

Internal URLs remain compatible; anonymous public requests cannot read staff data. Preserve nested paths, method semantics, query strings and RSC/assets. Ensure scoped client-side navigation never accidentally falls back to internal unprefixed host or another Venue.

## Authentication / tenancy

- Login on canonical hostname must not let the caller substitute a different `venue_slug`. The BFF resolves host to Venue, validates the login against it, and obtains a venue-bound session. Existing `venue_slug` login field may remain only on legacy/local hosts during migration.
- On every staff BFF route and corresponding backend command, verify venue of session matches resolved host Venue. No UI-only check.
- Session refresh and operator switch cannot change Venue behind the current hostname.
- Each QR token, GuestSession and all guest reads/writes must belong to resolved host's Venue, including after table release / generation reset.
- SSE reconnect/cursor, offline replay, idempotency, POS/Pix/Tap provider callbacks and cash reconciliation must be partitioned by Venue. Inbound PSP webhook identity is provider account/event, not arbitrary browser Host.
- Reject spoofed forwarded headers, host-looking URL parameters, cross-tenant IDs and custom domains that have not been verified.
- Hosts reserved by platform and legacy (including `api`, `admin`, `www`, `bar`, `cozinha`, `cliente`, `gerencia`, `atendimento`, `pedido`, `app`) cannot be claimed as Venue labels.

## Rollout guardrails

The first PR may document the contract and add pure lookup scaffolding, but **must not turn on tenant-host routing until backend host/session and guest checks have proven isolation**. Staging canary first, with two Venues and negative cross-tenant tests. Do not redirect canonical domains or regenerate/republish guest QR before this gate passes.

## Evidence

See [acceptance.md](acceptance.md) for verifiable assertions, [plan.md](plan.md) for slices, [tasks.md](tasks.md) for actions. Keep criteria pending until reproducible test evidence exists.


## P0 implementation boundary (2026-10-12)

The first implementation adds VenueDomain, an audited provisioning service and PostgreSQL lifecycle protection, an authoritative resolver, signed BFF host assertions, common staff/guest guards and host validation for establishment pages. It preserves the current paths. The BFF adds a host restriction to the existing opaque-token authentication system; it does not introduce another identity system.

Compatibility hosts are exact infrastructure/legacy names configured explicitly, with loopback defaults only for development. Production configuration requires an explicit compatibility list and dedicated BFF secret. Venue subdomains cannot be configured as compatibility transports. Guest authorization is held in per-QR host-only HttpOnly cookies, and unknown/foreign guest authorization has indistinguishable 404 behavior on establishment hosts.

The rollout gate remains closed for Portuguese path rewrites, tenant-specific manifests/titles, wildcard DNS/TLS, production hostname promotion and QR migration. See [P0 security contract](../../docs/architecture/spec025-p0-security.md) and the criterion-by-criterion [acceptance record](acceptance.md). Custom-domain onboarding and Organization/Tenant billing remain out of scope.
