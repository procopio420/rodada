# Spec 014 — Realtime, Connectivity & Degraded Operation

**Status:** Draft for implementation  
**Owner capability:** Cross-cutting reliability contract

## Objective

Define the cross-surface runtime contract for Rodada: lightweight clients, an authoritative backend, realtime delivery, cached projections, reconnect/replay and safe degraded operation. Users must distinguish canonical truth from cached/pending local state, while the system avoids duplicate orders/payments and remains responsive on inexpensive operational devices.

## Product problem

A real bar will run Rodada on phones, tablets and shared terminals with variable hardware and weak Wi-Fi/mobile handoff. The product cannot feel like a heavy website that freezes while waiting for the network, and it cannot make realtime transport the source of truth. Pretending everything is “offline capable” risks double charging, stale availability and duplicate production. Blocking every screen because the realtime stream dropped is also unacceptable.

## Scope

- all operational surfaces: Atendimento, Cozinha, Bar, Cliente and Gerência;
- lightweight client/runtime responsibilities versus authoritative backend responsibilities;
- HTTP command semantics and SSE-first realtime delivery;
- snapshot + delta + resume/replay;
- transactional outbox and durable event publication;
- API/internet/local-network failure;
- realtime delivery failure with healthy API;
- Android and PWA reconnect;
- cached/stale reads;
- pending local intents;
- retry/idempotency;
- operation classification;
- order/payment restrictions;
- reconciliation/conflict;
- operational fallback/runbook.

## Explicitly out of scope

- full local-first database/edge server in P0;
- peer-to-peer canonical POS;
- offline Tap on Phone provider bypass;
- offline Pix confirmation;
- pretending cached availability is current;
- automatic acceptance of conflicting recovery records.

## Connectivity model

Connectivity is not one boolean.

Track at least:

### API state
- REACHABLE;
- DEGRADED;
- UNREACHABLE.

### Realtime state
- HEALTHY;
- RECONNECTING;
- UNAVAILABLE.

### User-facing state

Normalize to:
- **ONLINE** — API healthy and realtime healthy/recent.
- **RECONNECTING** — transient loss; automatic retry underway; data still within freshness budget.
- **STALE** — API may be reachable or cached reads visible, but realtime/freshness guarantee exceeded.
- **OFFLINE** — API unreachable; only cached reads/local pending capture available.

A client can be STALE because its realtime stream is down even while mutations remain safe through a healthy API.

## Source-of-truth invariant

PostgreSQL/API-confirmed domain state remains canonical.

Local cache may be:
- last known canonical state;
- draft;
- pending intent;
- recovery evidence.

It must never be rendered indistinguishably from confirmed server state.

## Cross-surface runtime architecture

Rodada is one authoritative operational system with multiple specialized clients.

```text
                           PostgreSQL
                      canonical domain state
                              |
                  same database transaction
                    domain state + outbox
                              |
                              v
                    transactional outbox
                              |
                       event dispatcher
                              |
                   SSE / event-stream delivery
                              |
        +------------+--------+---------+-----------+
        |            |                  |           |
  Atendimento     Cozinha             Bar       Gerência
    Android         PWA               PWA          PWA
        |
      Cliente PWA consumes the same canonical contracts
```

Core rule:

> **The backend is the system. Clients are responsive, resilient operational projections of that system.**

Consequences:
- no client owns canonical Order, Tab, Payment, ProductAvailability, fulfillment or table state;
- business invariants live in backend/domain services, not in UI state;
- a surface may maintain a local projection for speed, but the projection is explicitly versioned/freshness-aware;
- clients do not call each other to discover state;
- one committed domain change may update several surfaces through the same event contract;
- a realtime outage never changes which component is authoritative.

Examples:
- Atendimento confirms an Order through HTTP;
- backend commits Order/OrderItems and corresponding outbox facts atomically;
- Cozinha/Bar receive routed production changes;
- Cliente sees order progress;
- Gerência updates its live projection;
- no surface needs to poll or invoke another surface directly.

## Client weight and startup contract

Operational clients must optimize for predictable touch interaction during peak service, including low/mid-range Android devices and tablets.

For Web/PWA surfaces:
- the operational shell must be cacheable and able to start without SSR being available;
- do not require a server-render round trip before showing the last known safe projection;
- cache safe read models locally, using IndexedDB or an equivalent durable browser store where persistence is useful;
- network refresh happens after the local shell/projection can render;
- avoid large decorative dependencies, unnecessary animation and whole-screen rerenders in hot operational views;
- Kitchen/Bar/Guest/Management may share contracts and design tokens without being forced into one giant frontend bundle.

For Android Atendimento:
- use local durable storage appropriate to Android for cached projection/pending intents;
- the app must not wait for realtime connection before becoming usable for safe local/read operations;
- Tap on Phone/device-specific capabilities remain native.

A reference performance budget must be established during implementation. At minimum:
- cached operational state is rendered without waiting for network;
- a newly received realtime event updates only the affected projection/component;
- reconnect does not force a full application restart.

## Command versus realtime transport

### Commands

Canonical mutations use normal authenticated HTTP requests.

Examples:
- create/confirm Order;
- change ProductAvailability;
- mark fulfillment state;
- table/occupancy actions;
- payment commands;
- cash operations.

Commands:
- are server-validated;
- are idempotent where retry can occur;
- return canonical result/version metadata;
- do not depend on realtime delivery succeeding.

### Server-to-client realtime

The default transport for operational server-to-client updates is **SSE (`text/event-stream`)**.

Rationale:
- most Rodada realtime traffic is server -> client;
- user actions already have an HTTP command path;
- reconnect/resume semantics are simpler;
- it works over ordinary HTTP infrastructure;
- clients do not need to maintain a second bidirectional command protocol.

WebSocket is not forbidden, but requires a concrete feature that needs continuous bidirectional messaging and cannot be served cleanly by HTTP commands + SSE. It must not be introduced merely because a screen is “realtime”.

Native `EventSource` is not mandatory. Where authentication/header constraints require it, a fetch-stream SSE adapter may implement the same event-stream contract.

## Event envelope and routing

Realtime events must carry enough metadata to be applied or rejected deterministically.

Conceptual envelope:

```json
{
  "id": "opaque-resume-cursor",
  "venue_id": "uuid",
  "type": "production.item.ready",
  "aggregate_type": "OrderItem",
  "aggregate_id": "uuid",
  "occurred_at": "2026-10-06T20:00:00-03:00",
  "version": 12,
  "payload": {}
}
```

Requirements:
- event type names are stable/versionable contracts;
- ordering is guaranteed only at the documented stream/aggregate scope, not assumed globally;
- consumers are idempotent;
- venue/user authorization filters what can be subscribed to;
- sensitive payloads are minimized;
- clients may receive an event and choose to invalidate/refetch rather than patch local state directly.

## Snapshot + delta + resume

Every realtime surface follows the same logical lifecycle:

```text
open app
  -> render safe cached projection when present
  -> GET canonical snapshot / refresh active projection
  -> open SSE from snapshot/resume cursor
  -> apply deltas
  -> persist safe projection + latest cursor
```

After a disconnect:

```text
stream drops
  -> existing projection remains visible with freshness state
  -> reconnect with last accepted event id/cursor
  -> server replays retained events when possible
  -> if cursor is expired/unknown/gapped, server instructs revalidation
  -> client fetches fresh snapshot
  -> incremental stream resumes
```

Rules:
- replay must be bounded by a defined retention policy;
- clients must tolerate duplicate delivery;
- clients must detect or be told about an unrecoverable gap;
- reconnect must never silently assume no changes occurred;
- `Last-Event-ID` or an equivalent explicit resume cursor may be used depending on client adapter.

## Transactional outbox

A canonical mutation and the fact that drives realtime/projections must not be able to diverge.

For domain changes that need publication:
1. validate command;
2. change canonical domain state;
3. insert outbox event in the **same PostgreSQL transaction**;
4. commit;
5. dispatcher publishes committed outbox events to subscribers/projection workers.

Redis may be used for fan-out, wakeups, ephemeral distribution or coordination, but:
- Redis Pub/Sub is never the only record that an event occurred;
- loss/restart of Redis cannot erase a committed business fact;
- event publication is at-least-once and consumers must be idempotent;
- outbox delivery status is operational metadata, not financial/domain truth.

## Mutation classification

Every mutation belongs to one class.

### Class A — API-required, never offline-confirmed

Includes:
- Order confirmation;
- Product/variant/modifier availability change;
- guest ordering/block/revocation;
- Tab split/merge/reopen;
- pricing Adjustment;
- provider Payment creation/confirmation/refund;
- CashShift close/review;
- role/device/config changes;
- any mutation that changes financial truth or access control.

When API is unreachable, these cannot appear successful.

### Class B — Locally capturable intent, server-confirmed later

May be captured with client-generated UUID/idempotency key but is **not canonical until replay succeeds**.

P0 examples:
- staff order draft / pending order intent;
- emergency cash receipt evidence;
- external-terminal collection evidence;
- non-sensitive text draft.

Rules:
- persistent local queue;
- visually marked “Pendente de envio”;
- no ledger/order/production side effect locally;
- replay validates current server state;
- conflicts require user action.

### Class C — Replayable operational event

Only explicitly approved monotonic/non-financial actions may continue locally after their base entity was previously confirmed and cached.

P0 candidate:
- fulfillment progress PREPARING/READY on an already confirmed OrderItem, with pending-sync marker.

This class must be enabled only after domain-specific conflict tests exist. It cannot create a new OrderItem, Charge, Payment or guest authorization.

### Class D — Local UI-only

- filtering;
- navigation;
- editing an unsubmitted draft;
- viewing cached content.

## Order semantics

### New order while online/stale-realtime

If API is REACHABLE:
- order confirmation is allowed even if realtime is down;
- server revalidates Product + variant/modifier availability;
- client-generated idempotency key prevents duplicate retry;
- subscribed surfaces receive the committed change through SSE; if realtime delivery is degraded they recover through bounded revalidation/polling until the stream resumes.

### New order while API offline

P0:
- user may build/save a **PendingOrderIntent** locally;
- UI says “Pedido ainda não enviado”;
- it is not assigned a canonical Order number;
- it is not counted in Tab balance;
- it is not considered in production;
- on reconnect, replay sends one confirmation using original client intent id/idempotency key.

If availability/pricing changed:
- server rejects affected lines;
- UI asks operator to review;
- no silent substitution.

### Duplicate-order prevention

- every submit intent gets stable client_command_id/idempotency_key before first network attempt;
- retry after timeout uses same key;
- client keeps acknowledged server result mapping;
- server enforces uniqueness;
- queue replay is serial per Tab where ordering matters;
- a user pressing “Enviar” again while same intent is pending does not mint a second key unless explicitly creating a second order.

## Availability staleness

Cache stores:
- state;
- server version;
- fetched_at.

When STALE/OFFLINE:
- Product availability is labeled potentially outdated;
- Class A confirmation still depends on API;
- no UI may infer that cached AVAILABLE means sellable now.

UNAVAILABLE cached state may remain visually unavailable, but reconnect still refreshes.

## Fulfillment during degraded network

### Realtime unavailable, API healthy
Fully usable via API + polling/revalidation.

### API unavailable
If Class C rollout is enabled:
- station may mark PREPARING/READY locally for already known confirmed items;
- each transition has client event id and occurred_at;
- UI displays pending sync;
- dispatch/guest cannot be assumed updated;
- replay validates legal transition and existing corrections.

If Class C is not enabled for the deployed client/version, station stays read-only and follows manual runbook.

No local transition may create a financial effect.

## Guest PWA

Guest ordering requires API.

When API is unavailable:
- cached menu may be shown only with clear offline/stale notice;
- Add-to-cart/draft may remain local;
- submit is blocked/pending but never says “pedido recebido”;
- payment is unavailable;
- service requests are not claimed sent until API confirms;
- old GuestSession validity cannot be extended locally.

## Android reconnect

Rodada Atendimento:
- listens to network changes but verifies API health rather than trusting OS connectivity;
- exponential backoff with jitter;
- resumes foreground with immediate revalidation;
- preserves pending intents in durable encrypted/local app storage as appropriate;
- retries only idempotent/safe operations;
- shows per-intent status: pending, syncing, conflict, failed, confirmed;
- does not require app restart.

Cellular fallback is allowed by OS/network policy; Rodada should not force Wi-Fi-only operation.

## PWA reconnect

Applies to Cozinha, Bar, Cliente and Gerência, with permissions/data scopes appropriate to each surface.

- detect online/offline as hint only;
- health/revalidation determines actual state;
- Service Worker may cache shell and safe read data;
- IndexedDB or equivalent may persist safe projections/cursors/drafts;
- no service-worker fabricated API success;
- on resume/reconnect, refresh active sensitive projections before enabling actions that require fresh canonical state;
- pending draft data may persist locally;
- staff data caches must be isolated per authenticated context.

## Realtime stream unavailable with API healthy

This is **not OFFLINE**.

Behavior:
- HTTP mutations continue through the API;
- UI becomes RECONNECTING then STALE if freshness budget is exceeded;
- the current projection remains visible instead of blanking the screen;
- clients revalidate/poll active critical views with bounded cadence;
- server responses remain canonical;
- Redis/SSE delivery never becomes a second source of truth;
- after stream recovery, client resumes from its cursor when possible;
- if replay cannot prove continuity, client performs a snapshot/full revalidation before trusting later incremental events.

## Payment restrictions

### Tap on Phone
Requires:
- API reachability;
- provider/network capability required by adapter;
- valid authenticated session/device.

If connectivity is lost after provider submission:
- Payment becomes or is reconciled as CONFIRMATION_PENDING;
- do not create another equivalent attempt;
- local SDK success alone is not definitive if backend confirmation is missing.

No offline Tap on Phone bypass.

### Pix
Creation/confirmation requires API/provider connectivity.

An already displayed QR may remain visible with status “confirmação indisponível” if backend cannot be reached. Rodada must not locally mark it paid.

### Cash
Physical cash can occur during outage only under emergency recovery flow.

Local recovery record:
- recovery_id;
- tab reference/snapshot;
- intended amount;
- tender/change;
- actor/device;
- occurred_at;
- note/reason;
- status PENDING_SYNC | REQUIRES_REVIEW | RECONCILED.

It is **not** a confirmed Payment until server replay/reconciliation.

On reconnect:
- if Tab still supports exact receipt and no conflicting settlement, server may create idempotent CASH Payment + CashMovement;
- otherwise require CASHIER/MANAGER review.

### External terminal
Same evidence model:
- record amount/reference optionally;
- label “Cobrado fora — pendente de sincronização”;
- do not auto-repeat provider charge;
- reconciliation may create EXTERNAL_TERMINAL Payment once or raise conflict.

## Manual/external fallback runbook

For sustained outage:
- use manual paper/venue-approved external process for orders/payments;
- do not fabricate canonical server IDs;
- assign local recovery identifier;
- after reconnect, enter/reconcile through explicit recovery flow;
- production fallback printing, if supported, follows Spec 015 and must visibly distinguish recovery tickets to avoid duplicate preparation.

The runbook is an operational safety valve, not a second hidden POS.

## Cash operations

Supply/withdraw/count/close remain API-required in P0.

Emergency physical action may be noted locally, but server truth is created later through audited recovery. CashShift close cannot occur canonically offline.

## Tab/floor operations

- location drafts can be locally edited but canonical move requires API unless specifically promoted to Class C later;
- release/cleaning complete remains API-required because it revokes guest access/generation;
- split/merge/reopen always API-required.

## Authentication under loss

Per Spec 008:
- no new offline login;
- cached session may label local pending intent actor;
- server reauthorizes on replay;
- expired/revoked actor causes replay rejection.

## Reconciliation after reconnect

Sequence:
1. restore API health;
2. refresh auth/session;
3. fetch current canonical versions for affected entities;
4. replay safe idempotent Class C events in causal order;
5. replay/submit Class B intents;
6. classify result:
   - CONFIRMED;
   - ALREADY_APPLIED;
   - CONFLICT;
   - REJECTED;
7. re-fetch active screens;
8. resume realtime and then incremental updates.

Financial recovery conflicts never auto-resolve by “last write wins”.

## Conflict examples

- PendingOrderIntent contains now-unavailable item -> review required.
- Offline cash evidence amount exceeds current remaining balance -> manager review.
- READY pending event but item was cancelled centrally -> reject event, show conflict.
- role revoked before replay -> authorization rejection.
- Table occupancy generation changed -> stale operation rejected.

## Ordering / queue causality

For commands affecting same aggregate:
- preserve capture order;
- stop replay at first conflict that makes following commands ambiguous;
- unrelated aggregate queues may replay independently.

## Idempotency

Every replayable/capturable intent has:
- stable id;
- venue/device;
- actor context;
- target aggregate;
- captured_at;
- payload hash/version;
- idempotency key.

Server maps duplicate retry to existing result.

## Data freshness

Each cached critical projection includes last_server_sync_at.

UI thresholds:
- RECONNECTING: brief transient;
- STALE: beyond configured freshness budget;
- OFFLINE: confirmed API unreachability.

Exact seconds may be implementation/config detail, but state transition must be deterministic and testable.

Financial totals shown from cache while offline carry “Última atualização HH:MM” and cannot be used to initiate integrated payment.

## Permissions

Connectivity does not relax permissions.

Recovery/reconciliation:
- ordinary pending order retry: original authorized actor/session revalidated;
- cash/external payment conflict: CASHIER/MANAGER;
- manual override of recovery: MANAGER with reason;
- no client can promote its own local record to confirmed.

## API / conceptual contracts

- `/health` or lightweight reachability;
- command idempotency envelope;
- mutation response with `server_version`/canonical identifiers;
- conflict response with current canonical state;
- recovery reconciliation endpoints;
- snapshot/read-model endpoints for active operational surfaces;
- SSE/event-stream endpoint scoped by authenticated Venue/surface;
- stable event envelope with id/type/aggregate/version/timestamp;
- resume cursor / `Last-Event-ID` semantics;
- explicit “cursor expired / full refresh required” response or event;
- bounded polling/revalidation fallback for realtime-only degradation.

## Metrics/events

Technical/operational:
- connectivity state duration;
- realtime disconnect count;
- SSE reconnect/resume success rate;
- replayed event count and cursor-gap/full-refresh count;
- outbox publish lag/backlog;
- pending queue depth/age;
- replay success/conflict/reject;
- API latency/error rate;
- recovery payment count;
- confirmation_pending duration.

Do not treat connectivity as staff performance.

## Audit

Canonical audit records:
- replayed command retains original captured_at plus server applied_at;
- recovery financial records keep recovery_id/device/actor;
- manual reconciliation records reviewer/reason;
- conflicts/rejections may be retained as technical operational evidence without polluting financial ledger.

## Security/privacy

- durable local queue encrypted/OS-protected where appropriate;
- no PAN/CVV/provider secret cached;
- minimize guest/customer PII in offline cache;
- remote logout/revocation applies once server reached; sensitive screens should local-lock on normal session expiry policy;
- Service Worker cache must not leak staff data cross-user.

## Dependencies

## Depends on

- Specs 001/003/004/006 for domain mutation semantics.
- Spec 008 session reauthorization.
- Specs 009–013 for classification of newer commands.

## Integrates with

- Spec 015 consumes this degraded-operation contract for printer/production fallback behavior.

## Enables

- pilot resilience;
- deterministic UX for every surface under weak network;
- safe recovery without double orders/payments.

## Deliberately deferred

- local edge server;
- multi-device peer sync;
- fully offline guest ordering;
- offline provider payment authorization;
- automatic conflict merge for financial records.
