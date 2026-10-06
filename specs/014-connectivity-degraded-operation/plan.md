# Plan — Spec 014

## Recommended sequence

1. **Connectivity state contract**
   - API vs realtime health;
   - ONLINE/RECONNECTING/STALE/OFFLINE;
   - freshness metadata.

2. **Command envelope/idempotency**
   - client_command_id;
   - idempotency key;
   - target version;
   - actor/device/captured_at.

3. **Realtime degradation**
   - polling fallback;
   - socket recovery full revalidation.

4. **Android durable pending queue**
   - PendingOrderIntent;
   - recovery cash/external evidence;
   - explicit statuses.

5. **PWA degraded reads/drafts**
   - cached shell/read model;
   - stale labels;
   - no fake mutation success.

6. **Reconciliation service**
   - ordered replay;
   - conflict taxonomy;
   - financial recovery review.

7. **Optional Class C fulfillment rollout**
   - only after monotonic transition tests.

8. **Runbooks / observability**
   - sustained outage;
   - recovery metrics and dashboards.

## Rollout

Ship read-state/realtime degradation first. Add local mutation capture only per operation after its server idempotency contract exists.

Do not enable broad offline queues with a generic “retry all”.

## Testing strategy

- network fault injection;
- socket-only failure;
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
