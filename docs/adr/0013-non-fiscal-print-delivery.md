# ADR 0013 — Non-fiscal documents and conservative print delivery

Status: Accepted for Spec 015 P0.

Documents freeze canonical OrderItem customization and ledger `totals` under the Tab lock.
A content fingerprint identifies financial revisions; production identity remains tied to the
confirmed Order and station. Financial mutations never call printer adapters. On-demand
production needs no automatic transaction hook, so paper outages cannot abort selling.

PostgreSQL stores jobs and attempt fencing tokens. Workers claim with SKIP LOCKED and a
60-second lease. Only provable failure before sending can retry, up to five attempts with
bounded exponential backoff. Expired sends and partial sends require operator inspection;
a late result cannot authorize another send. One initial production job exists across all
endpoints for a document. Failover is a linked, audited and marked copy.

HTML and plain text are portable artifacts. Browser Save PDF provides portable PDF without
adding a rendering service. ESC/POS output strips controls and transliterates to ASCII because
code pages and cuts vary by unverified printer model. Cut is explicit, off by default.
LAN TCP and CUPS adapters run behind an outbound local bridge with fixed local connection
references, never arbitrary network addresses supplied by client receipt data.

OUTPUT_READY and SPOOL_ACCEPTED do not mean paper exists. PRINTED requires an audited
operator confirmation. Browser dialog initiation is uncertain because cancellation/printing
cannot be observed reliably. Printer health remains advisory and UNKNOWN when sensors are
unavailable; bridge heartbeat is distinct from physical printer readiness.

Automatic KDS-health fallback, Android Bluetooth, and certified fiscal issuance remain
separate rollout decisions. The financial read model is owned by Ledger/Spec 011, not printing.
