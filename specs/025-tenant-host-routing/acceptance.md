# Spec 025 — Acceptance criteria

**Código da PR #116 foi mergeado na main em 13/10.** Os itens abaixo permanecem **PENDING ACCEPTANCE** até vincular testes, SHA exato, ambiente e sign-off. Item desmarcado não significa ausência do código, e CI verde não prova DNS/TLS nem operação física.

## Auditoria #130 — evidência de 14/10/2026

Base `d5acc98f0267483ec3ca3a5154babccbcad88eb0`; correções e testes no código
`42a14efcc1ac3e8eb156aef6d28fd67b8d33e6ae`. A [matriz completa](audit-130-evidence.md)
registra controle, implementação, teste, falha, resultado e ambiente/SHA.
Os PASS locais são separados de CI final/merge e do aceite operacional abaixo.

- [x] Regressões test-first de OAuth Host mismatch500, assinatura Unicode500,
  authority inválida/lookalike, segredo BFF produção/pilot e reasonomitido500.
- [x] Nova prova PostgreSQL17.6 A/A,B/B,A/B,B/A de finanças, idempotência,
  ausência de efeitos estrangeiros e capabilities públicas de asset/recibo.
- [x] Revalidação SSE ASGI/sync_to_async, outbox/reconnect nos dois sentidos,
  sessão/domínio/membership revogados e API compartilhada.
- [x] Revisão técnica independente do código42a14ef sem P0/P1 aberto; status
  `NO_FINDINGS_WITH_GAPS`, sem aprovação de produção/GitHub.
- [x] API completa congelada local746PASS e CI746PASS emd77; BFF focado2PASS
  A/B,B/A. Turno41ce213PASS (64Tabs/8clientes/restart), DockerPASS.
- Gate do HEAD final e merge SHA: [PR153](https://github.com/procopio420/rodada/pull/153)
  e relatório final da #130, conforme [registro executado](audit-130-evidence.md).
  O integrador exige API/Web verdes no HEAD antes de merge; não extrapolar SHA anterior.
- [ ] **BLOCKED #151:** prova real ingress/Host/HMAC e preview A/B. Script em
  14/10 retornou exit22/HTTP421 no manifest de e2ea.rodada.bar; não demonstra
  cookies Secure, stripping externo, canário ou operação crítica em preview.
- [ ] Rollout/canary e rollback operacional: [#152](https://github.com/procopio420/rodada/issues/152),
  após os gates P0. Android+Web completo permanece #106.

**Auditoria P0 concluída ≠ wildcard de produção homologado. #130 continua aberta
enquanto seu critério de borda estiver bloqueado; #151 não transfere nem reduz
esse requisito de fechamento.** Assets publicados e recibos por capability são
portáveis intencionalmente; A/B nesses GETs é PASS autorizado, enquanto gestão,
sessões, QR e finanças devem negar acesso cruzado.

## Host mapping and DNS

- [ ] A `VenueDomain`-equivalent, unique and audited registry resolves `bardoaderlan.rodada.bar` to the seeded Venue ID whose slug remains `bar-do-aderlan`.
- [ ] Reserved hostnames cannot be claimed; unrecognized/disabled/lookalike/invalid hostnames fail closed (404 or 421), with no default/demo fallback.
- [ ] Reverse proxy and application agree on the normalized trusted Host. Browser-supplied `X-Forwarded-Host`, `X-Rodada-*` or `?venue=` cannot choose a different Venue.

## Navigation

- [ ] `/cozinha`, `/gerencia`, `/caixa`, `/bar`, `/atendimento`, `/relatorios`, and `/m/:token` resolve to existing modules on the same Venue hostname; paths, subpaths, query strings, methods, assets and SSE survive.
- [ ] Per-host app manifest/title/start URL is correct; authenticated navigation never changes hostname unexpectedly.
- [ ] Root/legacy hosts and Railway/local demonstration paths continue functioning; existing Android flows remain intact.

## Authorization and isolation

- [ ] Login on host A cannot authenticate venue B even with a valid B operator/PIN, and never sets B's staff cookie on A.
- [ ] Staff session from host A replayed on B yields 403 `VENUE_HOST_MISMATCH`; both reads and writes fail before any B data is returned/changed.
- [ ] Token refresh, operator switch and restored browser session cannot bypass host/session Venue binding.
- [ ] Cookies are host-only, secure in production, httpOnly (where applicable), and cannot be read/reused by sibling tenant host through domain scope.
- [ ] Guest QR/guest session valid on A is rejected on B without exposing the existence of the token (404); stale QR remains invalid after occupancy generation changes.
- [ ] Guessed foreign IDs on ordering, payments, refunds, cash, catalog, management and table endpoints cannot read or mutate another Venue.
- [ ] SSE/cursor/outbox, retry/idempotency/offline replay, audit and provider callbacks show tenant partitioning in positive and negative tests.
- [ ] Two independently seeded Venues can run end-to-end in parallel, without cross-tenant state leakage.

## Operational

- [ ] Wildcard HTTPS, Host routing, explicit app/DB trust boundaries and logging are configured in preview and verified (not inferred).
- [ ] Switch-on is behind a documented rollback gate; no unsupported production readiness claim.

## Staged P1 evidence (not release approval)

- [ ] `npm run test:tenant` — path/host unit regression, `apps/web/tests/tenant-routing.test.mjs` (CI result required).
- [ ] `npm run test:integration` — independent Venues in `start_api.py`, BFF + Django assertions in `tenant-hosts.spec.ts` (CI result required).
- [ ] `bash scripts/verify-tenant-host-preview.sh` — preview wildcard HTTPS, manifest, reserved/unknown host and health (real DNS/TLS not yet configured).
- [ ] Aderlan shift and P0 safety gates on the merged #116 code at the current release SHA, followed by manual operator/QR browser verification and canary approval.

## Establishment launcher UI (visual follow-up; not a tenant-security sign-off)

- [ ] Verified tenant root displays the approved Rodada logo, the resolved Venue name and an accessible enter/switch operator link to `/staff`.
- [ ] All five full-card module links point to the existing same-origin paths and remain protected by existing auth/capability gates.
- [ ] At 360/390/430, 768/1024 and 1280/1440px, the grid renders 2/3/4 columns respectively, card tap targets are at least 44px tall, and the page does not overflow horizontally.
- [ ] Browser/keyboard review covers focus, long venue name, mobile touch and reduced-motion behavior; integrate the two-Venue Playwright assertion without replacing the security checks above.
