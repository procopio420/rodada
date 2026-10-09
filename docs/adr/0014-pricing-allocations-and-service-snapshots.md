# ADR 0014 — Pricing allocations and explicit service snapshots

Extend the canonical ledger Adjustment, retaining historical cancellation/courtesy
records. Persist allocation facts and use the existing Tab lock/version for all
commercial mutations. Integer half-up percentage rounding and largest remainders
make every cent reproducible. PostgreSQL triggers enforce append-only pricing facts.

Service is a venue-configured, explicit assessment snapshot on net consumption.
A stale basis blocks settlement until explicit reassessment. Refresh compensates
old service before appending a new assessment; partial payments never mutate.
Venue policy declares operational revenue/pass-through and refundable-service
semantics. Financial transfer lines retain their net value and record constituent
commercial amounts, so transferred adjustments follow responsibility without sales.

Approval is a persisted exact intent with both requester and approving manager;
a changed Tab version invalidates approval. No financial fact exists before approval.
