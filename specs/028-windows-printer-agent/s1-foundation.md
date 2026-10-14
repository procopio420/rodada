# S1 Foundation — implementation contract

Base: main d5acc98. Risk R3 (auth/tenant/migrations). No Windows service,
pairing API, driver, submission or agent claims in this slice.

## Audit / adaptations before code

- Spec 015 already owns queue, leases, attempt tokens and conservative lease expiry.
  Reuse it unchanged. S3/S4 must bind agent + route + configuration version to the
  existing attempt, never add a second queue.
- DeviceRegistration requires a Venue, while unpaired installations cannot have one.
  PrintAgent has nullable Venue/device until pairing; paired identity requires both
  and a matching Venue. AgentCredential belongs to Access and references PrintAgent.
- Spec 015 calls CUPS a transport; persisted adapter enum is SPOOL, not CUPS.
- No executable agent claim endpoint in S1. A dedicated authenticated contract read
  proves machine identity and cannot expose receipts or create attempts. Version 1
  lives under /printing/agents/v1/. Staff authentication remains unchanged.
- Agent routes are stored disabled initially and not consumed by legacy bridge.
  Creating a route does not claim jobs or enable printing. S3 must explicitly introduce
  exclusive agent delivery ownership before enabling a routed endpoint; it must not
  let the legacy bridge execute an agent-owned endpoint.
- Agent lifecycle, printer health and submission outcomes have independent enums.
  ONLINE is heartbeat-derived, never proof of device availability or physical paper.
- Flag is typed per Venue, false by default. Disabling it denies device authentication
  but preserves bridge access and all history. Revocation remains possible with flag off.
- Credentials are 256-bit opaque tokens, hash-only server storage, fixed printing
  scope, expiry, atomic rotation and irreversible revocation. No StaffSession identity.
  Issuance is an internal Access service, not an unauthenticated provisioning API.
- Cross-model Venue consistency must be enforced in PostgreSQL, not only full_clean.
  Audit uses existing AuditEvent; machine diagnostics are not an arbitrary JSON log API.

## Gates planned

Disposable PostgreSQL: additive forward/backward migrations, schema constraints,
valid/invalid/expired/revoked credentials, staff/device separation, negative capabilities,
cross-Venue references/requests, rotation/revocation races, CAS and existing printing suite.
Lint/check/migration drift, typed standalone protocol check, independent R3 review,
PR CI. No hardware acceptance in S1.

## Network and retention policy

V1 routes initially accept literal RFC1918 IPv4/ULA IPv6 on port 9100 only;
DNS resolution/rebinding and configurable approved ports require a later explicit
allowlist contract. No public IP, loopback, link-local or metadata service destination.
Windows queue identifiers remain opaque service-context names; S3 must validate
shared-queue network destinations before any side-effectful call. No inbound listener.

Credentials expire in 30 days, rotation atomically revokes the previous credential;
no automatic resurrection. Audit and attempt history are retained, not removed when
an agent is revoked. Pairing hash cleanup and bounded heartbeat diagnostic retention
are S2 responsibilities; S1 does not ingest arbitrary telemetry or receipt data.

## Sequential progress

| Slice | Status | PR | CI | Blockers |
| --- | --- | --- | --- | --- |
| S1 Foundation | Implemented; local gates/review pass, awaiting CI/approval | [#149](https://github.com/procopio420/rodada/pull/149) | Running | CI and authorized merge |
| S2 Pairing | Pending | — | — | S1 approval and merge |
| S3 Printing MVP | Pending | — | — | S2 approval and merge |
| S4 Multiagent | Pending | — | — | S3 approval and merge |
| S5 Compatibility | Pending | — | — | S4 approval and merge (user sequential order) |
| S6 Distribution | Pending | — | — | S5, signing certificate and later physical stable gate |
| S7 Pilot | Pending | — | — | S6, Windows/printer access and real physical evidence |

## Independent review

R3 independent context `/root/s1_review` reviewed d5acc98 → 6ccd154.
Found P1: machine authentication did not compare the middleware-resolved Host Venue.
Fixed in 438769a, with a real signed BFF cross-Venue API regression.
Re-review 6ccd154 → 438769a: foreign context 403, own/native 200 through actual
view/authentication (credential retrieval mocked); no remaining reproducible findings.
Reviewer did not independently run DB integration. Status NO_FINDINGS_WITH_GAPS,
pending final PostgreSQL/CI. No platform approval, merge or deploy was performed.

## Executed local evidence (2026-10-14)

- Foundation candidate: 31 tests PASS on disposable PostgreSQL 16.2,
  including reverse/reapply migrations with legacy endpoint preserved, credential
  issuance race, rotation/revocation race, route CAS, constraints and tenant guards.
- Standalone protocol: mypy 1.18.2 `--strict`, 2 files PASS; Ruff PASS.
- Django system check PASS; migration drift check PASS (test settings).
- Added-line API quality gate: zero new findings, one legacy finding in full audit.
- Full API PostgreSQL regression and final signed-host regression: in progress.

The disposable PostgreSQL server is local only, launched from pgserver 0.1.4 bundled
PostgreSQL 16.2. This executor maps only UID 0; a test-process ownership view shim
was used solely for the local PostgreSQL binary. No shim or pgserver dependency is
part of Rodada source, migrations or CI. CI uses its standard PostgreSQL service.
No shared demo/production database, hardware, financial data, Windows service,
installer or physically printed output was used or certified.

## Final code gate — 5da5799 (2026-10-14)

- Full API foundation regression: **755 PASS**, 497.96 s, PostgreSQL 16.2;
  run started on foundation candidate before the Host/import fixes.
- Final Host/import code: **79 PASS**, 24.93 s, PostgreSQL 16.2, including
  **32 S1 tests** and all existing test_printing/test_printing_concurrency/
  test_printing_snapshots cases. No skipped tests or hardware claims.
- Signed BFF foreign Host: 403, same Venue/native: 200.
- Django check, no migration drift, zero full/API added-line lint findings;
  standalone mypy strict and Ruff PASS.
- API CI first run 38595417557 failed E402 (late model registration import).
  Corrected with top-level imports and explicit exports, without changing existing
  model bodies or relaxing lint. Re-review of final import diff found no issues;
  model registry/export/FK resolution check PASS in independent context.
- API/Web CI for 5da5799 running. Latest outcome and approval gate are tracked in
  PR #149; this evidence is a dated snapshot, not a merge or production sign-off.

Gate decision: **WAIT FOR CI**, then request merge authorization for S1 only.
S2 starts automatically after authorized and confirmed S1 merge, from refreshed main.
