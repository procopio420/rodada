# Acceptance — Spec 008

## Authentication happy path

**Given** an ACTIVE StaffMember membership in a Venue and a new Android app installation never registered with Rodada  
**When** the staff member enters a valid PIN  
**Then** the backend registers the installation automatically as UNTRUSTED, issues a staff session scoped to that Venue and the app shows the current operator without manager approval.

## BYOD device trust does not block routine work

**Given** an authenticated waiter on a personal Android installation with trust state UNTRUSTED  
**When** they view Tabs, confirm orders or perform another ordinary operation their membership authorizes  
**Then** the server evaluates staff capabilities and succeeds without a device-trust promotion or approval screen.

**And given** a valid login on another previously unknown installation  
**Then** it also succeeds without manager intervention; previous installations are not required to be removed first.

## Revocation scope and reinstall

**Given** a registered installation is REVOKED  
**When** its existing sessions refresh or mutate  
**Then** they are denied, regardless of the employee's role.

**And given** the same employee still has an ACTIVE membership and authenticates from a distinct, newly registered installation  
**Then** the new session is evaluated normally; the old device revocation is not falsely treated as a physical-device ban.

**And given** the membership is SUSPENDED or REVOKED  
**Then** login and mutations are denied from every installation.

## Payment eligibility is independent

**Given** a waiter authenticated on an Android phone lacking NFC, a supported PSP SDK or required provider provisioning  
**When** they use Rodada Atendimento  
**Then** normal orders and Tabs still work, while Tap on Phone is unavailable and supported payment fallbacks remain discoverable.

## BYOD privacy and fallback

**Given** an employee uses their personal phone  
**Then** the POS does not require MDM enrollment, access to unrelated personal content or continuous location tracking to authenticate and serve orders.

**And given** the personal device is unavailable or unsuitable  
**Then** the Venue can serve the same customer via an authorized shared/loaner device or cashier flow.

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

## Web concurrent refresh (2026-10-09)

Given valid refresh cookies and an expired/missing access cookie, concurrent authenticated reads of PDV, Bar, Cozinha and Caixa must all succeed and leave one valid operator session. Requests sent with stale cookies within five seconds receive the same rotation, without issuing a second backend refresh. Tokens remain HttpOnly and absent from response JSON.

Given a session revoked after that rotation, reusing the buffered result must still fail API authorization and clear privileged cookies. A transient upstream refresh failure must not clear valid cookies. The coordinator is memory-bounded, isolates credentials and releases pending/expired entries. This acceptance is for one Web process, not multiple replicas.

Verificação Web10/10/2026: membro sem capability de gerência deve ver aviso explícito tanto no cockpit quanto na região Alertas operacionais, sem projeção Comandas abertas. Teste integrado distingue os dois avisos legítimos, exige ambos e não afrouxa autorização.
