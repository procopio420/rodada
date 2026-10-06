# Plan — Spec 013

## Recommended sequence

1. **Inventory typed config ownership**
   - map each field to venue/floor/catalog/billing/payments/cash/management/access.

2. **Migrations**
   - VenueProfile/operations policy where missing;
   - typed policy/version records;
   - VenueConfigurationChange audit projection.

3. **Domain commands**
   - validate/preview/apply per section;
   - safe-change classification;
   - optimistic versions.

4. **Gerência configuration shell**
   - section navigation;
   - summaries/status;
   - permission-aware actions.

5. **Operational sections**
   - stations/zones/service points/tables/floorplan;
   - guest policy;
   - business date;
   - service/SLA/alerts.

6. **Sensitive sections**
   - staff/devices links to Spec 008;
   - provider binding with secret boundary.

7. **Realtime and rollout**
   - config invalidations;
   - effective-at handling;
   - active-service blocker tests.

## Rollout

Replace hardcoded defaults section by section; do not migrate to a generic JSON column.

## Testing strategy

- role/permission matrix;
- stale-version conflicts;
- active-resource blockers;
- effective-at/business-date boundaries;
- provider secret redaction;
- guest projection isolation;
- backward-compatible defaults.

## Dependencies first

Land each domain owner's validation contract before exposing its config editor. Venue Configuration should not invent semantics the owner spec has not defined.
