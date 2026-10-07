# Tasks — Spec 015

## Domain/API
- [ ] ReceiptDocument kinds/source version.
- [ ] Customer check renderer.
- [ ] Payment/digital receipt renderer.
- [ ] PrinterEndpoint abstraction.
- [ ] StationPrinterBinding.
- [ ] PrintJob lifecycle.
- [ ] Initial production logical key.
- [ ] Explicit reprint semantics.
- [ ] Printer health normalization.
- [ ] Production fallback trigger policy.

## Persistence
- [ ] Document snapshot/hash/template version.
- [ ] PrintJob idempotency.
- [ ] Attempt history.
- [ ] Unique initial production key.
- [ ] Reprint linkage.
- [ ] Receipt token hash/expiry.

## Android
- [ ] Print/share customer check/receipt.
- [ ] Bluetooth printer adapter where supported.
- [ ] Printer status/error UI.
- [ ] Explicit reprint flow.

## Staff Web/PWA
- [ ] Digital/print check.
- [ ] Station fallback print/reprint.
- [ ] Printer failure banner.
- [ ] Network printer selection where authorized.

## Guest
- [ ] Authorized digital receipt view.
- [ ] Expired/revoked token handling.
- [ ] No cross-Tab leakage.

## Realtime
- [ ] Print-job status updates.
- [ ] Printer health invalidation.
- [ ] KDS recovery revalidation.

## Management
- [ ] Printer endpoint/binding status.
- [ ] Failed jobs/reprints timeline.
- [ ] Fallback usage metrics.

## Infra/integration
- [ ] Network printer adapter.
- [ ] Print worker queue/lease.
- [ ] Bluetooth integration boundary.
- [ ] Health probing only where reliable.

## Quality/tests
- [ ] Printer failure never rolls back Order/Payment.
- [ ] Retry same job does not create new production instruction.
- [ ] Reprint is visibly marked and audited.
- [ ] CONFIRMATION_PENDING never prints paid receipt.
- [ ] Production ticket only from confirmed Order in P0.
- [ ] Multiple worker concurrency safe.
- [ ] No card secrets in documents/logs.
