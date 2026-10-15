# Issue #130 — auditoria multitenant P0, 2026-10-14

Estado: auditoria de código/provas locais executadas; gates de CI e integração são rastreados no PR #153 e no comentário final da #130, com SHA exato. **Fechamento #130 BLOCKED pela prova real de borda, #151. Spec025 e wildcard de produção NÃO HOMOLOGADOS.**

## Identidade e ambiente

- Base atualizada por `git fetch origin`: `d5acc98f0267483ec3ca3a5154babccbcad88eb0`.
- Código auditado/corrigido: `42a14efcc1ac3e8eb156aef6d28fd67b8d33e6ae`, branch `audit/issue130-multitenant-p0`.
- PostgreSQL **17.6** local, cluster novo exclusivo da auditoria, TCP loopback 55430, usuário de teste `audit130`; pytest cria/remove seus bancos `test_*`. Web usa exclusivamente `rodada_web_e2e`. Nenhuma transação simulada foi criada fora desses bancos descartáveis.
- API Python 3.13.15/Django 5.2.17; Web Node 24.19.0/Next 16.3.8. Não houve alteração Android, DNS, deploy remoto ou consulta de banco operacional.
- A/B: `e2ea.rodada.bar`/`e2eb.rodada.bar`. API matrix cria operadores OWNER distintos, sessões Android, produtos, Tabs, Orders/Charges, Payments/Refunds e documentos independentes. SSE cria sessões/QR/domínios distintos; BFF reutiliza seeds E2E existentes.

## Evidência anterior, preservada sem extrapolar SHA

| Fonte | Estado verificado | Evidência |
| --- | --- | --- |
| #101 | CLOSED, sem merge; não copiado | [PR](https://github.com/procopio420/rodada/pull/101) |
| #116 | MERGED `4fc06b351ae5afe7640bbecfe8289f001c739707` | [API](https://github.com/procopio420/rodada/actions/runs/38478271708), [Web](https://github.com/procopio420/rodada/actions/runs/38478271803) SUCCESS nos heads do PR |
| #131 | MERGED `6bc4c278123ee9c61e6897f1026303dc72fd92a7` | [API](https://github.com/procopio420/rodada/actions/runs/38488927548), [Web](https://github.com/procopio420/rodada/actions/runs/38488927539) SUCCESS; review histórico era SELF_REVIEW |
| #140 | MERGED `c4c580a3b66ded5f893fc7ec80077a3dfefd66f9` | [API](https://github.com/procopio420/rodada/actions/runs/38562330476), [Web](https://github.com/procopio420/rodada/actions/runs/38562330857) SUCCESS nos heads do PR |
| Base `d5acc98` | somente Knowledge Base encontrado nesse SHA | [run](https://github.com/procopio420/rodada/actions/runs/38592048141); não é prova de API/Web |

## Matriz de fronteiras de confiança

Paths API abaixo relativos a `apps/api/`; Web a `apps/web/`. PASS significa controle testado no ambiente local descrito, não implantação. FAIL registra comportamento anterior reproduzido, seguido do resultado do patch. NOT TESTED/BLOCKED não equivale a PASS.

| Controle / fronteira | Implementação | Teste existente/ampliado | Falha potencial | Resultado | Evidência |
| --- | --- | --- | --- | --- | --- |
| Browser → Host/registry | `venue/domain_resolution.py`, `hostnames.py`, VenueDomain/migrations0008–0010 | `test_venue_domain_resolution.py`, `test_spec025_domain_lifecycle.py` | label confundida com slug, domínio desconhecido/inativo/não verificado/reassign | PASS local; UUID imutável e auditoria PostgreSQL | baseline 15 + suíte API final |
| Host → Next proxy/aliases/context | `proxy.ts`, `lib/server/venue-context.ts`, `lib/tenant-host.ts` | `tenant-routing.test.mjs`, `integration/tenant-hosts.spec.ts` | fallback para demo/cache entre hosts | PASS tenant3 e integração BFF focada2 em d77 | tenant 3; contexto/manifest `no-store` por Host |
| Browser → BFF/CSRF | `lib/server/auth-gateway.ts`, auth routes | tenant-hosts + session-refresh | forwarded-host/cross-Origin substitui autoridade, refresh cruzado | PASS integração BFF focada2 em d77, incluindo B/A | typecheck/build/auth4 e integração final |
| Cookies/session cache | auth/guest BFF, `session-refresh.ts` | tenant-hosts/session-refresh | Domain amplo, credencial no browser, refresh compartilhado entre hosts | PASS para host-only/HttpOnly/SameSite e cache por Host; Secure real NOT TESTED | TLS/produção #151 |
| BFF → HMAC | `venue/host_middleware.py`, `lib/server/venue-host.ts` | `test_spec025_host_security.py` | assinatura inválida/expirada, método/path trocado, Unicode500 | FAIL Unicode antes; PASS após rejeitar não ASCII; HMAC cobre timestamp/método/path/Host | regressão first-fail; suíte focada25 |
| Authority assinada → Django | middleware `split_domain_port`, registry/ALLOWED_HOSTS | host security parâmetros + portas443/3130/compat | porta inválida/lookalike tratado como legado | FAIL 6 casos antes; PASS após validação sintática/range e compat explícita | não é prova de atacante forjando HMAC forte |
| Segredo produção/pilot | `settings_production.py`, `deploy/railway/runtime-profile.sh` | `test_production_profile.py`, `test_railway_runtime_profile.py` | segredo ausente/curto/repetitivo aceito | FAIL antes; PASS startup/rejeição após patch | 12 produção/OAuth + 10 runtime; revisor executou preflight independente |
| Django → VenueContext | `access/services.py`, bearer auth, `assert_staff_venue` | host security, matrix, access tests | staff A no HostB; headers/query selecionando Venue | PASS 403 e ausência de mutação nos dois sentidos | matrix3; SSE/host25; BFF final |
| VenueContext → services/ORM → PostgreSQL | scoped services, locks/constraints | matrix, ordering/cash/ledger/provider/concurrency suites | IDOR ou replay antes autorização | PASS matrix A/B,B/A; PASS API746 em d77; gate do HEAD repetido no PR #153 | Order/Charge/Payment/Refund contados e replays com mesma chave local |
| PostgreSQL RLS | isolamento deliberadamente na API/ORM, DB compartilhado | não existe RLS como gate desta spec | acesso administrativo direto não equivale a sessão de Venue | NOT APPLICABLE à fronteira de autorização de clientes; DB privado é gate operacional | não alegar isolamento de credenciais de administrador do DB |
| Android → API compartilhada | reserved `api.rodada.bar`, StaffBearerAuthentication | matrix login platformANDROID/me/foreignTab; access API | hostAPI confundido com Venue, quebra compat nativa | PASS smoke do protocolo API; E2E em dispositivo NOT TESTED | matrix3; E2E Android+Web permanece #106 |
| QR/GuestSession → Tab | guest_access, generation/epoch, host guard | guest tests, tenant-hosts, SSE | token estrangeiro revela existência ou visita revogada aceita | PASS API/SSE746 e B/A BFF focado2 | foreign404, revoke/reconnect; integração final |
| SSE/ASGI → sync_to_async/outbox | #131 `read()` bind/finally, reconsulta domain/token por poll | `test_spec025_sse_stream_isolation.py`, realtime | ContextVar resetado, A/B misturados, revogação/reconnect/cursor cruzado | PASS local: ASGI real, concorrência A/B, staff/guest, sessão/domain/membership, replay/outbox simétrico | SSE+host25; sem benchmark de capacidade/ingress ao vivo |
| Assets públicos | PublishedIconAssetView/published_asset, filename exato; gestão scoped | quick_catalog + matrix | bytes não publicados/private path, alteração foreign | PASS origin: publicados portáveis A/A,B/B,A/B,B/A; alterado/unpublished404; foreign mutation404 | matrix3; contrato público abaixo |
| Recibos capability | ReceiptAccessToken SHA256/24h/revoke; SharedReceiptView station vazia/read-only/no-store | printing + matrix | adivinhar/expirar/revogar/alterar documento ou compartilhar segredo | PASS token válido portável, guessed/expirado/revogado404, POST405, foreign revoke404 | matrix3; snapshot limitado ao documento autorizado |
| OAuth PSP | cookie assinado sessão+hashstate, state staff+Venue+10min, consume lock | payment_readiness/MerchantCallbackTests + sumup | falsificado/replay/sessão revogada/Hostforeign; AccessServiceError500 | FAIL Hostforeign antes; PASS403 sem exchange/consume após patch | OAuth/produção12; transporte provider é double, não PSP real |
| Merchant/device/connection | scoped MerchantConnection/DeviceAuthorization; creds AEAD | sumup/merchant_disconnect/payment_readiness | connection foreign ou merchant errado confirma dinheiro | controles existentes preservados; PASS API746 em d77; gate do HEAD repetido no PR #153 | nenhum provider/merchant real consultado |
| Webhooks e workers PSP | provider/venue identity, inbox dedupe, evidence lookup | payment_provider/sumup/payment_readiness/concurrency | browserHost muda merchant, duplicate/out-of-order settle | controles e tests existentes inspecionados; suíte final abaixo | ingress/PSP real NOT TESTED; sem pagamento remoto |
| Financeiro/caixa/refunds | scoped lookup/Tab locks, #140 UUID Payment/Refund para CashMovement | ledger_payments/cash/concurrency + matrix | IDs foreign, alias mesma chave entre Tabs/Venues, reasonomitido500 | FAIL reasonomitido antes; PASS default vazio no serializer e scoped404/replay200 | matrix3; proteções #140 reutilizadas |
| Ingress/proxies/TLS → Next/API | nginx template Host original, stripping BFF em rawAPI, backends loopback | script preview + Docker smoke CI | headers externos confiados, porta pública API, TLS falso | **BLOCKED / NOT TESTED em preview real** | script exit22/HTTP421 manifest A; #151 bloqueia #130 |
| Rollback/canary | feature flag, domain disable, stable app/schema preservado | runbook/documentação | habilitar wildcard pela CI ou rollback destrutivo | documentação inspecionada; exercício operacional NOT TESTED | #151/#152; nenhum rollout autorizado |

## Política pública explícita (não mudar o modelo de produto por suspeita)

**Imagens:** a referência `ProductIcon.published_asset` publica bytes validados, convertidos em PNG, distribuíveis sem sessão e entre hosts. Publicar uma imagem é uma decisão de distribuição pública: cache `public, max-age=31536000, immutable` pode preservar bytes já distribuídos mesmo após remove/substituição; remoção bloqueia novas buscas na origem, não revoga cópias. Não publicar documentos privados, dados de Customer/Tab/Order, prompt/credenciais/provider secrets ou caminhos arbitrários. O endpoint confere icon e basename exatos; gestão é autenticada/scoped. `Product.active` não redefine retroativamente confidencialidade de bytes já publicados. Não há correção host-bound a aplicar a uma publicação intencional.

**Recibos:** link aleatório de 256 bits aproximados (`token_urlsafe(32)`, só SHA256 persistido) é capability bearer portátil entre hosts. Quem possui o link lê o snapshot daquele documento: Venue/Tab/rótulos/itens/totais e referências financeiras; esse é o conteúdo que o operador está compartilhando. Não concede login, impressão, alteração, acesso a outro recibo, production ticket, credenciais PSP/PIN/telefone/notas Customer. Validade24h/revogação no banco, `no-store` e `no-referrer`; URL token exige cuidado de compartilhamento. Acesso em HostB ao tokenA é PASS intencional, não IDOR; token inválido não revela existência. Revogação não apaga cópias baixadas pelo destinatário autorizado.

**OAuth:** callback externo usa API compartilhada e cookie OAuth host-only assinado pelo Django para sessão original e hashstate. `consume_authorization` verifica staff/Venue/TTL/single-use. Host canônico é restrição adicional quando há assertion validada. Exchange é proibido na sessão/Host incompatível; AccessServiceError agora vira resposta DRF403. Falhas/replay nunca autorizam confirmação financeira por si sós. BFF/tenant OAuth live não homologado; nenhum provider real foi usado.

**HMAC:** timestamp ±60s, método/path/Host; não cobre body/query nem possui nonce. Assertion isolada nunca substitui sessão/capability/idempotência. Replay dentro janela é risco de transporte restrito à fronteira interna confiável, não autorização adicional. Ingress precisa remover headers externos; loopback/privateTLS, segredo exclusivo, sem logs e sem exposição pública do backend. Len32/diversidade5 é piso de rejeição, não medição de entropia: provisionar segredo gerado criptograficamente e independente do Django secret. Demo continua fallback aleatório compartilhado no processo; pilot exige provisionamento antes migração. `settings_production` não é o perfil automático do Railway; preflight pilot também valida BFF secret.

## Execuções locais e limitações de SHA

As regressões foram escritas antes dos patches. FAIL anteriores provados: OAuth callback500, HMAC Unicode500, reasonomitido500, produção/pilot3 configurações inseguras e 6 authorities assinadas inválidas aceitas. Não houve exfiltração comprovada.

| Comando / escopo | Resultado executado | Ambiente/SHA |
| --- | --- | --- |
| PostgreSQL baseline host/domain/SSE | 15 PASS | base+deltas iniciais; não usar como SHA final |
| produção profile + MerchantCallbackTests | 12 PASS | patch candidato antes freeze |
| runtime preflight | 10 PASS | patch candidato; sem DB |
| nova matrix A/B,B/A | 3 PASS | patch candidato antes freeze |
| matrix + host security | 15 PASS | patch candidato antes últimos dois testes de Host |
| SSE + host security | 25 PASS | código equivalente a `42a14ef` (ordenação import subsequente) |
| `manage.py check --settings=rodada_api.settings` | PASS, 0 issues | código42a14ef; PG17.6 local |
| `makemigrations --check --dry-run --settings=rodada_api.settings` | PASS, no changes | código42a14ef |
| `npm run typecheck`, `test:tenant`, `test:auth`, `build` | PASS; tenant3/auth4 | antes freeze; final verificação abaixo |
| quality `--kind api`/`--kind web --base d5acc98` | PASS; Ruff0; Web0 | 42a14ef |
| ESLint full audit/incremental gate | PASS gate; 24 diagnostics históricos | base+deltas; gate final abaixo |
| preview script A/unknown | **BLOCKED** exit22: manifest HTTPSA HTTP421 | ambiente público não comprovado, base/patch script inalterado |

A primeira suíte API completa e Web91 foi iniciada enquanto o candidato ainda recebia testes; seus resultados são diagnósticos, não substituem CI do SHA congelado. Nenhuma suíte visual global foi pedida/executada: não há mudança visual; integrações funcionais continuam obrigatórias.

## Revisão independente

Revisor `/root/independent_security_review`, contexto novo sem autoria, leu skills/code-review/POS safety e os 12 arquivos do diff `d5acc98` → `42a14efcc1ac3e8eb156aef6d28fd67b8d33e6ae`, além dos controles existentes. **INDEPENDENT/R3/NO_FINDINGS_WITH_GAPS**, nenhum P0/P1 aberto. Identificou segredo fraco no runtime Railway fora do perfil production; corrigido e revalidado pelo revisor via preflight sem banco. `git diff --check` PASS. Não executou pytest/Playwright; não concedeu aprovação GitHub, deploy ou GO. Gates externos e CI final ficam com o integrador. Aprovação de plataforma por outra identidade, se exigida pelo GitHub, é distinta de review técnico independente.

## Gates finais / integração

PR de integração: [#153](https://github.com/procopio420/rodada/pull/153). O campo HEAD/checks do PR e o comentário final da [#130](https://github.com/procopio420/rodada/issues/130) registram o SHA final, runs e merge SHA após conclusão. Não inferir gate do HEAD a partir de um run de SHA anterior: o integrador reexecuta API/Web e confere todos os checks antes de merge. Uma atualização exclusivamente documental não altera a árvore API/Web já testada, mas seus gates de PR continuam obrigatórios.

| Prova executada | SHA/ambiente | Resultado/evidência |
| --- | --- | --- |
| API completa local após freeze | checkout8bf0789; árvore API igual a42a14ef/d77/41ce213; PG17.6 descartável | **746 PASS**, 919.11s; sem skips. Os deltas subsequentes são selector de teste Web, fixture de turno e documentação, sem delta API. |
| API CI manual | d77c7f9f7792b9a62eb5ddb951d3088c79fde34d; Actions PostgreSQL17 | **746 PASS**, 615.88s; [run38597077811](https://github.com/procopio420/rodada/actions/runs/38597077811), Django check/drift PASS |
| Web BFF tenant focado, código congelado | d77c7f9; PostgreSQL17.6 local + Next/Django reais | **2 PASS**, 24.7s, A/B e B/A; fixture corrigida para enviar QR selector junto ao cookie guest |
| Web typecheck/tenant/lint congelados | código42a14ef/d77; Node24 local | PASS typecheck/tenant3; lint incremental0 novos/fatais (24 históricos), Ruff0 e Webguard0 |
| Primeiro Web completo | iniciado antes freeze; banco dedicadoPG17.6 | **91 PASS**, 12.9min, diagnóstico; gate de CI HEAD continua obrigatório |
| Turno isolado CI | 41ce213ec00f3a982d3eee2d0222a1df5890cab3; Docker PostgreSQL17 | **PASS** [run38598086959](https://github.com/procopio420/rodada/actions/runs/38598086959): 30 regressões PASS, 8clientes/64Tabs, 1366 requests/1043mutations, delta204800centavos, exposure0, sem erros; restart DB/API/dispatcher/Web+64Tabs reconciliados |
| Docker smoke CI | 41ce213; container/DB descartáveis | **PASS** [run38598014419](https://github.com/procopio420/rodada/actions/runs/38598014419) |
| Roteiro turno/reconciliação local | script41ce213; DB novo rodada_demo no cluster55430, Uvicorn8131+dispatcher | **PASS** HTTP completo + API restart/verify: 4TabsCLOSED, charges9500/adjustments-1200/payments8900/refunds600/exposure0; caixa13700/discrepancy0; SQL read-only duplicateOrderKey/PaymentKey/itemCharge0 |
| Preview A/unknown | script inalterado; HTTPS público | **BLOCKED** manifestA421/exit22, #151 |

A execução API inicial **não foi PASS**: 727PASS/1FAIL (fixture Python carregada antes de sua atualização de BFF secret). A repetição congelada deu746PASS. A primeira tentativa de repetir Web focado falhou no startup por banco de fixture já povoado; recriado exclusivamente `rodada_web_e2e` descartável. A tentativa seguinte revelou ausência de selector QR no novo teste B/A (401 antes de upstream); selector corrigido, repetição2PASS. Nenhuma falha foi apagada ou convertida em PASS sem execução.

Os gates de turno iniciais [38596746197](https://github.com/procopio420/rodada/actions/runs/38596746197) e [38596751673](https://github.com/procopio420/rodada/actions/runs/38596751673), em8bf0789, **FAIL** em `demo-full-shift.py:287`: fixture antiga assumia REFUND_REQUIRED após qualquer parcial. Spec017 UX-34 exige MANUAL_REVIEW_REQUIRED/refund0 quando item600 é coberto por exposure4300. Script41ce213 preserva parcial+approval/replay/exposure3700 e acrescenta Tab independente fullypaid600+refund600/replay/close; sem mudança de domínio financeiro. O novo turnoCI passou, preservando ambas as provas.

Revisão independente ampliada a **41ce213ec00f3a982d3eee2d0222a1df5890cab3**, sem P0/P1. P2 documental (suite final descrita prematuramente como executada) corrigido emd77. Roteiro/replays/deltas conferidos pelo revisor; HTTP/CI conferidos pelo integrador. As revisões são registradas no PR153, sem autoaprovação formal GitHub.

**#130 permanece OPEN enquanto #151 não cumprir seu contrato.** Testes, CI e merge não homologam preview, wildcard ou piloto físico. #152 acompanha canary posterior. Não usar `Closes #130` no PR.

## Integração e complemento de provas — 2026-10-14

PR153 integrado em **110f970456b9b67c076020b0052a27674b0fc2df**, após API746/Web91/Docker/KB
SUCCESS no HEADacbc5c5. [API head](https://github.com/procopio420/rodada/actions/runs/38599251287)
746PASS/680.55s; [Web head](https://github.com/procopio420/rodada/actions/runs/38599251500)
91PASS/7.9min; [Docker](https://github.com/procopio420/rodada/actions/runs/38599250983)
e [KB](https://github.com/procopio420/rodada/actions/runs/38599251169) SUCCESS.
O merge também incorpora o PR150 (`8053b44`), integrado durante a CI: testsAPI
adicionais e navegação/status Guest. A árvore completa não é idêntica ao HEAD153;
revisão independente pós-integração110f970 não encontrou enfraquecimento de
Host/GuestSession/BFF/financeiro. [API main](https://github.com/procopio420/rodada/actions/runs/38601261533)
e [Web main](https://github.com/procopio420/rodada/actions/runs/38601261201) devem
ser conferidos no próprio SHA antes do relatório final, sem extrapolar head anterior.

Conferência da matriz identificou duas provas específicas ainda faltantes, sem
vulnerabilidade nova demonstrada. Complemento apenas de testes, baseado110f970:

- OAuth: amplia a regressão existente para **A/A200, B/B200, A/B403, B/A403**,
  operadores/sessões/states/merchants independentes; negativos validam código
  `VENUE_HOST_MISMATCH`, nenhum exchange/consume/connection. Replays restauram o
  cookie assinado original e retornam409 sem novos transport calls ou connections/audits.
  Transport é double explícito; não houve conexão PSP real nem efeito financeiro.
- Financeiro: **Refund IDs** estrangeiros no endpoint de reconciliação retornam404
  `REFUND_NOT_FOUND` nos dois sentidos antes de selecionar provider, mantendo
  contagens Tab/Order/Charge/Payment/Refund. Complementa Payment IDs já testados.
- Suíte focada `MerchantCallbackTests` + `AuditTwoVenueTests`: **9PASS/32.27s**
  em PostgreSQL17.6 descartável (candidato de testes, ainda antes do commit do
  complemento; gate final é seu PR/CI). Nenhuma mudança de runtime/API/BFF.

Probes HTTPS no HEADacbc5c5 para **A e B** terminaram421 no manifest/exit22;
[#151](https://github.com/procopio420/rodada/issues/151#issuecomment-6173300748)
preserva bloqueio. O relatório final da #130 registra o merge do complemento,
CI de seus SHAs e main; não transfere nem reduz o critério de borda.
# Existing Railway follow-up

[Checkpoint #151](railway-151-checkpoint.md) records the fresh public HTTPS
observations at base `bbaa147` and remaining operational gates. It does not
supersede the original separate-preview criterion or the audit evidence below.

## PR #159 — provisionamento e contenção seguros, 2026-10-15 UTC

Código congelado/revisado: `ca2e0903a27b49320c20d3e18c8772f97327eb30`,
base main `47043184408c090ddae33df17d4d72010603f764` após integração concorrente
do PR #118. Branch `ops/spec025-qa-bootstrap-safe`, [PR159](https://github.com/procopio420/rodada/pull/159).
O head final e seus gates são registrados no PR; commits documentais posteriores
não alteram as árvores API testadas. Não extrapolar CI do head antigo `a04e5b9`.

| Controle | Implementação/teste | Falha comprovada antes | Resultado e ambiente |
| --- | --- | --- | --- |
| Provisão inerte | `provision_spec025_ab`, `test_provision_does_not_enable_shared_api_login_before_activation` | Login nativo QA era permitido antes da ativação | PASS local: novos memberships SUSPENDED; ativação explícita restaura somente gestor reservado |
| Contenção de todos operadores QA | `test_containment_suspends_other_local_operators_without_affecting_foreign_access` | Segundo operador local permanecia ACTIVE e podia renovar acesso | PASS local: todos vínculos ACTIVE locais suspensos, versão/invalidation, sessões revogadas; acesso estrangeiro preservado |
| Colisão concorrente | `test_committed_foreign_login_claim_after_preflight_aborts_entire_provision` | Identidade estrangeira criada/commitada após preflight recebia MANAGER QA | PASS local: resultados reais revalidados sob locks; rollback integral A/B, vínculo estrangeiro intacto |
| Idempotência/serialização | `test_parallel_provision_is_idempotent_on_postgresql` e teste de repetição/piloto | Ausência de lock para namespace ainda inexistente | PASS local: advisory transaction lock; dois comandos produzem dois Venues, gestores, aliases, mesas e eventos de provisão, sem duplicação |
| Corrida com autenticação | Testes `test_containment_refuses_inflight_login_atomically_then_retry_revokes_it` e `test_containment_refuses_inflight_operator_switch_then_revokes_both_sessions` | DeadlockDetected reproduzido entre login e containment antes do patch | PASS local: NOWAIT/no_key, SQLSTATE55P03 vira REFUSE após rollback inteiro; retry contém sessões criadas pela operação concluída |
| Sessões/ASGI/SSE | `test_containment_ends_live_asgi_staff_guest_streams_and_denies_reconnect`, dois Venues e dois modos Host/native | Cobertura operacional do comando não existia | PASS local: quatro streams staff/guest ativos por caso encerram revoked, reconnect negado; QR novo e tokens antigos negados após containment |
| Estado reportado | `test_reprovision_after_activation_reports_preserved_state` | Rerun em aliases ativos anunciava inatividade | PASS local: estado preservado reportado corretamente; IDs/PIN hashes não rotacionados |
| Credenciais QA | `test_provision_rejects_shared_pin_before_writing` | PINs iguais não eram rejeitados | PASS local: PINs distintos exigidos antes das escritas; entropia aleatória continua obrigação operacional |

Executado em PostgreSQL **17.11**, container local exclusivo `rodada159-audit-pg`,
porta **127.0.0.1:55539**, banco de teste descartável, sem dados do piloto:

```bash
cd apps/api
# POSTGRES_* apontam exclusivamente para o container descartável acima.
python -m pytest tests/test_spec025_qa_provisioning.py \
  tests/test_spec025_host_security.py tests/test_spec025_domain_lifecycle.py \
  tests/test_spec025_sse_stream_isolation.py tests/test_spec025_audit_matrix.py \
  tests/test_railway_runtime_profile.py --ds=rodada_api.settings \
  --tb=short --reuse-db -o addopts='' -q
```

**67 passed / 56.91s** (inclui 16 regressões de provisão/contenção).
Django check:0 issues; migration drift:no changes; Ruff:0 findings;
`git diff --check` e KB check PASS. Antes das correções, quatro regressões
falharam no candidato antigo; o teste adicional de corrida reproduziu deadlock
antes de NOWAIT. Falhas de fixture SSE sem cursor foram corrigidas enviando o
cursor canônico, sem alterar o serviço nem remover assertions de segurança.
Revisor independente `/root/review_159`, contexto próprio sem autoria:
**INDEPENDENT/R3/NO_FINDINGS_WITH_GAPS** em ca2e0903, sem P0/P1/P2 reproduzível;
somente leitura e diff check executados pelo revisor, sem autoaprovação GitHub.

Revalidação pública nesta execução: DNS A/B/unknown/piloto/API via Cloudflare;
TLS validado por hostname, SAN `*.rodada.bar`/`rodada.bar`, expiração
2027-01-11T17:35:11Z. A/B e unknown retornam **421** em root/manifest/context,
inclusive com forwarded/BFF headers falsificados. Script obrigatório em **A e B**:
**exit22/HTTP421** no manifest. Aderlan health/ready/staff/context200; contexto
público permanece `Bar do Aderlan` sob headers forjados. API compartilhada
health/ready200, auth/me anônimo401; landing200/TLS válido. Esses são smokes
anônimos, não prova autenticada de pedido, dinheiro, SSE, Android ou stripping
de headers privados. Prova da origem Railway/SSL mode segue NOT TESTED.

GitHub deployment `7080524766` reporta main4704318 SUCCESS em
`rodada-aderlan-demo-20261009 / demo` (2026-10-15T00:23:30Z), confirmando o vínculo
GitHub→Railway. Não revela ID Railway/runtime/variáveis/backups. Railway CLI
**5.68.0** instalado; `whoami` inicialmente Unauthorized; autenticação oficial
browserless solicitada, não concluída nesta fotografia. Discovery do conector
informa Railway não instalado nesta sessão; nenhum MCP Railway disponível.
Comando de backup confirmado via help oficial:
`railway postgres pitr backup create --project <project> --environment demo --service <postgres-confirmed> --name pre-spec025-ab`.
**NOT RUN**: inventário privado/SSH, backup on-demand, recuperação verificada,
provision/activate/deactivate remoto, flag, homologação habilitada e rollback
operacional. Não houve escrita operacional, mudança DNS/proxy, criação de
infraestrutura, pagamentos reais nem exposição PostgreSQL. #151/#130 permanecem
OPEN; exceção ao preview fisicamente separado exige decisão formal, não inferida.
