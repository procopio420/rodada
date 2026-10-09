# Demo release evidence — 2026-10-09

**CONDITIONAL GO for a supervised local demo using manual/test payments.**
The complete operational shift, native recovery and service/database restart passed.
No production cutover or provider settlement is asserted.

## Candidate and audit

- Repository `procopio420/rodada`; release branch `release/2026-10-09-demo-readiness`.
- Frozen main: `742faac639adc998f3a4da6d8af485b407317851`.
- Code candidate: `615b0551e7f6eb6a017afe68d860b80dde55cdf5`.
- Isolated worktree: `/home/lucas/projects/rodada/demo-readiness`; the original
  checkout belongs to the pricing agent. No changes to that checkout or to provider,
  pricing or printing feature implementations. No independent feature branch merged.
- Read repository instructions, README, readiness plan, product/domain/design and
  architecture contracts, relevant acceptance/spec contracts 001/002/008/009/010/
  012/014/017 and ADRs on Tab/occupancy, availability, House snapshots, management,
  HTTP/SSE/outbox and catalog icon outbox.
- Verified recent merge commits: #46 `742faac`, #53 `9cd6d65`, #54 `56cd02a`,
  #55 `66c76a2`. The readiness plan's older inventory is not current evidence.
- Current migration graph applied from empty PostgreSQL through catalog,
  customization, tab transfers, ledger/payment status, cash, provider and realtime.
  Django system check and migration drift check passed. No release migrations added.

## Reproduction

See [demo commands](../../demo/README.md). `bash scripts/demo-smoke.sh` builds the
actual Web/API services, migrates and provisions test identities, runs a shift using
HTTP only and prints independent read-only SQL reconciliation. Restart mode is
`RODADA_DEMO_RESTART=1 bash scripts/demo-smoke.sh`. No direct SQL balance repairs.

Runtime: Docker 29.8.2, Compose 5.6.0, PostgreSQL 17.11; container Python 3.13.16,
Django 5.2.18, DRF 3.18.3, psycopg 3.3.6, uvicorn 0.54.0; Web Node 24.19.0,
Next 16.3.8, React 19.3.0; Android JDK 17.0.2, SDK 37/build-tools 37.0.0,
API 36 Google APIs x86_64 emulator. No physical phone, NFC, printer or PSP merchant
was exercised. No Redis is required by current durable SSE implementation.

## Cross-module findings and fixes

1. **Committed payment recovery (P0 release recovery):** replay after another
   client closed the Tab returned `TAB_CLOSED`. Regression reproduced 409 before
   fix. Replay lookup now precedes closed-state validation, retaining actor/Venue
   authorization, amount/method conflicts and rejection of new payments on closed
   Tabs. Original payment/audit/cash records are not duplicated.
2. **Money input validation:** manual payment/refund views used `int()` on
   unvalidated JSON, accepting/truncating fractional inputs and permitting malformed
   identifiers/oversized amounts to reach persistence. Typed bounded serializers
   reject malformed payloads with stable error codes and no ledger effect.
3. **Android demo endpoint:** app used a fixed port 8000; emulator smoke preflight
   could target another port while `installDebug` rebuilt the APK at the default.
   Added `rodadaApiBaseUrl` build property; emulator script builds for its preflight
   URL and installs the exact APK through adb. TCP reachability alone is explicitly
   not described as native login proof.
4. Variant price is an explicit effective base price, not an extra delta added to
   Product price. Runner and UI assertions use 3000 base + 500 modifier = 3500.
5. Split is performed **before** payment. The current Spec 009 deliberately blocks
   transferring paid responsibility. Production/Charge origin remains the source
   Tab; transfers are balanced responsibility effects, never sales.
6. Refund is added back to exposure; signed adjustments and transfer effects are
   included. The prose `Charge − Payment − Refund` in the older plan is not the
   reconciliation formula used by the implementation or this release evidence.
7. Separate ASGI and dispatcher are mandatory. HTTP success is not SSE delivery;
   the runner waits for actual published events and revalidates snapshots.
8. AI icon gateway/worker, live provider provisioning, pricing engine and receipts
   are not required to conduct this manual/test shift. Their independent branches
   remain outside this frozen candidate. Revalidate the complete shift after each
   accepted PR; this run does not certify those unmerged features.

9. **Prepaid production recovery (P0):** a financially closed Tab blocked legal
   production transitions for already confirmed items with `TAB_CLOSED`, stranding
   prepaid orders. The regression failed before the fix. Fulfillment now continues
   through the authorized state graph without reopening the Tab or changing money.
   The latest live shift pays/closes the House Tab before production and delivery;
   the PostgreSQL regression verifies unchanged ledger facts and zero exposure.

## Completed automated checks

| Check | Actual result |
| --- | --- |
| Baseline API SQLite | 256 passed, 12 skipped; no PostgreSQL lock claim |
| Baseline API PostgreSQL | 269 passed; cleanup warning for leaked test connections |
| Candidate PostgreSQL full suite, before final refund validation test | 272 passed; same cleanup warning |
| Financial release regression + cash + corrections | 39 passed |
| Final production/ledger/dispatch/correction regression | 54 passed on final code |
| Web typecheck / production build | PASS |
| Web realtime Node contract suite | 8 passed |
| Real browser workflows, PostgreSQL | 7 passed, no business-response interception |
| Web visual/accessibility suite | 144 passed; visual fixtures are distinct from operational proof |
| Android JVM / assembleDebug / lintDebug | 38 passed, zero failures/errors; build/lint PASS |
| Live ASGI SSE | PASS; 2166 ms observed confirmation-to-event in this run |
| Full HTTP shifts | Repeated PASS; final run `9c66483634`, including prepaid production and delivery |
| Final PostgreSQL full suite | 274 passed in 391.92s; real PostgreSQL, no skips or cleanup warning (`--reuse-db`) |
| Native process-death pending order | PASS; real API outage, force-stop, intent restoration, exactly one order |
| PostgreSQL and full service restart | PASS; persisted canonical report verified after restarting db/API/dispatcher/Web |

The PostgreSQL cleanup warnings concern disposable test databases, not incorrect
business assertions. New release concurrency workers explicitly close their thread
connections. Existing catalog/customization/House test workers retain connections
with production `CONN_MAX_AGE`; do not hide this warning or count SQLite skips as
concurrency proof.

## Shift and failures

| Required step/scenario | Evidence |
| --- | --- |
| BYOD staff authentication | Real Android UI login + HTTP protocol assertions; UNTRUSTED accepted |
| Anonymous Tab, optional occupancy | Native Tab opened; HTTP shift associates two independent Tabs |
| Bar + Kitchen with variants/modifiers | Native 4700-cent cart configured; HTTP snapshots/queues validated |
| Confirm once | Concurrent identical HTTP commands return same Order; restored native intent confirms one Order |
| Production states / both queues | HTTP NEW → ACCEPTED → PREPARING → READY → DELIVERED; native Order advanced in actual Web queues |
| SSE disconnect/replay | Actual HTTP/SSE replay, invalid cursor reset, separate publication process |
| House limit | Hit limit, 409 denial, manual partial restores capacity, consume and close |
| Partial manual/test payments | Concurrent duplicate partial returns same Payment ID |
| Split unpaid balance | 1200 cents moved; retry returns same operation; history retained |
| Partial followed by correction/refund | REFUND_REQUIRED then explicit 600-cent refund + -600 adjustment; idempotent |
| Close Tabs / CashShift | Zero exposure; expected/count 14300 cents, discrepancy zero |
| Management / audit | Exact report deltas and actor/session provenance asserted |
| Session revocation | Administrative command denies staff mutation; connected guest SSE revoked; native returns to Login |
| Cross-Venue | Read/payment mutation denied; no cross-Venue ledger effect |
| Concurrent order/payment | PostgreSQL real-service race preserves operating limit and ledger |
| Distinct simultaneous manual payments | One commits, second PAYMENT_EXCEEDS_EXPOSURE; no overcollection |
| Stale product/option | Real availability mutations; new cart rejected; original intent remains replayable |
| Unexpected input/response | Malformed money/IDs/JSON rejected; real 202 refund-needed response handled |
| Redis restart | N/A: runtime does not use Redis |
| Android restart with pending intent | PASS; cart customization and pending intent restored, original snapshots preserved |
| PostgreSQL/API/Web/dispatcher restart | PASS; same IDs/report/closed states recovered without new business commands |

## Reconciliation and payment classification

All shift money is **MANUAL_TEST**: operator declarations of test cash/external
terminal receipt and manual/test refunds. `CONFIRMED` is the application's manual
ledger state, not evidence of card acquiring, Pix settlement or actual funds.
No provider simulator callback or fabricated provider confirmation is used in the
full shift. Provider unit suites include explicitly fake providers; those passes do
not constitute settlement evidence.

Per complete HTTP shift, cents:

| Fact | Cents |
| --- | ---: |
| Charges | 8900 |
| Signed adjustments | -600 |
| Confirmed manual/test Payments | 8900 |
| Confirmed manual/test Refunds | 600 |
| Net sales = Charges + Adjustments | 8300 |
| Net received = Payments − Refunds | 8300 |
| Venue net transfer effect | 0 |
| Exposure = Charges + Adjustments − Payments + Refunds + Transfers | 0 |
| Cash opening float / receipts / counted | 10000 / 4300 / 14300 |
| Cash discrepancy | 0 |

[Completed check output](demo-artifacts-2026-10-09/completed-checks.txt),
[Final run JSON](demo-artifacts-2026-10-09/full-shift-final.json),
[earlier repeat](demo-artifacts-2026-10-09/full-shift-repeat.json),
[SQL reconciliation](demo-artifacts-2026-10-09/postgres-reconciliation.txt),
[live SSE](demo-artifacts-2026-10-09/live-sse.json).

An initial harness run aborted on its incorrect expected-status set (valid 202
was treated as failure). It is **not** counted as a successful shift. Its committed
facts were settled/refunded/closed through public HTTP commands, with an explicit
QA reason; no rows were deleted and no SQL was used to repair balances. Aggregate
SQL therefore includes the recovered attempt as well as successful shifts.

The final aggregate SQL includes 18 CLOSED Tabs: Charges 55700, adjustments -3600,
Payments 55700, Refunds 3600 cents; net sales and net received both 52100 cents.
Exposure, transfer net, duplicate checks and all six CashShift discrepancies are zero.
The additional 4700-cent native order is included.

Native evidence: [outcomes and confirmation-time snapshots](demo-artifacts-2026-10-09/native-android.json),
[pending recovery](demo-artifacts-2026-10-09/android-pending-recovered.png),
[Android READY via SSE](demo-artifacts-2026-10-09/android-web-ready.png),
[revoked session](demo-artifacts-2026-10-09/android-session-revoked.png),
[Bar Web READY](demo-artifacts-2026-10-09/native-order-bar-ready.png),
[Kitchen Web READY](demo-artifacts-2026-10-09/native-order-kitchen-ready.png).
The HTTP runner deliberately records `native_android_ui: NOT_RUN`: it does not
pretend to drive Android. The separate native artifact/screenshots are the UI proof.
Snapshots in native JSON were captured at confirmation (NEW); later fulfillment and
closure outcomes are separately recorded. Emulator evidence does not certify a physical phone.

Native recovery reproduction: build/install the configured APK using demo README,
login as release-staff, open a Tab and configure a Bar/Kitchen cart. Stop only the
API, tap confirmation, force-stop Android, restart API and reopen Android. Select
the Tab, restore the pending cart and retry confirmation. Confirm one Order and
its snapshots in both production queues. Advance states in Web, observe Android
SSE updates, then deliver/settle/close through authorized APIs. Revoke the Android
session from administration and verify Login. This native sequence was conducted
manually against real services; it is not claimed as an automated instrumented test.

The full suite began on `6f13da2`; the only subsequent code edit removed an
unused test import (`615b055`). Runtime business code and fixture behavior are identical.
Ruff E/F checks excluding existing line-length violations, shell syntax and
`git diff --check` passed. Remote CI status is reported separately by the PR.

## Decision

**CONDITIONAL GO** for tonight’s supervised demo on this frozen candidate and the
recorded Compose/emulator setup. Use clearly identified MANUAL_TEST payments and
retain the canonical financial history. The demonstrated integrated flow passed;
no unresolved P0 was observed in this scope. Physical BYOD hardware and real settlement
remain unverified. Spec 006/011/015 independent branches are excluded and must each
receive complete integration revalidation before acceptance. The added GitHub workflow
is reproducible automation; local results below do not assert an unobserved CI pass.
Production cutover remains **NO-GO**: physical device/pilot verification, applicable
provider provisioning/settlement, printing/fiscal obligations and parallel-shift
rollback are outside this evidence.
