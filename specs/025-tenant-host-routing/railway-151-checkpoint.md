# #151 — existing Railway homologation checkpoint

Recorded 2026-10-14, source baseline
`bbaa14799d832c60b3c2404f0e34e70f387512b1`.
This is a read-only external checkpoint, not deployment or acceptance.

## Target and authorization

The user selected the existing project `rodada-aderlan-demo-20261009`,
environment `demo`, service `rodada-web`, shared PostgreSQL and existing wildcard.
No new project/service/database or paid infrastructure is authorized.
Fictional Venues A/B and their scoped test data are authorized; existing Aderlan
data must remain untouched. The user explicitly requires separate approval for
activating `RODADA_ENABLE_TENANT_HOST_UI=true` and public DNS/proxy changes.
Those operations have not been performed.

The existing acceptance requirement for a separate preview remains in force.
Reusing operational infrastructure does not itself satisfy it. Before claiming
closure, establish whether a controlled, logically isolated A/B exercise meets
the original contract; otherwise obtain a formal decision and keep the issues
open. Do not rewrite a historical acceptance criterion into a PASS.

## Executed observations

| Probe | Result | Limit |
| --- | --- | --- |
| A/B DNS | Both resolve to Cloudflare IPv4/IPv6 | Proxied answers do not reveal the origin CNAME |
| A/B/Aderlan/API TLS | Hostname-validated TLS succeeded; public certificate SAN `*.rodada.bar`, `rodada.bar`, expiry 2027-01-11 17:35:11 UTC | This is edge TLS, not Railway origin certificate or Full Strict proof |
| A/B root, manifest, staff, BFF context | HTTP 421 | Tenant rollout gate remains closed; actual runtime variable inventory not accessible |
| A/B direct health/ready/context/auth/catalog | HTTP 400 | Compatible with host allowlist rejection; cause not confirmed from server logs |
| Unknown host root/manifest | HTTP 421 | Proves rejection while rollout is disabled, not the enabled registry path |
| Aderlan root/staff/manifest | HTTP 200 | Anonymous availability only |
| Aderlan health/ready | HTTP 200, public status `ok`/`ready` | No authenticated operation or DB backup verified |
| Aderlan BFF context, ordinary and forged forwarded/BFF headers | HTTP 200, public name remains `Bar do Aderlan` | One public metadata route, not full authenticated A/B proof |
| API shared host health/ready | HTTP 200 | Native login/session flow not executed remotely |
| API shared host anonymous auth/catalog | HTTP 401 | No bearer credential used |
| Root `rodada.bar` | TLS valid and root HTTP 200 | Root manifest HTTP 404; institutional host is not tenant PWA |
| Preview script for A and B | Both exit 22, HTTP 421 at manifest | No later script assertion reached |

Commands: hostname-validated Python TLS/HTTPS GET smoke, and
`PREVIEW_TENANT_HOST=<A or B> PREVIEW_UNKNOWN_HOST=unregistered-preview.rodada.bar bash scripts/verify-tenant-host-preview.sh`.
No login secrets, cookies, tokens or customer bodies were recorded.

## Code and CI findings

`apps/web/proxy.ts` intentionally denies non-pilot tenant hosts unless the flag
is exactly `true`. This explains the shape of the observed Web rejection; the
deployed SHA and variable value must still be verified rather than inferred.

The unconfigured demo startup generates a shared BFF secret once and exports it
to both Next and Django. Therefore absence of the variable name alone does not
prove absence of a valid runtime HMAC secret. Pilot preflight, however, requires
an explicitly provisioned strong secret. Use variable names only for inventory.

Baseline API CI [38640293751](https://github.com/procopio420/rodada/actions/runs/38640293751)
passed. Web CI [38640294051](https://github.com/procopio420/rodada/actions/runs/38640294051)
failed at ESLint: the destructured `destinationLabel` parameter is unused in
`order-workspace.tsx`. The focused correction removes only that unused binding,
preserving the prop type and caller compatibility; no UI/auth behavior changes.
Final PR checks must run before any integration/deployment.

The independent read-only review identified a pre-existing P1 restart hazard:
demo seeding changes pilot staff and guest policy. The candidate patch introduces
`RODADA_DEMO_SEED_ON_START=false`, skipping demo seed and Play reviewer bootstrap
without changing release mode. Preflight rejects tenant activation in demo with
seed still enabled, and requires an explicit strong BFF secret for activation.
Nine new cases were added; eight unsafe cases failed before the implementation,
while the allowed configuration already passed. All 19 profile tests then passed
locally. Legacy default demo bootstrap and pilot preflight remain intact.
This patch has not been deployed; the operational P1 remains a NO-GO until the
running configuration is verified and the seed is disabled for the approved
change. Local typecheck, tenant/auth tests, build and the baseline-comparison
ESLint gate passed (24 historical diagnostics, zero new/fatal diagnostics).

At candidate `542efabd5903e34b7458d5e4882947c4c539c834`,
[API CI](https://github.com/procopio420/rodada/actions/runs/38647755210) passed
827 tests with PostgreSQL;
[Docker smoke](https://github.com/procopio420/rodada/actions/runs/38647755200)
and [KB](https://github.com/procopio420/rodada/actions/runs/38647755215) passed.
[Web CI](https://github.com/procopio420/rodada/actions/runs/38647755286)
uncovered 13 failures / 82 passes after the main lint failure was fixed:
integration interactions still referenced removed Attendance controls.
The focused test follow-up uses the current named/contextual opening, expands
table details, exercises the 10-item pages through item 201 at mobile widths,
and awaits canonical guest order persistence. Financial/auth/replay assertions
remain. Covers is proved through authenticated API/BFF with replay/history, not
the upstream-removed UI. New Tab list navigation is proved after the visible
Buscar refresh; automatic list refresh after contextual opening is not asserted.
Final follow-up CI is recorded on PR156 before any merge/activation decision.

The retained A/B/C draft test also reproduced an actual regression: after an
explicit contextual opening creates C, an unsent draft on A prevents the requested
Tab effect from selecting C. The candidate removes that cart-only guard, retains
pending-order/correction guards, validates the returned canonical Tab ID and
consumes each successful explicit request once so later manual selection remains
stable. Drafts remain keyed by original Tab ID. This is a runtime correction,
not solely a selector update; acceptance requires the unchanged draft/ledger/
replay assertions to pass on the final candidate.
The corrected selection code passed 10 focused real Next/BFF/Django/PostgreSQL
cases locally: A/B/C drafts at 360/390/430 and staff/guest committed-order
recovery/revocation. The 201-Tab pagination test also passed with canonical
readback before page assertions. Typecheck/build and lint gate passed after the
runtime correction. The complete final CI remains required; earlier partial
local runs and the failed Web run are not relabeled as successful full suites.

A separate local Docker rehearsal built the exact candidate `542efab` image,
using only a new disposable PostgreSQL container: bootstrap once, change fictitious
staff PIN/name/membership and guest policy, then restart with seed disabled and
tenant flag enabled, followed by same-build flag-off backout. Sanitized snapshot
digests for staff/policy and ledger counts stayed identical; readiness passed
after both restarts. Containers/database were removed. This proves the startup
opt-out on that image, **not operational Railway backup or rollback**. No real
PSP/payment/pilot data was used. Script/log are retained in the local
`pilot-artifacts/issue151/` directory; reproduction/result is attached to PR156.

## Production change cannot yet be approved concretely

Railway connection is unavailable in the executor session: discovery reports the
Railway plugin not installed; no Railway MCP tools or Railway CLI are exposed.
No project/environment IDs, deployment, staged patch, variable names, current
origin TLS status, database connection or backup have been freshly verified.
Cloudflare account configuration is also unverified. Historical issue comments
are not evidence of current settings.

After connection, complete the inventory before proposing an exact change:

1. Confirm project/environment/service IDs, source SHA, deployment and all staged
   changes. Record the current deployment; do not assume it is an eligible backout
   candidate. Verify startup seed preservation before selecting a rollback build.
2. Inspect variable **names**, release mode and startup logs without secret values.
   If runtime mode is `demo`, `start.sh` invokes `seed_demo` at every restart;
   that command rewrites existing Aderlan staff PINs/memberships. A flag-triggered
   restart cannot be called pilot-preserving until this behavior is addressed or
   excluded by verified runtime state. Do not switch to `pilot` blindly: its PIN
   and secret preflight can refuse the existing shared database.
3. Verify backup timestamp/integrity and a protected restore rehearsal into a
   disposable local database. Never run `rehearse_restore.sh` against operational
   PostgreSQL: it migrates and seeds its source before backup. Never restore/reset
   operational data to demonstrate rollback.
4. Inspect collisions and tenant ownership read-only, then prepare a transactional
   idempotent bootstrap limited to A/B, with protected random credentials, audited
   provenance and no Aderlan writes. Keep domains/guest access inactive until the
   safety gates. No global payment-simulation flag or PSP connection changes.
5. Confirm origin TLS, actual Cloudflare CNAME/proxy and SSL mode. Do not infer a
   DNS error from Railway `REQUIRES_UPDATE` under a proxied DNS response.
6. Produce the exact config diff and rollback: explicit safe Host allowlist,
   shared strong HMAC provisioning without revealing values, flag activation,
   any necessary origin certificate/DNS changes and their separate approval.
   Review every staged change before applying the environment patch.

Rollback contains only approved configuration/build changes and A/B containment:
disable their aliases/guest access, revoke test sessions, retain IDs and append-only
financial/audit history. Never delete ledger or restore the shared database. Flag
off is UI containment, not session/domain revocation. Verify Aderlan/root/native
smoke after backout. No rollback has been executed at this checkpoint.
Keep `RODADA_DEMO_SEED_ON_START=false` during backout. Older builds without this
opt-out ignore the switch and seed on restart, so they are not eligible rollback
candidates for the shared demo. Establish and verify a stable opt-out-capable
build with seed disabled before proposing tenant flag activation.

## Status

**BLOCKED**: Railway access and fresh operational inventory; enabled ingress/Host/
HMAC A/B proof; authenticated pilot/native smoke; safe backup/rollback; formal
resolution of the separate-preview criterion if needed. #151 and #130 stay open.
Canary/rollout remains #152. Public edge TLS PASS does not make these gates PASS.

## Authenticated checkpoint — 2026-10-15 UTC

This section supersedes the old access blocker above, retaining that history.
CLI5.68.0 and Railway MCP are now authenticated. The existing target was freshly
confirmed: project `1ca79d6a-a555-4346-b4b6-72b0a7706359`, demo environment
`ab6da311-0926-4b5a-ab86-1d21fe893e12`, web service
`8129ec63-1222-4564-a552-d05a04ee07a2`. Three services online, no staged changes.

Runtime SSH before merge verified main4704318, deployment
`6ba51bb4-7b7a-4cd8-b464-cf017e15b95b`, seed disabled, tenant flag disabled,
explicit HMAC passing the length/diversity preflight, additive QA allowed hosts
and private PostgreSQL connection. Django checks passed; migrations shown applied.
Only boolean/configuration results were printed, never secret values.
A dedicated personal SSH key was registered for this audit; its private key
remains on the operator machine and was not published.

PostgreSQL service `8a53ce2e-3923-43d2-98c5-590cffa0315b`, volume
`49b4b7c9-9e4f-408b-8d81-feb6ac760270`, server18.6. No public domain/TCP proxy.
Read-only Django inspection confirmed the pilot and its active/verified canonical
alias; QA reserved Venues/domains were absent (counts0/0). No QA writes performed.
Wildcard Railway origin certificate VALID, verified, ACME propagated. Traffic
CNAME remains REQUIRES_UPDATE/currentValue empty under proxied DNS; do not infer
Cloudflare SSL mode or an origin failure from this alone.

PR159 merged as `18da0109436bc76b199ec82ca7f7c75e5c54b57d` after exact-head
`7436debeea1e823e0b866813900e9bb1b014dc53` gates:
[API849 PASS](https://github.com/procopio420/rodada/actions/runs/38660364284),
[Web98 PASS](https://github.com/procopio420/rodada/actions/runs/38660364382),
[KB PASS](https://github.com/procopio420/rodada/actions/runs/38660364356).
Independent R3 review covered all six files at that exact head, no reproducible
P0/P1/P2; technical review is not GitHub approval or operational acceptance.
The deployment triggered by merge is
`40f0c485-5499-48f6-b1c4-7b8fe91f9d64`; its final status and merged-main
[API](https://github.com/procopio420/rodada/actions/runs/38665238342)/
[Web](https://github.com/procopio420/rodada/actions/runs/38665238180) results are
recorded in PR159/#151 comments after completion, not inferred from PR CI.

### Backup entitlement is the current write blocker

Official `postgres pitr status`: disabled, no bucket wired.
Official `backup list` and `schedule list`: both empty.
The authorized on-demand backup attempt returned exit1:

```text
railway postgres pitr backup create --project <confirmed-project> \
  --environment <confirmed-demo> --service <confirmed-postgres> \
  --name pre-spec025-ab --json
GRAPHQL_ERROR: Manual backups and backup schedules are only available for Pro workspaces
```

**No backup ID was returned. Backup and restore verification remain BLOCKED.**
No upgrade, PITR enable, database restart, restore, provision/apply, activation
or flag change was performed. The user was asked to choose whether to enable
Pro via account controls, retain the block, or formally accept an encrypted
logical backup transferred privately and restored/verified in disposable local
PostgreSQL. The latter is an exception to the original official-backup contract,
not assumed acceptance, and cannot be labeled `railway-backup:<invented-id>`.
Until resolved, never run provision/activate `--apply` or declare homologation.
The separate-preview acceptance decision also remains outstanding.

### Additional read-only edge/HMAC probes

Executed from authenticated SSH in the main4704318 runtime, without staff/guest
credentials or financial writes:

| Probe | Observed result | Limit |
| --- | --- | --- |
| Direct Railway origin TLS, using origin address with tenant SNI/Host | Valid certificate SAN `*.rodada.bar` for A, B and pilot; health A/B421, pilot200 | Does not verify Cloudflare Full Strict setting |
| Valid internal HMAC to loopback Django `/venue/context/` | 200 establishment, public pilot name | Confirms runtime secret and signed Host resolution, no A/B identity exists yet |
| Invalid, expired and adulterated assertion | 403 HOST_ASSERTION_INVALID | Only read-only metadata probes |
| Unsigned pilot private `/auth/me/` | 403 HOST_ASSERTION_REQUIRED | No pilot login attempted |
| Valid signed assertion presented externally to shared API context | 200 compatibility, no tenant name | Public ingress stripped the otherwise valid tenant assertion |
| Valid signed assertion externally to pilot private `/auth/me/` | 403 HOST_ASSERTION_REQUIRED | External header did not satisfy BFF authority |

No signature, cookie, token or secret value was printed or persisted in evidence.
HMAC was computed inside the container with the existing secret. These probes
resolve a subset of the previous boundary gaps; enabled A/B sessions, cookies,
QR, mutations, SSE, native authenticated flows and rollback remain NOT TESTED.

### PR159 deployment verified

Railway deployment `40f0c485-5499-48f6-b1c4-7b8fe91f9d64` subsequently reached
**SUCCESS**. A fresh SSH call confirmed runtime commit
`18da0109436bc76b199ec82ca7f7c75e5c54b57d` and that exact deployment ID, with
seed disabled and tenant UI disabled. In `/app/apps/api` the deployed command ran:

```bash
python manage.py provision_spec025_ab
python manage.py provision_spec025_ab --operation provision
```

Both reported venue/domain/operator absent for A and B; the second ended
`DRY RUN: operation provision not executed`. No `--apply` was used. This proves
the guarded command is deployed and inspection works, not provisioning or edge
acceptance. Backup entitlement and recovery verification remain the write gate.

## Logical backup exception and recovery proof — 2026-10-15

User decision: **"usa backlup logico com ssh, sem PRO ainda"**. This explicitly
resolves the backup-method decision above; no Pro upgrade or PITR enable occurred.
It does not accept a shared-preview exception or authorize the tenant UI flag.

Executed privately against the confirmed PostgreSQL service/instance:

- PostgreSQL source18.6; pg_dump18.6. Exported read-only repeatable-read snapshot
  kept open while all90 public table counts and `pg_dump --snapshot` were taken.
- SSH binary transport verified beforehand; dump streamed directly into
  AES-256-GCM encryption, archive and encrypted manifest owner-only outside repo,
  key in separate owner-only directory. No secret or plaintext dump logged/saved.
- Exact logical archive SHA-256:
  `8ab58dcd85832a489905f7db26053d32df02032552d392a90ee9796a34c44cfb`.
  Logical dump522186 bytes. This is **not** an official Railway backup ID.
- Ciphertext authenticated and plaintext SHA recomputed before restore. Decrypted
  stream fed into pg_restore18 with `--exit-on-error --no-owner --no-acl`, fresh
  local disposable database `rodada025_restore_verified`, tmpfs PostgreSQL storage.
- **PASS:** all90 table counts equal the same source snapshot; every restored
  public constraint validated. Restore0.85s; capture+verification56.89s;
  verified2026-10-15T01:42:59Z. These checks prove archive recovery/relational
  integrity, not correctness of pre-existing financial business history.
- Encrypted archive/manifest retained in protected operator custody, key separate;
  retention review2026-10-22T01:42:59Z. No automatic deletion of the sole verified
  backup during ongoing work; no source reset/restore/schema or ledger mutation.

The command's new truthful reference is `logical-sha256:<exact digest>` together
with `--logical-backup-verified`; tests/review/CI/deployment must pass before using
that contract operationally. No `--apply`, QA activation or flag has yet run at
this checkpoint. Previous official-backup rejection remains historical evidence.

## Real A/B staging and containment — 2026-10-15 UTC

This checkpoint supersedes the historical missing-access/backup/apply statements
above. It does **not** supersede the original separate-preview/browser acceptance
contract. #151 and #130 remain OPEN; #152 remains later canary/rollout.

### Integrated code, deployments and concurrent main change

- [PR166](https://github.com/procopio420/rodada/pull/166) merged as
  `4056adbd0ba564a3c169db76b42f26141257977c`, following exact-head
  `8568384c8211093cfbc76383d08055730ce755f2` API/Web/KB SUCCESS and
  [independent R3 review](https://github.com/procopio420/rodada/pull/166#issuecomment-6182501873).
- On merged4056: [API38669986695](https://github.com/procopio420/rodada/actions/runs/38669986695),
  [Web38669986592](https://github.com/procopio420/rodada/actions/runs/38669986592),
  [KB38669986576](https://github.com/procopio420/rodada/actions/runs/38669986576)
  all SUCCESS (API854PASS/571.54s; Web98PASS/7.3min). Railway deployment `179ceae2-712d-49e5-a299-63370dc50285`
  observed SUCCESS and exact runtime SHA confirmed over SSH.
- Concurrent [PR164](https://github.com/procopio420/rodada/pull/164) then advanced
  main/runtime to `b63b6111d66c640e8d4fde8ab2042743c9083eee`, deployment
  `ef830243-aa54-4d45-a4df-4f0b08efe632` observed SUCCESS. The stale-SHA guard
  refused the first rollback witness before any new login or containment write.
  Readback confirmed A/B still active and zero unrevoked QA sessions; probes and
  witness were then explicitly rebound to the new SHA. No concurrent work reverted.
- API tree is identical at both SHAs: `ee557bc3b3f391d9b5a897bb09cc614c1ad60d25`;
  deploy tree `0da2422754eb3bb4abe1e21e35096ef8c1b7bd8f` also identical.
  Web/Android changed in164: their main-SHA checks must be recorded separately,
  not inferred from4056. [Android38671039437](https://github.com/procopio420/rodada/actions/runs/38671039437)
  SUCCESS; [Web38671039040](https://github.com/procopio420/rodada/actions/runs/38671039040)
  SUCCESS (98 browser integration tests/9.2min).

### Backup and actual commands

The authorized logical archive was re-authenticated with GCM and both encrypted
and plaintext SHA before apply; its authenticated manifest timestamp binds the
recovery receipt and the less-than24h validity check. Reference:
`logical-sha256:8ab58dcd85832a489905f7db26053d32df02032552d392a90ee9796a34c44cfb`.
Original recovery evidence remains90/90 same-snapshot counts, validated
constraints, disposable PostgreSQL18 restore0.85s; not a financial-invariant audit
of pre-existing production history. Ciphertext/key remain separate owner-only
custody, retention review22Oct. No production restore or public database proxy.

Executed over private SSH in `/app/apps/api`, with distinct random12digit PINs
injected into only the command process through protected stdin, never arguments,
logs, Railway global variables or startup:

```bash
python manage.py provision_spec025_ab
python manage.py provision_spec025_ab --operation provision --apply \
  --backup-reference 'logical-sha256:8ab58dcd85832a489905f7db26053d32df02032552d392a90ee9796a34c44cfb' \
  --logical-backup-verified
# Same provision executed again after commit: idempotence PASS.
python manage.py provision_spec025_ab --operation activate --apply \
  --backup-reference 'logical-sha256:8ab58dcd85832a489905f7db26053d32df02032552d392a90ee9796a34c44cfb' \
  --logical-backup-verified --edge-confirmed
python manage.py provision_spec025_ab --operation deactivate --apply
```

The executor called these same management-command operations via `call_command`,
inside an additional repeatable-read transaction with lock/statement timeouts.
Hashes of every table's rows before/after verify that provision changed no
pre-existing row and added only reserved QA-owned rows. Activation/containment
compare every foreign-row multiset after subtracting permitted QA-owned models;
critical QA postconditions precede commit. This proves changes by **that
transaction**, not absence of unrelated concurrent transactions. No row content
or hashes of private individual rows are published. Postcommit readback matched.
Independent review corrected executor postcommit validation and backup timestamp
binding before apply; a further containment check was corrected to preserve
REVOKED memberships. Real disposable PostgreSQL17 regressions proved rollback on
bad QA state, committed idempotence, activation/deactivation and containment of
an extra ACTIVE operator/session while the reserved manager remained REVOKED.

| QA identity | Venue UUID | Operator UUID | Final state after witness |
| --- | --- | --- | --- |
| e2ea.rodada.bar | 00c7e9b0-fad7-43fd-aa42-405e46ac2133 | ea4e106b-04ed-4493-ac80-294adc10992d | domain inactive/verified, membership SUSPENDED, guest blocked |
| e2eb.rodada.bar | ff6b3b99-062d-4b83-ae8a-ef6cc41d937e | 6213f996-4734-4612-8ce9-0092d6ae623b | domain inactive/verified, membership SUSPENDED, guest blocked |

### Live boundary and authentication results

| Control/scenario | SHA/environment | Result and limit |
| --- | --- | --- |
| Public TLS A/B/pilot/unknown and Railway-origin TLS A/B/pilot |4056 and b63, existing Railway/Cloudflare|PASS hostname validation; origin target pgyvbzi2.up.railway.app with tenant SNI. Cloudflare Full Strict setting itself NOT TESTED |
| Valid loopback HMAC / missing, invalid, expired, altered |4056 and b63, real ASGI|200 pilot context; missing private assertion403 HOST_ASSERTION_REQUIRED; bad signatures403 HOST_ASSERTION_INVALID |
| Externally supplied valid pilot HMAC through public ingress |4056 and b63|Shared API stays compatibility; QA initially421, after registry activation200 with own QA UUID, never pilot UUID; demonstrates stripping |
| Forged forwarded/BFF headers to pilot BFF |4056 and b63|200 with pilot UUID preserved; no client-selected tenant |
| Unknown host |4056 and b63|BFF421; raw API400 from Django allowlist, fail closed. This is not a raw API421 claim |
| QA A/A and B/B Android protocol login/me/catalog/tabs |4056, public api.rodada.bar|PASS200, correct distinct Venue/platform, empty own catalog/Tabs; protocol smoke, not physical Android device |
| A/B and B/A credentials on shared API |4056|403 MEMBERSHIP_REQUIRED, no token issued |
| A token on B and B token on A, signed canonical ASGI |4056|403 VENUE_HOST_MISMATCH, no foreign payload; positive same-host200. Browser BFF still gated |
| QA refresh/logout |4056|Refresh200; own new sessions logout204, old access401 afterward |
| Two concurrent QA signed ASGI SSE streams; domain/session containment |b63|Both ready, then revoked; zero change events during this witness. No guest-session fixture or financially busy event stream tested here |
| After containment: me/refresh, reconnect, new native login |b63|401/401, canonical reconnect421, login403 MEMBERSHIP_SUSPENDED, both directions |
| Foreign-row preservation during operational changes |4056 provision/activation; b63 containment|PASS transaction-scoped fingerprint and readback; no financial fixtures created |
| Aderlan/landing/shared API anonymous availability |4056, postdeploy|pilot root/context/health200; landing200; APIhealth200. Full authenticated pilot smoke NOT TESTED |

Public requests with Python's default User-Agent initially received Cloudflare
1010/403. An explicit `Mozilla/5.0 Rodada-Spec025-Audit` User-Agent passed the same
probes without changing Cloudflare, TLS or application validations. Failed
observations are retained in protected sanitized receipts, not relabeled PASS.

### Remaining gates and next change

`RODADA_ENABLE_TENANT_HOST_UI` remains absent/off. Seed-off and explicit HMAC
remain configured; no staged Railway changes were present in the inspected
inventory. No DNS/proxy/configuration/PSP changes, paid resources or shared UI
flag activation occurred. A/B currently suspended; their historical auth/audit
records remain intact.

The existing pilot test operator/membership is ACTIVE, but its protected PIN is
not available to the SSH smoke process. No credential reset, guessed PIN or
pilot operator mutation was attempted. Manual authenticated pilot verification
has been requested without asking for a credential in chat.

Pending: authenticated pilot smoke; specific approval of the shared-flag diff
(absent/off -> true on rodada-web only) and controlled same-build backout to
false plus QA deactivate; enabled HTTPS script/manifest/browser cookies and
login/QR/read/write/reconnect/guest revocation A/B and B/A; formal decision on
shared environment vs original separate preview. No operational database is
used to simulate money. Finance/restart/turno gates run in disposable CI:
[Aderlan38671562736](https://github.com/procopio420/rodada/actions/runs/38671562736)
and [release38671565495](https://github.com/procopio420/rodada/actions/runs/38671565495),
both dispatched on b63. The isolated pilot shift completed SUCCESS; integrated
release completed FAIL:853PASS/1FAIL438.17s, missing standalone print contract
in disposable image. [PR168](https://github.com/procopio420/rodada/pull/168) copies
only that existing contract; test remains unchanged. Candidate
[release38672594038](https://github.com/procopio420/rodada/actions/runs/38672594038)
completed SUCCESS on exact f02d11da39ca28143e1f695f18977b45d49ee8e1:
**854PASS/428.63s**, HTTP shift+restart PASS, independent R3 review no findings.
PR168 merged75f637f8e5297b960375df8c1dd83b6478a5d1ec. The original baseline
failure remains recorded; no test was skipped.


Machine-readable [sanitized execution receipts](evidence/railway-ab-20261015.json)
retain actual scenario statuses, QA IDs, backup recovery metadata, both deployment
proofs and containment results. These are executor observations, not independently
signed Railway attestations; they contain no source rows, secrets, cookies or
tokens. Post-containment pilot root/context/health/ready, landing and shared API
health/ready remained200; API anonymous private401, QA manifest421. QA-only final
counts confirm zero Tabs/Orders/Charges/Payments/Refunds, zero ACTIVE memberships,
zero unrevoked staff sessions and no guest sessions. A bounded HTTP-log query on
ef830243 returned zero5xx records for the preceding15min (limit100), not a claim
about every request or all history.


### Read-only continuation — 2026-10-15 03:25 UTC

Concurrent PR170 advanced main/runtime to
`992acffbc49fbfa9789263db1036194626b75772`, Railway deployment
`29550e4c-ff76-46db-bc00-2b99ac8b5e90` observed SUCCESS. No changes to API/deploy
trees relative4056; Web and Android differ and have their own exact-SHA SUCCESS:
[Web38675107062](https://github.com/procopio420/rodada/actions/runs/38675107062),
[Android38675107066](https://github.com/procopio420/rodada/actions/runs/38675107066).
Private SSH inspect on992 confirmed QA still inactive/verified, managersSUSPENDED,
guestblocked, with no transaction changes and postcommit readback matching.
No new activation or shared-flag change. Manual API/Web checks dispatched on992
for fresh current-main evidence; results pending. Authenticated pilot, specific
flag approval and formal separate-preview exception still await user response.


## Final controlled window — preflight 2026-10-15 04:15 UTC

The explicit [user authorization](https://github.com/procopio420/rodada/issues/151#issuecomment-6183795233)
accepts this shared environment as the formal exception to physically separate
preview, temporary flag activation and final deactivation. This changes the
execution environment, not the security assertions or the requirement for actual
browser A/B and rollback evidence. No further approval is pending for that scope.

Observed source `04d82e764e36b79da9f1870c46c7c67a1e8b892b`, Railway deployment
`1e821e0c-fb31-4ea5-920b-f75ffdb6bd01` SUCCESS. Before the window, logical archive
and recovery receipt were authenticated again; the recorded 90/90 restore
verification belongs to its original snapshot, not a current PITR guarantee.

A fresh authorized pilot login passed 16 HTTPS BFF/native protocol assertions:
Venue identity, active membership/capabilities, host-only Secure/HttpOnly cookies,
tables/catalog/Tabs reads, snapshot, SSE and reconnect, refresh-only cookie,
independent native login/me and logout of only the two newly created audit
sessions. No pilot order, Tab, cash or financial mutation was performed. This
is native API protocol compatibility, not a physical Android device test.

Nineteen current edge probes passed: public/origin hostname-valid TLS; internal
valid HMAC and rejection of missing/invalid/expired/altered signatures; external
assertion stripping; pilot Host unchanged under forged forwarded/BFF headers;
unknown host rejection; inactive QA rejection. DNS/TLS were independently checked
for A/B/pilot/API/landing. API and Web full gates were still running at this
checkpoint. Flag remains false, QA domains inactive, memberships suspended and
guest mutations blocked. Browser A/B and final rollback are **not yet accepted**.

New pairing boundary matrix PR172 head `ec1ce5fb479030285e05967e9c3ca142e292eb5c`:
API [38678969723](https://github.com/procopio420/rodada/actions/runs/38678969723),
Web [38678969787](https://github.com/procopio420/rodada/actions/runs/38678969787),
KB [38678969768](https://github.com/procopio420/rodada/actions/runs/38678969768)
all SUCCESS, independent R3 review recorded on the PR. PR172 is not integrated
at this checkpoint. Prior isolated release at main9082351 passed 874 API tests
and HTTP shift/restart, [38678983333](https://github.com/procopio420/rodada/actions/runs/38678983333);
this does not replace the gates for newer main04d82e7.
