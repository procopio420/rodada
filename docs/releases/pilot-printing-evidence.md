# Workstream D — printing, fiscal and operations

Baseline: d07ca67, fresh local execution 2026-10-12. PostgreSQL 17 Docker instance
`rodada-pilot-final-pg`, loopback 55512, disposable database; no merchant or real customer data.

Fresh focused PostgreSQL gate: 85 passed in 50.34s (printing snapshots, immutable document/job
semantics, concurrency/fencing, bridge, KDS detector and access invalidation). This first gate
preceded addition of the real HTTP redirect regression; repeat bridge/security gate follows.
FILE writes actual local artifact; LAN socket and CUPS subprocess boundaries are fault-injected.
No physical printer, actual CUPS queue, Wi-Fi or fiscal issuance is claimed.

Found/fixed bridge credential safety: authentication previously followed urllib redirects and
accepted prefix-only API URLs. API/refresh now refuse redirects and validate credential-free
HTTPS origin (HTTP only explicit loopback). Regression starts two actual local HTTP origins
and verifies no credential reaches redirected destination. Spec015 records the contract.

KDS detector remains observational; auto fallback disabled, heartbeat producer/runtime
certification outstanding. Receipt immutable snapshots and audited linked uncertain-delivery
reprints remain canonical. Onsite procedure and incident/VR System rollback runbooks accompany
this release. Fiscal type/regime/provider/contingency needs owner/accountant decision.

Logs retained locally: `/tmp/rodada-pilot-print-tests.log`, `/tmp/rodada-pilot-bridge-tests.log`;
CI links and integrated-SHA repeat results will be recorded in the final manifest.
