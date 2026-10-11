# ADR 0013 — Serialize station enablement with order routing

Status: proposed implementation; PostgreSQL verification pending.

Station enablement is typed per Venue and BAR/KITCHEN, with behavior-preserving
enabled defaults and optimistic versions. Venue row locking precedes Tab and
Product locks during confirmation and precedes station mutation. This prevents
an empty preview from racing a new committed production item. Deactivation
checks canonical undelivered items and outstanding production PrintJobs again
inside apply; historical routing and bindings are never rewritten.

Venue locks use PostgreSQL NO KEY UPDATE, preserving serialization while
allowing FK KEY SHARE checks in legacy Tab-first ledger/audit transactions.
Ledger never calls confirm_order in the inspected source. This avoids a new
Venue-lock/Tab-lock cycle caused solely by appending an AuditEvent.

Committed order replay returns the original Order before checking current
station enablement. New mixed orders fail atomically if any route is disabled.
Preview is advisory and carries no authority token. Apply revalidates current
session, capability and recent authentication and writes audit plus outbox
invalidation in the same transaction. Printer spool acknowledgment is not
paper evidence; station changes never reclassify print delivery outcomes.

The Venue lock trades confirmation concurrency across Tabs for a simple safe
configuration boundary. A finer per-station locking strategy requires measured
contention and a proved global lock order before replacing this boundary.
