# Aderlan — provider acceptance boundaries (12/10/2026)

## Delivered in this slice

- Harden the Paytime adapter to reject any configured base URL other than a credential-free HTTPS origin. This prevents merchant authorization headers from being built for URL userinfo, paths, query fragments, invalid ports or cleartext origins.
- Add isolated provider-origin contract tests and a Paytime simulated-transport ledger regression. An `APPROVED`, `EXPIRED`, or unknown Pix status must not be counted as received money without authenticated `PAID` lookup. **No PSP/sandbox transaction has been executed.**
- Preserve existing rules: no blind retry of ambiguous payment, exact idempotency key, webhook verification, and no fake settlement for Tap or Pix.

## External blockers and graduation criteria

| Contract | Before enabling in a real venue |
| --- | --- |
| Paytime Pix | Merchant sandbox credentials, approved establishment, verified QR purchase and signed/authenticated webhook, timeout, expiry/cancellation semantics, refund contract and reconciliation |
| SumUp Pix | OAuth approval, sandbox merchant eligibility, callback/rotation proof, provider lookup and refund/expiry evidence |
| Tap on Phone | Licensed SDK access, approved application ID, certificates, merchant provisioning, device/BYOD delegation, SDK lifecycle + physical NFC test |
| Deployment | Secret manager only; separate dev/staging/prod stores and webhook URLs; no credentials in Git, APK or logs |

Merchant approval and provider-backed money movement remain **EXTERNAL_BLOCKED**. For the reduced Aderlan pilot, enable only legitimate cash/external-terminal fallback with explicit audit. Do not label that mode as integrated phone payment.
