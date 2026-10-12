# Pilot payment readiness — 2026-10-12

Base: `d07ca67` (`origin/main` at audit). This is fresh local evidence, not merchant
activation or bank settlement. PR [#86](https://github.com/procopio420/rodada/pull/86)
actually adds strict Paytime HTTPS-origin validation and non-settlement regressions;
its merged SHA is `4228fb4efc9daba2cce5285c99cea9aaed450f92`. Those changes are
preserved, not recreated.

## Audit and implementation

| Requirement | Status | Evidence and limit |
| --- | --- | --- |
| Manual cash/external terminal | PARTIAL | Ledger/idempotency tests run freshly below; onsite terminal receipt and cash-count reconciliation still required. |
| Pix amount/reference/merchant verification | PASS | Paytime and SumUp injected-contract tests; never proof of real settlement. |
| Timeout, duplicates, unknown state | PASS | Durable intents, one POST, authoritative lookup, ambiguity blocking alternative charge. |
| Expiration/cancellation | PARTIAL | SumUp authoritative EXPIRED tested; Paytime unknown EXPIRED stays pending. Paytime CANCELED is verified by lookup. No local clock expiry or invented cancellation endpoint. |
| Integrated refunds | PARTIAL | SumUp reservation/new matching successful event tested. Fixed atomic reservation+reconciliation identity and provider-free replay. Paytime Pix refund unavailable. |
| Simulation isolation | PASS | Simulator requires DEBUG and explicit opt-in; API/history marks simulated, no payable fake QR. Test databases only; simulation is forbidden for pilot financial records. |
| Tap on Phone | EXTERNAL_BLOCKED | No licensed bridge/private artifact or merchant/BYOD approval. Existing SDK-neutral boundaries retained; shipping capability stays disabled. |
| Actual Pix/card transaction | EXTERNAL_BLOCKED | No provider credentials, merchant approval, sandbox transaction or physical payment device used in this workstream. |

The discovered refund defect allowed a committed refund reservation without its
ProviderRefundRequest if identity persistence failed. Both now commit atomically
before provider POST. Matching duplicate refund intent returns persisted state
without provider GET, even during outage; changed payload still conflicts. Ambiguous
POST remains PENDING and reserved, never automatically resent. A crash after local
commit and before POST remains conservatively pending; staff/provider reconciliation
is required, rather than claiming a refund occurred.

Existing Android PaytimeSdkBoundary and SumUpSdkBoundary keep SDK classes/card data
outside core domain. Capture callbacks supply evidence; backend reconciliation owns
confirmation. Paytime configure belongs once in Application.onCreate; teardown and
host-stop handling never claim cancellation of an unknown capture. No fabricated
private imports or enabled Tap adapter were added.

## Fresh commands/results

Results are filled only after completion. Commands run from `apps/api` with
`/home/lucas/projects/rodada/venv/bin/python` (Python 3.13).

- SQLite: `python -m pytest tests/test_sumup_payments.py tests/test_paytime_live.py tests/test_paytime_origin_policy.py tests/test_payment_provider.py tests/test_payment_readiness.py tests/test_ledger_payments.py tests/test_payment_migration.py tests/test_payment_settlement_migration.py` — **66 passed, 1 skipped** (137.03 s; PostgreSQL-only migration test skipped).
- PostgreSQL disposable QA cluster at localhost:55579, separate `pilot_payment_test`
  database, Django `test_pilot_payment_test`: `python -m pytest --ds=rodada_api.settings tests/test_payments_concurrency.py tests/test_sumup_payments.py tests/test_paytime_live.py tests/test_payment_provider.py` — **41 passed**, zero skipped (73.94 s; real PostgreSQL row locks).
- `ruff check modules/payment_provider/refunds.py tests/test_sumup_payments.py` — PASS.
- `DJANGO_SETTINGS_MODULE=rodada_api.settings_test python manage.py makemigrations --check --dry-run` — PASS, no changes detected.
- `git diff --check` — PASS.

Regression cases specifically assert offline matching replay, conflicting replay,
zero provider POST after storage failure, rolled-back reservation, and unchanged
refund ledger until genuine provider evidence. Existing tests exercise concurrent
intent and refund reservations, duplicate events, expiry, unknown outcomes and
production simulator rejection. Android E2E is owned by the operational workstream;
HTTP tests here are not native Android E2E.

## Activation checklist and owners

1. **Bar owner + provider:** choose merchant identity and confirm Brazil Pix/card
   eligibility, commercial fees/payout timing, refund limitations, staff/BYOD device
   delegation and written pilot approval. No employee receives the owner's secret.
2. **Provider + release manager:** obtain approved sandbox account/credentials;
   exact HTTPS OAuth redirect/webhook URLs and scopes; store secrets exclusively
   server-side. For Paytime provision establishment, integration/x-token,
   authentication key and Basic webhook credentials. For SumUp use encrypted
   identity-bound OAuth connection and explicitly authorized capabilities.
3. **Engineer:** create isolated sandbox Venue/database; DEBUG=false and simulation
   disabled for the assisted pilot; preserve historical provider config for pending
   intents. Schedule reconcile_payments and alert on aged pending/failed lookups.
4. **Provider + engineer:** acquire licensed Maven access, exact artifact/version,
   application/signing registration and approved device/token lifecycle. Implement
   actual SDK bridge only after inspecting licensed interfaces; compile opt-in
   build and verify teardown, process death and merchant switching.
5. **Provider + QA:** homologate a physical Android/NFC phone under approved
   attestation/PIN/developer-mode rules. Record device/build, approval identifier
   and observed lifecycle outcomes; emulator/unit success cannot close this gate.
6. **QA + merchant:** in approved sandbox only, create one partial Pix intent,
   scan provider QR, verify authoritative merchant/reference/gross cents/status,
   duplicate notification and reconciliation, then balance/close. Interrupt API
   after submission; recover same UUID without POST retry. Observe provider expiry,
   cancellation and unknown states; retain pending until verified.
7. **QA + provider:** request supported partial/full refund, force response timeout,
   replay same intent and verify only one POST; apply a new matching successful
   refund event once; verify amount and remaining exposure. Get Paytime-specific
   written Pix refund/expiration contract before implementing those operations.
8. **Release manager:** archive sanitized provider IDs/status, ledger reconciliation,
   approvals and physical-device results before enabling integrated payments.
   Until then assisted pilot uses audited cash or external-terminal receipts; an
   unresolved integrated payment must not be replaced with a blind manual charge.

## Current official sources checked 2026-10-12

[SumUp APM guide](https://developer.sumup.com/online-payments/apm/integration-guide)
requires discovering supported methods per checkout; public Pix availability does
not establish merchant eligibility.
[SumUp Android Tap SDK](https://developer.sumup.com/terminal-payments/sdks/android-ttp)
and [refund endpoint](https://developer.sumup.com/api/transactions/refund) remain
provider contracts, not evidence of activated Rodada access.
[Paytime reversal](https://docs-parceiro.paytime.com.br/docs/estorno-de-transa%C3%A7%C3%A3o)
is documented for credit transactions; it does not establish Pix partial refunds.
[Paytime SDK implementation](https://docs-parceiro.paytime.com.br/docs/tap-on-phone-desenvolvimento-implementacao)
documents one-time configuration and device activation. Existing detailed onboarding
and activation documents remain applicable; no provider communication was sent.

Recommendation from payment workstream: integrated payments **NO-GO** pending
external gates. Assisted/manual-terminal pilot is eligible only if overall release
and onsite financial/fiscal gates pass; this workstream does not independently
approve the entire pilot.
