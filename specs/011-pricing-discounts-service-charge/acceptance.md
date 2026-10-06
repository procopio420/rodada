# Acceptance — Spec 011

## Item percentage discount

**Given** an eligible item net basis of 2000 cents  
**When** an authorized cashier applies 10.00% item discount  
**Then** a -200 cent Adjustment is persisted, the original Charge remains unchanged and payable decreases exactly 200 cents.

## Fixed discount bound

**Given** an eligible Tab basis of 3000 cents  
**When** a 3500-cent fixed discount is requested  
**Then** the server rejects it and no Adjustment is written.

## Courtesy

**Given** a manager grants full courtesy to a 1200-cent item with required reason  
**When** committed  
**Then** the item Charge remains, a -1200-cent COURTESY effect is recorded with actor/reason, and reporting classifies it as courtesy rather than zero-price sale.

## Service charge

**Given** eligible net consumption of 10000 cents and venue default 10.00%  
**When** service charge is assessed  
**Then** SERVICE_CHARGE effect is exactly +1000 cents and no Product/OrderItem is created.

## Service charge after discounts

**Given** gross consumption 10000 cents and 2000 cents of active eligible discounts  
**When** 10.00% service charge is calculated  
**Then** basis is 8000 cents and service charge is 800 cents.

## Reduce service charge

**Given** an active 1000-cent service charge  
**When** authorized staff reduces it to 500 cents  
**Then** original assessment remains queryable and a -500-cent SERVICE_CHARGE_REDUCTION effect records the change.

## Rounding/allocation

**Given** a Tab-level percentage discount whose proportional shares produce fractional cents  
**When** applied  
**Then** largest-remainder allocation is deterministic and allocated cents sum exactly to total discount.

## Permission threshold

**Given** STAFF lacks a requested discount threshold  
**When** they submit it directly  
**Then** server returns APPROVAL_REQUIRED or CAPABILITY_REQUIRED according to policy and no financial effect is committed.

## Manager approval

**Given** an approvable request above cashier threshold  
**When** a manager reauthenticates and approves  
**Then** one Adjustment is created with requester and approver; retrying the same idempotency key creates no duplicate.

## Partial payment safe edit

**Given** payable is 10000 cents and 4000 cents is already confirmed received  
**When** manager applies an Adjustment that leaves payable 8000 cents  
**Then** it may commit if policy permits and remaining balance becomes 4000 cents.

## Partial payment unsafe edit

**Given** 9000 cents already received  
**When** a proposed discount would reduce payable to 8000 cents  
**Then** server rejects with SETTLEMENT_CORRECTION_REQUIRED unless a valid refund/correction orchestration handles the 1000-cent over-receipt.

## Payment stale amount

**Given** a payment screen was opened before a pricing Adjustment  
**When** it attempts to create an integrated payment with stale balance/version  
**Then** backend rejects/revalidates instead of charging the stale amount.

## Refund helper

**Given** an item had allocated discounts  
**When** manager prepares item-based refund  
**Then** refund preview uses persisted net allocations and never refunds the undiscounted list price by mistake.

## Concurrency

**Given** two managers calculate discounts from the same pricing version  
**When** both commit concurrently  
**Then** one succeeds and the stale request must re-preview against the new basis.

## Audit / closing

**Given** discounts, courtesy and service charge occurred during a business date  
**When** daily close is generated  
**Then** gross consumption, each adjustment category, service charge and refunds are separately reconstructible without double counting.
