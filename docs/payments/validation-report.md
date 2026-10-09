# Payment provider readiness validation — 2026-10-09

Branch: `feat/payments-provider-readiness`, based on `origin/main` at `742faac`.
Provider capability audit, activation checklist and remaining software/merchant gates:
[readiness report](provider-readiness-2026-10-09.md).

| Check | Result |
| --- | --- |
| Full backend suite, SQLite | **266 passed, 14 skipped**, 405.63s |
| Financial suite, isolated PostgreSQL 17 | **86 passed**, 196.98s |
| Android JVM tests | **39 passed**, 0 failures/errors/skips |
| Android testDebugUnitTest / assembleDebug / lintDebug | **BUILD SUCCESSFUL**, 2m11s |
| Django system check | No issues |
| Migration drift | No changes detected |
| Ruff, modified payment modules/tests (generated migrations excluded) | Passed |
| git diff --check | Passed |
| Real provider sandbox / private SDK / physical-device capture / live payments | **NOT RUN: access not provisioned** |

All provider test results are **TEST_DOUBLE** or explicitly **SIMULATED**. There is
no SANDBOX_CONFIRMED or LIVE_CONFIRMED evidence. `simulated=false` is not proof of
live processing. The 14 full-suite skips include PostgreSQL-only concurrency and
migration checks; the relevant payment cases passed in the separate financial run.
Other modules' skipped PostgreSQL checks are not claimed by this payment report.

Financial verification includes Paytime and SumUp contracts; partial-payment/refund
reconciliation; duplicate/out-of-order provider events; timeout and restart recovery;
merchant isolation; competing collectors; duplicate webhook processing; competing
refund reservations; distinct Tabs claiming one merchant transaction; and migration
backfill plus the database uniqueness constraint. OAuth tests cover initiating
browser/state binding, one-time exchange, denial, revoked session and token-free
callback output. Pix tests cover artifact retention, safe QR fetch recovery and
notification hints that never establish settlement.

Android verification covers existing lifecycle boundaries and serialized recovery
intent behavior, SDK-unavailable handling, backend-only confirmation and the new
local-expiry invariant. It does **not** prove physical-device process death recovery,
Keystore behavior on hardware, private SDK compilation, attestation, PIN or real NFC.

A superseded SQLite run was invalidated by source/schema edits during execution;
a shared PostgreSQL follow-up was invalidated by another process dropping/changing
the test database. A migration test fixture was corrected to use the complete
historical migration graph. The final results above come from fresh runs of the
completed code, with PostgreSQL isolated at localhost:55457. Reproduction commands
are in the readiness report. No financial data was silently repaired or reset.

## Incremental behavior and rollout notes

- Browser callback is bound to a signed Secure/HttpOnly cookie and current manager
  authorization. Configure the exact HTTPS callback URI; clients initiating OAuth
  in a browser must include cookies. Missing transaction-read scope rejects connection.
- SumUp notification endpoint stores only an untrusted lookup hint and returns 204;
  scheduled authenticated lookup is required. Optional webhook_base_url supplies the
  documented return_url. No webhook signature scheme was invented.
- Both HTTP adapters now assign merchant-transaction ownership; a duplicate owner
  stays CONFIRMATION_PENDING. Migration 0009 backfills known historical SumUp owners
  and refuses conflicting duplicates. Unknown historical IDs require investigation.
- Historical Paytime connections remain usable after primary config removal. One
  unavailable connection no longer aborts the reconciliation command.
- Pix QR image fetch can recover via reconciliation without another charge creation;
  provider identifiers/expiry are returned. Android displays expiry and offers EMV copy.
- Refund URL parameters are encoded and refund keys are validated as strings.
  Existing historical/refund reservations and ledger semantics are preserved.

The release integration agent owns final validation. No PR is merged by this work.

---

## Historical baseline report (retained; not current test counts)

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
