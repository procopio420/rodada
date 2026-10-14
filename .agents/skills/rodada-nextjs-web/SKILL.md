---
name: rodada-nextjs-web
description: Use when changing Next.js App Router, React, route handlers, Web authentication, tenant routing, guest ordering or Playwright tests in apps/web of Rodada.
---

# Next.js 16 / React 19 — Rodada Web

## Activate for
`apps/web/**`: Next.js App Router, server/client components, route handlers, BFF, same-origin auth, polling/SSE, visual and browser integration.

## Before writing code
1. Read [Web AGENTS](../../../apps/web/AGENTS.md), [Next package manifest](../../../apps/web/package.json), the specific spec and [routing contract](../../../docs/architecture/tenant-routing-contract.md).
2. **This project uses Next.js 16.3.x.** Read the installed `apps/web/node_modules/next/dist/docs/` for APIs you modify; don't rely on memory of older Next versions or bypass the automatically generated Next.js AGENTS block.
3. Inspect the existing auth gateway, `proxy.ts`, Venue host resolution, API routes, relevant components and tests.

## Design and architecture
- Keep access/refresh secrets in the BFF and Secure/HttpOnly host-only cookies. No token in `NEXT_PUBLIC_*`, local/session storage, URLs or client state.
- Browser cannot select another Venue via forwarded headers/slug; canonical hostname is context, not permission. Every protected command is verified again server-side.
- Server decides sale/authorization, SSE only notifies changes; after an ambiguous POST, preserve original intent and reconcile canonical state before showing success or retrying.
- Distinguish `loading`, `offline`, `timeout`, unauthorized and committed-but-response-lost. Do not show 'connection lost' just because a normal order is loading.
- Preserve the operational sequence `NEW → PREPARING → READY`; preparation starts only on the operator action specified by the contract.
- Reuse components/tokens from [design system](../../../docs/design/system.md). Also activate `rodada-ui-design` for visual/UX changes.

## Validation
```sh
cd apps/web
npm ci
npm run typecheck
npm run test:auth
npm run test:tenant
npm run build
npm run test:visual
npm run test:integration
```
The browser/BFF suite needs isolated PostgreSQL and real Django per `.github/workflows/web.yml`. Do not fake a successful E2E with a mocked browser service. Test both Venue-positive and cross-Venue-negative flows when auth/host changes. Retain traces and report limitations in handoff.
