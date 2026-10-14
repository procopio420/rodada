# Acceptance — Spec 009

## Location move

Web T06d criteria (local scope):
- [x] Explicit Tab ID/origin/destination confirmation; only another occupied table is eligible, with no automatic occupancy/release.
- [x] Exact session-scoped replay after lost response/reload and failed readback, without duplicate location/financial effects.
- [x] Gateway rejects financial operations/fields; drafts and Orders/Charges/Payments remain unchanged.
- [x] Mobile 360/390/430, complete visual regression, build/types and PostgreSQL checks pass.

Web evidence: 331 visual tests PASS (7.2m), including 13 new movement scenarios;
one real Web/API PostgreSQL journey covers all three mobile widths, paid/unpaid
Tabs, exact replay/reload, readback failure and financial gateway rejection.
58 API PostgreSQL tests PASS (122.306s); build/types, Ruff and 12 auth/realtime
tests PASS. See Spec026 revalidation.md, T06d Web, for limits and commands.

Spec 026 T06d regression criteria:
- [x] Stale destination generation rejects atomically without changing source location/version, financial records or audit.
- [x] Valid paid and unpaid moves preserve financial snapshots, origin occupancy and optional audit reason.
- [x] Exact concurrent retries produce one operation/assignment/event; release races leave no active assignment to a released occupancy.
- [x] Replay after destination release returns the original response, rechecks authorization and does not resurrect an assignment.

Local evidence: six tests in test_tab_location_safety on disposable PostgreSQL
(17.981s), plus a 57-test hospitality/ledger/tab_operations regression run
(118.264s, including five of those six tests before the final isolation case).
Ruff and Django system/migration checks pass. That backend-only run implies no
Web/device/deploy verification; Web evidence is recorded separately above.
Full details: Spec 026 revalidation.md, T06d backend section.

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

## Verified progress

The backend/API and native Android paths are implemented and exercised; see
[validation.md](validation.md) for commands, test evidence and adjacent-owner boundaries.
PostgreSQL tests cover actual concurrency, not SQLite's lock emulation. Persisted HTTP
workflows include all structural commands and prove independent occupancy lifecycle.
Management reports preserve exposure after merge and do not count transfers as sales.

Additional regression criteria:

- An expired payment with a terminal attempt permits an unpaid transfer; an active
  ambiguous attempt still blocks it.
- A retry after subsequent payment returns the immutable original response, while a
  revoked transfer capability rejects that same retry.
- Concurrent identical splits create one destination, one operation and one transfer.
- Concurrent payment and full split cannot both commit against the same responsibility.
- Failed refresh after Android server rejection retains that rejection and clears stale preview.

### T07d — entrada parcial Android
- [x] Valor inválido/zero bloqueia preview e não vira comando de zero; ponto decimal produz centavos exatos sem commit automático.
Evidência em Spec 026 revalidation.md: Compose em seis configurações e 48 testes PostgreSQL PASS, mantendo contrato server-side e replay existentes.
