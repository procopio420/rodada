# VR System: product map and feature inventory
**Observation:** 2026-10-08. **Scope labels:** DOC = official documentation; RELEASE = change log; CHECKLIST = official QA/installation checklist; MKT = marketing. **Aderlan deployment/usage UNKNOWN for every row** unless explicitly stated otherwise. `Current?` is *not* a guarantee of current build or license.

## Product/module graph
```text
VR System / VR Tech vendor
└─ E-Trade: main ERP/commercial/stock/finance database and management
   ├─ PDV: general checkout/retail sale, optional Gourmet-related print routing
   ├─ Gourmet: venue-specific sale, table/comanda, ordering, cashier
   │  ├─ Gourmet Droid: Android ordering/selected closing; uses Gourmet
   │  └─ Monitor KDS: separate display dependent on E-Trade + Gourmet/PDV routing
   ├─ Delivery module: monitored delivery/takeout orders and routing
   ├─ Bridge: synchronization for selected integrated channels
   └─ VR Pedidos: online/QR/cardápio/autoatendimento with specific integration settings
```
This is a **functional model inferred from explicit docs** [S01–S05], **not** verified commercial packaging. Module contracts, fees and versions must be requested from owner/vendor. Gestor is an additional reporting app advertised by the vendor [S01]. **Important distinction:** KDS `Modo KDS` and sector/print area must be configured; VR Pedidos integration requires Bridge mappings and a dedicated open integration cashier [S04,S05]. VR Pedidos is NOT synonymous with Gourmet Droid.

## Inventory
| Capability / module | Documented behavior & prerequisites | Evidence / date | Current? | Aderlan installed/used? | Confidence |
| --- | --- | --- | --- | --- | --- |
| E-Trade base / general financial, stock | Suite baseline with prices, records, cash and reporting | S01 MKT; S02 DOC | Publicly advertised | UNKNOWN | H platform, M details |
| General PDV | Cash sale; ticket/fiscal, product and cashier configurations | S01 MKT; S03/S12 DOC | Documented | UNKNOWN | H |
| Gourmet / desktop touch | Restaurant/bar table, comanda, orders, station routing, financial | S02 DOC; S06 CHECKLIST | Documented | UNKNOWN | H |
| Gourmet Droid Android | Waiter launches mobile orders, Gourmet dependency | S02 DOC; S08 2025 RELEASE | Documented | UNKNOWN; reported computer-focused | H |
| KDS screen | E-Trade item prep time; compulsory print area; routing per item or grouped on leave/close | S04 DOC ~2022 | Historical, recheck | UNKNOWN | H historical |
| KDS freshness | Vendor says new info every **30s**; six cards/page | S04 DOC | **Unverified in 2026 build** | UNKNOWN | H historical |
| KDS states | On-time/delayed/ready/cancelled; ETA based on item time; “ready” when whole group complete | S04 DOC | Historical | UNKNOWN | H historical |
| Table assignment and comanda | Comanda individual or table group; configurable table codes/barcodes | S07 DOC 2021–2023 | Documented | UNKNOWN | H |
| Combined tables/comandas | Merge table, merge comanda and association in QA; merge tables with associated comandas in v37 | S06 CHECKLIST; S11 2026 RELEASE | Build dependent | UNKNOWN | H |
| Desmembrar item / check split | QA explicitly exercises splitting an item; does **not** prove arbitrary financial split algorithm | S06 CHECKLIST | Documented | UNKNOWN | H for scenario |
| Products + priced extras | Additional item changes total; combos/kits/couvert in QA | S06 CHECKLIST; S02 DOC | Documented | UNKNOWN | H |
| Ticket sectors | Sector output (Bar/Cozinha), fabricated items with component routing rules | S06 CHECKLIST; S04 DOC | Documented | UNKNOWN | H |
| Printing at moment of item/closing | Configuration determines KDS/print dispatch timing; must configure print area | S04 DOC | Documented | UNKNOWN | H |
| Cancellation of table/order | Permissions and edit/cancel semantics in old workflow | S15 DOC 2018 | Must verify updated behavior | UNKNOWN | M |
| Operative staff & permissions | E-Trade configurable staff account; seller attribution, seller badge & commission | S03 DOC; S07 DOC | Documented | UNKNOWN | H |
| Waiter commission | Vendor checklist highlights seller badges/commission, not universal rollout | S07 DOC | Documented | UNKNOWN | M |
| Cash open/close and physical float | Financial module tracks cash transactions, withdrawals and daily print/PDF | S09 DOC, S16 DOC | Documented | UNKNOWN | H |
| Mobile cash close | Droid handles close, open-tab blocking and printer behavior; specific gaps listed | S08 2025 RELEASE | Build dependent | UNKNOWN | H |
| Multiple payment methods/credit | QA stress-tests cash, card, credit, change and reports; don't assume enabled | S06 CHECKLIST | Documented | UNKNOWN | H |
| PIX/card auto-receipt | Cashier config may auto-settle card/Pix depending settings | S16 DOC | Config dependent | UNKNOWN | M/H |
| Discounts/surcharges/couvert | Item and sale discounts, extra charge, cover count in official testing | S06 CHECKLIST | Documented | UNKNOWN | H |
| Credit account | Customer credit scenarios in payment QA; separate from VR Pedidos limitation | S06 CHECKLIST; S05 DOC | E-Trade documented | UNKNOWN | M |
| Audit/fraud controls | Role permissions, cancellation and financial guardrails exist; exact retention/immutability unknown | S07/S08/S15 DOC | Config dependent | UNKNOWN | M |
| Inventory/recipes/production orders | E-Trade stock, product compositions and order of production | S02 DOC | Documented | UNKNOWN | H |
| Reports | Receipt by method, products, cashier & general sales in QA/E-Trade; VR Pedidos basic reports only | S06 CHECKLIST; S05 DOC | Documented | UNKNOWN | H |
| Customer loyalty/history | E-Trade customer capabilities mentioned, VR Pedidos returning-order history for phone number | S02 MKT; S05 DOC | Separate modules | UNKNOWN | M |
| Delivery and takeout | Gourmet Delivery and monitored imported orders; integration required | S02/S05 DOC | Config/module dependent | UNKNOWN | H |
| QR guest orders | VR Pedidos table QR: guest sends request; Droid waiter scans/validates before import | S05 DOC ~2026 | Feature documented | UNKNOWN | H |
| QR digital menu alone | VR Pedidos QR may be view-only or accept orders, per store config | S05 DOC | Config dependent | UNKNOWN | H |
| Kiosk with TEF | WebPrinter/TEF to E-Trade, depends on integration cashier, Windows local setup | S05 DOC | Dependent on TEF/tested drivers | UNKNOWN | H |
| NFC-e/CF-e | Gourmet/PDV fiscal sending and ticket options; export XML from E-Trade | S03,S12,S13 DOC | Config/compliance dependent | UNKNOWN | H |
| NF-e/NFS-e | E-Trade fiscal suite; 2026 release mentions NFS-e | S01, S13 and 2026 changelog S11 | Module/legal variant unknown | UNKNOWN | M |
| Export/import migration | Public guide documents product/client CSV **import** plus authorized SQL export examples; no proven one-click full export | S10 DOC | Manual/vendor path | UNKNOWN | H |
| Backup | Windows/SQL Server backup manual documented, process version-dependent | S14 DOC | Documented | UNKNOWN | H |
| Barcode/scale | Physical comanda barcodes and optional E-Trade balance integration | S07; [scale guide](https://vrsystem.info/publico/post/balancas---exportacao-de-dados/e8dec840-2fe9-4b58-9cd1-1e59e17cede2) | Optional | UNKNOWN | H |
| Reservations | No reliable current official evidence found during this pass | — | UNVERIFIED | UNKNOWN | L |
| Multi-device offline guarantees | No verified guarantee of autonomous offline ordering; SQL-local nature not equivalent to offline all stations | S14 DOC only | UNKNOWN | UNKNOWN | L |
| Public license price | No trustworthy **published price for comparable Gourmet+PDV+Droid+KDS package** confirmed | — | UNKNOWN | UNKNOWN | L |

## Contradictions / important gotchas
- **30 seconds** is in historical KDS manual, not a 2026 benchmark or Aderlan observation [S04].
- VR Pedidos' guide has multiple modes (online delivery, menu, kiosk/TEF); statements about payment support may be **mode-specific**, and its limitations section explicitly disclaims continuous updates [S05]. Don't generalize “no online payment” to kiosk TEF.
- The official QA script is useful as a **scenario checklist** but not proof of workflow count or any bar's usage [S06].
- **Physical receipt vs electronic fiscal transmission** are independent [S12]. Accounting assessment is external.
- Training material may describe old bugs or custom settings; do not make Rodada copy a vendor's historical semantics blindly.
- Commercial packaging (which is paid) is **UNKNOWN**. Request Aderlan invoice / vendor-approved summary instead of guessing license counts or hardware prices.

## Pilot relevance
- **Probable P0 after field verification:** table/comanda split/merge, sides/notes/modifiers, priced discounts/fees, payment reconciliation, cashier close, print failover, fiscal compliance.
- **Probable P1:** waiter commission report if paid this way; simple sales/product export; useful demand-driven history.
- **Probable P2 or OUT_OF_SCOPE:** deep ingredient/BOM, purchasing, multi-branch finance, turnstile, scales, full delivery marketplace and general accounting (unless field evidence shows the bar really depends on one).
