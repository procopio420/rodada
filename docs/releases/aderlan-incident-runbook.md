# Aderlan — assisted pilot incident runbook

Assign shift manager as incident commander before opening. Keep deployment/backup credentials
in the secret manager; record IDs and redacted diagnostics, never PINs/tokens/card data.

| Incident | Immediate action | Recovery evidence |
| --- | --- | --- |
| API/network unavailable | Stop new Rodada confirmations. Preserve Android pending intents/keys. Assign one operator to numbered manual contingency records and VR System workflow. | Restore connectivity; reconcile canonical history before replay with identical key. Enter manual consumption once with cross-reference. |
| SSE down, API healthy | Continue canonical HTTP operations; refresh snapshots/poll. Check dispatcher/outbox lag and client reconnect. | Queue/snapshot matches database; bounded resume works without losing events. |
| Payment pending/timeout | Keep Tab open, record intent/reference and responsible cashier. Do not repeat charge or record manual receipt without separate confirmed receipt. | Authenticated provider inquiry/reconciliation or approved support resolution; confirmed ledger appears once. |
| Printer failure before send | Use KDS and inspect retryable job; repair connection. | Same logical job retries with bounded policy. |
| Partial/unknown printer delivery | Pause paper-based production, inspect spool/paper and agree with station what was prepared. No automatic retry. | Explicit linked marked reprint with actor/reason; canonical item remains single. |
| Station KDS outage | Check other eligible devices and canonical queue. Use authorized on-demand tickets/manual station coordination. | Fresh authenticated queue observations and station confirmation. Auto fallback stays disabled. |
| Cash mismatch | Freeze close snapshot, count again with second person; record discrepancy and manager review. | Append correction with reason; original close history remains. |
| Suspected access leak | Revoke session/device/membership and restrict incident scope. | Rejected mutations under revoked and cross-Venue credentials; protected audit retained. |

## Backup and restore

Take backups before release and after close using `pg_dump --format=custom` with protected
connection configuration, encrypt/store off-host, checksum and retention approved by owner.
Never log connection strings. Restore only into a named empty disposable clone; run migrations
checks and compare canonical ledger totals, pending provider references, print jobs and audit.
Record recovery point/time. Restore and restart exercises must not contact live PSP adapters.
Infrastructure evidence records the actual disposable drill; production recovery objectives
and scheduled backup monitoring require deployment owner approval.

## Rollback to VR System

1. Shift manager freezes new Rodada input and assigns a single reconciliation owner. Record
   incident time, deployment SHA and immutable backup/checksum. Preserve database and audit.
2. Export/list all open Tabs, ordered items, adjustments, confirmed payments/refunds, pending
   intents and uncertain print jobs. Match against external terminal receipts/cash evidence.
3. Owner/accountant invokes the agreed incumbent fiscal contingency. Enter remaining unpaid
   consumption into VR System once with Rodada references. Do not collect already received
   money twice. Hold pending payment exceptions for provider reconciliation.
4. Disable Rodada entry/guest ordering using authorized controls, revoke affected sessions and
   keep recovery access restricted. Reconcile any late provider callback before taking payment.
5. Application rollback uses the prior pinned image only after schema compatibility review.
   Never delete migrations or restore an old backup over newer money to make rollback pass.
   If schema is incompatible, preserve data and use forward fix or a tested clone migration.
6. Two operators compare terminal batch, counted cash, Rodada export and VR System records;
   owner approves discrepancies with explicit audit. Return to Rodada requires a fresh manifest,
   passed relevant regression/recovery gates and renewed onsite signoff.
