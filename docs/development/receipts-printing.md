# Non-fiscal receipts and production printing — Spec 015

## Audit and integration decisions

Audit baseline: origin/main 742faac, branch feat/receipts-printing-fallbacks.
Django modular monolith owns canonical records; Web uses the authenticated Next.js
API gateway. Android uses OperationsRepository/OperationsHttpClient with token refresh,
canonical Tab details, immutable order customization and idempotent payment commands.
Customer checks also reuse `tab_operations.responsibility` to show transferred products,
original quantities and canonical transfer amounts without guessing partial quantities.
No printer operation is added to confirmation/payment transactions or the Android retry queue.

`modules.ledger.services.totals` is the existing payable read model: charges, append-only
adjustments, confirmed money, confirmed refunds and responsibility transfers. Printing takes
its results under the Tab row lock. Spec 011's future discount/service-charge rules remain
owned by billing; printing adds no discount, courtesy or tax calculations. Current ledger
adjustments are item cancellation/courtesy replacement; no unimplemented service charge is
invented or silently shown as zero. Every document contains canonical item/charge/payment
references, a source fingerprint, content hash, timestamp and template version.

Production reads confirmed OrderItem product/name/quantity/price/customization/station
snapshots. Legacy items without station snapshots freeze the existing routing when first
issued. A ticket is per confirmed Order/station, independent of KDS state and client caches.
Cancelled items are excluded on initial issuance; an already-issued ticket remains historical.
Corrections/remakes continue through the existing correction workflow, not by editing paper.

Aderlan's actual printers, operating systems, LAN topology, USB drivers, width, code pages,
cut support and device-status capabilities **have not been verified**. No physical acceptance
is claimed. First rollout is on-demand; automatic heartbeat-driven fallback and Bluetooth
remain disabled pending dependable integration evidence.

## Supported outputs and hardware options

| Output | Delivery | Evidence recorded |
| --- | --- | --- |
| Browser | Native print dialog / Save PDF | OUTPUT_READY, then DELIVERY_UNCERTAIN when dialog requested |
| Portable text | Downloaded UTF-8 receipt | Generated artifact, no paper claim |
| HTML file | Local bridge writes durable file | OUTPUT_READY |
| ESC/POS LAN | Local bridge sends TCP bytes, configurable local host/port | SPOOL_ACCEPTED or uncertain |
| USB through CUPS | Local `lp` raw queue, OS owns USB device/driver | SPOOL_ACCEPTED or uncertain |

58mm uses 32 columns; 80mm uses 48. HTML uses a bounded content-based page height;
verify actual driver paper settings and margins before physical rollout. Margins/fonts may need adjustment after measuring
actual printable width. ASCII transliteration avoids assuming a printer code page; optional
cut is off until tested. Browser HTML escapes content; ESC/POS strips control characters.
No cash drawer, buzzer, fiscal commands or device configuration bytes are emitted.

Technical references: [Epson status command documentation](https://download4.epson.biz/sec_pubs/pos/reference_en/escpos/dle_eot.html)
shows model-specific sensor/status commands; these are not universal paper-completion proof.
[CUPS lp documentation](https://openprinting.github.io/cups/doc/man-lp.html) describes spool
submission. The implementation deliberately records submission separately from physical output.

## Install

1. Install the API environment using `apps/api/pyproject.toml` and apply `python manage.py migrate`.
2. Build/deploy Web with `npm ci` and `npm run build` in apps/web; retain the existing API gateway configuration.
3. In Gerência → Impressoras, create a Browser endpoint first. Pick 58/80mm and bind BAR/KITCHEN as appropriate.
4. Staff/Cashier have `print.customer`. Manager/Owner have both station print capabilities and `print.manage`.
   Grant station operators only `print.production.bar` or `print.production.kitchen` through existing audited
   membership capability overrides; never infer permission from hostname or selected board.
5. Preview a bill from PDV → selected Tab → Ver conta / recibos. Printing creates a stable job.
   Browser output opens the native dialog only through an explicit action. Save PDF is a portable artifact.
6. Closed Tabs remain selectable for final receipt and explicit copy. Confirmed payments can generate
   partial/payment receipts. Pending payment does not generate a paid receipt.
7. Kitchen/Bar → Tickets de produção creates only that station's ticket. KDS remains usable with no endpoint.

## Optional workstation bridge

The bridge is outbound-only, requires Python 3.12+ and imports only the isolated adapter module.
It does not require database credentials or an inbound HTTP port. Use HTTPS outside loopback.
The initial implementation uses a normal authenticated manager session: an optional normal session refresh token rotates access credentials in memory. Session
expiry/revocation stops the bridge visibly. Authenticate again and restart; it does not persist a PIN or silently
create a privileged perpetual token. A dedicated scoped service-device credential is a future
access-module decision, not an invented printing auth bypass.

Copy `tools/print-bridge/config.example.json` to a local protected file outside Git. Replace the
endpoint UUID with the configured endpoint and set the same opaque connection reference.

File output example:

```json
{"endpoints":{"ENDPOINT_UUID":{"adapter":"FILE","connection_ref":"cashier-local","directory":"/var/lib/rodada/receipts"}}}
```

Network example after hardware verification:

```json
{"endpoints":{"ENDPOINT_UUID":{"adapter":"NETWORK","connection_ref":"bar-lan","host":"192.168.1.50","port":9100}}}
```

USB/CUPS example after verifying raw ESC/POS support:

```json
{"endpoints":{"ENDPOINT_UUID":{"adapter":"SPOOL","connection_ref":"kitchen-usb","queue":"aderlan-kitchen"}}}
```

Windows USB should use Browser printing with the installed vendor driver in P0. Native Windows
spooler and Android Bluetooth adapters are not claimed. Do not configure a CUPS queue as
ESC/POS until the printer and queue support it.

Supply `RODADA_PRINT_API_URL`, `RODADA_PRINT_ACCESS_TOKEN` and optionally `RODADA_PRINT_REFRESH_TOKEN` through a protected service
environment, never command-line arguments/logs. Start from repository root:

```bash
python tools/print-bridge/bridge.py --config /etc/rodada/printing.json
```

`--once` polls once, useful for deterministic file-output validation. Restrict output directory
permissions; receipt files contain customer consumption/payment information. The bridge
claims only locally listed endpoints and checks adapter/reference agreement before submission.
Management displays its last-poll availability separately from printer health.
Schedule `python manage.py recover_print_jobs` every minute, including when no bridge is
running. Management and bridge polling also recover expired leases. Do not run parallel
physical adapters outside this job protocol.

## Failure/recovery runbook

| Condition | Result and operator action |
| --- | --- |
| Printer disconnected before bytes | Same job retries with 10/20/40/80 seconds; fifth failed attempt is final |
| Bridge offline / internet outage | Server queue persists; POS and KDS continue if their API is healthy |
| Duplicate request | Same initial job; production initial identity also spans printers |
| Restart before claim | Queued job remains available |
| Restart or loss after claim | After 60 seconds: DELIVERY_UNCERTAIN; inspect spool queue and paper |
| Reconnect after definitive failure | Due queued/retryable job may be claimed normally |
| Partial printing / timeout during write | No automatic resend; inspect and explicitly reprint a marked copy |
| Spooler error after launch | Uncertain, because partial acceptance cannot be excluded |
| Spooler accepts data | SPOOL_ACCEPTED, not PRINTED |
| Browser dialog cancelled | DELIVERY_UNCERTAIN; cancel job or explicitly request another copy |
| Late result after recovery | Fenced result rejected; no job resurrection |
| Original endpoint unavailable | Explicit linked reprint can select another bound endpoint; no new initial production job |
| Reprint after closure | Historical immutable receipt, marked REIMPRESSÃO / CÓPIA, audited actor/reason |

Only “Confirmar que vi o papel” records PRINTED, with operator audit. It is operator evidence,
not certification from a test adapter. Cancel does not erase attempt history or recall paper.
After API outage, never create new canonical tickets from an unconfirmed local cart. Manual
paper contingency stays outside canonical printing until the normal order recovery workflow.
A station's missing print permission/configuration/error never disables its KDS mutations.

## Read-only digital receipts

Guest “Ver minha conta” validates the existing GuestSession and returns only its Tab's canonical
check or closed receipt. Client-supplied Tab/kind are ignored. Revocation/occupancy epoch and
expiry remain owned by Guest Access. Staff can create a document-scoped random receipt link,
valid 24 hours, and revoke it. Only SHA-256 token hashes are persisted; tokens grant no mutation
or production access. Public responses use no-store. Treat link possession as read access,
avoid logging full token URLs at the edge, and distribute only intentionally. No email/WhatsApp
connector is installed or invoked.

## Fiscal boundary

All outputs are clearly marked DOCUMENTO NÃO FISCAL. No NFC-e, CF-e, NF-e or fiscal-provider
certification is implemented. Fiscal regime, provider, mandatory fields and issuance workflow
require separate confirmation from Aderlan and the accountant before integration. Non-fiscal
payments/receipts are not presented as fiscal issuance.

## Automated validation

`tests/test_printing.py` covers source versions, pending-payment refusal, isolated adapters,
station permissions, audit, crash fencing, browser ambiguity, scoped receipt tokens and an
actual API Order → production → confirmed payment → Tab close → final receipt scenario.
`tests/test_printing_snapshots.py` freezes text/HTML/ESC/POS output for every document kind,
width and original/copy. PostgreSQL transaction tests cover simultaneous generation, duplicate
requests, cross-endpoint initial dedupe, SKIP LOCKED workers and duplicate result/reprint commands.
Web integration covers cashier/production/configuration/share/revoke and generates a real PDF
artifact through Chromium without physical printing. Visual checks verify layout/accessibility.

Run the isolated PostgreSQL gate:

```bash
docker run --name rodada-printing-test -e POSTGRES_USER=rodada -e POSTGRES_PASSWORD=rodada-test -e POSTGRES_DB=rodada_printing_test -p 127.0.0.1:55451:5432 -d postgres:17-alpine
cd apps/api
python -m pytest tests/test_printing.py tests/test_printing_concurrency.py tests/test_printing_snapshots.py --ds=rodada_api.settings_printing_postgres
```

Run `python -m pytest` for API regressions; from apps/web run `npm run typecheck`, `npm run build`,
`npm run test:visual` and `npm run test:integration`. Set `RODADA_TEST_PYTHON` to the API Python
executable. See the acceptance record for exact observed results and limitations.
