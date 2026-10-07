# Acceptance — Spec 018

## SLA alert activation

**Given** a KITCHEN item remains active beyond its configured warning SLA  
**When** the alert evaluator processes canonical fulfillment state  
**Then** one WARNING OperationalAlert episode becomes active with station/item provenance and a deep link to the exact context.

## Dedupe

**Given** the evaluator receives the same SLA condition repeatedly  
**When** it runs ten times  
**Then** there remains exactly one active alert for that dedupe key.

## Escalation

**Given** the same active condition crosses its danger threshold  
**When** reevaluated  
**Then** the existing alert escalates to DANGER, lifecycle history records the change, and expanded routing may enqueue one escalation delivery rather than a duplicate alert.

## Cooldown

**Given** a warning push was sent and the condition remains unchanged inside cooldown  
**When** evaluator runs again  
**Then** no duplicate warning push is sent, while the alert remains visible in-app/Cockpit.

## Acknowledgement is not resolution

**Given** a manager acknowledges a cash discrepancy alert  
**When** CashShift review_status is still PENDING  
**Then** the alert is ACKNOWLEDGED but not RESOLVED.

## Auto-resolution

**Given** a strategic Product unavailable alert is active  
**When** canonical ProductAvailability changes to AVAILABLE  
**Then** the alert auto-resolves and no manual “resolve” tap is required.

## Recurrence

**Given** a Product-unavailable alert resolved  
**When** the same Product later becomes unavailable again  
**Then** a new linked alert episode is created rather than rewriting the old resolved episode.

## Repeated payment failure threshold

**Given** one ordinary declined payment attempt  
**When** no configured repeat threshold is crossed  
**Then** no manager alert/push is created by default.

**Given** the configured number of relevant failures occurs within the window  
**When** evaluated  
**Then** one alert for the Tab/payment context is activated and routed to the configured cashier/manager roles.

## Confirmation pending

**Given** a Payment remains CONFIRMATION_PENDING longer than reconciliation threshold  
**When** evaluated  
**Then** an actionable payment exception alert is active.

**When** payment later becomes CONFIRMED or FAILED canonically  
**Then** the alert resolves automatically.

## Guest service request

**Given** a fresh BILL_REQUEST exists  
**When** it is still inside normal SLA  
**Then** it remains a Dispatch task without notifying every manager.

**When** it exceeds the configured warning/escalation ages  
**Then** alerting routes/escalates according to rule while preserving the original DispatchTask as source of truth.

## Excessive queue

**Given** BAR queue crosses threshold for a sustained interval  
**When** condition activates  
**Then** one station-level alert is created, not one per queued item.

**When** queue falls below the configured recovery threshold  
**Then** the alert resolves without flapping around the same threshold.

## Cash discrepancy

**Given** CashShift closes with review_status=PENDING  
**When** discrepancy rule evaluates  
**Then** manager receives/observes one actionable alert linked to that exact CashShift.

## Closing not completed

**Given** business-date close remains incomplete after configured grace  
**When** evaluated  
**Then** MANAGER/OWNER routing receives an alert linked to that Daily Close, and acknowledgement alone does not mark the close complete.

## Strategic product noise control

**Given** a normal non-strategic Product becomes UNAVAILABLE  
**When** evaluated  
**Then** no management push is emitted solely for that change.

## Push provider failure

**Given** an active DANGER alert and push provider is unavailable  
**When** delivery fails  
**Then** NotificationDelivery records failure/retry state but the OperationalAlert remains active and visible via API/Cockpit.

## Realtime outage

**Given** WebSocket is unavailable  
**When** a canonical alert is activated/resolved  
**Then** API/polling can recover the same state and no client-side duplicate alert is invented.

## Deep-link security

**Given** a staff member receives a push but loses authorization before opening it  
**When** they tap the notification  
**Then** the app reauthenticates/rechecks server authorization and does not expose the protected context.

## Preference boundaries

**Given** a user disables an optional push category  
**When** an INFO/WARNING event in that optional category occurs  
**Then** push may be SUPPRESSED according to policy but the canonical authorized in-app alert remains visible.

**Given** Venue policy marks a DANGER category mandatory  
**When** a user preference would otherwise suppress it  
**Then** mandatory routing wins according to policy.

## Audit/provenance

**Given** an alert was activated, escalated, acknowledged and resolved  
**When** history is inspected  
**Then** canonical source references, rule/version, timestamps, actor for acknowledgement, severity transitions and resolution reason are recoverable.
