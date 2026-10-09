# Plan — Spec 008

## Independent closure — 2026-10-09

Add real API BYOD tests for untrusted ordinary orders, replacement/reinstall,
installation versus membership revocation, refresh/lock and mutation audit provenance.
Reproduce missing registration audit and conflict-current-state response before fixing
Access only. Add PostgreSQL parallel role-update coverage. Inspect native auth and
manifest without changing navigation/payment provisioning; physical-device approval
remains an explicit external gate.

## Recommended implementation sequence

1. **Domain and migrations first**
   - VenueStaffMembership;
   - capability vocabulary and baseline role bundles;
   - StaffSession;
   - DeviceRegistration;
   - revocation/audit records.

2. **Authentication contracts**
   - staff identifier + PIN login;
   - refresh/logout/lock;
   - effective-capability query;
   - operator switch;
   - reauthentication challenge.

3. **Server-side authorization**
   - shared authorization service/decorator/policy layer;
   - venue scoping;
   - denial semantics;
   - actor/session/device propagation into AuditEvent.

4. **Android**
   - secure session storage;
   - automatic device registration after authenticated first login, with UNTRUSTED allowed for normal authorized operations;
   - BYOD personal phones without manager approval; separate shared-terminal TRUSTED fast switch;
   - login;
   - lock/switch operator;
   - privileged reauth.

5. **Web/PWA**
   - secure staff session;
   - shared-terminal switch where enabled;
   - expired/revoked handling.

6. **Management**
   - staff memberships/roles;
   - active devices/sessions;
   - revoke lost device/session.

7. **Degraded/reconnect integration**
   - reauthorize replayed commands;
   - invalidation on revocation/role change.

## API contracts

Define stable conceptual contracts before UI:
- /auth/login;
- /auth/refresh;
- /auth/lock;
- /auth/switch-operator;
- /auth/reauthenticate;
- /me + capabilities;
- management endpoints for membership/device/session lifecycle.

Return normalized denial reasons such as AUTH_REQUIRED, SESSION_EXPIRED, MEMBERSHIP_REVOKED, CAPABILITY_REQUIRED and REAUTH_REQUIRED.

## Affected surfaces

- Atendimento Android;
- Bar/Cozinha Web/PWA;
- Gerência;
- all mutation APIs through shared authorization middleware/policies.

Guest PWA is intentionally not migrated to staff auth.

## Rollout / migration

Migrate seeded roles into memberships, invalidate old development sessions, and deploy backend authorization before exposing role-sensitive UI.

Do not rely on UI rollout order for security.

## Testing strategy

- unit tests for capability resolution;
- integration tests for each baseline role;
- session expiry/revocation tests;
- device revocation propagation;
- first-login auto-registration and normal order placement on UNTRUSTED personal device;
- phone replacement/reinstall versus revoked installation and revoked staff membership;
- Android without NFC can take orders; payment-provider onboarding remains separate;
- shared/loaner fallback and no compulsory MDM/personal data access;
- Android secure-storage/session recovery tests;
- Web CSRF/session tests;
- replay after offline with expired/revoked actor;
- audit provenance tests.

## Dependencies that must land first

Spec 001 Venue/StaffMember/AuditEvent foundations. No later operational spec should invent its own role rules instead of consuming Spec 008.
