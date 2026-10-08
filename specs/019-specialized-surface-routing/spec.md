# Spec 019 — Specialized Web Surface Routing

**Status:** In implementation

## Objective

Expose Rodada's Web applications as focused, host-selected product surfaces while
keeping one Next.js codebase and one canonical Django API.

## Scope

- `bar.rodada.ai` enters Rodada Bar;
- `cozinha.rodada.ai` enters Rodada Cozinha;
- `cliente.rodada.ai` resolves guest QR paths;
- `gerencia.rodada.ai` enters Rodada Gerência;
- each host has a matching document title and install manifest identity;
- existing local routes remain compatibility entry points during migration.

## Non-goals

- splitting the API or domain modules;
- deleting working `/bar`, `/kitchen`, `/guest`, `/manage`, `/cash`, `/refunds`, or `/pos` routes;
- creating a generic cross-surface navigation shell.

## Invariants

- host selection changes the primary surface, never authorization rules;
- Cliente remains guest-credential based and must not receive staff controls;
- cash, refunds, dispatch, and payments remain capabilities, not hosts;
- the API remains the canonical source of truth.

## Web visual foundation (PR #40)

All existing Web entry points consume the prototype's semantic tokens and shared
control, field, panel and status treatments. Production queues remain readable
with long names and crowded content at 360–430 px; important controls retain
44 px touch targets, visible focus and accessible names. Loading, empty, saving,
authorization, network error and stale states must not imply successful mutations
or measured zero values before a canonical response exists.

Spec 020 completes the executable Quick Catalog API and connected creation form
after operational queues, with explicit icon fallback and no configured AI provider.
Guest history, historical cash selection and operational reports follow Spec 020.
Management preserves exception-first ordering, including pending
cash discrepancy reviews and correction refunds, without invented analytics.

The shared shell contains no personal developer credit or personal contact link.
The developer attribution added in PR #40 was removed at the user's request.

Visual fixtures are test-only. CI checks all existing surfaces at 360, 390, 430,
768 and 1280 px, accessibility and matching prototype primitives. Full-screen
prototype comparisons document differing functionality rather than treating
unrelated layouts as equivalent. A separate suite exercises the real Django API
through the Web BFF with a disposable database; mocked visual tests are never
reported as real API E2E coverage.
