# Plan — Spec 018

## Recommended implementation sequence

1. **Domain/migrations**
   - typed AlertRule;
   - OperationalAlert;
   - NotificationDelivery;
   - NotificationPreference;
   - unique active dedupe constraint.

2. **Evaluator foundation**
   - consume canonical facts/outbox/read models;
   - idempotent activate/update/resolve;
   - provenance;
   - severity/cooldown/escalation.

3. **First rule set**
   - fulfillment/queue SLA;
   - payment failure/confirmation pending;
   - aged guest request;
   - cash discrepancy/unclosed shift;
   - strategic product unavailable;
   - closing not completed.

4. **Cockpit integration**
   - migrate Spec 007 active alerts to the same model/query;
   - in-app list/detail;
   - deep links.

5. **Push**
   - device delivery registration;
   - recipient routing;
   - idempotent delivery;
   - privacy-safe payload;
   - retry/failure metrics.

6. **Acknowledgement/escalation**
   - enable only for rules where ownership matters;
   - auto-resolution from source condition;
   - hysteresis for queue/flapping rules.

7. **Configuration integration**
   - expose typed rule/routing fields through Spec 013;
   - user optional push preferences.

## Rollout

Start in-app/Cockpit only. Validate dedupe/resolution quality before enabling push. Enable push rule by rule; never default to “all events”.

## Testing strategy

- duplicate source facts;
- evaluator replay;
- active-key uniqueness;
- severity escalation;
- cooldown suppression;
- ack vs resolution;
- recurrence after resolution;
- source condition clears while delivery pending;
- push provider outage;
- authorization/deep-link tests;
- flapping/hysteresis.

## Dependencies that must land first

Canonical source facts from Specs 003/006/007/012 and authorization from Spec 008. Spec 013 configuration UI can land after the rule contracts are stable.
