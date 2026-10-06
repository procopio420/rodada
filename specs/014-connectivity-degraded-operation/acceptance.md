# Acceptance — Spec 014

## Realtime outage only

**Given** Redis/WebSocket is unavailable but API is healthy  
**When** staff confirms an Order  
**Then** Order confirms through API exactly once, UI shows realtime degraded/stale state, and other surfaces can recover via polling/revalidation.

## API outage

**Given** API is unreachable  
**When** staff builds an order  
**Then** it may be saved as PendingOrderIntent, but UI must not assign canonical Order status, balance effect or “pedido recebido”.

## Order replay

**Given** a pending order intent and API reconnects  
**When** replay succeeds  
**Then** one canonical Order is created using the original idempotency key and local status becomes CONFIRMED.

## Stale availability conflict

**Given** a pending intent contains an item cached AVAILABLE  
**And** the Product became UNAVAILABLE centrally  
**When** replay occurs  
**Then** server rejects/returns affected item and does not silently substitute or create partial unintended production.

## Duplicate submit prevention

**Given** an Order submit timed out after the server committed it  
**When** client retries with the same idempotency key  
**Then** it receives the existing result and no duplicate Order/Charge is created.

## Tap on Phone ambiguity

**Given** provider submission occurred and connectivity is lost before backend confirmation  
**When** app regains network  
**Then** it reconciles the existing Payment/Attempt; it does not start an equivalent new charge while state is CONFIRMATION_PENDING.

## Pix offline

**Given** a Pix QR is displayed and backend becomes unreachable  
**When** customer pays externally  
**Then** Rodada does not mark Payment confirmed until canonical provider/backend confirmation is received.

## Emergency cash

**Given** API is offline and venue follows emergency cash runbook  
**When** staff records local cash evidence  
**Then** it is visibly PENDING_SYNC and not counted as confirmed Payment/CashShift truth.

**When** reconnect reconciliation finds the Tab balance unchanged and authorization valid  
**Then** exactly one CASH Payment can be created.

## Cash conflict

**Given** offline cash evidence is 5000 cents  
**And** current remaining Tab balance on reconnect is only 3000 cents  
**When** reconciliation runs  
**Then** no automatic 5000-cent Payment is posted; record becomes REQUIRES_REVIEW.

## External terminal fallback

**Given** an external terminal charge occurred during outage  
**When** evidence is captured and synced  
**Then** server creates at most one EXTERNAL_TERMINAL Payment or raises review; it never charges the customer again automatically.

## Guest offline

**Given** guest PWA loses API connectivity  
**When** guest taps submit  
**Then** UI never claims the order was received; payment and service requests remain unconfirmed until server acknowledgment.

## Fulfillment replay

**Given** Class C READY is enabled and a confirmed cached item is marked READY offline  
**When** sync finds the item was centrally cancelled  
**Then** READY event is rejected/conflicted and history is not rewritten.

## Auth revocation

**Given** a pending command was captured by a valid staff session  
**And** membership is revoked before reconnect  
**When** replay occurs  
**Then** backend denies it; command is not reassigned to another operator.

## Reconnect ordering

**Given** two dependent pending commands for the same Tab  
**When** the first conflicts  
**Then** replay stops before applying a later command whose meaning depends on the conflicted state.

## UI freshness

**Given** critical cached financial data is shown offline  
**Then** the screen displays OFFLINE/STALE and last synchronization time, and integrated payment cannot be initiated from that stale amount.

## Audit

**Given** a recovery record is reconciled manually  
**When** audit is inspected  
**Then** original captured_at, applied_at, device, actor, recovery_id, reviewer and reason are recoverable.
