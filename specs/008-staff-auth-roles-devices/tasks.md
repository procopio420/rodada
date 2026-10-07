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
