---
name: rodada-nextjs-web
description: Use when changing Next.js App Router, React, route handlers, Web authentication, tenant routing, guest ordering or Playwright tests in apps/web of Rodada.
---

# Next.js 16 / React 19 — Rodada Web

## Activate for
`apps/web/**`: Next.js App Router, server/client components, route handlers, BFF, same-origin auth, polling/SSE, visual and browser integration.

## Before writing code
1. Read [Web AGENTS](../../../apps/web/AGENTS.md), the specific spec/acceptance and relevant package metadata. Load the [routing contract](../../../docs/architecture/tenant-routing-contract.md) when the task touches Host, tenant, BFF, auth or guest sessions; load relevant design rules for visual changes.
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

During local iterations run the nearest test first. Before PR readiness, run the **applicable gates** in `apps/web/package.json` and `docs/ci-workflows.md`; full CI remains authoritative and its path-triggered checks are not optional:

- Any Web code or type/API change: `cd apps/web && npm run typecheck && npm run build` (plus relevant tests).
- Visual/UI changes: **always** `npm run test:visual`, including deterministic comparison and mobile/desktop checks when relevant.
- Auth, BFF, Host/tenant, guest access: `npm run test:auth` and `npm run test:tenant`, with positive and cross-Venue-negative cases; for real cross-stack interactions, also `npm run test:integration`.
- Payment, recovery, ordering and high-risk cross-surface changes: integration/replay/negative tests and release gates required by the corresponding spec and CI policy.

Run `npm ci` when dependencies are not installed or need refreshing; don't reinstall reflexively for every small edit. The browser/BFF integration suite needs isolated PostgreSQL and real Django per `.github/workflows/web.yml`; don't claim mock E2E as a real pass. Retain traces and report skipped or unavailable gates explicitly.
