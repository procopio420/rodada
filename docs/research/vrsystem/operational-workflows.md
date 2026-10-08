# Reconstructed shift: VR System against Rodada
**Evidence boundary:** this is a **document-based conditional reconstruction**, NOT observation at Bar do Aderlan. All `Aderlan use = UNKNOWN`; every action count and measured execution time = **UNKNOWN**. Hardware and actors are candidate roles to verify onsite. Sources are indexed in [sources](sources.md); Rodada references refer to 2026-10-08 `main`.

Notation: VR **D** = documented, **C** = config/optional, **U** = not established. Rodada **I** = implemented/tested, **P** = partial, **S** = specified only. Persist = fields/events Rodada must retain. “Failure” identifies test scenario, not an allegation of VR failure.

## 1. Opening, setup, readiness
| Step | VR workflow + evidence | Operator/equipment | Persist and failure mode | Rodada counterpart / opportunity |
| --- | --- | --- | --- | --- |
| Operator starts and logs in | D staff login; role/config gating [S03,S15] | Cashier; Windows PC (Droid if deployed) | actor/session, venue, capabilities; wrong operator/device | I Auth backend PIN/device; verify real BYOD login / role switch; no need per-order login |
| Open cashier / float | D cash open and movements [S08,S09,S16] | Cashier; PC/cash drawer | cashPoint, business date, float, operator; duplicate open or wrong drawer | I `cash/services.py` + tests; manager/mobile cash screen; one canonical cash shift |
| Staff role and cashier policy | C staff restrictions, open tables/pending orders can block close [S08] | Manager; PC | permission/version policy, exceptions | P access configurable; verify actual Aderlan policy, don't mirror permission numerics |
| Stations online | C KDS requires specific mode, area of print and sector [S04] | Cook/bar; monitor or printer | station routing, enabled settings, heartbeat; missing route | I route BAR/KITCHEN in Product; **S durable SSE/outbox and print fallback** |
| Hardware/config check | C printer, ticket, fiscal, cash settings [S03,S04,S12] | Manager; Windows/receipt printer/network | endpoint, fiscal mode, issue/retry state; printer down or silent fiscal | **S** 015; no print-job model today; add start-shift readiness check if paper used |

## 2. Arrival and first order
| Step | VR workflow + evidence | Operator/equipment | Persist and failure mode | Rodada counterpart / opportunity |
| --- | --- | --- | --- | --- |
| Open table/comanda | D per-individual or whole table, E-Trade preregistered card codes [S07] | Cashier/waiter; PC/physical card/scanner (C) | table, comanda, association; duplicate identity | I `Tab` opens without table; occupancy separately mapped in hospitality; fewer mandatory identities |
| Anonymous walk-in | U whether exact anonymous action; Gourmet supports new order [S03,S15] | Cashier; PC | ephemeral Tab id, business date; lost anonymous account | I no-name Tab/optional display label `test_ordering_foundation.py` |
| Multiple guests / same table | D comanda per person or group [S07] | Cashier/waiter; PC/barcode (C) | TableOccupancy ↔ many Tabs; merging wrong customers | I occupancy assignment, NOT financial merge [`hospitality/services.py`] |
| Link customer/regular | D customer/financial controls as E-Trade capabilities, usage unknown [S02,S06] | Cashier; PC | customer link/consent, balance policy | I `house_account` with audited limits; identity optional |
| Search/select products | D base catalog & sales plus extras [S06] | Cashier or Droid waiter; keyboard/touch | price snapshot, product revision, disabled products | I catalog server validation; Android BYOD mobility is a **proposed** gain only |
| Variant/extra/special note | D priced extra, kits, combinations [S06] | Cashier; PC/Droid C | variant/addon/notes as immutable snapshots; kitchen receives wrong choice | **S Spec 010**, model and request serializer presently quantity/product only |
| Create/confirm order | D order persisted, print/KDS may happen per-item or after leave/close [S04] | Cashier/waiter; PC/Android C | idempotency, actor, financial and production transaction; duplicate dispatch | I `ordering/services.py` and tests; server confirmation atomically creates Charges |

## 3. Bar and kitchen
| Step | VR workflow + evidence | Operator/equipment | Persist and failure mode | Rodada counterpart / opportunity |
| --- | --- | --- | --- | --- |
| Route products to station | D print area compulsory for KDS; optional sector [S04] | Station PC/KDS/printer | destination, item snapshot, dispatch status; item never appears | I Product.fulfillment_station; separate BAR/KITCHEN Web |
| Display incoming | D historical **30-second** KDS update and 6/page [S04] | Cook/bar; KDS monitor | timestamp, received_at, freshness; idle screen stale | P Rodada **5-second polling**, SSE spec-only; benchmark only with same network |
| Prep, ready and delivery | D KDS ready/delayed/cancelled states; missing ETA field disables delayed status [S04] | Cook and runner; monitor | item timing, reason, actor, source, confidence | I item transition & dispatch task; P passive last-mile; avoid forced “delivered” taps |
| Partial readiness / multiple items | D whole card green only once all ready [S04] | Cook; KDS | per-item state, order aggregate; hidden partially ready item | I per-item state; verify grouping UX on busy-shift simulation |
| Item unavailable | Vendor-specific behavior not established in cited KDS docs | Cook/manager | versioned availability, worker, blocked confirmation | I shared ProductAvailability; staff+guest race tested |
| Cancel/remake/post-pay refund | D cancel rights [S15], QA checks paid movement; exact remake policy U [S06] | Manager and operator; PC | immutable original, reversal, audit, refund record | I corrections/refunds `tests/test_full_shift_smoke.py`; provider refund integration still blocked |
| KDS fails / paper backup | C item dispatch linked to print config [S04] | Cook, cashier; printer/monitor | failover reason, print job/reprint, no double-prep | **S 015**: printer/PDF path not implemented; practice fallback drills |

## 4. Tables, splits and exceptional reassignments
| Step | VR workflow + evidence | Operator/equipment | Persist and failure mode | Rodada counterpart / opportunity |
| --- | --- | --- | --- | --- |
| Move table / assign comanda | D association & 2026 updated merge [S07,S11] | Cashier; PC/Droid C | location version + history; order at wrong destination | I reassign Tab to occupancy; **not** ledger transfer |
| Join tables/comandas | D QA scenario and v37 merge with associated card [S06,S11] | Cashier; PC | source/destination Tab, conserved balance, audit | **S 009**: no TabTransfer or endpoint; hard P0 if actually used |
| Split item/check | D QA “Desmembrar Item”; exact boundaries and clicks U [S06] | Cashier; PC | exact cents, item selection, counterpart; duplicated/vanished charge | **S 009**, require additive balanced ledger and no confirmed-payment moving |
| Duplicate accidental order/tab | D old cancellation uses permission; QA not detailed [S15] | Manager; PC | reason, compensation, idempotency | P order item corrections exist, structural duplicate-Tab fix missing |
| Reopen closed transaction | U exact product support/version | Manager; PC | reopening reason/version, original payment unchanged | **S 009**; field verify before P0 |
| Count people/couvert | D explicit cover count and couvert in QA [S06] | Cashier; PC | covers, charge, discount/exception | **S 016** covers; **S 011** couvert/service/discount components |

## 5. Settlement and closing
| Step | VR workflow + evidence | Operator/equipment | Persist and failure mode | Rodada counterpart / opportunity |
| --- | --- | --- | --- | --- |
| Print a pre-payment check | D ticket workflows via payment config [S12] | Cashier; receipt printer | immutable check snapshot, generation timestamp | **S 015**; customer digital Tab view exists but print missing |
| Pay partially/split tenders | D vendor QA scenarios for change, card, credit [S06] | Cashier; PC/POS terminal | per-payment method, tendered, change, reconciliation | I manual partial ledger/cash/terminal; live Pix/Tap only test adapter |
| Pix/card provider finality | C E-Trade settings for auto card/PIX postings [S16] | Cashier; terminal/PC/QR | external provider id, pending/confirmed, webhook | P provider attempt inbox/idempotency, **no real provider**; never mark ambiguous payment settled |
| Discount/courtesy/service/couvert | D item/total discount, additions, couvert [S06] | Cashier/manager; PC | Adjustment reason/actor/tax base, allocation | **S 011** beyond correction adjustments; loss-risk if charged today |
| Credit/refund/change | D vendor QA includes return cash and customer credit [S06] | Cashier/manager; till | actual refunded/change cents, outstanding | I cash change and refunds, but provider refunds need a live adapter |
| Close comanda | D Gourmet sale/close [S06] | Cashier; PC | zero or authorized unpaid balance, closed_at | I `ledger/close_tab`; verify real courtesy/payment rules |
| Cash supply, sangria, count and variance | D cash module [S09]; mobile close in certain builds [S08] | Cashier/manager; till | cash movements, count, discrepancies, approvals | I `cash/services.py`; UI Web/Android partly complete, CI reported |
| Daily sales and exceptions | D vendor reports E-Trade, simplified VR Pedidos reports [S05,S06] | Owner/cashier; PC | business date, item, tender, refund, staff, open Tabs | I management reports CSV, date cutoff, audit; verify specific report owner relies on |
| Fiscal issue / extract | C NFC-e & payment-dependent output [S12,S13] | Cashier/accountant; PC/cert/printer | authorized XML/protocol, cancellation/contingency | **MISSING; externally blocked legal assessment** |
| Late correction and next opening | D vendor cashier tools; exact policy U [S08,S09] | Manager; PC | immutable prior closing & late adjustment | I reviewed historical close + late-correction backend |

## Peak-shift comparison plan — no fabricated measures
Instrument **same 10 representative scenarios** on authorized, test-capable station(s): 1 drink, 1 food with add-on, multi-station order, second waiter same Tab, split a table between guests, 2-tender close, remove incorrect item, kitchen marks ready, item out-of-stock, printer/network loss. On VR and Rodada log: `tap/key/click count`, number of screen switches, P50/P95 user-visible duration, dispatch lag at kitchen/bar, human escalations, wrong/missed item count, correction time. At least 5 rehearsals per scenario; 20+ under a realistic peak-load simulation if feasible. Record device model, network, version, clock sync and visible effects; exclude typing time differences or classify separately. Compare with identical seeded catalog and scenario scripts. **Current VR action/time counts = UNKNOWN.**

## Faster-by-design opportunities (hypotheses, not measured wins)
Android BYOD avoids return to cashier PC for every order; searchable standalone Tabs do not require assigning a physical Table; waiter need not tap delivered in normal flow; product outage immediately blocks staff/guest server-side; single ledger computes all collection modes; manager sees exceptions before reports. Counter-risk: requiring per-item additional screen, flaky BYOD or missing print fallback may erase any gain.

## Data & risk controls for all workflows
Persist `venue, business_date, actor/device, Tab, TableOccupancy association history, OrderItem snapshot, state/timestamps, Charge/Adjustment/Payment/Refund ids, provider evidence, CashShift, audit and idempotency` as relevant. Failure drills: lost Wi-Fi, SSE down but API up, kiosk stale, printer silent, duplicate tap, delayed webhook, unexpected power-off, shared PIN leak, cross-venue access, fiscal contingency. *Unknown* device counts, actual printer models, payment provider, peak loads and table layout are field tasks, not engineering assumptions.
