# Bar do Aderlan — final pilot readiness

Audit opened 2026-10-12. Initial requested main: `4228fb4efc9daba2cce5285c99cea9aaed450f92`.
Fetched main: `d07ca67c1fde04b036b4b9cdecc43f212db82a14`; additional tenant-routing specification is not a shipped routing implementation.

Statuses: PASS = current reproducible evidence within stated scope; PARTIAL = implemented with remaining validation; MISSING = absent required engineering evidence; EXTERNAL_BLOCKED = access, owner/accountant or hardware dependency. Previous passing reports are historical only.

## Phase 0 audit

Reviewed AGENTS, product/architecture/domain/design contracts, Spec015, its acceptance and ADR0013; assigned relevant payment, connectivity, release and operational specifications to their owners. No `.codegraph` exists in this checkout.
PR83 added real emulator uplink interruption and separate physical-Wi-Fi harness; PR84 seven-page gate and Docker smoke; PR85 full-shift/64-Tab/restart workflow; PR86 Paytime origin/non-settlement hardening; PR87 LAN bridge preflight/fiscal checklist. Actual file changes and merge commits verified through GitHub.
Open PR89 is operational UX/DEV work and is outside this release until independently validated. Existing main Android real POST run 38259788434 failed uplink restoration; historical API/Web passes do not certify this release. Railway cached credential returns Unauthorized; actual remote deployment SHA is unavailable.

| Requirement | Status at audit | Required fresh evidence / remaining gate |
| --- | --- | --- |
| Pinned isolated staging deployment | EXTERNAL_BLOCKED | Railway auth and isolated target; local image rehearsal underway |
| Public seven surfaces HTTPS | PASS | Fresh read-only smoke by infra; does not prove deployed SHA/auth/QR |
| Migrations, Django, PostgreSQL | PARTIAL | Full current-SHA checks underway |
| Next.js, SSE, dispatcher, authentication | PARTIAL | Container runtime and integrated CI required |
| Test order and customer QR | PARTIAL | Disposable deployed API shift underway; no real guest data |
| Full shift/64 Tabs/restart reconciliation | PARTIAL | Fresh isolated suite underway |
| Native Android disconnect/durable exactly-once | PARTIAL | Main CI recovery failure investigated; native rerun required |
| Physical venue Wi-Fi recovery | EXTERNAL_BLOCKED | Handset and actual venue network drill |
| Staff/guest/cross-Venue/revocation | PARTIAL | Current PostgreSQL regression gates required |
| Cash/manual external-terminal payments | PARTIAL | Ledger and close gates plus supervised onsite proof |
| Live Pix/SumUp/Paytime settlement | EXTERNAL_BLOCKED | Merchant credentials, approval and sandbox/device transactions |
| Tap on Phone | EXTERNAL_BLOCKED | Private SDK/device/merchant approval; feature remains disabled |
| Pending/duplicate/refund financial safety | PARTIAL | Provider audit and current regressions underway |
| Immutable documents/print jobs, FILE/LAN/CUPS | PARTIAL | PostgreSQL and adapter boundary tests underway |
| Physical output and paper failure | EXTERNAL_BLOCKED | Actual printers, queues, paper/encoding acceptance |
| Certified automatic KDS print fallback | MISSING | Detector producer/runtime certification incomplete; disabled |
| Backup/restore/rollback | PARTIAL | Disposable restore drill and operator runbook required |
| Fiscal issuance and contingency | EXTERNAL_BLOCKED | Owner/accountant decision; non-fiscal receipts cannot replace fiscal system |
| Assisted onsite acceptance | EXTERNAL_BLOCKED | Operator/device/hardware/network signoff |

Final result will be updated after integration. No production or VR System replacement authorization is inferred.
