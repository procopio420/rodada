# Spec025 — concurrently integrated printer pairing boundary

The final operational audit was prepared on637b8e6. Concurrent PR155 integrated
new pairing credentials/schema as974e0bc; current main9082351 also contains the
independent release-registry correction171. Do not extend old-SHA PASS to this
new auth boundary without regression evidence.

Existing product policy is preserved: anonymous native pairing uses a strong
installation proof/capability before staff approval; no Venue exists before that
approval. Valid proof/status is not a host-selected staff identity. Manager
sessions and issued machine credentials must remain Venue/Host scoped, BFF must
not forward native bootstrap/machine endpoints, and invalid proof cannot disclose
a credential. Operational print-agent enablement/delivery remains off.

Add only missing regressions in disposable PostgreSQL: staff list/configure and
machine heartbeat A/A, B/B, A/B, B/A; foreign ID cannot revoke a different Venue's
agent; wrong-host approval cannot consume a pairing request or create a credential;
own-host approval succeeds once and replay creates no duplicate; invalid proof
is rejected on either Host without credential disclosure. Native bootstrap and
initial credential issuance use the existing public API in synthetic fixtures.

These tests do not execute native agents, pair printers, enable operational
printing, create orders or payments, or alter Railway. Full existing API/Web gates
and independent final-head review remain required. Local integrated isolation
results and operational SHA/deployments are recorded in the final audit checkpoint.
