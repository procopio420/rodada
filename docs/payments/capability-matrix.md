# Payment capability matrix

All provider columns are public-contract implementation, not live verification.

| Capability | SumUp Pix | SumUp embedded Tap | Paytime Pix | Development simulator |
| --- | --- | --- | --- | --- |
| Creation | REST adapter | Durable intent; SDK blocked | Preserved REST adapter | Durable fake |
| Partial payment | Ledger supported | Ledger supported | Ledger supported | Tested |
| Dynamic QR/copy code | APM artifacts | N/A | Preserved EMV/QR | Non-payable simulation label |
| Confirmation | Checkout + transaction lookup | Merchant lookup by client ID | Authenticated lookup | Deterministic DB outcome |
| Expiration | valid_until/EXPIRED contract | No invented timer | Unverified | Scripted |
| Cancellation | Deactivate unprocessed only; no UI promise | SDK event requires reconciliation | Unverified | Scripted |
| Partial refund | Request + matching new REFUND evidence | Same API; activation blocked | Unverified; manual confirmation rejected | Reservation/evidence tests |
| Webhooks | Direct inbox rejected; polling implemented | Polling | Basic + authoritative lookup | Not public |
| Multi-merchant | OAuth encrypted connection | BYOD delegation blocked | Venue settings | Venue-scoped |
| Private SDK build | N/A | Opt-in dependency; real bridge not compiled | N/A | Standard build green |
| Real transaction evidence | NONE | NONE | NONE | No real money |

## Verification checklist

- [x] Integer ledger and exact-decimal provider amount conversion.
- [x] Provider ownership checked against Venue/merchant identity.
- [x] Creation intent persisted before external work; no ambiguous POST retry.
- [x] Provider selection preserves Paytime and rejects implicit production simulator.
- [x] Simulated Android lifecycle and backend-confirmed UI.
- [x] OAuth state/credential encryption/tenant-binding tests.
- [x] Refund reservation before external I/O and audit-preserving reversal.
- [ ] SumUp merchant/payment scopes approved.
- [ ] Real Pix QR scan → authenticated confirmation and refund tested.
- [ ] Private embedded SDK resolution and bridge compilation.
- [ ] Approved employee/BYOD OAuth access and device provisioning.
- [ ] Root/debug/attestation failure tested on provider SDK.
- [ ] Real card/PIN test on physical phone.
- [ ] Provider-specific fees/settlement and Pix cancellation confirmed.
- [ ] Production homologation and rollout approval.
- [ ] Financial realtime publisher integration when shared outbox is available.

See validation-report.md for automated results; checkboxes do not assert sandbox/live verification.

The step-by-step human and engineering activation sequence is in
[provider-activation-steps.md](provider-activation-steps.md).
