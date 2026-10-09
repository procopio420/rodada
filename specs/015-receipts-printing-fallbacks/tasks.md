# Tasks — Spec 015

## Delivered P0
- [x] Canonical/versioned immutable customer check, partial/payment and closed-Tab snapshots.
- [x] Confirmed station production snapshots with variants/modifiers/removals/notes.
- [x] Stable source fingerprint, content hash, template version and source record references.
- [x] Canonical Ledger totals and Tab responsibility read models; no independent pricing rules.
- [x] PrinterEndpoint, StationPrinterBinding, durable PrintJob and PrintAttempt history.
- [x] Unique initial production identity across endpoints; idempotent requests/reprint commands.
- [x] PostgreSQL SKIP LOCKED claim/lease/fencing, bounded retry/backoff and crash recovery.
- [x] Separate generated output, spool acceptance, uncertain delivery and operator paper confirmation.
- [x] Explicit copy/failover with original link, watermark, actor/time/reason audit.
- [x] Printer/bridge advisory health and paginated management failure review.
- [x] HTML, portable text, browser Save PDF and sanitized ESC/POS at 58/80mm.
- [x] Optional outbound workstation bridge with fixed local LAN/CUPS/file adapters.
- [x] Normal authentication/refresh/revocation; no printer secrets in business documents.
- [x] PDV bill/receipt/print/copy, historical closed Tabs, Kitchen/Bar on-demand tickets.
- [x] GuestSession-scoped digital bill and hashed, expiring/revocable read-only receipt links.
- [x] Capability enforcement for customer/station/configuration and cross-Venue isolation.
- [x] PostgreSQL receipt immutability trigger and ORM mutation guards.
- [x] Golden document/output fixtures, fault tests, PostgreSQL concurrency and API E2E.
- [x] Real Web Order→ticket→partial→closed receipt/share/revoke/PDF scenario.
- [x] Printing layout/accessibility checks and existing Web visual regression gate.
- [x] Installation/configuration/runbook, ADR and hardware verification checklist.

## Rollout decisions deliberately not enabled
- [ ] Real Aderlan printer model/OS/LAN/driver/code-page/cut/status verification and paper acceptance.
- [ ] AUTO_FALLBACK after trustworthy KDS heartbeat/read-model health and threshold contract.
- [ ] Android Bluetooth/native print adapter after actual paired-device/SDK verification.
- [ ] Native Windows USB spool adapter; use browser/vendor-driver fallback in P0.
- [ ] Provider-mandated safe receipt metadata after provider contract review.
- [ ] Fiscal regime/provider/issuance confirmation by Aderlan and accountant (separate integration).

Status polling is implemented; dedicated print realtime events and aggregated fallback metrics
are future projection work. Printer availability does not enter financial/KDS transactions.

## Fixtures em Windows

Comparação golden lê os arquivos existentes como UTF-8 explícito, preservando bytes e igualdade literal de texto/HTML/ESC-POS. Não substituir fixtures nem aplicar normalização que esconda diferenças. O encoding padrão da máquina não define o contrato do documento.
