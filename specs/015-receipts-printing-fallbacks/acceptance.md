# Acceptance — Spec 015

## Customer check

**Given** an OPEN Tab with confirmed items, discounts, service charge and partial payment  
**When** staff generates a customer check  
**Then** it shows canonical current subtotal/adjustments/confirmed receipts/remaining balance with generation time and non-fiscal labeling.

## Stale check

**Given** a check was generated  
**When** Tab changes later  
**Then** historical check remains unchanged and a newly generated check reflects the new source version.

## Payment receipt

**Given** Payment is CONFIRMED  
**When** receipt is generated  
**Then** it contains safe amount/method/time/reference and no sensitive card data.

## Ambiguous payment

**Given** Payment is CONFIRMATION_PENDING  
**When** user requests definitive paid receipt  
**Then** system refuses or renders pending-status document, never “pago confirmado”.

## Production ticket source

**Given** an unconfirmed cart  
**When** production print is requested  
**Then** no canonical production ticket is generated.

**Given** confirmed KITCHEN OrderItems  
**When** fallback print is requested  
**Then** ticket is rendered from immutable confirmed snapshots including modifiers/notes.

## Retry idempotency

**Given** a production PrintJob times out  
**When** worker retries the same job  
**Then** it remains one logical production ticket/job and does not create a second OrderItem/task.

## Explicit reprint

**Given** an initial production ticket exists  
**When** authorized station staff reprints it  
**Then** a new linked job is created, output is prominently marked REIMPRESSÃO and actor/reason policy is audited.

## Auto-fallback dedupe

**Given** KDS is unhealthy and AUTO_FALLBACK enabled  
**When** repeated health checks observe the same confirmed Order  
**Then** only one initial logical fallback ticket is enqueued for that station/order generation.

## Printer offline

**Given** every printer is OFFLINE  
**When** staff confirms an Order through healthy API  
**Then** canonical Order/Fulfillment still succeeds and UI surfaces print fallback failure without rolling back the sale.

## WebSocket outage

**Given** realtime is down but API healthy  
**When** print is requested  
**Then** printing may proceed through canonical API/job flow.

## Digital receipt authorization

**Given** guest has valid opaque receipt token for their receipt  
**When** they open it  
**Then** only that receipt is returned; guessing another sequential id is not possible.

## Multiple stations

**Given** an Order has BAR and KITCHEN items  
**When** production fallback triggers  
**Then** each station receives only its routed item snapshots through its binding.

## Permission denial

**Given** staff is not authorized to reprint another station's production ticket  
**When** direct API request is made  
**Then** backend denies it and no PrintJob is created.

## Audit

**Given** production reprint and printer binding change occur  
**When** management timeline is inspected  
**Then** actor, time, target and reprint/config provenance are available.
