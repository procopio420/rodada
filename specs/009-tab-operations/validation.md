# Spec 009 — verified delivery

The persisted backend and native Attendance workflows initially shipped in PR #47.
This continuation on `feat/tab-operations` brings that branch forward to current main,
checks the newer payment adapters, and fixes issues found in financial/reporting and
Android rejection recovery. No PR was merged by this delivery.

## Financial and operational contracts

- A committed `TabTransferLine` is an immutable balanced pair: negative source
  responsibility, equal positive destination responsibility. Original Order, OrderItem,
  Charge, Payment and Refund ownership stays unchanged.
- Source/destination Tab locks are acquired in ID order. Versions are checked inside
  the transaction; the durable operation result and optional new destination are committed
  once. A retry reauthorizes and returns the original response even after later payments.
- Confirmed money/refunds, active provider attempts, nonterminal payments and pending
  refunds block transfers on either side. Expired payments allow transfers only after
  active attempts are terminal. No payment adapter or reconciliation implementation changed.
- The destination uses its effective House Account limit, including audited overrides.
  Subsequent order confirmation consumes the transferred balance through existing ledger totals.
- Responsibility uses three queries for multiple charges instead of querying allocations
  and adjustments for each item. Operation detail locks the Tab while reading the version,
  balance, available lines and provenance.
- Management current open exposure includes transfer effects before per-Tab clamping;
  sales and product mix continue to count original charges only. Unpaid merged responsibility
  therefore remains visible on the surviving Tab.
- Location changes refresh active Dispatch destinations, preserve completed destination
  history and never release occupancies. Split/merge retain production ownership.
- Empty cancellation and merge revoke source GuestSessions without rebinding them.
  Reopen requires `tab.reopen` and a reason, preserves the original closure/payment history,
  and emits a durable post-close exception with the original closure timestamp.

## Android

Compose presents Mover local, Dividir conta, Transferir consumo, Juntar comandas,
Cancelar comanda vazia and authorized Reabrir comanda using persisted API data.
Item/quantity or partial-cent selection, destination search/create and server previews
retain exact totals and source/destination versions. Closed/cancelled/settling Tabs offer
only applicable commands. The server remains the permission authority.

Network ambiguity retains the encrypted original command and idempotency key; recovery
is explicit and never silently submits a new mutation. A deterministic server rejection
clears the preview. If its subsequent canonical refresh also fails, the original rejection
remains visible and the workflow requires a fresh read before another submission.

## Executed checks

- Django system check and migration drift: pass, no schema changes required.
- PostgreSQL: 28 passing tests covering Tab operations, persisted HTTP workflows,
  full-shift smoke, House Account HTTP E2E and payment concurrency. Includes competing
  full splits, concurrent identical retries and payment-versus-split serialization.
- PostgreSQL follow-up: 6 passing tests covering reauthorized replay after later payment,
  merged/split management exposure and the HTTP operation workflows.
- Targeted SQLite Tab-operation/report regression suite: 22 passed, 4 PostgreSQL-only
  tests skipped. PostgreSQL execution above provides the actual row-lock evidence.
- Android: `testDebugUnitTest assembleDebug lintDebug` pass; 30 unit tests, zero failures.
- Ruff on the modified Tab-operation service/views/tests and `git diff --check`: pass.
- Final complete API suite: **208 passed, 9 skipped in 262.18 seconds**. Skips cover
  PostgreSQL-only suites; the relevant concurrency/HTTP runs above passed on PostgreSQL.

Reproduction:

```bash
cd apps/api
python manage.py check --settings=rodada_api.settings_test
python manage.py makemigrations --check --dry-run --settings=rodada_api.settings_test
python -m pytest
python -m pytest tests/test_tab_operations.py tests/test_tab_operations_e2e.py \
  tests/test_full_shift_smoke.py tests/test_house_account_e2e.py \
  tests/test_payments_concurrency.py --ds=rodada_api.settings_payments_postgres
```

The disposable PostgreSQL settings use port 55447 and the existing local test database;
CI also runs Tab-operation concurrency and HTTP tests against its PostgreSQL service.

```bash
JAVA_HOME=/path/to/jdk17 ANDROID_HOME=/path/to/sdk ./scripts/android-check.sh
```

## Remaining owner integrations

- The durable AuditEvent contract exposes invalidation targets and source/destination
  provenance. Live transport delivery/consumption belongs to the realtime owner; this
  branch does not modify the transport or claim a connected subscription test.
- DailyClose policy and Gerência exception/timeline rendering belong to Management.
  The post-close fact is persisted and exposed through operation history now; no
  DailyClose snapshot or original CashShift closing result is rewritten.
- Guest Access does not yet persist TabIdentifier. Automatic identifier reassignment
  remains prohibited; an explicit safe reassignment command waits for that owner's model.
- Android unit/build/lint were executed. No emulator or physical device was available;
  native gesture/device smoke is not claimed. The HTTP E2Es exercise the actual authenticated
  API and persisted financial workflows without ledger/provider mocks.
- Web structural-operation screens and related-Tab drill-down remain adjacent-surface
  work listed separately in tasks.md. No Web UI files changed in this delivery.
