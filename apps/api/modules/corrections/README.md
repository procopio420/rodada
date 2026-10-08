# Corrections integration contract

The correction module preserves an immutable explanation for a mistake. It is
not a replacement ledger and never edits `OrderItem` snapshots, `Charge`,
`Payment`, or `Refund` history.

## Simple cancellation boundary

`cancel_before_fulfillment` only accepts `NEW` and `ACCEPTED` items and
requires a reason plus idempotency key. Its mandatory
`financial_reversal_hook(correction, item, actor)` runs in the same
transaction and appends an immutable `LedgerAdjustment` against the existing
`Charge`. If it raises, neither the correction nor the item cancellation
commits. The original charge, snapshot and production history remain intact.

`POST /order-items/<id>/corrections/cancel/` is the staff command for this
path. It is capability-protected (`order.correct`) and always uses the ledger
reversal hook. If the Tab already has confirmed money, it deliberately leaves
the item unchanged and records a `REFUND_REQUIRED` correction request instead.
`POST /corrections/<id>/settle-refund/` is the manager-only,
recently-reauthenticated settlement command. It selects an eligible confirmed
payment explicitly, appends its Refund and the charge reversal in one
transaction, then applies the item cancellation. It works for a partial paid
Tab without fabricating item-level payment allocations: the selected refund may
be smaller than the original Charge, while the full negative adjustment removes
the original responsibility.

## Future hooks

- **Dispatch:** cancelling a READY item is intentionally excluded here; the
  manager stage-aware path must cancel/resolve its delivery task by exception
  without deleting it.
- **Remake/replacement:** `replacement_order_item` links a future newly
  confirmed item; it must receive independent production and financial facts.
