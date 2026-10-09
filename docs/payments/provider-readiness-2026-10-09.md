# Provider capability audit — 2026-10-09

This audit inspects the current adapters, Spec 006, merchant onboarding documents,
and official public documentation. No merchant credentials or private SDK access
were provisioned for this work. Public API support does not establish merchant
eligibility, successful payment, bank payout or production approval.

| Boundary | Paytime | SumUp |
| --- | --- | --- |
| Pix API | Marketplace transaction REST API; integer cents, EMV and transaction ID. Existing HTTP adapter retained. | Checkout/APM `pix` and `qr_code_pix` documented; availability discovered for each checkout. Existing HTTP adapter retained. |
| Developer/merchant onboarding | Commercial partner access, integration-key, authentication-key, x-token; establishment registration and gateway activation; API homologation before production credentials. | Developer application plus sandbox merchant; independent live merchant onboarding; exact registered HTTPS OAuth redirect; payment scope review. |
| OAuth | Partner login contract confirmed. Merchant OAuth authorization-code and delegated employee scopes: UNKNOWN. | Authorization-code and refresh grants confirmed. `payments` plus `transactions.history` or `transactions.read` required by Rodada for settlement lookup. Employee BYOD token isolation and permitted delegation: UNKNOWN. |
| Embedded Brazil Android Tap | Public Kotlin/Java embedded SDK guide and homologation process. Physical Android 11+, NFC and security requirements; approval still required. | Embedded Android Tap SDK documents Brazil credit/debit and PIN testing. Merchant eligibility and rollout still require approval. |
| SDK/repository | Private Maven debug credentials from commercial manager; guide lists SDK 1.0.2, Kotlin 2.3+, JDK17, AGP8.4+. No artifacts/access provisioned. | Private Maven credentials requested through integration team; documented utopia-sdk 1.1.6, Kotlin2.2+, API30+, compile/target36+, JDK17 and desugaring. No artifacts/access provisioned. |
| Webhook authenticity | Configurable HTTP Basic authentication documented; Rodada additionally performs authenticated transaction lookup. No cryptographic signature assumed. | Checkout notification with event_type/id and mandatory API verification documented. Signature contract UNKNOWN. Rodada accepts unsigned notifications only as durable lookup hints; polling supplies authoritative evidence. |
| Transaction lookup | GET transaction; missing creation result searches exact reference, amount and establishment. APPROVED alone is insufficient. | GET checkout plus merchant transaction by id; embedded Tap lookup by client_transaction_id. Currency, merchant, amount and identity must match. |
| Cancellation/expiry | Pix REST cancellation/expiry contract UNKNOWN. No cancellation promise. | DELETE only deactivates unprocessed checkout; already processed Pix cancellation UNKNOWN. valid_until and EXPIRED supported, only provider outcome releases pending intent. |
| Refund | Published reversal endpoint explicitly credit-only. Pix REST refunds UNKNOWN; integrated Pix refunds remain unavailable. SmartPOS documentation also excludes SDK Pix reversal, which is not proof of all REST behavior. | Full/partial refund request and transaction events documented. Pix merchant eligibility/refund support UNKNOWN until confirmed. Request acceptance never changes ledger; matching new successful REFUND evidence does. |
| Sandbox/testing | Sandbox gateway activation rules and mocked export data documented. Tap debug credentials require partner access. REST Pix test progression and real clearing behavior UNKNOWN. SmartPOS scripted Pix scenarios do not prove marketplace API behavior. | Sandbox merchants use test credentials; dedicated Tap developer credentials and physical phone required. Online card test amounts are not assumed to be Pix test behavior. Brazil PIN/attestation procedure needs approved testing access. |
| Settlement evidence | No SANDBOX_CONFIRMED or LIVE_CONFIRMED evidence. | No SANDBOX_CONFIRMED or LIVE_CONFIRMED evidence. |

## Evidence vocabulary

- TEST_DOUBLE: injected HTTP responses or fake SDK interfaces; no provider network payment.
- SIMULATED: explicit Rodada deterministic simulation in a disposable development environment.
- SANDBOX_CONFIRMED: authenticated provider sandbox transaction with matched intent,
  merchant, integer amount/currency and canonical backend confirmation; not real money.
- LIVE_CONFIRMED: authenticated production transaction with matched intent and approved
  live merchant/device. Bank payout requires separate evidence.

Never infer SANDBOX_CONFIRMED/LIVE_CONFIRMED from `simulated=false` or passing contract tests.

## Current incremental implementation

Browser OAuth callback uses a ten-minute signed Secure/HttpOnly/SameSite=Lax cookie,
bound to initiating staff session and state hash. Current membership, session,
device, venue.configure and recent PIN reauthentication are checked at callback.
Denial consumes state; exchange failures require a fresh authorization. Tokens and
provider error descriptions never appear in callback output. Local disconnect
remains supported; remote revocation endpoint is UNKNOWN.

Pix lookup preserves existing attempt artifacts. Failed QR image fetch is retried
on explicit reconciliation, with no repeat POST/PUT. API returns provider reference,
transaction reference and expiry; Android can copy EMV and display provider expiry.
Past local expiry never releases an ambiguous payment. Scheduler visits historical
intents even after primary provider configuration removal and isolates unavailable
connections. Historical Paytime lookup can use retained fallback configuration.

## Executable activation gates and blocked operations

1. Merchant owner creates approved merchant/developer accounts. Integration owner
   obtains sandbox credentials privately and confirms merchant Pix capability.
   No secret belongs in an APK, source control, screenshot or provider request draft.
2. Deployment owner provisions RODADA_PAYMENT_CREDENTIAL_KEY (Base64 32-byte key)
   and server-side RODADA_SUMUP_OAUTH JSON with client_id/client_secret and redirect_uri
   `https://api.rodada.ai/payments/merchant-connections/callback/`. Register exactly
   this URI with SumUp. Redact callback query strings from reverse-proxy access logs.
3. In the initiating manager browser, reauthenticate via POST /auth/reauthenticate/.
   POST /payments/merchant-connections/ with staff Bearer auth and browser fetch
   `credentials: 'include'`; then navigate to returned authorization_url in that
   same browser. HTTPS is required for the callback cookie. Complete within the
   recent-reauthentication window; otherwise reauthenticate and begin again.
   Native clients can still submit code/state to the authenticated POST endpoint.
   GET /payments/merchant-connections/ lists identity/scopes/expiry without tokens.
   DELETE with connection_id disconnects locally; revoke provider app access too.
4. After explicit provider approval, configure connection capabilities and per-Venue
   RODADA_PAYMENT_PROVIDERS as described in sumup-onboarding.md. Retain historical
   RODADA_PAYTIME_PROVIDERS for unresolved Paytime intents. Capability approval is
   not inferred from successful OAuth. No automatic capability enablement exists.
Optional per-Venue SumUp config `webhook_base_url: "https://api.rodada.ai"` adds the documented checkout return_url; notifications are never confirmation.

5. From apps/api, run `python manage.py reconcile_payments --limit 100` periodically
   (for example every minute), monitor unavailable count and unresolved intents.
   Run authenticated integrated payment POST → QR/EMV display → provider sandbox
   payment procedure → payment reconcile POST. Inspect matching provider transaction
   and Tab balance; archive only redacted references/status/amount/currency.
6. Exercise duplicate/reordered notification, timeout, restart and refund after
   actual access exists. A SumUp refund requires its documented eligibility plus a
   new matching successful provider event. Paytime Pix refund stays blocked.
7. SDK owner obtains private Maven access and approved employee token model. Run
   `cd apps/attendance-android && ./gradlew -PsumupSdk=true assembleDebug` only after
   access provisioning. Implement SumUpSdkBoundary/PaytimeSdkBoundary from actual
   artifact classes and official sample, map lifecycle/results, keep reconciliation
   authoritative, and test a physical NFC phone. Default builds prove neither private
   SDK compilation nor real capture. Never use separate POS app handoff as embedded Tap.
8. Provider approves homologation/signing/attestation, merchant/device provisioning,
   production rollout and commercial terms. Only then test a small live charge and
   refund; record LIVE_CONFIRMED separately from sandbox evidence. Do not merge this PR.

External blockers: account/KYC and commercial approval; payment scopes; merchant Pix
eligibility; private SDK artifacts/Maven access; approved employee/BYOD delegation;
physical NFC device and provider-approved test procedure; sandbox credentials/test
instruments; production attestation, signing/homologation and rollout; Pix cancellation,
refund eligibility, fees, payout schedule and real settlement evidence.

Software not claimed here: manager connection GUI (API/callback flow is available),
private
SDK implementation, delegated Android token issuance, guest-initiated integrated
payment UI, payout/chargeback ingestion or production reconciliation operations.
These are distinct from the tested ledger and provider boundaries.

## Authoritative sources inspected

- [Paytime Pix/transaction lookup](https://docs-parceiro.paytime.com.br/docs/exibir-transa%C3%A7%C3%A3o)
- [Paytime transaction list/reference/EMV](https://docs-parceiro.paytime.com.br/docs/listar-transa%C3%A7%C3%A3oes)
- [Paytime webhook Basic configuration](https://docs-parceiro.paytime.com.br/docs/listar-eventos-de-webhook)
- [Paytime gateway activation](https://docs-parceiro.paytime.com.br/docs/ativar-gateway-para-o-estabelecimento)
- [Paytime API homologation](https://docs-parceiro.paytime.com.br/docs/homologa%C3%A7%C3%A3o)
- [Paytime credit reversal](https://docs-parceiro.paytime.com.br/docs/estorno-de-transa%C3%A7%C3%A3o)
- [Paytime Tap requirements](https://docs-parceiro.paytime.com.br/docs/tap-on-phone-desenvolvimento-inicio)
- [Paytime Tap integration steps](https://docs-parceiro.paytime.com.br/docs/tap-on-phone-etapas-da-integracao)
- [Paytime SmartPOS constraints](https://docs-parceiro.paytime.com.br/docs/smartpos-homologacao-principais-requisitos)
- [SumUp APM/Pix guide](https://developer.sumup.com/online-payments/apm/integration-guide)
- [SumUp OAuth](https://developer.sumup.com/tools/authorization/oauth)
- [SumUp transaction/refund API](https://developer.sumup.com/api/transactions/get)
- [SumUp checkout notifications](https://developer.sumup.com/online-payments/webhooks)
- [SumUp embedded Android Tap](https://developer.sumup.com/terminal-payments/sdks/android-ttp)
- [SumUp sandbox testing](https://developer.sumup.com/online-payments/testing)

Current SumUp and Paytime adapters bind settlement ownership to provider + merchant + transaction, independently of Venue. Migration 0009 backfills confirmed historical SumUp transaction ownership from sanitized attempt metadata, then enforces global uniqueness per SumUp merchant/transaction. Existing duplicate financial owners must be investigated before migration can succeed; history is never silently rewritten. Unknown historical transaction IDs remain blank and require provider reconciliation.

## Local verification commands

Use the project's Python environment; no provider credentials are needed:

```sh
cd apps/api
python -m pytest
PAYMENTS_TEST_DB_PORT=55457 DJANGO_SETTINGS_MODULE=rodada_api.settings_payments_postgres \
  python -m pytest tests/test_payment_readiness.py tests/test_sumup_payments.py \
  tests/test_paytime_live.py tests/test_payment_provider.py tests/test_payments_concurrency.py \
  tests/test_ledger_payments.py tests/test_cash_management.py tests/test_house_account.py \
  tests/test_house_account_e2e.py tests/test_payment_migration.py \
  tests/test_house_account_migration.py tests/test_payment_settlement_migration.py
DJANGO_SETTINGS_MODULE=rodada_api.settings_test python manage.py check
DJANGO_SETTINGS_MODULE=rodada_api.settings_test python manage.py makemigrations --check --dry-run
# Repository root, JDK17 + Android SDK configured:
./scripts/android-check.sh
```

The isolated PostgreSQL instance used for this audit can be reproduced with:

```sh
docker run --detach --name rodada-readiness-test \
  --publish 127.0.0.1:55457:5432 --env POSTGRES_USER=rodada \
  --env POSTGRES_PASSWORD=rodada-test --env POSTGRES_DB=rodada_payments_test postgres:17
```

Those are disposable local test credentials, not merchant or deployment secrets.
Use one pytest process per PostgreSQL database. SDK Maven credentials must be supplied
as SUMUP_MAVEN_USER/SUMUP_MAVEN_PASSWORD through the approved secret store; the
optional build is an artifact-resolution gate, not proof of a working SDK bridge.
