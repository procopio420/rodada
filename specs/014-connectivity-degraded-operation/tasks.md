# Tasks — Spec 014 — Realtime, Connectivity & Degraded Operation

## Architecture/contracts
- [ ] Define one cross-surface event envelope and versioning rules.
- [ ] Define SSE endpoint/subscription authorization by Venue/surface.
- [ ] Define snapshot/read-model endpoints used before incremental streaming.
- [ ] Define resume cursor / Last-Event-ID semantics and retention window.
- [ ] Define explicit cursor-gap/full-refresh-required behavior.
- [ ] Document WebSocket as exception-only with criteria for introducing it.
- [ ] Define shared client connectivity/freshness semantics across Android/PWAs.

## Domain/API
- [ ] Keep canonical mutations on authenticated HTTP command endpoints.
- [ ] Define command envelope/idempotency metadata.
- [ ] Define conflict/replay result taxonomy.
- [ ] Define PendingOrderIntent server reconciliation.
- [ ] Define offline financial recovery record reconciliation.
- [ ] Expose server versions/freshness where required.
- [ ] Define safe Class A/B/C/D classification registry/documentation.

## Persistence/event delivery
- [ ] Add transactional outbox written atomically with publishable domain changes.
- [ ] Add outbox dispatcher with at-least-once delivery semantics.
- [ ] Ensure Redis/PubSub, if used, is only ephemeral fan-out/coordination.
- [ ] Add bounded replay storage/cursor lookup sufficient for reconnect policy.
- [ ] Make event/projection consumers idempotent.
- [ ] Server idempotency/result mapping.
- [ ] Recovery record persistence.
- [ ] Applied/rejected replay provenance.
- [ ] Realtime resume/revalidation metadata if used.

## Android
- [ ] HTTP command + SSE/fetch-stream realtime client.
- [ ] API + realtime state machine.
- [ ] Persist safe cached projections and latest accepted resume cursor.
- [ ] Persistent pending queue.
- [ ] Persist encrypted, typed recovery envelopes for already idempotent Order, Payment, Correction, Refund, CashMovement and DeliveryCompletion commands; no untyped command dump or secrets.
- [ ] Pending/syncing/conflict/confirmed UI.
- [ ] Pending order draft.
- [ ] Emergency cash evidence capture.
- [ ] External-terminal evidence capture.
- [ ] Foreground/reconnect revalidation.
- [ ] Backoff/jitter.
- [ ] No blind payment retry.

## Operational Web/PWA — Cozinha / Bar / Gerência
- [ ] Cacheable lightweight app shell with no SSR dependency for live operation.
- [ ] Persist safe projections/cursor in IndexedDB or equivalent where useful.
- [ ] Render last-known safe projection before waiting for network refresh.
- [ ] ONLINE/RECONNECTING/STALE/OFFLINE states.
- [ ] SSE client with reconnect/resume.
- [ ] Bounded revalidation/poll fallback when SSE is unavailable.
- [ ] Update only affected projection/components for incoming events.
- [ ] Cached reads with last-update timestamp.
- [ ] Draft persistence where safe.
- [ ] Revalidate before sensitive mutation after reconnect.

## Guest
- [ ] Use the same snapshot + SSE + freshness protocol within guest authorization scope.
- [ ] Offline/stale menu messaging.
- [ ] Local cart allowed without fake submit success.
- [ ] Block payment/service-request confirmation offline.
- [ ] Revalidate session/occupancy on reconnect.

## Realtime
- [ ] SSE failure does not disable healthy HTTP API.
- [ ] Resume from last accepted cursor after transient disconnect.
- [ ] Replay duplicate delivery safely.
- [ ] Detect expired/unknown/gapped cursor and force snapshot revalidation.
- [ ] Bounded polling/revalidation fallback.
- [ ] Prove one committed event can update multiple authorized surfaces without client-to-client calls.

## Management
- [ ] Connectivity health indicator.
- [ ] Recovery/conflict queue for authorized managers.
- [ ] Do not count pending local financial evidence as received.

## Infra/integration
- [ ] Fault-injection tests/runbook.
- [ ] API health endpoint.
- [ ] Observability for disconnect/replay/conflict.
- [ ] Sustained outage manual runbook.

## Quality/tests
- [ ] Timeout after commit + retry does not duplicate order/payment.
- [ ] Stale AVAILABLE cannot bypass server validation.
- [ ] SSE/event delivery down + API healthy remains operational.
- [ ] Redis restart cannot erase a committed outbox fact.
- [ ] Reconnect from a valid cursor receives missed events without a duplicate domain mutation.
- [ ] Unrecoverable cursor gap forces canonical snapshot before incremental trust.
- [ ] Duplicate realtime delivery leaves client projection correct.
- [ ] Cached operational PWA state appears without blocking on network.
- [ ] Cozinha/Bar do not require a giant shared frontend bundle to consume shared contracts.
- [ ] Revoked actor replay rejected.
- [ ] App restart preserves pending intents.
- [ ] Payment CONFIRMATION_PENDING blocks blind retry.
- [ ] Recovery conflict requires explicit review.
- [ ] No PAN/CVV/secrets in local queue.
