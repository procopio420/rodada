# ADR 0013 — Product customization pricing and snapshots

**Status:** Accepted for Spec 010

## Decision

Extend Catalog and Ordering; do not introduce another cart/order/ledger domain.
Variants store an explicit nonnegative base price in cents. Modifier options add
nonnegative cents; REMOVE normally adds zero. The difference between the chosen
variant price and Product price is also captured for historical explanation.
Product price changes therefore do not unexpectedly change an explicitly priced
variant. There is no combinatorial SKU matrix and no Spec 011 repricing.

The shared published catalog contains variants and attached groups/options, including
operational availability, defaults, cardinality, display priority and versions.
Confirmation accepts IDs and exceptional notes, calculates money in the existing
transaction, checks the House Account limit and creates the existing Charges.

OrderItem stores a complete JSON snapshot with plain variant/group/option IDs,
labels, cents, note, quantity and routing. No historical lookup depends on a
surviving variant/option. Model save guards reject changing confirmed identity,
quantity, pricing, customization or routing. Authorized state transitions continue.
Remakes copy that snapshot; replacement of a product requiring choices must use a
new configured confirmation instead of guessing a base configuration.

Confirmation locks its Tab, Products in ID order and ProductAvailability rows.
Configuration and variant/option availability mutations lock all Products in the
Venue in ID order before changing reusable children. This prevents attach/group
edit races and serializes validation with operational changes. This broader lock
is deliberately limited to relatively infrequent catalog mutations; ordinary
orders still lock only the Products they contain. Availability uses expected_version
and audits before/after/reason/actor. Manager/Owner receive both station capabilities;
station operators need an explicit `catalog.availability.bar` or
`catalog.availability.kitchen` allow grant. A shared option spanning stations needs
permission for every affected station.

## Consequences

Existing products have empty customization and retain quick-add. Historical rows
need no customization backfill. Client previews use integer arithmetic but never
send authoritative prices. Idempotency fingerprints preserve selected IDs and notes
and aggregate identical configurations only. Ambiguous Android recovery retains the
complete original payload, even if a product is no longer in the active menu.

Existing Web polling (5 seconds) and Android polling (15 seconds plus resume/reconnect)
refresh availability; confirmation remains immediately authoritative. This branch
does not take ownership of SSE/outbox infrastructure. Large Venues may later need a
more granular reusable-group locking protocol; it must retain the same race guarantees.
