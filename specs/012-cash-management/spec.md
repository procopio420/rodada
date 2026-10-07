# Spec 012 — Cash Management

**Status:** Draft for implementation  
**Owner capability:** Cash

## Objective

Expand CashShift into a practical cash-control model for a real bar: opening float, receipts, change, supply, sangria, count, discrepancy, close and review—without becoming accounting software.

## Product problem

Cash is physical and must reconcile with confirmed cash payments and manual drawer movements. A simple “cash total” is insufficient when multiple operators share a drawer, cash is supplied/withdrawn during service, change is given, a shift crosses midnight or the drawer is not closed.

## Scope

- physical cash points;
- opening/closing CashShift;
- opening float;
- cash receipts and change;
- supply and withdrawal/sangria;
- cash count and discrepancy;
- manager review;
- multiple operators;
- late correction;
- daily closing integration;
- permissions, audit and degraded behavior.

## Explicitly out of scope

- bookkeeping/general ledger;
- bank reconciliation;
- accounts payable/receivable;
- payroll;
- armored transport;
- inventory of coins/notes as mandatory workflow;
- fiscal cash-register requirements.

## Domain concepts

### CashPoint

Physical place/drawer where cash is held.

Examples:
- Caixa principal;
- Gaveta bar;
- Caixa móvel 1.

Fields:
- venue_id;
- label;
- active;
- optional device/location association.

A Venue may begin with one CashPoint.

### CashShift

Operational custody period for one CashPoint.

Fields:
- id;
- venue_id;
- cash_point_id;
- business_date;
- status: OPEN | COUNTING | CLOSED;
- opened_by;
- opened_at;
- opening_float_cents;
- closed_by optional;
- closed_at optional;
- counted_amount_cents optional;
- expected_amount_cents_snapshot optional;
- discrepancy_cents optional;
- review_status: NOT_REQUIRED | PENDING | REVIEWED;
- reviewed_by/at/reason optional;
- version.

At most one OPEN/COUNTING shift per CashPoint.

### CashShiftParticipant

Optional persisted association of staff who handled the drawer during the shift. It does not replace actor attribution on each cash mutation.

### CashMovement

Append-only physical cash movement.

Kinds:
- OPENING_FLOAT;
- CASH_PAYMENT;
- CASH_REFUND;
- SUPPLY;
- WITHDRAWAL;
- CORRECTION.

Fields:
- shift_id;
- kind;
- amount_cents signed or direction + positive amount;
- related_payment_id/refund_id optional;
- actor;
- reason_code/text when required;
- occurred_at;
- idempotency_key;
- correction_of_id optional.

No movement is deleted or overwritten.

### CashTenderDetail

For a CASH Payment, optionally records:
- amount_due_cents;
- amount_tendered_cents;
- change_given_cents.

Physical net drawer effect is the confirmed cash Payment amount:
amount_tendered - change_given = payment amount.

This supports “R$100 recebido / R$18 troco” without inflating expected cash.

## Invariants

1. CashPoint has at most one active CashShift.
2. Opening float is persisted once and contributes exactly once to expected cash.
3. Confirmed CASH Payment creates one idempotent CASH_PAYMENT movement in the active shift.
4. Payment amount, not tendered gross, is the net expected-cash increase after change.
5. Supply/withdrawal requires explicit amount and actor; withdrawal always requires reason.
6. Closed shift accepts no ordinary new movement.
7. Late correction never edits the original close snapshot; it creates append-only correction history and a post-close exception.
8. Expected amount is deterministically reconstructible from opening float + movements.
9. Counted amount is human observation and remains distinct from expected amount.
10. Discrepancy = counted - expected at close snapshot.
11. Cash discrepancy is not silently converted into a sale, discount or Payment.
12. Cash operations are scoped to one Venue and one CashPoint.
13. Every movement answers who/what/when/why where required.
14. Daily close aggregates cash shifts but does not rewrite them.

## Opening a shift

Command open_cash_shift(cash_point, opening_float_cents, actor, business_date).

Rules:
- CASHIER/MANAGER by default;
- no other active shift for point;
- opening float >= 0;
- records OPENING_FLOAT movement or immutable opening field exactly once;
- if previous shift is still active, new shift is blocked unless manager resolves/carries over per policy.

A device may be associated for convenience but is not the financial owner.

## Multiple operators

P0 supports shared drawer:
- one CashShift per CashPoint;
- many operators may record cash Payments/movements if authorized;
- every action keeps its actor/session/device;
- primary opened_by does not imply all movement belongs to that person.

Optional CashShiftParticipant may be inferred from actual movements/login context.

Do not use this as employee surveillance/attendance.

## Cash receipt and change

When CASH Payment confirms:
1. Payment belongs to Tab per Spec 006;
2. backend requires an active compatible CashShift or explicit manager fallback policy;
3. CashTenderDetail validates tendered >= payment when tendered is captured;
4. change = tendered - payment;
5. one CASH_PAYMENT movement with net payment amount is created transactionally/idempotently.

If exact cash is entered, tendered may equal payment.

## Supply

Cash added to drawer for operational reasons.

Requires:
- amount > 0;
- actor with cash.supply;
- reason code/text according to policy.

SUPPLY increases expected amount.

## Withdrawal / sangria

Cash removed from drawer.

Requires:
- amount > 0;
- CASHIER/MANAGER capability;
- mandatory reason;
- cannot make expected physical cash nonsensically negative without manager override/explicit correction;
- WITHDRAWAL decreases expected amount.

P0 does not track destination bank/safe as accounting account. Optional note/reference is enough.

## Cash refunds

If a confirmed Refund is physically paid in cash:
- create CASH_REFUND movement exactly once;
- decreases expected cash;
- links Refund;
- authorization follows Spec 006 + cash permissions.

A card/Pix refund does not alter CashShift.

## Counting and close

### Start count

OPEN -> COUNTING.

While COUNTING:
- ordinary cash mutations are blocked or require returning to OPEN before final count;
- UI makes the drawer “em conferência”.

### Count

P0 requires total counted cents.

Optional denomination breakdown may be supported as input aid but the sum is canonical observation.

### Close

COUNTING -> CLOSED in one transaction:
- calculate expected from canonical movements;
- persist expected snapshot;
- persist counted;
- calculate discrepancy;
- determine review_status by Venue threshold;
- emit cash.shift_closed.

The count cannot be silently changed after close.

## Discrepancy

discrepancy_cents = counted_amount_cents - expected_amount_cents_snapshot

Positive = surplus. Negative = shortage.

Cash owns the typed reconciliation policy:
- threshold requiring manager review;
- whether zero/small discrepancy can close without manager at the device.

Spec 013 provides the configuration surface for this policy.

A discrepancy does not create a CORRECTION automatically.

## Manager review

If review_status=PENDING:
- manager sees expected, counted, discrepancy, movements and actor provenance;
- can mark REVIEWED with note/reason;
- review acknowledges/explains; it does not alter expected/count.

If a factual cash movement was missing/wrong, use late correction instead.

## Late corrections

After CLOSED:
- ordinary movement cannot be inserted back in time as if it existed at close;
- authorized manager creates a CashMovement/CashCorrection linked to original movement/shift with occurred_at and recorded_at distinction;
- original expected/count/discrepancy close snapshot stays immutable;
- a derived “corrected expected/discrepancy” may be shown separately;
- daily close receives post-close correction fact.

If physical cash is moved now, that movement belongs to the currently active shift plus a link to the historical correction context where applicable.

## Shift not closed

If a shift remains OPEN past business-date cutoff:
- it remains open; system does not auto-fabricate a close/count;
- Gerência receives actionable exception via Specs 007/018;
- same CashPoint cannot open another shift by default;
- manager may continue/carry the shift or close it with explicit count;
- business-date reporting marks cash position incomplete.

## Daily closing interaction

DailyOperationsSummary consumes:
- shifts opened/closed;
- expected/count/discrepancy snapshots;
- pending reviews;
- unclosed shifts;
- late corrections;
- cash Payments/Refunds.

Daily close cannot claim cash reconciled while required shift review/unclosed state remains unresolved, unless manager explicitly confirms an exception with audit.

## Permissions

Baseline:
- STAFF: collect cash only if venue allows and an active shift context is selected;
- CASHIER: open/operate/count/close shift, supply/withdraw within policy;
- MANAGER: all cashier actions + review discrepancy + late correction + exceptional carryover;
- OWNER: configure policy via Spec 013.

## Commands / queries

Commands:
- open_cash_shift(...);
- record_cash_payment_movement(... internal from payment);
- record_cash_refund_movement(...);
- supply_cash(...);
- withdraw_cash(...);
- start_cash_count(...);
- close_cash_shift(...);
- review_cash_discrepancy(...);
- record_late_cash_correction(...).

Queries:
- active_cash_shift(cash_point);
- cash_shift_position(id);
- cash_shift_movements(id);
- cash_close_preview(id);
- unresolved_cash_exceptions(business_date).

## Concurrency / idempotency

- unique active shift per CashPoint at DB level or equivalent transaction guard;
- Payment/Refund link unique to corresponding cash movement;
- movement commands require idempotency key;
- close uses shift version and locks movement boundary;
- concurrent close vs Payment cannot silently omit/add receipt: either Payment commits before close calculation or fails/retries against closed shift according to transaction ordering.

## Realtime

Cash position updates Gerência/Cashier after:
- cash Payment/Refund;
- supply/withdrawal;
- count/close/review.

Realtime is read invalidation; movements are committed through API/database.

## Error/degraded behavior

- offline integrated/canonical cash receipt follows Spec 014; no client may invent server-confirmed Payment;
- if API unavailable, physical emergency cash sale may follow documented manual contingency, then must be reconciled as explicit external/manual recovery after reconnect;
- supply/withdrawal/count/close are not silently queued unless Spec 014 explicitly permits a safe local capture workflow;
- UI marks unconfirmed local notes as pending, never as expected cash truth.

## UX

Cashier view prioritizes:
- current CashPoint/shift;
- expected amount;
- recent cash movements;
- supply/sangria;
- “Conferir caixa”.

Count screen hides expected amount by default if Venue wants blind count; policy may reveal after submission.

Discrepancy shows exact cents and next action, not a shame/leaderboard signal.

## Metrics/events

Events:
- cash.shift_opened;
- cash.payment_recorded;
- cash.refund_recorded;
- cash.supplied;
- cash.withdrawn;
- cash.count_started;
- cash.shift_closed;
- cash.discrepancy_reviewed;
- cash.late_correction_recorded.

Metrics:
- expected vs counted;
- discrepancy absolute/value;
- unclosed shift count;
- cash payment share;
- supply/withdrawal volume.

Use metrics for control/process diagnosis, not simplistic staff ranking.

## Audit

Every manual cash operation records actor/session/device, amount, CashPoint, shift, timestamp and reason where required.

Close/review/late correction are immutable audit events.

## Security/privacy

- server-side permission checks;
- no sensitive payment card data;
- cash notes length-limited;
- only authorized management sees detailed actor history;
- device binding is provenance, not authority.

## Migration / backward compatibility

Existing basic CashShift rows migrate to one default CashPoint per Venue. Historical shifts may have limited movement detail and are marked legacy/incomplete rather than fabricated.

## Depends on

- Spec 001 CashShift/ledger/AuditEvent.
- Spec 006 Payments/Refunds.
- Spec 008 roles/capabilities.
- Spec 011 pricing only for correct daily closing definitions.
- Spec 007 closing/read models.

## Enables

- reliable pilot cash operation;
- Spec 013 typed cash-policy configuration;
- cash discrepancy alerts in Spec 018;
- trustworthy daily/monthly closing.

## Deliberately deferred

- full accounting;
- bank/safe subledgers;
- mandatory denomination inventory;
- cash forecasting.
