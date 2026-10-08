# Plan — Spec 014 — Realtime, Connectivity & Degraded Operation

## Recommended sequence

1. **Cross-surface runtime contract**
   - backend authoritative, clients as projections;
   - HTTP commands;
   - SSE-first server -> client realtime;
   - shared event envelope and surface authorization;
   - lightweight PWA/native startup behavior.

2. **Transactional outbox + event delivery**
   - write domain change + outbox in one PostgreSQL transaction;
   - idempotent dispatcher/consumers;
   - Redis optional for ephemeral fan-out only;
   - bounded replay retention and cursor-gap handling.

3. **Snapshot + delta + resume**
   - snapshot/read-model endpoints;
   - resume cursor / Last-Event-ID;
   - replay when possible;
   - full revalidation when continuity cannot be proven;
   - local safe projection persistence.

4. **Connectivity state contract**
   - API vs realtime health;
   - ONLINE/RECONNECTING/STALE/OFFLINE;
   - freshness metadata.

5. **Command envelope/idempotency**
   - client_command_id;
   - idempotency key;
   - target version;
   - actor/device/captured_at.

6. **Realtime degradation**
   - SSE reconnect/backoff;
   - bounded polling/revalidation fallback;
   - cursor replay;
   - snapshot recovery after an unrecoverable gap.

7. **Android durable pending queue**
   - PendingOrderIntent;
   - recovery cash/external evidence;
   - explicit statuses.

8. **PWA degraded reads/drafts**
   - cached shell/read model;
   - stale labels;
   - no fake mutation success.

9. **Reconciliation service**
   - ordered replay;
   - conflict taxonomy;
   - financial recovery review.

10. **Optional Class C fulfillment rollout**
   - only after monotonic transition tests.

11. **Runbooks / observability**
   - sustained outage;
   - recovery metrics and dashboards.

## Rollout

Ship the authoritative HTTP command path and snapshot + SSE read path first. The first usable slice should prove one mutation propagating to at least two different surfaces without either client owning canonical state. Then ship degraded realtime recovery. Add local mutation capture only per operation after its server idempotency contract exists.

Do not enable broad offline queues with a generic “retry all”.

## Testing strategy

- network fault injection;
- SSE/event-delivery-only failure;
- replay from a valid cursor;
- expired/gapped cursor forcing snapshot refresh;
- Redis restart after domain commit does not lose the committed fact;
- duplicate outbox/event delivery is idempotent;
- cached-start render before network refresh on PWA;
- timeout after server commit;
- duplicate retry;
- app kill/restart with queue;
- actor revocation before replay;
- stale availability;
- payment ambiguity;
- conflict ordering;
- PWA cache isolation.

## Dependencies first

Server idempotency and canonical mutation semantics from Specs 001/006/008. Payment recovery must not ship before reconciliation is tested.

## Implementation slice

Implement a database outbox/publication log and async SSE endpoints first; adapt existing audit facts through a named allowlist, with explicit emission for guest/staff order confirmation. Add header-authenticated Web/native transports which invalidate canonical reads, guest-scoped history, and fault/replay tests. Verify existing full-shift suite before integration and PR.
