# VR System vs Rodada — operational capability matrix
**Repo baseline:** [main 4ba9c23](https://github.com/procopio420/rodada/commit/4ba9c237b74878730c8b133e70dd8b02087c2cd7), checked 2026-10-08; **VR = public evidence only**. Aderlan usage is `REPORTED` only for the fact of computer-based VR operation; no individual feature is `CONFIRMED`. All other rows `UNKNOWN`. `NOT_USED_CONFIRMED` = no verified instances.

Legend: Rodada `I` = IMPLEMENTED_AND_TESTED, `P` = IMPLEMENTED_PARTIALLY, `IP` = IN_PROGRESS, `S` = SPECIFIED_ONLY, `M` = MISSING, `EB` = EXTERNALLY_BLOCKED, `NA` = NOT_APPLICABLE. An `I` on a subsystem does not prove full live deployment. `P0?` indicates conditional blocker pending field discovery.

| Feature | VR module | VR evidence | Aderlan? | Rodada state | Rodada code/test evidence | Gap / priority |
| --- | --- | --- | --- | --- | --- | --- |
| Computer cashier operation | Gourmet/PDV | S01/S02 | REPORTED | P | `apps/web/app/pos/page.tsx`; `apps/web/tests/integration/workflows.spec.ts` | Real workstation drill / P0 |
| Staff auth & roles | E-Trade/Gourmet | S03,S15 | UNKNOWN | I | `access/services.py`, `test_access_security.py` | Validate staff devices / P0 |
| Register staff permissions and device trust | E-Trade | S03/S08 | UNKNOWN | P | `access/models.py`, Android secure session | Onboarding/revocation onsite / P0 |
| Open cashier float | E-Trade | S08/S09 | UNKNOWN | I | `cash/services.py`, `test_cash_management.py` | Physical cash rehearsal / P0 |
| Cash supply & withdrawal | E-Trade | S09 | UNKNOWN | I | `cash/services.py`, cash views | No code gap / P0 check |
| Cash count/close/variance/review | E-Trade/Droid | S08 | UNKNOWN | I | `test_cash_management.py`, `test_web_completion.py` | Actual shift reconciliation / P0 |
| Anonymous Tab | Gourmet order (mode U) | S03/S15 | UNKNOWN | I | `test_ordering_foundation.py` | Better model; no parity gap |
| Table setup & occupancy | Gourmet | S07 | UNKNOWN | I | `hospitality/models.py`, `test_hospitality_tables.py` | Map actual table IDs / P0 |
| Multiple Tabs per table | Gourmet | S07 | UNKNOWN | I | `hospitality/services.py`, `test_full_shift_smoke.py` | Better separation |
| Move Tab to another table | Gourmet | S11 | UNKNOWN | P | `hospitality/services.py` assigns occupancy | Operational location exists; full spec 009 remaining / P0? |
| Merge table/comandas | Gourmet | S06/S11 | UNKNOWN | IP | `specs/009` only; no TabTransfer model/routes | Monetary merge P0? if used |
| Split bill/transfer items | Gourmet | S06 | UNKNOWN | IP | `specs/009`; `ordering/models.py` lacks transfers | P0? |
| Reopen/cancel empty Tab | Gourmet (reopen U) | S15 | UNKNOWN | S | `specs/009` | P1 pending field |
| Duplicate Tab repair | Gourmet cancel | S15 | UNKNOWN | P | `corrections/services.py`; no structural merge | P0? |
| Barcode physical comanda | Gourmet | S07 | UNKNOWN | S | `specs/004`; opaque QR/tab identifiers partial | P1 if cards in use |
| Product master, price, station | E-Trade | S02/S06 | UNKNOWN | I | `catalog/models.py`, `test_catalog_models.py` | Data migration / P0 |
| Category tree / bulk import | E-Trade | S05/S10 | UNKNOWN | M | catalog Product fields lack category + importer | P0? catalog migration; P1 UX |
| Quick Catalog resolve/create | E-Trade product register | S02 | UNKNOWN | I | `catalog/services.py`, `test_web_completion.py` | Better; AI images EB/P2 |
| Variant (size/flavor) | Gourmet | S06 | UNKNOWN | S | `specs/010`; no Variant model | P0? menu-specific |
| Priced modifiers, extras | Gourmet | S06 | UNKNOWN | S | `specs/010`; `ordering/serializers.py` has only base product & qty | P0? |
| Ingredient removals / production notes | Gourmet | S06 | UNKNOWN | S | `specs/010`; no structured line snapshot | P0? |
| Combo/kit/combined | Gourmet | S06 | UNKNOWN | M | no combo/kit model | P1 if sold, P0? if core menu |
| Price snapshot & server validation | Gourmet | S06 | UNKNOWN | I | `ordering/services.py`, `test_ordering_foundation.py` | Rodada safer |
| Product unavailable across surfaces | Vendor not verified | — | UNKNOWN | I | `catalog/views.py`, `test_ordering_foundation.py` | Rodada distinctive capability |
| Order idempotent confirm | Vendor not verified | — | UNKNOWN | I | `ordering/services.py`, `test_ordering_foundation.py` | Rodada distinctive |
| Kitchen/Bar routing | Gourmet/KDS | S04/S06 | UNKNOWN | I | `ordering/views.py`, `production-board.tsx` | Station setup & field validation / P0 |
| Queue freshness | Monitor KDS | S04 historic 30s | UNKNOWN | IP | `production-board.tsx` 5s polling; `specs/014` SSE | SSE/outbox P0 high-value; unmeasured superiority |
| Item-ready & dispatch | Gourmet/KDS | S04 | UNKNOWN | I | `ordering/services.py`, `dispatch/services.py`, `test_dispatch.py` | Per-role rehearsal / P0 |
| Prep ETA / late signaling | Monitor KDS | S04 | UNKNOWN | P | timestamps in order state; no verified configurable prep target | P1 |
| Cancel/remake wrong item | Gourmet | S15, remake not established | UNKNOWN | I | `corrections/services.py`, `test_corrections.py` | Audit verified by tests |
| Full multi-station grouped KDS | Gourmet/KDS | S04 | UNKNOWN | P | two boards; item queues | P1 grouping usability |
| Paper kitchen fallback / reroute | Gourmet | S04/S06 | UNKNOWN | S | `specs/015`; no PrintJob code | P0? if required |
| Guest QR browse/order | VR Pedidos | S05 | UNKNOWN | P | `guest_access/services.py`, `workflows.spec.ts` | Guest tracking polling / current track |
| Guest QR waiter validation | VR Pedidos/Gourmet Droid | S05 | UNKNOWN | NA | Rodada guest token/epoch + server confirmation | Intentional simpler UX; staff can block |
| Partial manual payments | Gourmet | S06 | UNKNOWN | I | `ledger/services.py`, `test_ledger_payments.py` | Real cashier practice / P0 |
| Cash + change | E-Trade | S06 | UNKNOWN | I | `cash/services.py`, `test_cash_management.py` | Cash tray drill / P0 |
| External card terminal recorded | E-Trade/PDV | S06 | UNKNOWN | I | `PaymentMethod.EXTERNAL_TERMINAL`; test Web | Manual proof, no provider attestation |
| Production Pix | Gourmet/PDV | S16 | UNKNOWN | IP/EB | `payment_provider/adapters.py`: deterministic fake only | Live provider P0 if digital collection in pilot |
| Native Android Tap on Phone | Droid? provider specific U | S02 (mobile orders) | UNKNOWN | IP/EB | `TapToPayProvider.kt` Unavailable | SDK credentials/onboarding/device eligibility P0 if used |
| Provider webhook & idempotency | VR payment internal U | S16 | UNKNOWN | P | `payment_provider/services.py`, `test_payment_provider.py` with test double | Live signature, webhook and reconciliation P0 |
| Refund / paid correction | Gourmet refund semantics U | S06 | UNKNOWN | P | `ledger/services.py`, `test_full_shift_smoke.py` | Live provider refund still missing P0? |
| Discount per item/Tab | Gourmet | S06 | UNKNOWN | S | `specs/011`; no pricing endpoints | P0? if used |
| Courtesy/service charge | Gourmet | S06 | UNKNOWN | S | `specs/011` | P0? if used |
| Couvert / party size | Gourmet | S06 | UNKNOWN | S | `specs/016` | P1, P0? if charged |
| Credit/house relationship | E-Trade | S06 | UNKNOWN | P | `house_account/services.py`, `test_house_account_e2e.py` | Policy confirmation / P0? |
| Customer history | E-Trade/VR Pedidos | S05 | UNKNOWN | P | `house_account`, guest history | P1 if loyalty used |
| Sales by product/method/period | E-Trade | S05/S06 | UNKNOWN | I | `management/views.py`, `test_web_completion.py` | No new code required baseline |
| Sales by employee/commission | E-Trade | S07 | UNKNOWN | M | no specialized staff commission read model | P1 if commissions paid |
| Closing & late corrections | E-Trade | S08/S09 | UNKNOWN | I | `cash/services.py`, `test_web_completion.py` | Operational runbook |
| Receipts/print customer check | Gourmet/PDV | S06/S12 | UNKNOWN | S | `specs/015`, no printer services/app | P0? |
| Fiscal NFC-e/CF-e/NF-e | Gourmet/PDV/E-Trade | S03/S12/S13 | UNKNOWN | M/EB | no fiscal app/routes | **EXTERNAL verification blocker**, conditional implementation |
| Stock/ingredients/recipe costing | E-Trade | S02 | UNKNOWN | M | no stock app | P2 / OUT_OF_SCOPE unless daily process |
| Delivery and takeaway | Gourmet, VR Pedidos | S02/S05 | UNKNOWN | M | no delivery app | P2 or OUT_OF_SCOPE pilot |
| Reservations/turnstile/scale | Optional/unknown | S02/S07 | UNKNOWN | M/NA | no models | OUT_OF_SCOPE barring actual dependence |
| Backup & restore | E-Trade | S14 | UNKNOWN | P | `apps/api/scripts/*backup*/*restore*`, `test_restore_rehearsal.py` | production restore drill P0 |
| Audit trace | E-Trade permission evidence | S08/S15 | UNKNOWN | I | `audit/services.py`, multiple tests | Rodada append-only corrections |
| Reports export | E-Trade/VR Pedidos | S05/S09 | UNKNOWN | I | `test_web_completion.py`, CSV | baseline |
| Data catalog export/import | E-Trade | S10 (authorized SQL→CSV; import) | UNKNOWN | M | demo seed only, no controlled VR mapper | Migration tooling P0 before cutover |
| Network recovery and stale state | VR UNKNOWN | — | UNKNOWN | IP | `specs/014`, Android pending intents, polling | failure drills P0 |

### Key classification caveats
- “Rodada I” = code and test coverage on inspected **main**; not real-device, printer, fiscal or payment acceptance.
- Code-inspected absences are **specific** (no Variant/Modifier, TabTransfer, PrintJob or corresponding routes in main); do not claim proof of runtime inability in a different unpublished branch.
- `P0?` means **may become P0** only after staff confirms actual usage / non-negotiable requirement.
- No public source demonstrates VR KDS response time in the Aderlan installation; **30s is historical documentation**, while Rodada **5s is current polling interval**, not measured end-to-end latency.
