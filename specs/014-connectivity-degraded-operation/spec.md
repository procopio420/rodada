# Spec 014 — Connectivity & Degraded Operation

**Status:** Draft for implementation  
**Owner capability:** Cross-cutting reliability contract

## Objective

Define exactly how Rodada behaves under bad network conditions so users can distinguish canonical truth from cached/pending local state and the system avoids duplicate orders/payments.

## Product problem

A real bar will encounter weak Wi-Fi, mobile handoff, API outages and realtime outages. Pretending everything is “offline capable” risks double charging, stale availability and duplicate production. Blocking every screen at the first WebSocket failure is also unacceptable.

## Scope

- API/internet/local-network failure;
- Redis/WebSocket failure with healthy API;
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

A client can be STALE because WebSocket is down even while mutations remain safe through healthy API.

## Source-of-truth invariant

PostgreSQL/API-confirmed domain state remains canonical.

Local cache may be:
- last known canonical state;
- draft;
- pending intent;
- recovery evidence.

It must never be rendered indistinguishably from confirmed server state.

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
- Bar/Kitchen may receive update via polling until realtime recovers.

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

- detect online/offline as hint only;
- health/revalidation determines actual state;
- Service Worker may cache shell and safe read data;
- no service-worker fabricated API success;
- on resume/reconnect, refresh active Tab/menu/queue before enabling sensitive actions;
- pending draft data may persist locally.

## Redis/WebSocket unavailable with API healthy

This is **not OFFLINE**.

Behavior:
- mutations continue through API;
- banner/status becomes RECONNECTING then STALE if threshold exceeded;
- clients poll active critical views with bounded cadence;
- server response remains canonical;
- no duplicate local event bus becomes source of truth;
- after socket recovery, client performs full revalidation before trusting incremental events.

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

- /health or lightweight reachability;
- command idempotency envelope;
- mutation response with server_version;
- conflict response with current canonical state;
- recovery reconciliation endpoints;
- realtime resume cursor or full-refresh instruction.

## Metrics/events

Technical/operational:
- connectivity state duration;
- realtime disconnect count;
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
