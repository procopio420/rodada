# Tasks — Spec 014 — Realtime, Connectivity & Degraded Operation

## Frontend piloto — 10/10/2026
- [x] Mostrar inventário local legível de pendências, sem descarte/replay automático.
- [x] Preservar bloqueio de outra sessão/coleção ilegível e registrar dependência da revisão canônica.

## Architecture/contracts
- [x] Define one cross-surface event envelope and versioning rules.
- [x] Define SSE endpoint/subscription authorization by Venue/surface.
- [x] Define snapshot/read-model endpoints used before incremental streaming.
- [x] Define resume cursor / Last-Event-ID semantics and retention window.
- [x] Define explicit cursor-gap/full-refresh-required behavior.
- [x] Document WebSocket as exception-only with criteria for introducing it.
- [x] Define shared client connectivity/freshness semantics across Android/PWAs.

## Domain/API
- [x] Keep canonical mutations on authenticated HTTP command endpoints.
- [ ] Define command envelope/idempotency metadata.
- [ ] Define conflict/replay result taxonomy.
- [ ] Define PendingOrderIntent server reconciliation.
- [ ] Define offline financial recovery record reconciliation.
- [x] Expose server versions/freshness where required.
- [x] Define safe Class A/B/C/D classification registry/documentation.

## Persistence/event delivery
- [x] Add transactional outbox written atomically with publishable domain changes.
- [x] Add outbox dispatcher with at-least-once delivery semantics.
- [x] Ensure Redis/PubSub, if used, is only ephemeral fan-out/coordination.
- [x] Add bounded replay storage/cursor lookup sufficient for reconnect policy.
- [x] Make event/projection consumers idempotent.
- [x] Server idempotency/result mapping.
- [x] Recovery record persistence.
- [ ] Applied/rejected replay provenance.
- [x] Realtime resume/revalidation metadata if used.

## Android
- [x] HTTP command + SSE/fetch-stream realtime client.
- [x] API + realtime state machine.
- [ ] Persist safe cached projections and latest accepted resume cursor.
- [ ] Persistent pending queue.
- [x] Persist encrypted, typed recovery envelopes for already idempotent Order, Payment, Correction, Refund, CashMovement and DeliveryCompletion commands; no untyped command dump or secrets.
- [ ] Pending/syncing/conflict/confirmed UI.
- [ ] Pending order draft.
- [ ] Emergency cash evidence capture.
- [ ] External-terminal evidence capture.
- [x] Foreground/reconnect revalidation.
- [x] Backoff/jitter.
- [x] No blind payment retry.

## Operational Web/PWA — Cozinha / Bar / Gerência
- [x] Cacheable lightweight app shell with no SSR dependency for live operation.
- [x] Persist safe projections/cursor in IndexedDB or equivalent where useful. Safe projections use sessionStorage; cursor stays in memory and reload deliberately takes a new snapshot.
- [x] Render last-known safe projection before waiting for network refresh.
- [x] ONLINE/RECONNECTING/STALE/OFFLINE states.
- [x] SSE client with reconnect/resume.
- [x] Bounded revalidation/poll fallback when SSE is unavailable.
- [x] Update only affected projection/components for incoming events.
- [x] Cached reads with last-update timestamp.
- [ ] Draft persistence where safe.
- [x] Revalidate before sensitive mutation after reconnect.

## Guest
- [x] Use the same snapshot + SSE + freshness protocol within guest authorization scope.
- [x] Offline/stale menu messaging.
- [x] Local cart allowed without fake submit success.
- [x] Block payment/service-request confirmation offline. Guest exposes no payment/service-request submission in this slice; no offline success path was added.
- [x] Revalidate session/occupancy on reconnect.

## Realtime
- [x] SSE failure does not disable healthy HTTP API.
- [x] Resume from last accepted cursor after transient disconnect.
- [x] Replay duplicate delivery safely.
- [x] Detect expired/unknown/gapped cursor and force snapshot revalidation.
- [x] Bounded polling/revalidation fallback.
- [x] Prove one committed event can update multiple authorized surfaces without client-to-client calls.

## Management
- [x] Connectivity health indicator.
- [ ] Recovery/conflict queue for authorized managers.
- [x] Do not count pending local financial evidence as received.

## Infra/integration
- [x] Fault-injection tests/runbook.
- [x] API health endpoint.
- [ ] Observability for disconnect/replay/conflict.
- [x] Sustained outage manual runbook.

## Quality/tests
- [x] Timeout after commit + retry does not duplicate order/payment.
- [x] Stale AVAILABLE cannot bypass server validation.
- [x] SSE/event delivery down + API healthy remains operational.
- [x] Redis restart cannot erase a committed outbox fact.
- [x] Reconnect from a valid cursor receives missed events without a duplicate domain mutation.
- [x] Unrecoverable cursor gap forces canonical snapshot before incremental trust.
- [x] Duplicate realtime delivery leaves client projection correct.
- [x] Cached operational PWA state appears without blocking on network.
- [x] Cozinha/Bar do not require a giant shared frontend bundle to consume shared contracts.
- [ ] Revoked actor replay rejected.
- [ ] App restart preserves pending intents.
- [x] Payment CONFIRMATION_PENDING blocks blind retry.
- [ ] Recovery conflict requires explicit review.
- [x] No PAN/CVV/secrets in local queue.

## Verification — operational realtime slice (2026-10-09)

Checked items describe this implementation or preserved, tested existing safeguards;
unchecked items belong to the broader degraded-operation rollout and are not claimed
as delivered by the realtime PR. See [delivery evidence](../../docs/development/operational-realtime.md).

- PostgreSQL backend suite: 224 passed; final realtime + full-shift regression: 20 passed.
- Web: typecheck/build, eight transport fault tests and all 110 visual gates passed.
- Android: 32 unit tests, assembleDebug and lintDebug passed. Existing typed encrypted
  recovery envelopes and original idempotency keys remain intact.
- Live PostgreSQL/ASGI: durable publication in a separate process, actual Redis restart,
  replay, duplicate HTTP command, cursor reset and connected revocation passed.
- Real browser: persisted guest history/status, live updates, offline shell reload,
  safe cache timestamps and disabled offline commands passed.
- Real Web integration: all five PostgreSQL-backed workflows passed.

Remaining work includes durable Android operational projections, generalized offline
intent/reconciliation flows, emergency evidence capture and production observability/
capacity measurement. Android reload always bootstraps from canonical reads; Class C
fulfillment is disabled. The existing encrypted recovery store is preserved, rather
than expanded into a generic offline command queue.
