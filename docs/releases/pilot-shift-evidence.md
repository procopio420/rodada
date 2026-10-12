# Pilot operational QA — 2026-10-12

Source under test: `d07ca67c1fde04b036b4b9cdecc43f212db82a14` (latest origin/main after the supplied initial SHA). Merged PR #83 was reviewed at
`a36e7889da168308d65e85ae4ce98040aaf01124`; #85 at
`efd33041b64237575e2589eddf0fc4cda53e184f`. Their previous results are historical,
not evidence for this release candidate.

## Changes

- Allow separate demo PostgreSQL/API/Web ports so parallel acceptance uses its
  own Compose project and persistent volume without reusing an existing demo.
  Bind host can be selected explicitly; existing default is preserved.
- Fix native network restoration acceptance: restored Android may choose wlan0
  after the originally cut eth0 loses its route. Verify a routed UP interface,
  preserve the all-uplinks-DOWN proof, and require wlan0 on physical Wi-Fi.
  Allow 60 seconds for asynchronous Android reconnection and print failed route.

The current main failure at
https://github.com/procopio420/rodada/actions/runs/38259788434 passed actual eth0
cut, no alternate route, committed 201, encrypted intent retention and offline
force-stop, but rejected the recovery route. This is an acceptance-harness defect,
not evidence of duplicated orders or confirmed payments.

## Fresh execution

Disposable Docker project `rodada-pilot-shift-20261012`, PostgreSQL 17 on loopback
55579, API 18874, Web 3219. No merchant, real customer, production database or
provider settlement used. Payment classification is `MANUAL_TEST`.

```sh
COMPOSE_PROJECT_NAME=rodada-pilot-shift-20261012 \
RODADA_DEMO_DB_PORT=55579 RODADA_DEMO_API_PORT=18874 \
RODADA_DEMO_WEB_PORT=3219 RODADA_DEMO_BIND_HOST=127.0.0.1 \
RODADA_DISPOSABLE_DB_ACK=1 bash scripts/verify-aderlan-full-shift.sh
```

The full shift has freshly passed and survived DB/API/dispatcher/Web restart:
8900 cents gross/received, 600 refunded, 8300 net received, zero open exposure,
14300 expected cash and zero discrepancy. PostgreSQL contractual regressions:
25 passed, including four-track shift, cash, payment concurrency, KDS and restore.
The 64-Tab workload passed: 8 clients, 1366 requests/1043 mutations, 204800 cents
both gross and received, zero open exposure/tabs. p95 HTTP latency 1409.27 ms,
p99 1702.77 ms; there is no pre-agreed latency SLA. Fresh DB/API/dispatcher/Web
restart then verified all 64 closed ledgers and canonical report totals.

Native Android API36 rooted emulator (`emulator-5580`) also freshly passed:
actual wlan0 DOWN, standby eth0 DOWN, no alternate route while committed 201 was
held; CHECKING intent retained encrypted; two process force-stops with offline
instrumentation; restored routed UP interface; same-key/body HTTP200 replay;
PostgreSQL exactly Order=1, Item=1, Charge=1, Payment=0. This exercises production
Android HTTP/recovery code through native instrumentation, not a complete Android
UI shift and not physical Wi-Fi. JVM: 55 tests, zero failures/errors; debug APK and
instrumentation APK builds passed. Hold-response evidence now identifies this
transport explicitly instead of incorrectly labeling it TCP reset.

Committed sanitized evidence: [shift artifacts](evidence/2026-10-12/shift/).
No staff access tokens or real merchant data are included. CI remains pending:
[Android disconnect](https://github.com/procopio420/rodada/actions/runs/38278598989),
[full pilot shift](https://github.com/procopio420/rodada/actions/runs/38278598947),
[integrated demo](https://github.com/procopio420/rodada/actions/runs/38278598937).
These local passes do not imply that pending CI or integrated-SHA gates passed.

## Physical/external acceptance

`EXTERNAL_BLOCKED`: Bar Wi-Fi, waiter physical phones, LAN printers, merchant
settlement and fiscal issuance have not been tested by this workstream. Execute
`docs/development/android-physical-wifi-cut-acceptance-2026-10-11.md` on an
explicitly disposable phone and isolated local PostgreSQL, connected to the bar's
actual AP, and attach route/link/201/intent/process-death/replay proof. Also conduct
one supervised complete shift with two waiters, Bar and Kitchen, cash closing,
manual terminal receipts and owner-signed ledger reconciliation before replacing
VR System. A native instrumentation gate is narrower than a complete UI shift.
