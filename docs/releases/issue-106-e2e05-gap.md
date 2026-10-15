# Issue #106 — E2E-05 cross-client status

## Implemented in draft PR #194

- Playwright uses the real Guest QR UI, a logged-in Bar UI and the existing shared disposable Django/PostgreSQL fixture. The product is marked UNAVAILABLE **after the Guest clicks Send but before the original HTTP command reaches Django**. No order response is mocked.
- The server must reject the Guest command with `409 / PRODUCTS_NOT_CONFIRMABLE`, leave the draft visible, and create no Order or exposure.
- `scripts/verify-issue106-unavailable.py` independently verifies the same SHA, Venue, PostgreSQL instance, product availability and zero Order/Item/Charge/Payment on that Tab. Both the local runner and the Android workflow invoke the verifier and preserve its receipts.

**Status: CODED / NOT YET CI-VERIFIED.** The new test must run successfully at the exact PR SHA, and its browser/SQL receipts must be inspected before any PASS is recorded. Staff and Android stale-cart paths, an already-confirmed order remaining unchanged, and the full E2E-01..14 release matrix remain open. Do not close issue #106 or declare physical-payment/fiscal homologation from this slice.
