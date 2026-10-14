# S2 Pairing — implementation contract (before code)

Base main 2a04379, synchronized with bbaa147 before final review; S1 PR #149 merged with user approval on 2026-10-14.
Risk R3: anonymous bootstrap, proof possession, credentials, Windows service.
S1 CI: API 756 PASS / Web 91 integrations PASS. No deployment authorized.

## Decisions / adaptations

- Versioned paths /printing/agents/v1/ retained. Status is POST, not the proposed
  GET: proof secret belongs in a request body, never URL/query/logs.
- Device creates persistent installation UUID and 256-bit proof. Start retries use
  the same identity/proof; 80-bit human code expires after 10 minutes. Existing
  installation cannot be hijacked by another proof or silently re-paired.
- Manager inspects code, confirms installation UUID, then atomically approves once.
  Browser never receives the machine credential. Server derives an opaque token
  with a dedicated >=32-character deployment secret, request UUID and proof hash;
  only its hash persists. PoP status can recover an approval response lost in
  transit until machine acknowledges activation. After acknowledgement no raw
  credential is served again. Approval replay is rejected.
- Anonymous start/status and manager code lookup have durable DB throttle buckets;
  REMOTE_ADDR only (untrusted forwarded headers ignored). No process-local limiter.
- RODADA_AGENT_PAIRING_SECRET is required for pairing; absent/weak secret fails
  closed. Configuration is documented, never written to production by tests.
- Feature enable is explicit print.manage Venue configuration, not a side effect
  of installer/pairing. Does not change KDS/printing trigger modes.
- Dedicated heartbeat records server clock/version only. Printer health is untouched.
- Windows service runs as LocalService with its service SID. Machine-scope DPAPI
  plus a protected ACL grants private state to that service SID, SYSTEM and admins.
  Public diagnostics contain only pairing code/expiry/status; no proof/token.
- No runtime queue, printer enumeration, spool submission or claims: S3 scope.
- Development service commands are sufficient in S2; packaged EXE/update/signing S6.

## Gates

PostgreSQL: expiry, wrong proof/second installation, approval replay/brute force,
negative capability/foreign Venue, concurrent approval, response lost/recovery/ack,
heartbeat/revocation/flag toggle and full legacy regression. Worker tests inject
network loss/restart/revocation and prove no staff credentials or print side effects.
Windows runner: DPAPI/ACL isolation, register service, autostart/start/stop under
noninteractive service identity, local diagnostics and clean uninstall. No physical
printer/hardware certification. Manage: real BFF workflow, responsive/visual checks.

## Development operation (not distribution)

On a disposable/administered Windows 11 x64 test host, use Python 3.12 and
`pip install -e apps/printer-agent`. Run pywin32_postinstall.py -install, then:

```powershell
python -m rodada_printer_agent.service --startup auto install
python -m rodada_printer_agent configure --api-origin https://api.rodada.bar
python -m rodada_printer_agent.service start
python -m rodada_printer_agent.ui
```

No service credentials in command arguments. Configure before starting; repeated
configuration preserves protected installation identity. LocalService + service SID
are set by configure. Private DPAPI state in ProgramData/Rodada/Impressoras/private;
readable public diagnostics separate. DPAPI decryption is UI-forbidden. A protected
OWNER_RIGHTS ACL prevents other processes sharing LocalService from changing the
private file DACL via implicit ownership. Existing junction/symlink paths refused.

Stop/remove with service CLI. Removing service does not implicitly unpair/delete
server audit. For lost/revoked authorization, revoke the old PC in Manage, stop the
service and explicitly replace private local state under administrator control;
installer repair/uninstall safe cleanup is S6. Keep flag false for production until
rollout authorized. Configure dedicated pairing key through normal ops separately;
never use Django's fallback development SECRET_KEY. Rotate pairing key only with
pending codes drained/expired; changing it invalidates pending credential recovery.

`cleanup_print_agent_pairing` removes expired unconsumed requests/throttle windows
older than24h. Install identity proof hashes persist so cleanup does not permit
UUID takeover. Approved requests and AuditEvent remain historical.


## Review corrections and current evidence

Approval-code validity is ten minutes. After approval, proof-of-possession
credential recovery has a separate ten-minute grace period from approval, until
activation acknowledgment. Status and activation serialize on the agent lock.
Expired pending requests return 410; already-paired bootstrap returns 409 and
pauses the local installation for explicit administrative recovery. The worker
persists the credential before every unacknowledged activation attempt, including
retries after storage failure.

Local checks: 89 PostgreSQL printing regression/foundation/pairing tests passed
before these review corrections; worker now 11 tests passed, strict mypy passed.
Corrected local PostgreSQL suite: 90 passed, including migration reverse/reapply
and concurrent approvals. Windows CI run 38641566462 passed actual service
installation/start/session0, autostart, restart, DPAPI, ACL and revocation.
Manage integration/screenshot inspection and full API CI remain pending.
The Windows smoke gate verifies ordinary-user ACL denial; adversarial processes
running as LocalService without this service SID are not yet separately exercised.

| Slice | Status | PR | CI | Blockers |
| --- | --- | --- | --- | --- |
| S1 Foundation | Merged | #149 | API/Web passed | None |
| S2 Pairing | PR/review | #155 | Windows passed; API/Web pending | Manage integration/visual evidence |
| S3 Printing MVP | Pending | — | — | S2 approval/merge |
| S4 Multiagent | Pending | — | — | S3 approval/merge |
| S5 Compatibility | Pending | — | — | S4 approval/merge |
| S6 Distribution | Pending | — | — | S5 approval/merge; signing certificate |
| S7 Pilot | Pending | — | — | Previous slices; physical evidence |


After syncing main bbaa147, the existing Attendance integration tests still
selected the removed optional-name accordion. Initial Web trace proved the current
UI exposes Nome da Comanda / Abrir comanda instead. Four integration fixtures were
updated only for those selectors; financial assertions and application behavior
are unchanged. This inherited gate failure is separate from printer pairing.


Security review found a precreated-parent namespace substitution risk. Provisioning
now creates the dedicated Rodada parent and all service directories atomically
with their final protected ACL. Existing directories with an untrusted owner,
broad write/delete/ownership rights or unsupported ACLs are rejected rather than
repaired: tightening an ACL cannot revoke attacker handles already open. Global
ProgramData ACL is untouched. Windows smoke now rejects an unsafe precreated
parent and verifies an ordinary user cannot rename the service namespace.
Administrative recovery must stop the service and move/remove unsafe preexisting
paths under trusted control before provisioning; do not merely rewrite the ACL.


Windows runtime at 865db94 passed run 38642910878, including unsafe precreated
parent/private ACL and readable retained-file rejection. Source gating evidence
and final SHA are maintained in PR #155; this document records tested snapshots,
not automatic completion of the slice. Latest verification also reconfigures the
service after LocalService writes its state, preserving installation/credential.


Final-head verification snapshot (48c8876): API run 38643282466 passed all 830
PostgreSQL 17 tests and migration/check gates; Windows run 38643282481 passed.
Web run 38643282461 passed 87/99, including all four pairing/revocation cases.
The 12 failures were obsolete main Attendance flows: required table picker,
collapsed table cards, generic scoped move action and ten-row mobile pagination.
Updated fixtures preserve financial/idempotency/recovery assertions, explicitly
exercise the current table flow and retain navigation beyond 200 tabs. They wait
for Venue configuration before opening a tab (main initially loads that flag
asynchronously). No application financial, table or fulfillment logic is changed.
Pairing screenshots at 360/390/430/1280 were actually inspected: readable without
horizontal overflow. The pairing test now also waits for the ten-second fleet
poll to show the server heartbeat as ONLINE. Final revalidation follows in PR155.


A 401 from proof polling also pauses the installation and clears local proof/code:
approval can be revoked before the service retrieves its first credential. This
negative lifecycle is now covered alongside post-activation revocation; it does
not repeatedly poll a permanently invalid proof or silently request new pairing.


Second Web trace (0396c50): 88/99 passed, including pairing and full movement
recovery. Bound-tab primary labels are Mesa <label>; customer names remain in the
subtitle. Fixtures must assert that subtitle, retaining exact table focus.
The existing PartySizeEditor was not mounted anywhere in the current app (also
absent from the S1 base). Preserve its existing UI test by mounting that existing
component in Organizar mesa, avoiding a replacement with API-only assertions.
This is an observational UI repair; no order, payment, money or fulfillment rule
changes. Main compact cards remain compact.
Pagination trace completed 85 clicks before the 120-second total deadline, with
successful canonical reads (103 tab GET 200 responses). The now-expanded test
executes 120 page navigations across three widths instead of six; its total
budget is 300 seconds, with individual 5-second assertions unchanged. No skips
or finance/recovery/idempotency assertions removed.


Expired unconsumed requests may be cleaned while an unpaired installation is
offline. Missing status requests therefore return generic 410 recovery-expired;
renewal still validates the persisted installation proof via bootstrap, preventing
identity takeover. Incorrect proof for an existing request remains 401 and pauses
local authorization. Added real PostgreSQL cleanup/reconnect negative coverage.

The restored observation editor locks the enclosing dialog and its other mutations
while a save is in flight or its result is uncertain, preserving the same retry
intent until canonical confirmation.
