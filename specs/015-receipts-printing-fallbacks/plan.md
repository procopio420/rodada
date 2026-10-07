# Plan — Spec 015

## Recommended sequence

1. **Document model/renderer**
   - ReceiptDocument;
   - deterministic templates;
   - customer check/payment receipt/digital receipt.

2. **Print domain**
   - PrinterEndpoint;
   - StationPrinterBinding;
   - PrintJob + attempts;
   - logical production key/idempotency.

3. **Network printer adapter**
   - send/status normalization;
   - retry/uncertain outcome semantics.

4. **Android Bluetooth adapter**
   - only where supported;
   - report result into canonical job.

5. **Production fallback**
   - on-demand first;
   - AUTO_FALLBACK after KDS health signal is trustworthy;
   - explicit REPRINT semantics.

6. **Management/config**
   - printer health;
   - bindings;
   - failure/reprint audit.

7. **Hardening**
   - queue worker leases;
   - failover printer;
   - fault tests.

## Rollout

Start with digital check/receipt and on-demand print. Do not enable automatic production fallback until duplicate-prevention and KDS health tests pass.

## Testing strategy

- golden formatting snapshots;
- idempotent print request;
- worker concurrency;
- ambiguous network timeout;
- reprint watermark/audit;
- KDS failure auto-fallback dedupe;
- printer-down POS continuity.

## Dependencies first

Canonical Order/Payment/pricing snapshots and Spec 014 degraded-state contract.
