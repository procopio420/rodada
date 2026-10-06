# Plan — Spec 016

## Recommended sequence

1. **Domain/migration**
   - PartySizeObservation;
   - target constraint;
   - current/version pointer;
   - no historical backfill.

2. **Commands**
   - active record/correct;
   - guest authorization;
   - manager post-release correction.

3. **Table/Tab surfaces**
   - fast chooser;
   - unknown state;
   - provenance/conflict.

4. **Realtime**
   - occupancy/management invalidation.

5. **Analytics**
   - visit_covers;
   - revenue_per_cover ratio-of-sums;
   - coverage metrics;
   - explicit exclusions.

## Rollout

Start optional. Existing data remains UNKNOWN and reports show coverage from rollout date forward.

## Testing strategy

- multiple Tabs one occupancy counted once;
- no fake default;
- guest/staff concurrency;
- post-release correction;
- analytics denominator/exclusions;
- Tab-without-occupancy fallback.

## Dependencies first

Spec 004 occupancy identity and Spec 007 reporting projection semantics.
