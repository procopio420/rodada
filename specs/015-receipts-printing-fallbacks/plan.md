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


## Executed P0

- Audited Ordering, Ledger totals, Tab responsibility, customization, Access, Web gateway,
  cashier/production surfaces and Android operational flows on origin/main 742faac.
- Added derived immutable documents, station binding, durable jobs, fenced attempts and
  PostgreSQL immutability trigger without touching financial/payment-provider rules.
- Added HTML/text/ESC-POS renderers and conservative LAN/CUPS/file adapters behind an
  outbound authenticated local bridge. Normal session refresh rotates credentials in memory.
- Connected PDV, Kitchen/Bar, Guest and printer management using existing components,
  capability checks and bounded status polling.
- Added golden artifacts, PostgreSQL concurrency/fault tests, API end-to-end acceptance,
  real Web integration/PDF evidence and printing layout/accessibility checks.
- Installation/runbook: docs/development/receipts-printing.md; hardware verification remains
  pending in docs/development/printing-hardware-checklist.md.

Automatic fallback is deferred until a trustworthy station heartbeat exists. Android
Bluetooth and Windows native spool APIs are deferred until actual OS/device models and
vendor SDK compatibility are confirmed. These are not enabled by configuration in P0.
