# Plan — Spec 010

## Recommended sequence

1. **Migrations/domain**
   - ProductVariant;
   - ModifierGroup / ModifierOption;
   - ProductModifierGroup;
   - operational availability fields;
   - OrderItem customization snapshot.

2. **Ordering validator/pricer**
   - server-side cardinality;
   - availability;
   - exact cents;
   - idempotent snapshot + Charge.

3. **Catalog management**
   - configure variants/groups/options;
   - station/manager availability actions.

4. **Atendimento**
   - one-tap quick add when possible;
   - compact modifier sheet when needed.

5. **Guest**
   - same published schema and availability;
   - required-choice validation.

6. **Production surfaces**
   - compact, consistent rendering of variant/modifiers/removals/notes.

7. **Realtime/hardening**
   - availability invalidation;
   - stale cart recovery.

## API contracts

Stabilize a product ordering schema that exposes:
- effective selectable variant set;
- modifier groups/cardinality/defaults;
- price deltas;
- availability/version.

Confirmation sends IDs/selections only; backend computes price.

## Rollout

All existing products remain modifier-free. Add configuration incrementally per Product.

## Testing strategy

- pricing arithmetic;
- min/max and defaults;
- stale/unavailable selection;
- concurrent availability update vs confirmation;
- snapshot immutability;
- guest/staff parity;
- idempotent order confirmation.

## Dependencies first

Spec 001 order confirmation and price snapshot, Spec 005 Catalog identity and Spec 008 authorization.
