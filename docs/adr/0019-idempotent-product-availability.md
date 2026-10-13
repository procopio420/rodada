# Versioned product availability commands

Status: accepted. Specifications: 001, 026 (T10d.3).

Legacy availability POST increments a version on every request. Retain that
contract for existing clients; add an explicit opt-in using idempotency_key and
expected_version together. Persist a terminal receipt bound to Venue/session/key
and a fingerprint including product, state, expected version and optional reason.
Reauthorize the original session/capability before replay. Different payload under
the same key conflicts; a different session never receives the original receipt.

Lock StaffSession with NO KEY UPDATE, then ProductAvailability. This serializes
same-session keys without blocking audit FK checks from Tab-first transactions.
Reject stale versions durably without changing the product. A successful no-op
records the command but does not change version, timestamp or invent a state event.
Real changes record before/after, versions, actor/session, reason and command ID.
Receipt, changes and audits share one transaction; unexpected failure rolls back.
Expose availability_version in catalog reads. This does not change active,
confirmed items, snapshots, ledger or Payments. Browser recovery and concurrent
availability controls require T10d.4; no UI barrier is removed in this API slice.

T10d.4 adds a per-product browser journal in sessionStorage, capturing version and
original session before POST. Terminal receipt validation and canonical readback
precede removal. Independent versioned products and verified production items may
coexist with persisted batch/item commands; review, legacy commands and catalog
configuration retain barriers. Invalid storage or different actors fail closed.
