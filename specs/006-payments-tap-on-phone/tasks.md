# Tasks — Spec 006

## Domain/API

- [x] expand Payment methods/statuses
- [ ] PaymentAttempt model
- [x] idempotency key uniqueness/semantics
- [ ] ProviderEvent inbox
- [x] Refund model
- [x] balance/exposure projection from ledger
- [x] prevent Table/TableOccupancy coupling
- [ ] provider-neutral PaymentProvider port
- [ ] provider capabilities
- [x] normalized payment errors
- [x] create payment command
- [ ] confirm payment transition rules
- [ ] confirmation_pending reconciliation
- [ ] cancel rules
- [x] refund total
- [x] refund partial
- [x] audit financial mutations
- [x] permissions/RBAC
- [ ] webhook signature validation per adapter
- [ ] webhook idempotency
- [ ] scheduled/manual reconciliation
- [ ] realtime financial events

## Rodada Atendimento — Android

- [x] app/surface Android nativo em Kotlin + Jetpack Compose
- [ ] contratos/API compartilhados sem acoplar domínio ao Android
- [x] **Pagar** action on Tab
- [x] full balance option
- [x] custom/partial value
- [x] method picker
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
- [x] External terminal fallback
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
- [x] no PAN/CVV persistence
- [x] redact provider secrets/sensitive fields from logs
- [x] double tap cannot double-charge
- [x] frontend retry cannot double-charge
- [ ] webhook duplicate cannot double-apply
- [ ] provider timeout cannot auto-retry ambiguous charge
- [x] cash/manual payment records actor
- [x] external terminal is visually/auditably distinct
- [ ] closing Tab never frees TableOccupancy
- [x] tests for partial payment
- [x] tests for refunds
- [ ] tests for reconciliation
- [ ] metrics: time-to-pay, approval/failure, method/provider, confirmation_pending
