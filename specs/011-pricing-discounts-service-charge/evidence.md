# Financial acceptance evidence — 2026-10-09

Validation used the isolated `rodada-pricing-test` PostgreSQL 17 container bound
to loopback port 55450. No venue production database was modified. Runtime logs
are local validation artifacts; the tests and reproduction commands are committed.

## Backend

Final full PostgreSQL regression: **250 passed, no skips** (394.59 seconds).
Focused pricing/API/concurrency/upgrade verification: **27 passed**. This includes five real PostgreSQL concurrency/trigger
checks and the legacy upgrade test. Migration checks report **no changes**;
all migrations also applied successfully to a fresh PostgreSQL database.

```bash
cd apps/api
export POSTGRES_PASSWORD=rodada-test POSTGRES_PORT=55450
python -m pytest --ds=rodada_api.settings_pricing_postgres
python -m pytest tests/test_pricing.py tests/test_pricing_concurrency.py \
  tests/test_pricing_upgrade.py --ds=rodada_api.settings_pricing_postgres
python manage.py migrate --settings=rodada_api.settings_pricing_postgres
python manage.py makemigrations --check --dry-run --settings=rodada_api.settings_test
```

SQLite remains a fast check, not evidence of locking behavior. The initial full
regression found legacy paid-correction and version-test compatibility issues;
those were corrected, with the final full PostgreSQL run passing. No financial
assertion was weakened: the existing transfer test now explicitly proves that
payment changes invalidate the old version before retry with a current version.

## End-to-end financial reconstruction

`test_customized_bill_correction_and_management` persists ordinary consumption
2000 and customized consumption 2800 (variant 2500 + modifier 300). Tab discount
800 leaves net 4000, then 10% service adds 400. The first Payment receives 2000.
A real manager-approved remake creates a new 2800 Charge with equal append-only
replacement courtesy, preserving the original customization snapshot. A subsequent
400 courtesy corrects the commercial bill. Service refresh writes -400 and +360;
the final Payment receives 1960. Closing succeeds at zero exposure.

Management reconstructs gross 7600, discount 800, courtesy 3200, net consumption
3600, service/pass-through 360, payable 3960, received 3960 and exposure zero.
Neither original Charge nor confirmed Payment amount is rewritten. Allocations
sum to their signed facts; transfer effects never count as new sales.

## Money/authorization boundaries

- Percentage is integer basis points; half-up cents use `(basis * bps + 5000) // 10000`.
- Largest remainders use stable Charge UUID ordering and persist exact allocations.
- Preview writes no Adjustment. Approval persists exact intent and both actors.
- Approval and all replays revalidate active venue membership/capabilities.
- Privileged commits/configuration require recent PIN reauthentication.
- Discount above consumption or resulting payable below net receipts commits nothing.
- Pending/ambiguous payments and pending refunds block repricing.
- Stale service basis is checked per Charge, not only aggregate consumption.
- Unpaid transfer components conserve original subtotal, discount, courtesy, service
  and revenue/pass-through treatment; confirmed money blocks transfer.
- PostgreSQL forbids adjustment/allocation UPDATE/DELETE and rejects inexact sums.

## Web / Android

Web TypeScript and production build pass. Real browser integration against
PostgreSQL passes **7 scenarios**, including cashier discount preview/application,
service, partial payment, correction, final payment, close and Management report.
Visual layout/accessibility verification includes the existing adjacent surfaces
and six new pricing/cashier/management cases at 360, 390 and 768 px. No visual
baseline was reset. The full visual gate passed **122 tests**; six pricing checks
passed again against the final production build.

Android: **36 unit tests pass**, debug APK and lint pass. Native actions include
item/Tab discount, courtesy, service assessment/removal, reversal, exact before/after
preview, approval request, PIN and persisted ambiguous-response recovery. Native
payment recovery retains the original bill version. Monetary input parsing uses
decimal text and integer minor units, not floating point.

```bash
cd apps/web
npm run typecheck
npm run build
npm run test:visual
# Start on a fresh dedicated rodada_web_e2e database, not a venue database:
RODADA_E2E_POSTGRES=1 POSTGRES_DB=rodada_web_e2e POSTGRES_PORT=55450 \
  POSTGRES_USER=rodada POSTGRES_PASSWORD=rodada-test POSTGRES_HOST=127.0.0.1 \
  npm run test:integration
cd ../attendance-android
./gradlew testDebugUnitTest assembleDebug lintDebug
```

## Deliberate boundaries

Service is an explicit assessment and refresh, not an automatic UI surcharge.
Venue policy declares revenue/pass-through and refund assistance separately;
this does not claim fiscal/GL compliance. Paid financial transfers remain blocked
per Spec 009. Reversals of transferred allocations and superseded service reductions
fail explicitly; they do not guess responsibility. Guests see commercial totals
without internal approval/reason details; optional service removal goes through
policy-authorized staff. Printing infrastructure and provider SDKs are untouched.
