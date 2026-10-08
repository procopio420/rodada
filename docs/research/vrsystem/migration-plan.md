# Safe replacement and migration — Bar do Aderlan
**Strategy:** VR System remains contractual operational fallback until parity and go/no-go are **verified in the real bar**. Research only; no production changes. Proprietary database queries or GUI automation require explicit owner/vendor authorization; prefer vendor-facilitated exports.

## 0. Prerequisites and responsibilities
| Owner | Deliverable |
| --- | --- |
| Aderlan | Authorize discovery, inventory hardware/modules, identify staff champion; share redacted bill and export rights |
| Caixa lead | Confirm daily operational rules, tender and closing reports, open Tab list; join rehearsals |
| Kitchen/bar leads | Validate routing, modifiers, written tickets/KDS and backup |
| Accountant/fiscal specialist | In writing: existing NF-e/NFC-e/CF-e process and obligations, target issuer, authorization/certification/integration, contingency and retention. **No legal exemption inferred** |
| Rodada engineering | Version-controlled mapping/dry-run, data backups, test matrix, adapter readiness, deploy/rollback automation |
| VR vendor/authorized operator | Supported catalog/price/table export and termination/licensing terms; no unauthorized DB inspection |

## 1. Data plan
| Source | Target | Method | Confidence / limitation |
| --- | --- | --- | --- |
| Product names/codes/base prices | Rodada Product + `legacy_product_code` mapping in migration manifest | Request vendor-approved CSV export; S10 documents SQL-assisted export and CSV import formats for E-Trade, **not** general one-click export | Export workflow UNKNOWN until authorized |
| Categories | Proposed Rodada category mapping (current Product has no category) | Export categories with product lists; if missing, manually curate; do not assume implementation | Product-category model MISSING |
| Variants/addons/combos | Spec 010 ProductVariant/ModifierGroup; combo decision | Manually reconstruct prioritized top menu from redacted item screens and current recipe/price table | Requires product feature completion if used |
| Tables/sector IDs | Rodada Table/Zone/ServicePoint | Read-only list and manual verified mapping; opaque QR label printed from Rodada | Physical re-label carefully |
| Staff roles and PIN | New Rodada StaffMember/VenueMembership/DeviceRegistration | Owner-approved manual enrollment, new PINs only; **never copy passwords, PIN hashes or VR credentials** | Re-issue credentials |
| Identified customers | Optional local Relationship | **Do not migrate by default**; consent and business purpose first; minimal fields only | Most pilot orders anonymous |
| Existing open Tabs | New operating boundary | **Prefer cutover at shift boundary with all VR Tabs closed**; otherwise signed dual-booked exception ledger, no synthetic confirmed payment/imported fake order | Highest-risk migration |
| Historical sales | Reporting-only historic source, not new canonical Charges | Keep VR read-only licensed access/export or aggregate PDF/CSV summaries where legally authorized | Nice to have, not P0 |
| Tax/fiscal history | Existing accountable issuer/system | Accountant-directed retention and access; **do not convert old notes into Rodada fiscal records** | EXTERNAL dependency |

**Do not import old confirmed VR sales as new Rodada Order/Payment/Charge.** Avoid carrying discounts as mutated prices. Store source mapping, import timestamp, version/hash, exception count and rollback batch ID. Dry-run in isolated database, test samples and compare exact cents.

## 2. Cutover stages
### Stage A — Documentation and acceptance
1. Resolve [field-discovery](field-discovery.md) evidence; obtain Aderlan approval for mandatory use cases.
2. Validate software production readiness: cash, staff, Tab lookup, Bar/Kitchen routing, modifiers, discounts/service where used, split/merge where used, print fallback where used, provider/fiscal process, reliable recovery.
3. Copy limited sanitized product/price/table config to Rodada staging; human review top 50 high-turn items plus **100% items with extras/combos** (scope adjustable to actual catalog).
4. Rehearse end-to-end shift with simulation, web/mobile, printer and terminals on test accounts. Execute disaster recovery in isolated environment.

### Stage B — Shadow pilot without double operations
1. VR remains **single source of true customer billing, production dispatch and official fiscal issue**.
2. Rodada runs a parallel **read-only/sample shadow ledger** for supervised comparison; operators enter **sanitized simulated or consented shadow events only**, never charge a real customer a second time, never send duplicate tickets to production, and never accidentally affect inventory/fiscal.
3. Record per-order mapping (non-PII), missing/duplicate/late orders, observed fulfillment times, total by tender, waived/add-on/service cents, open balances, cash deltas.
4. End-of-shift compare `VR net billed = Rodada modeled net billed` for the **paired sample**, not whole-business totals when samples differ. Exception must be diagnosed, not hidden by arbitrary adjustment. No assertion that cash movement or fiscal transaction has two sources of truth.
5. Require at least **two normal shifts and one busy shift** with zero unresolved material money/order mismatch in the compared controlled sample (proposed acceptance gate, not a benchmark). Have staff explicitly sign off each high-frequency task.

### Stage C — Limited live mode / safe rollback
1. Select *one bounded lane/session/area* where Rodada is operational source for **that lane**, VR reserved as fallback, no concurrent double-keying of financial truth for those sales. Label pilot Tabs with their source system; use separate cash/payment reconciliation and controlled fiscal rules.
2. Staff champion present, fallbacks printed; any pending provider payment remains pending until canonical confirmation. Confirm routing by station and KDS at opening.
3. If critical incident occurs, **stop accepting new Rodada orders**, collect already-confirmed Rodada obligations, settle only once with dedicated incident register, then switch new work to VR after explicit cashier handoff. Never auto replay all Rodada orders as fresh VR sales.
4. Keep the roll-back cutoff time, open orders, Tab balances, confirmed payments, provider pending ids, already-prepared items and fiscal documents. Get manager approval before manual reentry.

### Stage D — Full switch
- A quiet shift/day boundary with VR cash/Tabs closed or documented exact reconciliation; reopen Rodada cash from a newly counted physical float; keep readable VR archive/export per lawful terms; print/table QR cards affixed; helpdesk staffed.
- Sign-off from owner, cashier, kitchen, bar, at least one waiter, plus accountant fiscal disposition.

## 3. Numeric reconciliation protocol (exact cents, no arbitrary zeroing)
For each parallel comparable transaction/Tab, compare: `gross items + service/couvert - discounts/courtesy + other justified charges = net payable`; `net payable - confirmed collections + confirmed refunds = exposure`. Verify cash tendered/change, card/Pix finality and external terminal slip. Group final totals by business date, station, payment method, operator and shift; log any timing-related differences separately from actual amount differences. Corrections preserve origin. For post-midnight bar, use Venue cutoff not civil midnight. Confirm fiscal totals *independently* per accountant.

## 4. Go/no-go and rollback
| Gate | GO | NO-GO |
| --- | --- | --- |
| Actual must-have workflows | Staff run every observed high-frequency action without missing semantics | Missing split/modifier/fee/print operation used in core shift |
| Money integrity | Exact cent reconciliation, no duplicate receipts, provider ambiguous states blocked and recovered | Unreconciled tender, pending marked paid, double-charge |
| Kitchen/bar | Every canonical confirmed item reaches correct queue **once**; measured peak service acceptable to staff | Lost/duplicated ticket, unobservable stalled queue |
| Network/disaster | API vs SSE loss explicit, reconnect catches up; restore rehearsal passes; fallback documented | Silent stale-state, can't recover confirmed Tab/payment |
| Fiscal/legal | Accountant signs operational solution and responsibilities for issued documents | Unknown legal status or unavailable mandatory fiscal issuing |
| Training/hardware | Role/device permissions, staff quick guide, enough working phones/PCs, printer if critical | Unusable BYOD, missing terminals, no contingency operator |
| Migration | Catalog correct, no duplicate open balance, every outstanding VR Tab reconciled | Unaccounted open Tab or item-price mismatch |
| Support | Owner/cashier know how to return to VR and whom to call | No vendor access/license, no human fallback |

**Immediate rollback triggers:** confirmed order missing at either station for an unrecoverable period, unexplained financial divergence, incorrectly “paid” provider state, unauthorized role change, broken mandatory fiscal flow, inability to accept/recover orders after connectivity event. Duration/latency SLO is to be set after field measurement; do not invent a baseline.

## 5. Cost/contract questions (verified price UNKNOWN)
The VR website advertises a suite/modules but **no reliable equivalent all-in published invoice** was established. Ask for redacted invoice and confirm: core E-Trade, Gourmet, Droid, KDS, Bridge/VR Pedidos, number of PDV/terminal licenses/serials, onboarding/setup, support SLA, Windows/SQL Server/remote support, printers, backups, card acquiring fees, fiscal integrations, cancellation notice/data portability and data export labor. Compare against Rodada's explicitly assumed infrastructure cost, PSP acquiring costs, per-venue support, printer/phone replacement, training and incident risk. Do **not** replace unknown monthly VR price with a guess.

## 6. Post-cutover controls
Daily paired cash review for first 10 trading days (proposed), pending PSP settlements, product/price drift, screen freshness, staff feedback, corrections, open Tabs and fiscal issuer ledger. Weekly owner review of error/correction patterns and infrastructure uptime. Restrict/rotate credentials, log imports and remove temporary sanitized test copies per retention plan.
