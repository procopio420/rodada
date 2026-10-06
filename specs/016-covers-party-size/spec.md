# Spec 016 — Covers / Party Size

**Status:** Draft for implementation  
**Owner capability:** Floor / visit analytics

## Objective

Define a canonical, honest meaning for number of people (“covers”) without assuming one Tab equals one person or fabricating precision when the count is unknown.

## Product problem

Gerência wants ticket/revenue per person and occupancy insight, but Rodada allows multiple Tabs in one TableOccupancy and Tabs without tables. Counting Tabs, identities or orders as people would be wrong.

## Scope

- party size / covers;
- TableOccupancy relationship;
- optional Tab relationship when no occupancy exists;
- guest/staff capture;
- correction/provenance;
- unknown state;
- analytics definitions.

## Explicitly out of scope

- seat-by-seat ordering;
- mandatory customer identity;
- facial/person counting;
- automated camera/BLE people counting;
- one Tab = one person assumption;
- payroll/staff counts.

## Canonical concept

### PartySizeObservation

Append-only observation/correction of party size.

Fields:
- id;
- venue_id;
- target_type: TABLE_OCCUPANCY | TAB;
- target_id;
- covers_count positive integer;
- source: STAFF | GUEST | IMPORTED;
- staff_member_id nullable;
- guest_session_id nullable;
- observed_at;
- recorded_at;
- supersedes_id nullable;
- note/reason optional;
- confidence is not used in P0 because counts are explicit, not inferred.

Current party size is the latest valid non-superseded observation for the target.

No observation means **UNKNOWN**, not zero.

## Target rules

### TableOccupancy

Primary canonical target when physical occupancy exists.

One TableOccupancy represents the party/group context and may contain multiple Tabs.

All Tabs in the occupancy share the same party-size context for visit-level cover analytics. They are not each counted separately.

### Tab

A Tab-level PartySizeObservation is allowed only as a fallback for Tabs with no TableOccupancy when staff/guest explicitly knows group size.

If a Tab later joins a TableOccupancy:
- occupancy-level covers become canonical for physical/visit analytics;
- Tab observation remains historical provenance;
- do not sum Tab count with occupancy count.

## Invariants

1. Covers are never derived from number of Tabs.
2. Covers are never derived from number of identified Customers.
3. UNKNOWN is distinct from 0; 0 is not a valid active party size.
4. Multiple Tabs sharing one occupancy share one cover count for occupancy analytics.
5. Corrections append a new observation and preserve the prior one.
6. Closing a Tab does not finalize/release occupancy covers by itself.
7. Releasing TableOccupancy snapshots the latest known covers for visit reporting; later authorized correction remains possible with provenance.
8. Guest-provided count is explicit provenance and may be corrected by staff.
9. Analytics using covers must report data coverage/exclusions when some visits are UNKNOWN.
10. No financial amount is changed by editing covers.
11. Orders/payments never require Customer identity because covers are known.

## Optional vs required capture

Default P0:
- capture is optional;
- unknown count must not block opening Tab, confirming Order or payment.

Venue may configure “prompt for covers” for dine-in/occupancy flows, but P0 should not hard-block operational service solely because count is missing.

If a venue later requires count, the rule belongs to typed configuration and must still provide manager exception; it is not a hidden frontend requirement.

## Initial value

Possible capture moments:
- staff starts TableOccupancy;
- guest DIRECT flow starts occupancy;
- staff opens a table-associated Tab;
- later from occupancy detail.

UI offers common values quickly (1–8 plus manual), but no default fake value of 1.

## Later correction

Any authorized staff can correct current active occupancy count.

After occupancy release:
- MANAGER may correct for factual error;
- correction requires reason;
- analytics projection rebuilds/adjusts;
- original observation/release snapshot remains auditably traceable.

## Guest-provided value

Guest may submit covers only for:
- valid GuestSession;
- current active/table-start flow;
- their resolved TableOccupancy/Tab context;
- before staff policy locks the field.

If staff has already recorded a newer value, guest stale update conflicts rather than overwriting silently.

Guest-provided value is not less “real” by definition, but provenance remains visible to staff/analytics quality.

## Staff-provided value

Staff can:
- set initial;
- correct;
- confirm guest value.

A confirmation action is not required in happy path; provenance alone is sufficient unless venue config asks for review.

## Who may edit

Baseline:
- STAFF/CASHIER: active occupancy/own operational context;
- MANAGER: all active + post-release correction;
- OWNER: same;
- GUEST: own active context under guest policy.

All checks are server-side through Spec 008/GuestSession authorization.

## Commands / queries

Commands:
- record_party_size(target, count, expected_version, source);
- correct_party_size(target, count, reason, expected_version);
- optionally accept_guest_party_size(...) if policy introduces review.

Queries:
- current_party_size(target);
- party_size_history(target);
- occupancy_cover_metrics(period).

Normalized errors:
- INVALID_COVER_COUNT;
- STALE_PARTY_SIZE;
- TARGET_RELEASED;
- GUEST_NOT_AUTHORIZED;
- MANAGER_REQUIRED.

## Concurrency

Target has version/current observation pointer.

If guest and staff submit concurrently from same version:
- one succeeds;
- other receives current value/provenance;
- no last-write-wins silent overwrite.

Idempotency key prevents duplicate observation from retry.

## Realtime

Party-size change invalidates:
- occupancy/table detail;
- guest context if visible;
- Management live occupancy metrics;
- affected analytics projection.

No other operational state depends on realtime delivery of covers.

## UX — Atendimento / Table Ops

- show “Pessoas: —” when unknown;
- tap opens fast count chooser;
- do not force a long form;
- if guest supplied: small provenance label when useful;
- correction is one compact action;
- never display “1 pessoa” merely because one Tab exists.

## UX — Guest

If requested:
- simple “Quantas pessoas estão com vocês?”;
- allow skip when optional;
- explain only as service context, not identity collection;
- later edit while authorized.

## UX — Gerência

Metrics with covers show:
- covers known;
- unknown visits;
- coverage percentage;
- revenue/ticket per cover only over defined known-cover population.

Do not show decimals implying precision if sample coverage is poor without an accompanying coverage warning.

## Analytics semantics

### Visit covers

For a released TableOccupancy:
visit_covers = latest valid covers_count effective at release, or UNKNOWN.

A post-release factual correction supersedes the value for rebuilt analytics while retaining audit provenance.

### Revenue attributed to occupancy

Revenue uses canonical financial allocation of Tabs associated with that occupancy according to event/time attribution policy defined by Gerência. Moving a Tab later must not blindly move historical revenue; use persisted occupancy/location facts.

P0 may restrict “revenue per occupancy cover” to Tabs whose relevant consumption is unambiguously associated with that occupancy.

### Ticket/revenue per cover

For a period:
revenue_per_cover =
  sum(eligible net revenue for known-cover visits)
  / sum(covers for those visits)

Do not average visit-level ratios unless explicitly labeled.

Report:
- numerator;
- known covers;
- count of known vs unknown visits;
- coverage percentage.

### Tab without occupancy

If explicit Tab covers exist and the Tab never belongs to occupancy, it may contribute to non-table cover analytics.

Never combine both Tab and occupancy covers for the same consumption.

### Occupancy metrics

Unrelated metrics such as:
- occupancy duration;
- table turnover;
- cleaning time
do not require covers.

Cover-density metrics require known count and must expose coverage.

## Persisted vs derived

Persisted:
- PartySizeObservation history;
- current pointer/version if useful;
- release-time snapshot/reference.

Derived:
- current count;
- known/unknown;
- analytics ratios;
- coverage metrics.

## Error/degraded behavior

Recording/correcting covers is API-required.

If offline:
- UI may keep local draft;
- it is not canonical until replay;
- ordering/payment remain usable according to Spec 014 rules and are not blocked by unknown covers.

## Metrics/events

Events:
- party_size.recorded;
- party_size.corrected;
- occupancy.released includes party_size reference/snapshot when known.

Metrics:
- known covers;
- unknown cover visits;
- data coverage;
- revenue/ticket per known cover;
- covers per occupancy where known.

Do not produce staff performance metrics from who entered/corrected covers.

## Audit

Active ordinary count capture may rely on observation provenance rather than separate noisy AuditEvent.

Corrections, especially post-release, must record actor/source, old/new count, time and reason where required.

## Security/privacy

Covers are operational count, not identity.

Do not require names/phone/CPF to count people. Guest authorization remains scoped through Spec 004.

## Migration / backward compatibility

Existing TableOccupancies/Tabs have UNKNOWN covers. Do not backfill 1 or infer from Tab/Customer count.

Historical analytics must label pre-capture periods as missing data.

## Depends on

- Spec 004 TableOccupancy/GuestSession.
- Spec 008 staff authorization.
- Spec 007 management analytics definitions.
- Spec 009 location/history semantics for attribution.

## Enables

- honest ticket/revenue per cover;
- better occupancy/capacity analysis;
- future staffing/capacity insights without identity requirements.

## Deliberately deferred

- seat-level identity;
- inferred people counting;
- camera/BLE counting;
- mandatory covers for all service modes.
