# Paytime live activation and verified scope

The REST adapter creates Pix transactions, retains EMV/QR evidence, validates gross
amount/method/establishment/reference, and applies authenticated lookup results.
POSTs are never retried. Pending intents survive restart in PostgreSQL and Android's
existing encrypted intent store. Configure `RODADA_PAYMENT_PROVIDERS` as a JSON
object keyed by Venue UUID, with `base_url`, `integration_key`, `x_token`,
`authentication_key`, `establishment_id`, `webhook_user`, `webhook_password`.
Credentials must be injected by the deployment secret manager. `bearer_token` is
an optional short-lived alternative; production should use `authentication_key`.
Register the webhook with matching Basic credentials at
`/payments/webhooks/paytime/{venue_uuid}/`, over HTTPS. Schedule
`python manage.py reconcile_payments --limit 100` periodically.

Routes: GET `/payments/capabilities/`; POST
`/tabs/{tab_uuid}/payments/integrated/` with integer amount_cents, method PIX and
idempotency_key; GET/POST `/payments/{payment_uuid}/integrated/` for durable status
and explicit reconciliation. Staff permission remains `payment.collect`.

Unknown references are recovered through documented transaction listing with exact
reference matching. Missing/incomplete matches remain confirmation pending. A
local clock does not prove expiry. Provider expiry semantics and a Pix cancellation
contract require Paytime confirmation; there is no local cancellation shortcut.
The published reversal API is credit-only and does not establish partial/Pix
refunds. Manual refunds remain functional; integrated refunds reject until genuine
provider support is available. Existing legacy manual Pix is retained for venues
without integrated configuration; configured venues require provider confirmation.

## External gates

- Obtain REST credentials and activate the merchant's Pix gateway.
- Verify the documentation's inconsistent STORE/ESTABLISHMENT fee-owner wording
  in sandbox; ensure gross amount equals the requested amount.
- Exercise real QR payment, PAID confirmation, failure and cancellation/expiration
  behavior; no live transaction has been executed in this environment.
- Obtain private Tap Maven coordinates/access, license, applicationId registration,
  merchant activation and signing certificate registration.
- Implement the licensed SDK boundary using actual classes and attested device
  status; configure once in Application.onCreate and homologate physical devices.
- Android 11+ physical NFC hardware is required; SDK debug transactions may be
  simulated. SDK callbacks must be reconciled by backend before confirmed UI.
- Tap remains unavailable in the shipping app until these gates are satisfied.
- Guest payment and realtime financial propagation remain outside this slice.

## Primary provider contracts researched

- https://docs-parceiro.paytime.com.br/docs/criar-transa%C3%A7%C3%A3o-pix-qr-code
- https://docs-parceiro.paytime.com.br/docs/exibir-transa%C3%A7%C3%A3o
- https://docs-parceiro.paytime.com.br/docs/listar-transa%C3%A7%C3%A3oes
- https://docs-parceiro.paytime.com.br/docs/gerar-qrcode-pix-transacional
- https://docs-parceiro.paytime.com.br/docs/registrar-novo-evento-webhook
- https://docs-parceiro.paytime.com.br/docs/gerar-token-de-autentica%C3%A7%C3%A3o
- https://docs-parceiro.paytime.com.br/docs/estorno-de-transa%C3%A7%C3%A3o
- https://docs-parceiro.paytime.com.br/docs/tap-on-phone-desenvolvimento-implementacao
