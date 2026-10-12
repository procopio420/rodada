# Partial cancellation of confirmed order items

Status: accepted. Related specification: Spec 017.

Confirmed quantities and pricing snapshots remain immutable. Each applied pre-fulfillment correction records the cancelled quantity; operational projections subtract applied quantities to show the remaining units. Full cancellation changes fulfillment state only when no units remain.

Partial reversals use a distinct negative ledger adjustment kind so multiple partial cancellations can coexist while retaining existing whole-cancellation uniqueness. Monetary reversal allocates the current net consumption proportionally in cents; cancellation of the final units consumes the remaining cents. Tab/item locks and idempotent correction intents prevent concurrent over-cancellation and duplicate reversals.

Paid items and advanced fulfillment retain their authorized correction flows. Existing production-document snapshots remain frozen; newly generated production tickets use the remaining quantity. Payments are never created or modified by this cancellation flow.
