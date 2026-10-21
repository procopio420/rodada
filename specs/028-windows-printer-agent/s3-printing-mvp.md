# S3 Printing MVP — contract before implementation

Base: S2 merged with owner authorization in PR155, SHA974e0bc.
Risk R3: executable print authority, physical side effects and tenant identity.

Reuse PrintJob/PrintAttempt, recover_expired/claim_job/finish_attempt, immutable
ReceiptDocument and Spec015 renderers. No second queue/dedupe or new order trigger.
Add AGENT endpoint adapter so legacy bridge cannot claim machine-owned delivery.
Bind each attempt to agent, route and version; one enabled route per endpoint in
S3. Route edits never redirect existing attempts. S4 generalizes multiple routes.

Version1 discovery reports service-context queues (healthUNKNOWN unless observed)
and explicitly configured private TCP addresses. Manager creates/enables a route
with CAS; WindowsDriver is default. RAW requires an explicit manager attestation
for that route; discovery or vendor/model text cannot assert RAW compatibility.
Generic ASCII ESC/POS and Windows rendered text reuse the backend015 layout.
Cut/QR/status remain disabled; profiles/certification belong to S5/S7.

Machine claims are scoped server-side to eligible assigned routes; no arbitrary
endpoint IDs. Use existing60s lease/fencing and conservative expiry =>UNCERTAIN.
Crash after claim, before/during/after submission never causes automatic replay;
new claims cannot retrieve SENDING/UNCERTAIN. Result retries may repeat the same
token and outcome, never submit again. Transport only reports FAILED_RETRYABLE
when failure is proven before a side-effectful call; otherwise UNCERTAIN.
Spool job ID or transmitted bytes are observations, never physical confirmation.

Positive/negative gates: genuine PostgreSQL claim races, tenant/revoke/stale
result/CAS/legacy compatibility and full confirmed document flow. Fake spool/GDI
and TCP fault tests prove RAW gating, rendered-vs-RAW separation, pre-send vs
ambiguous failure. Windows runner imports actual APIs/service context. Hardware
and physical paper remain explicitly pending for S7.

Review corrections: route approval refetches and locks the current observation,
requires its displayed configuration fingerprint, and disables/increments routes
when queue or driver changes. Manage freezes the inspected fingerprint and requires
renewed inspection/attestation after polling detects a change. Inventory capped500
records per installation,100 per report; no discovery creates/merges logical printers.

Claims include a bounded remaining TTL with5s safety reserve. Agent measures from
before the HTTP request using a monotonic clock (conservatively includes transit),
checks after preparation and at transport entry; native StartDoc* and TCP write
also recheck after connection/setup. Expired claims perform no submission. A driver
already entered may block beyond lease; this remains uncertain/manual inspection,
not a promise that a remote fence can cancel an already-running Windows call.

Local evidence so far:28agent fault/native-API tests, mypy strict10files;15PostgreSQL
API/race/pipeline tests;80printing/foundation/pairing regressions before final review
corrections. Full final-head CI, responsive screenshots and R3 re-review pending.

## S3 recovery follow-up (2026-10-20)

Confirmed main baseline: `4652b3013e69fa8e4f08a5a3a4e1f8c3a2720cfe`.
A partial RAW/GDI failure previously closed the handle without explicitly aborting
its open spool document. Best-effort AbortPrinter/AbortDoc now releases that
unfinished document; outcome remains DELIVERY_UNCERTAIN even if abort succeeds.
Abort cannot retract paper or authorize retry. Regression also verifies that a
failed durable journal write prevents any spool call. Existing service, discovery,
DPAPI journal, authenticated API and conservative lease semantics are reused.
Local Linux: 30 agent tests PASS; actual Windows service/native gate requires CI.
No physical validation, installer or slice-wide final acceptance is claimed here.
