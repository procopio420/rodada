# ADR 0009 — HTTP Commands, SSE Realtime and Transactional Outbox

**Status:** Accepted  
**Date:** 2026-10-06

## Context

Rodada has specialized operational surfaces: Atendimento, Cozinha, Bar, Cliente and Gerência. Most realtime traffic is server-to-client state propagation, while user actions are discrete commands.

The system must remain responsive on modest phones/tablets, tolerate unstable venue networks, avoid duplicate financial/ordering effects and never make Redis or a live connection the source of truth.

## Decision

1. PostgreSQL-backed domain state remains canonical.
2. Canonical mutations use authenticated HTTP command endpoints.
3. SSE (`text/event-stream`) is the default server-to-client realtime transport.
4. WebSocket requires an explicit continuous bidirectional use case that HTTP + SSE cannot satisfy cleanly.
5. Clients bootstrap from a canonical snapshot/read model and then consume incremental events.
6. Reconnect uses a stable resume cursor / `Last-Event-ID` equivalent.
7. If continuity cannot be proven because the cursor is expired/unknown/gapped, the client fetches a new canonical snapshot before trusting later deltas.
8. Publishable domain mutations write a transactional outbox record in the same PostgreSQL transaction as the canonical state change.
9. Outbox delivery is at-least-once; consumers and client projections must be idempotent.
10. Redis may provide fan-out, wakeups or ephemeral coordination, but never be the only durable record that an event occurred.
11. Operational PWAs use a cacheable lightweight shell and may persist safe projections/cursors locally so startup does not block on the network. Android follows the same protocol with native durable storage.

## Consequences

### Positive

- realtime failure does not disable a healthy command API;
- simpler transport for the dominant server -> client traffic;
- deterministic reconnect/recovery;
- committed facts survive Redis/process restarts;
- specialized clients can stay small while sharing contracts;
- the backend remains the single authority across all surfaces.

### Tradeoffs

- requires outbox cleanup/monitoring and replay retention policy;
- SSE connection/auth/proxy behavior must be tested in production infrastructure;
- duplicate delivery is expected and must be handled;
- some future feature may still justify WebSocket and will need its own rationale.

## Related

- Spec 014 — Realtime, Connectivity & Degraded Operation
- ADR 0001 — Modular Monolith
- `docs/architecture/overview.md`
