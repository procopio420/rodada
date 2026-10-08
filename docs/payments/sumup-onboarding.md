# SumUp onboarding — no live payments verified

Rodada has no SumUp or Paytime account, credentials, SDK access or live payment
evidence. SumUp is the primary candidate; Paytime Pix is preserved as an alternative.
All test evidence below concerns deterministic simulators and injected HTTP contracts.

## Audit and dependencies

This branch builds on open PR #48 (Paytime REST Pix and Android recovery). The
existing Payment is a persisted intent, PaymentAttempt records provider work,
Payment.provider_payment_id is the checkout/transaction reference, Refund preserves
the original receipt, and Payment confirmation settles a Tab. Bank payout is a
separate provider concept and is not inferred from Tab settlement. CashPoint,
CashShift, CashMovement and existing manual refunds remain unchanged. Money belongs
to Tab, never Table. The audited base has no implemented financial SSE/outbox
publisher; audit facts and canonical API polling are used. Manager realtime delivery
needs the shared event infrastructure to land; it is not claimed by this slice.

MerchantConnection stores a fixed Venue/provider/merchant identity. OAuth credentials
are encrypted with AES-256-GCM and identity-bound associated data. DeviceAuthorization
binds merchant/device/operator independently of provider attestation. Configuration
and credential access always include Venue. Historical attempts use their original
provider; changing a primary candidate does not silently re-route reconciliation.

## Accounts and approval

1. Create a SumUp merchant account at https://me.sumup.com/ and complete business
   details. The documentation does not describe a separate anonymous developer login.
2. Open Developer Settings, create a Sandbox Account, then create an OAuth application
   with Rodada's homepage and exact HTTPS redirect URI. Keep client secret server-side.
3. Ask the integration team for Android **Tap-to-Pay** private Maven access and
   manual verification of payment scopes. The regular Android SDK and URI/payment
   switch integrations do not satisfy the embedded phone-only requirement.
4. Request confirmation of Brazilian merchant eligibility, Pix methods and BYOD
   employee authorization. Do not provision employee tokens until SumUp approves
   the model, limits, revocation behavior and scope isolation.

## Official contracts verified from public documentation

Embedded Tap: version 1.1.6 is the latest listed release (2026-08-25). Artifact
`com.sumup.tap-to-pay:utopia-sdk:1.1.6`; repositories
`https://maven.sumup.com/releases` and
`https://tap-to-pay-sdk.fleet.live.sumup.net/` (private credentials required).
Android 11+/API 30, physical NFC device, compile/target 36+, Java 17, Kotlin 2.2.x
recommended and core desugaring `com.android.tools:desugar_jdk_libs:2.1.5`.
SDK uses `TapToPayApiProvider.provide(applicationContext)`,
`init(AuthTokenProvider)` once, `startPayment(CheckoutData): Flow<PaymentEvent>` and
`tearDown()`. `AuthTokenProvider.getAccessToken()` supplies access; Rodada does not
send owner's long-lived secret to Android. `CheckoutData.totalAmount`/tipsAmount
are minor units, `clientUniqueTransactionId` is Rodada Payment UUID. Brazil requires
credit/debit selection (`ProcessCardAs.Credit(instalments=...)`/`Debit`). PIN is
provider-managed and mandatory under documented Brazilian testing conditions.

Events: CardRequested/CardPresented/CVMRequested/CVMPresented inform UI;
TransactionDone is evidence, not Rodada confirmation. TransactionFailed,
TransactionCanceled and TransactionResultUnknown all trigger backend verification.
Provider errors/attestation determine rooted/debug/unsupported conditions. A local
failure does not prove no charge occurred. SDK session teardown must run on logout;
process death requires reconciliation by persisted intent before another capture.

Pix: create POST `/v0.1/checkouts`, reference/merchant/currency/amount binding,
GET `/v0.1/checkouts/{id}/payment-methods`, PUT checkout with `payment_type`.
Both `pix` and `qr_code_pix` use artifacts: code content and barcode location.
`pix` pays directly into merchant SumUp bank account if present; `qr_code_pix` uses
normal payout and incurs a fee. Merchant eligibility is discovered, never assumed.
REST amount is major units; Rodada serializes exact Decimal JSON numbers from cents.
GET checkout verifies status; PAID is additionally verified via merchant transaction.
`valid_until` is documented; EXPIRED is provider-confirmed. DELETE deactivates only
unprocessed checkout; no guarantee of stopping already processed Pix is assumed.
Refund POST `/v1.0/merchants/{merchant}/payments/{transaction}/refunds` supports
amount/full or partial requests. Requests are reserved before I/O, never retried
after ambiguity, and only a new successful matching REFUND event applies ledger
reversal. Pix refund eligibility and eventual consistency still need sandbox proof.
Webhook signature verification is not invented; SumUp adapter rejects direct inbox
webhooks. Polling is the implemented authoritative path.

OAuth: `/authorize` + `/token`, authorization code and refresh grants. `payments`
requires manual verification; `transactions.history` supports reconciliation.
Client credentials alone are not assumed to authorize arbitrary merchant data.
Use authenticated manager POST `/payments/merchant-connections/` to start, then
submit returned code/state in the same staff/Venue context. State is single-use,
expires in ten minutes and is stored hashed. No callback frontend is included yet.
Refresh rotates encrypted tokens. Disconnect deletes credentials, revokes local
payment-device authorization and records audit. Remote token revocation is NOT
implemented because the inspected docs do not establish a revocation endpoint;
remove the app authorization in the merchant dashboard and verify with SumUp.

## Local credential-free environment

Use a disposable demo Venue/database only:

```sh
export DJANGO_DEBUG=true
export RODADA_PAYMENT_SIMULATION=true
# Substitute the seeded demo Venue UUID:
export RODADA_PAYMENT_PROVIDERS='{"VENUE_UUID":{"provider":"simulator","scenario":"success"}}'
python manage.py migrate
python manage.py seed_demo
```

Check the backend's existing DEBUG environment variable (`DJANGO_DEBUG`). Authorize
the Android device as TRUSTED through the existing access-management flow. Log in
with an operator possessing payment.collect. The debug build exposes simulation
credit/debit. Simulator scenarios: success, failed, cancelled, unknown, expired.
The first lookup remains pending; the second returns the configured outcome.
Backend simulation cannot be enabled with DEBUG false. Simulator never produces a
payable Pix code, and simulated receipts remain labeled. It is unsuitable for pilot
financial records. Simulated balances change only in this disposable environment.

## Credentialed setup and first transaction

Generate a 32-byte key, Base64 encode it and store in deployment secret manager as
RODADA_PAYMENT_CREDENTIAL_KEY. Keep this independent of Django's signing secret.
Configure RODADA_SUMUP_OAUTH with client_id/client_secret/redirect_uri. Complete
merchant OAuth; verify merchant identity and granted scopes. Enable capability pix
only after approved merchant APM access. Set RODADA_PAYMENT_PROVIDERS by Venue UUID:
`{"provider":"sumup","connection_id":"UUID","payment_type":"qr_code_pix"}`.
Keep Paytime credentials separately in RODADA_PAYTIME_PROVIDERS for old attempts.
Schedule reconcile_payments. Expiration can be configured with expires_seconds.
Never distribute credential configuration to Android.

For real SDK work, supply Maven credentials and run `./gradlew -PsumupSdk=true
assembleDebug`. The optional build resolves the artifact but no real SDK bridge is
wired. Implement SumUpSdkBoundary against actual classes/imports from the official
sample; map events and credit/debit; obtain approved short-lived BYOD token flow;
prove merchant switching tears down credentials; compile and run on physical NFC
phone. Standard fake build success does not prove private SDK compatibility.

Sandbox merchants run in the production API environment with test credentials.
Docs allow debug for sandbox, but Brazil PIN testing requires Developer Options
disabled. Confirm the supported installation/test-card procedure with SumUp before
presenting a real card. Production requires non-debuggable app, USB debugging/ADB
and Developer Mode disabled, attestation passed and merchant activation. Obtain
written rollout approval. First live transaction: approved merchant + real SDK
build + authorized physical phone → small Tab charge → provider transaction lookup
with matching merchant/reference/amount → canonical confirmation → balance zero →
close Tab. Save non-sensitive provider evidence and reconcile a refund afterwards.

## Human blockers and commercial questions

Private SDK access; payments scope approval; Brazilian embedded Tap activation;
employee-owned phones per merchant and merchant token delegation; device limits;
Pix bank-account vs payout eligibility; Pix/card/refund fees; debit/credit/installment
and settlement schedules; sandbox cards and PIN testing; production certification,
signing registration and rollout limits. None are established by simulator tests.

## Ready-to-send integration request (draft; not sent)

Subject: Rodada POS — Brazil embedded Android Tap, BYOD and multi-merchant Pix

Hello SumUp Integrations,

Rodada is a Kotlin/Jetpack Compose POS for high-volume Brazilian bars. The first
pilot is Bar do Aderlan. Each independent bar must receive funds in its own account.
Waiters use authorized personal Android phones. Payments belong to a Tab, support
partial amounts, and require backend transaction verification. We have no merchant
account, SDK access or completed live transactions yet.

Please confirm:
1. Is embedded Android Tap-to-Pay SDK 1.1.6 available for Brazil without a separate
   SumUp payment app? What production/homologation and signing requirements apply?
2. Are multiple employee-owned phones supported under one merchant? Which employee
   authentication/delegation model, token scopes/lifetimes, device limits and
   revocation mechanisms are supported? Can Rodada safely supply short-lived OAuth
   access to AuthTokenProvider without distributing owner secrets?
3. Can a SaaS use authorization-code OAuth for independent merchants? Which scopes,
   onboarding review and marketplace/partner agreements are required?
4. How do we enable Pix Checkout/APM `pix` and `qr_code_pix` per merchant? Please
   confirm bank-account/payout eligibility, expiration, cancellation and refund rules.
5. Please provide the private Maven access process, sandbox credentials/test accounts,
   test cards and supported Brazil PIN/attestation testing procedure.
6. What are credit/debit/installment rates, Pix fees, refund fees and payout timing?
7. What certification, pilot limits, production approval and rollout process apply?

We can share our architecture and non-sensitive test evidence. Please direct us to
an approved secure portal for all credential provisioning.
