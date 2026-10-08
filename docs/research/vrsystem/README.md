# VR System → Rodada — competitive and migration audit
**Observed:** 2026-10-08 (America/Sao_Paulo). **Rodada baseline:** main `4ba9c237b74878730c8b133e70dd8b02087c2cd7`. **Scope:** Bar do Aderlan, supervised pilot, no product-code changes.

## Executive decision
**Not ready to replace VR System.** Rodada has real API/Android/Web vertical slices and tested cashier, ledger, guest, correction and management flows, but lacks production PSP integration, structured modifiers/variants, financial split/merge of Tabs, discount/service-charge handling and printing fallback. Realtime is five-second polling, not the specified durable SSE/outbox. Field verification and independent fiscal/accounting clearance remain prerequisites. A narrow, reversible **supervised shadow pilot** is feasible once the two-way operational accounting procedure, backup/fallback and staff consent are in place; no live payment may be claimed as integrated until provider certification/live tests exist.

## Confirmed public findings (NOT Aderlan usage)
1. **E-Trade** is the platform; **Gourmet** is a configurable restaurant module; **Gourmet Droid** is an Android variant working with Gourmet. A separate **PDV** exists. The **Monitor KDS** is configured alongside Gourmet/PDV; its official article says updates every **30 seconds** (historical document; confirm installed version). [S01,S02,S04]
2. Gourmet's official upgrade-test script checks **table/comanda association, merging, splitting items, additions, discounts, couvert, sector tickets, NFC-e**. These are meaningful replacement threats, not proof Aderlan uses them. [S06]
3. A 2026 release adds **joining tables with associated comandas**. Do not assume the version installed at Aderlan includes it. [S11]
4. **VR Pedidos** is a separate configurable online/cardápio/QR channel with E-Trade integration via Bridge and an **integration cashier that must remain open**; QR-by-table flow described in the documentation requires **waiter validation through Gourmet Droid**. It is not proven deployed at Aderlan. [S05]
5. Fiscal emission cannot be dismissed: the vendor explicitly describes **NFC-e/CF-e printing choices in Gourmet** and NFC-e for Gourmet/PDV; sales/legal status at Aderlan remains UNKNOWN. [S03,S12]

## Verified Rodada on main
| Capability | Status | Concrete evidence |
| --- | --- | --- |
| Tab without table, order confirmation, server-side unavailable product, immutable price snapshot | IMPLEMENTED_AND_TESTED | `modules/ordering/services.py`, `tests/test_ordering_foundation.py` |
| Manual cash / external terminal receipt, partial payments, refunds, correction flows | IMPLEMENTED_AND_TESTED (manual only) | `modules/ledger/services.py`, `modules/corrections/services.py`, `tests/test_full_shift_smoke.py` |
| Open/supply/withdraw/count/close/review cash shift | IMPLEMENTED_AND_TESTED | `modules/cash/services.py`, `tests/test_cash_management.py`; Web `/cash` |
| Staff identity/device auth, separate bar/kitchen/guest/management surfaces | IMPLEMENTED_PARTIALLY | `modules/access/*`, `apps/web/*`, `apps/attendance-android/*`; actual BYOD fleet untested |
| Quick catalog create-or-reuse and fallback icon | IMPLEMENTED_AND_TESTED (without external AI) | `modules/catalog/services.py`, `tests/test_web_completion.py`; CI recorded in `docs/development/web-operational-completion.md` |
| Guest Tab order history | IMPLEMENTED_AND_TESTED (polling) | `tests/test_web_completion.py`, `apps/web/tests/integration/workflows.spec.ts` |
| Integrated Pix/Tap on Phone | IN_PROGRESS / EXTERNALLY_BLOCKED | `payment_provider/adapters.py`: test double only; Android `TapToPayProvider.kt` always unavailable |
| Financial split/merge/reopen Tabs, modifiers, price policy, print queue, durable SSE/outbox | SPECIFIED_ONLY | specs 009/010/011/015/014; absent concrete migrations/routes/production implementation in current tree |
| Fiscal documents | MISSING, applicability UNKNOWN | no fiscal module/route; needs accountant review and Aderlan verification |

The 2026-10-08 Web completion record cites 159 API tests (plus 3 SQLite skips), 30 PostgreSQL CI tests, 102 Web visual tests and 5 E2E browser flows from merged PR #43; **reported CI, not rerun during this research**. This audit inspected current main content, not a live installation.

## P0 decisions
- **Already in the four in-progress tracks:** 006 live provider Pix/Tap, 005 external icon AI (not pilot-critical), 009 advanced Tab ops, 014 SSE/outbox and guest tracking. Avoid duplicate backlog assignment.
- **New priority behind/in parallel with those tracks:** structured variants/modifiers (010), discounts/courtesy/service charge (011), customer check and printer fallback (015), failure-mode rehearsal and verified backup/restore (014/015). Their pilot-blocker status depends on Aderlan's workflows, except safe recovery which is always required.
- **Conditional external blockers:** fiscal obligations and their operational fulfillment; payment/provider onboarding; current open Tabs and catalog access; actual workstation/receipt/printer requirements; signed off rollout/rollback.
- **Not automatic launch scope:** deep inventory/BOM, accounting ERP, delivery marketplaces, turnstiles, scales, cross-branch treasury, loyalty/campaign suite.

## Five field unknowns to resolve
1. Exactly which binaries/modules/versions/screens are running and which staff actually use them.
2. Which split/merge, additions, service charge, discount and printed ticket actions occur on a peak shift.
3. Whether the current POS issues NFC-e/CF-e/NF-e or another fiscal workflow does, and who approves the compliant transition.
4. Actual payment rails and settlement: Pix, POS terminals, fees, partial tender, refunds, tip, cash-change and how discrepancy is resolved.
5. Data and fallback: who can export catalog, current open balances, printer models, internet/Wi-Fi behavior, VR invoice/license and emergency steps.

## Reading order
[Capability inventory](product-capabilities.md) · [Full shift](operational-workflows.md) · [Comparison matrix](feature-parity.md) · [Priority engineering backlog](gap-backlog.md) · [Field script](field-discovery.md) · [Migration & go/no-go](migration-plan.md) · [Evidence catalog](sources.md).

**Evidence rule:** `PUBLIC_DOCUMENTED` ≠ `ENABLED_AT_ADERLAN` ≠ `ACTUALLY_USED`; use `UNKNOWN` until field observation. No invented click counts, prices or legal conclusions.
