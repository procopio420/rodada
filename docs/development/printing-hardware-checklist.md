# Aderlan printing hardware verification — not yet performed

Record operator, date, workstation OS, printer manufacturer/model/serial, firmware,
interface, driver/SDK, paper width and test evidence for each device. Obtain confirmation
from Aderlan before choosing adapters or replacing equipment.

- [ ] Inventory existing cashier, Kitchen and Bar computers and their operating systems.
- [ ] Identify the actual printer models and connection types; photograph labels and ports.
- [ ] Confirm vendor documentation for ESC/POS command compatibility and raw printing.
- [ ] Measure actual printable width on 58/80mm paper; verify 32/48-column legibility.
- [ ] Print Portuguese names/accents, variants, additions, removals, quantities and long notes.
- [ ] Confirm the chosen ASCII/code-page strategy; approve any loss of unsupported characters.
- [ ] Verify cut capability before enabling the opt-in cut command.
- [ ] Check receipt margins, price/payment values, timestamps, references and non-fiscal label.
- [ ] Check Kitchen and Bar station separation and prominent REIMPRESSÃO markers.
- [ ] Confirm LAN addresses/reservations/firewall and whether the API server can reach the LAN.
- [ ] For USB, install/verify the vendor driver and OS queue; test browser printing first.
- [ ] For CUPS, verify raw ESC/POS queue support and operator access without root privileges.
- [ ] Verify paper-out/cover-open/status behavior only using commands supported by that model.
- [ ] Document which status is genuinely observed versus UNKNOWN/inferred connection condition.
- [ ] Disconnect before send: one durable job, bounded safe retry, digital queue still operational.
- [ ] Interrupt during printing: DELIVERY_UNCERTAIN, no automatic second ticket.
- [ ] Restart the bridge before/after submission; inspect expired lease and late-result fencing.
- [ ] Remove paper mid-ticket; recover using an explicit marked copy after spool inspection.
- [ ] Restore connectivity/printer; ensure retry uses the existing identity and queued jobs persist.
- [ ] Submit duplicate API commands and run two bridge processes; verify one initial ticket.
- [ ] Try a second bound printer; verify initial dedupe and explicit-copy failover.
- [ ] Cancel browser dialog; verify that Rodada does not claim PRINTED.
- [ ] Verify browser Save PDF and print-driver margins for both widths.
- [ ] Reprint a closed Tab; validate immutable original, actor/reason/time and no new ledger effects.
- [ ] Complete a full service rehearsal: confirm Order, KDS prepare, partial payment, final payment,
      Tab close and final receipt with every printer unavailable.
- [ ] Review local token/output file permissions and retention with the venue operator.
- [ ] Decide future automatic fallback only after reliable KDS heartbeat/threshold tests.
- [ ] Confirm fiscal regime/provider/issuance requirements separately with Aderlan and accountant.

Acceptance record: no physical printer tested in this implementation. Automated TCP mocks,
spool mocks, HTML files and generated PDF are software evidence only.
