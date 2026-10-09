# Operational realtime delivery — Spec 014

## Implemented contract

[Spec 014](../../specs/014-connectivity-degraded-operation/spec.md) and
[ADR 0009](../adr/0009-http-commands-sse-realtime-outbox.md) define this slice.
Backend domain state stays authoritative. Commands remain HTTP; SSE carries
invalidation facts, and clients re-read canonical projections before accepting cursors.

`modules.realtime.services.emit_event` is the public transaction-only publication
port. Domain changes and outbox rows commit/roll back together. A locked VenueStream
row allocates commit-ordered venue sequences. The dispatcher publishes committed
rows into the database-backed replay log; concurrent dispatchers serialize by venue.
Delivery is at least once and never performs a client-side domain mutation.

The v1 envelope contains id/cursor, venue_id, type, aggregate_type/id, occurred_at,
version and minimal payload. Private Tab routing stays server-side. Existing audit
facts bridge Tab/Table/occupancy/zone, guest Tab/session, item transitions/corrections,
Dispatch, availability, payment/refund, charge/replacement, cash lifecycle and
published Product/ProductIcon changes. `order.confirmed` emits directly inside the
Order transaction. New event domains must add an explicit visibility policy.

Staff streams use authenticated Venue/capability scope. Guest streams reauthorize
GuestSession and deliver only its Tab and public catalog invalidations. Revocation
ends an active subscription. Access-token expiry instead requests credential rotation
and cursor resume. Cursor gaps/expiry require a new canonical snapshot. Replay is
retained for 24 hours; unpublished facts are never pruned. Redis is optional and
stores no canonical publication facts.

## Surfaces and degraded behavior

- Kitchen/Bar: production and availability invalidations; existing work layout and
  Quick Catalog remain intact. A local age-display timer does not poll the API.
- Guest: QR/session resolution, authorized Tab creation, real confirmation,
  history/status and ledger balance survive reload. Canonical NEW/ACCEPTED/PREPARING/
  READY/PICKED_UP/DELIVERED/CANCELLED states are displayed; inferred milestones are
  not manufactured. Existing Tab short-code joining remains outside this slice.
- Management: live operational projection, cash exceptions and timestamped safe cache.
- Android Atendimento: OperationalRealtime interface, native header-authenticated
  adapter, foreground invalidation/revalidation and reconnect. A cursor advances only
  after canonical reads succeed. Existing encrypted recovery records and payment/
  Tab-transfer semantics are preserved.

Web reconnect uses exponential backoff/jitter, a 45-second liveness watchdog,
30-second reconnect freshness budget and 15-second fallback reads during transport
loss. Revalidation coalesces bursts and is bounded to four refreshes/second.
Android fallback is bounded to 30 seconds. Healthy HTTP commands remain usable when
SSE fails; reconnect never confirms payments or retries financial commands.

Web shells and immutable static assets are cached by a narrowly scoped service
worker. API requests and commands are never cached or replaced with local success.
Safe staff projections are isolated by Venue/session in sessionStorage; guest cache
contains public menu only. ONLINE/RECONNECTING/STALE/OFFLINE and last-read timestamps
separate cached data from live state. Cold reload renders safe cache while canonical
revalidation runs. Guest offline reload exposes cached menu with no financial history,
submission or locally extended GuestSession. A reload takes a new snapshot rather
than persisting a cursor without its canonical projection.

## Verified evidence (2026-10-09)

| Check | Result |
| --- | --- |
| Complete PostgreSQL backend suite | 224 passed |
| Final realtime + full-shift PostgreSQL regression | 20 passed |
| Web transport faults | 8 passed |
| Web typecheck and production build | Passed |
| Visual / responsive / accessibility / prototype comparisons | 110 passed |
| PostgreSQL-backed real Web workflows | 5 passed |
| Android JVM tests | 32 passed |
| Android assembleDebug / lintDebug | Passed |
| Live ASGI/PostgreSQL + actual Redis restart | Passed |
| Browser live tracking, reload, offline shell/cache and blocked commands | Passed |

The fault checks cover delayed/chunked SSE frames, dropped connections, duplicate/
reordered events, invalid/expired/gapped cursors, dispatch delay/retry, separate
publication process, healthy API with unavailable SSE, guest Venue/Tab isolation,
connected revocation, access-token rotation and no financial command replay.

Latest local samples: confirmation-to-SSE **2,432 ms** and READY-to-guest rendering
**2,430 ms**, including explicit separate-process dispatch. Earlier samples ranged
from 1,028 to 2,432 ms. These are local smoke measurements, not p95 or low-cost-tablet
load claims. Mobile screenshots at 390 px showed no horizontal overflow; the full
visual gate also exercises 360/390/430/768/1280 px and deterministic prototype
comparisons, without accepting a new baseline.

Reproduction:

```sh
# apps/api, using an explicitly disposable PostgreSQL database
python manage.py migrate
python -m uvicorn rodada_api.asgi:application --port 18764
python manage.py dispatch_realtime
python -m pytest --ds=rodada_api.settings
python scripts/verify_realtime.py
# Optional: REALTIME_TEST_REDIS_CONTAINER=<dedicated test container> restarts Redis
# while a confirmed Order's outbox fact is still unpublished.

# apps/web, with RODADA_API_BASE_URL=http://127.0.0.1:18764
npm run typecheck
npm run build
npm run test:realtime
npm run test:visual
npm run test:integration
npm run start -- --port 18765
npm run test:realtime:browser
```

The live browser script requires Python Django/Playwright and Chromium;
CHROMIUM_EXECUTABLE can select an installed browser. PostgreSQL-backed Playwright
uses RODADA_E2E_POSTGRES=1 and the dedicated database rodada_web_e2e. Set
RODADA_TEST_PYTHON to the API environment. Parallel worktrees can select isolated
RODADA_VISUAL_PORT/RODADA_REFERENCE_PORT and RODADA_E2E_API_PORT/RODADA_E2E_WEB_PORT.

## Deployment and remaining rollout

Use ASGI and supervise `dispatch_realtime` separately. Disable proxy buffering and
caching of text/event-stream. Schedule `prune_realtime` hourly. Monitor pending
outbox count/age, worker health and stream/replay latency. The dispatcher retries
DB outages with bounded backoff; publication history remains in PostgreSQL.

Subscriptions currently check the database each second. Measure sustained peak load,
connection budget and low-cost tablets before extending pilot capacity; optional
Redis wakeups/fan-out can reduce shared reads without replacing the durable log.
Management refreshes its existing active projection; it has no new incremental
analytics read model. Structured production observability remains follow-up work.

Android operational projections/cursors are not durable across process death; it
bootstraps canonically and keeps its encrypted recovery store intact. Generalized
offline intent/reconciliation, emergency cash/external-terminal evidence, conflict
review queues and Class C offline fulfillment remain unchecked in Spec 014. No
provider bypass, automatic financial retry or offline confirmed order was introduced.
For sustained outages, follow the existing Spec 014 manual/external runbook and
reconcile explicitly when the canonical API returns.
