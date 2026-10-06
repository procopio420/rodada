# Spec 018 — Notifications & Operational Escalation

**Status:** Draft for implementation  
**Owner capability:** Operational alert lifecycle + notification delivery

## Objective

Turn canonical operational exceptions into a coherent alert/escalation model that surfaces the right problem to the right role at the right time without duplicating the Management Cockpit or notifying every normal event.

## Product problem

Rodada already produces facts about fulfillment, payments, guest requests, cash and closing. A busy venue needs actionable exceptions to reach staff/managers without requiring constant dashboard watching. Naive notification systems create alert fatigue, duplicate pushes and inconsistent “truth” separate from the operational modules.

## Scope

- in-app operational alerts;
- manager alerts;
- push delivery;
- severity;
- deduplication;
- cooldown;
- acknowledgement where useful;
- automatic resolution;
- escalation;
- routing by role/capability;
- per-user delivery preferences within policy;
- event provenance;
- lifecycle/history;
- deep links to exact operational context.

## Explicitly out of scope

- duplicating the Management Cockpit read models;
- notifying every order/payment/status event;
- generic marketing notifications;
- customer marketing/push;
- incident-management suite/pager product;
- arbitrary user-authored rule scripting;
- employee surveillance or performance scoring.

## Ownership boundary

Canonical source domains own the facts and conditions:

- Fulfillment/Dispatch own item/task state and timestamps;
- Payments own Payment/Attempt/Refund state;
- Catalog owns ProductAvailability;
- Cash owns shift/count/discrepancy;
- Management owns business-date closing/read models.

Spec 018 owns:
1. evaluation of approved actionable alert rules from those facts;
2. lifecycle of one alert episode;
3. routing/escalation;
4. delivery through in-app/push channels.

Rodada Gerência (Spec 007) **renders the same OperationalAlert records/projections**. It does not maintain a second alert system.

Spec 013 may provide the configuration UI for the typed rules defined here, but Venue Configuration does not own alert semantics.

## Domain concepts

### AlertRule

Typed rule definition, versioned by Venue where configurable.

Conceptual fields:
- id / stable rule key;
- venue_id or system default;
- kind;
- enabled;
- source_scope;
- warning threshold;
- danger/escalation threshold where relevant;
- cooldown;
- routing policy;
- acknowledgement policy;
- push policy;
- configuration version.

Rules are named product concepts, not arbitrary expressions.

Initial kinds:

- FULFILLMENT_SLA_BREACH;
- STUCK_FULFILLMENT;
- EXCESSIVE_QUEUE;
- REPEATED_PAYMENT_FAILURE;
- PAYMENT_CONFIRMATION_PENDING_TOO_LONG;
- GUEST_SERVICE_REQUEST_AGED;
- CASH_DISCREPANCY;
- CASH_SHIFT_NOT_CLOSED;
- STRATEGIC_PRODUCT_UNAVAILABLE;
- DAILY_CLOSING_NOT_COMPLETED.

More rules require explicit product semantics.

### OperationalAlert

One actionable alert episode.

Fields:
- id;
- venue_id;
- rule_key/version;
- subject_type / subject_id;
- context references;
- dedupe_key;
- severity: INFO | WARNING | DANGER;
- status: ACTIVE | ACKNOWLEDGED | RESOLVED | EXPIRED;
- first_detected_at;
- last_evaluated_at;
- last_condition_at;
- acknowledged_by/at optional;
- resolved_at / resolution_reason optional;
- escalation_level;
- provenance references to canonical events/facts;
- deep_link target;
- occurrence/repeat metadata.

### NotificationDelivery

Delivery of an OperationalAlert through a channel.

Fields:
- alert_id;
- recipient_staff_id;
- channel: IN_APP | PUSH;
- delivery_reason: INITIAL | ESCALATION | REMINDER;
- state: PENDING | SENT | FAILED | SUPPRESSED;
- idempotency_key;
- attempted_at / sent_at;
- failure_code;
- suppression_reason.

Delivery failure never changes the underlying OperationalAlert state.

### NotificationPreference

Per StaffMember + Venue preferences for optional delivery categories/channels.

Preferences may reduce push noise where venue policy allows, but cannot:
- hide the canonical in-app alert from an authorized operational surface;
- grant access to alerts the user otherwise cannot see;
- disable mandatory critical routing defined by Venue policy.

## Alert lifecycle

Conceptual lifecycle:

```text
condition false
    |
condition becomes true
    v
 ACTIVE
   |  \
   |   \ acknowledge when rule supports it
   |    v
   | ACKNOWLEDGED
   |      |
   |      | condition still true + escalation threshold
   |      v
   |  ACKNOWLEDGED (higher severity / new escalation delivery)
   |
   +---- condition clears ----> RESOLVED

ACTIVE/ACKNOWLEDGED -- condition becomes irrelevant by expiry policy --> EXPIRED
```

Acknowledgement and resolution are different:
- acknowledge = a human has taken ownership/seen it;
- resolve = the canonical condition is no longer true.

Acknowledgement must never fabricate resolution.

## Alert episodes and recurrence

Dedupe applies while one condition episode is active.

If an alert resolved and the condition later returns:
- create a new alert episode;
- link to previous occurrence when useful;
- do not reopen the old historical alert in place.

This preserves incident history and avoids one forever-growing record.

## Invariants

1. An alert derives from canonical facts/read models; a push payload is never source of truth.
2. One active alert episode exists per dedupe key.
3. Re-evaluating the same unchanged condition is idempotent.
4. Acknowledgement never resolves the source condition.
5. Auto-resolution occurs only when the rule can prove the condition cleared from canonical state.
6. Escalation changes severity/routing on the same active episode; it does not create duplicate alerts for the same condition.
7. Cooldown suppresses repeated delivery, not the underlying active alert.
8. Delivery retry cannot produce duplicate logical push for the same alert/recipient/reason.
9. Role routing is authorization-aware and Venue-scoped.
10. User preference never overrides mandatory critical routing configured by the Venue.
11. Deep links point to a canonical context the recipient is authorized to open.
12. Normal events such as every new Order or every successful Payment do not generate alerts by default.
13. No alert rule may require workers to perform extra taps solely to feed analytics.
14. Resolution/history remains available for Gerência/timeline reconstruction.

## Severity

- INFO: useful actionable context with low urgency; usually in-app only.
- WARNING: attention needed within operational horizon.
- DANGER: sustained/financial/high-impact condition requiring prompt action.

Severity belongs to the alert condition, not the channel.

A push may be reserved for WARNING/DANGER according to rule/routing policy.

## Dedupe key

Deterministic, domain-specific.

Examples:
- fulfillment SLA: rule + station/order_item/task episode;
- excessive queue: rule + station;
- repeated payment failure: rule + Tab or payment context + rolling episode;
- cash discrepancy: rule + cash_shift_id;
- strategic unavailable: rule + product_id;
- daily close missing: rule + business_date.

Dedupe key must not contain secret/customer PII.

## Cooldown

Cooldown controls repeated **deliveries** while an alert remains active.

Example:
- warning push sent at 21:00;
- evaluator runs every minute;
- no new warning push during 20-minute cooldown;
- if severity escalates to DANGER after 8 minutes, escalation delivery may bypass warning cooldown according to policy.

Cooldown never removes the alert from the Cockpit.

## Acknowledgement policy

Acknowledgement is appropriate when ownership matters:
- cash discrepancy review;
- closing not completed;
- sustained payment exception;
- aged guest request/escalated service issue.

It is generally unnecessary for:
- transient excessive queue;
- strategic Product unavailable if the condition itself is visible and self-resolving.

Each rule declares acknowledgement behavior.

Acknowledging may suppress optional reminder pushes for the same recipient/role while the condition remains unchanged, but escalation can still notify.

## Auto-resolution

Examples:
- fulfillment SLA alert resolves when item/task reaches terminal/resolved state;
- queue alert resolves when queue returns below recovery threshold;
- payment confirmation-pending alert resolves when Payment reaches terminal known state;
- product-unavailable alert resolves when Product becomes AVAILABLE;
- cash discrepancy alert resolves only according to cash review policy, not merely because time passed;
- closing alert resolves when canonical daily close is confirmed or an explicit audited exception is accepted.

Use hysteresis/recovery threshold where needed to avoid alert flapping.

## Escalation

Rules may define:
- elapsed-time threshold;
- severity transition;
- expanded role routing;
- optional reminder cadence bounded by cooldown.

Example:
```text
Guest BILL_REQUEST open
  0–5 min    -> no push / visible in Dispatch
  5 min      -> WARNING to STAFF/CASHIER responsible for zone
  10 min     -> DANGER to MANAGER
```

Exact thresholds are Venue-configurable typed values where the rule allows.

Escalation never changes the underlying DispatchTask state.

## Rule semantics

### Fulfillment SLA breach

Source:
- OrderItem/Fulfillment timestamps and configured station SLA.

Condition:
- active item exceeds warning/danger threshold for its current stage.

Do not alert on items already CANCELLED/DELIVERED or corrections that made the stage irrelevant.

Deep link:
- station/order item context.

### Stuck fulfillment

Used when an item remains in one stage materially longer than expected, especially PREPARING/READY.

May share source facts with SLA rule but must have distinct user meaning. Avoid enabling both rules with identical thresholds if they would produce duplicate alerts.

Default P0 recommendation: use one station SLA rule unless a separate stuck semantic is operationally useful.

### Excessive queue

Source:
- station queue projection.

Condition:
- active queue count/age crosses configured threshold for a sustained period.

Use recovery threshold/time to avoid flapping.

Dedupe:
- one active alert per station/rule, not one per item.

### Repeated payment failure

Source:
- PaymentAttempt failures from Spec 006.

Condition:
- N failed attempts for the same Tab/payment context within a configured rolling window, excluding user-cancelled attempts where appropriate.

Normal single decline does not notify manager by default.

Deep link:
- exact Tab/payment history.

### Payment confirmation pending too long

Source:
- Payment CONFIRMATION_PENDING age.

Condition:
- exceeds reconciliation threshold.

Route:
- CASHIER/MANAGER.

Resolution:
- canonical reconciliation to CONFIRMED/FAILED/CANCELLED/refunded terminal path.

### Guest service request aged

Source:
- DispatchTask BILL_REQUEST / SERVICE_REQUEST.

Normal fresh request remains in Dispatch and does not automatically push everyone.

Alert starts only when:
- request crosses configured age/SLA;
- or a DANGER category explicitly demands immediate escalation.

Deep link:
- exact DispatchTask/Tab/location.

### Cash discrepancy

Source:
- closed CashShift discrepancy/review_status from Spec 012.

Condition:
- threshold requires review and review_status=PENDING.

Route:
- MANAGER/OWNER according to policy.

Acknowledgement:
- allowed, but resolution requires review/accepted exception per Cash rules.

### Cash shift not closed

Source:
- active shift crossing expected closing/business-date boundary.

Condition:
- CashShift remains OPEN/COUNTING after configured grace period.

Route:
- CASHIER first, MANAGER on escalation.

### Strategic Product unavailable

Source:
- ProductAvailability.

Only Products explicitly marked in typed alert policy as strategic/alert-worthy are eligible.

Normal item unavailability does not notify management.

Dedupe:
- product + outage episode.

Resolution:
- Product AVAILABLE or alert policy no longer applies.

### Daily closing not completed

Source:
- Management closing status for business_date.

Condition:
- expected close time + grace elapsed without canonical closing confirmation or accepted exception.

Route:
- MANAGER/OWNER.

Do not mark resolved because a notification was acknowledged.

## Routing

Routing targets capabilities/roles, not hardcoded user IDs alone.

Examples:
- zone/station operational alert -> currently authorized STAFF for relevant scope;
- payment exception -> CASHIER + escalation MANAGER;
- cash discrepancy -> MANAGER;
- closing not completed -> MANAGER/OWNER.

If explicit on-duty ownership exists from Dispatch/session context, it may narrow delivery. Absence of ownership falls back to role routing.

An alert must remain visible in Gerência to any authorized manager even if push was routed elsewhere.

## User preferences and noise control

P0 preferences may include:
- push enabled/disabled for optional categories;
- preferred push categories;
- device push registration.

Venue policy defines:
- mandatory critical categories;
- default routing;
- cooldown;
- escalation.

Do not add generic “push every event” preferences.

Quiet hours:
- optional for non-critical off-service pushes;
- DANGER or closing/cash critical routing may bypass quiet hours only if Venue policy explicitly marks it mandatory;
- in-app active alerts are not hidden by quiet hours.

## Push delivery

Push payload should contain minimum useful lock-screen data:
- Rodada/Venue;
- concise condition;
- severity;
- opaque alert/deep-link reference.

Avoid customer names, exact sensitive financial details or secrets on lock screen unless absolutely needed and explicitly safe.

Opening push:
1. app authenticates;
2. fetches current alert/context;
3. checks authorization;
4. if already resolved, shows resolved state/history rather than stale action.

## Deep links

Represent as structured destination, e.g.:
- TAB / tab_id;
- PAYMENT / payment_id;
- FULFILLMENT_ITEM / order_item_id;
- DISPATCH_TASK / task_id;
- CASH_SHIFT / shift_id;
- PRODUCT / product_id;
- DAILY_CLOSE / business_date.

The client maps destination to the correct specialized surface.

Do not persist arbitrary external URLs as operational deep links.

## API / commands / queries

Evaluator/internal commands:
- evaluate_alert_rule(rule_key, subject/fact);
- upsert_active_alert_episode(dedupe_key, condition_snapshot);
- escalate_alert(alert_id, new_severity);
- resolve_alert(alert_id, canonical_reason).

User commands:
- acknowledge_alert(alert_id, actor);
- update_notification_preferences(...).

Delivery:
- enqueue_delivery(alert, recipient, channel, reason);
- record_delivery_result(...).

Queries:
- active_alerts(venue, filters);
- alert_detail(id);
- alert_history(subject/period);
- unread/in-app counts where useful.

## Realtime

OperationalAlert create/update/resolve invalidates:
- Gerência “Agora”;
- relevant operational surface;
- recipient in-app notification center/badge.

If realtime fails:
- alert remains persisted;
- Cockpit recovers via API/polling;
- push worker may continue independently;
- no canonical alert is lost merely because WebSocket is down.

## Concurrency / idempotency

- unique active dedupe key;
- evaluator uses upsert/locking/versioning;
- severity escalation is monotonic within an episode unless rule explicitly de-escalates visually without losing history;
- delivery idempotency key = alert + recipient + channel + delivery_reason + escalation level/cooldown window;
- duplicate source events do not duplicate alerts;
- resolving and escalating concurrently must re-check canonical condition/version.

## Error / degraded behavior

### Alert evaluator delayed
Source domain continues operating. When evaluator resumes, it derives current active condition and may record delayed first_detected_at from source facts where deterministically known.

### Push provider unavailable
- alert remains ACTIVE in-app/Cockpit;
- NotificationDelivery becomes FAILED/retryable;
- retry obeys idempotency/cooldown;
- no operational mutation depends on push success.

### API offline on recipient
Push may arrive, but action opens stale/degraded UI per Spec 014 and cannot perform unsafe mutation until canonical API is reachable.

### Realtime unavailable
API/polling remains authoritative; no duplicate local alert engine.

## Permissions

- authorized staff see alerts relevant to their operational scope;
- MANAGER/OWNER see management alerts;
- acknowledgement requires visibility + rule capability;
- resolving manually is generally not permitted unless the source domain supports an explicit accepted-exception command;
- notification preference edits affect only the current staff member unless manager owns Venue routing policy;
- all authorization is server-side via Spec 008.

## Audit

AuditEvent required for:
- human acknowledgement where operationally meaningful;
- manual accepted exception that resolves a source condition;
- Venue rule/routing changes through the config surface.

Automatic alert creation/escalation/resolution uses immutable alert lifecycle/provenance and technical event history; it need not generate a separate generic AuditEvent for every evaluator run.

## Metrics/events

Events:
- alert.activated;
- alert.severity_changed;
- alert.acknowledged;
- alert.resolved;
- alert.expired;
- notification.delivery_sent;
- notification.delivery_failed/suppressed.

Metrics:
- alert episode count by kind/severity;
- time to acknowledgement when meaningful;
- time to canonical resolution;
- escalations;
- push success/failure;
- suppression/cooldown rate;
- repeated/flapping rule rate.

Do not rank employees by alert count or acknowledgement speed without contextual product spec.

## Security/privacy

- no secret/provider credential in alert payload;
- lock-screen push minimizes customer/financial detail;
- deep-link authorization rechecked on open;
- recipient routing is Venue-scoped;
- preferences do not bypass permissions;
- event provenance stores references/hashes rather than copying sensitive raw payloads where possible.

## Migration / backward compatibility

Spec 007 alert projections/rules migrate into OperationalAlert semantics:
- existing active management alerts map to typed rule + active episode where enough source context exists;
- if exact prior episode provenance is unavailable, keep legacy timeline entries without fabricating acknowledgement/resolution history;
- Gerência switches to the same active-alert query used by notification routing.

## Depends on

- Spec 003 Dispatch facts/SLA context.
- Spec 006 Payment states/attempts.
- Spec 007 Management Cockpit/read models/business date.
- Spec 008 roles/capabilities.
- Spec 012 CashShift/discrepancy facts.
- Existing Catalog ProductAvailability.

## Integrates with

- Spec 011 for financial adjustment/courtesy exception facts where alerting is later justified.
- Spec 013 as the configuration surface for typed rules/routing.
- Spec 014 degraded/reconnect behavior.
- Spec 017 correction facts when a future actionable correction alert rule is introduced.

## Enables

- actionable push without alert fatigue;
- consistent Cockpit + in-app + push semantics;
- escalation of unresolved operational exceptions.

## Deliberately deferred

- arbitrary rule-builder DSL;
- SMS/email escalation;
- customer marketing push;
- external PagerDuty-style incident management;
- predictive/ML alerts.
