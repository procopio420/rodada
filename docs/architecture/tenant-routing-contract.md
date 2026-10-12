# Public routing contract — Rodada multiestabelecimento

Updated 2026-10-12. **Design/implementation backlog, not an announcement of live domains.**

## Canonical example

The hostname names the physical Venue; URL path names an experience. Public alias `bardoaderlan` is mapped to existing internal Venue `bar-do-aderlan` through the P0 persistent VenueDomain registry; public path rollout remains gated.

| Audience | Target URL | Current internal app route |
| --- | --- | --- |
| Entry/login | `https://bardoaderlan.rodada.ai/` | `/staff` |
| Attendance companion | `https://bardoaderlan.rodada.ai/atendimento` | `/attendance` |
| Bar | `https://bardoaderlan.rodada.ai/bar` | `/bar` |
| Kitchen | `https://bardoaderlan.rodada.ai/cozinha` | `/kitchen` |
| Management | `https://bardoaderlan.rodada.ai/gerencia` | `/manage` |
| Cash | `https://bardoaderlan.rodada.ai/caixa` | `/cash` |
| Reports | `https://bardoaderlan.rodada.ai/relatorios` | `/reports` |
| Guest QR | `https://bardoaderlan.rodada.ai/m/<opaque-token>` | `/guest/<opaque-token>` |

`rodada.ai` is product marketing; `admin.rodada.ai` is future platform administration; `api.rodada.ai` is shared API infrastructure. They are not Venues.

## Trust flow

```text
HTTPS ingress (trusted Host; sanitized forwarded headers)
    -> hostname registry (unique hostname -> Venue UUID; fail closed)
    -> Next BFF/proxy (module path -> existing internal route)
    -> Django API checks:
         staff: session.venue_id == host venue_id + capability
         guest: token/session/occupancy.venue_id == host venue_id
    -> only authorized Venue business rows
```

The host does not confer auth. No client-controlled `X-Rodada-Venue`, `X-Forwarded-Host` or `venue_id` may expand access. Legacy demo paths stay while enforcing API scopes; canonical URLs only go live after binding and two-Venue negative tests.

## Hostname vs slug

`bardoaderlan.rodada.ai` is a short brand-facing alias. Existing `bar-do-aderlan` is the database slug and stays unchanged. A network of Venues may later belong to a single `Organization/Tenant`, but that is not implemented or silently implied by hostname routing.

See [ADR 0016](../adr/0016-tenant-hostname-module-paths.md) and [Spec 025](../../specs/025-tenant-host-routing/spec.md).


## P0 implementation record

The authoritative registry and signed BFF/Django host boundary are implemented; this does not publish canonical paths or DNS. Establishment page hosts are validated, staff sessions and guest credentials are constrained to their resolved Venue, and compatibility is an exact infrastructure-host allowlist. See [security/lifecycle/rollout](spec025-p0-security.md) and [Spec 025 acceptance](../../specs/025-tenant-host-routing/acceptance.md) for executed evidence and remaining gates.
