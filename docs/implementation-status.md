# Implementation Status

Last reviewed: 2026-10-06.

## Implemented specifications

The current vertical slices cover the repository's approved Specs 001–003:

- domain and persistence: venues, staff, zones, service points, products, customers,
  venue-local relationships, tabs, orders/items, ledger entries, cash shifts, audit
  events, dispatch tasks/events and delivery runs;
- API: staff PIN/session login, tab/order/payment/fulfillment flows, customer lookup/history, relationship
  limits and overrides, cash summaries, zone/service-point configuration and dispatch;
- web: mobile-first staff POS, kitchen queue, operational queue, peak mode, partial
  payments, cash summary and offline replay for idempotent orders/cash receipts;
- realtime: venue-scoped dispatch WebSocket notifications backed by a persistent
  incremental event feed and HTTP snapshot recovery;
- tests: financial/domain invariants, offline idempotency, venue isolation,
  relationship limits, dispatch ownership, delivery derivation and realtime broadcast.
  `python manage.py smoke_demo` additionally verifies the seeded staff API happy path.

## Spec-to-implementation map

| Spec | Domain | API | Web/realtime | Tests |
| --- | --- | --- | --- | --- |
| 001 Core POS | `catalog`, `pos`, `ledger`, `cash`, `audit` | `/api/auth/login`, `/api/products`, `/api/tabs`, orders, fulfillment, payments, shifts | staff POS, kitchen, offline queue | `pos/tests.py`, `manage.py smoke_demo` |
| 002 Conta da Casa | `customers`, relationship policy and tab limit snapshot | customer search/history and limit override | customer selection, exposure and partial payment | `customers/tests.py` |
| 003 Dispatch | `dispatch`, zones and service points | tasks, claims, completion, runs and event feed | Agora/peak queue and venue WebSocket | `dispatch/tests.py` |

## Not implemented without an approved spec

The repository currently has no product/UX/API contract for customer QR sessions,
2D venue maps, table cleaning states, canonical catalog autocomplete, generated item
icons, menu-availability mutation UX, or Tap to Pay/provider callbacks. A real PSP is
explicitly outside Spec 001. These areas require numbered specs and, where durable
architecture is selected, ADRs before implementation under `AGENTS.md`.

The existing payment path records explicitly manual payments; it does not simulate a
PSP success. Local staff authentication uses a seeded PIN and opaque bearer session;
it is suitable for the demo, not a replacement for a production identity lifecycle.

## Configuration

- `REDIS_URL`: shared Django Channels layer; without it development uses memory.
- `NEXT_PUBLIC_API_URL`: staff web API base.
- `NEXT_PUBLIC_WS_URL`: staff web WebSocket origin.

See [`docs/demo/local-runbook.md`](./demo/local-runbook.md) for safe local reset,
seed, credentials and smoke commands.
