# SumUp candidate validation — 2026-10-08

No SumUp/Paytime merchant credentials, private SDK artifacts, provider sandbox
transactions or live transactions were available. All provider results below are
injected HTTP contract responses or explicit deterministic simulation.

## Implemented and checked

- SumUp Checkout/APM Pix creates a durable merchant-bound intent and uses exact
  Decimal JSON from integer cents. Displaying a code never confirms payment.
- Settlement requires authenticated checkout AND matching merchant transaction,
  including identity, amount and currency. Authoritative expiration is supported.
- Creation timeout recovers via checkout reference or persisted checkout ID;
  processing timeout does not repeat PUT or POST. Unknown Tap results reconcile by
  durable client transaction ID. Historical attempts retain their provider.
- Paytime Pix, authenticated callbacks, manual cash/external-terminal flows,
  House Account, partial payments and existing refunds remain covered.
- OAuth state is single-use and bound to staff/Venue; encrypted credentials bind
  connection identity. Refresh and local disconnect are tested. Device/operator
  authorization is tenant scoped. Android has no owner credential or token endpoint.
- Refund reservations remain attached to original payments. Ambiguous refund requests
  are not resubmitted; newly verified provider events reverse the ledger once.
- PostgreSQL tests exercise competing collectors, duplicate intent/confirmation,
  duplicate webhook inbox processing and refund reservations with separate connections.
- API E2E covers order → Pix/card split → verified simulated settlement → history →
  close. Backend restart recovery uses persisted provider state, not client success.
- Android tests cover the SDK boundary, eligibility, initialization failure,
  cancellation/unknown/failure reconciliation, serialization of credit/debit recovery
  intents and clear simulation labeling. The debug APK builds and lint passes.

## Results

| Check | Result |
| --- | --- |
| Full backend suite (SQLite) | 180 passed, 5 skipped; 180.64s |
| Financial suite (PostgreSQL 17) | 72 passed; 100.83s |
| Existing payment/House Account migration tests (PostgreSQL 17) | 2 passed; 16.71s |
| Android JVM tests | 27 passed, no failures/errors |
| Android testDebugUnitTest / assembleDebug / lintDebug | BUILD SUCCESSFUL; 52s |
| Django system checks | No issues |
| Migration drift | No changes detected |
| Targeted Ruff (payment provider/tests; generated migrations excluded) | Passed |
| git diff --check | Passed |
| Provider sandbox / private SDK / live payments | NOT RUN — external access unavailable |

The full-suite skips include three PostgreSQL concurrency tests and two existing
PostgreSQL-only migration tests. The three payment concurrency tests passed in the
PostgreSQL financial suite; the two migration tests also passed in a separate
PostgreSQL run.

## Reproduce

```sh
cd apps/api
python -m pytest
DJANGO_SETTINGS_MODULE=rodada_api.settings_payments_postgres python -m pytest \
  tests/test_sumup_payments.py tests/test_paytime_live.py tests/test_payment_provider.py \
  tests/test_payments_concurrency.py tests/test_ledger_payments.py \
  tests/test_cash_management.py tests/test_house_account.py tests/test_house_account_e2e.py
DJANGO_SETTINGS_MODULE=rodada_api.settings_payments_postgres python -m pytest \
  tests/test_payment_migration.py tests/test_house_account_migration.py
DJANGO_SETTINGS_MODULE=rodada_api.settings_test python manage.py makemigrations --check --dry-run
DJANGO_SETTINGS_MODULE=rodada_api.settings_test python manage.py check
# From repository root, with JDK17 and Android SDK configured:
./scripts/android-check.sh
```

PostgreSQL validation uses a disposable PostgreSQL 17 instance on localhost:55447;
settings_payments_postgres uses test-only credentials, with environment overrides.
Do not run two pytest processes against this same disposable test database.
The SQLite suite deliberately skips PostgreSQL concurrency cases; only the separate
PostgreSQL execution proves those database behaviors.

## Limits and activation gates

The opt-in `-PsumupSdk=true` dependency configuration has NOT been resolved or built.
SumUpSdkBoundary is Rodada's interface, not an implementation of private SDK classes.
Standard Android compilation proves the fake boundary only. Real integration still
requires official artifact access, event/output mapping, approved AuthTokenProvider
issuance, lifecycle wiring, physical-phone attestation/PIN testing and homologation.

No direct SumUp webhook ingestion is enabled: verification is authoritative polling.
Processed Pix cancellation, Pix refund eligibility, artifact-host availability,
commercial fees and multi-employee OAuth/BYOD support require provider verification.
Remote OAuth token revocation is not implemented; disconnect is local and the
merchant must revoke app access with SumUp. The OAuth callback UI is not included.
No new tipping or installment selection UX is claimed. Existing service charges
continue through canonical Tab balances; full payout/settlement ingestion is pending.

Financial realtime infrastructure was absent in the audited base. Existing audit
facts and API refresh/polling remain in use; manager realtime fan-out is not claimed.
This branch depends on Paytime PR #48 and does not merge it or any other parallel PR.

See [onboarding and integration-request draft](sumup-onboarding.md) and
[capability matrix/checklist](capability-matrix.md) for the human activation steps.
