# Bar do Aderlan — final pilot readiness

2026-10-12. **NO-GO for an actual customer pilot today.** The candidate has been implemented and rehearsed on disposable infrastructure, but authorized cloud deployment/identity, physical device/network/printer acceptance and owner/accountant fiscal contingency remain unverified. Integrated payments are independently NO-GO. This is not approval to replace VR System.

Pinned executable RC: `19dfc80e27f619a32c02518fad745e30db09830e` (`release/aderlan-pilot-rc-20261012`). [Manifest](aderlan-pilot-release-manifest.json), [onsite procedure](aderlan-onsite-acceptance.md), [incident/VR rollback runbook](aderlan-incident-runbook.md). Release reports are metadata; the tested source/image identity is fixed separately from subsequent documentation commits.

PASS means fresh evidence within the explicitly stated scope, PARTIAL means implementation with an incomplete gate, MISSING means absent engineering capability/evidence, and EXTERNAL_BLOCKED means account, physical or owner/accountant dependency. Automated test success does not establish production readiness.

## Phase 0 audit and scope

Initial requested main was `4228fb4efc9daba2cce5285c99cea9aaed450f92`. Fetched main initially `d07ca67c1fde04b036b4b9cdecc43f212db82a14`. Read repository AGENTS, core product/design/domain/architecture contracts, applicable Specs015/022, acceptance criteria, release reports and actual Railway/Docker/workflow configuration. No `.codegraph` directory exists. Inspected actual merged diffs: #83 native real-uplink interruption/durable reconciliation; #84 seven-surface smoke; #85 PostgreSQL full shift/64 Tabs/restart; #86 provider-origin and Pix non-settlement safety; #87 LAN bridge and fiscal checklist. Reused these implementations; historical green reports were not reused as fresh gates.

Main advanced during this mission. Included already merged operational/Android/correction changes before the final pin and repeated integrated gates; did not chase later open feature branches. At final audit #99 (Spec027 service claim) and #101 (tenant hostname implementation) remain open and excluded. Django Venue/guest isolation is tested separately; a proposed multi-tenant hostname deployment is not certified. No new database migrations were introduced by the four release workstreams; current-main migrations, including its later correction migrations, were applied to fresh PostgreSQL.

## Four parallel workstreams and integrated fixes

| Stream | Delivered and reviewed | Evidence / boundary |
| --- | --- | --- |
| A — Infrastructure | #94 image identity/version recorder and deployment/backup/rollback evidence; #96 explicit secure pilot startup and protected owner bootstrap; #104 origin authority correction | Fresh final image, zero-fixture start, migrations, login/browser/SSE, API order/QR, restore/restart. Railway credential Unauthorized; no cloud writes. |
| B — Complete shift | #92 isolated Docker ports and restored-interface recovery; #95 asynchronous uplink-cut observation; #100 stable canonical-state and native-route preflight | Existing full-shift/64-Tab/restart and native POST gates rerun. Emulator is native Android; physical Wi-Fi and entire final native UI shift remain separate gates. |
| C — Payments | #91 atomic refund reservation+provider reconciliation identity, offline duplicate replay and regressions | Timeout/unknown/pending/duplicate/refund safety tested. No private SDK, merchant approval or actual settlement claimed; activation checklist retained. |
| D — Printing/operations | #90 strict bridge API origin and no credential redirects; immutable document/adapter gates, onsite/fiscal acceptance and incident/VR runbooks | FILE/LAN/CUPS boundaries and failures tested; no printer paper/CUPS physical queue certified. Automatic fallback stays disabled. |

Additional integration fixes: #97 stabilized fixture time/SSE for visual checks without changing goldens or tolerances; #102 includes runtime-profile script in disposable full-suite image; #103 exposes unchanged native POST gate for exact-SHA dispatch. Each substantive workstream received independent peer review; #104 infrastructure review explicitly approved preserved authority and unchanged CSRF rules. Merge only followed relevant validation. Links: [#90](https://github.com/procopio420/rodada/pull/90), [#91](https://github.com/procopio420/rodada/pull/91), [#92](https://github.com/procopio420/rodada/pull/92), [#94](https://github.com/procopio420/rodada/pull/94), [#95](https://github.com/procopio420/rodada/pull/95), [#96](https://github.com/procopio420/rodada/pull/96), [#97](https://github.com/procopio420/rodada/pull/97), [#100](https://github.com/procopio420/rodada/pull/100), [#102](https://github.com/procopio420/rodada/pull/102), [#103](https://github.com/procopio420/rodada/pull/103), [#104](https://github.com/procopio420/rodada/pull/104).

## Requirement matrix

| Pilot requirement | Status | Evidence and remaining gate |
| --- | --- | --- |
| Pinned reproducible isolated local release | PASS | Exact RC image `sha256:cd1f2adb5ea06be98ed5e5bac183c7888008fc8071b540836efc5a60575d0137`, archived with checksum; loopback18095/private Docker network/new database. Dependencies float: promote this artifact, not an assumed identical rebuild. |
| Railway isolated staging / actual remote SHA | EXTERNAL_BLOCKED | CLI5.65.0 Unauthorized. Public HTML cannot attest commit, DB isolation or deployment policy. |
| HTTPS seven surfaces | PARTIAL | Fresh read-only public seven-route smoke passes; authenticated HTTPS cloud journeys and remote SHA unknown. |
| Secure pilot config / first owner | PASS | Final empty start: Venue/Staff/Product/Tab/Payment all zero; DEBUG/simulation false; protected hashed owner+audit; default guest blocked; restart preserves PIN. |
| Migrations / PostgreSQL / Django | PASS | Final fresh PostgreSQL17.11, 79 migrations; system check, no drift, migrate check and restored migration count. |
| Next.js / authentication / dispatcher / SSE | PASS (local) | Actual Chromium login with secure HttpOnly cookies; API/BFF snapshot and stream frames; final outbox10 events/0 unpublished. Public/device scope excluded. |
| Attendance/bar/kitchen/manage/cash/reports | PARTIAL | Seven local routes and actual browser auth/readback and232 visual/16 real BFF integration tests passed. Onsite devices and training unverified. |
| Deployed test order / QR | PASS (local) | Fresh final API order, two items/two charges1500c/zero payments, idempotent replay200, BAR/KITCHEN queues; opaque QR201; reblocked guest mutation403. |
| Complete shift /64 Tabs / restart reconciliation | PASS (disposable HTTP) | Fresh final full-shift workflow passed; never described as native UI shift or physical bar evidence. |
| Native Android POST interruption / durable queue | PARTIAL | Final uplink-cut job PASS. RST attempt1 failed to prove a live app PID before its second force-stop; same-SHA RST attempt2 PASS (one order/item/charge, zero payments, one original-key HTTP200 replay). Ten narrow offline lifecycle diagnostics passed but did not reproduce the failure; reliability remains PARTIAL. Prior443 pass is historical, not final evidence. |
| Entire native Android operational shift | PARTIAL | Earlier84 native login/order/cash/refund canonical readback closed one test Tab with zero exposure; cash-close stopped on expired token. Final complete UI shift NOT_RUN. |
| Physical handset / venue Wi-Fi | EXTERNAL_BLOCKED | No actual venue Wi-Fi/cellular fallback/force-stop drill performed. |
| Staff/guest/cross-Venue/revocation | PARTIAL | Final PostgreSQL593 tests (two API jobs plus integrated run) and Web gates passed; onsite role/device revocation still mandatory. |
| Manual cash/external-terminal financial flow | PARTIAL | Disposable ledger/shift tests; actual cash count/terminal receipts and operator signoff not performed. |
| Pending/duplicate/provider/refund safety | PARTIAL | Atomic refund fix and focused41 PostgreSQL tests passed; final593-test PostgreSQL regressions passed; contract tests are not provider settlement. No false confirmation or simulated real-money claim. |
| Live Pix/Paytime/SumUp/Tap on Phone | EXTERNAL_BLOCKED | No credentials, merchant eligibility/private SDK/device approval or sandbox settlement. Disabled until [activation checklist](pilot-payments-evidence.md) closes. |
| Immutable print docs/jobs and FILE/LAN/CUPS boundaries | PARTIAL | Final593 PostgreSQL suite and36 bridge regressions passed; actual FILE/loopback36-byte socket/failed port/CUPS subprocess boundary passed. CUPS executable is a local test stub, not a real queue. No paper delivery proof. |
| Physical printers / uncertain-delivery inspection | EXTERNAL_BLOCKED | Owner-selected58/80mm devices, queue, encoding, paper and cable-failure drill required. |
| Certified automatic KDS print fallback | MISSING | Health producer/runtime certification incomplete; disabled. Assisted scope must use explicit manual ticket procedure. |
| Backup / restore / restart | PASS (local) | New restored DB matches one order/two charges1500c/zero payments/refunds/24 audits/one staff/79 migrations; real restart matches credential/ledger/audit snapshot. Not cloud encrypted backup certification. |
| Cloud monitoring / off-host backups / restore policy | EXTERNAL_BLOCKED | Operator runbooks prepared; Railway alerts/retention/history cannot be inspected. |
| Fiscal issuance / contingency | EXTERNAL_BLOCKED | Rodada documents non-fiscal. Owner/accountant must define existing compliant issuance and contingency before customers; no fiscal issuance tested. |
| Onsite assisted acceptance / VR rollback | EXTERNAL_BLOCKED | Exact16-step procedure exists, no signatures or physical rehearsal. VR remains available. |

## Final exact-SHA CI

Completed six gates: full API593 tests in each job; integrated593 tests; Web232 visual and16 real BFF tests; Android build/JVM/lint/force-stop persistence; Docker including four origin cases; full shift25 tests plus64 Tabs/actual restart. Native RST attempt1 failed at the live-PID proof; attempt2 and native uplink passed. All seven dispatches target `19dfc80e27f619a32c02518fad745e30db09830e`. All are completed; native workflow success follows a failed first RST attempt, preserved separately.

| Gate | Run | Result |
| --- | --- | --- |
| API — full PostgreSQL and focused concurrency | [38314947779](https://github.com/procopio420/rodada/actions/runs/38314947779) | PASS |
| Web — lint/type/build/visual/real BFF | [38314950595](https://github.com/procopio420/rodada/actions/runs/38314950595) | PASS |
| Android — build/JVM/lint/force-stop persistence | [38314953184](https://github.com/procopio420/rodada/actions/runs/38314953184) | PASS |
| Native Android real POST — RST/uplink cut | [38314956027](https://github.com/procopio420/rodada/actions/runs/38314956027) | PASS after retry; reliability PARTIAL |
| Railway Docker — routes/order/queues/origin security | [38314958715](https://github.com/procopio420/rodada/actions/runs/38314958715) | PASS |
| Full shift —25 tests/64 Tabs/restart reconciliation | [38314961773](https://github.com/procopio420/rodada/actions/runs/38314961773) | PASS |
| Integrated release — full PostgreSQL/Web/runtime | [38314972691](https://github.com/procopio420/rodada/actions/runs/38314972691) | PASS |

[Final local/CI artifacts](evidence/integrated-19dfc80/) include manifest, bootstrap, API/QR/SSE, browser, origin rejection, migration, image/backup checksums, restore and before/after restart snapshots. Earlier [defcd94 rehearsal](evidence/integrated-defcd94/) and workstream reports are explicitly historical. Seven443 CI runs passed before the additional Nginx correction; they do not replace final19 gates. A patched443 container was only a reproduction/correction test and was replaced by the rebuilt19 image on a new empty DB.

Native proof artifact names repeat across attempts: RST attempt2 is artifact11776394238, not the failed attempt1 artifact11776397760. The manifest records both and the actual uplink artifact. Narrow [lifecycle diagnostic](evidence/integrated-19dfc80/native-lifecycle/reproduction-notes.md) is not live-POST/physical evidence.

Probe corrections are recorded honestly: QR creation returns201 (not necessarily200); initial HTTP client sent the wrong QR field; empty Next route-announcer live region is not an application error; a first browser screenshot preceded report loading. The final browser gate waits for financial report content and rejects nonempty alerts. Restore comparison is quiesced: additional auth audit events after a dump are new writes, not evidence of backup corruption. No weakened financial assertions, goldens or product authorization checks were used.

## Blockers and release decision

Engineering: no confirmed financial duplication was detected in the completed gates. Native RST force-stop proof failed on attempt1; lifecycle cause remains unproven and gate reliability stays PARTIAL despite the successful retry. Ten narrow generic offline diagnostics passed without reproducing it; retain lifecycle/crash evidence on the next original scenario before changing timing. Complete final native UI operational/closing journey and public HTTPS authenticated smoke are still required evidence; automatic print health/fallback is missing and excluded/disabled in the reduced pilot. Tenant hostname PR101 is unmerged and not part of this candidate. Do not activate unimplemented provider bridges or present non-fiscal output as fiscal.

External: Railway reauthentication and an explicitly new isolated staging target/DB; actual deployment SHA/build identity and managed monitoring/backup/restore; physical Android/Wi-Fi, station/printer drills and staff training; owner/accountant fiscal workflow and signed reduced scope. Provider credentials, merchant/sandbox approval and certified devices/private SDK are additional independent blockers for integrated payments.

**Next milestone:** deploy the archived/reviewed candidate only to an explicitly isolated authorized staging environment, record actual SHA and HTTPS authenticated evidence, close the native lifecycle gate with evidence, then execute every applicable step of the [onsite acceptance procedure](aderlan-onsite-acceptance.md). Once cloud, physical, financial and fiscal gates are signed, reassess **GO — assisted pilot with manual/external-terminal payments**. Integrated payment GO needs actual provider/device approval. Keep VR System as fiscal/operational contingency; this RC does not authorize full replacement.
