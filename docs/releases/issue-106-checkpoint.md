# Issue #106 execution checkpoint

Base initially inspected: `fdc45944` (2026-10-15); main `2b981bba` integrated without conflicts. Branch: `test/106-integrated-foundation`.
This is a continuation record, not evidence that E2E-01..14 passed.

## Inventory A1/B1/C1/D1/E1/F1

Read-only inspection at the base SHA; existing tests below were **not rerun**.

| Area | Reuse | Remaining shared-client proof |
| --- | --- | --- |
| A | `apps/api/tests/test_guest_access.py`, `test_spec004_closeout.py`; Web `service-requests.spec.ts`, `table-entry.spec.ts` | QR-first → claim → independent Tabs → lifecycle and old-session denial on one fixture |
| B | `apps/web/tests/cross-surface/android-native-to-web.spec.ts`; integration `production-item-intents.spec.ts`, `availability-intents.spec.ts` | Current cross-surface covers one BAR item; add KITCHEN, Compose UI confirmation, Web and Guest origins |
| C | API `test_ledger_payments.py`, `test_cash_management.py`, `test_payments_concurrency.py`; Web `pos-cash-receipt.spec.ts` | UI financial workflow on the native-origin Tab, independent final reconciliation |
| D | API `test_table_service_concurrency.py` has real barriers/separate connections for start/start, claim/claim, release/open; `test_order_intent_concurrency.py`, `test_guest_concurrency.py` | Execute on PostgreSQL and correlate auth/tenant negatives with shared journey; do not duplicate #130 ingress audit |
| E | `LivePostDropReconciliationTest.stage`, `LiveTableServiceDropReconciliationTest.stage`, native drop/link-cut scripts | Live native tests use production HTTP/storage, **not Compose ordering UI**; full-shift HTTP explicitly records native UI NOT_RUN |
| F | `android-live-post-drop.yml` shares PostgreSQL/Django with the browser; full-shift harness reuses domain assertions | Full E2E-01..14 orchestration, scenario schema, final evidence and GO/NO-GO still missing |

The Web integration config starts/seeds a different backend/database; it cannot
prove continuity of the native Order. Existing ORM reconciliation is independent
of browser responses, but is not a full SQL ledger audit for the entire shift.

## First implementation: F2 safety prerequisite

The native fixture preparer previously had no destination guard. Both native and
browser verifiers now share an exact local database allowlist, reject libpq
routing overrides, inspect effective Django connection settings and query the
actual database/server identity before ORM use. Fixture and native receipt carry
database/Venue identities. A foreign Venue/generation/product is rejected.

This implements a prerequisite of F2; **F2 remains incomplete** until the real
native/browser shared-ID run is verified. No A1–F8 checkbox is marked complete
on the strength of code alone.

Executed locally:

- `python -m unittest discover -s scripts/tests -p test_cross_surface_fixture.py -v`: 6 PASS (subprocess destination rejections and mocked connection identity tests; not a PostgreSQL E2E).
- `python apps/api/manage.py check`: PASS, Django 5.2.18 / Python 3.12.
- Python compilation and `git diff --check`: PASS.
- Ruff on the new helper/tests: PASS.

Environment preparation: Django installed and Web dependencies installed.
PostgreSQL is not running: Docker/psql absent; packaged PostgreSQL startup failed
because this runtime cannot create its required unprivileged account. Apt package
retrieval was attempted separately. Android SDK/adb/emulator and `/dev/kvm` absent.
These are environment limitations, not successful native/DB executions.

## Continuation and gate

1. Run the changed native workflow on this PR SHA and inspect all artifacts.
2. Complete F2 reusable multi-surface fixture, then A2–A6 using the existing
   cross-surface config (never `playwright.integration.config.ts`).
3. Implement/run B, D/E, C and final F tasks according to #106's individual prompts.
4. Independent R3 review must inspect the final diff/SHA; no GitHub self-approval.
5. Do not close #106 until every automated acceptance requirement is proven.

Automated full-suite decision: **NO-GO / missing execution and coverage**.
Physical device/Wi-Fi, PSP/NFC/Tap/Pix, printers, fiscal and onsite sign-off remain
separate external gates with VR System rollback. No deploy/Play/payment/remote DB
operation performed. Main merge autodeploy configuration outside Actions is not
verified; inspect before any integration.

## First CI feedback

Run [38748983538](https://github.com/procopio420/rodada/actions/runs/38748983538), head `20c8cfac`: PostgreSQL 17.11 migrations PASS; guard tests PASS; fixture preparation FAIL because the service reports its Docker bridge IP, not host loopback. Android/browser steps SKIPPED after this failure. Correction records the exact inspected disposable service container IP in GITHUB_ENV and accepts only that address in CI, while the configured client destination remains loopback. A different private server still fails the regression. No integrated PASS claimed.

## Local recovery — 2026-10-15 (continuation, not closure)

Base `5a53326d`, isolated `test/106-local-resume`, draft PR #191. All existing
worktrees and uncommitted changes preserved. #186 contains 59 incidental
API/Android/Web/spec029 files introduced by bc48f2ef; only its four evidence
files are included here. #185 merged locally without conflicts. The original
PR branches are preserved, no merge/deploy to main.

Historical run 38751044388 at #185 `37a1c4b0`: native HTTP/storage -> Bar UI ->
PostgreSQL PASS, actual link-cut SKIPPED. Receipts downloaded and inspected.
Local tools: Docker 29.8.2, PostgreSQL 17.11 exclusive loopback:55606, Python
3.13, JDK17, SDK37, API36 AVD/KVM. venv and npm lockfile installation isolated.
Local baseline replay/force-stop, table start/open response loss, browser Bar
and independent PostgreSQL reconciliation PASS during development. 91 JVM,
16 PostgreSQL concurrency, 47 guest/ledger/cash domain tests PASS; these are
not 14 integrated scenario PASSes. Two trace-redaction regressions PASS.

New QR UI slice passed locally: guest-first occupancy, explicit Web claim,
two empty Tabs, closing both does not release, explicit release/cleaning,
old-session 403, unchanged QR token, independent SQL with zero ledger effects.
Does not yet prove two consuming Tabs or a new visit reusing the same QR.
New production MainActivity Compose login/open/catalog/confirm/account journey
and raw PostgreSQL readback PASS locally after replacing WSGI runserver by
ASGI/Uvicorn. Earlier attempts failed because the native UI remained STALE
without continuous SSE; failures preserved locally. Android UI uses the same
Django/DB directly, recovery tests retain the TCP fault proxy. Successful
traces are now retained and redacted before upload. Exact final-SHA CI and
artifact inspection remain required; development PASS is not final acceptance.

Independent foundation review `/root/review_foundations`, base `5a53326d` to
`f495a26b`: NO_FINDINGS_WITH_GAPS, all 12 files, 6+13 tests PASS. Does not cover
subsequent Compose/QR/ASGI/trace changes; refresh required. F2/F5/F7 partial;
A2/A4/A5 partial acceptance, remaining phases not certified. Full suite NO-GO.
