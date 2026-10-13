# Idempotent production batches

Status: accepted. Related specifications: 001, 010, 026.

A production batch is one human command, not a fan-out of HTTP transitions.
Persist its terminal receipt under a unique Venue/session/key and fingerprint.
Serialize same-session commands with a NO KEY UPDATE lock on StaffSession (allowing
audit FK checks from Tab-first transactions), then lock affected Tabs
and OrderItems in sorted order. Individual production transitions also lock Tab
before Item, matching correction transactions. Validate every precondition before
applying any state; reject all lines together and retain the rejection receipt.
Unexpected failure rolls back the entire transaction, including derived Dispatch.
Replay returns the original receipt without new timestamps, audit or tasks.
Configuration comes from immutable snapshots, excluding only known monetary and
quantity fields. NEW and ACCEPTED are compatible waiting origins for PREPARING;
READY requires PREPARING. Legacy snapshots remain individual operations.
This journal does not grant capability, transfer session ownership or change money.

Individual Web actions on verified snapshots reuse this command with exactly one
line. A separate sessionStorage journal retains one bound intention per item,
persisted before sending. Distinct items may await responses concurrently; replay
uses the original key/payload, including after the item leaves the waiting queue.
Canonical command readbacks are serialized, and realtime refreshes deferred during
a command readback are requested again afterward. Terminal receipt plus successful
readback clears only that item. Pending batches, legacy transitions and availability
retain their existing barriers; this decision does not authorize concurrent changes
to those scopes or adopt another staff session's saved commands.

T10d.2 narrows a persisted batch's individual-action barrier to its selected IDs.
Before persistence and during review the barrier remains global. Disjoint verified
items may issue/recover their own commands, after checking the stored batch's
binding. Invalid or altered batch storage fails closed. No new batch, legacy action
or availability mutation is enabled by this change. Both journals use the same
serialized canonical readback coordinator; one receipt never clears the other.
