# Revalidação — Spec 026 T01 e recortes T02/T03a/T03b

Data: 12/10/2026. Base: `main` em `ad5d64f`, mais alterações locais desta slice.
`plan.md`/`tasks.md` já estavam modificados antes desta execução; preservados.
Worktrees existentes preservadas. Não houve pull adicional, commit, push, merge
ou acesso à demo compartilhada. Nenhuma versão publicada foi verificada.

## Evidência e classificação

Presente significa lacuna encontrada na base integrada, com inspeção ou teste
identificado. Parcial significa melhoria integrada ou apenas parte do achado
confirmada. Resolvido exige evidência no escopo indicado, sem inferir deploy ou
ergonomia humana. Não verificado conserva a hipótese sem transformá-la em fato.

| Achado | Estado | Evidência atual / próxima lacuna |
| --- | --- | --- |
| UX-01 | Parcial (T07a local) | Carrinho acessível por controle persistente e detalhes financeiros expansíveis; Compose em 360/390/430 dp e fonte 100%/150% PASS. Categorias, ergonomia completa, jornada Android/API e aparelho não verificados. |
| UX-02 | Parcial (evidência local) | T06b: API/Web busca apelido normalizado antes da paginação; código/mesa e Android ainda abertos. |
| UX-03 | Resolvido no fluxo local individual | `production-board.tsx` NEW/ACCEPTED → PREPARING → READY; navegador fixture executou duas ações explícitas em Bar e Cozinha, sem envio automático. Não comprova lote/pico/deploy. |
| UX-04 | Resolvido (teste local T10c) | Configuração confirmada, legado independente e lote explícito/revisado com replay, conflitos e resultado por linha;425 visuais +1 volume e6 Web/API PostgreSQL360/390/430. Publicação/piloto não verificados. |
| UX-05 | Resolvido com evidência local (T10a mobile) | Atalhos persistentes e foco alcançam passe/disponibilidade em uma ação com 30 linhas, Cozinha/Bar 360/390/430; Web/API PostgreSQL. Tempo humano, aparelho e versão publicada não medidos. |
| UX-06 | Resolvido com evidência local no workspace montado | T04: A→B→A, nova Tab, configurações, descarte e confirmação isolados; 3 jornadas Web/API/PostgreSQL em360/390/430. Reload e persistência durável permanecem T05. |
| UX-07 | Resolvido com evidência local no recorte de reload | T05a/T05b recuperam o mesmo pedido staff/guest na mesma aba/sessão/visita, sem adotar outra ocupação. Fechar aba, outra sessão/aparelho e drafts após reload não cobertos. |
| UX-08 | Resolvido no recorte CASH POS local | `pos-cash-receipt.tsx`: envelope na mesma aba/sessão, ref síncrona, replay/readback. Web/API/PostgreSQL demonstram resposta perdida após commit e um Payment/movimento. Fechar aba/reconciliação entre sessões permanecem fora; deploy não verificado. |
| UX-09 | Presente (inspeção) | `manage/page.tsx` e alert context mantêm links de módulo sem selecionar registro; T12. |
| UX-10 | Resolvido no recorte de confirmação local Android | T07b: diálogo identifica mesa/efeitos, cancelar não chama callback; confirmação bloqueada com mudança local de ocupação/permissão ou busy. Compose 360/390/430 dp × fonte 100%/150% PASS; disputa posterior ao snapshot e jornada Android/API não verificadas. |
| UX-11 | Resolvido no recorte local Android | T07c: Pedir navega para seleção de conta aberta, Nova comanda é explícita; IDs/homônimos, vazio e guards testados em 360/390/430 dp × fontes 100%/150%. Inventário completo Android, aparelho e jornada Android/API não homologados. |
| UX-12 | Parcial (evidência local) | T06c: Atendimento Web abre Tab da ocupação por ID e retorna com foco/filtro; nova Tab nesta mesa e Android permanecem abertos. |
| UX-13 | Parcial (T08a–T08d locais) | Android, Atendimento Web, guest e PDV Web oferecem revisão de rodada e inclusão guardada no draft. Jornadas Web/API PostgreSQL comprovam repetição e replay sem duplicação em 360/390/430; variantes/adicionais têm cobertura compartilhada. Jornada Android/API integral, versão publicada, aparelho e ganho humano permanecem não verificados. |
| UX-14 | Resolvido com evidência local (T09a) | Guest tem +/−, remoção em zero, agrupamento por IDs/configuração e limite 99 sem perda de unidades. Fixtures e Web/API PostgreSQL 360/390/430 comprovam quantidade, bloqueios e replay; publicação/aparelho/tempo humano não verificados. |
| UX-15 | Resolvido com evidência local (T09b) | Busca global por nome, categorias, retorno/vazio e acesso estável ao draft; fixture de 146 produtos (143 CSV + três fixtures existentes), mobile e Web/API PostgreSQL comprovados. Catálogo publicado, aparelho e ganho humano não verificados. |
| UX-16 | Parcial (T07a local) | BalanceCard usa detalhes expansíveis e mantém saldo/avisos/guards; controles financeiros ainda antecedem catálogo. Conferência de pagamento preservada, ergonomia completa não homologada. |
| UX-17 | Resolvido no recorte local T07d | Decimal/NumberPassword nos campos financeiros; parser exato rejeita texto/sinais/overflow. Pagamento, limite, estorno e transferência testados em 360/390/430 dp × fontes 100%/150%; tipos reais do editor no emulador confirmados. IME físico e seleção automática do valor não homologados. |
| UX-18 | Presente (código Android) | MOVE_LOCATION continua em TabOperationsScreen junto de operações financeiras; T06/T07. |
| UX-19 | Resolvido com evidência local Web no recorte T06d | Movimento explícito origem → destino, gateway exclusivo e intenção recuperável. Jornada real PostgreSQL em 360/390/430 preserva financeiro/ocupação/histórico; 13 cenários novos e suíte visual completa 331 PASS. Android/versão publicada não verificados. |
| UX-20 | Parcial (inspeção e T02) | Enums/payment e filtro CLOSED persistem em refunds/page.tsx. T02 distingue revisão sem devolução de estorno positivo; histórico elegível permanece pendente. |
| UX-21 | Presente (inspeção) | PIN continua formulário separado em Estornos. A revisão nova preserva reauth; redesenho contextual é T12. |
| UX-22 | Resolvido com evidência local no recorte manual | T03b: envelope imutável, reload/replay/readback, PIN e sessão preservados; Web/API/PostgreSQL360/390/430. Provider e retomada entre sessões permanecem abertos. |
| UX-23 | Parcial (teste local) | T10d.1/T10d.2 permitem itens verificados independentes, inclusive fora de lote pendente. T10d.3 fornece API idempotente/versionada de disponibilidade; UI, novo lote e legado conservam barreiras. Próxima T10d.4 implementa recuperação Web por produto. |
| UX-24 | Parcial (inspeção) | TabListCreateView pagina 200; AttendanceWeb percorre ativas, OrderWorkspace agora navega pelas páginas (T06a local); refunds/manage ainda não consomem todas as páginas; T06. |
| UX-25 | Presente (inspeção) | manage/page.tsx Promise.all(openTabs.map(detail)); falha global ainda possível; T12. |
| UX-26 | Presente (código Android) | recoveryEvidence listado no Agora sem abrir contexto específico por entrada; T11. |
| UX-27 | Não verificado quanto à obrigatoriedade | Botões de entrega existem; não demonstram que taps são obrigatórios nem ausência de inferência. T11 precisa investigar alternativa. |
| UX-28 | Presente (código Android) | serviceRequests antecede deliveryTasks mesmo em peak; T11. |
| UX-29 | Presente (inspeção) | daily-close/page.tsx compartilha decisionReason entre propostas; T12. |
| UX-30 | Presente (inspeção) | blockers exibem ID abreviado sem ação contextual; fingerprint no corpo operacional; T12. |
| UX-31 | Parcial (inspeção) | staff-auth-screen.tsx exige venueSlug; campo PIN e linguagem precisam revisão. Tenant não publicado/verificado nesta execução; T13. |
| UX-32 | Presente (inspeção) | cash/page.tsx “Voltar ao atendimento” aponta /pos; T13. |
| UX-33 | Presente (inspeção) | reports/page.tsx De/Até sem presets de dia operacional; T13. |
| UX-34 | Presente na base; recorte T02 corrigido localmente | Corrections calcula max(0,item_net-exposure), mas marcava REFUND_REQUIRED também com zero. Novo comando gerencial resolve cancelamento integral NEW/ACCEPTED sem Refund. Validação abaixo. |
| UX-35 | Resolvido com evidência local | T04: reseleção mantém aria-expanded true e foco no título; recolher somente no cabeçalho. Atendimento/POS em360/390/430. Versão publicada não verificada. |

## Causa e contrato da menor slice

Não há alocação Payment → item. O cálculo canônico estava correto: 3800 de
consumo, 1000 recebido e cancelamento de 800 deixam 2000 de exposição aberta.
A classificação e a ausência de comando gerencial sem refund criavam o impasse.
Não havia demonstração de prejuízo ou recebimento duplicado.

Novo pedido usa MANUAL_REVIEW_REQUIRED quando refund_required_cents é zero.
`settle-without-refund` exige capacidade, gerente ativo e reauth recente;
revalida estágio, quantidade e saldo sob lock da Tab. Adiciona reversão e auditoria
na mesma transação. Se o saldo mudou e exigiria devolução, tudo é revertido.
Replay por ID da correção conserva um único efeito. Pendência histórica zero
REFUND_REQUIRED usa o mesmo comando; nenhum registro antigo é reescrito em lote.
O campo legado `refund_required_corrections` permanece por compatibilidade de
leitura e inclui as revisões. Web apresenta ação sem estorno, mesmo sem pagamento
elegível, e conserva o ID/corpo vazio depois de resposta ambígua.

Proprietária: Spec 017, seção UX-34. Cancelamento parcial de quantidade paga,
produção avançada, atualização de estorno positivo após saldo mudar e deep links
do modal de Atendimento ficam fora deste recorte. Não declarar T02 inteira PASS.

## Validação desta execução

- PostgreSQL dedicado em 127.0.0.1:55476, bancos rodada_payments_test (Django
  cria/destroi seu banco test_) e rodada_web_e2e; nenhum banco da demo utilizado.
- `manage.py test tests.test_corrections tests.test_partial_cancellation_concurrency
  tests.test_pricing --settings=rodada_api.settings_payments_postgres --noinput`:
  57 testes PASS; inclui aprovação/replay concorrente, saldo alterado com rollback,
  desconto/serviço, estorno positivo existente, permissão, reauth, isolamento,
  legado zero, imutabilidade de Payment/Charge e ausência de Refund/CashMovement.
- Build Web com TypeScript: PASS no build final. Check Django e
  makemigrations --check --dry-run: PASS, sem migration nova necessária.
- Suíte `test:visual` executada via CLI do Playwright: 238 PASS (235 casos
  permanentes + 3 observações temporárias T01), sem alterar baseline/tolerância;
  execução final de 4,8 minutos. Screenshots review-360/390/430.png inspecionados
  por assertions de layout/a11y; captura 390 inspecionada visualmente.
- Integração `correction-without-refund.spec.ts`: 1 PASS com API real/PostgreSQL;
  aprova zero, verifica Payment intacto e replay, executa preparo → pronto do
  item restante. Fixture aprovou limite 5000 explicitamente antes do consumo.
  Tentativas iniciais corrigiram esperas de login/mutations, limite de fixture e
  seletor de alerta que incluía o anunciador de rotas; nenhuma proteção relaxada.
- Lint Ruff nos cinco arquivos Python de lógica/testes: 16 avisos preexistentes,
  os mesmos 16 na versão final, zero novos. Comparação feita contra HEAD com a
  mesma configuração, diagnóstico e linha de origem. Não alegar lint global limpo.
  Ferramenta obtida em pasta temporária; nenhum manifest/dependência alterado.
- Após ajuste de lint nas permissões, teste de autorização do novo endpoint:
  1 PASS adicional. Não houve mudança da lógica financeira após os 57 testes.
- `npm run test` não existe em package.json: foi executado o gate existente
  `test:visual`, exigido pelo AGENTS.md, além da integração e build.
- Observação T01 com fixtures: UX-06 enviável true → false ao voltar; UX-35
  aria-expanded=false; UX-03 PREPARING → READY em Bar e Cozinha.
- Logs locais em visual-artifacts/spec026/runtime: financial-tests.log,
  visual-tests-final.log, integration-tests.log e lint-comparison.json.
  Observações temporárias T01 arquivadas em t01-observation.spec.ts fora da
  suíte permanente: não transformar a perda de draft atual em contrato de teste.
- Tempos humanos, gestos de scroll, Android/aparelho, pico, piloto e deploy:
  não verificados. Nenhuma redução de tempo/taps humanos é alegada.

Próxima tarefa: T03, começar pelo recebimento POS UX-08; congelar intenção,
impedir envio concorrente e ensaiar resposta perdida após commit em PostgreSQL.
T04 é a próxima frente de contexto após segurança financeira.

## Arquivos alterados

- API: modules/corrections/services.py e views.py; modules/ordering/views.py;
  rodada_api/urls.py. Classificação, leitura da revisão e comando autorizado.
- Testes API: tests/test_corrections.py e test_partial_cancellation_concurrency.py.
- Web: app/refunds/page.tsx, app/manage/page.tsx,
  components/correction-without-refund.tsx e confirmed-item-removal.tsx.
- Testes Web: tests/visual/correction-without-refund.spec.ts e
  tests/integration/correction-without-refund.spec.ts.
- Contratos: Spec 017 spec/plan/acceptance; Spec 026 spec/plan/tasks/acceptance
  e este relatório. README aponta o estado local atualizado.

Revisão final: diff sem erros de whitespace e sem inclusão de contexto pessoal.
Worktrees e dados preexistentes preservados. Banco de teste desligado após checks.

## T03a — recebimento CASH recuperável (UX-08)

### Problema, causa e recorte

Na base ad5d64f, `OrderWorkspace.collect` gerava UUID por chamada, sem guarda
síncrona/busy ou payload retido. expected_version já protegia contra versões
obsoletas; isso não identificava um retry após atualização do saldo. Não foi
reproduzido prejuízo na base antiga nem atribuída perda à versão publicada.
No replay CASH, a API comparava apenas amount/method e ignorava caixa/tender.

`PosCashReceipt` preserva envelope mínimo v1 antes do fetch (sem credenciais ou
nome do cliente); congela Tab/valor/caixa/chave/expected_version. Double tap usa
ref síncrona. API e leitura autorizada confirmam id/método/valor/status do Payment
antes de liberar. Rede/5xx/JSON inválido/readback falho conservam a operação;
Verificar mesmo recebimento usa o mesmo POST e chave. Nova operação não é
permitida por simples saldo atualizado. Rejeição inicial conhecida400/409 permite
edição, inclusive recálculo de taxa de serviço; conflito/desconhecido/ambiguidade/
autorização mantêm revisão bloqueada.

O payload contém originating_session_id opcional, conferido pela API contra o
actor autenticado para fechar a corrida entre auth/me e mutation. Web checa
Venue/staff/session; troca/revogação não adota a intenção. Armazenamento ilegível/vazio
ou sem escrita bloqueia primeiro envio. Um recebimento de outra sessão permanece
preservado, exige revisão e não tem comando de descarte/reconciliação nesta slice.
A exclusão após readback confere o envelope, para não apagar outra operação.

Replay do ledger CASH valida CashMovement.shift.cash_point e CashTenderDetail
original; null/omitido de tender equivale ao amount. Replay após fechamento da
Tab/turno retorna fato original; não usa um turno novo nem muda snapshots.
Legado sem evidência física permanece review-only. Nenhuma migration.

### Arquivos desta continuação

- API: `modules/ledger/services.py`, `modules/ledger/views.py`;
  `tests/test_ledger_payments.py`, `tests/test_payments_concurrency.py`.
- Web: `components/pos-cash-receipt.tsx`, `components/order-workspace.tsx`,
  `app/globals.css`; `tests/visual/pos-cash-receipt.spec.ts` e
  `tests/integration/pos-cash-receipt.spec.ts`.
- Contrato/plano/aceite: Specs 006, 012, 014 e 026; tasks/revalidation da026 e README.
  Alterações de T02 e worktrees existentes preservadas.

### Evidência atual

- PostgreSQL descartável em `127.0.0.1:55476`, cluster de teste da Spec026. Suite Django
  `tests.test_ledger_payments tests.test_payments_concurrency tests.test_cash_management`
  com `--settings=rodada_api.settings_payments_postgres --noinput`: **30 PASS**.
  Conferência, centavos/troco, efeito único, actor/audit, rollback, divergência de
  caixa/tender, sessão alterada/revogada, legado e replay após fechamento cobertos.
  Após ordenar importação local, teste novo de concorrência repetido: **1 PASS**.
- Jornada real Web/API/PostgreSQL: **2 PASS**, recebimento e regressão T02.
  Consumo de 2000 centavos, recebimento de 1000; o teste aguarda HTTP 201 real e interrompe a resposta
  depois do commit. Leitura independente comprova Payment e saldo de 1000 centavos antes do
  reload. Retry mantém payload/id; depois há um Payment, um movimento de +1000 centavos e
  saldo de 1000 centavos. A simulação usa URL canônica para incluir o commit, sem interromper
  apenas o redirect Next. Não usa provider ou dinheiro real.
- Suíte visual completa final: **245 PASS**, incluindo **10 cenários novos**
  na compilação final, sem alterar tolerâncias/referências: duplo toque,
  perda de resposta/reload, rejeições iniciais de versão/taxa, readback 503,
  troca/revogação, storage indisponível/corrompido/vazio e 5xx/conflito. Fixture distingue isolamento de
  comportamento financeiro real. Layout/Axe/alvos de 44px em360/390/430 no formulário
  e na pendência; imagens em `visual-artifacts/spec026/cash-form-*.png` e
  `cash-pending-*.png`. Inspeção visual direta em390px, sem aparelho físico.
- Build Next/TypeScript final **PASS**; Django check **PASS**;
  makemigrations check/dry-run conectado ao PostgreSQL: nenhuma mudança.
- Ruff nos quatro arquivos Python desta slice: 7 diagnósticos atuais, 7 na HEAD,
  **zero introduzidos**, comparados por código/mensagem/linha de origem na mesma
  configuração. Lint global não é declarado limpo; Web não possui script lint.
- Web não possui `npm run test`; equivalente documentado é `test:visual`.
  Com npm fora do PATH, execução usa `node node_modules/@playwright/test/cli.js test`
  (e `--config playwright.integration.config.ts` para integração). Configs existentes
  iniciam serviços locais; env RODADA_REFERENCE_PYTHON/RODADA_TEST_PYTHON aponta
  o Python do projeto. Integração usa somente DB `rodada_web_e2e`, recriado entre
  ensaios; RODADA_E2E_POSTGRES=1, POSTGRES_HOST=127.0.0.1, POSTGRES_PORT=55476.
- Logs em `visual-artifacts/spec026/runtime/t03-financial-tests.log`,
  `t03-final-concurrency.log`, `t03-build.log`, `t03-integration-tests.log`,
  `t03-visual-focused.log`, `t03-visual-final.log`, `t03-lint-comparison.json`.

### Limites e próxima tarefa

Retomada cobre a mesma aba/sessão com sessionStorage íntegro. Fechar a aba,
apagar armazenamento, transferir revisão entre sessões e outras abas/dispositivos
não são homologados. Aviso/bloqueio é proteção, não resolução gerencial completa.
Estado ao fim de T03a: UX-22/estorno permanecia presente; resolução manual documentada na seção T03b abaixo. Nenhum fluxo de provider/Android foi alterado.
Próxima tarefa registrada ao fim de T03a: **T03b/UX-22**, congelar intenção de estorno positivo e
recuperar o mesmo Refund preservando PIN, autorização e Payment original.
Piloto, medição humana, aparelho e deploy não verificados. Sem commit/push/merge/deploy. PostgreSQL descartável encerrado após os testes.

## T03b — estorno manual positivo recuperável (UX-22)

### Problema e causa raiz

A tela guardava apenas uma chave em memória, reconstruía o corpo a partir dos
campos editáveis e liberava a chave antes de conferir o histórico. Reload perdia
a intenção. Na API, replay de Refund CASH não conferia o caixa original;
correção APPLIED conferia Payment/chave sem conferir o valor. O bloqueio de
comanda fechada antecedia replay mesmo quando o efeito já existia.

### Implementação e limites do contrato

- `apps/web/lib/client/manual-refund-intent.ts`: envelope mínimo
  `rodada.intent.refund.v1`, persistido antes do POST, guard síncrono, corpo/rota
  derivados do envelope, não dos campos atuais; recuperação explícita na mesma
  aba/sessão. Nunca persiste PIN/token/nome de cliente.
- `apps/web/app/refunds/page.tsx`: congelar seleção/valor/motivo/caixa, manter PIN
  disponível e mostrar Verificar mesmo estorno inclusive após reload sem seleção.
  Confirmar exige resposta canônica + Refund correspondente no Payment original
  via Tab readback. Correção exige APPLIED e pendência removida. A revisão sem
  devolução T02 mantém sua ação de retomada habilitada.
- `apps/api/modules/ledger/{services,views}.py`: originating_session_id opcional,
  conferência do movimento/caixa original no replay CASH e replay antes da
  precondição de comanda fechada. Nenhum movimento/snapshot é refeito.
- `apps/api/modules/corrections/{services,views}.py`: serializer de centavos/UUIDs,
  validação de sessão e delegação do replay APPLIED à conferência do Refund
  original; payload divergente retorna conflito sem outra reversão.
- Specs006/012/014/017 e026: contrato/plano/aceite atualizados antes do código;
  tasks/revalidation e README atualizados com o estado final comprovado.

Timeout, 5xx, conflito, REAUTH_REQUIRED, readback falho ou sessão divergente
preservam a intenção. PIN recente continua obrigatório no servidor. Rejeição
inicial segura e comprovadamente sem efeito libera edição; após incerteza a
mesma rejeição nunca abandona o comando. Sem storage íntegro bloquear nova
operação; sem sessão original pedir revisão, sem adotar ou oferecer descarte.

Escopo entregue: estornos manuais e settle-refund, com CASH na jornada integrada.
Provider não recebe confirmação manual; seu contrato permanece separado.
Fechar aba, remover storage e resolução em outra sessão/aparelho continuam
abertos. Não há homologação de Android, aparelho físico, provider, piloto ou deploy.

### Testes e evidência local

- `apps/api/tests/test_ledger_payments.py`: fingerprint de valor/motivo/caixa,
  excesso de refundable, original Payment preservado exceto status derivado,
  readback financeiro, replay com Tab/turno fechados, PIN vencido, sessão
  divergente/revogada e histórico legado sem movimento (não reconstruído).
- `apps/api/tests/test_corrections.py`: valor divergente no replay APPLIED,
  sessão original/diferente e entradas inválidas sem truncamento de centavos.
- `apps/api/tests/test_payments_concurrency.py`: mesma intenção e intenções
  distintas concorrentes, um único Refund/débito/audit; limite reembolsável.
- `apps/api/tests/test_partial_cancellation_concurrency.py`: correção paga
  concorrente produz um Refund, reversão e aprovação; Payment preservado.
- `apps/web/tests/visual/manual-refund-intent.spec.ts`: 13 casos novos de duplo
  toque, perda de resposta/reload, readback503, reauth/conflito, rejeição inicial,
  sessão divergente/revogada e storage indisponível/corrompido/vazio.
- `apps/web/tests/integration/manual-refund-intent.spec.ts`: seis jornadas reais
  Web/API/PostgreSQL (avulso e correção ×360/390/430), route.fetch aguarda201 após
  commit e só então interrompe a resposta. Recarregar não envia; ação explícita
  repete corpo idêntico, recebe200 com mesmo Refund, sem novo débito/reversão.
  Consumo1500, Payment1000, Refund500: exposição1000 no avulso e0 na correção;
  reversão da correção-1000; caixa varia+500 (recebimento1000 menos devolução500).
  Os métodos são registros de teste; não há devolução real de dinheiro.

Comandos equivalentes aos scripts documentados (npm não está no PATH):

```powershell
# apps/api; PostgreSQL descartável 127.0.0.1:55476
$env:PAYMENTS_TEST_DB_PORT='55476'
../../.venv/Scripts/python.exe manage.py test tests.test_ledger_payments tests.test_payments_concurrency tests.test_cash_management tests.test_corrections tests.test_partial_cancellation_concurrency --settings=rodada_api.settings_payments_postgres --noinput
../../.venv/Scripts/python.exe manage.py check --settings=rodada_api.settings_payments_postgres
../../.venv/Scripts/python.exe manage.py makemigrations --check --dry-run --settings=rodada_api.settings_payments_postgres
# apps/web; variáveis locais de runtime/DB conforme README/config de integração
node node_modules/next/dist/bin/next build
node node_modules/typescript/bin/tsc --noEmit
node node_modules/@playwright/test/cli.js test
node node_modules/@playwright/test/cli.js test --config playwright.integration.config.ts manual-refund-intent.spec.ts correction-without-refund.spec.ts pos-cash-receipt.spec.ts
```

Não existe script `npm run test` ou lint Web neste package.json. Executado o
script equivalente `test:visual` completo. Config/baselines/tolerâncias preservados.
Screenshots em `visual-artifacts/spec026/refund-*`; formulário e pendência390
inspecionados visualmente. Layout/Axe/alvos44px/overflow360/390/430 são evidência
automatizada, não ergonomia observada em aparelho ou medição humana de tempo.

Uma primeira rodada visual detectou a ação T02 bloqueada pelo fieldset; corrigido
mantendo bloqueios dos campos financeiros e retomada da revisão. Outra falha foi
seletor de teste capturando também o anunciador Next; restringido ao main, sem
alterar asserção/tolerância. Apenas resultados finais completos contam como PASS.

Resultados finais:

- **72 PASS** na suíte financeira PostgreSQL completa acima; **12 PASS** na
  rodada focada anterior de concorrência/correção (incluídos na suíte final).
- **8 PASS** Web/API/PostgreSQL: seis estornos360/390/430 mais regressõesT02/T03a.
- **258 PASS** na suíte visual completa final (13 novos casos); sem baseline novo
  ou tolerância relaxada. As três regressões Web de revisão zero passam.
- Build Next **PASS**, `tsc --noEmit` **PASS**, Django check **PASS**,
  makemigrations check/dry-run: nenhuma mudança. Nenhuma migration necessária.
- Ruff: **15 achados atuais,16 em HEAD,zero introduzidos**, mesmos arquivos,
  configuração/código/mensagem/linha de origem; lint global permanece com dívida.
- `git diff --check` e whitespace das novas fontes **PASS**. Diff revisado com
  isolamento de contexto pessoal; arquivos/alterações anteriores e worktrees
  preservados. Branch `main`/HEAD `ad5d64f` mantidos, sem commit/push/merge/deploy.
- Logs finais ignorados em `visual-artifacts/spec026/runtime/`:
  `t03b-financial-final.log`, `t03b-concurrency-final.log`, `t03b-integration-final.log`,
  `t03b-visual-final.log`, `t03b-build.log`, `t03b-lint-comparison.json`.

Próxima tarefa exata: **T04/UX-06 eUX-35** — preservar draft por Tab e tornar
reseleção previsível. Gates de campo/Android/provider/deploy permanecem abertos.

PostgreSQL descartável encerrado após todos os checks desta continuação.

## T04 — rascunhos por Tab e reseleção previsível (UX-06/35)

### Causa e recorte

`OrderWorkspace` possuía um carrinho único. Seleção de outra Tab e abertura de
nova Tab chamavam setCart([]), perdendo o trabalho anterior. O resultado da lista
para a Tab atual alternava tabCollapsed, ocultando o pedido no gesto de seleção.
A Spec025 antiga contratava esse reset/collapse; foi atualizada antes do código.

Novo contrato proprietários001/025/026: mapa de linhas por Tab.id em memória,
setter ligado ao destino original, nova Tab vazia e confirmação/descarte somente
do destino ativo. Reseleção revela o conteúdo e foca o título; apenas o cabeçalho
recolhe. Descarte usa ActionDialog com confirmação nomeando a comanda e retorno
sem efeito. Rascunho não vazio bloqueia fechamento com orientação explícita.
Ref síncrona e fieldset impedem envio/edição/switch enquanto a leitura/abertura
está em andamento, com status visível; falha na leitura mantém seleção e rascunho anteriores.
Pedido enviado/ambíguo continua congelado; não é draft livre para descarte.
Catálogo atual ainda recalcula preço e revalida variant/modifiers/disponibilidade.

Limite: workspace montado. No Atendimento, seções ocultam o workspace sem
remontá-lo; a sessão autenticada possui key de sessão no componente pai.
Não foi adicionado storage, persistência em outra aba ou recuperação após reload.
T05 deve contratar a recuperação durável de pedidos enviados; este recorte não
transforma uma intenção ambígua em edição local nem declara UX-07 resolvido.

### Arquivos alterados nesta slice

- `apps/web/components/order-workspace.tsx`: mapa, seleção serializada, reseleção,
  foco, descarte confirmado e proteção do fechamento com draft não vazio.
- `apps/web/tests/visual/attendance-draft.spec.ts`: expectativa de reseleção
  atualizada ao novo contrato; recolher explícito continua coberto.
- `apps/web/tests/visual/tab-drafts.spec.ts`:11 novos cenários de isolamento,
  Tab nova, descarte/cancelamento/foco, configurações distintas/quantidades,
  confirmação por destino, disponibilidade alterada, falha na leitura e pendência.
- `apps/web/tests/integration/tab-drafts.spec.ts`:3 jornadas Web/API/PostgreSQL
  reais, uma por largura360/390/430, pedidos/ledger isolados por Tab.
- Specs001/025/026: spec/plan/acceptance, tasks/revalidation e README com estado
  comprovado. Nenhum endpoint, migration ou regra financeira alterado nesta slice.

### Validação

Primeira rodada detectou contraste4,32 no botão danger; reutilizado
buttonDangerReadable existente (texto legível, borda/tint danger preservados),
sem CSS ad hoc nem relaxar Axe. Fixtures POS das novas Tabs precisavam incluir
pricing; adicionadas apenas à fixture isolada. Na jornada integrada, a seleção
Todos podia recolher o catálogo já aberto; o teste usa a busca real por produto.
Não são chamados testes financeiros os mocks da suíte visual.

**14 PASS** na rodada focada:11 novos +3 regressões de quantidade/recolher,
com layout/Axe/alvos44px em360/390/430, Atendimento ePOS. Capturas em
`visual-artifacts/spec026/t04-draft-*` e`t04-discard-*`. Inspeção visual direta
390px; não há aparelho físico, medição humana nem ergonomia homologada.

**36 PASS** PostgreSQL para `tests.test_ordering_foundation tests.test_ledger_payments`
com `--settings=rodada_api.settings_payments_postgres --noinput`, porta55476.
Build Next e `tsc --noEmit` PASS. Sem script lint ou `npm run test` no package Web;
executar o script existente test:visual via CLI equivalente. API sem mudança
nesta slice; nenhuma alegação de lint global limpo. Config/baselines/tolerâncias
inalterados. Resultados finais de integração e suíte visual completa registrados
na consolidação abaixo, após conclusão.

Comandos usados (apps/web, com runtimes/DB descartável documentados):

```powershell
node node_modules/next/dist/bin/next build
node node_modules/typescript/bin/tsc --noEmit
node node_modules/@playwright/test/cli.js test tests/visual/tab-drafts.spec.ts tests/visual/attendance-draft.spec.ts
node node_modules/@playwright/test/cli.js test
node node_modules/@playwright/test/cli.js test --config playwright.integration.config.ts tab-drafts.spec.ts pos-cash-receipt.spec.ts correction-without-refund.spec.ts
```

Logs ignorados em `visual-artifacts/spec026/runtime/`:t04-build.log,
t04-focused-final.log,t04-api-tests.log,t04-integration-final.log,t04-visual-final.log.
Permanece main/ad5d64f com alterações anteriores/worktrees preservados.
Sem commit/push/merge/deploy, demo compartilhada ou produção.

### Consolidação final T04

- **5 PASS Web/API/PostgreSQL**: três jornadas T04 em360/390/430 mais
  regressões T02 sem devolução e T03a resposta perdida de recebimento CASH.
  A confirma2000 centavos, B permanece sem Order/Charge até confirmar seu próprio
  pedido de500; C permanece vazia. Nenhum Payment criado pelas jornadas T04.
- **269 PASS** na suíte visual completa final (5,9min), incluindo os11 novos
  cenários T04. Baselines e tolerâncias preservados.
- **36 PASS** API PostgreSQL; build Next e TypeScript final PASS;
  diff sem erro de whitespace. Web não oferece script lint nem npm run test;
  foi executado test:visual pelo CLI equivalente documentado acima.
- Capturas390px Atendimento/rascunho e POS/descarte inspecionadas diretamente.
  Não equivale a aparelho real ou medição humana. Sem deploy/piloto homologado.

Próxima tarefa exata: **T05/UX-07**, contratar e implementar a menor recuperação
  durável do mesmo pedido staff Web após resposta perdida/reload, mantendo
  payload/chave/Venue/sessão/Tab e consulta canônica antes de liberar novo envio.
  Guest continua separado até validar sessão/ocupação/revogação próprias.

## T05a — recuperação do mesmo pedido staff Web (UX-07)

### Problema e causa

A API já serializa confirmações pela Tab e compara o fingerprint de chave/source/
linhas. O Web guardava apenas refs em memória: reload perdia chave/payload e
permitia uma nova confirmação apesar de commit anterior possível. Além disso,
a UI antiga liberava sucesso antes de provar o Order no detalhe canônico.

### Mudança

Contracts001/014/026 atualizados antes do código. Hook `order-intent.ts` preserva
sessionStorage antes do primeiro POST, sem credenciais: schema, Venue, ator,
sessão, Tab, gateway original, instante e payload/chave. Uma intenção por aba.
Retomada explícita valida auth/me e scope original, envia payload/chave exatos,
valida Order/tab_id retornados e exige o mesmo Order na leitura da comanda antes
de limpar storage e liberar a UI. Não libera por saldo ou catálogo atual.
Gateway original preserva STAFF/CASHIER inclusive Atendimento→PDV.

OrderWorkspace mantém draftsT04 separados, bloqueia edição/descarte/troca/
fechamento durante ambiguidade e mostra recuperação após reload sem depender da
Tab na primeira página da lista. AttendanceWeb revela Contas quando existe
recuperação ou falha de storage, evitando uma ação escondida pela navegação.
Readback/clear-storage falhos não limpam draft nem anunciam sucesso.
Rejeição inicial conhecida permite revisão; rejeição durante recuperação não
prova ausência de commit. Sessão distinta/revogada não adota a intenção.

### Arquivos desta slice

- `apps/web/lib/client/order-intent.ts`: envelope validado, storage, auth e replay.
- `apps/web/components/order-workspace.tsx`: integração e readback canônico.
- `apps/web/components/attendance-web.tsx`: revelar recuperação em Contas.
- `apps/web/tests/visual/order-intent.spec.ts`:13 casos novos, incluindo seis
  jornadas Attendance/POS360/390/430, readback, duplo toque, sessão/revogação,
  storage, rejeição e gateway original; mocks não são evidência financeira.
- `apps/web/tests/visual/attendance.spec.ts` e `tab-drafts.spec.ts`: fixtures de
  Order canônico/readback e espera assíncrona após auth; sem tolerância relaxada.
- `apps/web/tests/integration/order-intent.spec.ts`:3 commits reais com resposta
  perdida/reload; em390px também retoma Atendimento→PDV pelo gateway original.
- `apps/api/tests/test_order_intent_concurrency.py`: dois casos PostgreSQL
  concorrentes; mesmo conteúdo e conflito de conteúdo, Order/Charge/audit únicos.
- Specs001/014/026 spec/plan/acceptance e026tasks/revalidation/README: estado local.

Nenhum endpoint, migration, domínio financeiro, Payment ou snapshot alterado.

### Validação e correções encontradas

Rodada focada33 PASS antes do caso adicional de gateway. Teste antigo lia número
de requests imediatamente após click; auth/me tornou esse envio assíncrono.
Agora aguarda o request e comprova Pedido confirmado com readback da fixture.
Primeiro teste direto de concorrência usava string em vez de UUID tipado do
contrato de serviço; corrigido o teste, sem mudar a produção.

36 testes de ordering/ledger PostgreSQL PASS;2 novos testes concorrentes PASS,
com um Order, Charge, evento order.confirmed e nenhum Payment criado. Payload
concorrente divergente resulta IDEMPOTENCY_CONFLICT sem substituir o original.
Ruff do novo arquivo PASS (imports organizados); tipos e build final PASS.
Web não possui script lint ou npm run test: executado test:visual pelo CLI
correspondente. Nenhuma afirmação de lint global limpo.

Uma rodada integrada teve dois timeouts de login enquanto o build era
reconstruído. Ela foi descartada como evidência; rodada final usa build congelado
com DB E2E recriada. Suítes interrompidas não contam como PASS completo.
Captura390px da recuperação Atendimento inspecionada diretamente; demais
larguras possuem layout/Axe/alvos44px automatizados, sem aparelho físico.
Consolidação de integração e visual completo segue abaixo após terminarem.

Comandos usados (runtimes e PostgreSQL descartável conforme seções anteriores):

```powershell
# apps/web
node node_modules/next/dist/bin/next build
node node_modules/typescript/bin/tsc --noEmit
node node_modules/@playwright/test/cli.js test
node node_modules/@playwright/test/cli.js test --config playwright.integration.config.ts order-intent.spec.ts tab-drafts.spec.ts pos-cash-receipt.spec.ts correction-without-refund.spec.ts
# apps/api, PAYMENTS_TEST_DB_PORT=55476
../../.venv/Scripts/python.exe manage.py test tests.test_ordering_foundation tests.test_ledger_payments --settings=rodada_api.settings_payments_postgres --noinput
../../.venv/Scripts/python.exe manage.py test tests.test_order_intent_concurrency --settings=rodada_api.settings_payments_postgres --noinput
# raiz, ferramenta isolada; config do repositório
uv tool run --from 'ruff>=0.12,<1' ruff check --config apps/api/pyproject.toml apps/api/tests/test_order_intent_concurrency.py
```

Logs ignorados runtime/t05-{build,api,concurrency-final,focused-final,integration-final,visual-final}.log.
Limites: mesma aba/sessão com storage íntegro. Não cobre guest, fila offline,
fechar aba, outra sessão/aparelho, drafts não enviados após reload nem resolução
entre sessões. UX-07 permanece parcial; sem deploy/piloto/observação humana.
Próxima slice exata: **T05b/UX-07 guest**, investigar envelope e recuperação com
sessão/Tab/occupancy/epoch/revogação antes de implementar, sob Specs004/014/026.

### Readback financeiro independente T05a

Após a rodada integrada estável, consulta direta no PostgreSQL descartável
comprovou nas três Tabs Order recovery360/390/430: Order=1, Charge=1,
AuditEvent order.confirmed=1, Payment=0 e exposure=2000 centavos.
A retomada390 também passou por /pos mantendo confirmação pelo gateway staff
original. As oito jornadas integradas finais passaram em1,4min.

### Consolidação final T05a

**282 PASS** na suíte visual completa final (6,1min), sem baseline/tolerância
alterados; **8 PASS** Web/API/PostgreSQL (1,4min); **38 PASS** API PostgreSQL
(36 ordering/ledger +2 concorrência). Build Next, TypeScript final, Ruff do novo
teste e diff/whitespace PASS. Capturas390px Atendimento e POS inspecionadas.
Branch main/ad5d64f e worktrees/alterações anteriores preservados; sem commit,
push, merge, deploy, demo compartilhada ou produção. PostgreSQL descartável
encerrado ao concluir os checks. T05a local aceita; T05/UX-07 segue parcial pelos
limites guest/storage/aba/sessão já registrados. Próxima tarefa: T05b guest.

## T05b — retomada guest na mesma visita

Causa: guest guardava só a chave em ref, recalculava lines a cada tentativa e
perdia chave/carrinho no reload. A API já tinha replay e validação de sessão/
ocupação/generation; não foi reimplementada regra financeira.

Specs004/014/026 contratadas antes do código. Contexto autorizado ganhou
session_scope não secreto (Venue, GuestSession, Table, occupancy, generation).
IDs não autorizam acesso. Hook salva payload/chave e scope antes do POST,
sem copiar a credencial guest. Revalida contexto integral antes de replay e
exige Order/tab_id mais presença do mesmo Order no readback antes de limpar.
Pedidos ambíguos bloqueiam outro envio, edição e nova Tab; retomada explícita
permanece visível após reload. Com pendência, resolve consulta context em vez
de QR resolve, que poderia emitir sessão substituta. Revogação ou contexto
alterado conserva o envelope e encaminha à equipe; não transfere a intenção.

Arquivos da slice:
- apps/api/modules/guest_access/views.py: scope no contexto, sem novo endpoint.
- apps/api/tests/test_guest_access.py: scope sem token, replay/ledger/audit e geração revogada.
- apps/web/lib/client/guest-api.ts: transporte existente extraído sem mudança de autorização.
- apps/web/lib/client/guest-order-intent.ts: envelope, scope, storage, replay/readback.
- apps/web/components/guest-ordering.tsx: recuperação visível e bloqueios; sem sessão substituta.
- apps/web/tests/visual/guest-order-intent.spec.ts:14 cenários (mobile, readback/duplo toque,
  seis divergências de contexto, revogação, bloqueio, storage e rejeição).
- apps/web/tests/integration/guest-order-intent.spec.ts:3 retomadas reais e1 após liberar mesa.
- Specs004/014/026 spec/plan/acceptance,026tasks/revalidation e README: estado verificado.

39 testes API em PostgreSQL PASS: guest access/global block, ledger e concorrência.
8 jornadas Web/API/PostgreSQL PASS (54,6s):4 guest novos,3 staff e chamada guest.
Consulta independente confirmou, para360/390/430/revoked, Order=1, Charge=1,
guest_order.confirmed Audit=1, Payment=0, exposure=1000 centavos por Tab.
Readback perdido mantém payload/chave; visita revogada não produz novo POST.
Ruff dos dois arquivos Python alterados, tipos e build PASS. Imports organizados.
Primeiro foco19 PASS/1 FAIL por unroute remover também o handler original da
fixture; corrigido teste para reinstalar o abort. Sem mudança de regra por fixture.
Visual completo final registrado abaixo após conclusão; tolerâncias/baselines intactos.

Comandos equivalentes aos scripts existentes, com DB/runtimes descartáveis já
registrados: build Next; tsc --noEmit; playwright test; playwright test
--config playwright.integration.config.ts guest-order-intent.spec.ts order-intent.spec.ts
service-requests.spec.ts; manage.py test tests.test_guest_access tests.test_global_guest_block
tests.test_ledger_payments tests.test_order_intent_concurrency
--settings=rodada_api.settings_payments_postgres --noinput (porta55476).
Ruff check --config apps/api/pyproject.toml nos dois arquivos Python desta slice.
Web não possui npm run test/lint: executado test:visual pelo CLI correspondente.
Logs ignorados runtime/t05b-{build,focused,api,integration,visual-final}.log.

Limites: mesma aba com storage íntegro e sessão/visita autorizadas. Sem fechar
aba, troca de sessão/aparelho, draft não enviado após reload, fila offline ou
reconciliação gerencial. Nenhum Payment/snapshot alterado; sem migration,
deploy, demo compartilhada, produção, aparelho ou medição humana.
Próxima tarefa do plano: T06/UX-02, menor busca/paginação de comandas staff
com mais de200 registros; movimentos de mesa ficam em recorte separado.

### Consolidação final T05b

**296 PASS** visual completo (6,2min), incluindo14 novos cenários guest;
**8 PASS** Web/API/PostgreSQL (54,6s); **39 PASS** API PostgreSQL.
Build Next, TypeScript, Ruff dos arquivos Python alterados e diff/whitespace PASS.
Captura390px da recuperação guest inspecionada; sem aparelho/medição humana.
PostgreSQL descartável encerrado. Main/ad5d64f e alterações/worktrees anteriores
preservados; sem commit/push/merge/deploy. Aceite marcado somente para o recorte
comprovado; próxima tarefa do plano T06/UX-02.


## T06a — Paginação staff Web (2026-10-12)

Base local: main ad5d64f, com slices anteriores não commitadas preservadas.
Causa: TabListCreateView já retornava next_offset, mas OrderWorkspace descartava
esse cursor e limitava a lista às primeiras 200 comandas. Implementado anterior/
próxima página no PDV, Atendimento e diálogo de histórico. Falha conserva página,
seleção e rascunhos; atualização obsoleta não pode sobrescrever a página nova.
O filtro existente explicita que atua nesta página. Histórico compartilha a página
consultada e continua somente leitura. Não há migração ou regra financeira nova.

Evidência real: `tests/integration/tab-pagination.spec.ts`, uma jornada com
201 Tabs em PostgreSQL dedicado rodada_web_e2e, exercitando 360/390/430.
GET via BFF confirma 200 + 1 registros e next_offset; rascunho permanece ao mudar
página. Readback final conserva zero Orders, Payments e exposição na Tab selecionada.
Teste financeiro/API: 37 PASS (ordering_foundation + ledger_payments) no PostgreSQL
local descartável. Teste novo cobre alcance de todas as Tabs, isolamento de Venue
e offset negativo. Build e tipos PASS. Logs locais ignorados em
visual-artifacts/spec026/runtime/t06-{build,api,integration,visual}.log.

Limites: paginação offset não congela inventário durante novas aberturas; filtro
por apelido é local à página, sem índice global, código ou mesa. Lista de 200
registros continua usando a projeção financeira existente; não se afirma melhoria
de número de consultas/latência. Android, versão publicada, refunds/manage e
observação de turno não foram validados neste recorte.
Próxima slice exata: T06b, busca global normalizada por apelido no backend e
Web, conservando paginação, homônimos, ausência de nome e rascunhos; código/mesa
exigem verificar seus contratos existentes antes de ampliar a busca.

Validação Web final: execução completa 303 testes: 300 PASS e 3 falhas dos
novos testes POS por ausência da fixture GET pricing. Corrigida somente essa
fixture; arquivo afetado reexecutado com 8 PASS (inclui resposta de refresh antiga).
Não houve mudança de implementação após a execução completa nem relaxamento de
baseline/tolerância. Não se declara uma segunda execução completa verde.
Ruff do teste Python PASS após organização dos imports existentes; tipos e
diff-check PASS. PostgreSQL encerrado. Sem commit, push, merge ou deploy.


## T06b — Busca global por apelido (2026-10-12)

Causa: filtro de apelido era aplicado somente aos 200 registros da página Web.
GET /tabs/?q agora filtra no Venue autenticado antes de paginar. search_label é
projeção textual derivada (Unicode/casefold/acentos/espaços), preenchida pela
migração 0007 e mantida em save de display_label. Apelido original e valores
financeiros permanecem intactos. Escritas em massa devem preencher a projeção.
PDV/Atendimento/histórico possuem busca explícita; aplicação reinicia offset zero,
sem trocar Tab ou limpar rascunho. Falha mantém consulta/resultados anteriores.
Opções homônimas/sem apelido no workspace mostram UUID real; sem auto-seleção.

Evidência: 39 testes PostgreSQL PASS (ordering_foundation + ledger_payments),
incluindo >200, paginação filtrada, acentos/caixa/espaços, substring literal com
%/_, homônimos, outros Venues, limite de q, backfill e atualização de apelido.
Jornada real Web/API em PostgreSQL dedicado rodada_web_e2e PASS: 203 Tabs, dois
homônimos anteriores à primeira página, busca via BFF e UI em 360/390/430;
seleção/rascunho preservados, readback final com zero Orders/Payments/exposição.
Build, tipos, migrations --check e diff-check PASS. Ruff PASS nos arquivos novos
(search/migração) e teste; modelos/views mantêm dez RUF012 preexistentes (baseline
HEAD tinha esses dez mais dois erros de imports). Regras não foram suprimidas.
Logs locais ignorados: visual-artifacts/spec026/runtime/t06b-*.log/json.

Limites: não há busca por código curto/mesa, Android, deploy ou medição humana.
Busca substring sem índice especializado; não se afirma ganho de latência ou
escala. Offset continua sujeito a aberturas concorrentes. Histórico compartilha
consulta/página do workspace. Sem alterações em ledger/Payments nesta slice.
Próxima slice exata: T06c, busca por mesa e abertura da Tab a partir da mesa,
com retorno ao contexto, conforme vínculos de ocupação existentes; não inventar
identificador curto sem contrato de domínio.

Suíte visual completa final: **310 PASS em 6,4 min**, incluindo seis cenários
de busca/erro/limpeza/rascunho em PDV e Atendimento 360/390/430, sem alteração de
baseline/tolerâncias. Teste de resposta anterior da T06a permanece PASS. Diff
revisado, alterações anteriores/worktrees preservadas. PostgreSQL encerrado;
sem commit/push/merge/deploy.


## T06c — Entrada pela mesa e retorno no Atendimento Web (2026-10-12)

Causa: occupancy.tabs aparecia como texto, exigindo reconhecer a mesma comanda
na lista de Contas; a projeção da ocupação também incluía vínculos já liberados.
AttendanceWeb agora filtra nome/número da mesa, oferece escolhas explícitas por
UUID e abre o detalhe mesmo fora da página de Contas. OrderWorkspace reutiliza
seleção serializada, mantém drafts por Tab e valida contexto pelo GET existente.
TabDetailView valida conjuntamente table_id/occupancy_id, Venue, geração, estado
ocupado, ocupação e associação não liberadas. Vínculo obsoleto retorna 409; UUID
inválido/parcial 400 e Tab de outro Venue 404. A lista exclui vínculos liberados,
sem apagar histórico. Contexto é uma precondição de leitura; não congela a mesa
nem amplia autorização de pedidos posteriores.

Retorno preserva filtro/foco/rascunho e usa a lista/polling existentes. Removida
a atualização completa que havia sido acrescentada a cada retorno: com 203 Tabs,
a sequência acumulava leituras financeiras redundantes. Não há mudança de
projeção financeira, mutation automática de mesa ou novo fluxo de pagamentos.

Evidência: 70 testes PostgreSQL PASS (hospitality_tables, ordering_foundation,
ledger_payments e tab_operations); incluem conflito de vínculo movido/liberado,
geração divergente, Venue, UUIDs e preservação do histórico/auditoria em leitura.
Jornada Web/API em rodada_web_e2e PASS com 203 Tabs: duas comandas da mesma mesa
fora da primeira página, ida/volta e drafts independentes em 360/390/430, sem
overflow horizontal com UUIDs reais. Confirmação final cria exatamente um Order
com três unidades/3000 centavos na Tab A; Tab B permanece com zero Orders e saldo,
Payments seguem vazios e ocupação/geração/vínculos permanecem iguais.

As execuções iniciais evidenciaram espera prematura no teste e leitura redundante
no retorno; não foram aceitas como PASS. Teste final aguarda respostas HTTP finais
(exclui redirects 308) e atualização iniciada após o readback, sem mudar tolerância
ou timeout das asserções. Testes visuais reutilizam stable() existente para auditar
estados assentados, sem aceitar baseline ou excluir regras de contraste.
Build final/tipos/diff PASS. Ruff: teste PASS; 15 RUF012 nas views permanecem,
comprovadamente iguais ao HEAD; imports corrigidos, sem regras suprimidas.
Logs locais ignorados em visual-artifacts/spec026/runtime/t06c-*.log/json.

Arquivos do recorte: attendance-web.tsx, order-workspace.tsx, ordering/views.py,
hospitality/views.py, test_hospitality_tables.py, testes Web table-entry.spec.ts
(visual e integração), e spec/plan/acceptance das proprietárias 001/004/026.
Limites: código curto, Android, nova Tab automaticamente vinculada, movimento
A→B, contexto após reload e versão publicada permanecem abertos. Consultas da
projeção financeira em volume seguem lacuna própria; não se afirma ganho de
latência/ergonomia humana. Próxima slice exata: T06d, apresentar movimento de
comanda A→B como ação operacional distinta de transferir consumo, reutilizando
contrato/autorização/auditoria/idempotência da Spec 009 e preservando Payments.

Suíte visual final: **318 PASS em 6,7 min**, incluindo oito cenários novos de
entrada/retorno, conflitos, pending e clique duplo, além dos 310 anteriores.
Nenhum baseline/tolerância relaxado. Revisão final do diff PASS; alterações
anteriores/worktrees preservadas. PostgreSQL e serviços de teste encerrados.
Sem commit, push, merge ou deploy. Critérios T06c marcados apenas no recorte Web.

## T06d — correção da API de movimento existente

Base atual conferida: main/ad5d64feca02b1f3b569f2dd51963a0e041d095e,
com alterações anteriores e worktrees preservadas. MOVE_LOCATION já existia;
não foi reconstruído. O gateway Attendance Web ainda não admite operations.
Antes de expor esse controle, a reprodução HTTP em PostgreSQL confirmou duas
lacunas: destino com geração divergente foi aceito (200 em vez de 409) e motivo
informado não chegou à auditoria, com e sem Payment. A divergência de geração
foi semeada deliberadamente; não se afirma ocorrência normal ou em produção.

Contrato da Spec 009 e plano/aceite atualizados antes do serviço. A validação
agora exige generation = Table.access_generation sob os locks existentes;
emit recebe o motivo já normalizado. Não há migration, novo comando, mudança
financeira, relaxamento de permissão ou alteração de UI. Replay exato retorna
o resultado original mesmo após liberação, sem recriar associação e sempre
reautorizando. A origem continua ocupada e o vínculo anterior permanece histórico.

Evidência atual: test_tab_location_safety, seis testes PostgreSQL PASS em
17.981s; regressão tab_operations/hospitality_tables/ledger_payments mais cinco
testes iniciais do recorte, 57 PASS em 118.264s. São 58 testes distintos, não 63.
Cobertura: geração inválida, destino indisponível/liberado/outro Venue,
capability negada, movimento pago/não pago, snapshots completos de
Orders/Charges/Payments, saldo, motivo/ator/hora, replay após liberação,
retries simultâneos e movimento versus liberação concorrente. Suites existentes
cobrem versão conflitante, dispatch ativo/concluído e transferências financeiras.

Comandos no diretório apps/api, PAYMENTS_TEST_DB_PORT=55476 e PYTHONUTF8=1:
`../../.venv/Scripts/python.exe manage.py test tests.test_tab_location_safety tests.test_tab_operations tests.test_hospitality_tables tests.test_ledger_payments --settings=rodada_api.settings_payments_postgres --noinput`;
reexecução final de `tests.test_tab_location_safety` no mesmo ambiente.
`manage.py check` e `makemigrations --check --dry-run`, ambos com settings_test,
PASS (sem alterações de schema). Ruff nos dois arquivos Python PASS, sem
supressões; import preexistente do serviço organizado. Diff revisado/check PASS.
Logs ignorados: visual-artifacts/spec026/runtime/t06d-before.log (falhas
reproduzidas), t06d-tests.log e t06d-final.log (resultados finais).

Arquivos: modules/tab_operations/services.py, tests/test_tab_location_safety.py,
spec/plan/acceptance da 009 e spec/plan/tasks/acceptance/revalidation da 026.
Sem UI alterada, não se reexecutaram build/tipos/visual Web ou jornada mobile;
o teste HTTP usa APIClient e PostgreSQL, não navegador. Android, dispositivo,
providers e versão publicada seguem sem evidência nova. Próxima tarefa exata:
concluir T06d no Atendimento Web com ação Mover comanda, origem/destino explícitos,
gateway restrito a MOVE_LOCATION, confirmação, proteção de intenção ambígua,
readback autorizado e testes Web/API em 360/390/430. T06 amplo permanece aberto.


## T06d — movimento explícito no Atendimento Web

Base main/ad5d64f permanece a mesma, com alterações anteriores/worktrees
preservadas. A lacuna Web comprovada era oferecer apenas associação de uma
comanda no diálogo da mesa, sem movimento explícito A→B e sem gateway para
MOVE_LOCATION. O domínio já existia na Spec009; não foi reconstruído.

Entregue: Mover comanda junto ao vínculo da mesa, ID/origem explícitos, leitura
contextual para capturar versão, escolha de outra mesa já ocupada, confirmação
origem→destino e motivo opcional. Gateway admite exclusivamente o payload de
MOVE_LOCATION; rejeita split/merge/reopen/cancel e fields financeiros adicionais.
Componente sempre montado preserva envelope antes de POST, sem credenciais,
por Venue/ator/sessão. Ref síncrona impede envio duplicado. Ambiguidade bloqueia
edição/navegação/saída; reload mostra Verificar mesmo movimento sem autoenvio.
Replay conserva versão/payload/chave e revalida auth/me. Só rejeição inicial
conhecida libera revisão; erro no replay preserva intenção. Sucesso exige
resultado imutável válido e readback autorizado de Tab e mesas; local atual
pode diferir do solicitado, sem recriar vínculo ou emitir nova operação.

Evidência atual:
- 58 testes API PostgreSQL PASS em 122.306s (tab_location_safety,
  tab_operations, hospitality_tables, ledger_payments).
- Uma jornada real Web/API PostgreSQL PASS, 22.4s de teste / 37.7s total:
  três larguras 360/390/430, comanda não paga e duas parcialmente pagas,
  perda de resposta depois do commit, reload, falha de readback e replay exato.
  Cada comanda tem uma TabOperation e um tab.location_changed. Orders, Charges,
  Payments, Refunds e LedgerAdjustments comparados integralmente antes/depois;
  saldo intacto, zero transferências, origem não liberada e vínculo antigo
  preservado com released_at. Gateway nega cinco operações distintas e fields
  lines/destination_tab_id/service_point_id/amount_cents, além de destino inválido.
- 13 cenários novos de navegador com fixtures PASS: três larguras, cancelamento
  sem POST, duplo toque, draft preservado, reload, payload idêntico, readback
  falho, sessão diferente, storage falho/corrompido, origem obsoleta, rejeição
  inicial versus replay rejeitado e destino já liberado após commit.
- Suíte visual completa final: 331 PASS em 7.2 min, incluindo os 13 novos;
  nenhum baseline/tolerância alterado. Checks de layout/acessibilidade das
  jornadas novas e regressões anteriores passaram.
- Build/types PASS; Ruff do serviço/teste API PASS; 12 testes auth/realtime PASS;
  revisão do diff/check PASS. API system check sem erros durante os testes.

A primeira execução visual falhou por fixture incompleta de party-size; foi
completada usando o contrato existente. A primeira integração consultou antes
concluir login; passou após esperar o botão autorizado ficar disponível. Essas
execuções iniciais não foram aceitas como evidência de sucesso. Nenhum timeout
ou tolerância de asserção foi relaxado. Capturas revisadas em 360/390/430:
visual-artifacts/spec026/t06d-move-{largura}.png (fixtures locais, não aparelho).

Comandos Web executados pelos CLIs locais: node node_modules/next/dist/bin/next
build; node node_modules/typescript/bin/tsc --noEmit; node
node_modules/@playwright/test/cli.js test (equivalente ao script test:visual).
package.json não define script test genérico nem lint Web. Integração:
playwright test --config playwright.integration.config.ts
 tests/integration/tab-location-move.spec.ts, com RODADA_E2E_POSTGRES=1,
POSTGRES_DB=rodada_web_e2e, host 127.0.0.1/55476 e RODADA_TEST_PYTHON apontando
à .venv. Banco exclusivamente descartável, recriado antes da jornada. A API usa
settings_payments_postgres e PAYMENTS_TEST_DB_PORT=55476, conforme seção anterior.
Logs ignorados: visual-artifacts/spec026/runtime/t06d-web-{build,focused,
integration,api,visual,unit}.log. Dados de teste e serviços locais encerrados.

Arquivos desta continuação: components/tab-location-move.tsx,
components/attendance-web.tsx, app/api/attendance/[...path]/route.ts,
tests/visual/tab-location-move.spec.ts, tests/integration/tab-location-move.spec.ts,
e documentação Spec004/009/014/026. Critérios marcados apenas no recorte Web/API.
Limites: mesma aba/sessão com storage íntegro; fechar aba, outra sessão/aparelho,
resolução gerencial e contexto guest não foram ampliados. Leitura contextual
não é lock duradouro da origem. Android/UX18, busca por código, demais lacunas
T06 e deploy/piloto continuam abertos. Não se afirma ganho de tempo humano.
Próxima slice do plano: T07/UX01 — tornar pedido e carrinho Android acessíveis,
com detalhes financeiros expansíveis e conferência de pagamento preservada;
revalidar estado atual antes de editar. Sem commit, push, merge ou deploy.

## T07a — carrinho Android e detalhes da conta (13/10/2026)

Base: main ad5d64f, com alterações anteriores preservadas. Android estava sem
alterações locais no início. Proprietária: Spec 001, contrato T07a; execução e
critérios contratados em Spec 026 antes do código. Worktrees preservadas.

Causa confirmada por inspeção: OrderCart era emitido depois de todos os produtos,
e o detalhamento financeiro permanecia expandido antes de Novo pedido. Não foi
medido tempo de procura no aparelho nem alegada reprodução publicada.

AttendanceScreen.kt agora mantém controle persistente Ver carrinho com quantidade
somada e total canônico do draft. A revisão abre no início da lista, reutiliza
OrderCart, e Voltar ao catálogo conserva posição e busca local. Navegação não
envia pedido nem altera linhas. Detalhes contábeis são expansíveis; saldo,
Pagar/Fechar e avisos continuam fora do disclosure. A revisão também mostra
alertas de limite/taxa. Condições financeiras, PaymentDialog, permissões,
ViewModel e envelope/replay existentes não foram alterados.

O primeiro teste de retorno revelou perda de posição quando o conteúdo lazy
mudava. A correção preserva índice/offset antes da alternância e os restaura
explicitamente. A regressão percorre até o produto 146, revisa e retorna à mesma
posição; confirma callbacks de quantidade, ausência de envio por navegação e
envio apenas pela confirmação. Outros casos verificam edição bloqueada/replay
explícito, disclosure sem mutation e guards de taxa, offline, busy e Tab fechada.
CriticalFieldsTest existente verifica nome/preço completos e revisão de pagamento,
incluindo caixa ativo, método, valor e cancelamento sem recebimento.

### Evidência desta execução

- Gradle Wrapper Windows: testDebugUnitTest assembleDebug lintDebug
  assembleDebugAndroidTest --console=plain: BUILD SUCCESSFUL (40s no último run).
  59 unitários em 22 suites, zero falhas; lint zero erros e oito avisos em arquivos
  não alterados. SDK android-37.0/build-tools 37.0.0; runtime disponível JDK 21,
  source/target Java 17. Não foi executado o script Linux que exige runtime JDK 17.
- Emulador exclusivo API 36 Google APIs x86_64, density 160:
  OrderWorkspaceTest (quatro cenários novos) + CriticalFieldsTest (três existentes),
  sete PASS em cada combinação 360×800/390×844/430×932 dp e fonte 1.0/1.5:
  42 execuções aprovadas. Capturas produzidas pelo teste com PNGs consecutivos
  idênticos; carrinho em 360 dp, fontes 1.0/1.5, inspecionado visualmente.
- PostgreSQL descartável localhost:55476, settings_payments_postgres:
  tests.test_ledger_payments tests.test_payments_concurrency
  tests.test_cash_management --noinput: 35 PASS em 41.110s. Cobre saldo, ledger,
  auditoria, replay e concorrência financeira existentes; nenhum endpoint novo.
- git diff --check PASS; revisão do diff sem conteúdo pessoal incorporado.

Logs locais ignorados: visual-artifacts/spec026/runtime/t07-build-final.log,
t07-ui-{360,390,430}-f{100,150}.log e t07-financial-postgres.log. Capturas:
visual-artifacts/spec026/runtime/t07-evidence/rodada-critical-evidence/.

Limites: testes Compose usam callbacks/fixtures, não uma jornada Android/API
com autenticação e recebimento real. Busca conserva o estado existente, mas
teclado/IME, TalkBack/foco completo, categorias, ergonomia humana, aparelho e
versão publicada não foram homologados. Interface Web não alterada nesta slice;
sua suíte não foi repetida. T07 permanece aberta, inclusive Nova comanda/Pedir.
Próxima slice exata: T07b/UX-10, confirmação da liberação de mesa Android com
identificação da mesa e revogação guest; cancelar deve produzir zero mutations.
Sem commit, push, merge ou deploy; sem operação na demo ou produção.

## T07b — confirmar liberação Android (13/10/2026)

Base main ad5d64f; alterações anteriores e worktrees preservadas. A causa era
TableCard chamar diretamente onRelease no primeiro toque. TablesScreen agora
captura mesa, label, ocupação e generation, abre revisão com encerramento da
ocupação, revogação do acesso guest atual e limpeza. Explicita que não fecha
comandas nem recebe pagamentos. Cancelar ou dismiss apenas limpa revisão;
confirmar limpa o alvo antes de chamar o callback existente, impedindo repetir
esse clique. Permissão, busy e identidade/generation/status da ocupação local
são revalidados; revisão divergente não adota a visita nova. API e regras
financeiras não foram alteradas. Contrato proprietário: Spec 004, T07b;
plano/aceite da Spec 026 definidos antes do código.

Arquivos: TablesScreen.kt e TableReleaseTest.kt; contratos/planos/aceite em
Specs 004/026. O teste inicial encontrou botão Cancelar com 40 dp; ambos os
botões receberam mínimo de 44 dp sem relaxar o teste.

Checks desta execução:
- Wrapper Android: testDebugUnitTest assembleDebug lintDebug assembleDebugAndroidTest
  --console=plain, BUILD SUCCESSFUL em 23s. 59 unitários PASS. Lint zero erros,
  oito avisos e duas sugestões em arquivos não alterados. Runtime local JDK 21,
  source/target 17 e SDK android-37.0/build-tools 37.0.0; script Linux/JDK 17 não rodado.
- TableReleaseTest: três cenários, todos PASS em 360×932/390×932/430×932 dp,
  density 160, fontes 1.0 e 1.5, emulador API 36 exclusivo: 18 execuções.
  Cancelar produz zero callbacks; confirmar identifica mesa original uma vez;
  mudança de ocupação/generation, busy ou perda de permissão bloqueiam.
  Captura 360 dp/fonte 1.5 inspecionada: efeitos completos e decisões legíveis.
- PostgreSQL descartável localhost:55476, settings_payments_postgres:
  tests.test_hospitality_tables tests.test_guest_access tests.test_ledger_payments
  tests.test_payments_concurrency --noinput: 48 PASS em 57.420s. Regressões de
  ciclo/autorizações/guest antigo, saldo, ledger, auditoria e concorrência existentes.
- Diff revisado e git diff --check PASS, sem conteúdo pessoal nos artefatos novos.

Evidências ignoradas em visual-artifacts/spec026/runtime/: t07b-build.log,
t07b-postgres.log, t07b-ui-{360,390,430}-f{100,150}.log e t07b-evidence/.
Emulador e PostgreSQL desta execução encerrados ao final.

Limites: Compose usa callbacks e fixtures; não se declara jornada Android/API
nem aparelho físico verificados. Back/toque externo seguem onDismissRequest
sem callback, mas não receberam ensaio separado. O endpoint ainda recebe apenas
Table.id: a verificação local não elimina uma disputa depois do snapshot nem
fornece recuperação durável de resposta perdida. Não foram alterados release,
ledger, Payments ou histórico. Web não alterada/testada nesta slice. Sem demo,
produção, commit, push, merge ou deploy.
Próxima tarefa exata: T07c/UX-11, distinguir Nova comanda de Pedir no Android,
reutilizando seleção explícita de destino e sem criação silenciosa de comanda.

## T07c — Pedir e Nova comanda Android (13/10/2026)

Base main ad5d64f; alterações anteriores/worktrees preservadas. A inspeção
confirmou Pedir conectado a openingTab=true, sem seleção de destino. O parâmetro
onOpenTab de TabList não tinha controle de criação correspondente.

AttendanceNavigation agora envia Pedir para TABS e chama onOrder. AttendanceScreen
usa essa ação apenas para mostrar Escolha a comanda para pedir; o caminho não
abre OpenTabDialog nem confirma pedido. TabList reutiliza selectTab autorizado,
mostra identificador abreviado para distinguir homônimos e filtra fechadas apenas
no modo pedir; Contas normal mantém seu histórico. Nova comanda é controle
explícito na lista Contas e título do diálogo. Loading/busy bloqueiam seleção e
criação. Workspace selecionado, draft e envelopes existentes não foram alterados.
Proprietária Spec 001/T07c; contratos e critérios definidos antes do código.

Arquivos de implementação: AttendanceScreen.kt, ui/AttendanceNavigation.kt,
OrderDestinationTest.kt e ui/AttendanceNavigationTest.kt. Specs 001/026 atualizadas.

Evidência desta execução:
- Gradle Wrapper Windows testDebugUnitTest assembleDebug lintDebug
  assembleDebugAndroidTest --console=plain: BUILD SUCCESSFUL em 28s. 59 unitários
  PASS. Lint zero erros, oito avisos e duas sugestões em arquivos não alterados.
  SDK android-37.0/build-tools 37.0.0 e runtime disponível JDK 21, source/target
  Java 17. Script Linux que exige runtime JDK 17 não executado.
- OrderDestinationTest (três novos cenários) e AttendanceNavigationTest (dois
  existentes, incluindo nova asserção de routing TABS): cinco PASS em cada
  configuração 360×932/390×932/430×932 dp, density 160, fontes 1.0/1.5,
  emulador API 36 exclusivo: 30 execuções. Homônimos selecionam IDs originais,
  sem chamar criação; vazio não cria automaticamente; criação explícita é distinta;
  loading/busy bloqueiam; navegação preserva geometria, labels e alvos de toque.
  Captura de escolha em 360 dp/fonte 1.5 inspecionada visualmente.
- PostgreSQL descartável localhost:55476, settings_payments_postgres:
  tests.test_ledger_payments tests.test_payments_concurrency --noinput:
  28 PASS em 44.355s, incluindo saldo/ledger/auditoria/replay/concorrência existentes.
- Diff revisado; git diff --check PASS; sem conteúdo pessoal incorporado.

Logs locais ignorados em visual-artifacts/spec026/runtime/: t07c-build.log,
t07c-postgres.log e t07c-ui-{360,390,430}-f{100,150}.log; capturas em t07c-evidence/.
Emulador e PostgreSQL desta execução encerrados ao final.

Limites: Compose verifica componentes reais e callbacks; ligação da tela ao
ViewModel também foi inspecionada, sem alegar jornada Android/API autenticada
ou aparelho físico. O inventário é a lista local existente, sem nova busca,
paginação Android ou seleção por mesa. Identificador abreviado é apoio visual,
não credencial nem código curto canônico. Persistência de draft, keyboard/IME,
TalkBack/foco completo e ergonomia humana continuam abertos. Web não alterada
nesta slice, sua suíte não repetida. Sem demo/produção, commit/push/merge/deploy.
Próxima tarefa exata: T07d/UX-17 — revisar teclados monetários e PIN, parse em
centavos com vírgula/ponto e validação de entradas nos diálogos Android existentes.

## T07d — teclados financeiros e parser exato (13/10/2026)

Base main ad5d64f; alterações/worktrees anteriores preservadas. Inspeção confirmou
campos de pagamento/limite/valor parcial sem teclado decimal e PINs financeiros
sem NumberPassword. Descobriu-se também que parseCents filtrava caracteres antes
de converter: texto como -3,00 ou abc3,00 podia produzir 300 centavos, e times(100)
não verificava overflow. Contratos Specs 006/009 e plano/aceite 026 precederam código.

OperationsModels.parseCents agora valida gramática explícita e usa BigDecimal
com deslocamento decimal/longValueExact, sem float ou arredondamento. Aceita
inteiros, vírgula/ponto com uma ou duas casas, ,5/.5, prefixo R$ e agrupamento
brasileiro 1.234,56; rejeita sinais, letras, formatos ambíguos, fração excessiva,
separador final, agrupamento sem fração e overflow. Zero permanece parseável;
positividade é guard do chamador. Campos de pagamento/estorno/limite/transferência
pedem Decimal, PINs de limite/correção/estorno pedem NumberPassword e mantêm máscara.
Limite ganhou feedback explícito e corpo rolável. Transferência parcial mostra
erro e bloqueia preview/commit de novo comando; falha de parse não vira amount_cents
zero. API, ledger, snapshots, autorização, review e envelopes/replay não mudaram.

Arquivos: operations/AttendanceScreen.kt, OperationsModels.kt, TabOperationsScreen.kt;
testes OperationsModelsTest.kt, MonetaryFieldsTest.kt e RefundFieldsTest.kt;
contratos/planos/aceite Specs 006/009/026.

Checks desta execução:
- Wrapper testDebugUnitTest assembleDebug lintDebug assembleDebugAndroidTest
  --console=plain: BUILD SUCCESSFUL em 26s no último build. 61 unitários PASS,
  incluindo novos casos de ponto/vírgula, agrupamento, Long.MAX_VALUE exato,
  negativo/texto/fração/overflow. Lint zero erros, oito avisos e duas sugestões
  em arquivos não alterados. SDK android-37.0/build-tools 37.0.0; runtime JDK 21,
  source/target 17. Script Linux com runtime obrigatório JDK 17 não executado.
- MonetaryFieldsTest (três novos), CriticalFieldsTest (três existentes) e
  RefundFieldsTest (um existente ampliado): sete PASS em cada combinação
  360×932/390×932/430×932 dp, density 160, fontes 1.0/1.5, emulador API 36
  exclusivo: 42 execuções. Pagamento inválido bloqueado e ponto produz 300 cents;
  transferência inválida não gera preview/zero e válida gera 300 cents sem commit;
  limite preserva motivo/PIN e produz 3100 cents. Revisão, caixa/método, estorno,
  chave de replay e cancelamento sem recebimento continuam testados.
- InputType do editor focado consultado no diagnóstico Android pelo teste:
  pagamento TYPE_CLASS_NUMBER + DECIMAL e PIN de estorno NUMBER + PASSWORD.
  Conteúdo do diagnóstico não é salvo nem impresso. Verifica solicitação real
  ao editor do emulador, sem homologar aparência/comportamento de IME físico.
- O teste de transferência inicialmente procurava um item lazy ainda não composto
  em fonte ampliada; passou a rolar a lista até o item antes da asserção, sem
  relaxar tolerâncias, sem baseline novo e sem ocultar falha de produto.
- PostgreSQL descartável localhost:55476, settings_payments_postgres:
  tests.test_ledger_payments tests.test_payments_concurrency tests.test_tab_operations
  --noinput: 48 PASS em 94.815s. Saldo/ledger/auditoria/replay/concorrência e
  neutralidade financeira de operações existentes preservados.
- Captura de estorno 360 dp/fonte 1.5 inspecionada; corpo rolável e decisões visíveis.
  Diff revisado e git diff --check PASS, sem contexto pessoal incorporado.

Logs ignorados em visual-artifacts/spec026/runtime/: t07d-build.log,
t07d-postgres.log, t07d-ui-{360,390,430}-f{100,150}.log; capturas em t07d-evidence/.
Emulador e PostgreSQL desta execução encerrados ao final.

Limites: callbacks/fixtures Compose, não jornada Android/API autenticada nem
aparelho. PINs/teclados de limite/correção e valor parcial têm configuração
inspecionada; InputType real foi ensaiado para pagamento e estorno. Seleção
automática do valor, IME físico, TalkBack/foco completo e ergonomia humana seguem
abertos. Web não alterada/testada nesta slice. Sem demo/produção, commit, push,
merge ou deploy. Gates globais da T07 não são encerrados por esses checks.
Próxima tarefa funcional exata: T08/UX-13 — Repetir rodada, copiando histórico para
novo draft/intenção e revalidando produto, preço, configuração e disponibilidade.

## T08a — repetir rodada Android (13/10/2026)

Base: main ad5d64f mais alterações locais preservadas; nenhuma versão publicada
verificada. O histórico Android descartava Product.id/configuração estruturada
já presentes no GET da API e não oferecia repetição. OperationsHttpClient agora
lê IDs do snapshot; OrderItem conserva configuração e texto histórico. A revisão
em RepeatOrder.kt/RepeatOrderDialog.kt compara com catálogo atual sem defaults.
AttendanceScreen abre a ação por pedido; OperationsViewModel inclui no carrinho
apenas o conteúdo revisado ainda válido. Não faz mutation financeira nem envio.

Repetição preserva draft existente, quantidade restante, variantes/opções/nota,
IDs novos de linha e fluxo existente de nova intenção no Confirmar pedido.
Cancelamentos/exclusões são informados. Produto ausente/inativo/indisponível,
configuração inválida/removida, legado sem snapshot e limites inválidos bloqueiam
toda a inclusão. Mudança durante revisão, Tab fechada/diferente, busy/loading,
offline ou pedido pendente impedem inclusão. Não há resolução automática dos
bloqueios; o operador pode escolher novamente os itens no catálogo.

Validação local:
- Wrapper Windows: testDebugUnitTest, assembleDebug, lintDebug,
  assembleDebugAndroidTest PASS. 67 testes unitários, incluindo 6 de repetição.
  JDK 21 disponível, target 17; não equivale ao script Linux/JDK 17.
  Lint: 0 erros, 8 warnings e 2 hints existentes. Build final 32 s.
- PostgreSQL descartável em 127.0.0.1:55476: manage.py test
  tests.test_customization tests.test_ledger_payments tests.test_payments_concurrency
  tests.test_tab_operations --settings=rodada_api.settings_payments_postgres
  --noinput: 61 PASS em 136,849 s. Nova regressão repete snapshot com nova intenção:
  preço atual 4000 vs histórico 3800, dois Orders/Charges, replay sem terceiro,
  snapshot original intacto e nova seleção indisponível rejeitada sem Charge.
  Payments/ledger/concorrência cobertos pela suíte existente, sem alteração de domínio.
- Ruff do teste API alterado PASS pelo uv tool run; não estava instalado na venv
  nem no cache inicial. A ferramenta foi obtida no cache de tools sem modificar
  dependências do projeto.
- Não houve alteração de UI Web; suíte Web não foi executada nesta slice.

Testes: RepeatOrderTest.kt, RepeatOrderDialogTest.kt e nova regressão em
apps/api/tests/test_customization.py. Também reexecutados OrderWorkspaceTest
(carrinho/bloqueios) e CriticalFieldsTest (conferência financeira).
Primeira captura tentou janela raiz e falhou; corrigida para isDialog.
Inspeção visual identificou sobreposição das ações em 360/fonte 150%, corrigida
com ações em coluna; teste passa a verificar regiões verticais separadas.

Limites: sem journey Android autenticado → API real nessa execução, aparelho
físico, IME físico, ganho de tempo humano ou deploy. Snapshot legado vazio é
bloqueado explicitamente. Web/guest e continuidade entre Tabs não implementados.
Próxima slice exata: T08b/UX-13 — repetir rodada staff Web com revisão equivalente,
preservação de drafts por Tab e intenção recuperável existente; validar Web/API
PostgreSQL, 360/390/430 e suíte visual completa sem relaxar baseline.

Matriz final de emulador Android API 36: 360/390/430 dp, altura 932 dp, densidade 160, fontes 100%/150%. 10 casos × 6 configurações = 60 execuções PASS (3 repetição, 4 carrinho, 3 campos críticos). Logs t08-ui-final-*.log e PNG repeat-order-w*-f*.png em visual-artifacts/spec026/runtime; capturas novas de repetição e regressões distinguem-se das capturas anteriores. Revisão manual da captura 360/150 confirmou ações separadas. git diff --check PASS; alterações anteriores/worktrees preservadas e contexto pessoal ausente dos artefatos desta slice.

## T08b — repetir rodada no Atendimento Web (13/10/2026)

Base main ad5d64f mais alterações anteriores preservadas. O histórico mostrava
configuração somente por rótulos e não copiava rodadas para o rascunho. A API já
retornava IDs/custos/snapshot necessários: nenhuma mutation ou contrato financeiro
novo foi introduzido. Snapshot em product-customization agora admite IDs históricos;
repeat-order.tsx valida/revisa e order-workspace.tsx integra leitura e inclusão.

Cada pedido confirmado agora tem grupo Rodada e ação Repetir rodada. A ação lê
GET autorizado do detalhe e catálogo antes de abrir ActionDialog. A revisão mostra
nome, configuração e centavos antigos/atuais, total a adicionar, diferenças,
exclusões canceladas/sem quantidade e motivos de bloqueio. Não faz matching por
nome, não usa defaults, não corta quantidades nem omite parcialmente itens inválidos.
Legado sem snapshot/preço, ausência/inatividade/indisponibilidade, variante removida,
seleção inválida e quantidade fora do limite Web 1–99 bloqueiam toda a inclusão.

Adicionar é local, explícito e protegido contra duplo clique; conserva rascunho
existente e outras Tabs, incluindo configurações diferentes do mesmo Product.
Navegação é bloqueada durante leitura/revisão; estado ocupado/pendente, dados não
fresh, Tab divergente/fechada e catálogo local alterado impedem inclusão. Falha ou
Voltar preserva draft. A revisão representa a leitura atual, não reserva preço ou
estoque: a API revalida disponibilidade/preço/limite/autorização na confirmação.
Mudanças de histórico só são conhecidas quando há nova leitura canônica; não foi
introduzido lock/reserva sobre o histórico nem garantia entre GETs e confirmação.

Confirmar usa useOrderIntent existente: nova chave, envelope recuperável, mesmo
payload no replay e readback. Original nunca é reenviado como nova intenção.
Nenhuma alteração em snapshots históricos, domínio, banco, Payments ou ledger.

Checks já concluídos:
- Build Next PASS pelo CLI documentado equivalente a npm run build.
- TypeScript tsc --noEmit PASS após novos testes.
- PostgreSQL descartável em 127.0.0.1:55476: tests.test_customization,
  tests.test_order_intent_concurrency, tests.test_ledger_payments e
  tests.test_payments_concurrency com settings_payments_postgres: 43 PASS em
  45,680 s. Testam snapshots/configuração e regressões financeiras/replay/concorrência.
- 3 jornadas Web/API reais em banco exclusivo rodada_web_e2e, 360/390/430 PASS
  em 37,3 s. Original 1000, catálogo atualizado 1200, draft prévio 500 e rodada
  repetida produzem saldo 2700; dois Orders/três Charges, snapshot original intacto.
  Resposta abortada depois de commit e replay com mesmo payload produzem a mesma
  nova Order, sem terceira Order/cobrança duplicada. Draft da outra Tab permanece;
  outra Tab sem Order e saldo zero. Payments dessas jornadas permanecem vazios;
  casos financeiros com recebimento/estorno são cobertos pela suíte existente acima.
- 10 casos iniciais fixture PASS; as três primeiras tentativas falharam porque
  a asserção da requisição foi feita antes do callback assíncrono. Usada espera
  pelo evento observável, sem relaxar tolerâncias/baseline. Caso adicional de
  variante/adicional/configuração distinta incluído na suíte completa.

Artefatos novos: components/repeat-order.tsx, tests/visual/repeat-order.spec.ts,
tests/integration/repeat-order.spec.ts. Editados order-workspace.tsx e
product-customization.tsx; contratos/planos/critérios das Specs 001, 010 e 026.
Logs t08b-{build,visual-focused-final,visual-full,integration,financial-tests}.log
em visual-artifacts/spec026/runtime. Capturas repeat-order-{draft,real}-*.png
em apps/web/test-results; inspeção manual do draft de 360 confirmou grupos,
linhas/configurações e ações legíveis. Resultado da suíte completa registrado abaixo.

Não há script npm run test ou lint Web no package.json; npm não está no PATH.
Executado o equivalente de test:visual pelo CLI Playwright documentado, sem alterar
scripts/dependências. Android não foi alterado/reexecutado nesta slice. Sem demo,
produção, versão publicada, aparelho ou ganho de tempo humano homologados.
UX-13 fica parcial globalmente: repetição guest e Web POS não implementadas.
Próxima slice: T08c/UX-13 — repetir histórico guest com sessão/ocupação originais,
revisão e bloqueio/revogação, preservando intenção recuperável de T05b.

Resultado final T08b: 342 testes visuais PASS em 6,8 min, incluindo os 11 novos
casos de repetição e configuração. Baselines/tolerâncias preservados. Build e
tipos PASS, git diff --check PASS. Revisados código/diff e artefatos da slice,
sem contexto pessoal incluído. PostgreSQL descartável desligado; servidores
Playwright encerrados pelo runner. Alterações anteriores/worktrees preservadas.
Sem commit, push, merge ou deploy. Critérios T08b comprovados marcados; T08
global permanece aberto para guest/Web POS e gates publicados/humanos.

## T08c / UX-13 — repetição guest (2026-10-13)

Base conferida: main ad5d64f; alterações anteriores e worktrees preservadas.
Guest não oferecia repetição. A revisão compartilhada de T08b já resolvia IDs,
configuração, diferenças e exclusões; reutilizada. Descoberta adicional: contexto
permitia consulta durante bloqueio, mas só projetava bloqueio emergencial do Venue,
sem informar o bloqueio/modo da mesa. API já rejeitava mutations corretamente.
Acrescentado guest_policy.table_ordering_enabled na projeção autorizada existente;
sem nova mutation, lock ou regra financeira. Ausência da flag bloqueia repetição.

Abrir/incluir reconsultam contexto e catálogo e exigem token/scope/Tab originais.
Mudança de preço/configuração exige nova revisão. Inclusão única preserva draft;
Enviar continua separado e usa intenção recuperável T05b. Produto/configuração
inválidos impedem inclusão inteira; cancelados/zero são excluídos explicitamente.
Não resolve QR, cria sessão/comanda ou altera histórico durante repetição.

Evidência local:
- 17 novos testes fixture PASS (14,6 s): preços, configuração distinta, legacy,
  quantidade inválida, item ausente/indisponível, variant removida, bloqueios,
  revogação, falha e mudança de token/scope/Tab; draft preservado e sem POST.
- Quatro jornadas Web/API reais PostgreSQL PASS (41,4 s): 360/390/430 e bloqueio
  de mesa após revisão. Cancelar preserva item prévio; inclusão não confirma.
  Resposta perdida após commit e replay do payload original resultam em apenas
  dois Orders; intenção distinta da original, exposição 2500, histórico original
  idêntico e Payments vazios preservados. Token permanece original e quantidade
  de resoluções QR não aumenta durante repetição. A inicialização real pode
  resolver duas vezes; a primeira asserção contava desde a abertura, corrigida
  para comparar antes/depois da repetição, sem mudar produto ou tolerâncias.
- 53 testes PostgreSQL de guest/customização/concorrência de intenção/ledger/
  pagamentos PASS (46,785 s); sete testes de bloqueio geral guest PASS (11,062 s).
  Comparação inicial do teste novo misturava POST e GET (GET inclui state_source);
  corrigida para comparar duas projeções GET e preservar o histórico completo.
- Ruff dos arquivos Python alterados, typecheck Web, Next build PASS.
  Sem script npm run test ou lint Web; test:visual executado pelo CLI equivalente.
- Captura real de 360 inspecionada: carrinho com item anterior e item repetido,
  ações legíveis e envio separado. Capturas 390/430 produzidas pela jornada.

Arquivos do recorte: API guest_access/views.py e tests/test_guest_access.py;
Web guest-ordering.tsx, repeat-order.tsx e lib/client/guest-order-intent.ts;
novos tests/{visual,integration}/guest-repeat-order.spec.ts; contratos/planos/
aceites das Specs 004, 010 e 026. Logs t08c-* em visual-artifacts/spec026/runtime;
capturas guest-repeat-{draft,real}-*.png em apps/web/test-results.

Limites: fixture não é versão publicada; pagamentos não vazios exercitados na
suíte financeira, não na jornada guest deste recorte. Revogação/rede/conteúdo
alterado têm fixtures e API, sem aparelho/observação humana/deploy. Android não
alterado. UX-13 permanece parcial globalmente: Web POS ainda aberto. Próxima
slice exata: T08d/UX-13 — revisão e inclusão de rodada histórica no Web POS,
reutilizando a revisão compartilhada e a recuperação da intenção existente.
Resultado da suíte visual completa e encerramento registrados abaixo.

Resultado final T08c: 359 testes visuais PASS em 7,1 min, sem alteração de
baseline/tolerância. Typecheck e git diff --check PASS após testes/documentação.
Diff do recorte revisado, sem dados pessoais. PostgreSQL descartável encerrado;
servidores locais encerrados pelo runner. Sem commit/push/merge/deploy.
Critérios T08c comprovados marcados; T08 global permanece aberto para Web POS.

## T08d / UX-13 — repetição no PDV Web (2026-10-13)

Base main ad5d64f; alterações anteriores/worktrees preservadas. Inspeção atual
confirmou que OrderWorkspace já compartilhava revisão/inclusão/recuperação com
Atendimento, mas repeatAllowed e exibição do histórico restringiam o comando à
superfície withoutPayments. A lacuna era de exposição/guards do PDV, não de API.

Contrato atualizado nas Specs 001/010 e plano 026 antes da implementação.
Habilitada repetição no PDV com histórico e revisão existentes; região Pedido
atual identifica o draft. Recebimento bloqueado durante leitura/revisão e
personalização impede abrir repetição. Sem nova mutation, regra financeira,
snapshot, dependência, CSS ou mudança de autorização. Cancelar preserva draft;
incluir não envia; Confirmar pedido cria a nova intenção e usa recuperação T05.

Validação local:
- 12 testes focados fixture PASS (11,8 s): Web360/390/430, preços anterior/atual,
  exclusões de cancelados, inclusão única, draft existente, legado/variante
  removida/quantidade inválida/ausência/inatividade/indisponibilidade, leitura
  falha, catálogo alterado, recebimento ambíguo e fechamento durante revisão.
- Três jornadas Web/API PostgreSQL PASS (36,6 s), banco exclusivo rodada_web_e2e.
  Original 1000, catálogo atual 1200 e draft prévio 500: exposição final 2700,
  dois Orders/três Charges. Resposta perdida após commit e replay idêntico
  retornam a mesma nova Order, sem terceira cobrança. Snapshot original e preço
  1000 preservados; Payments permanecem vazios, sem recebimento nestas jornadas.
  Outra Tab conserva draft, zero Order e exposição zero. Casos com pagamentos
  não vazios pertencem à suíte financeira, não a esta jornada de repetição.
- 43 testes PostgreSQL de customização, concorrência de intenção, ledger e
  pagamentos PASS (44,772 s). Nenhum arquivo Python alterado nesta slice.
- Next build e typecheck PASS; não há script npm run test/lint Web no package.
  Suíte visual executada pelo CLI equivalente de test:visual, npm fora do PATH.
- Captura fixture de 360 inspecionada: histórico/repetição, draft prévio e linha
  repetida com nota, confirmação separada, recibo abaixo. Capturas reais 360/390/
  430 incluem retorno à outra Tab e preservação do seu draft.

Tentativas iniciais: compilação restrita falhou por acesso ao runtime Windows;
reexecução com autorização local revelou fechamento JSX incorreto, corrigido e
recompilado. Um teste fixture ainda interceptava listagem Attendance em vez de
PDV; corrigido para a rota real. Journey inicial tentou login na tela POS em vez
do staff; interrompida e corrigida para login real antes da navegação. Nenhuma
falha escondida por baseline, tolerância ou alteração do produto para o teste.

Arquivos: components/order-workspace.tsx; novos tests/visual/pos-repeat-order.spec.ts
 e tests/integration/pos-repeat-order.spec.ts; contratos/planos/aceites 001/010/026.
Logs t08d-{build,visual-focused-final,integration-final,financial,visual-full}.log
em visual-artifacts/spec026/runtime. Capturas pos-repeat-order-{draft,real}-*.png
em apps/web/test-results. Diff do recorte revisado sem dados pessoais.

Próxima tarefa exata: T09a / UX-14 — quantidades guest e agrupamento somente de
configuração idêntica, preservando confirmação, intenção e bloqueios/revogação.
UX-13 ganha cobertura local nas quatro superfícies previstas; jornada Android/API
integral, versão publicada, aparelho físico e ganho de tempo humano permanecem
não homologados. Não transformar esses gates em critério local comprovado.
Resultado visual completo e encerramento do ambiente registrados abaixo.

Resultado final T08d: 371 testes visuais PASS em 7,2 min, sem alterar baseline ou
tolerância. Typecheck e git diff --check PASS após documentação final. PostgreSQL
descartável encerrado; servidores de teste encerrados pelo runner. Worktrees e
alterações anteriores preservadas. Sem commit, push, merge ou deploy. Critérios
locais T08 comprovados marcados; gates externos continuam abertos. Próxima T09a.

## T09a / UX-14 — quantidades guest (2026-10-13)

Base main ad5d64f e worktrees preservadas. Causa: addConfigured anexava sempre
uma linha quantity=1 e o guest só permitia Editar/Remover. Agrupamento local por
Product ID, variant ID, option IDs ordenados em cópia e nota literal resolve o
recorte. Copiar linhas antes de agrupar evita alterar objetos do draft anterior.
Validação integral retorna falha se qualquer soma sair de 1–99; inclusão, edição
e repetição não truncam nem descartam unidades. Edição preserva quantidade;
+/− recalculam total e zero remove. Repetição usa o mesmo agrupamento.

Aumento exige visita/Tab elegível, dados atuais, item/configuração disponíveis e
sem bloqueio de mesa/Venue/consumo. Redução/remoção permitem corrigir rascunho
obsoleto/indisponível. Intent pendente/envio/revisão/personalização bloqueiam
mudanças; replay conserva o envelope T05b. Bloqueio conhecido também desabilita
catálogo e envio. API permanece responsável pela revalidação transacional.
Nenhuma mudança de endpoint, domínio financeiro, snapshot confirmado ou Payment.

Contratos 004/010, plano/aceites 026 atualizados antes do código. Apenas componente
guest-ordering.tsx e novos tests/{visual,integration}/guest-quantity.spec.ts no
recorte de código; documentação das Specs 004/010/026. Tokens/grid de quantidade
existentes reutilizados, sem CSS ou dependência nova.

Evidências:
- 45 testes focados de quantidade/repetição/recuperação guest PASS após correção
  dos alvos de toque. Incluem 14 novos cenários: mobile, configuração por IDs,
  ordem de opções, nota literal, edição/agrupamento, zero remove, limite 99,
  overflow de edição/repetição e draft preservado, bloqueio/revogação/offline/
  indisponibilidade e replay imutável. Execução completa final cobre último layout.
- Três jornadas Web/API PostgreSQL no banco exclusivo rodada_web_e2e: toques
  agrupados, +/−, edição de nota mantendo quantidade, fusão da configuração
  idêntica e remoção a zero. Quantidade final 2, uma linha/um Order, Charge total
  2000 e exposição 2000, nota Sem sal, Payments vazios preservados. Resposta
  abortada depois de commit e replay idêntico retornam mesmo Order, sem cobrança
  duplicada. Em 390, bloqueio real de mesa preserva draft e impede aumento/envio;
  desbloqueio + atualização permitem seguir. Resultado/tempo final abaixo.
- 60 testes PostgreSQL guest/bloqueio geral/customização/concorrência de intenção/
  ledger/pagamentos PASS (55,712 s). Casos com Payments não vazios pertencem à
  suíte financeira; jornada guest deste recorte não recebeu pagamento.
- Next build e typecheck PASS. Sem alteração Python; Ruff não aplicável ao recorte.
  package Web não oferece npm run test/lint; test:visual pelo CLI equivalente.
- Primeira execução visual teve seis falhas reais de alvo de toque menor que
  44 px. Corrigida com layout existente, sem mudar teste/tolerância. Inspeção
  posterior da captura real de 360 revelou Editar/Remover quebrando palavras;
  distribuição corrigida no grid e suíte completa reiniciada. Captura final de
  360 inspecionada: rótulos legíveis, +/−/quantidade alinhados, envio separado.
  Capturas reais 390/430 geradas independentemente pela jornada.

Logs t09a-{build,visual-focused-final,integration-final,financial,visual-full}.log
em visual-artifacts/spec026/runtime; capturas guest-quantity[-real]-*.png em
apps/web/test-results. Nenhuma baseline/tolerância alterada. Mudanças anteriores
preservadas e diff do recorte revisado sem dados pessoais.

Limites: não há prova de publicação, aparelho físico ou ganho de tempo humano.
Busca/categorias/146 produtos, persistência e criação automática de comanda
continuam fora do recorte. Próxima exata: T09b / UX-15 — descoberta no catálogo
guest com busca/categorias e fixture de 146 produtos, preservando o draft e os
bloqueios existentes. Checks finais e encerramento registrados abaixo.

Resultado final T09a: 385 testes visuais PASS em 7,3 min, sem alteração de baseline/
tolerância; três jornadas reais finais PASS em 28,1 s. Typecheck, build e diff PASS.
PostgreSQL descartável encerrado e servidores de teste encerrados pelo runner.
Worktrees/alterações anteriores preservadas. Sem commit, push, merge ou deploy.
Critérios T09a comprovados marcados; T09b/UX-15 e gates externos permanecem abertos.

## T09b / UX-15 — descoberta guest (2026-10-13)

Base main ad5d64f e alterações/worktrees anteriores preservadas. Causa: catálogo
guest linear, sem busca/categorias e sem Product.category no GET. Projetado campo
persistido na leitura autorizada existente; UI reutiliza apresentação/collation
por nome do Atendimento, sem inferir categorias a partir de estação. Todos
inicial, busca global sem acento/caixa e trim nas bordas, categoria mantida ao
limpar busca, fallback Todos se removida, resultados vazios/contagem acessíveis.
Pedido atual foca/rola o draft sem envio ou nova comanda/sessão. Filtro não corta
o catálogo canônico que alimenta configuração, quantidade e revisão.

Contrato/planos nas Specs 004/010/023/026. Código: guest_access/views.py,
tests/test_guest_access.py, components/guest-ordering.tsx e novos
 tests/{visual,integration}/guest-catalog.spec.ts. Sem migration, nova mutation,
regra financeira, dependência ou CSS. Product IDs, snapshots e Payments mantidos.

Evidência local:
- O CSV versionado aderlan-menu-2026-10-09.csv contém 143 produtos, verificados
  por leitura CSV; fixture total 146 composta por esses 143 e três produtos já
  existentes nas fixtures Web. Não declarar catálogo publicado de 146 produtos.
- Oito novos testes fixture PASS (11,6 s) antes da última correção de posição;
  execução completa final repete todos com o código final. Mobile360/390/430,
  busca acentuada/global, categorias, retorno, vazio, fallback, preservação de
  nota/quantidade/IDs, Pedido atual/foco, indisponibilidade, bloqueios/revogação,
  intenção pendente e replay imutável. Sem baseline/tolerância nova.
- Três jornadas reais Web/API PostgreSQL PASS (32,3 s), banco exclusivo
  rodada_web_e2e, com duas categorias reais de fixtures. Filtrar Bebidas e buscar
  Kitchen globalmente, manter duas unidades/nota Sem sal, alternar Pratos e
  buscar Bar, remover Bar, usar vazio/retorno/Pedido atual sem mutação. Bloqueio
  real de mesa em 390 preserva draft e impede envio; liberar/atualizar permite
  seguir. Resposta perdida após commit e replay idêntico produzem um Order com
  uma linha de duas unidades, Charge total2000, exposição2000 e Payments vazios
  preservados. Casos não vazios pertencem à suíte financeira, não à jornada.
- 61 testes PostgreSQL guest/bloqueios/customização/concorrência/ledger/pagamentos
  PASS (63,158 s), incluindo nova projeção de categoria real/vazia e scope intacto.
- Ruff dos dois arquivos Python, Next build, typecheck e diff PASS. package Web
  não tem npm run test/lint; CLI equivalente de test:visual usado, npm fora PATH.
- Captura real de 360 inspecionada: busca/categorias/retorno ao draft legíveis,
  quantidade e nota intactas; capturas independentes em 390/430. Não medir ganho
  humano ou afirmar equivalência de aparelho físico com emulação de viewport.

Falhas e correções: leitura CSV de fixture via Python usava saída Unicode nativa
Windows interpretada como UTF-8; corrigida serialização ASCII JSON (nomes reais
restaurados), sem mudar busca. Objetos compartilhados nas fixtures contaminavam
cenário seguinte após indisponibilidade; copiados por caso. Journey real inicial
comprovou defeito de posição: atalho surgia só no primeiro item e deslocava o
produto entre dois toques, perdendo a segunda inclusão. Atalho agora sempre
visível, desativado vazio; novo contrato e build, jornada repetida comprovou
quantidade2. Nenhuma asserção financeira foi relaxada.

Logs t09b-{build,visual-focused-final,integration-final,financial,visual-full}.log
em visual-artifacts/spec026/runtime; capturas guest-catalog[-real]-*.png em
apps/web/test-results. Diff do recorte revisado sem dados pessoais. Limites:
fixture143+3 não comprova catálogo publicado, tempos humanos, paridade integral,
aparelho ou provider. Criação automática de comanda não foi escolhida nesta
execução e fica fora de T09; identidade/sessão e confirmação existentes mantidas.
Próxima exata: T10a / UX-04/05/23 — acesso ao passe e à disponibilidade na produção,
revalidando o que já existe antes de implementar; lote não entra nessa slice.
Resultado visual completo e encerramento registrados abaixo.

Resultado final T09b: 393 testes visuais PASS em 7,6 min, sem baseline/tolerância
alterados. Ruff, build, tipos e diff PASS após documentação final. PostgreSQL
descartável e servidores de teste encerrados. Worktrees/alterações anteriores
preservadas; sem commit, push, merge ou deploy. Critérios T09a/T09b comprovados
marcados, criação automática não escolhida e gates externos abertos. Próxima T10a.


## T10a — acesso ao passe/disponibilidade na produção

Base atual conferida: main ad5d64f; alterações anteriores e worktrees preservadas.
A inspeção confirmou UX-05: fila/resumo/passe e ferramentas empilhados em mobile,
sem acesso direto. Fixture de 30 linhas confirmou passe abaixo da primeira tela.
Produção já usava início manual; não houve reimplementação de UX-03.

Contrato atualizado em Specs 019/026 e design system antes do código.
ProductionBoard oferece Fila/Prontos/Disponibilidade sticky apenas mobile.
Contagens são linhas/produtos do snapshot, desconhecidas antes da leitura.
Cada atalho rola/foca região montada; não cria mutation nem limpa estado.
Erros/pendências conservam os bloqueios existentes; desktop conserva layout.

Arquivos deste recorte: production-board.tsx, globals.css, testes visuais
production-regions.spec.ts e production-regions-pending.spec.ts, integração
production-regions.spec.ts; Specs 019/023/026 e docs/design/system.md.
API, schema, snapshots financeiros e autorizações não alterados.

Jornadas reais: seis testes, Bar/Cozinha em360/390/430, PostgreSQL exclusivo
rodada_web_e2e. 30 linhas com notas distintas; limite autorizado com reautenticação
e chave idempotente no ambiente de teste, sem inventar recebimento. Navegação
conserva detalhe integral da Tab; indisponibilidade/reabertura conserva pedidos
e finanças; preparo manual deixa exatamente1READY e29NEW; Payments preservados.
Regressões:42 testes PostgreSQL (full_shift_smoke, customization, ledger_payments,
payments_concurrency),71.552s PASS. Build e tipos PASS.

A primeira fixture falhou por seletor ambíguo de alert (anunciador Next), corrigido
para o alerta da operação. A primeira jornada real respeitou o limite de consumo
e rejeitou o pedido grande; fixture passou a usar override autorizado, não bypass.
Captura inicial360 revelou quebra de Disponibilidade; token text-xs e linha
separada para contagem corrigiram legibilidade. Captura real360 inspecionada.
Rótulos longos de comandas ainda podem ocupar várias linhas no passe/tickets: padrão
preexistente, não homologado como ergonomia integral.

Sem script npm test ou lint Web no package.json; executados comandos documentados
de test:visual/test:integration, typecheck e build via Node instalado.
UX-04 (configuração/lote) e UX-23 (concorrência independente) permanecem abertos;
nenhuma inferência ou mutation em lote implementada. Tempo humano, aparelho físico,
versão publicada e gates globais T14 não verificados. Sem commit/push/merge/deploy.

Próxima exata: T10b / UX-04 — distinguir configuração operacional no agrupamento
de produção e contratar execução de lote compatível antes de implementar mutations.

Validação final T10a:401 testes da suíte visual completa PASS (8.6m), mais1
teste focado de navegação durante mutation pendente PASS. O teste adicional foi
criado após a descoberta da suíte completa e executado separadamente: não é
relatado como parte daquela execução. Nenhuma referência/baseline/tolerância
alterada.6 Web/API PASS (59.7s),42 PostgreSQL PASS (71.552s), tipos/build/diff PASS.
Logs: visual-artifacts/spec026/runtime/t10a-{build,visual-full,pending,
integration-final,postgres-tests}.log. Capturas mobile de ambas estações em
apps/web/test-results/production-regions-{KITCHEN,BAR}-{360,390,430}.png
e production-regions-real-{KITCHEN,BAR}-{360,390,430}.png. Capturas fixture e
real360 inspecionadas; as demais foram geradas e tiveram asserções independentes.
PostgreSQL descartável encerrado; servidores Web/API encerrados pelos runners.


## T10b — configuração confirmada no resumo de produção

Base conferida main ad5d64f, diff/worktrees anteriores preservados. Inspeção da
ProductionBoard confirmou agrupamento somente product_id, sem configuração no
resumo; transição individual canônica não fornece replay de comando de lote.
Não foi alegada reprodução anterior no navegador nesta continuação.

Contrato atualizado antes do código em Specs010/026. Resumo usa assinatura
operacional do snapshot: IDs/nome/semântica, observação exata e campos adicionais,
ordem JSON/modificadores normalizada; preços/quantidade/total excluídos. Snapshot
sem configuração verificável ou identidade/routing divergentes fica independente
com aviso, sem consultar defaults atuais. CustomizationText aparece no resumo
e continua na fila. Estados distintos podem compartilhar resumo com contagens;
resumo não é seleção nem autorização de lote.

Mudanças: lib/client/production-groups.ts, components/production-board.tsx,
package.json (test:production), tests/production-groups.test.mjs, visual/
production-configuration.spec.ts, integration/production-configuration.spec.ts,
visual/customization.spec.ts e visual/parity.spec.ts; Specs001/010/019/023/026 e
design system. API/schema/mutations não alterados.

Cinco unitários PASS: igualdade, preços/quantidades, IDs/semântica/nome/nota exata,
ordenação, campo operacional futuro, incompletude/routing e imutabilidade.
Seis Web/API PostgreSQL PASS (43.3s): ambas estações360/390/430, cinco linhas em
quatro grupos (3unidades simples,1grande,1nota,1adicional); replay conserva1Order.
Variante posteriormente renomeada/reprecificada e produto indisponível conservam
configuração e detalhe financeiro original. Preparo manual altera só1linha,
preservando snapshots e Payments. Charges750, recebimentos0 no cenário de teste.
47 PostgreSQL PASS (57.972s): full_shift_smoke, customization, customization_mix,
ledger_payments, payments_concurrency. Build/tipos PASS.

Testes antigos alterados por contrato, não por tolerância: fixtures sem snapshot
agora esperam cada linha independente; V03 mantém export/derivação original e
compara os chips/quantidades da Web contra suas linhas legadas, sem afirmar
igualdade visual com agrupamento antigo. As três asserções de customização agora
verificam resumo e fila separados, pois texto canônico aparece nos dois. A primeira
execução visual detectou ambiguidade desses seletores e foi interrompida; execução
focada parcial também interrompida para concentrar a validação na suíte final.
Nenhuma dessas execuções incompletas é relatada como PASS integral.

Contrato futuro de lote definido em Specs001/010/026: revisão explícita, comando
idempotente, precondições de configuração/estado/quantidade, locks determinísticos,
resultado por linha e rejeição integral de conflitos/falhas. Implementação,
concorrência/replay de lote e ergonomia humana seguem pendentes. UX04 é parcial,
UX23 permanece aberto. Não declarar ganho humano, aparelho ou versão publicada.

Próxima exata: T10c — implementar comando canônico de lote e revisão Web, com
replay/resposta perdida, autorização, conflitos, concorrência e rollback em
PostgreSQL descartável, preservando Dispatch/auditoria/snapshots/ledger/Payments.
Sem commit/push/merge/deploy; PostgreSQL descartável encerrado.

Regressão encontrada pela suíte completa intermediária:405 PASS/3FAIL. O aviso
legado alongado + bloco vazio empurraram Pronto para809.39px na viewport360×800
(limite original800). Correção funcional: aviso curto em span muted e configuração
renderizada somente quando possui conteúdo; sem alterar o limite da asserção.
A terceira falha usou expectativa anterior carregada durante discovery; arquivo
já esperava quatro linhas independentes, confirmado em nova execução.
22 testes focados posteriores PASS (23.5s), incluindo layouts360/390/430/768/1280/
1440, legado, conteúdo resumo/fila e ambas estações. Build final/tipos/diff PASS.

Validação final T10b:408 visuais completos PASS (8.3m),5 unitários PASS,6 Web/API
PostgreSQL PASS (43.3s),47 regressões PostgreSQL PASS (57.972s),22 regressões
focadas PASS, build final/tipos/diff PASS. Tolerâncias/baselines e exports originais
preservados. Logs em visual-artifacts/spec026/runtime/t10b-{unit,build-final,
regression,visual-complete,integration,postgres-tests}.log. Capturas fixture
production-configuration-{KITCHEN,BAR}-{360,390,430}.png e reais
production-configuration-real-{KITCHEN,BAR}-{360,390,430}.png em apps/web/test-results.
Capturas fixture/real360 inspecionadas; demais geradas com asserções independentes.
PG encerrado e runners Web/API encerrados. Não há npm test/lint Web definido;
executados scripts documentados test:production, test:visual, test:integration,
typecheck/build via CLI Node local; nenhum lint Web inventado.


### T10c.1 — comando de produção em lote (API local)
UX-04 permanece parcial: o resumo T10b não era um comando; a transição individual
não tinha journal/replay nem precondições de estado, quantidade e snapshot.
Entregue POST /production/batches/ com order.confirm, mesma sessão/Venue, 1–50
linhas inteiras verificáveis, configuração confirmada e estação compatíveis.
PREPARING aceita NEW/ACCEPTED; READY exige PREPARING. Todas as precondições são
validadas sob locks de sessão/Tabs/Items; conflito conserva rejeição canônica
sem aplicar linhas. Repetição exata devolve recibo original; outra intenção na
mesma chave conflita. Falha inesperada reverte estados/timestamps/Dispatch/audit.
Locks individuais passaram a Tab antes de Item, compatíveis com correções.
Journal de sessão usa NO KEY UPDATE para permitir FK de auditoria das correções.
Snapshots/preços/Payments/ledger não são alterados pelo lote. Legado permanece
individual; disponibilidade posterior não bloqueia trabalho já confirmado.

Arquivos de implementação: ordering/production.py, models.py, services.py,
serializers.py, views.py, migrations/0008_productionbatch.py e rodada_api/urls.py.
Testes novos: tests/test_production_batches.py (17 casos). Contratos 001/010/026
atualizados antes do código; ADR0018 registra journal, locking e rollback.

Evidência atual:96 testes PostgreSQL PASS (108.595s), incluindo 17 novos, Dispatch,
ordering, turno completo, customização/mix, ledger/Payments, corridas financeiras,
cancelamentos parciais e pedidos. APIClient prova contrato HTTP/autorização/fila;
não é jornada browser nem versão publicada. Corridas testam mesma chave,
payload alterado, sessões distintas, duas Tabs/seleção invertida e correção parcial.
Rollback falha no segundo Dispatch depois de criar o primeiro e conserva tudo.
43 regressões focadas também PASS (44.897s). A rodada financeira intermediária
teve 66 PASS/1 FAIL por fixture que às vezes selecionava item de uma unidade;
a fixture passou a selecionar explicitamente duas unidades para cancelamento parcial.
Rodada final conjunta corrigida PASS, sem relaxar asserções.

Django check/migration drift, compilação Python, tipos Web e diff PASS.
Ruff arquivos novos PASS. Lint dos arquivos existentes registra 12 avisos
(10 RUF012 e 2 I001), também presentes em HEAD ad5d64f; sem regras relaxadas.
Log:visual-artifacts/spec026/runtime/t10c-postgres-final.log.
Sem alteração de UI: visual/build Web e jornada Web/API mobile não executados
nesta slice. T10c.2 fica aberta para seleção/revisão explícita e persistência/
recuperação da intenção na sessão original. UX-23 não fechado: UI segue serializada.
Sem commit/push/merge/deploy ou mutação na demo/produção.


### T10c.2 — revisão e recuperação de lote na Web
Causa: o comando T10c.1 existia somente na API; o resumo de configuração não
oferecia seleção/revisão nem intenção recuperável no browser.
ProductionBoard agora oferece Selecionar preparo/prontos para grupos verificáveis
com mais de uma linha elegível. ActionDialog começa sem seleção, conserva
snapshot/configuração/destinos, valida estado/quantidade/fingerprint atuais e
requer confirmação humana. Seleção é de linhas inteiras, até 50; legado permanece
individual. sessionStorage conserva somente payload/chave/tempo e vínculo de
Venue/staff/session, sem credenciais ou nomes de cliente. Resposta perdida,5xx,
recibo inconsistente ou readback falho mantém pendência e bloqueia novas mutations.
Recuperação repete mesmo payload/chave; outra sessão não adota o lote, e outra
estação orienta retorno. Recibo validado e leitura atual são exigidos para liberar.
Resultado discrimina cada linha; rejeição integral exige nova seleção.

Correções encontradas nos testes: o botão de origem desativado retirava foco
antes do efeito do diálogo; ActionDialog aceita agora returnFocus explícito,
sem alterar o comportamento dos demais chamadores. Atualização realtime podia
substituir a leitura pós-confirmação; essa leitura tem prioridade durante o
readback, sem ignorar falha/aceitar recibo como substituto da fila atual.
Teste inicial de foco falhou mesmo com avanço de relógio; corrigido no produto.
Primeira integração também chamou rota inexistente de entrega no teste; corrigida
para dispatch/delivery, sem criar API fictícia. Rodada real final PASS.

Arquivos desta slice: components/production-board.tsx, action-dialog.tsx,
production-batch-review.tsx, lib/client/production-batch-intent.ts,
tests/visual/production-batch.spec.ts e production-batch-volume.spec.ts,
tests/integration/production-batch.spec.ts. Contratos/plan/acceptance 001/010/026
e design system atualizados antes do código; sem alteração da API nesta slice.

14 testes focados PASS (23.9s), incluindo mobile360/390/430 nas duas estações,
resposta perdida/reload, recibo inválido, leitura falha, rejeição, sessão diferente,
outra estação, armazenamento inválido/indisponível, revisão obsoleta e foco.
Teste separado de51 linhas/limite50/sem mutation e acessibilidade PASS (9.1s).
6 jornadas Web/API PostgreSQL PASS (50.1s), nas duas estações e360/390/430:
preparo→pronto, resposta realmente perdida após commit, reload e dupla tentativa,
mesmo comando/payload, indisponibilidade posterior, finanças/Payments/snapshots
preservados e duas entregas por pedido. API usada é real; interceptação descarta
apenas a primeira resposta depois de route.fetch concluir.
Readback direto na base exclusiva rodada_web_e2e:12 comandos,12 auditorias de
comando,24 transições,12 DispatchTasks,6 Payments; todos os lotes APPLIED.
49 testes PostgreSQL PASS (66.270s), incluindo17 de lote e regressões financeiras,
concorrência de recebimentos e cancelamentos. PostgreSQL descartável encerrado.
5 unitários de configuração, tipos e build final PASS. Capturas fixture e reais
360 inspecionadas;390/430 geradas e cobertas por asserções independentes.
Logs:visual-artifacts/spec026/runtime/t10c2-{focused-final,volume,integration-final,
postgres-tests,build-final}.log. Visual completo ainda em execução neste registro.
UX23 permanece aberto: a UI conserva bloqueio global enquanto houver lote
pendente; independência por escopo é a próxima slice T10d. Sem medição humana,
aparelho, piloto ou publicação comprovados. Sem commit/push/merge/deploy.

Validação final T10c.2:425 visuais completos PASS (8.9m), incluindo17 testes de
lote;1 teste de51 linhas/limite50 PASS separado, adicionado após discovery da suíte
completa. Sem código de produto alterado entre essas execuções. Tolerâncias,
baselines e exports preservados. Log:t10c2-visual-complete.log no runtime daSpec026.
Recibo inconsistente, storage adulterado,5xx e sessão revogada também PASS na suíte.
Tipos/build/diff revisados; nenhum contexto pessoal nos artefatos desta slice.
T10c concluída localmente; próximo recorte exato T10d/UX23 — concorrência da UI
por escopo protegido, mantendo replay/readback e bloqueio de conflito no mesmo
escopo. Gates amplos de T10/T14 seguem abertos.


## T10d.1 — independência individual verificável

Antes: uma ação individual usava a transição legada e bloqueava toda a estação.
Causa: lock de mutation e pendência únicos, sem recibo persistido por item.
Agora: itens com snapshot verificável usam comando canônico de uma linha,
journal por item/sessão antes do envio, lock por ID e readbacks serializados.
Resposta perdida de A não bloqueia B; replay conserva chave/payload mesmo em READY.
Erro de rede/leitura conserva intenção; rejeição terminal e readback removem apenas
essa linha. Sessão diferente/storage adulterado ou falho bloqueiam envio.
Contratos001/010/026,ADR0018,design system e testes atualizados; API existente
reutilizada. Lote/legado/disponibilidade/QuickCatalog mantêm barreiras.
438 visuais completos PASS (9.4m),29 focados,6 Web/API PostgreSQL PASS (1.0m),
49 PostgreSQL PASS (70.813s),5 unitários,tipos/build/diff PASS. Sem baseline,
tolerância ou export alterados. Capturas fixture/reais360 inspecionadas;
360/390/430 testados nas duas estações. Base exclusiva rodada_web_e2e:
18 comandos,18 auditorias de comando,18 transições de comando +6 de setup,
12 entregas,6 Payments. Replay command_id,ledger/Payments/snapshots preservados.
Logs:visual-artifacts/spec026/runtime/t10d1-{focused,integration,postgres-tests,
readback,build,visual}.log. Não existe script Web test/lint genérico.
PostgreSQL descartável encerrado; sem commit/push/merge/deploy. UX23 parcial;
próximo T10d.2: investigar contratos de lote/legado/disponibilidade para a menor
independência adicional segura. Aparelho,piloto,tempo humano e publicação abertos.

## T10d.2 — item independente de lote persistido

Base local: main/ad5d64f; alterações anteriores e worktrees preservados.
Causa: ProductionBoard tratava qualquer lote pendente como bloqueio global,
mesmo para IDs fora da seleção. O comando canônico já protege transações,
precondições, autoria e replay; esse bloqueio da UI era maior que seu escopo.
Agora locksItem protege os IDs selecionados e falha fechado se o envelope mudar.
Revisão/pré-persistência permanecem globais. Item independente valida também
Venue/staff/session do lote armazenado antes do POST; journals continuam separados.
Recuperar um item não remove lote, e recuperar lote não remove outro item.
Legado,disponibilidade,QuickCatalog e abertura de outro lote continuam protegidos.
ProductAvailabilityView ainda incrementa versão/audita cada POST, sem contrato
idempotente equivalente: liberar esse escopo fica fora desta entrega.
Contratos001/010/026,ADR0018 e design system atualizados; API não alterada.
38 focados PASS (51.1s),6 Web/API PostgreSQL PASS (1.1m),49 PostgreSQL PASS
(68.929s),5 unitários,tipos/build final PASS. Base exclusiva rodada_web_e2e:
18 comandos/18 auditorias/30 transições de comando/12 entregas/6 Payments.
Replay manteve command_id e payload; snapshots/ledger/Payments verificados iguais.
Capturas fixture360 das duas estações inspecionadas;360/390/430 testados.
Logs:visual-artifacts/spec026/runtime/t10d2-{focused,integration,postgres-tests,
readback,build-final}.log. Visual final ainda em execução neste registro;
execução inicial interrompida para corrigir texto do bloqueio, sem baseline novo.
PostgreSQL descartável encerrado. Sem commit/push/merge/deploy. Aparelho,piloto,
tempo humano e publicação não verificados. Próxima T10d.3: investigar disponibilidade
por produto/versionamento/recuperação antes de liberar esse escopo.

Validação final T10d.2:447 visuais completos PASS (9.2m), sem baseline/tolerância
ou export novos; log t10d2-visual-final.log. Mensagem final explica liberação das
linhas do lote; captura final360 revisada. Critérios T10d.2 comprovados marcados,
T10d/UX23 permanecem parciais. Diff revisado e sem contexto pessoal nos artefatos.

## T10d.3 — disponibilidade idempotente/versionada na API

Causa: POST legado incrementa versão e gera nova auditoria ao repetir uma ação,
sem distinguir resposta perdida de comando novo. AvailabilityCommand e migração
catalog0007 conservam recibo terminal por Venue/sessão/chave e fingerprint de
produto/state/versão/motivo. Endpoint opt-in valida chave+expected_version juntos;
replay conserva recibo, versão obsoleta persiste rejeição, payload alterado conflita.
No-op não inventa mudança de estado/versão/timestamp. Sessão/capability revalidadas;
lock NO KEY UPDATE na sessão, depois disponibilidade. Falha de auditoria reverte
tudo. Catálogo agora expõe availability_version. Legacy POST preservado.
Itens/snapshots/Product.active/ledger/Payments intactos; UI não alterada.
Specs001/026 atualizadas antes do código; ADR0019 registra decisão durável.
65 testes Django PostgreSQL PASS (71.667s), incluindo11 novos (4 de concorrência),
mais16 Quick Catalog pytest PostgreSQL PASS (24.68s), rodados sequencialmente.
Execuções iniciais registraram falta de pytest e disputa da base de teste;
versões declaradas instaladas e runners finais separados resolveram o ambiente.
Check/migration drift/compilação Python/diff PASS; Ruff dos3 arquivos novos PASS.
19 avisos em models/views/serializers também presentes em HEAD ad5d64f.
Logs:visual-artifacts/spec026/runtime/t10d3-{tests-final,pytest-final,lint-new,
lint-existing,lint-baseline}.log. Sem UI nova: visual/mobile browser, tipos/build
Web não executados. PostgreSQL descartável encerrado; sem commit/push/merge/deploy.
UX23/T10d continuam parciais; próxima T10d.4: intenção Web por produto, versão
capturada, replay/readback e lock por produto antes de permitir disponibilidade
independente. Aparelho,tempo humano,piloto e publicação não verificados.

## T10d.4 — disponibilidade Web recuperável e independente

Causa: ProductionBoard ainda enviava disponibilidade pelo POST legado e aplicava
inert às ferramentas durante qualquer pendência de produção. Agora catálogo
versionado usa journal por produto na mesma aba/sessão, persistido antes do envio,
com versão capturada, chave/estado originais e vínculo Venue/staff/session.
Recibo terminal validado e readback serializado precedem remoção; resposta perdida
ou falha de leitura conserva retry inclusive após reload e produto fora da fila.
Produtos distintos e itens verificáveis podem operar em paralelo; lote/item
pendente conserva seu journal. Revisão, legado, modificadores, QuickCatalog e novo
lote durante pendência mantêm barreiras. Sem versão, caminho legado conservado.
Storage inválido/adulterado/falho e sessão divergente não adotam intenção.
Specs001/026, ADR0019 e design system atualizados; sem mudança API nesta slice.

34 focados PASS (43.4s), antes de adicionar5 cenários de coexistência/no-op;
os18 novos cenários já PASS na execução visual completa ainda em andamento.
6 Web/API PostgreSQL PASS (41.8s),60 Django PostgreSQL PASS (63.333s),5 unitários,
tipos/build final PASS. Banco descartável novo/exclusivo na porta55477:
12 comandos APPLIED,12 auditorias de comando,12 mudanças; versões2 nos12 produtos,
6 ProductionBatches e6 Payments. Retry conserva command_id/recibo/payload; jornadas
verificam snapshots/finanças iguais antes/depois e item confirmado ainda produzível.
Captura fixture360 inspecionada;360/390/430 cobertos nas duas estações.
Logs:visual-artifacts/spec026/runtime/t10d4-{focused-final,integration,
postgres-tests,readback,build-final,visual-complete}.log. Primeiro build no sandbox
falhou com acesso negado do compilador Windows; execução autorizada PASS.
Sem baseline/tolerância/export alterados; sem commit/push/merge/deploy.
Visual completo final e encerramento do PostgreSQL ainda pendentes neste registro.
UX23/T10d amplo e gates aparelho/tempo humano/piloto/publicação continuam abertos.

Execução visual inicial:464 PASS e1 falha em Batch protection server. O teste
verificava calls imediatamente após encontrar a mensagem da tentativa anterior,
antes de terminar auth/POST do retry. Corrigida somente a sincronização com
expect.poll, conservando a exigência de dois envios e storage idêntico.
Cinco repetições PASS (10.5s); suíte completa final em execução sem mudança de
produto. Log:t10d4-batch-server-repeat.log e t10d4-visual-final.log.
Captura real BAR360 também inspecionada; PostgreSQL descartável encerrado.

Validação final T10d.4:465 visuais completos PASS (9.1m), sem baseline/tolerância/
export novos. Log:t10d4-visual-final.log. Tipos/build,6 Web/API PostgreSQL,
60 Django PostgreSQL,5 unitários e diff PASS; sem script Web lint/test genérico.
Critérios locais T10d.4 marcados. Main/ad5d64f e alterações anteriores preservados;
nenhum contexto pessoal incorporado à slice. Sem commit/push/merge/deploy.
Próxima tarefa do plano T11 (entregas, pico e recuperação Android); critérios
amplos UX23/T10d/T14 e aparelho/tempo humano/piloto/publicação continuam abertos.

### T11a/T11b — recuperação e filas Android (2026-10-13)
Pendências locais exibem estado, data e resumo do registro original. Abrir contexto
consulta somente a comanda canônica para pedido/pagamento/preço/estrutura, ou a
fila e task exata de entrega; não confirma nem substitui payload, chave ou sessão.
Troca de sessão bloqueia retomada; consulta suspensa revalida a sessão antes de
publicar contexto. Retry de entrega reutiliza a intenção existente da mesma task.
Prontos é o filtro inicial, inclusive no pico; Chamadas e Pendências são filtros
explícitos. Contagem desconhecida usa —. Pendências não ocupam o topo fixo.
Entrega organiza dados e botão verticalmente para fonte ampliada.
Correção/estorno/caixa sem contexto canônico continuam revisão explícita.
UX27: auditoria do backend encontrou conclusão manual; inferência passiva não
foi demonstrada. Preservada confirmação manual até evidência de source/confidence/
provenance e correção por exceção. T11 ampla permanece aberta.

Validação final T11a/T11b: 71 testes unitários Android PASS; 24 verificações
Compose PASS (4 cenários x 360/390/430dp x fontScale 1.0/2.0); 1 jornada
Android/API real PASS após recompilação final; 40 regressões Django PostgreSQL
PASS. Build/APKs/lint PASS (0 erros, 8 warnings, 2 hints); runner Python compila.
Readback do banco exclusivo porta55478: 0 Orders, 0 Payments após navegação.
Captura final360/f200 inspecionada: filtros legíveis em coluna. Primeira matriz
falhou em360/f200 por produto comprimido; corrigidos layout de entrega e filtros,
com nova matriz completa PASS. Não reduzidas asserções de envio/contexto.
Logs em visual-artifacts/spec026/runtime: t11-build-final-accessible.log,
t11-final-{360,390,430}-{1.0,2.0}.log, t11-real-final.log,
t11-postgres-tests.log, t11-readback-final.log; capturas t11-final-evidence/.
Diff do recorte revisado; alterações anteriores preservadas, sem dados pessoais.
API, emulador e PostgreSQL exclusivos desta validação encerrados. Sem commit,
push, merge ou deploy. Não comprova ergonomia física, tempos humanos, inferência
passiva ou piloto. T11a restante e T11/UX26/27 amplos permanecem abertos.

### T11c — conferência do turno original de caixa (2026-10-13)
Pendências CashMovement/CashClose oferecem leitura do shiftId original, inclusive
encerrado. CashShiftViewModel mantém contexto de conferência separado de state
operacional; GET não altera ponto selecionado, turno ativo, payload, chave ou
registro criptografado. Após GET revalida sessão, igualdade do envelope e shift ID.
Falha, turno inexistente, ID divergente e outra sessão não exibem snapshot.
Tela sobreposta mantém fila/filtro/posição anterior; retornar invalida leitura em
andamento. Oferece somente retorno/atualizar consulta, sem comandos financeiros.
Mostra comando original e movimentos canônicos; não infere sucesso/falha por
valor, motivo ou ausência do movimento. Reconciliação gerencial segue necessária.

Validação final T11c: 72 unitários Android PASS; 18 Compose PASS (3 cenários x
360/390/430dp x fontScale1.0/2.0), com retorno/consulta44dp, sem ações financeiras,
loading/falha; 1 jornada Android/API PostgreSQL PASS com turno encerrado original,
outro turno ativo preservado, envelopes intactos, ID divergente/inexistente,
troca de sessão durante GET e rejeição de adoção por novo login. As snapshots
originais/atuais permanecem idênticas após navegação; não marcou intenção concluída.
14 regressões Django caixa/autorização PostgreSQL PASS (8.137s). Build/APKs/lint
final PASS (0 erros,8 warnings,2 hints), diff do recorte PASS. Readback exclusivo:
0 Orders,0 Payments,0 SUPPLY/WITHDRAWAL/CORRECTION enviados pelas pendências;
aberturas/contagens/fechamentos usados apenas para montar fixtures de turnos.
Captura360/f200 final inspecionada; estado guardado claramente distinto da leitura.
Logs visual-artifacts/spec026/runtime/t11c-build-validated.log,
t11c-final-{360,390,430}-{1.0,2.0}.log, t11c-real-validated.log,
t11c-postgres-tests.log, t11c-readback-final.log; capturas t11c-final-evidence/.
Primeira inicialização do cluster usou porta padrão; cluster exclusivo reiniciado
com porta55478 explícita antes dos testes. API/emulador/PostgreSQL exclusivos
encerrados; alterações anteriores preservadas; sem dados pessoais, commit/push/
merge/deploy. Arquivos do recorte: CashRecoveryScreen.kt, CashShiftViewModel.kt,
AttendanceScreen.kt, RecoveryPresentation.kt, RecoveryPresentationTest.kt,
CashRecoveryApiTest.kt, CashRecoveryScreenTest.kt; docs026/012/014, design e README
Android atualizados. Não comprova ergonomia física nem tempos humanos. Próximo
recorte: consulta canônica de correção/estorno; T11/UX26 amplo, UX27 inferência,
aparelho e piloto seguem abertos.

T11d em validação (checkpoint posterior à T11c): adiciona API modules/corrections/recovery_views.py, tests/test_recovery_context.py e rotas em rodada_api/urls.py; Android ExceptionalRecovery.kt/ExceptionalRecoveryScreen.kt, ExceptionalRecoveryTest.kt, ExceptionalRecoveryApiTest.kt, ExceptionalRecoveryScreenTest.kt e extensões em OperationsRepository/OperationsViewModel/RecoveryPresentation/RecoveryPresentationTest/AttendanceScreen. Spec/plan026 atualizados antes do código. Não incorporar como checkpoint T11c; evidências finais serão registradas separadamente.

### T11d — conferência de correção e estorno (2026-10-13)
Três GETs canônicos resolvem item/Tab, payment/Tab e correction/item/payment/Tab.
OrderItem requer order.correct; payment/correction requerem refund.create.
Settlement exige payment da mesma Tab/Venue. Foreign/missing retornam404 indistintos;
query inválida400; capability403; sem autenticação401; POST405. Leitura não exige
reauth e não concede mutations; reauth e autorização financeira permanecem.
Android valida IDs conhecidos do envelope, alvo na Tab, sessão e registro após I/O.
Conferência separada não altera cart/seleção nem reenvia operação; alvo cancelado,
payment estornado, correction aplicada e Tab encerrada continuam investigáveis.
Registro/chave/payload preservados; nova sessão não adota e erro não publica contexto.
Retorno conserva fila/filtro; estado guardado e estado consultado são distintos.
Rótulos REFUNDED/PARTIALLY_REFUNDED traduzidos somente na apresentação compartilhada.
Ausência de correction nas pendências não comprova falha; estado do alvo não prova
resultado do envelope. Reconciliação gerencial e critérios de inferência continuam.

Validação final T11d: 76 unitários Android PASS;12 Compose PASS (2 cenários x
360/390/430dp x fontScale1.0/2.0),7 Compose adjacentes de filas/caixa PASS;
1 jornada Android/API PostgreSQL PASS na versão final (5.692s), repetida durante
validação com3 fixtures independentes. Consulta item cancelado, payment estornado,
correction aplicada e Tab encerrada; store/envelope e snapshots financeiros iguais
antes/depois, alvo inexistente e nova sessão bloqueados, sem marcar confirmação.
71 Django PostgreSQL PASS (124.110s), incluindo6 novos testes de resolução/read-only,
capability/autenticação, foreign/missing, cross-Tab, query inválida e estado histórico.
Build/APKs/lint PASS (0 erros,8 warnings,2 hints). Readback do banco exclusivo:
3 Orders,3 Payments,3 OrderCorrections,3 Refunds, todos fixtures das3 jornadas;
nenhuma nova operação em consulta, verificado pelos snapshots antes/depois.
Captura final360/f200 inspecionada, rótulo Estornado corrigido só na UI. Sem baseline,
tolerância, migration ou regra financeira nova; Web/PWA não recebeu UI neste recorte.
Primeiros testes locais falharam por fixtures sem confirmed_at e Product duplicado;
fixtures corrigidas. Primeira matriz teve falhas em360/390 com fonte ampliada por
asserções sobre nós fora da composição/viewport; rolagem específica adicionada,
mantendo visibilidade/conteúdo e proibição de replay; nova matriz completa PASS.
Logs visual-artifacts/spec026/runtime/t11d-build-final-labels.log,
t11d-final-{360,390,430}-{1.0,2.0}.log, t11d-adjacent-final.log,
t11d-real-validated.log, t11d-postgres-tests.log, t11d-readback.log;
capturas t11d-final-labels-evidence/. Diff do recorte revisado, alterações anteriores
preservadas e sem contexto pessoal. API/emulador/PostgreSQL exclusivos encerrados.
Sem commit/push/merge/deploy. Arquivos finais T11d: API recovery_views.py,
test_recovery_context.py e rodada_api/urls.py; Android ExceptionalRecovery.kt,
ExceptionalRecoveryScreen.kt, ExceptionalRecoveryTest.kt, ExceptionalRecoveryApiTest.kt,
ExceptionalRecoveryScreenTest.kt, OperationsRepository.kt, OperationsViewModel.kt,
RecoveryPresentation.kt, RecoveryPresentationTest.kt e AttendanceScreen.kt;
docs026/006/014/017, design e README Android. Gates UX26/G1 integrado, inferência
UX27 com source/confidence/provenance, aparelho/tempos humanos e piloto continuam.

## T12a — Validação local concluída
Recorte: motivo por proposta e rótulos humanos em fechamento/estornos. Arquivos:
apps/web/app/manage/daily-close/page.tsx, app/refunds/page.tsx,
lib/presentation-labels.ts, tests/visual/daily-close.spec.ts e refund-labels.spec.ts;
documentos 026/012/006/007. Preservadas alterações anteriores no checkout.
Build/typecheck PASS; 7 testes focados PASS, incluindo 3 larguras móveis, PIN,
cancelamento, autoaprovação proibida e rótulos desconhecidos. Capturas t12a-decisions-
{360,390,430}.png e t12a-refund-labels-{360,390,430}.png; 360 inspecionadas visualmente.
Logs em visual-artifacts/spec026/runtime/t12a-{build,types,focused,visual-full}.log.
Suíte visual completa: 471 PASS, sem skips/falhas ou alteração de baselines.
Build e typecheck PASS; diff do recorte revisado, sem contexto pessoal.
Servidores locais de validação encerrados pelo runner. Sem commit/push/deploy. Deep links, histórico de comandas encerradas,
reauth contextual de estorno, projeção gerencial e bloqueios acionáveis permanecem.

## T12b.1 — Validação local concluída
Recorte de UX09/30: contexto exato de turno de caixa via alerta/bloqueio de fechamento.
Arquivos: apps/web/app/cash/page.tsx, manage/alerts/[id]/page.tsx,
manage/daily-close/page.tsx, tests/visual/cash-context.spec.ts,
management-alerts.spec.ts e daily-close.spec.ts; documentos026/012/018.
Build/typecheck PASS, 21 testes focados PASS. Capturas t12b1-cash-{360,390,430}.png;
360 inspecionada: turno antigo selecionado, foco/retorno e revisão manual preservada.
Primeira execução teve 4 falhas de locator genérico por role=alert do anúncio Next;
locator do erro do produto especificado, nova execução completa focada PASS.
Logs visual-artifacts/spec026/runtime/t12b1-build.log, t12b1-types.log,
t12b1-focused-final.log, t12b1-visual-full.log. Regressão completa: 482 testes PASS em 10,9 minutos, sem skips/falhas ou alteração de baselines.
Diff do recorte revisado e sem contexto pessoal; servidores encerrados pelo runner.
API existente preservada: CashShiftDetailView exige payment.collect e usa Venue do
ator em cash_close_preview e CashShift. Fixtures não equivalem a prova real integrada.
Outros alvos/deep links, histórico de pagamentos/comandas elegíveis, PIN contextual
de estorno, projeção gerencial e G1 continuam pendentes. Sem commit/push/deploy.

## T12b.2 — Validação local concluída
Recorte PAYMENT: página read-only apps/web/app/manage/payments/[id]/page.tsx;
link manage/alerts/[id]/page.tsx; tests/visual/payment-context.spec.ts e
management-alerts.spec.ts; documentos026/006/018. Resolver protegido existente
preserva refund.create e Venue; sem mudança financeira/backend/migration.
Build/typecheck PASS, 19 testes focados PASS. Conferência encontra pagamento
original em comanda encerrada fora da lista, preserva intenção financeira guardada,
rejeita IDs/permissão/sessão divergentes e elimina leitura após acesso negado.
Capturas t12b2-payment-{360,390,430}.png; 360 inspecionada visualmente.
Logs visual-artifacts/spec026/runtime/t12b2-{build,types,focused,visual-full}.log.
Suíte visual completa: 494 PASS em 11,8 minutos, sem skips/falhas ou mudança de baselines.
Diff revisado, sem contexto pessoal; servidores locais encerrados pelo runner.
Fixtures não equivalem a integração real API/PG.
Item/correction, retry/edição de estorno contextual, projeção gerencial e G1 continuam.
Sem commit/push/deploy; alterações anteriores preservadas.

## T12b.3 — Validação local concluída
Arquivos: components/exceptional-context.tsx; app/manage/items/[id]/page.tsx,
manage/corrections/[id]/page.tsx, manage/alerts/[id]/page.tsx e refunds/page.tsx;
tests/visual/exceptional-context.spec.ts, management-alerts.spec.ts; docs026/017/018.
Build final/typecheck PASS; 37 testes focados finais PASS, incluindo regressão de
estorno e preservação de intenção guardada. Capturas t12b3-{items,corrections}-
{360,390,430}.png; correção360 inspecionada visualmente. Resolver/capability/Venue
existentes preservados, sem backend/migration/regra financeira nova.
Primeira fixture do link de estorno omitia refunds obrigatório e causava erro da
página de teste; histórico vazio adicionado à fixture conforme contrato. Execução
completa inicial interrompida; focused-final PASS antes de nova execução completa.
Logs visual-artifacts/spec026/runtime/t12b3-build-final.log, t12b3-types-final.log,
t12b3-focused-final.log, t12b3-visual-final.log. Visual completo final: 510 PASS, sem skips/falhas ou mudança de baselines.
Diff do recorte revisado e sem contexto pessoal; servidores encerrados pelo runner.
Fixtures não equivalem a prova integrada real API/PG. Correções sem pagamento,
telas de decisão/PIN contextual, projeção gerencial e G1 continuam pendentes.
Sem commit/push/deploy; alterações anteriores preservadas.
