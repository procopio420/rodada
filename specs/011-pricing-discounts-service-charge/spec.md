# Spec 011 — Pricing, Discounts, Courtesy & Service Charge

**Status:** Implemented; financial acceptance verified
**Owner capability:** Billing / Pricing adjustments

## Objective

Define every non-standard price effect on a Tab with deterministic cents, authorization, audit, refund/reporting semantics and guest/staff presentation.

## Product problem

Bars need discounts, courtesy and service charge, but these cannot be ad hoc edits to Product prices or fake Products. Once payment begins, pricing changes also interact with ledger history and refunds.

## Scope

- item-level and Tab-level discount;
- percentage and fixed discount;
- courtesy;
- default service charge;
- reduce/remove service charge;
- approval thresholds and reasons;
- allocation;
- ledger effects;
- partial payment/refund interactions;
- reporting and closing.

## Explicitly out of scope

- coupons/campaign engine;
- loyalty points;
- tax/fiscal calculation;
- dynamic surge/happy-hour engine;
- accounting GL;
- negative modifier prices;
- tips as service charge (tips remain separate per Spec 006).

## Canonical concept: Adjustment

Expand the existing append-oriented Adjustment concept. An Adjustment is a persisted financial effect; it never rewrites Product price, Charge snapshot or Payment.

Kinds:

- ITEM_DISCOUNT;
- TAB_DISCOUNT;
- COURTESY;
- SERVICE_CHARGE;
- SERVICE_CHARGE_REDUCTION;
- CORRECTION;
- REVERSAL.

Fields conceptually:
- id;
- venue_id;
- tab_id;
- kind;
- scope: CHARGE | TAB;
- source_charge_id optional;
- calculation_type: PERCENTAGE | FIXED | DERIVED;
- requested_value (basis points or cents) where applicable;
- effect_cents signed in ledger convention;
- reason_code / reason_text where required;
- created_by;
- approved_by optional;
- created_at;
- supersedes_adjustment_id optional;
- idempotency_key;
- metadata needed for deterministic allocation.

Service charge is not a Product and does not create an OrderItem.

## Money conventions

- integer minor units only;
- percentage is stored as integer basis points (1000 = 10.00%);
- no float;
- all allocation remainders are deterministic.

## Invariants

1. Product/OrderItem price snapshot is immutable.
2. Discount/courtesy/service charge is represented as Adjustment/assessment effects, never by editing historical Charge.
3. Final eligible consumption cannot become negative.
4. A discount cannot exceed its eligible basis.
5. Courtesy is explicit and auditable; it is not a zero-price Product.
6. Service charge is calculated only on eligible net consumption and never on itself, tips, payments or refunds.
7. Tab-level effects have deterministic per-Charge allocation for reporting/refund.
8. Confirmed Payments are never modified by a pricing Adjustment.
9. If a pricing change would make confirmed receipts exceed the resulting payable amount, it cannot commit silently; it must be combined with/preceded by a valid refund/correction flow.
10. Replaying an Adjustment command cannot apply the effect twice.
11. Reporting distinguishes gross sales, discounts/courtesy, service charge, refunds and received money.
12. Removing service charge never deletes the original assessment; it creates a reduction/superseding history.

## Eligible basis

### Item-level discount

Basis is the targeted Charge amount after any earlier immutable item-specific adjustments in the active chain, excluding service charge.

### Tab-level discount

Basis is the sum of eligible consumption Charges after item-level discount/courtesy and before service charge.

By default:
- consumption Charges are eligible;
- service charge, tips, refunds, prior payments and cash movements are not;
- correction/reversal lines follow their explicit semantic owner.

### Courtesy

Courtesy is a discount with stronger semantic/audit meaning.

P0 supports:
- full item courtesy;
- partial fixed/percentage courtesy;
- Tab courtesy only for authorized manager action.

## Calculation order

Canonical P0 order:

1. confirmed consumption Charges from OrderItems;
2. item-level discounts/courtesy;
3. Tab-level discount/courtesy allocation;
4. service charge assessment on remaining eligible net consumption;
5. service charge reduction/removal;
6. Payments/Refunds affect settlement, not pricing basis.

This order must be shared by backend, receipts and Gerência.

## Rounding and allocation

Percentage calculation uses integer arithmetic.

For a Tab-level fixed or percentage effect:
1. compute total target effect in cents;
2. allocate proportionally to eligible Charge net bases;
3. floor each share;
4. distribute remaining cents by largest fractional remainder;
5. stable tie-break by Charge id/creation order.

Persist the allocation lines so historical/refund/reporting calculations do not change if code changes later.

Total allocation must equal Adjustment effect exactly.

## Service charge

### Venue policy

Billing owns the typed service-charge/discount policy contract:
- enabled;
- default percentage basis points;
- optional maximum;
- whether guest-facing default is opt-out according to venue/legal policy;
- capability/reason thresholds for reduction/removal.

Spec 013 is the configuration surface for this policy; it does not own calculation semantics.

### Assessment

Service charge is calculated from eligible net consumption.

A persisted SERVICE_CHARGE Adjustment records:
- percentage used;
- exact basis cents;
- exact effect cents;
- allocation across eligible Charges.

It may be refreshed while the Tab is unsettled and no historical settlement depends on it, but persistence remains append-oriented: changes create a new superseding assessment/reduction, not destructive overwrite.

### Reduction/removal

Use SERVICE_CHARGE_REDUCTION with negative effect relative to the active assessment.

Examples:
- 10% default reduced to 5%;
- remove service entirely.

Reason may be optional for ordinary customer opt-out and mandatory for manager overrides according to Venue policy.

## Discounts

### Percentage

Store requested basis points and calculated exact effect cents.

Example: 15% of 3333 cents = deterministic integer result according to shared rounding rule.

### Fixed value

Cannot exceed eligible net basis.

### Maximum discount constraints

Venue policy may define:
- STAFF: no manual discount or up to X%;
- CASHIER: up to Y%;
- MANAGER: up to Z% / courtesy;
- OWNER: venue policy maximum.

Absolute hard invariant remains net >= 0.

Thresholds are capabilities/policy, not client UI constants.

## Approval

An Adjustment can require approval.

P0 flow:
- actor requests action;
- server checks capability/threshold;
- if actor lacks threshold but request is approvable, return APPROVAL_REQUIRED with preview;
- authorized manager reauthenticates if Spec 008 policy requires;
- one commit records requested_by and approved_by.

Do not create an applied Adjustment before approval.

## Reason requirements

Reason required for:
- courtesy by default;
- discount beyond configured threshold;
- post-payment pricing correction;
- service charge override outside ordinary opt-out policy;
- reversal/correction.

Use structured reason_code plus optional short text where practical.

## Interaction with partial payment

Partial payment does not freeze the entire Tab, but a later Adjustment must preserve settlement correctness.

Allowed after partial payment only if:
- resulting payable >= confirmed net received after refunds;
- no in-flight ambiguous Payment is invalidated by changed requested amount;
- policy permits.

Otherwise return SETTLEMENT_CORRECTION_REQUIRED and require refund/reconciliation orchestration.

## Interaction with Tab Operations

Spec 009 transferability must use **net allocated open responsibility** after active pricing adjustments.

P0 rule from Spec 009 still blocks financial split/merge when any confirmed Payment/Refund exists.

When moving an adjusted unpaid Charge:
- the associated allocated discount/courtesy follows that responsibility proportionally and immutably through transfer metadata;
- Tab-level service charge is recalculated as a new assessment on each affected Tab only when transfer rules explicitly allow and before payment;
- no original Adjustment is deleted.

## Refunds after discounts

Refund remains owned by Spec 006 and references Payment.

For item-based refund assistance:
- refundable consumption value uses the persisted net allocation after discounts/courtesy;
- service-charge refundable share uses persisted service allocation and venue policy;
- backend returns exact preview;
- final Refund never exceeds confirmed Payment/refundable balance.

Pricing history remains intact; refund adds reverse settlement history.

## Ledger effects

Conceptually:
- Charge: positive consumption;
- discount/courtesy Adjustment: negative effect;
- service charge Adjustment: positive effect;
- service charge reduction: negative effect;
- Payment confirmed: reduces open balance;
- Refund confirmed: increases open balance / reverses received money per canonical ledger.

Exact sign representation may follow existing ledger implementation, but formulas and report categories must remain semantically distinct.

## Commands / queries

Commands:
- apply_item_discount(...);
- apply_tab_discount(...);
- grant_courtesy(...);
- assess_service_charge(...);
- reduce_service_charge(...);
- reverse_adjustment(...).

Queries:
- pricing_preview(tab_id);
- adjustment_policy(actor, venue, tab);
- refundable_item_value(...);
- adjustment_history(tab_id).

Every command accepts idempotency_key and expected Tab/pricing version where relevant.

## Permissions

Baseline:
- STAFF: no manual discount by default; may honor ordinary service-charge opt-out if venue policy allows;
- CASHIER: configured low-threshold discounts and service-charge reduction;
- MANAGER: larger discounts, courtesy, reversals;
- OWNER: configure policy and perform manager actions.

Server-side capability + threshold checks are mandatory.

## Realtime

Applied pricing changes invalidate:
- Staff/Guest Tab totals;
- payment amount screens;
- receipt/check previews;
- Management live finance projections.

A payment screen with stale total must revalidate before creating a new payment intent.

## Concurrency / idempotency

- pricing mutations lock/version the Tab pricing state;
- concurrent discount/service-charge edits cannot both calculate from stale basis silently;
- idempotency key deduplicates command;
- allocation persistence and ledger effect commit in one transaction;
- in-flight payment amount mismatch returns conflict rather than silent repricing.

## Error / degraded behavior

No new discount/courtesy/service-charge mutation is committed offline.

Cached receipt/check may show “valor desatualizado” if stale; payment creation must fetch/revalidate canonical amount.

If approval service/API is unavailable, do not locally assume manager approval.

## UX — Atendimento/Cashier

- show original subtotal, each adjustment and final payable;
- item discount action is attached to item;
- Tab discount/courtesy is separate from payment;
- service charge has its own row and reduce/remove action when allowed;
- approval flow does not force re-entry of the amount;
- always preview “antes → depois” before privileged commit.

## UX — Guest

Guest sees:
- consumption subtotal;
- discounts/courtesy with understandable labels;
- service charge as a separate row;
- final total.

Do not expose internal approval metadata or staff reason text.

If guest can request removal under venue policy, that request still executes server-side policy.

## Management / reporting

Daily/monthly closing must expose at least:
- gross consumption;
- item discounts;
- Tab discounts;
- courtesy;
- service charge assessed;
- service charge reductions/removals;
- net sales definition;
- refunds separately;
- received by method.

Never count service charge as Product sales or inflate item mix.

## Metrics/events

Events:
- adjustment.created;
- adjustment.reversed;
- pricing.approval_required;
- service_charge.assessed;
- service_charge.reduced.

Metrics:
- discount/courtesy amount and reason categories;
- service charge assessed vs reduced;
- approval frequency;
- net/gross definitions.

Do not rank staff by discount/courtesy usage without context.

## Audit

Every applied/reversed Adjustment records:
- requester;
- approver if distinct;
- session/device;
- exact basis/value/effect;
- scope and target;
- reason where required;
- timestamp;
- superseded/reversed relationship.

## Security/privacy

- client cannot submit authoritative effect cents without server recomputation/validation;
- authorization/thresholds server-side;
- reason text escaped/length limited;
- no financial mutation from guest beyond explicitly allowed service-charge policy.

## Migration / backward compatibility

Existing COURTESY/CORRECTION/REVERSAL Adjustments remain valid.

Migration adds kind/scope/calculation/allocation fields with historical mapping. Historical records are not reclassified beyond deterministic mapping from known data.

## Depends on

- Spec 001 Charges/Adjustment/ledger.
- Spec 006 Payments/Refunds.
- Spec 008 auth/capabilities.
- Spec 009 transfer rules for adjusted responsibility.

## Enables

- Spec 012 accurate cash/closing summaries;
- Spec 013 typed pricing/service configuration UI;
- Spec 017 comped replacement/correction;
- Spec 007 reliable gross/net reporting and closing.

## Deliberately deferred

- promotion/coupon engine;
- time-based price schedules;
- taxes/fiscal;
- loyalty;
- accounting allocation beyond operational reporting.

## Executable contract (2026-10-09)

Percentages round half up: `(basis * basis_points + 5000) // 10000`.
Persist largest-remainder allocations with UUID lexicographic tie breaking.
The existing LedgerAdjustment table is extended; legacy correction records and
constraints retain their meaning. Append-only PostgreSQL triggers protect adjustment
facts and allocations against UPDATE/DELETE. Typed venue policy defaults to disabled
service; rates, maximum discount, staff/cashier thresholds, post-payment permission,
removal authority and service accounting/refund treatment are explicitly configurable.
Policy updates require expected version and recent privileged reauthentication.

Commands lock the Tab and require expected_version. Retries compare the full intent
fingerprint before version validation and reauthorize. Pending/ambiguous payments and
pending refunds block pricing. Discounts that exceed net consumption or produce
payable below net confirmed receipts fail atomically. Manager approval stores the
request and exact preview without applying money; approval commits only the original
request at its original version, with both actors recorded.

An assessment is a snapshot, not a silently changing default. Once assessed, new
orders or discounts require explicit refresh; payment and close reject stale service
basis. Refresh appends a full reduction of the prior active service and a new
assessment in the same transaction. Reductions remain explicit and never create a
Product. Service is operationally separated from consumption; policy records
REVENUE or PASS_THROUGH without claiming fiscal/GL compliance.

Unpaid transfers persist gross, discount/courtesy and service components per line,
proportionally with deterministic cents. Their sum equals transferred payable.
Allocated effects travel with responsibility, including service; rates are not
silently changed by split/merge. Reassessment is explicit on each Tab. A reversal
whose allocations have been transferred is rejected pending allocation-aware
correction; historical facts remain intact. Confirmed money still blocks transfers.
Refund assistance gives current net consumption and configured refundable service
share, bounded by net receipts; payment-to-item settlement is not inferred.

Pricing invalidation uses existing bounded HTTP refresh on this branch. No new
transport or provider SDK/printing changes are introduced. This PR stacks on Spec 010.

Service removal has a separate `service_removal_requires_manager` policy flag
(default true); authorized opt-out remains governed by `service_opt_out`.
Item adjustment selectors show the captured product name and original amount.
