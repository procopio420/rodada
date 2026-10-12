# Plan — Spec 016

2026-10-10 frontend: reuse Field/Button/notice in an occupancy-scoped component.
GET current/history, show source and current count; POST explicit version/key.
Tests cover unknown, stale conflict and lost-response retry. Expand only the
attendance gateway party-size path, preserving financial exclusions.

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

## Release candidate backend slice — 2026-10-09

PartySizeObservation is append-only with exactly one occupancy/Tab target, explicit positive count, target-locked version conflict, unique request key, actor/source and supersedes history. Staff and guest commands use existing capabilities/current GuestSession context. Released occupancy corrections require manager/owner and reason. Release AuditEvent freezes the observation reference/count, preserving the original snapshot after correction. Table occupancy queries and guest context expose additive party_size; public guest responses omit private staff/session provenance.

Metrics helper accepts only caller-provided canonical eligible revenue attribution, computes ratio-of-sums and coverage/exclusions, and never guesses revenue from a Tab's present location. It is not yet wired into management reporting. Native/staff/guest chooser UX and offline drafts remain open; task checkboxes are not comprehensive release evidence. PostgreSQL concurrency tests exercise guest/staff same-version writes.
