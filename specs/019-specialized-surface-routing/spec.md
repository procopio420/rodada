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
