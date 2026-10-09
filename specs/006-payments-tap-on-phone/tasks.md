# Tasks — Spec 006

## Domain/API

- [x] expand Payment methods/statuses
- [x] PaymentAttempt model
- [x] idempotency key uniqueness/semantics
- [x] ProviderEvent inbox
- [x] Refund model
- [x] balance/exposure projection from ledger
- [x] prevent Table/TableOccupancy coupling
- [x] provider-neutral PaymentProvider port
- [x] provider capabilities
- [x] normalized payment errors
- [x] create payment command
- [x] confirm payment transition rules
- [x] confirmation_pending reconciliation
- [ ] cancel rules
- [x] refund total
- [x] refund partial
- [x] audit financial mutations
- [x] permissions/RBAC
- [x] webhook signature validation per adapter
- [x] webhook idempotency
- [x] manual reconciliation service
- [ ] realtime financial events

## Rodada Atendimento — Android

- [x] app/surface Android nativo em Kotlin + Jetpack Compose
- [x] contratos/API compartilhados sem acoplar domínio ao Android
- [x] **Pagar** action on Tab
- [x] full balance option
- [x] custom/partial value
- [x] method picker
- [x] Tap on Phone capability detection
- [x] provider-neutral `TapToPayProvider`
- [ ] `PaytimeTapProvider` como primeiro adapter
- [ ] integração direta com Paytime Tap on Phone SDK
- [ ] garantir happy path sem abrir aplicativo externo
- [ ] lifecycle/cancelamento do SDK integrado ao lifecycle Android
- [x] processing UI
- [x] confirmation_pending UI blocking blind retry
- [x] confirmed UI
- [x] failed UI with retry/alternate method
- [ ] Cash received + change calculation
- [x] External terminal fallback
- [x] Payment history on Tab
- [ ] Refund action for authorized roles

## Pix

- [x] create Pix charge
- [x] QR + copy/paste payload
- [x] pending state
- [x] provider confirmation
- [ ] realtime Tab update
- [ ] expiry/failure behavior

## Guest

- [ ] **Minha comanda → Pagar**
- [ ] reuse same Tab/Payment API
- [ ] enforce GuestSession authorization
- [ ] Pix payment
- [ ] card online when provider supports
- [ ] success updates Staff in realtime

## UX advanced

- [ ] select items to compose payment amount
- [ ] compose by participant when identity allocation exists
- [ ] optional tip model/UI
- [ ] keep composition metadata separate from ledger truth

## Security/quality

- [x] backend owns amount/currency
- [x] no PAN/CVV persistence
- [x] redact provider secrets/sensitive fields from logs
- [x] double tap cannot double-charge
- [x] frontend retry cannot double-charge
- [x] webhook duplicate cannot double-apply
- [x] provider timeout cannot auto-retry ambiguous charge
- [x] cash/manual payment records actor
- [x] external terminal is visually/auditably distinct
- [ ] closing Tab never frees TableOccupancy
- [x] tests for partial payment
- [x] tests for refunds
- [x] tests for reconciliation
- [ ] metrics: time-to-pay, approval/failure, method/provider, confirmation_pending

Live REST/Android slice and external activation gates: see `activation.md`.
SDK integration, Pix expiry/cancel/refund and realtime remain unchecked.


## SumUp candidate — public contracts and explicit simulation

- [x] SumUp Checkout/APM adapter with exact minor-unit conversion and merchant binding.
- [x] Provider-authoritative Pix EXPIRED transition (contract tests; no live claim).
- [x] Encrypted tenant OAuth connection, refresh, local disconnect and device authorization.
- [x] Refund request reservation and authoritative new-event reconciliation tests.
- [x] Explicit development-only durable fake provider; no payable fake QR.
- [x] Android simulated credit/debit flow and backend confirmation, labeled simulation.
- [x] Isolated SDK boundary and opt-in private dependency configuration.
- [x] PostgreSQL concurrent intent, duplicate webhook and refund-reservation checks.
- [ ] Private SDK bridge compilation and real device lifecycle verification.
- [ ] Employee/BYOD token delegation approved by SumUp.
- [ ] SumUp sandbox Pix/card/refund verification and production homologation.
- [ ] Shared manager financial realtime delivery.

The earlier provider-specific live tasks are not evidence of an activated merchant.
See `docs/payments/sumup-onboarding.md` and the validation report for exact gates.
