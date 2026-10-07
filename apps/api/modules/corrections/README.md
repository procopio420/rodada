# Corrections integration contract

The correction module preserves an immutable explanation for a mistake. It is
not a replacement ledger and never edits `OrderItem` snapshots, `Charge`,
`Payment`, or `Refund` history.

## Simple cancellation boundary

`cancel_before_fulfillment` only accepts `NEW` and `ACCEPTED` items and
requires a reason plus idempotency key. Its mandatory
`financial_reversal_hook(correction, item, actor)` must run in the same
transaction and append the real open-responsibility reversal against the
current financial owner. If it raises, neither the correction nor the item
cancellation commits.

The current ledger has no append-only Adjustment/reversal primitive yet, so
callers must not expose this command until the hook is supplied by that owner.
It deliberately rejects any Tab with confirmed money because item-level payment
allocation is not yet canonical; that path belongs to manager-approved refund
or courtesy orchestration.

## Future hooks

- **Ordering:** route a staff cancellation command to this service with the
  actor and idempotency key; never add direct `CANCELLED` mutation that bypasses
  the correction fact.
- **Ledger/Spec 011:** implement the reversal hook as an append-only
  Adjustment against current responsibility, then pass it into this service.
- **Dispatch:** cancelling a READY item is intentionally excluded here; the
  manager stage-aware path must cancel/resolve its delivery task by exception
  without deleting it.
- **Remake/replacement:** `replacement_order_item` links a future newly
  confirmed item; it must receive independent production and financial facts.
