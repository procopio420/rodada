# ADR 0013 — Durable Catalog icon generation

Status: Accepted

Product owns a stable 1:1 ProductIcon. A database outbox commits with a new Product; a supervised worker performs image generation outside creation transactions. Unique venue/name constraints resolve concurrent exact matches. Fuzzy suggestions never determine identity.

IconGeneration records immutable input/style snapshots, fingerprints, provider/model/usage and attempts. Request aliases deduplicate repeated manager commands even after completion. Leases and claim tokens fence workers; icon revisions fence publication against upload/reset. An existing asset remains published until a replacement succeeds.

Django default_storage stores validated PNG assets, while opaque published URLs share one reference across all surfaces. The provider port has a real direct OpenAI adapter and a configurable HTTP gateway; deterministic generation exists only in tests. A failed or unavailable provider cannot affect catalog availability, ordering or financial state.
