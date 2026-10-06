# Acceptance — Spec 009

## Location move

**Given** an OPEN Tab at TableOccupancy A  
**When** authorized staff moves it to active TableOccupancy B  
**Then** current location becomes B, no Charge/Payment changes, historical events keep prior context, and occupancy A is not released.

## Split unpaid items

**Given** an unpaid Tab with three confirmed items  
**When** cashier selects one complete item and splits it to a new Tab  
**Then** the original OrderItem remains historically on the source Tab, a balanced TabTransfer moves its open financial responsibility, and Venue total receivable is unchanged.

## Partial movement

**Given** a transferable line of R$ 40,00  
**When** R$ 15,00 is moved with a valid explicit partial transfer  
**Then** source responsibility decreases by exactly 1500 cents, destination increases by 1500 cents, and the transfer records provenance.

## Payment restriction

**Given** a Tab with any confirmed Payment  
**When** staff tries to move item financial responsibility or merge it into another Tab  
**Then** the server rejects the operation with a deterministic blocker and no ledger/history changes.

## In-flight payment restriction

**Given** a Payment in CONFIRMATION_PENDING  
**When** a merge is requested  
**Then** the merge is rejected until reconciliation resolves the Payment.

## Merge duplicates

**Given** two unpaid duplicate OPEN Tabs in the same Venue  
**When** cashier merges source into chosen survivor  
**Then** transferable responsibility is moved once, source is CANCELLED with MERGED_INTO provenance, source history remains queryable, and confirmed records are not deleted.

## Guest identity safety

**Given** a GuestSession authorized to the source Tab  
**When** the source is merged into another Tab  
**Then** the GuestSession is not silently rebound to the survivor and must explicitly rejoin/resolve authorized access.

## Cancel accidental empty Tab

**Given** an OPEN Tab with no confirmed Orders, Charges, Payments, Refunds or non-zero Adjustments  
**When** an authorized actor cancels it as accidental  
**Then** state becomes CANCELLED, audit is written, and any TableOccupancy remains unchanged.

## Reject non-empty cancellation

**Given** a Tab with a confirmed Charge  
**When** cancel_empty_tab is requested  
**Then** it is rejected and the user is directed to correction/reversal flows.

## Reopen closed Tab

**Given** a CLOSED Tab with no incompatible settlement operation  
**When** a MANAGER reopens it with reason  
**Then** prior close and payments remain immutable, Tab becomes OPEN or REQUIRES_ACTION according to current exposure, and no TableOccupancy is created/released.

## Post-close reporting

**Given** the business day was already confirmed closed  
**When** a Tab from that day is reopened  
**Then** the original close is preserved and Gerência receives a post-close exception fact.

## Concurrency

**Given** two clients attempt to transfer the same full R$ 30 line concurrently  
**When** both commit  
**Then** at most one can transfer the full amount; the other receives current transferable state.

## Retry/idempotency

**Given** a committed split request  
**When** the same idempotency key is retried after timeout  
**Then** no second transfer or ledger effect is created.

## Permission denial

**Given** an actor without tab.reopen capability  
**When** they call reopen directly  
**Then** the backend rejects it and writes no state change.

## Degraded network

**Given** Atendimento is offline  
**When** staff attempts split/merge/reopen  
**Then** the UI does not claim success or mutate local canonical balance; the operation waits for online execution.

## Audit verification

**Given** a move, split, merge or reopen succeeds  
**When** timeline/audit is inspected  
**Then** actor, time, source/destination, exact amount where applicable and reason/policy context are recoverable.
