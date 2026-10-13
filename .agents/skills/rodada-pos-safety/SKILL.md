---
name: rodada-pos-safety
description: Use for cross-cutting financial safety, multi-tenant authorization, idempotency, connectivity recovery or production-readiness reviews in Rodada API, Web or Android.
---

# Rodada POS safety and transaction integrity

## Activate for
Any task affecting `Tab` balance, `Order`, `Charge`, payment/refund, cashier shift, Venue access/Host, QR/guest session, offline queue or recovery from an ambiguous mutation. Pair with the stack-specific skill; this one is deliberately cross-cutting.

## Threat and failure model
Read [product invariants](../../../docs/product/principles.md), [domain architecture](../../../docs/architecture/overview.md), [agent procedures](../../../docs/agents/PROCEDURES.md), and the relevant spec. At minimum examine:
- Double click, duplicated idempotency key, same key with different body, concurrent operators, answer lost after database commit, stale client state.
- Staff with valid token on foreign Venue Host; guest session/QR reused after occupancy release, malicious forwarded headers, cross-Venue ID and SSE cursor.
- PSP callback duplicate/out of order, pending/unknown payment, refund race and money mismatch.
- App restart, offline/reconnect, session rotated or revoked during replay.

## Non-negotiable invariants
- Identity optional, Tab mandatory; Order always on Tab; Table occupancy never owns financial ledger.
- Settlement only from observed canonical ledger/provider outcomes. `pending`/timeout never means paid. Monetary amounts are integer cents.
- Corrections, discounts, refunds and adjustments preserve provenance and append-only audit records; no silent deletion to make state look clean.
- Venue is the authorization partition. Deny cross-Venue auth/reads/writes/event streams; host/QR labels are not security credentials by themselves.
- Immutable request intent and idempotency token survive retry; same action gets one effect or explicit conflict, with canonical readback.
- Trust the server, not disabled UI or SSE. All clients see same product availability and blocked sales.

## Verify and report
For every impacted invariant, define one happy and at least one negative test. Run PostgreSQL concurrency/locking tests, permission + two-Venue negatives, duplicate and lost-response scenarios, and mobile/app lifecycle if applicable. Include precondition, exact actions, expected canonical DB state, operator/audit and evidence SHA. Never mutate actual customer transactions to "test" safety. Keep production, payment-provider and fiscal GO separate from green CI.
