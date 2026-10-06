# Tasks — Spec 014

## Domain/API
- [ ] Define command envelope/idempotency metadata.
- [ ] Define conflict/replay result taxonomy.
- [ ] Define PendingOrderIntent server reconciliation.
- [ ] Define offline financial recovery record reconciliation.
- [ ] Expose server versions/freshness where required.
- [ ] Define safe Class A/B/C/D classification registry/documentation.

## Persistence
- [ ] Server idempotency/result mapping.
- [ ] Recovery record persistence.
- [ ] Applied/rejected replay provenance.
- [ ] Realtime resume/revalidation metadata if used.

## Android
- [ ] API + realtime state machine.
- [ ] Persistent pending queue.
- [ ] Pending/syncing/conflict/confirmed UI.
- [ ] Pending order draft.
- [ ] Emergency cash evidence capture.
- [ ] External-terminal evidence capture.
- [ ] Foreground/reconnect revalidation.
- [ ] Backoff/jitter.
- [ ] No blind payment retry.

## Staff Web/PWA
- [ ] ONLINE/RECONNECTING/STALE/OFFLINE states.
- [ ] Poll fallback when WebSocket unavailable.
- [ ] Cached reads with last-update timestamp.
- [ ] Draft persistence where safe.
- [ ] Revalidate before sensitive mutation after reconnect.

## Guest
- [ ] Offline/stale menu messaging.
- [ ] Local cart allowed without fake submit success.
- [ ] Block payment/service-request confirmation offline.
- [ ] Revalidate session/occupancy on reconnect.

## Realtime
- [ ] Socket failure does not disable healthy API.
- [ ] Full refresh after reconnect before incremental trust.
- [ ] Bounded polling fallback.

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
- [ ] WebSocket down + API healthy remains operational.
- [ ] Revoked actor replay rejected.
- [ ] App restart preserves pending intents.
- [ ] Payment CONFIRMATION_PENDING blocks blind retry.
- [ ] Recovery conflict requires explicit review.
- [ ] No PAN/CVV/secrets in local queue.
