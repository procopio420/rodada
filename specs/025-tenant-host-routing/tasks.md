# Spec 025 — Tasks

## Auditoria P0 #130 — checkpoint 2026-10-14

- [x] Fetch main, inventário #101/#116/#131/#140 e checks por SHA;
  [matriz/evidência](audit-130-evidence.md), base d5acc98.
- [x] Código42a14ef: regressões e correções OAuth/HMAC/authority/segredo
  production+pilot/reason opcional; preservar controles #116/#131/#140.
- [x] PostgreSQL descartável A/B,B/A financeiro/assets/recibos e SSE ASGI;
  smoke de autenticação Android na API compartilhada.
- [x] Contrato explícito de assets públicos e recibos capability portáveis,
  sem transformar publicação legítima em vulnerabilidade presumida.
- [x] Review técnico independente42a14ef, sem P0/P1 aberto; lacunas externas
  documentadas, sem autoaprovação GitHub.
- [x] API congelada local/CI746PASS, Web tenant focado2PASS, turno64Tabs/8clientes
  e restartPASS, DockerPASS; ver matriz por SHA.
- Gate de CI do HEAD e integração: PR153/relatório final #130 registra checks e
  merge SHA; integração somente após todos os gates verdes.
- [ ] **BLOCKED #151:** preview real de dois Venues/ingress/HMAC; script421.
- [ ] Fechar #130 somente após comprovar todos os critérios originais,
  incluindo #151. Canary separado #152; E2E Android+Web #106 preservado.
- [x] PR153 mergeado110f970 após headacbc API/Web/Docker/KB verdes;
  revisão pós-integração inclui o delta Guest do PR150 sem P0/P1.
- [x] Ampliar casos ausentes de OAuth simétrico/replay cookie original e
  Refund IDs foreignA/B,B/A; suite focada9PASS local, gates do complemento/main
  rastreados no relatório final130. Não alterar implementação sem falha provada.

## Existing Railway homologation #151 — controlled preparation

Authenticated follow-up: [runtime/backup checkpoint](railway-151-checkpoint.md#authenticated-checkpoint--2026-10-15-utc).
- [x] PR159 head7436deb: API849/Web98/KB PASS, independent final R3 review,
  merge18da010; deployment/main CI tracked separately.
- [x] Fresh MCP+private SSH: existing service/main/source, no staged changes,
  seed-off/flag-off/HMAC preflight, private PostgreSQL18.6, QA absent, pilot alias valid.
- [ ] **BLOCKED backup entitlement:** no backups/schedules; official create
  rejected because Pro is required. User decision pending; no operational QA writes.

Fresh PR159 checkpoint (2026-10-15 UTC), codeca2e0903:
[executed evidence](audit-130-evidence.md#pr-159--provisionamento-e-contenção-seguros-2026-10-15-utc).

- [x] Correct independently reviewed provisioning/containment findings test-first:
  foreign concurrent identity claim, all QA memberships, initial suspension,
  accurate repeat output and auth lock inversion.
- [x] Execute 67 focused PostgreSQL17.11 tests after merging main4704318 into
  the candidate; staff/guest ASGI streams and native API containment included.
- [x] Independent R3 review of aggregate ca2e0903: no reproducible P0/P1/P2.
- [x] Install Railway CLI5.68.0 and prepare official login/SSH/backup commands.
- [ ] Complete Railway login and fresh private inventory; CLI Unauthorized
  at start, connector not installed in this executor. No operational writes.
- [ ] Final PR159 API/Web/KB CI, merge, deployment verification and backup/restore.
- [ ] Operational A/B provisioning, real enabled edge proof, controlled flag
  approval, rollback and formal preview exception (if required). #151/#130 OPEN.

- [x] Fresh main/source and public DNS/TLS/HTTP revalidation; [checkpoint](railway-151-checkpoint.md).
- [x] Prepare seed opt-out and fail-closed preflight to preserve Aderlan on shared
  runtime restart; test-first 19 profile cases and independent R3 review.
- [x] Disposable Docker seed-preservation and same-build flag backout rehearsal.
- [ ] Restore all API/Web/Docker/KB gates on PR156 final SHA; do not merge while
  source/autodeploy and operational restart safety remain unverified.
- [ ] Connect Railway and inspect deployment, variable names, staged changes,
  DB connection, backup and eligible backout; no secret disclosure.
- [ ] Prepare/apply scoped idempotent A/B bootstrap after inventory, preserving
  Aderlan and append-only test ledger. No global simulation/PSP changes.
- [ ] Obtain specific approval for the concrete shared flag change and any
  necessary public DNS/proxy change, then execute real HTTPS A/B proof.
- [ ] Resolve original preview/rollback contract formally before issue closure;
  keep #151/#130 open until demonstrated, canary/rollout remains #152.

## P0 — Prerequisites (must land before tenant URL is exposed)

- [ ] [Backend] Registry/migration: public hostname -> immutable Venue UUID; normalization, uniqueness, verified/active state, reserved labels, audit.
- [ ] [Backend] Resolver endpoint/service and negative tests; safe ingress Host trust policy.
- [ ] [Backend + Web BFF] Login host binding; reject mismatched typed venue slug; session verification on every staff endpoint, refresh and operator switch.
- [ ] [Backend] Guest QR/table token and GuestSession host/Venue binding with foreign-token 404.
- [ ] [Security] Review staff + guest + financial route scoping, SSE feeds, async jobs, PSP webhooks, idempotency and offline replay; add isolation tests.

## P1 — Compatible UI and migration

- [x] [Web] Tenant-path rewrite matrix and navigation, keeping localhost and Railway URLs unchanged (PR #116 code; CI pending).
- [x] [Web] Contextual login on canonical host; retain typed Venue in legacy/local mode only (PR #116 code; CI pending).
- [x] [Web] Host-local install manifest/title/start URL and cookie/CSRF tests for two venue domains (PR #116 code; CI pending).
- [x] [Data] Migration added to map public alias `bardoaderlan.rodada.bar` to existing `bar-do-aderlan`; applying/validating on Railway is pending.
- [x] [Tests] Automated two-Venue Next BFF/Django HTTP E2E added: wrong-host QR, credentials, cookies, refresh and mutation (CI green still required).
- [ ] [Infra] Actual preview wildcard DNS + TLS and trusted ingress headers not yet provisioned/verified. Rollback runbook and synthetic health script implemented in `docs/ops/spec025-preview-rollout.md` and `scripts/verify-tenant-host-preview.sh`.

## P2 — Release and followups

- [ ] Activate canary only after all P0 safety tests pass and complete a simulated turn in each of two Venues.
- [ ] Migrate customer-facing links/QR and define redirects for legacy hosts after verification; no token-in-URL handoff.
- [ ] Remove compat hosts in a separate reviewed change after usage becomes negligible.
- [ ] Plan Organization/Tenant billing + multi-Venue permissions separately, not as an implicit rename of Venue.

## Visual follow-up — Establishment home

- [x] [Web branch] Build approved-brand header and icon-based launcher with 2 mobile / 3 tablet / 4 desktop columns.
- [x] [Web branch] Add two-Venue browser integration assertions for branding, links, breakpoints and overflow.
- [ ] [QA] Run Web CI and inspect rendered browser screenshots at 360/390/430, 768 and 1280+ before merge/deploy.
