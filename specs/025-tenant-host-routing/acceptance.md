# Spec 025 — Acceptance criteria

## Aceite operacional final — Lucas Procópio, 15/10/2026 13:50 UTC

**Gates1/2/3 PASS; sign-off explícito recebido após os resultados.**
[Registro do aceite e autorização de integração/fechamento](https://github.com/procopio420/rodada/issues/130#issuecomment-6193701006).
[Revisão R3 independente](https://github.com/procopio420/rodada/pull/183#issuecomment-6193411847)
sem findings P0/P1/P2; [CI das evidências](https://github.com/procopio420/rodada/actions/runs/38744120507)
SUCCESS. Integração PR183 e verificação do deployment resultante autorizadas,
com flagfalse/seedfalse e QA contido. O fechamento130 ocorre somente após esses
gates finais. Os trechos de pendência abaixo são fotografias anteriores ao aceite.
Sem rollout permanente, mudança DNS/proxy, PSP ou homologação Android física.


## Gate3 — janela executada, aceite operacional pendente (15/10/2026 UTC)

[Recibo auditável](evidence/gate3-window-20261015.json), [canary/runbook](../../docs/ops/spec025-gate3-canary.md)
e [autorização Lucas Procópio](https://github.com/procopio420/rodada/issues/130#issuecomment-6192900495).
Runtime congelado `c589ff0862b1a7702e12c20a00cffda6cb2f289e`; flag-on
`a9f59467-ccf7-4206-8fac-a3b1290ed722` SUCCESS; flag-off `09536564-28fc-4f0e-a54b-97856de54fbc` SUCCESS.
Seed-off preservado, sem alteração de fonte, DNS/proxy, schema, PSP ou dinheiro.

| Critério | Resultado executado |
| --- | --- |
| Gates1/2 | PASS reaproveitado do runtime/CI já aprovado; não é repetição global |
| Preflight Gate3 | PASS: backup lógico95/95 restaurado/constraints/GCM/hash/custódia; novo login piloto, edge19, responsável/janela autorizados |
| Canary HTTPS/browser | PASS: script oficial A/B;87 checks Chromium A/A,B/B,A/B,B/A, cookies, QR, Customer/logout, refresh, SSE/cursors, IDs/headers estrangeiros; disponibilidade QA reversível/idempotente restaurada |
| Observação | PASS na amostra:112 probes de saúde200 entre 2026-10-15T13:16:22.257861+00:00 e 2026-10-15T13:30:52.790514+00:00;15min de observação, runtime periódico e logs/métricas sanitizados no recibo; não é SLA contínuo |
| Piloto | PASS: navegador real14 checks antes/durante/depois, protocolo HTTP Android/HTTPS16 durante/depois, somente leituras e logout das novas sessões de auditoria |
| Rollback | PASS: flagfalse, deploymentSUCCESS/seedfalse, quatro streams staff/guest A/B recebem evento próprio e revogação, nenhum estrangeiro observado, reconnect/refresh/login/QR/perfil negados; contenção externa repetida |
| Integridade | PASS no escopo:23 grupos estrangeiros iguais antes/depois (UUID/slug/QR/Tabs/pedidos/ledger/caixa); QA Orders/Charges/Payments/Refunds0; histórico preservado |
| CASH histórico | PASS leitura:1 confirmado piloto,0 sem CashMovement,0 Venue/tipo incorreto; nenhuma correção ou reconciliação completa realizada |
| Estado final | QA421; domínios inativos, memberships suspensas, Guest bloqueado,0 sessões QA staff/guest não revogadas; piloto/API/Landing saudáveis |
| Android físico | NOT_RUN; protocolo HTTP PASS não equivale a aparelho físico/turno106 |
| Aceite operacional | **BLOCKED_SIGNOFF**: requer sign-off explícito pós-janela de Lucas; autorização anterior era da intervenção |

A contenção confirmou na terceira tentativa: primeira falhou por serialização,
segunda recusou operação QA concorrente (NOWAIT), terceira confirmou. Somente
falhas transitórias reconhecidas foram repetidas, em no máximo três tentativas;
guardas de escopo preservadas. Repetição externa deixou o banco inalterado.
Não se atribui causa raiz adicional sem evidência.

A primeira tentativa do browser encontrou comparação de JSON dependente da ordem
das chaves, com HTTP200 e restauração QA bem-sucedida; corrigida no executor com
igualdade semântica e fixture local, repetição87PASS. Um smoke durante a troca de
deployment teve14 cenários funcionais aprovados, mas foi corretamente invalidado
pela guarda de runtime; somente execuções estáveis contam. Falhas históricas
permanecem no recibo. Revisão R3 dos executores corrigidos não encontrou P0/P1;
a revisão dos resultados/CI final é registrada no PR183 e na issue130.

**Gate3 técnico executado; Spec025/issue130 ainda não encerradas.** Nenhum rollout
permanente ou expansão wildcard autorizados. PR183 contém a documentação/evidência,
sem merge/deploy adicional nesta janela.151/152 continuam encerradas pela
consolidação prévia em130; não reabrir nem tratar isso como homologação física.


## Histórico — preflight inicial de 15/10/2026 (superado pela janela acima)

Inventário/runtime/backup/smoke/finanças foram executados sem ligar a flag.
[Recibo](evidence/gate3-preflight-20261015.json) e
[observabilidade](evidence/gate3-preflight-mcp-20261015.json);
[runbook Gate3](../../docs/ops/spec025-gate3-canary.md).
Fonte runtimec589ff0/deploymentad2f5da5 SUCCESS, seedfalse/flagfalse, QA contido;
smoke autenticado16PASS, edge19PASS, CASH1comMovement/0gaps. Novo backup lógico
restaurado95/95/constraints PASS substitui o backup90tabelas para a futura janela.
Nenhuma escrita financeira nem ativação operacional Gate3 ocorreu.

Modo Cloudflare Full (strict) confirmado pelo responsável no chat12:59:33UTC,
registrado como atestado (consulta automática NOT_RUN). Gate3 preflight **BLOCKED**
apenas por responsável/janela/autorização específica ainda pendentes. Canary e rollback
Gate3 **NOT_RUN**, sign-off operacional ausente; manter130OPEN. Gates1/2PASS são
reaproveitados do mesmo runtime/CI, não nova homologação. E2E físico106 não executado.


## Histórico — resultados Gates1/2 de 15/10/2026

Esta seção e o [recibo sanitizado final](evidence/railway-ab-20261015-final.json)
substituem os bloqueios operacionais dos checkpoints históricos abaixo, sem
transformar tentativas interrompidas em PASS. Fonte auditada/deployada:
`14d3240f607523265f9fd0b972b515c1b549b4b0` (PR182); árvore inteira igual ao
candidato `1e96050f5d5fe216c74a6f7313b890f22d8cf003` revisado e testado.

| Critério | Ambiente/execução | Resultado/evidência |
| --- | --- | --- |
| Recuperação antes de escrita | Backup lógico privado cifrado PostgreSQL18.6; restore descartável18/tmpfs | PASS:90/90 contagens do mesmo snapshot, constraints, GCM/hash/recibo reautenticados; não é PITR nem restauração operacional |
| A/A, B/B, A/B, B/A | Chromium real HTTPS, run053703, deployment `fddbcc96-3f8d-4ed4-8d2e-61be7473f2e0` | PASS:173 casos, fonte/deployment estáveis, login/refresh/logout, cookies host-only Secure/HttpOnly, QR/Guest, perfil/claim/rotação, catálogo/mesas/grupos/serviço idempotente, SSE/cursors, IDs e sessões estrangeiros negados |
| Borda | Script oficial A/B; probes públicos, origem Railway e loopback Django | PASS:19 TLS/Host/HMAC/stripping/unknown; manifests distintos; HMAC inválido/ausente/expirado/adulterado403, unknownBFF421/raw400 |
| Concorrência e revogação real | Quatro streams ASGI staff/guest A/B no SHA auditado, flag já false | PASS:um marcador próprio por stream, zero estrangeiro observado; quatro `revoked`, refresh/access/reconnect/novo login/QR/perfil negados após contenção |
| Backout | Flag=false, deployment `c006312d-9a87-47b5-8b22-d3c21719fd31` SUCCESS, comando deactivate e repetição externa | PASS:aliases inativos, memberships suspensas, guest bloqueado, zero sessões QA staff/guest não revogadas; repetição idempotente |
| Piloto e API nativa | Login novo autorizado, HTTPS, somente leitura, antes/durante/depois | PASS:16 checks por smoke, Venue/capabilities, mesas/comandas/catálogo, refresh e SSE/reconnect, protocolo Android; novas sessões de auditoria logout; nenhum fluxo financeiro/pedido real escrito |
| Integridade | Comparação de estado em19 grupos fora do QA | PASS:iguais ao snapshot pré-janela; exclui autenticação/auditoria e QA, não prova ausência de writes revertidos |
| Dinheiro operacional | Readback final QA | PASS:Orders/Charges/Payments/Refunds=0;9 Tabs QA históricas preservadas, sem reset/exclusão |
| CI e revisão do código | API952, Web105 integrações, Docker e KB; release integrado952+turno HTTP/restart | PASS no candidato; API/Web/KB também SUCCESS no merge auditado; revisão independente R3 sem finding P0/P1 aberto |

Correções reais: PR174 elimina deadlock reproduzido entre rotações Customer A/B;
PR182 encaminha somente seis endpoints nativos Customer para Django e mantém
páginas guest opacas/stripping. A primeira prova posterior recebeu eventos próprios,
mas a contenção interna falhou: esse ensaio permanece FAIL. Contenção externa
sucedeu; na repetição final o commit interno passou na primeira tentativa. Não se
atribui causa definitiva ao erro anterior nem se afirma exploração. O executor
agora guarda diagnósticos sanitizados e só repete, no máximo três vezes, erros
transitórios reconhecidos; guardas de escopo permanecem obrigatórias.

**Contrato GitHub atual:** #151 e #152 foram encerradas por consolidação externa;
#130 foi ampliada para Gates1/2/3 e exige canary para fechamento. Estes resultados
comprovam a janela A/B/Gate2, não Gate3. #130 permanece aberta; canary, expansão
wildcard e E2E físico amplo Android/Web (#106) não foram executados. Cloudflare
Full/Strict administrativo e PSP real não foram homologados por estes probes.
A autorização de ambiente compartilhado está registrada explicitamente; não
constitui dispensa de provas ou autorização de rollout.


## Checkpoints históricos (preservados por SHA)

**Código da PR #116 foi mergeado na main em 13/10.** Os itens abaixo permanecem **PENDING ACCEPTANCE** até vincular testes, SHA exato, ambiente e sign-off. Item desmarcado não significa ausência do código, e CI verde não prova DNS/TLS nem operação física.

## Janela final autorizada — 2026-10-15

[Aceite formal e autorização específica do responsável](https://github.com/procopio420/rodada/issues/151#issuecomment-6183795233):
para este ensaio, o Railway compartilhado substitui o preview fisicamente
separado. Risco residual: recursos, ingress e deployment compartilhados podem
afetar o piloto. Controles compensatórios: backup lógico restaurado/autenticado,
Venues QA exclusivos, negativos simétricos, HMAC/Host/TLS, monitoração do piloto,
janela limitada e rollback com revogação. A decisão não dispensa testes nem
permite PSP/dinheiro simulado no banco operacional ou canary (#152).

- [x] Smoke autenticado novo do Aderlan em637b8e6, operador Ana autorizado: login
  HTTPS/BFF200, Venue correto, mesas/comandas/catálogo200, cookies host-only
  Secure/HttpOnly, refresh somente cookie200, SSEready/reconnect200; protocolo
  Android compartilhado200. Somente novas sessões, ambas logout204; nenhuma
  comanda/pedido/pagamento/caixa real alterado. PIN não consta das evidências.
- [x] Backup lógico reautenticado, A/B inspecionados contidos, TLS/HMAC/stripping
  revalidados no deploymentc9053025/637b8e6 antes da janela.
- [x] Autorização formal da flag temporária e de seu backout, sem nova solicitação.
- [ ] Executar janela browser/QR/guest/negativos e conferir recibos sanitizados.
- [ ] Desligar flag/redeploy, conter QA, provar revogações e repetir smoke do piloto.
- [ ] Finalizar evidências/CI/review e fechar issues somente após provas completas.

## Checkpoint operacional — 2026-10-15 UTC, antes da flag

[Execução e limites por SHA](railway-151-checkpoint.md#real-ab-staging-and-containment--2026-10-15-utc).
PR166 integrado4056adbd com API/Web/KB verdes; runtime avançou por PR164 para
b63b611, preservado e revalidado. Backup lógico privado autenticado/restaurado
substitui somente o backup oficial autorizado, sem Pro.

- [x] Provisionamento real A/B inativo/suspenso, IDs distintos, rerun sem mudança;
  preservação transacional dos registros preexistentes.
- [x] TLS público/origem, Host/HMAC/stripping reais nos dois SHAs; unknown BFF421,
  raw API400 fail-closed. Cloudflare Full Strict administrativo não verificado.
- [x] Login/refresh/logout e leituras próprias A/B na API compartilhada; credenciais
  cruzadas403; token cruzado em ASGI canônico403, sem payload estrangeiro.
- [x] Ensaio real de contenção de A/B em b63: dois SSE staff revogados, sessões
  encerradas, refresh/acesso401, reconnect421, novo login403; histórico preservado.
- [ ] Smoke autenticado Aderlan: credencial protegida indisponível no processo SSH;
  verificação manual solicitada, sem reset de acesso.
- [ ] Aprovação específica da flag compartilhada e exercício real de seu backout.
- [ ] HTTPS script/manifest e matriz completa browser/QR/guest/read/write habilitada.
- [ ] Exceção formal para substituir preview fisicamente separado pelo compartilhado.
- [ ] Fechar #151/#130 somente após os critérios originais; #152 continua rollout.

Os estados anteriores abaixo são fotografias históricas, não bloqueios atuais de
acesso Railway/backup nem prova de homologação. A/B terminaram este ensaio com
domínios inativos, memberships SUSPENDED, guest bloqueado e flag Web desligada.

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

Integração153: `110f970456b9b67c076020b0052a27674b0fc2df`; headacbc API746/Web91/Docker/KB
SUCCESS. [Complemento de provas](audit-130-evidence.md) amplia OAuth A/A,B/B,A/B,B/A
com replay do cookie original e testa Refund IDs estrangeiros em ambos os sentidos;
9PASS locais, CI/main registrados no relatório final130. Sem delta de runtime.

## Host mapping and DNS

Authenticated update 2026-10-15: [fresh runtime/backup checkpoint](railway-151-checkpoint.md#authenticated-checkpoint--2026-10-15-utc).
Railway access is resolved, PR159 integrated as18da010 after headAPI849/Web98/KB
PASS and independent R3 review. Runtime seed-off, flag-off, private DB and HMAC
preflight verified over SSH. Official volume backup was denied because Pro is required; the user-authorized
logical recovery substitute, actual provision and containment are now recorded
in the newer checkpoint above. A/B browser edge acceptance remains pending.
Do not interpret historical missing-access statements below as current status.

Current read-only Railway revalidation (2026-10-14, base `bbaa147`):
[checkpoint #151](railway-151-checkpoint.md). Public edge TLS is valid, A/B still
return 421, and current operational inventory/backup/rollback remain blocked by
missing Railway access. No deployment or acceptance is implied.

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

### PR #159 — safe QA provisioning contract (not edge acceptance)

Backup exception authorized by the user on 2026-10-15: use a privately streamed,
encrypted logical PostgreSQL backup over SSH without upgrading to Pro. Provision
and activation may accept `logical-sha256:<64 lowercase hex>` only with explicit
`--logical-backup-verified`, attesting a completed independent disposable restore
and integrity verification of that exact archive. This is not a Railway volume
backup ID, nor approval of a shared-preview exception or tenant UI activation.
The command cannot itself inspect operator-held backup artifacts; the operator
must attach real hash/source/destination/restore results before any write.

- [x] Logical references reject malformed hashes and missing restore attestation
  before any write; existing official Railway backup references remain compatible.

Local proof at code SHA `ca2e0903a27b49320c20d3e18c8772f97327eb30`:
PostgreSQL17.11 disposable, 67 tests passed and independent R3 review;
[matrix and limits](audit-130-evidence.md#pr-159--provisionamento-e-contenção-seguros-2026-10-15-utc).
These checks certify the command locally, not its execution on Railway.

- [x] Initial QA memberships are SUSPENDED; only explicit activation enables
  the reserved manager. Domains and guest mutations remain inactive/blocked.
- [x] Concurrent claims of reserved slug/host/login abort the whole provision
  without attaching an identity owned by another Venue. Repeated provision
  preserves state and reports it accurately, including after activation.
- [x] Containment suspends every ACTIVE QA membership, revokes staff/guest
  sessions and denies new shared-API login/QR issuance. Foreign memberships
  and sessions remain intact; activation restores only the reserved manager,
  never revoked credentials or other suspended operators automatically.
- [x] Concurrent auth locks cause an explicit, atomic refusal, never deadlock
  or partial success. A subsequent containment attempt revokes sessions created
  by the completed login/operator switch, with foreign access preserved.
- [x] Verify the above against disposable PostgreSQL, including a committed
  concurrent foreign identity claim and live ASGI staff/guest streams.

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

### Native optional Customer identity ingress regression

- [ ] The six canonical `/guest/customer/{register,login,context,claim,logout,password}/` APIs reach Django through the existing raw ingress, preserve methods and remove untrusted BFF assertions. Missing guest proof fails with JSON401; opaque `/guest/customer` pages and lookalikes remain on Next/BFF. Verify through the actual disposable Railway image before deployment.
