# Acceptance — Spec 008

## Authentication happy path

**Given** an ACTIVE StaffMember membership in a Venue and a registered Android device  
**When** the staff member enters a valid PIN  
**Then** the backend issues a staff session scoped to that Venue and the app shows the current operator.

## Permission denial

**Given** a STAFF user without refund capability  
**When** they call the refund mutation directly, bypassing UI hiding  
**Then** the backend rejects it with CAPABILITY_REQUIRED and creates no Refund or financial effect.

## Fast operator switching

**Given** a trusted shared device currently used by Ana  
**When** Bruno selects his identity and authenticates with his PIN  
**Then** the next mutation is attributed to Bruno, not Ana, while the station/device context may remain.

## Session expiry

**Given** an expired session  
**When** a mutation is attempted and refresh is no longer valid  
**Then** no domain mutation occurs and the client asks for authentication again.

## Revoked membership

**Given** a MANAGER revokes a staff membership  
**When** an existing session next refreshes or performs a protected mutation  
**Then** authorization fails even if the client UI has not yet received realtime invalidation.

## Lost device

**Given** an OWNER revokes a lost trusted device  
**When** any session bound to that device attempts a new protected mutation  
**Then** it is rejected and the revocation is visible in audit history.

## Privileged reauthentication

**Given** an authorized manager whose recent-auth window expired  
**When** they attempt a refund  
**Then** the server returns REAUTH_REQUIRED; after successful reauthentication the same intended action can be retried without creating a duplicate refund.

## Connectivity loss

**Given** Atendimento goes offline with an active session  
**When** a command classified by Spec 014 as queueable is captured  
**Then** its original actor/session context is retained; on reconnect the backend reauthorizes it.

**And given** that membership was revoked before replay  
**Then** the command is rejected rather than reassigned or silently accepted.

## Concurrency

**Given** two managers concurrently update the same membership role from the same version  
**When** both requests arrive  
**Then** only one update succeeds without conflict; the other receives the current membership state.

## Audit verification

**Given** login, operator switch, device revoke and role change events  
**When** audit is queried  
**Then** each record identifies what happened, when, actor where applicable, Venue and device/session provenance without storing PIN/token material.

## Guest separation

**Given** a valid GuestSession  
**When** it is supplied to a staff-only endpoint  
**Then** the request is rejected regardless of the guest's Tab access.

## Cross-Venue isolation

**Given** a StaffMember belongs to Venue A but not Venue B  
**When** they try to mutate Venue B  
**Then** authorization is denied and no cross-Venue data is changed.
