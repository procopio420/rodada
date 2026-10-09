# Spec 010 — Product Modifiers & Variants

**Status:** Draft for implementation  
**Owner capability:** Catalog + Ordering snapshot semantics

## Objective

Define hospitality-native customization for menu items while preserving fast ordering, canonical availability and immutable confirmed-order snapshots.

## Product problem

Real bar/restaurant orders need choices such as size, flavor, “sem cebola”, cheese/add-ons and required selections. Free-text notes alone are too ambiguous for pricing, availability, production and guest ordering, but generic ecommerce variant modeling would add unnecessary complexity.

## Scope

- Product variants;
- modifier groups/options;
- required/optional and min/max selection;
- single/multi-select;
- zero/additional price;
- removals/add-ons/flavors/sizes;
- defaults;
- variant/modifier availability;
- snapshot into confirmed OrderItem;
- ordering/editing rules;
- staff/guest production display and ergonomics.

## Explicitly out of scope

- inventory BOM/ingredient depletion;
- arbitrary ecommerce SKU matrix;
- modifier-level tax/fiscal rules;
- automated recipe costing;
- separately fulfilled add-on as a modifier when it is actually another sellable Product;
- retroactive mutation of confirmed item customization.

## Domain distinction

### Product

The menu identity and default sellable item defined by existing Catalog.

Examples:
- Caipirinha;
- Hambúrguer;
- Pizza Margherita.

### ProductVariant

A **single base choice** that materially changes the sellable form before modifiers and may have its own price delta/availability.

Examples:
- Hambúrguer: normal / duplo;
- Pizza: pequena / média / grande;
- Chopp: 300 ml / 500 ml.

Use variants when exactly one base form must be chosen.

Do not create variants for every combination of toppings/removals.

Conceptual fields:
- id;
- product_id;
- name;
- active;
- price_delta_cents or explicit effective price policy;
- sort_order;
- is_default;
- operational availability;
- version.

If a Product has no variants, its current Product price is the base price.

### ModifierGroup

Reusable or product-scoped structured choice:
- id;
- venue_id;
- name;
- selection_mode: SINGLE | MULTI;
- min_selections;
- max_selections;
- required derived from min > 0;
- sort_order;
- allow_duplicates=false by default.

Examples:
- Ponto da carne;
- Adicionais;
- Remover;
- Sabores;
- Molho.

### ModifierOption

Choice inside a group:
- id;
- group_id;
- name;
- price_delta_cents;
- active;
- operational availability;
- default_selected;
- semantic_kind optional: ADD | REMOVE | CHOICE;
- sort_order.

“Sem cebola” should normally be a zero-price REMOVE option, not a negative-price hack.

### ProductModifierGroup

Associates a group with a Product and may override display/order/min/max only when needed.

Avoid copying a group just to change ordering on one Product.

## Variant vs modifier rule

Use **variant** when the customer chooses the base sellable form and exactly one choice defines the starting price/form.

Use **modifier** when the choice customizes that base form.

Examples:
- Chopp size 300/500 ml: variant.
- Pizza size P/M/G: variant.
- Pizza flavor: modifier group, because multi-flavor rules may allow 1–N choices.
- “Sem cebola”: modifier.
- Bacon extra: modifier.
- Drink ice/no ice: modifier.

If two choices must route/fulfill as separate products, create linked OrderItems rather than hiding that production work inside a modifier.

## Invariants

1. Confirmed OrderItem stores an immutable snapshot of Product, selected variant, modifier selections, labels and exact cents.
2. Catalog edits never reprice/relabel a confirmed OrderItem.
3. ProductAvailability UNAVAILABLE blocks every variant/option from new confirmation.
4. A variant/option marked operationally unavailable cannot be newly confirmed even when the UI is stale.
5. Modifier min/max constraints are validated server-side.
6. SINGLE groups allow at most one selection.
7. A default selection is convenience only; confirmation still validates availability and cardinality.
8. Sum of base/variant/modifier cents uses integer arithmetic.
9. Structured modifier exists => staff/guest should use it rather than encode the same request in notes.
10. Notes remain allowed for exceptional, non-priced requests and never override validation or price.
11. Modifier availability changes do not mutate already confirmed items.
12. Fulfillment routing stays owned by Product/OrderItem. A modifier may add preparation text but cannot silently create cross-station work.

## Pricing model

Effective unit price at confirmation:

effective_unit_price_cents =
  product_base_price_cents
  + selected_variant_price_delta_cents
  + sum(selected_modifier_option_price_delta_cents)

All values are integer cents.

Quantity multiplies after unit customization price is resolved unless a future pricing spec explicitly defines otherwise.

Zero-price options are valid and common.

Negative modifier price is disallowed in P0; discounts belong to Spec 011.

## Availability

### Product
Existing ProductAvailability remains top-level gate.

### Variant availability
Variant has operational state AVAILABLE | UNAVAILABLE when variants exist.

### Modifier option availability
ModifierOption has operational state AVAILABLE | UNAVAILABLE.

Operational state is distinct from administrative active/publication, matching ADR 0005.

Authorized station staff may change availability for variants/options whose parent Product routes to their station; MANAGER can manage all.

Every change records actor/time/old/new/reason optional and propagates to all surfaces.

## Confirmation flow

Cart configuration is mutable client state until Order confirmation.

At confirmation, backend:
1. loads Product and operational availability;
2. validates chosen variant belongs to Product and is active/available;
3. validates each group belongs to Product;
4. validates selected options belong to group and are active/available;
5. validates min/max/single/multi;
6. computes cents server-side;
7. persists immutable OrderItemCustomizationSnapshot;
8. creates Charge from the computed snapshot exactly once.

Client-submitted price is never authoritative.

## Snapshot

Conceptual OrderItem snapshot includes:
- product_id + product_name_snapshot;
- base_price_cents_snapshot;
- variant_id nullable;
- variant_name_snapshot;
- variant_delta_cents_snapshot;
- modifier selections:
  - group_id/name;
  - option_id/name;
  - price_delta_cents;
  - semantic_kind;
- unit_price_cents;
- quantity;
- exceptional_note optional;
- routing snapshot required by existing Ordering/Fulfillment.

## Order editing rules

Before confirmation:
- freely change variant/modifiers;
- stale availability may be discovered at submit.

After confirmation:
- do not mutate snapshot in place;
- customer/staff change goes through Spec 017 cancellation/correction/replacement semantics;
- if only a production note can still be safely added, that must be an explicit audited exception defined by Spec 017, not silent snapshot mutation.

## Production semantics

Bar/Kitchen display:
- Product name first;
- variant immediately after product when selected;
- modifiers grouped, concise and ordered;
- removals visually clear (“SEM cebola”);
- exceptional note separated from structured choices.

Example:

Hambúrguer · Duplo
+ bacon
SEM cebola
Molho: barbecue
Obs.: cortar ao meio

Production state remains on OrderItem.

## Guest ordering

- required choices block Add/Confirm until satisfied;
- zero-price choices still show selection state;
- unavailable options remain visible when useful but disabled and labeled;
- price delta is visible before selection/confirmation;
- defaults may be preselected but never hidden;
- notes are secondary under “Pedido especial” or equivalent.

## Quick staff ordering ergonomics

- products with no required choice can quick-add in one tap;
- if all required choices have one valid default, quick-add may use defaults and expose undo/edit immediately;
- otherwise tap opens compact modifier sheet;
- staff should not traverse optional groups unless needed;
- previous configuration may be repeatable only after revalidating current availability.

## API / commands / queries

Queries:
- product_ordering_schema(product_id);
- catalog with variant/option availability;
- modifier group management queries.

Commands:
- configure_product_variants(...);
- configure_modifier_group(...);
- attach_modifier_group(...);
- set_variant_availability(...);
- set_modifier_option_availability(...);
- confirm_order(... selections ...).

Ordering API returns normalized errors:
- VARIANT_REQUIRED;
- VARIANT_UNAVAILABLE;
- MODIFIER_REQUIRED;
- TOO_MANY_MODIFIERS;
- MODIFIER_UNAVAILABLE;
- INVALID_MODIFIER_SELECTION;
- CATALOG_VERSION_STALE where useful.

## Permissions

- STAFF/CASHIER/GUEST: select allowed customization;
- station staff: operational availability for parent station if granted;
- MANAGER: configure variants/groups/options and all operational availability;
- OWNER: same plus venue catalog policy.

Guest never configures catalog.

## Realtime behavior

Variant/option availability changes invalidate:
- Atendimento catalog;
- Bar/Kitchen catalog;
- Guest menu;
- carts containing affected choice show stale status.

Confirmation remains final authority even if realtime is delayed.

## Concurrency / idempotency

- availability mutation uses version/optimistic concurrency;
- confirmed Order idempotency covers full customization payload;
- repeated confirm with same idempotency key creates no duplicate OrderItem/Charge;
- catalog edits concurrent with confirmation resolve by transactional validation of current active/availability state.

## Error/degraded behavior

Offline/degraded ordering follows Spec 014.

For queued safe orders, the server must revalidate Product, variant and modifier availability at replay. A rejected stale customization returns exact affected choices; it is never silently substituted.

## Audit requirements

Audit:
- variant/group/option create/edit/archive;
- availability changes;
- manager configuration changes;
- exceptional post-confirm correction via Spec 017.

Ordinary customer/staff selection of modifiers is persisted in OrderItem snapshot, not duplicated as noisy AuditEvents.

## Metrics/events

Facts:
- order_item.confirmed includes variant/modifier snapshots;
- catalog.variant_availability_changed;
- catalog.modifier_availability_changed.

Metrics may include:
- selection mix;
- modifier attach rate;
- option unavailable time;
- cancellation/remake relation to customization errors via Spec 017.

Avoid inferring inventory usage from modifier counts unless inventory spec exists.

## Security/privacy

- server validates IDs belong to same Venue/Product/group;
- price computed server-side;
- notes are length-limited and treated as untrusted text;
- no HTML execution in production displays;
- guest sees only published ordering schema.

## Migration / backward compatibility

Existing Product without variants/groups remains valid and behaves exactly as today.

Existing OrderItems require no rewrite. New snapshot fields are nullable/empty for historical items.

## Depends on

- Spec 001 Catalog/Ordering/price snapshot.
- Spec 004 Guest Ordering.
- Spec 005 Catalog identity/quick create.
- Spec 008 permissions.

## Enables

- Spec 017 modifier-specific corrections/remakes;
- richer guest ordering;
- future inventory/costing integration without making it a dependency.

## Deliberately deferred

- ingredient-level stock;
- combinatorial SKU matrix;
- negative-priced modifier discounts;
- modifier-specific tax;
- automatic cross-station child item generation.

## Implementation contract

Variants store an explicit nonnegative `price_cents`, replacing the Product base price. Snapshots also record the difference from the Product price. Confirmation accepts additive `variant_id`, `modifier_option_ids` and `special_instructions` (500 characters); no submitted price is authoritative. Products with active variants require an explicit selected ID; defaults are visibly selected by clients. Groups are reusable within a Venue; association sets display priority, with cardinality owned by the group. Archival uses active=false and historical snapshots contain IDs as plain values, never mutable joins. Configuration and confirmation lock Products before child rows; reusable group edits lock all attached Products in ID order. Availability commands require expected_version and audit old/new state and reason. Polling existing catalogs supplies invalidation without adding SSE infrastructure.
