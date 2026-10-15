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

### Authorized logical-backup exception — 2026-10-15

The user explicitly selected logical backup over private SSH, without Pro.
For this change, an independently verified logical archive may be supplied as:

```bash
python manage.py provision_spec025_ab --operation provision --apply \
  --backup-reference 'logical-sha256:<exact-64-lowercase-hex-dump-sha256>' \
  --logical-backup-verified
```

The extra flag attests that **that exact archive** was restored and checked in a
disposable destination. It does not perform recovery verification or verify
operator-held files itself. The digest identifies the logical dump plaintext,
not an invented Railway volume-backup ID. Missing attestation or malformed
digest is refused before any database write. Official `railway-backup:<ID>`
references retain their existing operator-attestation contract. Activation still
requires the same backup reference/attestation plus independent `--edge-confirmed`;
shared UI flag activation remains a separate explicit approval.

Operator procedure used: authenticate SSH, export one PostgreSQL read-only
repeatable-read snapshot, collect table counts in it, run pg_dump18 with
`--snapshot`, stream directly into authenticated AES-256-GCM encryption. No
plaintext archive on disk. Store archive/manifest owner-only outside the repo,
and a separate owner-only key. Verify GCM authentication and dump SHA before
decrypting to pg_restore18 in a fresh local container with tmpfs data storage.
Restore with `--exit-on-error`, retaining constraints; compare **all table counts
to the same source snapshot**, verify constraints validated, then remove the
restored copy. Capture hash, timestamp, source IDs, destination and timings only;
never emit rows, PINs, tokens, credentials or private financial aggregates.
Retain encrypted custody with a review date seven days after capture; do not
delete the only recoverable backup automatically while the audit is ongoing.
The local restore is proof of archive recovery, not operational database restore,
PITR, official volume backups, or rollout acceptance.

### Executed checkpoint and next controlled change — 2026-10-15

[Actual SHA/deployment/scenarios and remaining gates](../../specs/025-tenant-host-routing/railway-151-checkpoint.md#real-ab-staging-and-containment--2026-10-15-utc).
PR166 is integrated; QA provision/repeated provision, registry activation and
containment have actually run. A/B are now inactive, managers suspended and
sessions revoked; guest mutations remain blocked. Shared Web flag was never
activated. No payment/order facts were created in the operational database.

The next proposed configuration diff is **only** on existing `rodada-web/demo`:
`RODADA_ENABLE_TENANT_HOST_UI` absent/off -> `true`. Keep
`RODADA_DEMO_SEED_ON_START=false`, explicit HMAC, allowed hosts, database and all
other variables unchanged. Before asking for activation approval: record current
main/runtime/deployment and CI, fresh backup verification, authenticated pilot
smoke, TLS/HMAC/stripping/unknown-host results and this rollback. Explicit flag
approval is still required; preview-contract exception is a different decision.

Backout: set the flag to `false` on the same reviewed code/build, wait for the
specific deployment SUCCESS and SHA readback, then execute QA `deactivate`.
Never roll back to a startup image that ignores seed-off. Confirm both QA aliases
off, no ACTIVE QA memberships, all staff/guest sessions revoked, old tokens and
refresh/reconnect denied on shared API/canonical hosts, and pilot/landing/API
smokes intact. Preserve QA history/financial/audit records. Do not restore the
operational database to simulate application rollback. Existing REVOKED
memberships remain REVOKED, never converted to SUSPENDED/ACTIVE as a side effect.
Emergency inspect/deactivate must not depend on backup freshness, custody-key
availability, PINs, seed configuration or the shared flag.

Executor safeguards: expected runtime SHA, Python optimization disabled,
repeatable-read transaction and short lock/statement timeouts, foreign-row
fingerprint before/after, critical postconditions before commit and explicit
postcommit readback. If deployment changes or a write result is ambiguous,
inspect/reconcile before retry. A stale-SHA refusal happened during the concurrent
PR164 deployment and prevented the witness from starting on an unexamined SHA.

Use an explicit audit User-Agent for HTTP probes; Cloudflare returned1010 to
Python's default UA. Do not change/disable Cloudflare controls to pass a probe.
Unknown BFF must return421 per script; an unknown raw Django Host can instead be
rejected400 by ALLOWED_HOSTS. Record the exact layer/status, no default tenant.
Origin TLS proof does not itself prove the administrative Full Strict setting.

The pilot reviewer account/membership exists but its protected PIN was unavailable
to the SSH smoke process. Do not reset a pilot credential or infer a PIN to clear
that gate. Obtain authenticated operator verification through the existing secure
login, without requesting credentials in chat.

### Logical archive recovery format

The retained format is explicit so loss of a temporary executor does not strand
the backup. Use the separate32byte raw key from protected custody; do not print it.
AAD is the UTF-8 encoding of the fixed source identities:

```text
1ca79d6a-a555-4346-b4b6-72b0a7706359|ab6da311-0926-4b5a-ab86-1d21fe893e12|8a53ce2e-3923-43d2-98c5-590cffa0315b
```

- Archive: seven-byte ASCII magic `R025B01`, nonce12bytes, AES256GCM ciphertext,
  final authentication tag16bytes. Authenticate **all** data before restore.
- Encrypted manifest: nonce12bytes followed by AESGCM ciphertext+tag, same key/AAD.
- Manifest `encrypted_sha256` binds the complete encrypted archive;
  `archive_sha256` binds the plaintext PostgreSQL custom dump. Verify both hashes
  against the GCM-authenticated manifest; require its dump reference and
  authenticated `verified_at` to match the recovery receipt. Do not refresh an
  old backup's age by editing an unencrypted receipt.
- Recovery destination is a new local PostgreSQL18 disposable database/tmpfs,
  never the source. Feed authenticated plaintext through a private pipe to
  `pg_restore --exit-on-error --no-owner --no-acl`; compare90 table counts to the
  authenticated same-snapshot manifest and validate constraints. No plaintext
  archive/log or row output. Remove the disposable restored copy afterward.
- Operational recovery/restore, privileged ownership/ACL restoration and financial
  reconciliation require a separate incident procedure/authorization. The
  completed local restore is not PITR or permission/financial business sign-off.


### Formal shared-environment acceptance — final authorized window

The [responsible user's explicit decision](https://github.com/procopio420/rodada/issues/151#issuecomment-6183795233)
accepts the existing shared Railway demo as substitute for a physically separate
preview **for this Spec025 exercise only**, with verified recovery, exclusive QA
Venues, negative tests, Host/HMAC/TLS, pilot monitoring and mandatory flag-off plus
QA session containment. Shared-resource/deployment risk is retained explicitly;
no automatic PASS, PSP, operational money simulation or #152 canary is authorized.
The condition of a new authenticated Aderlan smoke was actually met on637b8e6:
Ana HTTPS login/read-only tables/Tabs/catalog, refresh and SSE/reconnect PASS,
new browser/native protocol sessions logged out. Do not publish/reuse credentials
as fixtures or reset pilot access. Repeat after rollback. Earlier statements
that the environment exception was pending are historical checkpoints.

### Mandatory final-window rollback order

For the already authorized exercise, record the exact source SHA and activation
deployment before running the browser matrix. Check GitHub main and SSH runtime
again immediately before changing the flag; a new commit requires a new inventory
and applicable gates. A guard refusal is an aborted attempt, not homologation.

Always finish with this order, including on a failed scenario:

1. Set only `RODADA_ENABLE_TENANT_HOST_UI=false` on the existing web service.
   Observe the resulting specific deployment reach SUCCESS; read back flag false
   and `RODADA_DEMO_SEED_ON_START=false`. Do not substitute another deployment ID.
2. Through private SSH in `/app/apps/api`, execute
   `python manage.py provision_spec025_ab --operation deactivate --apply`.
   Emergency containment must not depend on archive decryption or a fresh backup
   proof. If execution times out or refuses stale SHA, inspect actual runtime and
   QA state before a guarded retry; do not assume rollback happened.
3. Check both QA domain bindings inactive, every active QA membership suspended,
   staff/guest sessions revoked, guest mutations blocked and new native login/QR
   issuance denied. Witness concurrently active A/B staff/guest streams closing
   and their reconnects denied. Public QA root/manifest/BFF must return421.
4. Re-run the authenticated pilot read-only smoke and shared API/landing health.
   Compare foreign domain/order/ledger/catalog/table history digests to the
   pre-window snapshot; publish only equality booleans and scoped model names.
   Authentication/audit writes are excluded intentionally. Legitimate concurrent
   pilot operations can change a digest and require investigation, not deletion.
5. Keep QA history and all financial/audit records. Check operational QA
   Order/Charge/Payment/Refund counts remain zero and service retries created no
   duplicate Tab/occupancy. Financial test evidence is disposable-DB CI only.

Do not restore the operational database or select an old image to demonstrate
flag backout. Logical archive recovery is a separate incident operation. A
successful exercise does not authorize #152 canary or permanent flag activation.
