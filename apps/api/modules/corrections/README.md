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
the item unchanged and records a `REFUND_REQUIRED` correction request instead;
it must be resolved by the manager refund/courtesy workflow, never by guessing
item-level payment allocation.

## Future hooks

- **Dispatch:** cancelling a READY item is intentionally excluded here; the
  manager stage-aware path must cancel/resolve its delivery task by exception
  without deleting it.
- **Remake/replacement:** `replacement_order_item` links a future newly
  confirmed item; it must receive independent production and financial facts.
