# Spec 017 — Order Corrections & Exception Handling

**Status:** Draft for implementation  
**Owner capability:** Ordering + Fulfillment correction orchestration

## Objective

Define what Rodada does after an ordering/production mistake or customer exception, preserving original OrderItem history while coordinating production, pricing/refund and management facts.

## Product problem

Wrong items, changed minds, rejected dishes and remakes are normal in hospitality. “Editing the old item until it looks right” destroys operational and financial truth. The correction flow must be quick, state-aware and proportionate to impact.

## Scope

- wrong item entered;
- customer change/cancel;
- cancellation after production started;
- rejected ready/delivered item;
- remake/replacement;
- station mistake;
- complaint;
- waste/spoilage marker;
- financial correction;
- authorization/escalation;
- audit and metrics.

## Explicitly out of scope

- structural Tab split/merge/move: Spec 009;
- general discounts/service policy: Spec 011;
- inventory consumption/CMV;
- disciplinary/performance scoring;
- editing confirmed OrderItem snapshot.

## Ownership boundary

Spec 017 answers: **what happened to the ordered/produced item and what corrective action is needed?**

Spec 009 answers: **which Tab currently carries financial responsibility?**

Spec 011 answers: **what discount/courtesy effect applies?**

Spec 006 answers: **was money refunded?**

## Domain concepts

### OrderCorrection

Immutable correction case/action linked to original OrderItem.

Kinds:
- CANCEL_ITEM;
- CUSTOMER_CHANGED_MIND;
- WRONG_ITEM_ENTERED;
- STATION_MISTAKE;
- CUSTOMER_REJECTED;
- REMAKE;
- REPLACEMENT;
- COMPLAINT;
- OTHER_EXCEPTION.

Fields:
- id;
- venue_id;
- original_order_item_id;
- kind;
- stage_at_request;
- requested_by;
- approved_by optional;
- reason_code;
- reason_text optional;
- created_at;
- status: REQUESTED | APPLIED | REJECTED;
- replacement_order_item_id optional;
- financial_disposition;
- idempotency_key.

### FinancialDisposition

Describes orchestration intent, not a second ledger:
- NONE;
- REVERSE_OPEN_RESPONSIBILITY;
- COURTESY_REPLACEMENT;
- REFUND_REQUIRED;
- MANUAL_REVIEW_REQUIRED.

Actual Adjustment/Refund records remain owned by Billing/Payments.

### WasteMarker

Optional operational marker:
- order_item_id;
- correction_id optional;
- kind: PREPARED_NOT_SERVED | REMAKE_DISCARDED | SPOILAGE | OTHER;
- quantity;
- reason;
- actor;
- occurred_at.

It does not decrement inventory in P0.

### Replacement linkage

A remake/replacement is a **new confirmed OrderItem** with its own immutable snapshot and fulfillment lifecycle, linked back to the original correction.

The original item is never reset to NEW/PREPARING.

## Core invariants

1. Confirmed OrderItem product/price/modifier snapshot is never edited in place.
2. Correction never deletes original Order, OrderItem, Charge, fulfillment milestones or delivery task history.
3. A remake/replacement creates new production work.
4. Financial correction is append-oriented through Adjustment/Refund, not Charge/Payment deletion.
5. A correction can be retried idempotently without creating duplicate replacement or reversal.
6. Later production stage requires equal or stronger authorization, never weaker.
7. Waste marker is operational evidence, not inventory/accounting truth.
8. If financial responsibility was transferred by Spec 009, financial reversal applies to the current responsibility lineage while original OrderItem stays historically on its original Tab.
9. A paid/refunded item cannot be “uncancelled” by rewriting ledger history.
10. Metrics distinguish original sale, correction, replacement and courtesy so gross counts are not misread as demand.
11. No correction flow may require workers to manufacture extra status taps for analytics.

## State-aware correction policy

### Draft/unconfirmed

Before Order confirmation:
- freely edit/remove item;
- no OrderCorrection needed because no canonical history exists.

### NEW / ACCEPTED

Typical default:
- STAFF may cancel wrong entry/customer change if no payment complication and within venue threshold;
- reason code required;
- create OrderCorrection;
- transition item to CANCELLED if legal;
- create financial reversal of open responsibility;
- remove/close pending production/delivery work.

### PREPARING

Cancellation/remake becomes operationally costly.

Default:
- MANAGER capability or station-authorized exception policy;
- station receives immediate cancellation signal;
- original item may transition to CANCELLED for active workflow while prior PREPARING event remains;
- optional WasteMarker if preparation/material is discarded;
- financial disposition defined explicitly.

### READY

Customer rejection/change:
- manager approval by default;
- delivery task is resolved/cancelled as exception, not erased;
- WasteMarker likely when item cannot be reused;
- remake creates new OrderItem;
- original READY/milestones remain history.

### PICKED_UP / DELIVERED

Do not roll state backward to make it look unserved.

Create correction/complaint:
- original operational timeline remains;
- replacement/remake may be issued as new item;
- financial action is courtesy/refund/manual review according to settlement state.

## Wrong item entered

If user notices after confirmation:
- use CANCEL_ITEM / WRONG_ITEM_ENTERED;
- do not edit Product/variant/modifiers on original;
- if correct item is still desired, add a new normal OrderItem or replacement linked to correction;
- UI can combine these into one quick “Corrigir item” flow.

## Customer changes mind

Before PREPARING:
- ordinary cancellation policy.

During/after PREPARING:
- show consequence and required authorization;
- venue may choose to still charge, reverse, courtesy or manager-review;
- system does not decide this from production state alone; financial disposition is explicit and policy-validated.

## Modifier mistake

Spec 010 snapshot remains immutable.

Correction flow:
- identify original;
- choose cancel+new item or remake;
- replacement carries corrected modifier snapshot;
- kitchen/bar sees only the new production work plus link “REFAZER de #...”.

## Remake

Use when same intended customer item must be prepared again due to operational issue.

Rules:
- new OrderItem;
- same Product/customization by default, editable if correction requires;
- link correction/original;
- default financial treatment for station mistake: COURTESY_REPLACEMENT (new Charge + matching courtesy under Spec 011) or an equivalent explicit zero-net mechanism approved by Billing;
- original revenue/demand reporting must exclude courtesy replacement from ordinary paid demand where appropriate.

## Replacement

Use when customer receives a different item instead.

Rules:
- new Product/customization snapshot;
- link to original correction;
- financial treatment chosen:
  - charge normally;
  - full/partial courtesy;
  - reverse original + charge replacement;
  - refund original settlement if already paid.

Backend preview shows exact cents before apply.

## Comped replacement

Canonical P0 rule:
- replacement OrderItem is priced normally from Catalog;
- it produces its normal Charge;
- Spec 011 creates explicit COURTESY equal to intended comped amount;
- net customer responsibility may be zero while product/production cost context remains observable.

Do not create fake zero-price Product.

## Financial reversal/correction

### Unpaid/open responsibility

If cancellation policy says customer should not pay:
- resolve current financial owner through Spec 009 transfer lineage;
- create REVERSAL/CORRECTION Adjustment against remaining eligible net responsibility;
- preserve original Charge and existing discounts allocation.

### Confirmed payment exists

If cancellation/rejection requires money back:
- manager-approved correction produces REFUND_REQUIRED preview;
- Spec 006 creates Refund against original confirmed Payment(s);
- no automatic deletion/reassignment of Payment.

If no money is returned (e.g. replacement/courtesy instead):
- use explicit courtesy/adjustment and settlement guard from Spec 011.

## Interaction with transferred items

An OrderItem may have historical origin Tab A but open responsibility transferred to Tab B.

Correction:
- operational history references original OrderItem/Order on A;
- financial-owner resolver identifies B/current lineage;
- reversal/courtesy affects correct current responsibility;
- timeline can show “pedido originado em A, responsabilidade transferida para B”.

P0 transfer remains blocked after confirmed payment per Spec 009, reducing ambiguous cases.

## Production consequences

Correction emits canonical operational facts:
- cancellation requested/applied;
- replacement/remake created;
- waste marked.

Stations:
- see cancellation prominently;
- do not delete old ticket/card from history;
- new remake/replacement appears as new WorkCard with clear linkage.

Dispatch:
- active delivery task for cancelled READY item becomes CANCELLED/resolved-by-exception;
- historical task/milestones remain;
- replacement creates its own delivery lifecycle.

## Approval / escalation

Baseline:
- STAFF: cancel own/new accepted item before PREPARING within configured amount threshold;
- station staff: mark station mistake/request remake;
- CASHIER: financial correction within capability;
- MANAGER: PREPARING/READY/DELIVERED corrections, high-value reversals, complaint settlement, comped replacement;
- OWNER: same.

Spec 013 may configure amount/stage thresholds but cannot bypass hard paid/refund rules.

Reauthentication may be required per Spec 008 for high-value/refund actions.

## API / commands / queries

Commands:
- preview_order_correction(item, kind, proposed_disposition);
- apply_order_correction(... idempotency_key, expected_versions);
- cancel_confirmed_item(...);
- create_remake(...);
- create_replacement(...);
- mark_waste(...);
- resolve_correction(...).

Queries:
- correction_options(item_id);
- correction_history(item_id);
- current_financial_owner(item_id);
- correction_preview financial/production consequences.

Response must state:
- production consequence;
- financial consequence;
- required role/approval;
- exact cents;
- whether refund is needed.

## Concurrency / idempotency

- original item correction version/lock prevents two terminal cancellations;
- same idempotency key cannot create duplicate remake/reversal;
- concurrent remake requests either resolve to same committed correction or conflict;
- financial and operational effects commit atomically where in same database transaction, or use explicit saga/outbox with recoverable intermediate state for provider Refund;
- refund provider side follows Spec 006 idempotency.

## Error/degraded behavior

Corrections are API-required.

Offline:
- user may capture a local note/request, but item is not considered cancelled/remade;
- production must not stop based only on unconfirmed local correction;
- reconnect revalidates current state and authorization.

If station does not receive realtime cancellation but API is healthy, polling/revalidation shows it; manager UI may surface stuck exception.

## UX — Atendimento

Primary action: “Corrigir item”.

Flow adapts to stage:
- NEW/ACCEPTED: quick reason + consequence preview;
- PREPARING/READY: warns “já está em preparo/pronto”, shows manager approval;
- DELIVERED: complaint/replacement/refund choices, never “editar pedido”.

Avoid exposing ledger jargon to staff; show “Cliente deixa de pagar R$ X”, “Novo item sem cobrança adicional”, “Precisa estornar R$ X”.

## UX — Bar/Cozinha

- cancelled item remains identifiable as cancelled;
- remake badge/link to original;
- replacement customization clear;
- waste marker as optional exception action;
- no need to confirm extra metrics in normal path.

## UX — Guest

Guest may request cancellation/change only where venue policy explicitly allows and server says state is cancellable.

Default P0: guest cannot unilaterally cancel a confirmed preparing item; UI offers “Chamar atendimento” when direct correction is unavailable.

Guest sees outcome, not internal staff blame/reason.

## Management

Timeline shows:
- correction kind/stage;
- original item;
- replacement/remake;
- financial disposition;
- waste marker;
- actor/approver;
- timing.

Analytics:
- cancellation rate;
- remake/replacement rate;
- reason categories;
- financial amount reversed/courtesy/refunded;
- stage at correction.

No simplistic leaderboard. Context by station/time/load is required for interpretation.

## Metrics/events

Events:
- order_item.correction_requested/applied;
- order_item.cancelled;
- order_item.remake_created;
- order_item.replacement_created;
- waste.marked;
- complaint.recorded.

Events include correction_id/provenance and link to financial effects where applicable.

## Audit

Always audit applied correction after confirmation, including:
- actor/approver;
- original item;
- stage;
- reason;
- exact financial disposition;
- replacement/waste links;
- timestamp/device/session.

## Security/privacy

- server-side capability checks;
- complaint reason text length-limited and protected from unnecessary guest exposure;
- do not put sensitive personal data in free-text reason;
- staff blame/disciplinary interpretation is outside product scope.

## Migration / backward compatibility

Existing CANCELLED OrderItems remain valid. Where prior history lacks OrderCorrection, expose as legacy cancellation with available AuditEvent provenance; do not fabricate reasons.

## Depends on

- Spec 001 Ordering/Fulfillment/cancellation.
- Spec 003 Dispatch task history.
- Spec 006 Refund.
- Spec 008 permissions.
- Spec 009 transfer lineage.
- Spec 010 customization snapshots.
- Spec 011 Adjustment/courtesy.
- Spec 014 degraded rules.

## Enables

- safe real-world exception handling;
- reliable cancellation/remake analytics;
- non-destructive recovery from mistakes.

## Deliberately deferred

- ingredient inventory write-off;
- automated staff discipline/scoring;
- AI blame/root-cause inference;
- customer self-service cancellation after production start.
