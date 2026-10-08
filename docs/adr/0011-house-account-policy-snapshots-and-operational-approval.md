# ADR 0011 — House Account snapshots and operational approval

**Status:** Accepted

## Decision

Spec 002 uses the existing Tab as the concurrency boundary. Confirmation locks
Tab, resolves idempotent replay, prices the canonical cart and validates projected
ledger exposure before creating OrderItems or Charges. Payment/refund paths that
affect exposure lock Tab before Payment. Product locks use deterministic order.

Customer identity is optional. VenueRelationshipPolicy is snapshotted at opening;
anonymous Tabs use VISITOR. Association or changes to the Relationship never
rewrite snapshots, orders or payments. An authorized reassessment is explicit and
audits previous/new policy. House Account is one modular-monolith capability,
keeping financial totals in the existing ledger.

An override is an append-only operational approval of a total limit with actor,
reason, previous/new amount, creation time, expiry and idempotency key. The latest
approval supersedes previous approvals; expiry does not resurrect an older one.
It requires canonical capability and recent reauthentication at the service and
HTTP boundary. It has no Payment/Refund/Adjustment effect.

Attention is composed of independent reasons. Clearing the spending reason does
not clear a manual review or unresolved correction. Time-based expiry is derived
on every read and confirmation; the persisted operational state is synchronized
on mutations and remains auditable. Polling/revalidation uses the existing HTTP
fallback until the shared realtime infrastructure is available.

## Financial guarantee boundary

No collateral, card credential, identity document or provider authorization is
created by manual approval. A real guarantee requires a separately specified
provider authorization/capture lifecycle (including expiry/reversal) or a
refundable-deposit liability ledger. These dependencies are outside P0.

## Migration

Existing Tabs receive VISITOR/R$30 snapshots. Existing ledger facts stay intact;
over-limit open Tabs need action. Previously unresolved manual attention is
preserved. New policies apply to future Tabs, unless explicitly reassessed.
