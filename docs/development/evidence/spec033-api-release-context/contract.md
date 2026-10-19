# Spec033 E04/E06: release original occupancy

`POST /hospitality/tables/{table_id}/release/` accepts the required pair `expected_occupancy_id` (UUID) and `expected_generation` (positive integer). Supply both. A missing/partial/invalid pair returns 400. With a valid pair, the service compares both values against the active occupancy while holding the existing Table → TableOccupancy row locks, before any lifecycle, assignment or audit writes. A mismatch returns 409 `STALE_OCCUPANCY`, without disclosing another occupancy ID. Venue scoping and TABLE_MANAGE remain unchanged; a foreign table returns 404. Omission returns 400; the product is unreleased and has no compatibility fallback.

This prevents an intention confirmed for group A from releasing replacement group B. UX2 clients must capture both fields with the original dialog/intent, never regenerate them on recovery. This slice does not modify financial policy, require settled Tabs, add delivery enforcement, implement release idempotency or change cleaning transitions. No migrations.

Validation must cover replacement A→B, mismatched generation, invalid/partial pairs, cross Venue, matching release/Guest access revocation and required-field omission on disposable PostgreSQL. Independent R3 and client adoption remain gates; no merge/deploy.
