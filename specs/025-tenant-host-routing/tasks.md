# Spec 025 — Tasks

## Gate3 — preflight executado, operação bloqueada

- [x] main/runtimec589ff0/CI/staged/SSH, seed-off/flag-off e contenção QA revalidados.
- [x] Novo smoke autenticado Aderlan16PASS; edge19PASS; health/landing/API200.
- [x] Backup anterior90tabelas reautenticado; novo snapshot atual restaurado95/95,
  constraints/custódia/GCM/hash e remoção de destino verificados.
- [x] CASH histórico somente leitura:1confirmado comMovement;0gaps/foreign/kind.
- [x] Baseline privado23grupos e observabilidade real limitados, sem publicar digests.
- [x] Responsável atestou Full (strict) no chat12:59:33UTC; consulta API NOT_RUN.
- [ ] Obter responsável, janela/fuso e autorização específica da intervenção.
- [ ] Executar canary e backout reais, revisão R3 pós-janela e sign-off operacional.

[Recibo preflight](evidence/gate3-preflight-20261015.json);130permaneceOPEN.

## Estado final da janela A/B — 2026-10-15 UTC

- [x] Exceção formal compartilhada e backup lógico reautenticado/restore90/90.
- [x] PR174: corrigir deadlock Customer A/B reproduzido, CI/revisão independente.
- [x] PR182: corrigir ingress nativo Customer e packaging; API952/Web105/Docker/KB
  e release integrado952+HTTP/restart PASS, revisão R3; merge14d3240f.
- [x] Browser HTTPS real173PASS e script oficial A/B, Host/HMAC/TLS/headers/cookies.
- [x] Quatro streams concorrentes staff/guest: eventos próprios, revogação e replay
  negado; flag=false, QA contido, repetição de deactivate idempotente.
- [x] Smoke autenticado Aderlan antes/durante/depois; API Android protocolo PASS.
- [x] Comparação19 grupos estrangeiros iguais; QA financeiro0, histórico preservado.
- [x] Preservar falhas históricas e registrar limites em
  [recibo final](evidence/railway-ab-20261015-final.json).
- [ ] Aceite final CI/documentação e turno isolado do SHA final: rastrear PR175.
- [ ] Canary/Gate3: NOT_RUN, sem autorização. GitHub consolidou151/152 em130;
  não reabrir/desfazer consolidação nem fechar130 apenas pelo Gate2.

As listas abaixo são checkpoints históricos; pendências antigas de login,
backup, credenciais, aprovação temporária e prova A/B foram superadas acima.

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

- [x] Exceção de backup autorizada pelo usuário: lógico privado SSH sem Pro;
  snapshot/dump AES-GCM e restore18/tmpfs,90 contagens iguais/constraints válidas;
  [hash/ambiente/limites](railway-151-checkpoint.md#logical-backup-exception-and-recovery-proof--2026-10-15).
- [x] Integrar contrato `logical-sha256` + attestation após regressões,
  revisão independente e API/Web CI; só então provisionar A/B com esse backup.

Authenticated follow-up: [runtime/backup checkpoint](railway-151-checkpoint.md#authenticated-checkpoint--2026-10-15-utc).
- [x] PR159 head7436deb: API849/Web98/KB PASS, independent final R3 review,
  merge18da010; deployment/main CI tracked separately.
- [x] Fresh MCP+private SSH: existing service/main/source, no staged changes,
  seed-off/flag-off/HMAC preflight, private PostgreSQL18.6, QA absent, pilot alias valid.
- [x] PR159 deployment40f0c485 SUCCESS, exact runtime18da010 confirmed by SSH;
  deployed inspection and provision dry-run executed, no writes.
- [x] Resolver entitlement sem Pro por exceção lógica autorizada, arquivo cifrado
  e recuperação verificada; referência real usada no provisionamento protegido.
- [x] Provisionar A/B, provar rerun idempotente e executar autenticação nativa
  positiva/cruzada, HMAC/TLS/Host e contenção real com SSE concorrente.
- [x] Corrigir gate de imagem descartável sem skip: PR168, standalone contract
  incluído, Integrated release854PASS/428.63s no head f02d11d, revisão independente.
- [ ] Validar piloto autenticado, obter aprovação específica da flag, executar
  browser/guest HTTPS e backout da flag; exceção de preview ainda não aceita.
  [Checkpoint atual](railway-151-checkpoint.md#real-ab-staging-and-containment--2026-10-15-utc).

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
