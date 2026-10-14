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
