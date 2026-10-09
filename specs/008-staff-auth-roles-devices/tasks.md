# Tasks — Spec 008

## Domain/API
- [x] Define VenueStaffMembership and lifecycle.
- [x] Define capability vocabulary and baseline STAFF/CASHIER/MANAGER/OWNER bundles.
- [x] Implement effective-capability resolution per Venue.
- [x] Define StaffSession lifecycle and revocation.
- [x] Define PIN authentication and lockout/backoff policy.
- [x] Define privileged reauthentication window/policy.
- [x] Add shared server-side authorization policy layer.
- [x] Normalize authorization error codes.
- [x] Propagate actor/session/device context to domain commands and AuditEvent.

## Persistence
- [x] Membership constraints and role/status migration.
- [x] DeviceRegistration persistence and trust state.
- [x] Session/refresh token persistence or revocation index.
- [x] Index active sessions by staff/device/venue.
- [x] Preserve immutable historical actor references.

## Android
- [x] Register installation/device.
- [x] Secure credential/session storage.
- [x] Login flow.
- [x] Session refresh.
- [x] Lock and Switch Operator.
- [x] Privileged action reauthentication.
- [x] Revoked/expired session UX.
- [x] Remote lost-device revocation response.

## Staff Web/PWA
- [x] Secure session mechanism.
- [x] Shared-terminal switch when enabled.
- [x] Expired/revoked state.
- [x] Permission-denied messaging.
- [x] Reauth flow for sensitive manager actions.

## Realtime
- [x] Session/role/device invalidation event.
- [x] Client clears privileged state on invalidation.
- [x] API remains authoritative if realtime is unavailable.

## Management
- [x] Staff membership list.
- [x] Change role/status with authorization.
- [x] Device/session list.
- [x] Revoke session/device.
- [x] Audit trail views.

## BYOD onboarding alignment
- [x] Server automatically registers an unknown installation after authorized staff login.
- [x] UNTRUSTED personal installation can hold a normal staff session; TRUSTED required only for specific shared-device behavior such as fast switch.
- [x] Add regression integration tests for BYOD first login, successful ordinary order on UNTRUSTED and phone replacement. Evidence: `apps/api/tests/test_access_api.py` on PostgreSQL, release report 2026-10-09.
- [x] Add tests for revoked-installation scope versus revoked membership across installations. Evidence: `test_revoked_installation_does_not_ban_replacement_but_membership_does`, release report 2026-10-09.
- [ ] Verify Android UX has no device-approval screen and works without NFC; payment provisioning must remain a separate feature gate.
- [x] Validate no compulsory MDM/personal-content permissions and document operational shared-device/cashier fallback (source/manifest review; physical behavior remains external).

## Independent closure — 2026-10-09

- [x] First-installation registration audit with actor/session/device, emitted once.
- [x] Membership conflict returns current state; PostgreSQL competing updates select one winner.
- [x] Direct refund denial, recent-auth requirement and exactly-once retry through real API.
- [x] Original-session replay helper rejects a locked session even after a new-phone login.
- [ ] Native recovery envelope must retain original session and reauthorize it on replay (Agent 3 + Agent 4 / Main Orchestrator; do not change shared contracts independently).
- [ ] Physical Android first login, no-NFC operation, remote revocation and loaner walkthrough.

Criterion-level evidence and handoffs: `docs/development/near-ready-specs-closure-2026-10-09.md`.

## Quality/tests
- [x] Role/capability matrix tests.
- [x] Cross-Venue isolation tests.
- [x] PIN brute-force/rate-limit tests.
- [x] Revoked membership cannot refresh.
- [x] Revoked device cannot continue mutations.
- [x] Fast switch never attributes action to previous operator.
- [x] Replayed queued command is reauthorized.
- [x] Guest credential cannot satisfy staff auth.
- [x] Sensitive credentials never appear in logs.
