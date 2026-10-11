# Four-track gap closure execution — 2026-10-11

This is an execution record, not production certification. No new criterion is PASS until complete behavior is reproduced at the integrated SHA. Test money only; no production database, provider activation, Railway deployment or physical printer claim.

## Baseline and isolation

Remote main began at ddf889af2871c74488b036cfbe8f2db54f3620b8 (plan commit; parent 2aef9d3663db0a34ece49c87299b5ff3e37596dd). Terminal clone failed immediately because proxy:8080 was unreachable. Docker local socket returned operation not permitted. Four agents ran concurrently using isolated connector-materialized source snapshots and separate local branches; these are not full-history worktrees. Remote commits are built against the current real Git tree, preserving all unmodified files. GitHub Actions provides actual PostgreSQL/Web/Android execution; static local checks are identified separately.

#71 reviewed and merged fa8456bc2fbb8fde4ccb95ee4134c45752e1a702 after API/Web/Docker smoke success on 973faec4f343b158fb25767a69c9ab32d8e41e90. #72 originally failed because the test asserted the queue before asynchronous UI completion. Commit 27755c55d8c9ac2577dba40a7182a2089ca92ec3 waits for the completed control to disappear while retaining the canonical empty-queue assertion; Web and Docker smoke passed. #72 merged f40382a25dc7813f4bcdf5ec64e9b54974e864fc.

## Ownership and integration contracts

| Agent | Contract | Owned files | PR | Dependencies |
| --- | --- | --- | --- | --- |
| A | Original key/actor/device/session preserved; typed order intent lifecycle; no financial replay from order queue | Android operations and Spec014; later recovery-only backend | Pending | Existing authenticated order/idempotency API |
| B | Typed station preview/apply, version and blockers; station_snapshot(venue_id, station); Venue NO KEY UPDATE before Tab/Product | venue station model/service/views/migration; ordering confirm hook; coordinated root routes | #73 | Existing confirmed snapshot routing |
| C | Immutable as-of DailyClose revision, repeatable-read coherent facts, separate review/corrections; Venue before authority lock | cash daily_close files/models/migration; payment_summaries helper; coordinated root routes | #74 | #71 aggregation reused; B lock order |
| D | Server-timed perdevice KDS observation, station aggregate sustained failure/recovery | documents_printing kds/models/views/local URLs/migration | #75 | D2 consumes B station configuration and existing printing dedupe |

Root route changes were prepared independently against fa8456bc, and must be combined sequentially on integration. Do not replace another slice's routes with a whole older URL file.

## Acceptance execution matrix

| Agent | Spec / AC | Implementation / commit | PR / merge | Validation commands / environment / result | CI | Remaining work | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 014-002/003/004/005/013/014/015 | Android A1 in progress | Pending | API36 process-death/emulator not executed | Pending | Publish A1; prove durable queue and review UI; A2 evidence | P0 |
| B | 013-003; related 013-001/009/013 | apps/api/modules/venue/stations.py; station_views.py; models.py; ordering/services.py; migration0006; commit62d3076ca3ecee97b1b9f54a6d5734e3c1628ea6 | #73 draft/unmerged | compileall, git diff --check locally passed; python manage.py check and makemigrations --check --dry-run Actions passed | PostgreSQL/Web/smoke running | Finish behavior gates then sequential merge; B2 global block, B3 policies/provider/UI | P0 |
| C | 007-007/008; 012-009/010/011/012/013 | cash/daily_close.py, daily_close_models.py, daily_close_views.py, payment_summaries.py, migration0003; commit435eb1d785d44ec21020aa11493161df32043386 | #74 draft/unmerged | compileall/diffcheck passed; Django checks and migration drift Actions passed | PostgreSQL/Web/smoke running | Resolve failures, review financial invariants; mobile workflow and correction approval evidence | P0 |
| D | 015-009 foundation | documents_printing/kds.py, kds_views.py, models.py, migration0005, tests/test_kds_health.py; commit629607ec99023b2979d2f9885af3db04812bb335 | #75 draft/unmerged | compileall/diffcheck passed only | PostgreSQL/Web/smoke running | D2 deduped auto jobs, Web producer and management; hardware validation | P0 / external |

## Failure injection: actual evidence status

| Scenario | Actual result | Evidence / next execution |
| --- | --- | --- |
| Timeout after committed Order retry | New A regression pending; inherited API idempotency retained | Must execute against integrated SHA |
| Android process killed/reopened | NOT EXECUTED | API36 emulator unavailable locally |
| Product unavailable on reconnect | New A/B all-or-nothing tests authored, runtime pending | PostgreSQL Actions |
| Revoked operator replay | A/D tests authored, runtime pending | PostgreSQL Actions and Android |
| R$50 evidence / R$30 balance | NOT IMPLEMENTED this slice | A2 review evidence model, no automatic Payment |
| Ambiguous card/Pix duplicate charge | Existing contracts retained; combined fault injection NOT EXECUTED | A2 + provider simulation |
| Unsafe station disable with active queue | B tests authored, runtime pending | PR73 PostgreSQL |
| Concurrent manager station edits | B two-worker test authored, runtime pending | PR73 PostgreSQL |
| KDS oscillation / revoked observation | D tests authored, runtime pending | PR75 PostgreSQL |
| 100 assessments + two workers | D1 tests one health row/no jobs; D2 ticket dedupe NOT IMPLEMENTED | Keep AUTO_FALLBACK disabled |
| Open cash shift close | C tests authored, runtime pending | PR74 PostgreSQL |
| Late correction immutable original | C SQL trigger + separate projection tests authored, runtime pending | PR74 PostgreSQL |
| Concurrent payment/close snapshot | C repeatable-read race authored, runtime pending | PR74 PostgreSQL |
| Full QR→order→production→payments→DailyClose shift | NOT EXECUTED for four-track integrated SHA | Required combined release gate |
| Physical printer / PSP / BYOD certification | EXTERNAL_BLOCKED | Site devices/providers required |

## Residual backlog

P0 software: execute/review all first-slice CI; integrate sequentially and rerun actual main regression; finish financial recovery evidence/review; global guest emergency block; automatic print jobs/provenance; management close UI; complete isolated full-shift/failure matrix.

P1 software: effective-dated calendar and service policy versions; provider redacted status projection; recovery observability/fault injection; management station/KDS controls; separately approved post-close correction workflow.

P2 software: monthly reports, occupancy comparisons and remaining Spec007 insights; complete push/floorplan acceptance separately.

External: API36 physical/process-death walkthrough and BYOD availability, kitchen/bar printers/paper/driver checks, real PSP credentials and certification. No production readiness claimed.

