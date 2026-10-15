# GitHub Actions policy

The pilot is web-first. Pull requests should verify the code they touch without launching
a full release/homologation suite on every commit.

| Workflow | Automatic | Manual | Purpose |
| --- | --- | --- | --- |
| Landing | PR/push changing `apps/landing/**`, `specs/030-marketing-landing/**` or its static tests | No | Python stdlib checks for brand copies, HTML/SEO links, local screenshots and pilot disclaimers |
| API | PR/push changing `apps/api/**` or `scripts/quality/**` | Yes | Ruff new-line gate + full diagnostic count; Django checks, migration drift and one full PostgreSQL pytest run |
| Web | PR/push changing web, API, prototype, quality script or this workflow | Yes | Next.js build, typecheck, **ESLint 9 + Next 16 full scan with new-line gate**, Web security guard, auth, visual and real BFF integration tests |
| Printer Agent | PR/push changing printer agent or its workflow | Yes | Strict types, worker fault tests and real Windows session-0 service/DPAPI/ACL; no installer/release |
| Android | PR/push changing Android | Yes | Unit tests and debug build; `lintDebug` **blocking**, upload report; release AAB smoke on main/manual only |
| Android real POST disconnect | PRs changing its workflow, cross-surface config/tests/verifiers or shared fixture guard | Yes | Native emulator transport/recovery → Web Bar on the same PostgreSQL; separate manual uplink cut |
| Aderlan isolated pilot shift acceptance | No | Yes | Full disposable PostgreSQL shift |
| Railway Aderlan demo Docker smoke | PR changing Railway deployment or staging smoke script | Yes | Build full Railway container and smoke runtime |
| Integrated release demo | No | Yes | Restart/concurrency and full shift gate |
| Play Store internal release | No | Yes | Signed AAB and optional explicit Google Play upload |

## Static quality gates

See [Quality Gates](agents/QUALITY-GATES.md) for exact blocking vs advisory status and legacy-debt handling. **Android Lint is a required pass** since PR #129 baseline audit succeeded; Web uses ESLint 9 / Next 16 Core Web Vitals + TypeScript with a full audit and a new/fatal diagnostics gate, in addition to TypeScript/build/Playwright. Ruff inspects all Python but blocks violations only when their diagnostic lands on a newly added source line.

## Release/homologation gates

- Keep **API** and **Web** as the normal PR gates for the web pilot.
- Run **Railway Aderlan demo Docker smoke** manually before changes that materially
  affect packaging/startup or a major pilot deployment; edits to `deploy/railway/**`
  still trigger it automatically.
- Run **Aderlan isolated pilot shift acceptance** and/or **Integrated release demo**
  manually before a high-impact release or operational homologation.
- For Android releases, run **Android** manually (including force-stop recovery) and
  **Android real POST disconnect** when payment/offline/network recovery logic changes.
  **Play Store internal release** remains explicitly dispatched; it is never invoked
  by ordinary PR/push and uploading to Play remains opt-in.
- `concurrency` discards superseded **PR** runs, never ongoing `main` or
  `workflow_dispatch` runs. Existing runs started before this policy may still
  require cancellation through the GitHub Actions UI.

This change modifies workflow scheduling and removes the duplicated API job,
but **does not delete the underlying tests**.

## Issue #106 shared-fixture safety

`scripts/cross_surface_fixture.py` is the shared destination/Venue boundary for
the native fixture preparer and Android→Web reconciler. It requires an exact
allowlisted local PostgreSQL database, validates Django's effective connection
and independently reads `current_database()` / `inet_server_addr()` before ORM
access. libpq destination overrides are rejected. The fixture and native receipt
carry database/Venue IDs; verification rejects a foreign Venue or generation.

Fast safety regressions: `python -m unittest discover -s scripts/tests -p test_cross_surface_fixture.py -v`.
These tests do not prove Android, browser or PostgreSQL execution. The existing
native workflow executes the real connected guard and shared fixture. Its native
transport instrumentation does not by itself prove ordering via Compose UI.
The complete automated #106 suite was executed at899255b1; see the
[current matrix](releases/issue-106-resumption-matrix.md) for evidence and gates. Never start the Web-only fixture
runner to validate the native order: it seeds a different database.

### #106 local continuation (2026-10-15)

The cross-surface stack now starts Django with Uvicorn/ASGI: WSGI runserver
cannot sustain the asynchronous realtime stream required by the native UI.
After the HTTP/storage recovery checks, `android-compose-order.sh` installs a
Debug APK targeting that same local backend on 8101 and drives production
MainActivity login/open/catalog/confirmation via Compose instrumentation.
The runner clears only the test app on an explicitly verified emulator, then
runs independent PostgreSQL reconciliation. It never selects a release build.
The browser consumes both native receipts and drives explicit Bar transitions;
QR-first/claim/two empty Tabs/release/cleaning are separate browser actions on
the same fixture Venue and PostgreSQL. The full runner additionally covers
Kitchen, Guest/Web origins, native contextual readback, financial UI/cutoff,
authorization and final SQL. Exact-SHA independent review is required for GO;
physical gates remain separate.

Successful traces are retained. Only archives exported by
`scripts/sanitize-cross-surface-traces.py` are uploaded, with credentials/PIN
redacted; raw traces remain local. Review the sanitized archive before treating
it as shareable evidence. Scenario completion still requires actual execution
at the reported SHA and the fail-closed #106 evidence contract.

Local execution of those shared-client slices is documented in
`docs/releases/issue-106-local-runner.md`. Receipts also bind to a hash of the
actual PostgreSQL cluster system_identifier and database, not just its name.
Runner captures are isolated per invocation and preserve previous evidence.
Repository workflows inspected on 2026-10-15 contain a Railway Docker build/smoke
job, not an application deploy action. This does not verify Railway's external
GitHub autodeploy setting; no merge/deploy is authorized by those checks.
