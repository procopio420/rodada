# Spec 025 — Tenant hostname and module paths

**Status:** PR #116 MERGEADO na main em 13/10 (código P0/P1); #131 e #140 integrados. #101 fechado sem merge. Auditoria #130 em execução; aceite integrado, DNS/TLS wildcard e ativação pública ainda NÃO HOMOLOGADOS.
**Date:** 2026-10-12
**Architecture:** [ADR 0016](../../docs/adr/0016-tenant-hostname-module-paths.md), [ADR 0018](../../docs/adr/0018-rodada-bar-canonical-domain.md)

## Problem / Outcome

Public URLs currently encode the surface (`cozinha.rodada.bar`), but Rodada must expose many establishments from one deployment with the establishment encoded in hostname and the module in pathname.

Expected pilot URL: `https://bardoaderlan.rodada.bar/cozinha`. The existing seed's `Venue.slug` is `bar-do-aderlan`; their equality is explicitly **not** assumed.

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

For a controlled activation on the existing shared Railway runtime, demo startup
must support explicitly disabling automatic seed/provisioning. Enabling tenant
UI while automatic demo seeding remains enabled must fail preflight before
database contact; a strong explicitly provisioned BFF secret is also required.
This preserves pilot credentials, permissions and guest policy across restart.
It does not authorize activation, bypass the separate-preview acceptance gate,
or change operational payment simulation globally.

The first PR may document the contract and add pure lookup scaffolding, but **must not turn on tenant-host routing until backend host/session and guest checks have proven isolation**. Staging canary first, with two Venues and negative cross-tenant tests. Do not redirect canonical domains or regenerate/republish guest QR before this gate passes.

## Evidence

See [acceptance.md](acceptance.md) for verifiable assertions, [plan.md](plan.md) for slices, [tasks.md](tasks.md) for actions. Keep criteria pending until reproducible test evidence exists.

## Public capabilities and production hardening — audit #130

Published icon bytes are intentionally public and portable across hosts. Only the
current `published_asset` and exact filename are served; authenticated management
remains Venue-scoped. Previously distributed immutable-cache bytes cannot be
made confidential by removing the origin reference.

A shared receipt is a portable, read-only bearer capability for one customer
document, valid for 24 hours and revocable. It can reveal that document's intended
snapshot across hosts, but grants no staff, mutation or printing authority.
Invalid/expired/revoked tokens return 404. Production tickets are not shareable.

Production and Railway pilot preflight reject missing, short or repetitive BFF
secrets before startup/database mutation. Provision a cryptographically generated,
independent secret; length/diversity checks are a minimum, not proof of entropy.
Signed authorities require valid hostname/port syntax, authoritative tenant
registry or explicitly accepted compatibility host. The optional refund reason
normalizes to an empty string before invoking the scoped financial service.

See [audit-130-evidence.md](audit-130-evidence.md) for tests, trust matrix and
limitations. Security audit completion does not authorize wildcard/canary.

## 2026-10-13 — Adaptation and incremental delivery

- Public canonical domain is now `rodada.bar` (replaces the earlier planned `rodada.ai`).
- `bardoaderlan.rodada.bar/` is the five-module entry hub: Atendimento, Cozinha, Bar, Caixa, Gerência.
- First UI slice only recognizes the literal pilot host to display navigation. Existing routes and login remain intact. This is **not** hostname-to-Venue resolution and confers no access.
- Do not enable wildcard DNS or claim multi-tenant isolation until registry, API/BFF session binding, guest checks, permissions and two-Venue negative tests pass.
- Existing internal module URLs remain linked during migration; canonical Portuguese paths are a later slice.

## 2026-10-13 — P1 implementation via PR #116 (mergeado, não homologado)

- The PR #110 alias rewrite matrix has been ported and extended to all verified tenant hosts once `RODADA_ENABLE_TENANT_HOST_UI=true` is enabled. The pilot host remains the default canary.
- Contextual BFF login resolves the authoritative Django `VenueDomain`, and rejects a typed slug mismatch. The login UI hides the slug field only when the signed host is resolved.
- Tenant metadata, PWA manifest and guest page title use the verified Venue name; legacy/root hosts retain existing metadata, routes and typed login.
- Browser+BFF integration fixtures seed two distinct Venues only in the isolated test database. Tests cover wrong-host cookies, login, guest QR, refresh and mutation denial.
- Preview DNS/TLS, end-to-end shift, P0 security review and final rollout remain external gates. Do not describe this PR as deployed or multi-tenant-ready before validation.

## 2026-10-13 — Visual refinement: establishment module launcher

The verified tenant root `/` is an operational module launcher, not a new login mechanism. Show the approved Rodada wordmark alongside the **server-resolved** Venue name and a persistent, accessible `/staff` link to enter or switch operators. The navigation contains exactly five already-existing destinations: Atendimento (`/atendimento`), Cozinha (`/cozinha`), Bar (`/bar`), Caixa (`/caixa`), Gerência (`/gerencia`). Each card exposes its label, a distinct operational icon and a short description; the entire card is a touch-sized link.

The grid is **2 columns below 768px**, **3 columns from 768px to 1099px** and **4 columns at 1100px and above**. Keep 360/390/430px mobile widths readable without horizontal overflow, preserve visible keyboard focus and reduced motion, and use the existing design tokens and approved SVG. No new role/capability filtering, venue selection, session lookup, permission bypass, or routing changes in this visual slice. Destinations remain protected by the existing backend/BFF authority.

### 2026-10-13 — Larger module pictograms

The five module launch cards should make their pictograms prominent enough to scan quickly during operation. The pictogram remains the existing shared line icon, in the approved accent color; do not create new logos or change module identity. The cards have a **74px icon container and 44px pictogram** below 768px, and **88px / 56px** respectively at tablet/desktop widths. Increase card vertical room to preserve readable labels and at least 44px touch targets; keep the two/three/four-column grid, keyboard focus, route destinations and venue-bound behavior unchanged. These dimensions are pinned in the existing real-Venue Playwright integration test.

### 2026-10-13 — Consistent top-aligned launcher copy

Module cards use a fixed icon row followed immediately by a top-aligned title/description block. Remove `margin-top: auto` from the copy; the title baseline must match across cards in the same grid row even when descriptions have different lengths. Keep descriptions concise enough to remain fully readable within two lines at 360px and larger viewports (two-line clamp is a safety net, not a substitute for readable copy). The final fifth card spans both columns **only on mobile**, while tablet/desktop retain the 3/4-column grid. Integration tests cover baseline alignment, copy visibility, span and overflow at the existing viewport matrix.

## Pós-ativação permanente — rejeição Web e transporte (2026-10-15)

O contrato original permitia404/421 para host inexistente/inativo; portanto a
raiz404 anterior era fail-closed permitido, não prova de quebra de isolamento.
Para eliminar a dependência do path/credencial na operação permanente, a fronteira
Next passa a retornar **421 `VENUE_HOST_NOT_FOUND`**, com `Cache-Control: no-store`,
para todo candidato a host de estabelecimento inexistente/inativo/não verificado,
antes de renderização, rewrite, CSRF, auth ou capacidade Guest. Isso inclui APIs,
manifest, paths desconhecidos e métodos sem credenciais. Assets de build
`/_next/static` e `/_next/image` permanecem fora do matcher; não carregam identidade
nem dados do Venue. Hosts de compatibilidade/reservados mantêm seu contrato.
A API nativa continua sob ALLOWED_HOSTS/HMAC: um Host desconhecido não permitido
pode retornar400 antes da resolução; essa resposta não é aceita como421 do BFF.

A consulta de contexto não pode converter indisponibilidade, falha HMAC ou payload
inválido em host inexistente: preservar403/5xx e distinguir transporte503 de
identidade421. Revalidar domínio no Django continua obrigatório após o guard,
inclusive se o domínio for desativado entre consulta e comando.

POSTs internos BFF não podem ser reenviados implicitamente pelo transporte ao
receber421. O resultado421 original deve alcançar o cliente sem exceção de
replay de body e sem duplicar comandos. Falha real de rede continua503;
não substituir indisponibilidade por401/404/421. Paths internos permanecem
canônicos com barra final; não usar redirects como parte da autenticação.
