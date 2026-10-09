# Payment activation: one small step at a time

This is the operational plan for getting SumUp access, finishing Rodada's real SDK
integration, and obtaining permission for the Bar do Aderlan pilot. Paytime Pix has
a separate optional track at the end. Public instructions were checked on 2026-10-08.

**Starting point:** payment code is merged, but we have no provider account,
credentials, private SDK access, sandbox payment evidence or production approval.
Every checkbox below is deliberately unchecked. A merged PR or working simulator
is not provider approval. No request has been sent on your behalf.

Use the steps in order. Steps 7–11 can proceed in parallel once the application
client ID exists. Pix can reach its own approved pilot before Tap if SumUp permits;
keep Tap disabled until its separate gates pass.

## Who does what

| Person | Responsibility |
| --- | --- |
| Rodada owner/integration contact | Own the application account, submit access requests, follow up, record approvals. |
| Bar do Aderlan owner | Own the bar's merchant account, complete provider checks and authorize Rodada. |
| Rodada engineer | Configure secrets, complete callback/SDK work, collect test evidence and deploy. |
| SumUp integration team | Grant restricted access, confirm product/merchant eligibility and define approval requirements. |

Rodada's application account and a bar's funds-receiving merchant account are
separate responsibilities. Ask SumUp which legal entity should own Rodada's
application. Each bar must authorize its own account; do not register every bar as
Bar do Aderlan or share one bar's credentials with another.

## Before opening provider websites

### 1. Assign one contact

- [ ] Choose the person who will manage provider correspondence.

Write their name, work email and phone in a private onboarding note. Agree who can
access the provider dashboard and who can deploy secrets. **Done when:** there is
one accountable contact and the bar owner knows who is asking for access.

### 2. Gather the application details

- [ ] Prepare a short fact sheet without secrets.

Include: Rodada's legal/business details if established, website/repository,
`com.rodada.attendance` Android application ID, Kotlin/Compose, Brazil/BRL,
Bar do Aderlan as the first pilot, intended phone models and initial operator/device
count. Say that money goes directly to each independent merchant and that we need
embedded phone-only Tap, dynamic Pix, partial payments and backend verification.
Let the provider specify any remaining business/KYC documents through its portal.
**Done when:** the fact sheet can accompany an access request.

### 3. Create an access tracker

- [ ] Copy this table into a private issue or onboarding note.

| Item | Current status | Evidence needed before marking approved |
| --- | --- | --- |
| Developer/sandbox account | Not obtained | Account identity and sandbox merchant identifier |
| OAuth client | Not obtained | Client ID and registered redirect URI; secret stored privately |
| `payments` permission | Not approved | Provider response naming the client ID and environment |
| Private Maven access | Not obtained | Successful download of the approved SDK version |
| Brazil embedded Tap | Not approved | Written product/merchant eligibility confirmation |
| Multiple BYOD waiters | Unverified | Approved authentication/delegation and revocation model |
| SumUp Pix/APM | Not activated | Approved merchant, enabled method and payout destination |
| Sandbox verification | Not run | Provider-backed Pix/card/refund evidence |
| Production pilot | Not approved | Provider's release criteria and approval reference |

Record ticket number, owner, submission date, next agreed follow-up date and
non-secret evidence links. Do not write credentials into this tracker.
**Done when:** every blocker has somewhere to record its progress.

## Get the accounts and OAuth credentials

### 4. Start with a developer/sandbox account

- [ ] Open [SumUp's testing guide](https://developer.sumup.com/online-payments/testing#setting-up-a-sandbox-merchant-account).

Use its **sign up for a developer account** link if you do not have an account.
For an existing account, open **Developer Settings → Sandboxes** and create a
sandbox merchant. The public guide describes both paths. Log in to the resulting
sandbox account and record its merchant identifier privately. If the account or
Brazil option is unavailable, attach that non-sensitive symptom to your request.
**Done when:** you can identify the sandbox merchant you are using.

### 5. Start the bar's real merchant onboarding separately

- [ ] The bar owner opens [SumUp's dashboard](https://me.sumup.com/) and follows the current Brazilian registration flow.

Have the owner complete the requested identity/business and payout details in
SumUp's own portal. Record the real merchant identifier and account verification
status, not identity documents in the repository. Ask whether a sandbox can model
this merchant's Brazilian Pix/Tap capabilities. **Done when:** the real merchant
exists and its onboarding/eligibility gaps are listed; this alone does not permit
a live transaction.

### 6. Decide the OAuth callback address with the engineer

- [ ] Choose an actual HTTPS staging domain and callback path before registering credentials.

For example, `https://<your-staging-host>/oauth/sumup/callback`; the placeholder is
not a working URL. Rodada does **not** currently implement that browser callback.
The engineer must implement its consent/state handling and prevent authorization
codes/tokens from appearing in access logs before using it. Plan a separate live
redirect address. **Done when:** the exact address and callback work are assigned.

### 7. Register Rodada's OAuth application

- [ ] Follow the [OAuth application registration instructions](https://developer.sumup.com/tools/authorization/oauth#register-an-oauth-application).

Open **OAuth apps → Create application**, enter Rodada's description/homepage and
register. Open it, select **Create client secret**, name the client, register the
exact redirect URI, save and download the credential JSON into secure storage.
Use a server/Web client for Rodada's current backend exchange; ask SumUp whether
embedded Tap also needs a separate Android client or affiliate registration.
**Done when:** the client ID, client secret and exact redirect URI are available.

### 8. Put the credentials in a secret manager

- [ ] The engineer stores the client secret securely, separately for staging and production.

Only the client ID belongs in support requests. Do not paste downloaded JSON,
refresh tokens, API keys or Maven passwords into chat, email, screenshots or Git.
A SumUp secret API key is a different credential from an OAuth client secret;
Rodada's current merchant integration uses OAuth. If SumUp requests an API-key
sample test, keep that key restricted to the controlled test setup and out of the
Rodada APK. See [API-key guidance](https://developer.sumup.com/tools/authorization/api-keys).
**Done when:** only authorized backend/build operators can retrieve secrets.

## Ask SumUp for the restricted access

### 9. Submit one technical access request

- [ ] Open [SumUp Developer Help](https://developer.sumup.com/help) and click **Contact us** / **contact form**.

Paste the [ready-to-send request](sumup-onboarding.md#ready-to-send-integration-request-draft-not-sent),
add the client ID from step 7 and the fact sheet from step 2. Ask that the ticket be
routed to the team responsible for **embedded Android Tap-to-Pay SDK** and Brazil
Pix/APM. The public documentation directs integrators to that form; its form
fields and review outcome have not been verified here. No integration-team email
address is assumed. **Done when:** you have a submission receipt or ticket number.

### 10. Ask for three separate permissions explicitly

- [ ] Request OAuth payment access, private SDK download access, and merchant/product activation.

Ask for `payments` activation on the stated client ID, and confirm
`transactions.history` and `user.profile_readonly` for Rodada's verification flow.
The `payments` scope needs manual review; ordinary client creation does not grant it.
See [SumUp's scope requirements](https://developer.sumup.com/tools/authorization/oauth#authorization-scopes).

Ask for private Maven username/password, approved SDK version and license terms.
Ask for Brazil embedded Tap and Pix activation separately, naming the sandbox and
real merchant. **Done when:** each request has an explicit answer, not just a
successful dashboard login or an unrelated reader-SDK approval.

### 11. Get answers to the blocking design questions

- [ ] Obtain written answers before promising waiter-owned-phone payment collection.

Send this question list with the ticket:

1. Can this Brazilian merchant use embedded Android Tap without a separate payment app?
2. Can several employee-owned phones collect for one merchant? What device limits apply?
3. Which approved token/delegation flow supplies `AuthTokenProvider`? What are its scopes,
   lifetime, merchant restrictions and operator/device revocation rules?
4. Is authorization-code OAuth approved for Rodada's independent-merchant SaaS model?
5. Which Pix method is enabled: `pix`, `qr_code_pix`, or both? Which account receives funds?
6. How do we exercise Pix confirmation/refund and NFC card/PIN behavior safely in the sandbox?
7. What fees, installments, settlement timing, signing, certification and pilot limits apply?

Ask for an approved credential-delivery mechanism and the production review checklist.
**Done when:** unknown answers are recorded as blockers; no owner API key is being
distributed to waiters as a workaround.

### 12. Follow up using the ticket, not new credentials

- [ ] Agree a next update date with the provider and record it.

If no review time is provided, propose a follow-up date; do not invent an approval
SLA. If access is denied or the embedded Brazil/BYOD experience is unsupported,
record that decision and stop the affected Tap track. Pix and the audited external
terminal fallback can remain separate options. **Done when:** the next action has
an owner, even while approval is pending.

## Verify SDK access without claiming the integration is finished

### 13. Confirm what Maven access actually gives us

- [ ] The engineer receives repository credentials through the agreed secure channel.

Compare the approved dependency/version and repository URLs with the
[official sample](https://github.com/sumup/sumup-android-tap-to-pay). Rodada currently
pins `com.sumup.tap-to-pay:utopia-sdk:1.1.6`. Private repository access is a build
credential, not merchant payment authorization. **Done when:** the engineer knows
which artifact is approved and where to download it.

### 14. Try the optional dependency build

- [ ] Inject the credentials into the build environment, then run:

```sh
cd apps/attendance-android
# SUMUP_MAVEN_USER and SUMUP_MAVEN_PASSWORD come from secure environment injection.
./gradlew -PsumupSdk=true assembleDebug
```

The normal build does not download the private SDK. Optional-build success proves
artifact/toolchain compatibility only; the real adapter is still absent. For a
401/403, verify access with SumUp; do not switch to a regular Android SDK or URI
integration. Record the SDK version and sanitized build result.
**Done when:** the approved artifact resolves and the optional build succeeds.

### 15. Complete the real adapter and enablement code

- [ ] The engineer implements `SumUpSdkBoundary` against the downloaded SDK, then tests it.

Use real SDK classes/events, the approved `AuthTokenProvider` mechanism, minor-unit
amounts and Rodada's durable UUID as `clientUniqueTransactionId`. Map all relevant
provider events, including flow closure, and wire initialization/teardown correctly.
Validate logout, merchant switching, process death and uncertain results against the
[embedded SDK guide](https://developer.sumup.com/terminal-payments/sdks/android-ttp).

**Current code gates that must also change in a reviewed implementation:** backend
`assert_tap_authorized` still raises `SUMUP_SDK_ACTIVATION_BLOCKED`; Android exposes
Tap only when `tapSimulationEnabled` is true. Setting environment variables or
marking a merchant capability does not remove these gates. Replace them only with
the approved real path and tests. **Done when:** the real bridge compiles and the
approved payment journey works in the provider test environment.

## Connect the merchant and verify Pix

### 16. Prepare the backend staging environment

- [ ] The engineer provisions a separate staging database, actual callback from step 6 and these settings:

| Backend setting | Value/source |
| --- | --- |
| `RODADA_PAYMENT_CREDENTIAL_KEY` | Independently generated 32-byte random key, Base64 encoded, stored in the secret manager |
| `RODADA_SUMUP_OAUTH` | JSON containing the issued `client_id`, `client_secret`, and exact `redirect_uri` |
| `RODADA_PAYMENT_SIMULATION` | `false` for provider verification |
| `RODADA_PAYMENT_PROVIDERS` | Venue selection configured after merchant connection |

Back up the encryption key securely; losing it prevents reading stored tokens.
Do not rotate it without an explicit re-encryption procedure. Run migrations and
verify HTTPS before consenting a merchant. **Done when:** staging can securely
store merchant credentials and the callback is functional.

### 17. Run merchant consent in the correct Rodada Venue

- [ ] Use a Rodada manager with `venue.configure` and recent reauthentication.

The engineering/manager sequence is:

```text
POST /auth/reauthenticate/                    {"pin": "<manager PIN>"}
POST /payments/merchant-connections/          {}
→ open the returned authorization_url; the intended merchant signs in and consents
→ callback reads code/state, validates the session and returns through the same manager/Venue
POST /payments/merchant-connections/          {"code": "<code>", "state": "<state>"}
GET  /payments/merchant-connections/
```

These are authenticated backend routes, not a currently available “Connect SumUp”
button. The OAuth state lasts ten minutes and is single-use; if exchange is
uncertain, start a new consent flow. Check the returned merchant identity against
the intended sandbox/live account. Never paste codes or PINs into issue reports.
**Done when:** a connection ID belongs to the correct Venue and merchant.

### 18. Enable only the approved Pix capability

- [ ] Record provider approval for that merchant and the chosen Pix method.

Have the engineer add an audited, tenant-scoped capability administration path:
there is currently no API to update `MerchantConnection.capabilities`. Set
`capabilities.pix` through that reviewed path only after approval. Keep Tap disabled
until its separate gates pass. **Done when:** capability configuration has evidence
and an audit record; adding a flag has not been mistaken for provider activation.

### 19. Select SumUp for the correct Venue

- [ ] Configure this JSON structure in the backend secret/configuration system, replacing placeholders:

```json
{
  "<RODADA_VENUE_UUID>": {
    "provider": "sumup",
    "connection_id": "<CONNECTION_UUID_FROM_STEP_17>",
    "payment_type": "qr_code_pix"
  }
}
```

Use `pix` instead if approved for that merchant. The public
[APM guide](https://developer.sumup.com/online-payments/apm/integration-guide)
distinguishes direct SumUp-bank-account Pix from normal-payout `qr_code_pix`, which
incurs a fee. Obtain the merchant's actual fee/payout agreement before choosing.
Do not add invented API hosts or put tokens in this selection object.
**Done when:** the Venue points to its own approved connection.

### 20. Run one provider-backed Pix test

- [ ] Ask SumUp for the supported sandbox Pix completion procedure, then follow it.

Open a staging Tab, add an order and create a partial Pix payment using Rodada.
Verify amount, merchant, provider-generated QR/copy code and pending balance.
Complete it using SumUp's approved test procedure; verify backend confirmation and
the reduced Tab balance. A sandbox bank QR may not be payable from a real banking
app; do not send real money to “test” it without provider instructions.
**Done when:** provider evidence confirms the intended transaction, not just a QR
or a mocked response. If Pix cannot be exercised in sandbox, record that limit and
request a separately approved controlled live test.

### 21. Verify reconciliation and refunds

- [ ] Run the engineer's recovery/refund test checklist before requesting a pilot.

Restart Rodada during pending payment, repeat the client request with the same key,
and exercise provider timeout/late confirmation using the provider's permitted
method. Confirm no second collection and no duplicate receipt. Test a partial
refund through the integrated refund API only when SumUp confirms Pix eligibility;
a request acknowledgment is not confirmed reversal.

Schedule and monitor `python manage.py reconcile_payments --limit 100`; interval
and timeout budget must fit the deployed scheduler. Pending integrated refunds use
`POST /refunds/{refund_uuid}/reconcile/` and currently need a separate follow-up
process; the payment command does not reconcile refunds. **Done when:** verified
outcomes survive restart and unresolved payments/refunds have an assigned follow-up.

## Authorize phones and get production permission

### 22. Choose one physical pilot phone

- [ ] The engineer checks the phone against the [SDK device requirements](https://developer.sumup.com/terminal-payments/sdks/android-ttp#prerequisites).

Use an NFC-enabled physical Android 11+ phone. Get the provider's supported test-card
and Brazil PIN procedure; online test-card numbers are not physical NFC cards.
For production, use a non-debuggable build and disable USB debugging, active ADB and
Developer Mode. Let provider attestation decide eligibility; never bypass it.
**Done when:** the actual phone and installation procedure are accepted for testing.

### 23. Authorize that device and operator in Rodada

- [ ] The manager verifies the phone's registration and authorizes the specific employee.

List devices at `GET /manage/access/devices/`. With access-management permission and recent reauthentication, mark only the
intended registered device trusted:

```text
PATCH /manage/access/devices/<device_uuid>/
{"trust_state":"TRUSTED","reason":"Approved payment pilot phone"}
```

With manager permission and recent reauthentication, submit:

```text
POST /payments/device-authorizations/
{"connection_id":"<merchant connection>","device_id":"<registered device>",
 "staff_id":"<active Venue staff member>","active":true}
```

This establishes Rodada authorization only. Provider device authorization and the
approved employee token flow from step 11 must also pass. Test disabling the
operator/device and verify that collection stops. **Done when:** one intended
phone/operator can use the correct merchant and a revoked one cannot.

### 24. Run the real SDK sandbox journey

- [ ] Collect a provider-approved test credit payment, then debit and partial amounts.

Verify card/PIN screens stay inside provider components, Rodada waits for backend
confirmation, and UUID/merchant/amount/currency match. Test cancellation, network
loss after card presentation and app termination; reconcile before another charge.
Test logout and a second merchant to prove there is no credential reuse across bars.
**Done when:** real SDK evidence exists; fake-provider tests are listed separately.

### 25. Assemble the provider approval package

- [ ] The engineer and integration contact collect a sanitized review package.

Include architecture/data flow, actual SDK version, package ID, signed-build
fingerprint if requested, supported devices, OAuth/employee model, Pix method,
transaction/refund references, recovery/duplicate tests and support procedure.
Include completed provider forms and commercial agreement details as requested.
Do not mark untested capabilities “passed.” **Done when:** each requested production
criterion has evidence or a provider-accepted limitation.

### 26. Submit for production review

- [ ] Reply on the original integration ticket with the package and request written pilot authorization.

Ask the response to name merchant/client, approved Brazil products, app/signing
identity, allowed devices/operators, transaction limits, fees/payout and any required
homologation. If no formal certificate applies, get written confirmation of the
applicable release criteria. **Done when:** the provider confirms readiness for
these exact products, not just receipt of the package.

### 27. Connect the real merchant and approve the deployment

- [ ] Repeat steps 16–19 in the live environment with the bar owner and live credentials.

Keep staging and production credentials separate. Verify the bar's identity and
payout destination again. Confirm simulator is disabled, the reviewed real Tap
path is deployed, reconciliation monitoring is operating and the external-terminal
fallback remains available. Confirm the support/escalation contact.
**Done when:** provider authorization and Rodada release approval are both recorded.

### 28. Perform one controlled first live payment

- [ ] With the bar owner present, use an amount and payment method approved for the pilot.

Open a real Tab/order, collect once, wait for provider lookup and verify the matching
merchant/reference/amount/currency before the balance changes. Record non-sensitive
provider reference and canonical ledger receipt. Reconcile payout and a provider-
approved refund test. If the result is unknown, stop collection and investigate;
do not retry by presenting the card again. **Done when:** real provider evidence
establishes the transaction and the bar confirms its funds destination.

### 29. Add a second bar only after the pilot

- [ ] Repeat merchant consent, eligibility, configuration, device authorization and a controlled test for the next establishment.

Reuse the approved Rodada application where SumUp allows it, not the first bar's
merchant connection. Test that Bar A cannot access Bar B's transactions, refunds,
devices or credentials. **Done when:** both bars receive their own payments and
merchant disconnect/revocation has been exercised.

## Optional Paytime Pix alternative

### 30. Request Paytime partner/sandbox access

- [ ] Start from [Paytime's official website](https://paytime.com.br/) and request its API integration/commercial channel.

Use the draft below. Request portal access, `integration-key`, sandbox
`authentication-key`/`x-token`, establishment ID, Pix gateway activation, payout/fees
and the homologation contact. Do not assume ordinary merchant login grants partner
API access. Exact portal enrollment screens and partner acceptance need Paytime's
response. **Done when:** access and product scope are confirmed for the bar.

### 31. Configure and test the preserved adapter

- [ ] The engineer follows [Paytime authentication](https://docs-parceiro.paytime.com.br/docs/gerar-token-de-autentica%C3%A7%C3%A3o) and [Rodada's existing activation notes](../../specs/006-payments-tap-on-phone/activation.md).

The documented sandbox origin is `https://api.sandbox.paytime.com.br`; confirm it
with the provisioned account. The partner key comes from Paytime, and portal keys
feed `/v1/auth/login` to obtain a short-lived Bearer. Store all credentials server-side.
When SumUp is primary, preserve Paytime configuration in `RODADA_PAYTIME_PROVIDERS`.
Register the HTTPS Rodada webhook with dedicated Basic credentials and verify it
with authenticated transaction lookup. Test gross amount/reference binding,
restart/duplicate behavior and the documented `STORE`/`ESTABLISHMENT` fee ambiguity.
Do not use Pix-out transfer APIs for collecting a Tab payment.
**Done when:** the existing adapter passes provider-backed Pix tests.

### 32. Submit Paytime's API homologation evidence

- [ ] Follow the [published transaction-API homologation checklist](https://docs-parceiro.paytime.com.br/docs/homologa%C3%A7%C3%A3o).

Download its template, mark the APIs actually used and record tests through Rodada's
real application. Paytime says Postman/Swagger-only evidence does not qualify.
Prepare the requested PDF and use the submission address shown in that page/the
confirmed partner ticket; it was obscured in this research, so no email is guessed.
Redact every secret from header screenshots. Request an approved secure alternative
if the reviewer needs additional evidence. Production keys follow approval; new API
features need their own review. **Done when:** production Pix scope and credentials
are explicitly approved. Paytime Tap would require a separate SDK/activation track;
this plan preserves Paytime as the Pix alternative.

Paytime request draft — not sent:

> Assunto: Rodada / Bar do Aderlan — acesso Sandbox e homologação Pix API
>
> Somos o Rodada, um PDV para bares brasileiros. Queremos manter a API Pix Paytime
> como alternativa de pagamento, com recebimento na conta de cada estabelecimento,
> pagamentos parciais e confirmação pelo backend. Ainda não temos conta, credenciais
> nem transações reais. Como solicitamos acesso ao portal/API parceiro, integration-key
> Sandbox, authentication-key, x-token, estabelecimento e gateway Pix? Confirmem as
> taxas/destino do recebimento, credenciais de webhook, procedimento de testes,
> requisitos de homologação e canal seguro para provisionamento. Nosso responsável
> é <nome/email>. Podemos enviar arquitetura e evidências sem segredos.

## The first action today

Complete steps 1–3, create the developer/sandbox account in step 4, then register the
OAuth application and submit the technical request in steps 7–11. Those actions
unlock provider review while engineering prepares the callback and real SDK work.
Nobody needs to make a live payment or give credentials to a waiter to start.
