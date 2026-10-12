# Spec 025 — Acceptance record

Recorded 2026-10-12. **P0 application security foundation implemented and tested. Canonical URL / production routing rollout remains NO-GO.** PASS means the stated application assertion ran successfully; it does not certify live infrastructure. See [security boundaries and rollout](../../docs/architecture/spec025-p0-security.md).

## Original acceptance criteria

| Criterion | Status | Implementation | Automated test / evidence |
| --- | --- | --- | --- |
| Unique audited registry maps `bardoaderlan.rodada.ai` to unchanged `bar-do-aderlan` UUID | PASS | `apps/api/modules/venue/{models,domains,hostnames}.py`; migrations 0008–0010; `seed_demo.py` | `test_authoritative_alias_preserves_slug`, `test_registry_constraints_and_audit`, `test_postgres_bulk_lifecycle_cannot_reassign_or_skip_audit`; both `test_tenant_domain_migration.py` tests. Full PG suite + migration/seed tests passed. |
| Reserved/unknown/disabled/lookalike/malformed hosts fail closed without demo fallback | PASS | `hostnames.py`, `host_middleware.py`, `apps/web/proxy.ts` | `test_unknown_reserved_malformed_fail_closed`, `test_disabled_unverified`, real BFF integration `public pages fail closed for unknown and unsupported hosts`; 421/403, no business data. |
| Browser forwarded/tenant headers and query Venue cannot select another Venue | PASS | `host_middleware.py`, `apps/web/lib/server/venue-host.ts`, `auth-gateway.ts` | `test_forwarded_and_tenant_header_spoofing`; real BFF spoofed CSRF Origin/forwarded Host test. HMAC method/path/expiry tests ran in PostgreSQL. |
| PT-BR public paths/subpaths/query/method/assets/SSE rewrite to existing modules | MISSING | P1; no new canonical path rewrites added | Existing internal modules remain; `/cozinha`, `/gerencia`, `/caixa`, `/m/:token` and related rewrite matrix deliberately not activated. |
| Per-host manifest/title/start URL and canonical navigation | MISSING | P1; existing `surfaces.ts` retained | Existing local surfaces tested. No tenant manifest or contextual login UI claim. |
| Root/legacy/local/Railway compatibility and Android preserved | PARTIAL | `settings.py`, `deploy/railway/start.sh`; unchanged native auth contract | `test_explicit_legacy_and_android_compatibility` (local, exact Railway host, Android), real legacy Web workflows. Actual live Railway release/smoke remains EXTERNAL_BLOCKED; no deploy performed. |
| Login A succeeds, valid B credentials on A never issue B cookies/session | PASS | Existing `authenticate_staff` + `assert_staff_venue`; BFF gateway | `test_login_cannot_substitute_foreign_venue`; real BFF foreign login test asserts 403 and no access cookie. |
| Staff A session replayed on B rejects reads/writes with 403 `VENUE_HOST_MISMATCH` | PASS | Common `_session_failure` guard and BFF host assertion | `test_foreign_host_rejects_session_before_reads_mutations`; real BFF session replay. No foreign Tab mutation committed. |
| Refresh/operator switch/restoration cannot bypass Venue binding | PASS | Existing access service guard; host-partitioned refresh coordination | `test_refresh_mismatch_does_not_rotate_or_revoke`, foreign-host switch/reauth cases; existing switch/reauth regression tests; real BFF refresh-only cookie restoration test. |
| Cookies host-only, production Secure, HttpOnly; no sibling Domain credential scope | PASS | `auth-gateway.ts`; per-QR guest cookies; actual-Host CSRF | Real BFF staff/guest tests inspect Set-Cookie attributes/no Domain and sanitized bodies; local browser workflows check HttpOnly cookies and no stored guest credential. Real sibling HTTPS deployment is covered by the external gate below. |
| Foreign QR/session indistinguishable 404; occupancy generation/release revokes stale guest | PASS | Existing guest service plus host guard, guest BFF cookies | `test_guest_qr_session_replay_and_generation`, `test_guest_unknown_and_foreign_sessions_are_indistinguishable`; real guest BFF and browser release/service-request workflows. |
| Guessed foreign business IDs cannot read/mutate Ordering, Payments, Cash, Catalog, Management, Tables | PASS | Existing actor/session-scoped queries/services; receipt/icon guards added | `test_guessed_foreign_objects_and_offline_idempotency`, `test_foreign_cash_access_refunds_management_and_audit_are_scoped`; existing financial/integration suite in PostgreSQL. Refund optional reason now defaults to empty instead of throwing before scoping. |
| SSE/cursor/outbox/recovery/idempotency/audit/provider callback partitioning | PARTIAL | `realtime/views.py`, existing Venue-qualified cursor/outbox/replay/provider ports | Real host/cursor/replay/audit tests and two-Venue parallel money workflow passed; open SSE revokes on alias disable. Provider account/signature logic reviewed and existing provider tests passed; no live two-merchant PSP/worker callback rehearsal claimed. |
| Independently seeded Venues run E2E concurrently without leakage | PASS | Existing shared deployment/domain services + host restriction | `test_two_venues_complete_parallel_orders_payments_and_audit`: real PostgreSQL threads, both log in on their own host, create Tab/Order, reuse identical intent keys, pay and close independently; audit/outbox ownership asserted. |
| Preview wildcard HTTPS/ingress/trust/logging configured and verified | EXTERNAL_BLOCKED | Documented ingress/secret/allowlist contract | No preview, DNS/TLS, actual sibling-domain browser deployment or cloud logs were changed/verified. Requires separate reviewed promotion. |
| Switch-on and rollback documented; no unsupported production readiness claim | PASS | [P0 security rollout record](../../docs/architecture/spec025-p0-security.md); existing paths retained | NO-GO gate kept closed; no canonical-path activation, DNS mutation, redirects, QR migration or merge performed. |

## Required 17-scenario security matrix

All backend entries below use real Django HTTP/ORM authentication against PostgreSQL, not mocked sessions/resolvers. Web integrations use real Next production build + Django and disposable fixtures.

| # | Scenario | Status | Automated evidence (`apps/api/tests/test_tenant_hosts.py` unless noted) |
| --- | --- | --- | --- |
| 1 | Valid host resolves exact Venue | PASS | `test_authoritative_alias_preserves_slug` |
| 2 | Unknown host rejected | PASS | `test_unknown_reserved_malformed_fail_closed`; real Web page-host test |
| 3 | Reserved host rejected | PASS | `test_unknown_reserved_malformed_fail_closed`; DB constraint cases |
| 4 | Inactive/unverified rejected | PASS | `test_disabled_unverified` |
| 5 | Header spoof cannot change Venue | PASS | `test_forwarded_and_tenant_header_spoofing`; BFF CSRF spoof test |
| 6 | Login A on Host A works | PASS | `test_login_cannot_substitute_foreign_venue`; real BFF login |
| 7 | Login B on Host A fails | PASS | Same test; no B session/access cookie issued |
| 8 | Session A on Host B fails | PASS | `test_foreign_host_rejects_session_before_reads_mutations`; real BFF replay |
| 9 | Refresh cannot bypass binding | PASS | `test_refresh_mismatch_does_not_rotate_or_revoke`; real BFF refresh-only restoration |
| 10 | A cannot read B objects | PASS | `test_guessed_foreign_objects_and_offline_idempotency`, foreign cash/access/audit test |
| 11 | A cannot mutate B objects | PASS | Same tests; orders/products/tables/payments/refunds/cash/membership/session assertions |
| 12 | Guest QR A on Host B is hidden | PASS | `test_guest_qr_session_replay_and_generation`; real BFF guest test |
| 13 | Guest session remains scoped | PASS | Same test + unknown/foreign indistinguishability; real release/generation assertions |
| 14 | SSE/reconnect cannot cross Venue | PASS | `test_sse_reconnect_rejects_foreign_cursor`, foreign-host SSE cases, `test_stream_revokes_after_domain_disabled` |
| 15 | Offline replay/idempotency cannot bypass scope | PASS | `test_guessed_foreign_objects_and_offline_idempotency`; parallel Venues reuse the same intent keys |
| 16 | Existing local / exact Railway transport auth works | PASS | `test_explicit_legacy_and_android_compatibility`; real local staff/guest/cash browser workflow. Live Railway promotion not claimed. |
| 17 | Android-facing auth remains compatible | PASS | `test_explicit_legacy_and_android_compatibility` ANDROID login/me/refresh; existing BYOD/access suite passed in PostgreSQL |

## Executed validation

Environment: PostgreSQL **17.6**, Django **5.2.17**, Next **16.3.8**, Node **24.19.0**. PostgreSQL cluster and databases were disposable and separate from operational data.

| Command | Actual result |
| --- | --- |
| `cd apps/api && pytest --ds=rodada_api.settings_tenant_postgres` | **577 passed**, no failures/skips, 778.92s. Includes all 41 host-isolation cases and existing financial/concurrency/auth tests. |
| `pytest tests/test_tenant_hosts.py tests/test_tenant_domain_migration.py --ds=rodada_api.settings_tenant_postgres` | **43 passed**, 64.47s. Final follow-up covers malformed Unicode signatures and both migration/seed cases after the full suite. |
| `pytest tests/test_tenant_domain_migration.py --ds=rodada_api.settings_tenant_postgres` | **2 passed**, 18.49s. Added migration-callable/seed cases, against real PostgreSQL. |
| `python manage.py makemigrations --check --dry-run --settings=rodada_api.settings_tenant_postgres` | **PASS: No changes detected** |
| `python manage.py check --settings=rodada_api.settings_tenant_postgres` | **PASS: no issues** |
| `cd apps/web && npm run typecheck` | **PASS** on final implementation |
| `npm run build` | **PASS** on final implementation |
| `npm run test:auth` | **4 passed** |
| `npm run test:realtime` | **8 passed** |
| Relevant `npm run test:integration -- --grep 'real BFF|real guest BFF|real staff, production|guest service|public pages fail|existing local demonstration'` with disposable Django API | **7 passed**, 44.6s. Real BFF host/CSRF/refresh/guest checks and complete local staff→production→guest→cash/refund workflow, and preserved legacy demonstration paths. |
| `npm run test:visual -- --grep 'guest|staff'` | **18 passed**, 44.5s. Visual fixtures verify layout/accessibility only; security evidence comes from real integrations above. |
| Plain initial `pytest` on SQLite | **NOT PASS: 516 passed, 40 skipped, 16 failed**. Implementation/test regressions were corrected; remaining full-suite SQLite failures require real PostgreSQL row locks/serialization. The final complete PostgreSQL run above is authoritative. |
| Initial unfiltered visual run | **INTERRUPTED**, 10 passed; not claimed as full visual-suite PASS. Replaced with the relevant complete 18-case run. |

The initial symlinked node_modules build was rejected by Turbopack; dependencies were copied into the isolated worktree and the final normal production build passed. Initial failing/repaired iterations are not represented as successful runs.

## Remaining risks and recommendation

**GO for review of the P0 application foundation; NO-GO for enabling public hostname/path rollout.** Actual preview ingress/TLS/HTTPS sibling-host browser behavior, live Railway promotion, real Android device acceptance and multi-merchant provider/worker rehearsal remain external gates. P1 contextual login, metadata and Portuguese path rewrites are not delivered by this security PR. No Organization/billing tables, provider rewrite, production DNS change or QR migration was introduced.

Production PostgreSQL enforces raw-write domain audit/identity protections; SQLite development does not implement the lifecycle trigger. System provisioning is privileged and attributed as system unless an authorized ActorContext is supplied. Database administrators can alter audit/trigger protection; restrict that access. The signed host assertion is an additional routing constraint and is replayable within its 60-second freshness window; it confers no session or guest authority. Private/TLS internal transport and a shared, dedicated high-entropy secret remain required operational configuration.
