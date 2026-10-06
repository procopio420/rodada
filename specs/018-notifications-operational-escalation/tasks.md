# Tasks — Spec 018

## Domain/API
- [ ] Define typed AlertRule kinds/config schema.
- [ ] Define OperationalAlert lifecycle.
- [ ] Define deterministic dedupe keys per rule.
- [ ] Define acknowledgement policy per rule.
- [ ] Define auto-resolution semantics.
- [ ] Define severity/escalation policy.
- [ ] Define structured deep-link targets.
- [ ] Active/history/detail queries.
- [ ] Acknowledge command.
- [ ] NotificationPreference command/query.

## Persistence
- [ ] Unique active alert per dedupe key.
- [ ] Alert lifecycle/provenance history.
- [ ] NotificationDelivery + idempotency.
- [ ] Preference storage.
- [ ] Rule/version storage.
- [ ] Repeat-of/episode linkage.

## Staff Web/PWA
- [ ] Gerência consumes canonical OperationalAlert list.
- [ ] In-app alert detail.
- [ ] Acknowledge where supported.
- [ ] Deep-link exact context.
- [ ] Resolved/stale-alert state.
- [ ] Optional notification preferences.

## Android
- [ ] In-app operational alerts relevant to staff scope.
- [ ] Push token/device registration.
- [ ] Push deep-link routing.
- [ ] Fetch canonical alert on open.
- [ ] No unsafe action from stale/offline push context.

## Guest
- [ ] No generic staff alert exposure.
- [ ] Guest service requests remain DispatchTasks; alerting only escalates staff side.

## Realtime
- [ ] Alert activate/update/resolve invalidation.
- [ ] Poll/API recovery when realtime unavailable.
- [ ] No client-side duplicate alert evaluator.

## Management
- [ ] Migrate Spec 007 alert cards to OperationalAlert.
- [ ] Alert history/timeline.
- [ ] Severity/filtering.
- [ ] Resolution/ack timestamps.
- [ ] Noise/flapping diagnostics.

## Infra/integration
- [ ] Push provider adapter boundary.
- [ ] Idempotent delivery worker.
- [ ] Retry/backoff.
- [ ] Delivery observability.
- [ ] Privacy-safe payload template.

## Quality/tests
- [ ] Duplicate source event creates one active alert.
- [ ] Cooldown suppresses delivery, not alert visibility.
- [ ] Ack does not resolve.
- [ ] Canonical condition clear auto-resolves.
- [ ] Escalation does not create duplicate episode.
- [ ] Resolved condition returning creates new episode.
- [ ] Push failure does not lose alert.
- [ ] Deep-link authorization rechecked.
- [ ] Normal new order/payment does not alert by default.
- [ ] No employee leaderboard derived from alerts.
