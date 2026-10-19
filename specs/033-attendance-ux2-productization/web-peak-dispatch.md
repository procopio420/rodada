# E03-07 / E06 — persisted peak queue validation

Audit: both canonical Dispatch endpoints return up to200 records; each Web queue
renders every returned task and has an independent15-second HTTP fallback. Fifty
READY plus fifty service calls fit the existing contract. No new endpoint,
pagination abstraction, task tap or KPI completion is needed.

Add test-only persisted fixtures:50 actual READY OrderItems/delivery tasks plus
50 service requests across50 active TableOccupancies/five zones. Create tasks via
the existing READY service and actual database records, never fabricated HTTP
queue payloads. Zero-price items/zero charges make this navigation/freshness proof,
not evidence of financial settlement or normal order production transitions.

At360/390/430/desktop, verify actual queue counts/zones, open the final canonical
tasks and Back without mutations, force only HTTP503, retain cached50 rows with
unknown counters, recover through HTTP refetch, and prove all task/item/ledger/
payment snapshots unchanged. Existing real-order-during-Dispatch503 tests cover
the separate sale-continuation invariant. No global acceptance from this slice.
