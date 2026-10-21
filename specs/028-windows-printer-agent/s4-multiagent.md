# S4 — multiagent execution contract

Risk R3; extends S3, reuses the sole PrintJob queue/attempt token and 60s lease.
Several explicitly assigned routes may be enabled for one endpoint. Each agent can
claim only its own fresh, non-OFFLINE observations. Priority orders that agent's
routes; it is not a promise of global leader election. First eligible poll wins
the existing PostgreSQL job lock; another installation never receives that token.
An absent discovery becomes OFFLINE immediately. No inferred USB/shared access.

A confirmed pre-send FAILED_RETRYABLE permits a fresh fenced attempt, including
another explicitly assigned route, after existing backoff. SENDING, SPOOL_ACCEPTED
and DELIVERY_UNCERTAIN never fail over. Expiry/crash/revocation after possible
submission stays uncertain; remote fencing cannot retract bytes in a Windows call.
No claim of physical exactly-once delivery. Credential and Venue checks apply on
all claims/results. Late results cannot finish a newer attempt. Route changes
preserve original attempt ownership/version, and discovery never merges devices.

Required evidence: real PostgreSQL two-installation race; pre-send failover versus
uncertain no-failover; stale/offline observation; revocation; cross-agent fencing;
existing cross-Venue, pairing, route CAS, confirmed pipeline and legacy regressions.

Rollback: before reversing migration 0014, explicitly disable extra enabled routes
until each endpoint has at most one. Reverse migration fails closed if that is not
satisfied; it must not silently discard assignments or select a physical printer.

Post-review validation adds manager API/CAS coverage for enabling a second route
and observation reappearance restoring only its explicitly assigned queue. These
are real PostgreSQL cases, not simulated database locking.
