# Spec 009 — Tab Operations

**Status:** Draft for implementation  
**Owner capability:** Ordering, with Billing coordination

## Objective

Define safe operational changes to Tabs—move, split, merge, relocate, cancel and reopen—without rewriting confirmed order or financial history.

## Product problem

Busy service creates duplicate tabs, wrong destinations, people changing seats and groups deciding to split. Rodada must make these fixes fast, but a correction cannot make prior Orders, Charges or Payments look as if they originally happened somewhere else.

## Scope

- move a Tab between TableOccupancies / ServicePoints;
- split financial responsibility into another Tab;
- merge duplicate Tabs under safe conditions;
- move selected OrderItem financial responsibility between Tabs;
- partial transfer;
- cancel empty accidental Tabs;
- reopen closed Tabs;
- GuestSession/TabIdentifier handling;
- concurrency, audit and management timeline.

## Explicitly out of scope

- cancelling/remaking a wrong prepared item: Spec 017;
- discount/courtesy/service-charge policy: Spec 011;
- refund mechanics: Spec 006;
- arbitrary accounting journal editor;
- rewriting confirmed Order.tab_id or Payment.tab_id.

## Ownership boundary

Spec 009 owns **structural Tab operations**.

Spec 017 owns **operational correction of what was ordered/produced**.

Spec 011 owns **price effects**.

When an action requires a refund, reversal or courtesy, the respective owner creates that financial history; Tab Operations orchestrates but does not redefine those rules.

## Domain concepts

### TabLocationAssignment

Current location remains a mutable association of Tab to:
- TableOccupancy, or
- ServicePoint, or
- neither.

Historical changes are audit/events, not rewritten Order history.

### TabTransfer

Immutable operation representing movement of open financial responsibility from one Tab to another.

Fields:
- id;
- venue_id;
- source_tab_id;
- destination_tab_id;
- kind: SPLIT | MOVE_ITEMS | MERGE;
- status: PREPARED | COMMITTED | CANCELLED;
- created_by;
- reason optional/required by policy;
- idempotency_key;
- created_at/committed_at;
- source/destination version captured.

### TabTransferLine

References the original economic source without changing it:
- transfer_id;
- source_charge_id and/or order_item_id;
- amount_cents transferred;
- quantity metadata when a whole item quantity maps cleanly;
- original_tab_id.

A committed transfer produces balanced ledger effects:
- negative transfer effect on source Tab open responsibility;
- equal positive transfer effect on destination Tab;
- total Venue receivable is unchanged.

The original OrderItem and Charge stay historically attached to the Tab where they were created.

## Invariants

1. Confirmed Order.tab_id and OrderItem historical ownership are never rewritten by a Tab transfer.
2. Confirmed Payment and Refund records never move between Tabs.
3. A committed transfer changes only open financial responsibility and current operational grouping.
4. Sum of balanced transfer effects across affected Tabs is zero.
5. Transfer amount can never exceed the transferable open amount of the referenced source line.
6. A closed Tab cannot receive new responsibility unless it is explicitly reopened first.
7. Cancelling an empty Tab is allowed only when it has no confirmed Orders, Charges, Payments, Refunds or non-zero Adjustments.
8. Closing/reopening a Tab never releases or recreates TableOccupancy.
9. GuestSession and TabIdentifier never migrate implicitly during split/merge.
10. Every structural mutation is version-checked and idempotent.

## What is persisted vs derived

Persisted:
- TabTransfer + lines;
- balanced ledger transfer entries/effects;
- current Tab location association;
- merge/cancel/reopen linkage/reason;
- AuditEvent;
- explicit identifier/session reassignment actions.

Derived:
- current balance/exposure;
- transferable amount;
- management timeline projections;
- whether a Tab qualifies as empty.

## Location moves

### Move Tab between contexts

Allowed for OPEN or REQUIRES_ACTION Tabs.

Command:
move_tab_location(tab_id, destination_table_occupancy_id?, service_point_id?, expected_version, actor)

Rules:
- no ledger effect;
- no Order/Payment mutation;
- active delivery tasks resolve destination according to canonical current Tab location and must refresh;
- historical events retain old destination context;
- moving to another TableOccupancy requires compatible Venue and active occupancy;
- moving away from an occupancy does not release that occupancy.

Manager permission is not required for ordinary relocation unless Venue policy says so.

## Split Tab

A split creates or chooses a destination OPEN Tab and commits one TabTransfer.

P0 supported split unit:
- complete unpaid charge/order-item responsibility;
- partial amount of a divisible charge only through an explicit amount line.

For hospitality clarity, UI should prefer selecting items/quantities rather than raw ledger amounts.

### Payment restriction

If the source Tab has **any confirmed Payment or confirmed Refund**, item-level/split transfer is blocked in P0 because payment allocation across charges is not yet canonical.

The user sees:
“Esta comanda já tem pagamento confirmado. Para corrigir, estorne/ajuste primeiro ou use o fluxo de correção.”

This deliberately favors financial correctness.

A future spec may introduce canonical payment allocation and relax this rule.

## Move OrderItems / financial responsibility

For confirmed items, “move item” means:
- preserve original OrderItem/Order;
- transfer the selected open financial responsibility through TabTransfer;
- display a provenance marker in both Tabs: “originado na Tab X / transferido para Tab Y”.

Production ownership does **not** move retroactively. Existing fulfillment task/milestones continue linked to the original OrderItem. Current delivery destination may follow the destination Tab only if the transfer is explicitly marked as also changing serving responsibility and item has not reached DELIVERED.

Default P0 behavior: financial transfer does not modify production routing.

## Merge duplicate Tabs

Allowed only when:
- same Venue;
- both Tabs are OPEN/REQUIRES_ACTION;
- neither has confirmed Payments or Refunds;
- no in-flight payment attempt is PROCESSING/CONFIRMATION_PENDING;
- source does not contain unresolved transfer.

Merge semantics:
1. choose survivor destination;
2. transfer all transferable open responsibility from source;
3. optionally move current location to survivor when requested;
4. explicitly reassign selected non-sensitive TabIdentifiers if safe;
5. cancel source with reason MERGED_INTO and pointer to survivor;
6. preserve source history.

GuestSessions are not migrated automatically. They must rejoin/resolve the surviving Tab.

## Partial movement

A selected line may transfer less than its open amount only when:
- the amount is representable in cents;
- resulting source/destination effects remain non-negative where policy requires;
- the UI makes it clear that this is a partial responsibility transfer, not an OrderItem quantity mutation.

If quantity is split for a multi-quantity OrderItem, history records quantity metadata plus exact cents, with cents as financial truth.

## Restrictions after payment/refund

- confirmed Payment: blocks split/merge/move-financial-responsibility in P0;
- confirmed Refund: same;
- PROCESSING or CONFIRMATION_PENDING payment: blocks structural financial transfer until resolved;
- failed/cancelled attempts do not block once terminal;
- location-only moves remain allowed while a payment exists, except a provider flow may temporarily pin operational context if required by adapter UI—not domain identity.

## Accidentally opened Tabs

### Cancel empty Tab

STAFF may cancel their own truly empty OPEN Tab if policy permits; otherwise CASHIER/MANAGER.

Cancellation:
- state -> CANCELLED;
- reason such as ACCIDENTAL_OPEN;
- no deletion;
- identifiers revoked as appropriate;
- TableOccupancy remains untouched.

## Reopen closed Tab

Manager capability required by default.

Allowed when:
- Tab is CLOSED, not CANCELLED;
- reason supplied;
- no currently active incompatible settlement operation;
- business-date closure policy permits correction.

Reopen:
- state -> OPEN or REQUIRES_ACTION based on current exposure;
- records reopened_from_closed_at and actor/reason in audit;
- does not undo Payment, Refund, Adjustment or prior close event.

If the daily close was already confirmed, reopening creates a post-close exception consumed by Spec 007; it does not rewrite the prior close.

## Impact on Orders

- confirmed Orders never change historical tab_id;
- draft/unconfirmed carts may be discarded/recreated under destination Tab because they have no confirmed history;
- delivery/fulfillment remains on original OrderItem;
- UI shows transferred financial responsibility separately from item production history when material.

## Impact on Charges

- original Charge remains on original Tab;
- TabTransfer creates balanced transfer effects;
- charge snapshot is never re-priced by transfer;
- Spec 011 adjustments remain attached to their original basis and may constrain transferability.

## Impact on Payments / Refunds

- never moved;
- any confirmed Payment/Refund blocks financial transfer in P0;
- in-flight ambiguous payment blocks transfer until reconciliation;
- a later refund follows Spec 006 against the original Payment.

## GuestSessions and TabIdentifiers

- location move preserves identifiers because Tab identity is unchanged;
- split creates a new Tab with no inherited identifiers unless explicitly issued;
- merge may reassign revocable technical identifiers only through explicit safe command;
- GuestSession never silently changes its authorized Tab;
- source identifiers are revoked when source Tab is cancelled after merge.

## Permissions

Baseline:
- STAFF: location move; cancel own empty accidental Tab; initiate simple unpaid split if enabled;
- CASHIER: split/move unpaid responsibility and merge unpaid duplicates;
- MANAGER: all above + reopen closed Tab + override restricted structural operation where this spec explicitly permits;
- OWNER: same plus policy configuration.

No role can bypass “do not move confirmed payments/refunds”.

## API / commands / queries

Commands:
- move_tab_location(...);
- prepare_tab_transfer(...);
- commit_tab_transfer(...);
- split_tab(...);
- merge_tabs(...);
- cancel_empty_tab(...);
- reopen_tab(...);
- reassign_tab_identifier(...).

Queries:
- transferability(tab_id);
- tab_transfer_preview(source, destination, lines);
- tab_history(tab_id);
- related_tabs(tab_id) for split/merge provenance.

Preview must return exact cents and reasons for non-transferable lines.

## Realtime

Committed location/transfer/merge/reopen changes invalidate:
- both Tab views;
- relevant Dispatch destination projections;
- guest/staff balance views;
- Management timeline/live snapshot.

Realtime is not transaction confirmation. Clients re-fetch canonical state.

## Concurrency / idempotency

- every command carries idempotency_key;
- source and destination Tabs are locked/version-checked in deterministic order;
- transfer commit and ledger effects occur in one database transaction;
- concurrent transfer of the same responsibility cannot exceed remaining transferable amount;
- merge locks both Tabs;
- stale location move returns current location/version.

## Error / degraded behavior

If API is unavailable:
- no financial Tab transfer/split/merge/reopen is executed offline;
- location-only move may be queued only if Spec 014 classifies it safe and must conflict-check on replay;
- UI never displays a queued split/merge as committed;
- failures show which Tabs remained unchanged.

## UX rules — Atendimento

- “Mover local” is distinct from “Dividir/Mover consumo”;
- split screen defaults to item selection with exact resulting totals;
- paid/ambiguous Tabs explain why transfer is blocked and link to correction/refund path;
- merge requires choosing survivor and shows identifiers/sessions that will not move automatically;
- destructive actions require reason only when policy says or operation is privileged;
- no worker should re-enter every item manually to fix a duplicate Tab.

## Management / timeline

Gerência shows:
- Tab moved;
- split/transfer committed;
- duplicate merged into survivor;
- empty Tab cancelled;
- closed Tab reopened;
with actor, time, reason, source/destination and exact cents when financial.

Historical charts must avoid double-counting balanced transfer effects as new sales.

## Metrics/events

Events:
- tab.location_changed;
- tab.transfer_committed;
- tab.split;
- tab.merged;
- tab.cancelled;
- tab.reopened;
- tab.identifier_reassigned.

Metrics:
- count/reasons of structural corrections;
- transfer amounts;
- reopen count;
- merge count.

Do not build staff leaderboards from correction frequency.

## Security/privacy

- server-side Venue/capability checks;
- guest cannot invoke staff Tab operations;
- identifiers/tokens displayed minimally;
- AuditEvent records actor/session/device per Spec 008;
- reason text is operational data and must not become a place for sensitive customer notes.

## Migration / backward compatibility

Existing Tabs require no rewrite. Add transfer/provenance structures and version field if absent. Existing location association remains current state; future changes begin emitting history.

## Depends on

- Spec 001 Core POS and append-oriented ledger.
- Spec 004 TableOccupancy / GuestSession / TabIdentifier.
- Spec 006 payment/refund states.
- Spec 008 actor/capability foundation.

## Enables

- Spec 017 safe correction orchestration;
- Gerência investigation of structural fixes;
- reliable split/merge workflows for pilot.

## Deliberately deferred

- canonical payment-to-charge allocation;
- moving confirmed payments between Tabs;
- cross-Venue transfer;
- retroactive rewrite of order ownership.
