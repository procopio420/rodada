# Etapa 2 — ensaio integrado do piloto Web

Atualização posterior: a limitação de cartão deste candidato motivou a
[slice local da etapa 3](pilot-stage3-external-terminal-2026-11-03.md).
Resultados e bloqueios abaixo continuam vinculados ao SHA da etapa 2;
implementação local posterior não reescreve essa fotografia nem declara GO.

Data: 03/11/2026. **CONCLUIDA como ensaio local, com impedimentos explícitos.**
Os três complementos foram executados: turno por UI no recorte CASH, 90 s sem
rede no navegador após commit de pedido/CASH e corrida de disponibilidade entre
dois operadores pela UI, no Bar e na Cozinha. Cartão pela UI segue impedimento
do escopo aprovado; não há PASS desse fluxo nem homologação física.
Registros de pendência anteriores abaixo são históricos e foram atualizados
pelos complementos. Concluir o levantamento não resolve o impedimento de cartão.
Resultado automatizado: PASS nos recortes executados. **NO-GO para produção**;
este relatório não encerra a Spec033 nem as issues315–319.

Autorização: “pode fazer”, após a conclusão da etapa 1 neste chat.
[Escopo aprovado](pilot-stage-1-scope-2026-11-03.md): Web, QR guest atual,
dinheiro e cartão externo; Android, impressora, PSP e QR híbrido adiados.

## Fechamento dos complementos — terceira lacuna, disponibilidade no carrinho

Autorização: “continue”, após o complemento de rede; reforçada durante a execução.
Novo [teste de corrida pela UI](../../apps/web/tests/integration/pilot-availability-race.spec.ts):
dois operadores reais de fixture (`STAFF` no Atendimento, `MANAGER` na estação),
em contextos e sessões distintos, na mesma Venue descartável. Produto/main
reconsultada: `67972d09200d43357b5b88dc0f64218967e4c24b`. Mesmo HEAD/branch
locais abaixo; teste e documentação sem commit, sem alteração do produto.

Em cada estação, o Atendimento confirma primeiro um pedido de referência pela
UI. Depois monta e envia pela UI um novo pedido misto BAR+KITCHEN. O teste retém
essa requisição antes de chegar ao backend; o segundo operador indisponibiliza
o produto pela UI. Somente após readback UNAVAILABLE a requisição original é
liberada ao servidor real. Nenhuma resposta HTTP, saldo ou disponibilidade é
fabricada. É uma ordenação determinística de eventos concorrentes, sem relógio
simulado nem chamada direta de mutação para indisponibilizar/enviar pedidos.
Helper de mesa do teste semeia somente contexto físico descartável; consultas
adicionais ao BFF são GET para conferir os resultados.

| Cenário | HTTP/código | Efeito após rejeição | Pedido anterior |
| --- | --- | --- | --- |
| Produto BAR esgota | 409 / PRODUCTS_NOT_CONFIRMABLE | Um Order anterior; charges/exposição 500→500; nenhum Payment; duas linhas no draft | Mesmo OrderItem NEW, depois PREPARING por clique explícito |
| Produto KITCHEN esgota | 409 / PRODUCTS_NOT_CONFIRMABLE | Um Order anterior; charges/exposição 1000→1000; nenhum Payment; duas linhas no draft | Mesmo OrderItem NEW, depois PREPARING por clique explícito |

O pedido misto é rejeitado inteiro: nem a linha ainda disponível produz novo
Order/OrderItem/cobrança parcial. Conferência de `orders` íntegros e dos totais
antes/depois passou. A rejeição é visível na tela; reabrir Adicionar itens → Ver
resumo mostra as duas linhas preservadas. A intenção de transporte rejeitada
definitivamente é limpa conforme contrato; isso não descarta o rascunho.
Indisponibilizar não cancela o item já confirmado, que continua preparável.
Ao final, produto reativado pela UI e readback AVAILABLE, sem alterar histórico.

**PASS: 2 testes, 23,9 s incluindo servidores**, sem retry na execução final.
`tsc --noEmit`, ESLint do teste e `next build`: PASS. Evidências sanitizadas:
[recibo BAR](evidence/pilot-stage2-2026-11-03/BAR-availability-race.json),
[recibo KITCHEN](evidence/pilot-stage2-2026-11-03/KITCHEN-availability-race.json),
[captura BAR](evidence/pilot-stage2-2026-11-03/BAR-rejected-cart.png),
[captura KITCHEN](evidence/pilot-stage2-2026-11-03/KITCHEN-rejected-cart.png) e
[manifesto com hashes](evidence/pilot-stage2-2026-11-03/availability-manifest.json).
Capturas inspecionadas: erro de confirmação e rascunho de dois itens, total
1500 centavos, distinto do saldo do pedido anterior.

Primeira tentativa encontrou erros de roteiro: depois da rejeição a UI volta
à comanda, então o resumo precisa ser reaberto para inspecionar as quantidades;
o clique de indisponibilidade é assíncrono e deve aguardar readback antes de
liberar o pedido. Corrigidos somente teste/sincronização, sem enfraquecer
asserções ou mudar produto. Traces brutos preservados apenas em
`.local/pilot-stage2/availability-first-attempt`, sem publicação de sessões.
Execução final confirmou BAR e KITCHEN. Cenários serializados para não propagar
fixture incompleta a outro cenário caso o primeiro falhe.

Reprodução: `playwright test --config playwright.integration.config.ts
pilot-availability-race.spec.ts`, com banco local descartável/variáveis descritos
abaixo. NOT_RUN neste complemento: suite completa, testes visuais completos
(nenhuma UI alterada), Android, operadores humanos e equipamentos físicos.
Trata-se de ensaio automatizado por interface, não observação de uso em bar real.

**Fechamento:** três lacunas identificadas receberam testes/evidência no recorte
especificado. Etapa 2 concluída como entrega do ensaio e backlog. Cartão externo
pela UI é **BLOCKED**, opção indisponível no recebimento do Atendimento observado;
implementação/correção não foi autorizada como parte deste teste. Revisão R3,
fiscal, operação e hardware continuam gates próprios. NO-GO produção.
Próximo responsável: usuário prioriza gaps (inclusive cartão) para etapa 3;
agente não inicia implementação, merge, deploy ou etapas posteriores automaticamente.

## Complemento — segunda lacuna, interrupção prolongada de rede

Autorização neste chat: “prox parte da etapa 2”.
[Teste novo](../../apps/web/tests/integration/pilot-network-outage.spec.ts):
dois cenários reais em Chromium/Next/BFF/Django/PostgreSQL, sem mocks de estado
ou relógio acelerado. Mesmo produto/SHA/branch/ambiente abaixo; alterações
locais apenas de teste e evidência, classe R2, sem mudança de produto.

Em cada cenário a requisição chega ao backend e confirma a transação; a primeira
resposta é descartada. Imediatamente todo o contexto do navegador operacional
fica offline por 90000 ms reais. `navigator.onLine=false` e falha de fetch
autenticado comprovam o corte do contexto, não apenas o bloqueio de um POST.
Um contexto separado, conectado e autorizado, consulta o estado canônico a
cada aproximadamente 15 s. A intenção local deve permanecer idêntica e a tela
não pode exibir confirmação que não recebeu.

| Cenário | Duração offline medida | Resultado canônico durante/depois |
| --- | ---: | --- |
| Pedido no Atendimento | 90106 ms | Um Order, saldo 2000 centavos, nenhum Payment; intenção preservada |
| Recebimento parcial CASH em /pos | 90146 ms | Um Payment de 1000 centavos, saldo restante 1000; um único movimento de caixa e acréscimo líquido de 1000 |

Após reconectar, recarregar a mesma aba e clicar duas vezes em Verificar mesmo
pedido/recebimento: exatamente duas tentativas ao backend no total (original +
replay), conteúdo byte a byte igual, mesmo ID canônico e nenhum efeito duplicado.
A intenção é removida somente após confirmação. São operações reais sobre
fixtures descartáveis; recebimento sintético, sem dinheiro/terminal/provedor real.

**PASS: 2 testes em 3,3 min**, execução sem retry e sem falha funcional observada.
`tsc --noEmit`, ESLint do novo teste e `next build`: PASS. Evidência vinculada a
hash do teste no [manifesto de rede](evidence/pilot-stage2-2026-11-03/network-manifest.json).
Recibos sanitizados: [pedido](evidence/pilot-stage2-2026-11-03/order-outage.json)
e [recebimento](evidence/pilot-stage2-2026-11-03/cash-outage.json), com IDs,
checkpoints, durações e hash do payload, sem tokens ou conteúdo de credenciais.

Capturas inspecionadas: [pedido sem rede](evidence/pilot-stage2-2026-11-03/order-offline.png),
[pedido recuperado](evidence/pilot-stage2-2026-11-03/order-recovered.png),
[recebimento sem rede](evidence/pilot-stage2-2026-11-03/cash-offline.png) e
[recebimento recuperado](evidence/pilot-stage2-2026-11-03/cash-recovered.png).
Offline mostra dados desatualizados/resultado não confirmado e a ação de
verificar a mesma operação; números cacheados não são tomados como saldo atual.

Reprodução: `playwright test --config playwright.integration.config.ts
pilot-network-outage.spec.ts`, com o PostgreSQL local dedicado, variáveis e
procedimento de preparação descritos abaixo. O teste fixa 90 s por caso e
150 s de timeout por teste, sem reduzir o intervalo para obter PASS.

Limites: emulação de rede do contexto Chromium, não queda física de Wi-Fi,
reinício do servidor/roteador, falta de energia, aparelho Android ou interrupção
de dezenas de minutos. Não comprova criação de um pedido/pagamento novo enquanto
já offline, nem outage prolongado de guest/KDS; cobre reconciliação após commit
incerto dos dois comandos acima. Esses limites não são apresentados como
homologação física. Não executados neste complemento: suite completa,
`test:visual` (sem UI alterada), revisão R3, fiscal ou infraestrutura remota.

Segunda lacuna entregue com PASS nesse recorte. **Etapa 2 continua EM_EXECUCAO**
para a corrida de disponibilidade no carrinho entre operadores pela interface.
Cartão pela UI continua sem homologação. Próximo recorte: agente executa quando
solicitado; NO-GO produção e etapas 3–6 preservados. Os complementos abaixo são
fotografias anteriores; pendências de rede neles foram atualizadas por esta seção.

## Complemento — primeira lacuna, turno inteiro pela interface

Pedido humano neste chat: “vamos focar em terminar a 2 etapa, faça a primeira
parte”. Executado o novo [teste de turno UI](../../apps/web/tests/integration/pilot-shift-ui.spec.ts)
com Next/BFF, Django e PostgreSQL reais, no mesmo produto e ambiente descritos
abaixo. Todas as mutações operacionais usam botões, formulários e seletores da
interface. O helper de conferência permite **somente GET**; não executa pedidos,
pagamentos, entrega ou ciclo da mesa por API. Fixture inicial contém apenas
catálogo, identidades, caixa disponível e recursos genéricos de teste.

Fluxo executado:

1. Login e cadastro da mesa com QR direto pela Gerência; abertura do caixa
   com fundo de 10000 centavos pela tela Caixa.
2. Abrir Tab contextual no Atendimento e enviar pedido BAR+KITCHEN pela UI;
   guest abre sua própria Tab na mesma ocupação e pede um item BAR pela UI.
3. Iniciar preparo e marcar pronto nas telas Bar/Cozinha; três entregas
   confirmadas na fila de Atendimento. Readback confirma a fila vazia.
4. Receber 500 centavos parciais, mantendo a primeira Tab OPEN com saldo 1000;
   receber os 1000 restantes e encerrar; a segunda Tab continua devendo 500.
   Receber os 500 da segunda Tab e encerrar. A mesa permanece OCCUPIED após
   ambas as quitações. Três Payments, saldos finais zero e nenhum erro JS.
5. Saída explícita, confirmação de liberação, início de limpeza e disponibilização
   pelos botões. Readback confirma CLEANING e AVAILABLE.
6. Conferir caixa, preencher 12000 centavos contados, confirmar fechamento e
   selecionar o turno fechado no histórico, tudo pela UI. Fundo 10000 + CASH
   2000 = 12000 esperados/contados, diferença zero.

**PASS:** um teste Playwright, 29,2 s incluindo servidores, viewport 390×844.
`tsc --noEmit`, `next build` e ESLint do novo teste: PASS. Gate KB: PASS,
49 documentos/310 links; conferidos 25 links locais dos três documentos afetados,
sem destinos ausentes, e `git diff --check`: PASS. PostgreSQL encerrado após o
ensaio. O turno usa uma conta
staff OWNER sintética nas superfícies e uma sessão guest distinta. Não comprova
troca simultânea de operadores, homologação humana ou funcionamento de rede física.
Recebimentos desta execução são exclusivamente CASH; cartão externo permanece
com a evidência anterior de API, sem ser contado como PASS de UI. A tela de
recebimento do Atendimento mostra Cartão indisponível no candidato examinado;
registrar pagamento CARD por API não supre essa limitação da interface.

Evidências sanitizadas: [IDs e totais do turno UI](evidence/pilot-stage2-2026-11-03/shift-ui.json),
[captura do fechamento](evidence/pilot-stage2-2026-11-03/cash-closed-ui.png) e
[manifesto específico](evidence/pilot-stage2-2026-11-03/ui-manifest.json).
Recibo inclui mesa/ocupação, duas Tabs, dois Orders, três Tasks, três Payments e
CashShift. Captura inspecionada: CLOSED, 12000 esperados/contados e diferença zero.
Os valores 11000 no ensaio anterior pertencem a outra execução (CASH+CARD).

Diagnóstico preservado: primeira tentativa navegava após observar Tab CLOSED
antes de o callback terminar de reconciliar o recebimento; recarga antecipada
mantinha intenção pendente e navegação protegida. Teste passou a aguardar a
limpeza canônica da intenção, sem apagar storage ou reenviar pagamento. Segunda
tentativa esperava resultado de caixa sem selecionar o turno no histórico;
ajustado o roteiro para selecioná-lo. Nenhuma alteração de produto ou asserção
enfraquecida. Traces brutos ficam somente em `.local/pilot-stage2/ui-first-attempt`
e `ui-second-attempt`, sem publicação de cookies/sessões.

Primeira lacuna concluída para turno Web em dinheiro. **Etapa 2 permanece aberta**
para os outros dois recortes solicitados: interrupção prolongada de rede e
indisponibilidade no carrinho entre operadores pela UI. Cartão pela interface
é limitação adicional do escopo aprovado a priorizar, sem ampliar silenciosamente
este recorte para implementação financeira. Nada desta execução fecha a Spec033,
dispensa revisão R3 ou autoriza merge/deploy. Testes completos/visuais, Android,
hardware e operação real não executados neste complemento, sem mudança de UI.

## Fotografia do primeiro ensaio — preservada abaixo

## Candidato, ambiente e limites

- Produto: main `67972d09200d43357b5b88dc0f64218967e4c24b`, revalidada
  por `git ls-remote`. Base documental/HEAD local:
  `1b6b20c74925f20d29e91f52dd9f96dc80669c89`.
- Branch: `codex/pilot-stage-1-scope`, com entregas locais sem commit.
  Código do produto inalterado. Novo teste de integração e documentação
  identificados por SHA-256 no [manifesto](evidence/pilot-stage2-2026-11-03/manifest.json).
- Windows, Node 24.22.1, Python 3.12.14, Django 5.2.19, Next 16.3.8;
  Chromium Playwright. Dependências Web instaladas com `npm ci`.
- PostgreSQL 17.11 em processo local, sem serviço Windows, somente
  `127.0.0.1:55432`. Cluster exclusivo `.local/pilot-stage2/pgdata`;
  `rodada_web_e2e` para Web, `test_rodada_web_e2e` criado/descartado por pytest.
  API HTTP em 8100 e Web em 3110; PostgreSQL real, sem substituição por SQLite.
- Fixtures sintéticas `web-e2e` e `other-e2e`, usuários de teste e valores
  fictícios. Nenhuma conexão com demo, banco remoto, PSP ou dinheiro real.
- Risco da entrega: R2, orquestração de teste e evidência de fluxos existentes;
  nenhuma alteração de autorização, ledger, migration ou interface do produto.
  Não houve revisão independente R3 do candidato: gate de release segue aberto.

O novo [ensaio único](../../apps/web/tests/integration/pilot-shift.spec.ts) usa
login, pedido guest e preparo pela UI real. Setup, pedido staff, entrega,
pagamentos e ciclo da mesa usam comandos reais do BFF no navegador, com readback
da API/PostgreSQL. **Não é um turno inteiro executado somente por cliques de
operadores.** Os outros testes exercitam Atendimento e recebimentos pela UI.

## Resultado por cenário

| Cenário | Resultado | Evidência e limite |
| --- | --- | --- |
| Mesa → duas Tabs → pedido staff BAR+KITCHEN e pedido guest | PASS | `pilot-shift.spec.ts`: mesma ocupação, duas Tabs distintas, dois Orders; replay staff preserva Order ID |
| Produção não inicia automaticamente | PASS | Itens NEW; cliques Iniciar preparo e Pronto no Bar/Cozinha; readback PREPARING e READY |
| Pronto → entrega | PASS | Três Task IDs associados aos OrderItem IDs corretos e à mesa; complete real via BFF; Atendimento UI coberto em `attendance.spec.ts` |
| Parcial → integral → fechamento | PASS | Parcial de 500 deixa 1000 e Tab OPEN; final de 1000 fecha primeira Tab; segunda continua devendo 500 e fecha após receber |
| Caixa conciliado | PASS | Fundo 10000 + dinheiro líquido 1000 = 11000; cartão 1000 separado; contado 11000, diferença 0, shift CLOSED |
| Fechar Tab não libera mesa | PASS | OCCUPIED após fechar a primeira e também após fechar a última Tab; saída explícita leva a DIRTY, CLEANING e AVAILABLE |
| QR/sessão antiga revogados | PASS | Contexto antigo retorna 403 / GUEST_SESSION_REVOKED após liberação; não significa que etiqueta física de mesa deva ser descartada |
| ACK perdido após commit de pedido | PASS | `order-intent` e `guest-order-intent`: abort real após resposta do backend; reload e replay do mesmo payload, mesmo Order ID, uma cobrança |
| ACK perdido após pagamento | PASS | `pos-cash-receipt` / `attendance-settlement-recovery`: reload/readback, um Payment e um efeito no caixa; cenário parcial e quitação |
| Rede e reconexão | PASS no recorte de transporte | Resposta perdida/abort/reload/retry nas suites citadas; não comprova Wi-Fi físico ou queda prolongada de toda a rede |
| Item esgota após carrinho | PASS API | `test_guest_access.py::test_guest_order_uses_canonical_pipeline_and_revalidates_stale_availability`: rejeição canônica sem cobrança; não foi uma corrida integral por cliques entre dois operadores |
| Disponibilidade com resposta incerta | PASS Web | `availability-intents`: BAR/KITCHEN em 360/390/430; readback e replay |
| Sessão expirada/revogada e permissão insuficiente | PASS | `workflows`, `tenant-hosts`, gateway CASH; recusa não aparece como sucesso vazio |
| Isolamento entre dois Venues | PASS | Next BFF + Django reais: credencial, replay, QR e realtime cruzados negados; hosts desconhecidos/inativos rejeitados |
| Concorrência / não duplicidade | PASS PostgreSQL | 37 testes focados: Order/Charge/audit, pagamento, refund, versão de disponibilidade, fechamento/caixa e release |
| Correções e revisão de divergência | PASS API/Web por recorte | Smoke API com cancel/remake/refund, caixa esperado 12700, contado 12600, diferença -100 explicitamente revisada; não misturar com caixa sem divergência do ensaio Web |
| Turno totalmente por UI, múltiplos operadores e rede física | BLOCKED para aceite operacional | Falta walkthrough humano nos equipamentos escolhidos; registrar na etapa 5, sem substituir por mocks |
| Android nativo, impressora, PSP, QR híbrido | NOT_RUN / fora do escopo aprovado | Nenhum aceite Android ou integração física transferido para este relatório |

## IDs, totais e artefatos

[Recibo Web sanitizado](evidence/pilot-stage2-2026-11-03/shift-web.json):
mesa `1d69c775-c29c-437d-9e3f-cdb0432a05ee`, ocupação
`032c6b6c-293b-457d-9e63-68f241b9ae69`, duas Tabs, dois Orders, três Tasks,
três Payments e um CashShift. IDs completos constam no JSON, sem QR ou sessões.

| Total do ensaio Web | Centavos |
| --- | ---: |
| Consumo confirmado | 2000 |
| Recebido em dinheiro, líquido de troco | 1000 |
| Recebido em cartão externo sintético | 1000 |
| Fundo inicial | 10000 |
| Caixa esperado / contado | 11000 / 11000 |
| Divergência | 0 |

O [recibo API](evidence/pilot-stage2-2026-11-03/shift-api.json) contém 39
respostas resumidas por allowlist de IDs, estados, códigos e centavos;
auth, tokens, PIN e QR omitidos. Foi capturado por instrumentação local do
APIClient durante o teste existente `test_full_shift_smoke.py`; não é tráfego
de navegador nem replay de produção. IDs são de fixtures descartadas pelo teste.

[Captura da Gerência em 390 px](evidence/pilot-stage2-2026-11-03/management-390.png)
inspecionada: exposição aberta zero após o ensaio. Uma captura não certifica
paridade visual ou acessibilidade de todo o produto.
Relatório HTML dos 40 testes e trace da primeira tentativa ficam em
`.local/pilot-stage2/baseline-web-report` e `first-shift-attempt`, apenas locais;
não publicar traces brutos com cookies/sessões de teste.

## Execução reproduzível e checks

Usar ambiente Python com `apps/api[dev]`, dependências de `package-lock.json`,
Chromium e PostgreSQL descartável. Variáveis do ensaio: `RODADA_TEST_PYTHON`
apontando ao Python real, `RODADA_E2E_POSTGRES=1`, `POSTGRES_DB=rodada_web_e2e`,
`POSTGRES_HOST=127.0.0.1`, `POSTGRES_PORT=55432` e usuário exclusivo de teste.
Nunca reutilizar conexão de demo/produção. Não guardar credenciais no relatório.

| Comando efetivamente executado | Resultado |
| --- | --- |
| `python manage.py check --settings=rodada_api.settings` | PASS, 0 issues |
| `python manage.py makemigrations --check --dry-run --settings=rodada_api.settings` | PASS, nenhuma mudança |
| `pytest tests/test_full_shift_smoke.py --ds=rodada_api.settings -v` | 1 PASS; repetido com captura sanitizada, 1 PASS |
| `pytest --ds=rodada_api.settings tests/test_order_intent_concurrency.py tests/test_payments_concurrency.py tests/test_guest_access.py tests/test_availability_commands.py tests/test_release_concurrency.py tests/test_release_native_concurrency.py -v` | 37 PASS |
| `next build`, com API local | PASS, compilação e TypeScript |
| `tsc --noEmit`, após novo teste | PASS |
| `node --experimental-strip-types --test tests/session-refresh.test.mjs tests/tenant-routing.test.mjs tests/backend-fetch.test.mjs` | 14 PASS com Python explícito |
| `playwright test --config playwright.integration.config.ts workflows.spec.ts attendance.spec.ts order-intent.spec.ts guest-order-intent.spec.ts attendance-settlement-recovery.spec.ts availability-intents.spec.ts tenant-hosts.spec.ts attendance-release-occupancy.spec.ts pos-cash-receipt.spec.ts` | 40 PASS, 3,3 min; padrão tenant-hosts também seleciona blocked-tenant-hosts |
| `playwright test --config playwright.integration.config.ts pilot-shift.spec.ts` | 1 PASS, 16 s incluindo servidores |
| `python -m unittest discover -s apps/web/tests/integration -p test_e2e_db_guard.py -v` | 6 PASS |
| `python scripts/check_agent_kb.py` | PASS, 49 documentos, 310 links após indexar este relatório |
| `python -m unittest discover -s scripts/tests -p test_check_agent_kb.py` | 5 PASS |

Os executáveis acima foram invocados pelos caminhos locais disponíveis, sem
alterar os scripts do produto. Primeiras tentativas preservadas como diagnóstico:
pnpm sem lockfile recusado (resolvido com npm ci); testes backend-fetch sem Python
explícito falharam no setup (14 PASS após configurar); reinício Web sobre fixture
remanescente falhou por slug duplicado (flush exclusivo no banco local dedicado);
novo ensaio leu NEW imediatamente após clique, antes do commit assíncrono. O teste
foi corrigido para aguardar readback PREPARING, sem trocar estado esperado,
enfraquecer asserções ou alterar produto. Execução final passou.

NOT_RUN: suite completa API/Web, `test:visual` completo (nenhuma UI alterada),
testes Android, carga/pico prolongado, dispositivos físicos, PSP, fiscal,
backup/restore/rollback e retenção/scheduler. Não houve CI remota desta entrega.

## Impedimentos priorizados e continuidade

Nenhuma falha funcional de produto reproduzida nos recortes executados.
Isso não prova ausência de defeitos fora desses cenários.

| Prioridade | Pendência | Próximo responsável / etapa |
| --- | --- | --- |
| P1 de rollout | Revisão R3 independente, backup/restore/rollback técnico e retenção periódica observável não comprovados | Revisor e operação, etapa 4; REVIEW_BLOCKED até revisão válida |
| Bloqueador operacional | Fiscal/contingência, nomes dos operadores, equipamentos/rede e janela/limites sem confirmação | Usuário/responsável do bar, antes das etapas 5–6 |
| Bloqueador de homologação física | Walkthrough humano, rede real, toque/foco/fonte e equipamentos sem evidência | Operadores + agente, etapa 5 |
| P2 conhecido, não revalidado aqui | Undercount por falha na observação de produção, issue319 | Priorizar teste/correção na etapa 3/4; métricas não podem bloquear vendas |
| Opção adiada | Retirada rápida PR314 e UX2 completa de produção | Usuário prioriza se houver necessidade; etapa 3 não iniciada |

GO limitado à continuidade de preparação local no escopo aprovado. NO-GO para
produção. Etapa 2 entregue com limites e bloqueios explícitos; etapa 3 depende
de priorização, etapas 4–6 mantêm seus próprios gates. Não iniciar outras etapas
automaticamente, fechar issues de aceite global ou interpretar isto como deploy.
