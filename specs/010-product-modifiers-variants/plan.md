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

## Implemented slices

- Catalog migration 0006 adds ProductVariant, ModifierGroup, ModifierOption and
  ProductModifierGroup with default uniqueness and cardinality constraints.
- Ordering migration 0006 adds customization and fulfillment-station snapshots.
- `catalog/customization.py` owns schema and pricing; configuration and optimistic
  availability commands are in `catalog/customization_views.py`.
- Existing confirmation, financial limit check and exactly-once Charge derivation
  consume calculated snapshots. Historical rendering and remakes use snapshots.
- Native Compose customization and complete encrypted intent recovery extend the
  existing Attendance cart. Guest and Web POS share the same selector/preview.
- Gerência configures existing Product IDs at `/manage/catalog`; Quick Catalog and
  ProductIcon ownership remain unchanged. Bar/Kitchen render options separately
  from exceptional notes and expose versioned option/variant availability actions.
- ADR 0013 records pricing, concurrency, authorization and polling decisions.

## Verification commands

From `apps/api`, use the repository Python environment:

```sh
python manage.py test --settings=rodada_api.settings_test
python manage.py makemigrations --check --dry-run --settings=rodada_api.settings_test
python manage.py migrate --settings=rodada_api.settings_customization_postgres
python manage.py test tests --settings=rodada_api.settings_customization_postgres
```

The customization PostgreSQL settings are test-only and require a dedicated local
PostgreSQL 17 container/database at 127.0.0.1:55449. Never point them at a live database.

```sh
ANDROID_HOME="$HOME/Android/Sdk" ./scripts/android-check.sh
cd apps/web
npm run typecheck
npm run build
RODADA_VISUAL_PORT=3130 RODADA_REFERENCE_PORT=3131 npm run test:visual
RODADA_TEST_PYTHON=/path/to/python npm run test:integration
```

Browser integration also supports the existing `RODADA_E2E_POSTGRES=1` contract with
a dedicated `rodada_web_e2e` database; this delivery verifies it in PostgreSQL as well.
