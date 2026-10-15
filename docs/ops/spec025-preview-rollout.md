# Spec 025 — Preview, evidence and rollback

Status: prepared, **not activated**. Requires P0 isolation gates and passing CI before exposing wildcard traffic.

Checkpoint 2026-10-14: [audit #130](../../specs/025-tenant-host-routing/audit-130-evidence.md)
has local PostgreSQL/code-review evidence, but actual preview remains **BLOCKED**.
The probe for `e2ea.rodada.bar` returned HTTP421 at the manifest (exit22).
[#151](https://github.com/procopio420/rodada/issues/151) tracks ingress/Host/HMAC
proof and still blocks #130; [#152](https://github.com/procopio420/rodada/issues/152)
tracks later canary/backout. These tickets do not authorize DNS/deployment.

## Shared deployment

The current request selects the existing Railway project/environment for a
controlled A/B exercise without new paid resources. See the [fresh checkpoint](../../specs/025-tenant-host-routing/railway-151-checkpoint.md).
Do not treat that decision as completion of the separate-preview criterion below.
Verify runtime release mode before any restart: default `demo` startup executes
`seed_demo`, including writes to existing Aderlan staff credentials/memberships.
Do not apply a flag/deploy change until pilot preservation and exact backout are
proved. Do not run `rehearse_restore.sh` on operational PostgreSQL; it seeds its
source. Restore verification belongs in a protected disposable destination.
The startup opt-out `RODADA_DEMO_SEED_ON_START=false` skips automatic demo seed
and reviewer provisioning while retaining the release mode. Tenant activation
in demo refuses seed-on-start and weak/missing explicit HMAC before DB contact.
Default legacy demo startup still seeds; this code does not configure Railway.
On backout, keep `RODADA_DEMO_SEED_ON_START=false` even with tenant UI disabled.
An older build without the opt-out ignores that variable and seeds again: it is
not an eligible pilot-preserving rollback candidate in demo mode. First establish
a healthy build with opt-out and seed disabled, then seek approval for flag-on.
Do not switch release mode to pilot as a shortcut around seeding/preflight.

All venues use one Railway deployment: Next.js (public module URLs) + Django API + one PostgreSQL.
Hostname (verified in `VenueDomain`) resolves to an immutable Venue UUID. Never create a Railway project/database per venue.
Do not equate `Venue.slug` with the hostname label.

## Canary rollout

1. Run API/Web/Docker/isolated-shift CI for PR #116. Run the two-Venue browser+BFF integration suite (`apps/web/tests/integration/tenant-hosts.spec.ts`).
2. Provision the pilot hostname using the existing `0009_pilot_hostname` migration; confirm the row maps to `Venue.slug=bar-do-aderlan`, `is_active=true`, `is_verified=true`. Check that no existing hostname was reassigned.
3. In a **separate preview environment** configure a wildcard CNAME for `*.rodada.bar` to the single app ingress (do not enable Cloudflare proxy until TLS strategy is verified). Configure an eligible wildcard certificate / TLS termination in the ingress. A wildcard DNS entry **does not** provision VenueDomain rows.
4. Configure `RODADA_BFF_HOST_SECRET` in the shared Next/Django runtime (never `NEXT_PUBLIC_*`); configure accepted Host names in Django ingress, preserving localhost and Railway compatibility. Strip incoming `X-Rodada-Bff-*`, `X-Forwarded-Host`, and untrusted forward headers at edge; inject trusted forwarding metadata only. If proxy and app do not agree on Host authority, stop.
   Production profile and Railway `pilot` preflight now reject absent/short/repetitive
   BFF secrets before DB contact. Generate at least32 characters cryptographically,
   independent of Django secret, provision in secret manager, confirm validation
   without printing values. Railway does not automatically select `settings_production`;
   do not claim its full settings apply just because pilot preflight passed.
5. Set `RODADA_ENABLE_TENANT_HOST_UI=true` **only in preview**, and verify both seeded venues and an unregistered host using `scripts/verify-tenant-host-preview.sh`. Check GET/POST, login/refresh/logout/operator switch, QR/catalog/order, SSE and payments with different identities.
6. Verify host-only Secure/HttpOnly staff and guest cookies, no `Domain=.rodada.bar`, per-host PWA title/manifest and cross-origin CSRF rejection.
7. Activate pilot canary only after complete simulated shift and P0 sign-off; keep `rodada.bar`, original Railway paths, and old mobile behavior intact.

## Required preview evidence

Run the HTTPS script for **both** A and B and the unknown host on the identified
preview deployment SHA. Attach sanitized results for DNS/TLS, actual Host received
at each hop, external-header stripping, BFF signature freshness/path/method rejection,
host-only Secure/HttpOnly cookies, login/refresh/QR/critical commands, SSE reconnect
and active domain/session revocation. Local Host headers plus real PostgreSQL do
not exercise a real ingress. Never record secret/cookie/token values in artifacts.
Published icon GETs and valid shared receipt capabilities remain portable; negative
cross-host auth/financial tests must not treat those intentional public reads as IDOR.

Exercise preview backout and record its SHA, health/legacy/native smoke and
preserved schema/UUID/QR. Disabling a domain must terminate its active streams;
disabling the UI flag alone is not session revocation. Do not delete/reassign domain
identity or reset an operational DB to simulate rollback.

## Backout

- Disable `RODADA_ENABLE_TENANT_HOST_UI` (or set `false`): non-pilot venue hosts return HTTP 421 at the Next edge.
- Remove preview wildcard routing / revoke preview aliases if any isolation anomaly appears. Keep existing hostname records for audit; prefer disabling `VenueDomain.is_active` over deleting/reassigning identity.
- Roll back only to a verified healthy build that preserves pilot data on startup,
  retaining `RODADA_DEMO_SEED_ON_START=false` and the DB schema/migrations. An old
  demo build without the opt-out is ineligible; do not remove the existing shared
  wildcard or perform destructive schema rollback to simulate containment.
- Validate Railway hostname and /health, /ready, /staff, login and Aderlan staff sessions on the stable deployment.
- Do not redirect guest QR tokens between domains or copy authentication cookies to new hosts.

## Observable evidence

`PREVIEW_TENANT_HOST=e2ea.rodada.bar PREVIEW_UNKNOWN_HOST=unregistered-preview.rodada.bar bash scripts/verify-tenant-host-preview.sh`
requires publicly resolvable HTTPS and valid certificate, otherwise **fails** (does not claim success). Store output, workflow URL and manifest response in release notes. No DNS/TLS provisioning is implied by this document.


## Guarded QA bootstrap on the existing Railway service

`provision_spec025_ab` is an operator-only Django management command (no HTTP
endpoint or automatic startup hook). Default is read-only `inspect`, and passing
an operation without `--apply` makes no changes. It reserves only the two
explicit QA identities/aliases `spec025-qa-a/e2ea.rodada.bar` and
`spec025-qa-b/e2eb.rodada.bar`. It refuses preexisting foreign ownership
or operator login collisions rather than reassigning customer identities.

**Before writing**: create a Railway PostgreSQL volume backup, obtain its real
backup ID, verify that the backup completed and rehearse restoring a separate
disposable database. The CLI's `--backup-reference` is only an operator
attestation; the command **cannot verify** Railway backup state itself.
Use randomly generated per-Venue 6–12 digit PINs in protected environment
variables `RODADA_SPEC025_A_PIN`/`RODADA_SPEC025_B_PIN`, never command
arguments, shell history, repository or logs.

```bash
# Commands below run INSIDE rodada-web via authenticated Railway SSH.
cd /app/apps/api
python manage.py provision_spec025_ab
python manage.py provision_spec025_ab --operation provision
# Only after a separately VERIFIED backup and tested restore:
python manage.py provision_spec025_ab --operation provision --apply \
  --backup-reference 'railway-backup:<actual-backup-id>'
```

New QA domains are **inactive and unverified**, guest mutations start blocked,
and new manager memberships are **SUSPENDED**, denying shared-API login before
explicit activation. No ledger, payment, PSP or Aderlan data is created/changed.
The two managers are strictly local QA identities; reruns preserve IDs,
existing PIN hashes and lifecycle state, and print the actual alias state.
PINs must be distinct. PostgreSQL transaction-scoped advisory locking serializes
bootstrap lifecycle commands; identities obtained after preflight are revalidated
to reject concurrent foreign claims rather than grant them QA membership.
Row locks use NOWAIT: if a concurrent login, refresh or operator switch owns a
required row, the entire command rolls back and reports `REFUSE ... no changes
committed`. This is **not successful containment**. Wait for that operation to
finish, rerun `deactivate`, then verify aliases, every QA membership/session and
live/reconnected streams. Never skip locked credentials to obtain a success.
This command intentionally does not create an active QR,
a guest occupancy or payment fixtures.

After trusted ingress/TLS have been independently verified, and after explicit
approval for this shared-host activation, an authorized operator may activate
**only the QA domain rows**:

```bash
python manage.py provision_spec025_ab --operation activate --apply \
  --backup-reference 'railway-backup:<actual-backup-id>' --edge-confirmed
```

This does not toggle `RODADA_ENABLE_TENANT_HOST_UI` or validate cookies, SSE,
HMAC, QR or Android. Those must still be tested separately before acceptance.
For containment, disable QA aliases, suspend **all ACTIVE memberships of each
QA Venue** (so every QA operator's shared `api.rodada.bar` login is denied), revoke staff/guest
sessions and block QA guest mutations without deleting or reassigning immutable
identity/history. Foreign-Venue memberships of the same staff remain untouched.
Re-activation restores only the reserved QA manager memberships; it does **not**
resurrect revoked sessions or automatically enable guest transactions:

```bash
python manage.py provision_spec025_ab --operation deactivate --apply
```

The shared demo's current `RODADA_DEMO_SEED_ON_START=false` must remain in force
during any redeploy and backout. Never use an older rollback image that reruns
`seed_demo` against the live Aderlan database. Do not use the public PostgreSQL
TCP proxy as a shortcut.

### Backup entitlement gate (observed 2026-10-15)

On the existing workspace, `railway postgres pitr backup create` returned
`Manual backups and backup schedules are only available for Pro workspaces`.
Backup/schedule lists were empty and PITR disabled. Never fabricate a backup ID,
enable PITR (which can restart the database/create storage), change plan or use
an unverified backup reference to unblock `--apply`. Obtain an explicit decision
on plan cost or a formal backup-contract exception first. A logical dump and
local restore drill, if approved, must use private SSH, encrypted custody and a
separate disposable PostgreSQL destination; it is not an official volume backup
and the current command requires a truthful supported reference contract.
No restoration over the operational database is authorized.
