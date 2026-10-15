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
