# Issue #106 — E2E-05 cross-client status

Historical slice record. For current exact-SHA execution and remaining gates, see
[the resumption matrix](issue-106-resumption-matrix.md). Historical failures and
NOT_RUN statements below describe their original snapshot.

## Implemented in draft PR #194

- Playwright exercises **real Guest QR, Atendimento Web and Bar UIs** against the same disposable Django/PostgreSQL. A product changes to UNAVAILABLE through Bar **after the confirmation click and before Django receives the POST**. Original HTTP commands are forwarded; no backend success or Order is mocked.
- Both Guest and Staff confirmations must return `409 / PRODUCTS_NOT_CONFIRMABLE`; drafts remain visible, the rejected Tabs have no new Order or exposure.
- `scripts/verify-issue106-unavailable.py` independently checks two receipts against the same exact SHA, Venue and PostgreSQL instance, then verifies the products' operational state and zero Order/Item/Charge/Payment for each rejected Tab.
- The local shared runner and the Android workflow require this SQL verification and retain browser/SQL artifacts.

**Status: CODED / NOT YET CI-VERIFIED.** Inspect exact-SHA browser/SQL receipts and failing jobs before declaring these two subcases PASS. Android stale-cart conflict, unchanged prior confirmed orders and the complete E2E-01..14 release matrix remain open. Do not close #106 or declare physical/fiscal homologation from this slice.
