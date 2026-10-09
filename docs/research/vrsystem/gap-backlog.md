# Evidence-based backlog and implementation order
**Date/baseline:** 2026-10-08; current `main`. Priorities are *pilot criticality*, not vendor parity. Do not start implementation from this audit: existing spec remains authority.

## P0 — verified technical gaps or mandatory acceptance gates
| ID | Failure scenario / required outcome | Status | Spec | Complexity | Dependency / evidence |
| --- | --- | --- | --- | --- | --- |
| P0-A | Customer pays Pix/Tap but provider callback times out: no double-charge, status reconciles, refund works | IN_PROGRESS + EXTERNALLY_BLOCKED | 006 | XL | Provider onboarding, adapter API/SDK, physical devices; fake adapter `payment_provider/adapters.py` and Android Unavailable |
| P0-B | Waiter and KDS lose network: confirmed item reaches station once, reconnect resumes correctly, authoritative totals converge | IN_PROGRESS | 014, ADR 0009 | L/XL | Outbox table/worker, SSE resume, fan-out & health; current Web setInterval 5000ms |
| P0-C | During migration, a customer with an open balance must never be lost or doubly charged; controlled catalog/snapshot import | MISSING | 001,009,013 (migration procedure new) | M | VR-approved export/manual reconciliation; seed command is not migration tooling |
| P0-D | Aderlan's real cash drawers, network, approved devices, staff permissions, production stations and emergency fallbacks work on a busy shift | IMPLEMENTED_PARTIALLY (integration acceptance) | 008,012,014,015 | M/L | onsite equipment inventory, full-shift acceptance and failover |
| P0-E | Fiscal output remains legally correct and reconciled during cutover | EXTERNALLY_BLOCKED | Separate fiscal decision after accountant signoff | **unknown** | Accounting/legal verification, issuer identity, documents & sequence, contingency; **never assume no emission** |
| P0-F | Paper ticket/guest bill is necessary during power/internet/KDS failure **IF** staff depends on it; no duplicate prep after retry | SPECIFIED_ONLY, conditional | 015 | L | printer mapping, spooler, print receipts, monitoring; no code module today |

## Conditional P0 — depends on real bar workflow; otherwise P1
| ID | Workflow problem | Rodada status | Spec | Complexity |
| --- | --- | --- | --- | --- |
| C0-1 | Two friends split 3 items and settle independently without altering paid history | IN_PROGRESS / no TabTransfer implementation | 009 | L |
| C0-2 | Customer orders half/half, size, extra cheese or “sem cebola”; station sees accurate price & modifiers | SPECIFIED_ONLY | 010 | L |
| C0-3 | Bill requires 10% service, item discount or manager courtesy while preserving immutable totals | SPECIFIED_ONLY | 011 | L |
| C0-4 | House sells bundled combo/kit with mixed Bar/Kitchen production | MISSING | 010 may need follow-up spec | M/L |
| C0-5 | Couvert charged per guest and report totals reconcile | SPECIFIED_ONLY | 016 + 011 | M |

## P1 — material value; not default blockers
P1-1 prep time/late SLA configuration and grouped KDS cards (S04; 003/018; M). P1-2 per-waiter revenue/commissions **only if payroll uses it** (007; M). P1-3 searchable product categories, safe bulk product creation/import, price audit (005/013; M). P1-4 visible bill sharing/tender comparison at cashier, customer receipt preview/export (015; M). P1-5 operational alerts and manager escalation (018; M/L). P1-6 historical feedback/loyalty if verified used (002; M). P1-7 barcode cards if kept physically (004; S/M).

## P2 / OUT_OF_SCOPE
- P2: recipe/ingredient counts, stock depletion, reservations, delivery/takeaway if later validated; real icon provider/AI styling; advanced insights, scale/barcode equipment as standalone improvement.
- OUT_OF_SCOPE for initial pilot: cross-company inventory procurement, general ledger, full fiscal ERP by default, public rewards engine, turnstile, multi-branch treasury, live promotion arbitrage and whole VR Pedidos ecommerce clone.
- The fiscal obligation is *not* out of scope just because direct issuing might be. The compliance decision is mandatory.

## Engineering story contracts for P0 and conditional P0
Each story below requires API permission checks, `AuditEvent`, idempotency/version lock when applicable, test of unhappy path and cross-surface display.

### P0-A — provider payments (track 1; Spec 006; XL)
- **Domain:** PaymentAttempt, ProviderEvent, pending/confirmed/refund evidence, canonical cents and provider-independent identity; do not claim success on provider timeout.
- **API:** initiate, webhook signature/inbox, lookup/reconcile, status; venue scoping, idempotent retries, no multiple active uncertain charges.
- **Surfaces:** Android provider-native Tap, guest/staff Pix QR, cashier status and disabled retry; external terminal remains explicit *manual*.
- **Permission/audit:** provider config manager-only; refund/override with reauth, actor, reason; secrets never in clients.
- **Dependencies/tests:** provider contract, webhook secret, homologation, actual Android/NFC phone, chargeback/refund capability, tests across duplicate/out-of-order webhooks, timeout, delivery twice, device offline, provider settlement. Existing `test_payment_provider.py` uses deterministic double; not evidence of live provider.

### P0-B — durable realtime (track 4; Spec 014/ADR 0009; XL)
- **Domain:** publishable event, per-venue monotonic cursor, durable outbox, at-least-once handling, state snapshot version.
- **API:** SSE auth, `Last-Event-ID`/resume, gap behavior, polling fallback with explicit freshness.
- **Surfaces:** Android/Bar/Kitchen/Guest/Manager connectivity states, no permanent stale green “ready”; quick recovery on reconnect.
- **Permission/audit:** venue/role-scoped subscriptions, no leakage of guest histories; auditable significant transitions.
- **Tests:** concurrent order transition and event commit, lost outbox dispatcher, split connection, cursor gap, P95 dispatch vs available VR KDS field baseline, 100+ orders simulation, 10+ station restart, slow consumer. Currently `production-board.tsx` polls every 5s.

### P0-C — migration-safe records (new; 001/009/013; M)
- **Domain:** legacy-ID mapping and immutable import provenance; item/price/category mapping; open-tab snapshot or boundary balance; never import duplicate financial history as new sales.
- **API:** admin-only idempotent dry-run import with schema verification and detailed reject manifest; snapshot hash/version report.
- **Surfaces:** manager import review and exception list; read-only sample import on preview environment.
- **Permission/audit:** owner authorization and data minimization, no raw customer PII by default.
- **Tests:** malformed CSV, duplicate normalized products, Unicode decimal commas, changed price between exports, open-tab balances, rollback from rehearsal, mismatch threshold **zero** before cutover.

### P0-D — readiness and restore (new acceptance; 008/012/014/015; M/L)
- **Domain/API:** per-Venue ability to verify ready/read-only service and shift reporting, explicit safe failure state, no fake confirmation.
- **Surfaces:** one-page start-shift and incident checklist usable without developer.
- **Permission/audit:** only manager may approve override/rollback; record incident and before/after totals.
- **Tests:** physical Android BYOD + KDS/bar PCs, unstable Wi-Fi, invalid PIN, lost device, cash deficit, print failure, PostgreSQL backup/restore to **isolated** DB, end-to-end full shift and reconciliation.

### P0-E — fiscal compliance decision (external; complexity unknown)
- **Domain/API/UI:** do not implement before accountant resolves responsible issuer, state-specific documents, available integration/provider and contingency.
- **Permissions/audit:** issuer credentials access controlled; electronic document logs must be retained according to accountant/legal guidance.
- **Tests:** if required, signed fiscal acceptance including authorized XML, cancellation, offline contingency, numbering and end-of-day accounting reconciliation. `specs/015` explicitly excludes fiscal documents.

### P0-F — nonfiscal checks/printing (conditional; Spec 015; L)
- **Domain:** ReceiptDocument immutable snapshot, PrinterEndpoint, PrintJob, retries, explicit REPRINT link.
- **API:** authorized generate/check/print/reprint/status health endpoints; idempotency for tickets.
- **Surfaces:** cashier “Ver conta / Imprimir”, Station fallback ticket, print status; continued KDS operation.
- **Permission/audit:** manager reprint reason, no payment marked paid while pending.
- **Tests:** USB/network/Bluetooth installed device, station-printer mapping, duplicate command, printer unplug, crash after spool, multiple simultaneous orders, clear “not fiscal”.

### C0-1 — split/merge and corrections (track 3; Spec 009; L)
- **Domain:** TabTransfer/lines balancing open exposure exactly; leave original Orders/Payments immutable.
- **API:** preview, prepare, commit with version/idempotency and rejection if confirmed-money collision; location move separate.
- **Surfaces:** cashier item selection, 2-column preview, origin/destination receipt; Android quick search.
- **Permission/audit:** manager if threshold or paid tab, immutable source/destination trace.
- **Tests:** 2+ partial payers, duplicate Tab, race split vs payment, merge with guest QR, split with discounts; test algebraic invariant sum effects = 0.

### C0-2 — modifiers/variants (new next priority; Spec 010; L)
- **Domain:** ProductVariant, ModifierGroup/Option, cardinality/availability, cents price delta and immutable snapshots.
- **API:** catalog + order validation and versioned product lookup.
- **Surfaces:** Android staff and Guest stepper with defaults; station displays removals and add-ons prominently.
- **Permission/audit:** catalog edit manager/station capabilities, mark unavailable with actor/time.
- **Tests:** stale modifier, min/max mismatch, single/multiple selection, paid add-on, same item different sizes, kitchen routing, price snapshot after update.

### C0-3 — discounts/courtesy/service (new next priority; Spec 011; L)
- **Domain:** append-only Adjustment and deterministic per-charge allocation, basis points for percentage, no negative payable.
- **API:** quote and post policy effect, reversal; refuse overpayment without compensating refund.
- **Surfaces:** clear cashier total with pre/post service, discretionary removal requiring approval.
- **Permission/audit:** manager reauth thresholds, reason required for courtesy.
- **Tests:** rounding, change after partial payment, refund, item/Tab overlaps, replay and reporting gross/net reconciliation.

### C0-4 / C0-5 — combos and couvert (P1 unless confirmed)
- **Domain/API/UI:** only after representative actual receipt photograph and catalog sample; compositions must route linked OrderItems to correct stations, guest count remains independent of Tabs.
- **Permission/audit:** manager prices/charges, snapshot each effect.
- **Tests:** partial cancellation, paid and unpaid items, multi-station production, order split.

## Recommended implementation order AFTER the 4 existing tracks
1. **Spec 010 variants/modifiers + restaurant-specific combos only if menu requires.**
2. **Spec 011 discounts/courtesy/service charge** and Spec 016 covers/couvert if charged.
3. **Spec 015 nonfiscal customer check + production printer failover**, if paper needed at Aderlan.
4. **Migration import/dry-run + contractual/fiscal integration decision**, supported by accountant/vendor/owner.
5. **Peak load and destructive-failure tabletop test** (Postgres recovery, lost Android, cashier swap, network fail, printer fail, ambiguous payment). Iterate until two-way reconciliation is zero.
Do not postpone P0 external provider/field/fiscal discovery until these tracks finish. Do not automatically build inventory, delivery and ERP.
