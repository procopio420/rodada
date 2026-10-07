# Tasks — Spec 008

## Domain/API
- [ ] Define VenueStaffMembership and lifecycle.
- [x] Define capability vocabulary and baseline STAFF/CASHIER/MANAGER/OWNER bundles.
- [x] Implement effective-capability resolution per Venue.
- [ ] Define StaffSession lifecycle and revocation.
- [ ] Define PIN authentication and lockout/backoff policy.
- [ ] Define privileged reauthentication window/policy.
- [ ] Add shared server-side authorization policy layer.
- [ ] Normalize authorization error codes.
- [ ] Propagate actor/session/device context to domain commands and AuditEvent.

## Persistence
- [x] Membership constraints and role/status migration.
- [x] DeviceRegistration persistence and trust state.
- [ ] Session/refresh token persistence or revocation index.
- [x] Index active sessions by staff/device/venue.
- [x] Preserve immutable historical actor references.

## Android
- [ ] Register installation/device.
- [ ] Secure credential/session storage.
- [ ] Login flow.
- [ ] Session refresh.
- [ ] Lock and Switch Operator.
- [ ] Privileged action reauthentication.
- [ ] Revoked/expired session UX.
- [ ] Remote lost-device revocation response.

## Staff Web/PWA
- [ ] Secure session mechanism.
- [ ] Shared-terminal switch when enabled.
- [ ] Expired/revoked state.
- [ ] Permission-denied messaging.
- [ ] Reauth flow for sensitive manager actions.

## Realtime
- [ ] Session/role/device invalidation event.
- [ ] Client clears privileged state on invalidation.
- [ ] API remains authoritative if realtime is unavailable.

## Management
- [ ] Staff membership list.
- [ ] Change role/status with authorization.
- [ ] Device/session list.
- [ ] Revoke session/device.
- [ ] Audit trail views.

## Quality/tests
- [x] Role/capability matrix tests.
- [x] Cross-Venue isolation tests.
- [ ] PIN brute-force/rate-limit tests.
- [ ] Revoked membership cannot refresh.
- [ ] Revoked device cannot continue mutations.
- [ ] Fast switch never attributes action to previous operator.
- [ ] Replayed queued command is reauthorized.
- [ ] Guest credential cannot satisfy staff auth.
- [ ] Sensitive credentials never appear in logs.
