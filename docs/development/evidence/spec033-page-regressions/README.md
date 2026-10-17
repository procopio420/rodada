# Spec 033 — regressão das páginas Web

Escopo: migração de seletores de testes existentes para a composição real de
páginas da PR #224. Não substitui testes de dinheiro por mocks, não modifica
useOrderIntent nem contratos da API. O fluxo usa Comanda → Adicionar itens →
resumo opcional ou envio direto → Conta, retornando pelo contexto da mesa.

Os cinco arquivos cobrem cancelamento com reversão canônica, rascunhos isolados
por Tab, referência/estação histórica após reload, repetição com preço atual e
ACK perdido, e seleção de Tabs anteriores à primeira página em mesa compartilhada.
As verificações financeiras, identidade do pedido, payload/chave de replay,
snapshot original, pagamentos e ocupação são preservadas.

Base: d6815f40; helper do integrador e0b15b1b. Migração inicial: 273966f8.
Typecheck e build executados com sucesso antes da primeira execução.

A execução inicial PostgreSQL 17.6 usa banco descartável rodada_web_e2e,
loopback 55638, API 8138 e Web 3138. O reset foi precedido por verificação de
host, porta, nome e ausência de outras conexões. Resultado final e correções
serão acrescentados após término; esta nota não declara a suíte aprovada.

Gaps de produto encontrados na composição inicial: o histórico da Conta não
oferecia repetir rodada, o atalho na Comanda bloqueava a repetição com rascunho,
e os estados dos itens na Conta apareciam como enums sem tradução. O integrador
corrigiu em 9cbe5a01/26f71a61. A ação histórica exige comparação visual e decisão
explícita de paridade; a execução funcional não concede esse aceite.

## Execução inicial (antes das correções)

Comando: `npm run test:integration -- attendance-removal.spec.ts tab-drafts.spec.ts attendance-order-status.spec.ts repeat-order.spec.ts table-entry.spec.ts --output=test-results/page-regressions`.
O filtro de nomes também selecionou os sete testes Guest/POS de repetição.
Resultado observado: 11 passaram, dois falharam, um interrompido e cinco não
executados. A interrupção local SIGINT, após comprovar a ausência da ação de
repetição, evitou repetir timeouts da mesma causa em outras larguras. Não foi
cancelado workflow CI. Logs preservados em `/tmp/ux2-page-regressions-tests.log`.

Passaram os quatro cenários canônicos de confirmação/estação/reload/produção
(360/390/430/1280), os quatro Guest repeat e os três POS repeat. A remoção
real efetuou a primeira reversão (quantidade 3→2, saldo 30→20) e falhou em
seletor textual legado; a repetição falhou pela ação ausente na Conta. Nenhum
destes resultados é registrado como aprovação integral.

A composição de teste recebeu 9cbe5a01, 8118b2ea, 26f71a61 e 4c6ff132 do
integrador. O teste de remoção preserva o estado traduzido Novo e ausência de
Cancelado na lista ativa; o subtotal usa o BillSummary real. O teste de
rascunhos aguarda a confirmação canônica antes de consultar o ledger da Tab B.


## Revalidação após interrupção do ambiente — 17/10/2026

Fonte `0e8e5dd4` recompilada; build e typecheck passaram. PostgreSQL 17.6
foi recuperado do desligamento anterior e iniciado explicitamente em loopback
55638. Antes de cada reset foram verificados host/porta/nome e zero outras
conexões ao banco descartável `rodada_web_e2e`. API 8138/Web 3138 exclusivas.

Execução de nove testes: **7 passaram e 2 falharam** (3,1 min). As quatro
larguras de confirmação/estação histórica/reload/produção passaram, assim como
rascunhos 390/430 e entrada de mesa compartilhada nas três larguras. Remoção
falhou por seletor exato `Novo` em um parágrafo que também contém o item;
rascunhos 360 falhou na transição de Voltar para Mesas do helper (snapshot na
página da mesa; os outros dois tamanhos passaram). Log versionado em
`run-nine-before-selector-fix.log`; não se considera a suíte aprovada.

A correção da remoção exige o texto completo do item com o estado traduzido,
sem remover a assertion do estado. O laço de larguras da entrada de mesa perdeu
apenas uma variável de índice não utilizada. ESLint dos cinco arquivos passou.
Execução dirigida subsequente: **4/4 passaram** (46,3 s), removendo 3→2→0 com
reversão canônica, e repetindo rodada em 360/390/430 com preço atual, mesmo
payload/UUID no replay, OrderID único, ledger e snapshot histórico preservados.
Log `run-removal-repeat.log`. O helper ainda precisa corrigir a sincronização
antes da revalidação final; estes resultados não concedem aceite de paridade.


## Revalidação final com sincronização dos retornos

Helper do integrador `6afc602f` integrado como `d051f84a`: aguarda a comanda
ficar oculta e a presença da mesa ou da navegação real antes de voltar à lista.
Não aumenta timeouts nem substitui cliques por chamadas da API. Typecheck e
ESLint passaram. A primeira execução dos 12 cenários produziu **11/12 PASS**
(3,9 min): rascunho 430 falhou após cancelar o descarte e clicar Enviar, sem
POST de confirmação da Tab B no trace. O draft permaneceu intacto. O teste
verificava o item atrás do diálogo sem aguardar explicitamente sua remoção.

Acrescentada a assertion de diálogo de descarte oculto após Voltar, antes de
verificar o rascunho e enviar. Nenhuma assertion de confirmação, ledger,
quantidade, UUID, payload ou isolamento foi removida. A execução dirigida dos
três rascunhos passou **3/3** (47,5 s). A causa interna do clique perdido não é
provada por um resultado verde; a sincronização exige agora o fim observável
da etapa anterior, e os resultados falhos ficam preservados.

Execução integral final com a sincronização explícita: **12/12 PASS, 3,3 min**,
sem retries. `run-twelve-verified.log` contém o comando e cada resultado.
Cobertura: referência e estação histórica canônicas em 360/390/430/1280;
transição real de produção; reversão financeira de item confirmado;
repetição com preço atual/ACK perdido e replay idêntico em 360/390/430;
rascunhos A/B/C isolados e confirmação independente em 360/390/430; mesa
compartilhada com Tabs anteriores à primeira página e pedidos no destino certo.

Esta evidência cobre os cinco arquivos de integração, não a regressão Web
inteira, Android, fonte ampliada, paridade lado a lado ou homologação operacional.
Nenhum épico é declarado aceito por este resultado. Sem merge ou deploy.
