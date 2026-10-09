-- Read-only canonical reconciliation. Signed transfers cancel at venue scope.
WITH financial AS (
 SELECT t.id, t.state,
   COALESCE((SELECT SUM(amount_cents) FROM ledger_charge WHERE tab_id=t.id),0) AS charges,
   COALESCE((SELECT SUM(amount_cents) FROM ledger_ledgeradjustment WHERE tab_id=t.id),0) AS adjustments,
   COALESCE((SELECT SUM(amount_cents) FROM ledger_payment WHERE tab_id=t.id AND status IN ('CONFIRMED','PARTIALLY_REFUNDED','REFUNDED')),0) AS payments,
   COALESCE((SELECT SUM(r.amount_cents) FROM ledger_refund r JOIN ledger_payment p ON p.id=r.payment_id WHERE p.tab_id=t.id AND r.status='CONFIRMED'),0) AS refunds,
   COALESCE((SELECT SUM(l.amount_cents) FROM tab_operations_tabtransferline l JOIN tab_operations_tabtransfer x ON x.id=l.transfer_id WHERE x.destination_tab_id=t.id),0)
   - COALESCE((SELECT SUM(l.amount_cents) FROM tab_operations_tabtransferline l JOIN tab_operations_tabtransfer x ON x.id=l.transfer_id WHERE x.source_tab_id=t.id),0) AS transfers
 FROM ordering_tab t JOIN venue_venue v ON v.id=t.venue_id WHERE v.slug='release-demo'
)
SELECT state, COUNT(*) AS tabs, SUM(charges) AS charges_cents,
 SUM(adjustments) AS adjustments_cents, SUM(payments) AS payments_cents,
 SUM(refunds) AS refunds_cents, SUM(transfers) AS transfers_cents,
 SUM(charges+adjustments-payments+refunds+transfers) AS exposure_cents
FROM financial GROUP BY state ORDER BY state;

SELECT s.status, s.opening_float_cents, s.expected_amount_cents_snapshot,
 s.counted_amount_cents, s.discrepancy_cents,
 COALESCE((SELECT SUM(amount_cents) FROM cash_cashmovement WHERE shift_id=s.id),0) AS movement_sum_cents
FROM cash_cashshift s JOIN venue_venue v ON v.id=s.venue_id
WHERE v.slug='release-demo' ORDER BY s.opened_at;

SELECT 'duplicate_order_keys' AS check_name, COUNT(*) AS violations FROM (
 SELECT o.tab_id,o.idempotency_key FROM ordering_order o JOIN ordering_tab t ON t.id=o.tab_id
 JOIN venue_venue v ON v.id=t.venue_id WHERE v.slug='release-demo' AND o.idempotency_key<>''
 GROUP BY o.tab_id,o.idempotency_key HAVING COUNT(*)>1
) d
UNION ALL
SELECT 'duplicate_payment_keys', COUNT(*) FROM (
 SELECT p.tab_id,p.idempotency_key FROM ledger_payment p JOIN ordering_tab t ON t.id=p.tab_id
 JOIN venue_venue v ON v.id=t.venue_id WHERE v.slug='release-demo'
 GROUP BY p.tab_id,p.idempotency_key HAVING COUNT(*)>1
) d
UNION ALL
SELECT 'duplicate_item_charges',COUNT(*) FROM (
 SELECT c.order_item_id FROM ledger_charge c JOIN ordering_tab t ON t.id=c.tab_id
 JOIN venue_venue v ON v.id=t.venue_id WHERE v.slug='release-demo'
 GROUP BY c.order_item_id HAVING COUNT(*)>1
) d;
