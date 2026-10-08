# Operational realtime — Spec 014 / ADR 0009

Commands remain HTTP. Events invalidate canonical reads and never confirm payments.

## Deployment

```sh
python manage.py migrate
python -m uvicorn rodada_api.asgi:application --host 0.0.0.0 --port 8000
python manage.py dispatch_realtime
```

Use ASGI, not WSGI/runserver. Supervise the dispatcher as a separate process. It
retries database failures with bounded 30-second backoff. Concurrent dispatchers
serialize publication per venue. Disable reverse proxy buffering and caching;
heartbeat is 15s and authorization is checked each one-second read cycle. Streams
rotate after five minutes; clients resume automatically.

Schedule `python manage.py prune_realtime` hourly: only published events older than
24h are deleted. Unpublished events are never pruned. Monitor oldest unpublished
occurred_at, pending count, worker health and database query latency. PostgreSQL
stores pending facts and published history. No Redis is required or trusted.

## Public emission port

```python
from django.db import transaction
from modules.realtime.services import emit_event

with transaction.atomic():
    # Validate and persist the canonical mutation.
    emit_event(venue_id=venue.id, event_type="order.confirmed",
               aggregate_type="Order", aggregate_id=order.id, tab_id=order.tab_id)
```

The port rejects calls outside a transaction. A locked VenueStream row allocates
sequence in that same transaction, ensuring venue sequence follows commit order.
Envelope schema_version is 1; version is the venue sequence. Private tab_id routing
is not serialized. Payloads must minimize data and exclude tokens, customer names,
financial amounts and provider secrets. Future domains integrate through this port.

An audit adapter bridges existing transactional Tab/Table, item, Dispatch,
availability, payment/refund and adjustment facts. Order confirmation emits explicitly
for guest and staff. Availability now has an atomic mutation boundary. Financial
and provider rules are unchanged.

## Protocol

Staff Bearer: `/realtime/snapshot/`, `/realtime/stream/`.
Guest X-Guest-Session: `/guest/realtime/snapshot/`, `/guest/realtime/stream/`.
Guests receive only their Tab and public Product invalidations; staff capabilities
filter operational/financial events. Query parameters cannot override scope.
Guest snapshot includes its authorized order history and ledger-derived balance.

1. Fetch snapshot cursor **before** reading canonical projections.
2. Connect with Last-Event-ID or cursor query parameter.
3. `change` carries the v1 envelope and SSE id; refresh affected canonical reads.
4. Accept cursor only after required refresh succeeds.
5. `ready` advances cursor through filtered events; `heartbeat` keeps connection live.
6. `reset` requires fresh baseline and canonical reads for expired, foreign, unknown
   or discontinuous history. `revoked` ends an unauthorized connected subscription.

Delivery is at least once. Consuming events never executes mutations. `?once=1`
returns a finite batch for tests; it does not run the required dispatcher.

## Validation and limits

`python -m pytest` covers atomic rollback, retry, replay, gaps, access and connected
revocation. Against a migrated disposable PostgreSQL DB and ASGI on port 18764:

```sh
POSTGRES_DB=rodada_realtime_verification python scripts/verify_realtime.py
```

The live smoke uses actual HTTP commands/SSE and publication in a separate process.
It tests guest ordering, duplicate commands, reload balance/history, missed statuses,
reset and revocation. It is not a peak-shift load benchmark.

Server subscriptions read the DB each second; client fallback is Web 15s / Android
30s, only during transport loss. This suits the pilot; measure database/connection
budgets before scaling subscribers. Redis fan-out can later reduce shared reads.
Android process restart deliberately takes a fresh snapshot instead of persisting
a cursor without a corresponding durable operational projection. Class C offline
fulfillment remains disabled. Cache never authorizes a command.
