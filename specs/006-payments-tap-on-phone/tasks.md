# Tasks — Spec 006

## Domain/API

- [ ] expand Payment methods/statuses
- [ ] PaymentAttempt model
- [ ] idempotency key uniqueness/semantics
- [ ] ProviderEvent inbox
- [ ] Refund model
- [ ] balance/exposure projection from ledger
- [ ] prevent Table/TableOccupancy coupling
- [ ] provider-neutral PaymentProvider port
- [ ] provider capabilities
- [ ] normalized payment errors
- [ ] create payment command
- [ ] confirm payment transition rules
- [ ] confirmation_pending reconciliation
- [ ] cancel rules
- [ ] refund total
- [ ] refund partial
- [ ] audit financial mutations
- [ ] permissions/RBAC
- [ ] webhook signature validation per adapter
- [ ] webhook idempotency
- [ ] scheduled/manual reconciliation
- [ ] realtime financial events

## Rodada Atendimento — Android

- [ ] app/surface Android nativo em Kotlin + Jetpack Compose
- [ ] contratos/API compartilhados sem acoplar domínio ao Android
- [ ] **Pagar** action on Tab
- [ ] full balance option
- [ ] custom/partial value
- [ ] method picker
- [ ] Tap on Phone capability detection
- [ ] provider-neutral `TapToPayProvider`
- [ ] `PaytimeTapProvider` como primeiro adapter
- [ ] integração direta com Paytime Tap on Phone SDK
- [ ] garantir happy path sem abrir aplicativo externo
- [ ] lifecycle/cancelamento do SDK integrado ao lifecycle Android
- [ ] processing UI
- [ ] confirmation_pending UI blocking blind retry
- [ ] confirmed UI
- [ ] failed UI with retry/alternate method
- [ ] Cash received + change calculation
- [ ] External terminal fallback
- [ ] Payment history on Tab
- [ ] Refund action for authorized roles

## Pix

- [ ] create Pix charge
- [ ] QR + copy/paste payload
- [ ] pending state
- [ ] provider confirmation
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

- [ ] backend owns amount/currency
- [ ] no PAN/CVV persistence
- [ ] redact provider secrets/sensitive fields from logs
- [ ] double tap cannot double-charge
- [ ] frontend retry cannot double-charge
- [ ] webhook duplicate cannot double-apply
- [ ] provider timeout cannot auto-retry ambiguous charge
- [ ] cash/manual payment records actor
- [ ] external terminal is visually/auditably distinct
- [ ] closing Tab never frees TableOccupancy
- [ ] tests for partial payment
- [ ] tests for refunds
- [ ] tests for reconciliation
- [ ] metrics: time-to-pay, approval/failure, method/provider, confirmation_pending
