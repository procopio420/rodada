# Spec 008 — Staff Auth, Roles & Devices

**Status:** Implemented core; native replay-session handoff and physical validation pending
**Owner capability:** Venue / Access Control

## Objective

Define the staff identity, session, authorization and device foundation used by every operational surface without turning Rodada into enterprise IAM.

## Product problem

Rodada runs on shared and mobile devices during peak service. Staff must enter quickly, switch operators safely, lose access immediately when revoked and leave an auditable actor on privileged or financial mutations. UI hiding is not authorization.

Guest access remains a separate security model.

## Scope

- StaffMember authentication;
- per-Venue membership;
- roles and capabilities;
- PIN/password login;
- fast operator switching on trusted shared devices;
- session lifecycle and revocation;
- device registration/trust;
- privileged-action reauthentication;
- Android and Web/PWA session behavior;
- degraded-connectivity rules;
- audit actor identity.

## Explicitly out of scope

- SSO/SAML/SCIM;
- cross-company enterprise directory;
- biometric identity as the only credential;
- payroll/time tracking;
- employee surveillance;
- guest/customer authentication.

## Domain concepts

### StaffMember

Human staff identity. A StaffMember may belong to one or more Venues through explicit memberships.

### VenueStaffMembership

Persisted relationship:

- venue_id;
- staff_member_id;
- status: ACTIVE | SUSPENDED | REVOKED;
- role;
- optional capability overrides;
- created_at/by;
- revoked_at/by.

A role is a baseline capability bundle, not the only authorization primitive.

### Roles

Baseline roles:

- STAFF;
- CASHIER;
- MANAGER;
- OWNER.

Default intent:
- STAFF: ordinary service/order/fulfillment actions;
- CASHIER: STAFF plus cash/payment operations;
- MANAGER: operational overrides, corrections, configuration subsets and reviews;
- OWNER: venue-wide administrative authority.

Exact capability checks live server-side.

### Capability

Stable action-oriented permission such as:

- tab.open;
- order.confirm;
- catalog.availability.manage_station;
- payment.collect;
- refund.create;
- cash.shift.open;
- cash.adjustment.create;
- tab.reopen;
- discount.override;
- staff.manage;
- venue.configure.

Capabilities are evaluated for a Venue and actor. Avoid page-based permissions such as “can see screen X”.

### StaffSession

Server-recognized authenticated session with:

- staff_member_id;
- venue context;
- device_id when applicable;
- issued_at;
- last_seen_at;
- expires_at;
- refresh/re-auth metadata;
- revoked_at/reason.

### DeviceRegistration

Represents a staff-operated installation/browser/device known to a Venue.

Fields conceptually include:
- stable generated device_id;
- venue_id;
- device type/platform;
- app installation/browser instance identifier;
- first_seen_at / last_seen_at;
- trust state: UNTRUSTED | TRUSTED | REVOKED;
- friendly label optional;
- revoked_at/by/reason.

Device trust never replaces user authentication.

### Personal devices (BYOD) versus shared terminals

**Rodada Atendimento adopts BYOD as the default:** a waiter may install the native Android app on their own phone and log in with their own staff identity. The Venue authorizes the **person** through an ACTIVE membership and server-side capabilities, not the phone.

- On first successful staff authentication, automatically create a Venue-scoped `DeviceRegistration` for the app installation, initially `UNTRUSTED`, without an owner/manager approval queue.
- An `UNTRUSTED` device **must be allowed** to create/refresh staff sessions and execute ordinary operations permitted to that staff member (e.g. view Tabs, confirm orders, perform authorized non-provider payment flows). Only `REVOKED` devices block those sessions.
- `TRUSTED` is an optional elevated device context for **shared Venue terminals**, notably fast operator switching; it is not a prerequisite for personal-phone login or routine service.
- Installation identity is an app-generated random identifier, not a hardware fingerprint. Store only its hash server-side and minimal metadata necessary for security and support; do not inspect personal contacts, photos, messages, location or unrelated apps.
- Replacing a personal phone requires only another successful staff login and automatic registration of the new installation. The old session/installation can be revoked independently.
- Revoking one installation invalidates its current sessions, **not the person's membership**. Reinstallation may produce a new installation identity; device revocation alone must never be described as permanent physical-device blocking. To disable a staff member across installations, suspend/revoke their Venue membership and invalidate sessions.
- No employee is required to hand over their personal phone, enroll in MDM, or accept continuous tracking. Venue onboarding must provide an operational fallback (e.g. a shared/loaner device or cashier workflow) for unavailable or unsuitable personal phones.
- Tap on Phone onboarding and provider device certification are **separate payment capabilities**; any additional PSP authorization/provisioning must not prevent ordinary POS login and orders.

Staff UX must not expose `UNTRUSTED` as a pending-approval state for a personal device.

## Authentication strategy

### Primary login

P0 supports:
- staff identifier + PIN for fast venue login;
- stronger password/recovery flow for OWNER/MANAGER account administration.

PIN requirements:
- stored only as a strong salted verifier;
- rate-limited per account + device + Venue;
- never logged;
- not reused as a guest token;
- lockout/backoff after repeated failures without permanently blocking the shift.

### Fast operator switching

Allowed on TRUSTED venue devices.

Flow:
1. device remains registered;
2. current operator locks/switches;
3. next staff selects identity and enters PIN;
4. backend issues a new StaffSession;
5. previous operator session on that UI context is no longer the active actor.

Fast switching must not silently inherit the previous actor.

### Privileged-action reauthentication

For high-impact actions, policy may require recent reauthentication, initially:
- refund;
- manual payment reconciliation;
- large discount/courtesy above configured threshold;
- cash discrepancy acceptance;
- staff/device revocation;
- reopening a financially closed Tab.

Reauthentication proves the current actor again; it does not create a second identity.

## Session lifecycle

States are represented by validity rather than a business state enum:

ACTIVE -> EXPIRED
ACTIVE -> REVOKED
ACTIVE -> SUPERSEDED where a policy intentionally replaces it

Rules:
- access token lifetime is short;
- refresh/session credential is longer-lived and revocable;
- server checks membership status on refresh and sensitive mutations;
- revocation must prevent new authorized mutations promptly;
- device revocation invalidates sessions bound to that device;
- membership revocation invalidates all sessions for that Venue;
- session expiry never changes domain ownership/history.

## Android behavior

Rodada Atendimento:
- stores session credentials in Android secure storage;
- resumes without repeated full login while refresh is valid;
- requires PIN/reauth on policy-defined privileged actions;
- supports explicit Lock/Switch Operator;
- device capability/payment provisioning is separate from login;
- personal phone login and regular POS use do not require device trust promotion or manager approval;
- lost/stolen device can be remotely revoked.

A device may stay registered while no staff session is active.

## Web/PWA behavior

Cozinha, Bar and Gerência:
- secure cookie or equivalent protected session mechanism;
- no long-lived bearer token in localStorage;
- shared terminal may use trusted-device fast switching where enabled;
- manager/owner consoles should use shorter inactivity lock or reauth for privileged mutations.

## Guest separation

GuestSession and TabIdentifier from Spec 004 are not StaffSession.

A guest token can never satisfy a staff capability check. A staff session does not grant access to another Venue without an ACTIVE membership.

## Authorization invariants

1. Every privileged mutation authorizes server-side against Venue + actor + capability.
2. Client-side visibility is convenience only.
3. A role change affects future authorization without rewriting historical AuditEvents.
4. Audit records persist immutable staff_member_id and session/device provenance where relevant.
5. Device trust never grants business permissions.
6. Revoked membership cannot refresh or create new staff sessions for that Venue.
7. A mutation cannot attribute itself to whichever user was previously active on a shared device.
8. System/background actors are explicit and never impersonate staff.
9. A first-time authenticated personal installation registers automatically without approval and can perform operations allowed by its actor's capabilities while UNTRUSTED.
10. Device TRUSTED never substitutes for staff identity; payment-provider provisioning is independent from staff/device trust.
11. Revocation of an installation is not a permanent ban on that physical phone; staff-wide revocation uses membership/session controls.

## Persisted vs derived

Persisted:
- staff identity;
- Venue memberships;
- baseline role and explicit overrides;
- device registration/trust;
- sessions/revocations;
- auth/security AuditEvents.

Derived:
- effective capabilities from membership role + explicit venue policy;
- current session validity;
- “recently reauthenticated” window.

## Commands / queries

Conceptual commands:
- authenticate_staff(venue, credential, device_context);
- switch_operator(device, staff, pin);
- refresh_session(session);
- lock_session(session);
- revoke_session(session_id, actor, reason);
- register_device(venue, device_metadata);
- trust_device(device_id, actor);
- revoke_device(device_id, actor, reason);
- update_membership_role(membership, role, actor);
- require_reauthentication(action_context).

Queries:
- current_actor();
- effective_capabilities(actor, venue);
- active_sessions_for_staff();
- devices_for_venue();

## Realtime behavior

Revocations and role changes may push an invalidation event. Realtime is an acceleration only: every protected API still validates authorization.

Clients receiving revocation:
- clear privileged state;
- stop optimistic mutations;
- show “Sessão encerrada” or “Acesso atualizado”;
- require login again when needed.

## Connectivity and degraded state

When API is unavailable:
- an existing UI may continue showing cached non-sensitive operational reads according to Spec 014;
- no new offline login;
- no offline role/device changes;
- no privileged financial/admin mutation can be newly authorized offline;
- queued safe commands may retain the authenticated actor/session envelope but are reauthorized server-side on replay;
- if the session expired or was revoked before replay, the command is rejected and must not be silently reassigned.

## Concurrency / idempotency

- session revocation is idempotent;
- repeated device revoke is idempotent;
- membership role update uses versioning/last-write protection;
- auth requests do not create duplicate StaffMembers;
- replayed domain commands preserve original actor intent but revalidate current authority as defined by each command.

## Audit requirements

Record at minimum:
- login success/failure class without credential material;
- logout/lock/switch;
- session revoked;
- device registered/trusted/revoked;
- membership role/status changes;
- privileged reauthentication success/failure class;
- actor/session/device on relevant mutations.

Never log PIN, password, access token, refresh token or payment credentials.

First authenticated registration records a distinct `auth.device_registered` event
with the new session/device provenance and UNTRUSTED state. Repeated logins on the
same installation do not emit a second registration event. A membership version
conflict returns the current membership ID, role, status and version, scoped to
the actor's Venue, so the caller can review before retrying.

## UX rules

### Atendimento Android
- after an authorized first login, start normal operation immediately; do not show a device-approval waiting screen;
- device without NFC continues to use the POS normally, with Tap on Phone disabled/fallback as appropriate;
- lock/switch is reachable in one or two taps;
- active operator name/avatar/initials visible in operational header;
- no full credential ceremony between ordinary tasks on a trusted active session;
- privileged reauth is inline and returns to the action.

### Bar/Cozinha
- shared-terminal switching is fast;
- station context remains while actor changes;
- permission denial explains the missing capability, not a generic error.

### Gerência
- session/device management lives under Gestão/Mais;
- owner can revoke a lost device quickly;
- manager cannot escalate own role unless explicitly authorized.

## Metrics/events

Security/operational events:
- auth.login_succeeded / failed;
- auth.session_revoked;
- auth.device_registered / revoked;
- auth.operator_switched;
- auth.reauth_required / succeeded / failed;
- membership.role_changed.

Metrics should support operational/security diagnosis, not employee attendance scoring.

## Security/privacy

- credential verifiers use modern password hashing;
- rate limit credential guessing;
- CSRF protections for cookie sessions;
- secure storage on Android;
- token rotation where applicable;
- least-privilege capability checks;
- sensitive logs redacted;
- device metadata minimized to operational/security needs.

## Migration / backward compatibility

If existing seeded StaffMember rows only contain role:
1. create ACTIVE VenueStaffMembership from current venue relation;
2. map existing roles unchanged;
3. mark existing development devices UNTRUSTED;
4. require fresh login after migration.

No historical AuditEvent actor is rewritten.

## Depends on

- Spec 001 Core POS: Venue, StaffMember and AuditEvent foundations.
- ADR 0001 modular monolith and ADR 0005 domain boundaries.

## Enables

- Specs 009–018 for explicit actor/permission semantics;
- Spec 006 sensitive payment actions;
- Spec 013 staff/device configuration;
- pilot hardening RBAC/revocation requirements.

## Deliberately deferred

- enterprise federation;
- hardware-backed staff badges;
- biometric-first login;
- centralized multi-venue corporate IAM.


## Web refresh coordination — demo correction (2026-10-09)

Concurrent Web requests and tabs using the same rotating refresh credential must share one refresh within a Web server process. A bounded five-second in-memory result window covers requests already sent with old cookies; keys are SHA-256 digests, credentials never enter logs, browser JavaScript or durable storage. Each retried request still authorizes against the API, including after revocation. Access tokens invalidated by rotation may refresh once using the existing refresh cookie, alongside ACCESS_TOKEN_EXPIRED. No lifetime, capability, device trust or API rotation changes.

Transient refresh failure (e.g. API 503) preserves cookies and reports failure; invalid/revoked credentials clear them. This slice covers the existing single-process demo; coordinating multiple Web replicas remains outside this local acceptance and requires shared coordination before such deployment. No financial mutation is replayed after a successful response.
