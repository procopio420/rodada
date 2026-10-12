# Aderlan — printing, fiscal, and incident-readiness checklist

## Hardened print boundary

The local outbound print bridge validates its static endpoint map before claiming any job. NETWORK endpoints must target private on-premises IP ranges or explicit `.local`/`.lan` names with integer TCP port 1–65535. SPOOL queues require safe simple names; FILE endpoints require explicit directories. Malformed configuration blocks the claim, so no bytes or tokens are directed at a public destination by accident. Existing bridge resend rule remains: unknown post-send delivery is `DELIVERY_UNCERTAIN`, **never automatic duplicate output**.

These checks validate configuration, NOT paper acceptance or status polling on the actual Aderlan printer.

## Before onsite sign-off

- [ ] Identify printer model, connection (USB/CUPS/LAN/Bluetooth), driver, thermal paper width 58/80 mm, cutting/encoding capabilities, and persistent LAN address.
- [ ] Print kitchen, bar and final customer receipts. Compare quantities, variants, notes, currency and paper formatting with canonical Tab/Order/Payment data.
- [ ] Unplug/disconnect printer *after* output begins; confirm uncertain delivery does not silently reprint and manual operator review/reprint is audited.
- [ ] Disconnect KDS; classify station health from authenticated queue-read heartbeats, not SSE/browser presence. Auto fallback stays disabled until threshold and producer are certified.
- [ ] Ask bar operator and accountant to confirm fiscal regime, mandatory document type, issuing integration and fiscal contingency rules. A common digital/thermal receipt **is not by itself a fiscal document**.
- [ ] Test permission revocation, cross-venue isolation, restore, discrepancy workflow and rollback to incumbent VR System with operator supervision.
- [ ] Record responsible person, venue/device, captured evidence/time, GO/NO-GO decision for each gate.

**External gates:** physical printer receipt, fiscal requirements, KDS failure drill, backup restoration against a disposable clone and busy-shift on actual network. This change is intentionally not an assertion that these happened.
