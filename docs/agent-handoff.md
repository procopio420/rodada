# Handoff — Atendimento Web/API/Android

Registro de 2026-10-14. Objetivo: publicar todas as alterações locais autorizadas
na branch `codex/ux-teste-mobile`, abrir PR e documentar o trabalho. Sem merge,
deploy ou operação em produção autorizados.

## Estado antes da publicação

- Base local `47043184408c090ddae33df17d4d72010603f764`; `origin/main` consultada
  em `b63b6111d66c640e8d4fde8ab2042743c9083eee`, com commits adicionais. Não foi
  feita integração da main; o PR deve permanecer rascunho até conciliação.
- Branch remota de trabalho não existia na consulta inicial. Sem merge/rebase
  em andamento observado; arquivos locais permanecem preservados.
- Usuário autorizou publicar Web, API, Android e documentação. `.worktrees/`,
  APKs, dados, logs e artefatos locais ignorados ficam fora do commit.
- Web: entrada unificada, popup persistente por Tab, catálogo/revisão/conta,
  draft/configurações, busca/filtro/grade e histórico. Contrato na Spec029.
- API/Web: MOVE_LOCATION aceita mesa AVAILABLE por table_id, inicia ocupação e
  atribui responsabilidade na transação, exige capabilities e mantém replay.
  Testes novos cobrem replay, indisponível, outro Venue e versão divergente.
- Android: fluxo Compose equivalente, drafts em memória por Tab/sessão, Back,
  histórico e recuperação excepcional segura; ASGI documentado para SSE.
- Arquivos: `apps/api/modules/tab_operations/`, `apps/api/tests/test_tab_operations.py`,
  `apps/web/app/attendance/`, gateway/estilos/componentes/testes Web alterados,
  `apps/attendance-android/`, `docs/design/system.md`, Spec027 e Spec029.

## Evidência e limites

Android: build/JVM/lint PASS, 88 testes JVM, 34 execuções Compose em seis
combinações 360/390/430dp x fontes1/2, A/B/A real somente leitura PASS e Back real
PASS. Manifest e logs locais em `visual-artifacts/android-native-port/final/`.
Revisão independente Android: NO_FINDINGS_WITH_GAPS, sem aprovação GitHub.
Ver `specs/029-attendance-mobile-design/android-evidence.md`.

Web: documentação histórica da branch registra build/tipos e 33 jornadas focadas;
não reexecutadas na publicação. Suíte legada integral e comparação global ainda
pendentes. Ver `specs/029-attendance-mobile-design/acceptance.md` e `evidence.md`.
API nova e pacote integrado não tiveram execução/revisão independente nesta etapa:
REVIEW_BLOCKED para recomendar merge do conjunto R3. CI do novo commit ainda precisa
ser consultada. Nenhum resultado Android prova integração financeira/produção.

Última ação concluída: revisão dos arquivos, fetch e identificação do escopo
completo. Próximo passo: revisar/stage explícito, commit, push sem force e criar
PR draft; conferir SHA remoto e anexar o PR à conversa. Registrar URL/SHA no
resultado da publicação. Se a publicação for interrompida, conferir estado real
antes de repetir commit ou criar PR duplicado.

## PROMPT PARA O PRÓXIMO AGENTE

Continue a publicação/revisão do Atendimento Web/API/Android do repositório Rodada
na branch codex/ux-teste-mobile. O usuário autorizou commit/push de todas as
alterações Web, API, Android e documentação e a criação de PR; não autorizou merge
ou deploy. Verifique CODEX_HOME, leia o AGENTS global/override efetivo, AGENTS local,
docs/agents/PROCEDURES.md, este checkpoint, specs/029-attendance-mobile-design e os
contratos adjacentes Spec014/Spec027. Descubra o caminho real com git rev-parse
--show-toplevel e confira arquivos reais, branch, HEAD, status, upstream e PRs.
Base testada: 47043184408c090ddae33df17d4d72010603f764; origin/main foi consultada em
b63b6111d66c640e8d4fde8ab2042743c9083eee, sem integrar. Não sobrescreva alterações
ou worktrees e não repita trabalho concluído. Android está implementado/testado
conforme android-evidence.md (88 JVM, 34 Compose, A/B/A real e Back). Web/API locais
também entram na publicação por autorização explícita, mas sua validação integrada
e revisão R3 completa estão pendentes. Confira se commit/push/PR já terminaram;
se não, retome o primeiro passo pendente sem force-push e sem incluir .worktrees,
logs, bancos, APKs, credenciais ou contexto pessoal. Mantenha PR draft; depois
concilie main semanticamente, execute gates proporcionais Web/API/Android e revisão
independente R3 antes de recomendar integração. Registre fatos, erros, resultados,
pendências e a próxima ação; não trate intenção/spec ou CI como homologação.

## Publicação concluída

- Implementação/documentação publicadas no commit
  `26ca193ba0eb688211a96b18ff5fb61d295a901d`; SHA remoto confirmado.
- PR draft: https://github.com/procopio420/rodada/pull/169, criado e anexado à conversa.
  GitHub indicou `mergeable=false` contra main; resolver divergências antes de integração.
- Restou somente `.worktrees/` não rastreada, preservada deliberadamente. Sem merge,
  rebase, reset, force-push ou deploy. Esta atualização documental é commit posterior;
  consultar `git rev-parse HEAD` para o topo atual da branch.

### PROMPT PARA O PRÓXIMO AGENTE — após publicação

Continue a revisão do PR draft https://github.com/procopio420/rodada/pull/169,
branch codex/ux-teste-mobile, repositório Rodada. O usuário pediu publicar Web,
API, Android e documentação: isso foi concluído; implementação em
26ca193ba0eb688211a96b18ff5fb61d295a901d, com atualização documental posterior.
Não repita commit/push/criação do PR. Verifique CODEX_HOME e leia AGENTS global
ou override, regras locais, docs/agents/PROCEDURES.md, este checkpoint e Spec029.
Confira o diretório real com git rev-parse --show-toplevel, HEAD/status/upstream,
arquivos e PR remoto. Preserve .worktrees/ e trabalho concorrente. Android passou
build/lint/88 JVM, 34 Compose em 360/390/430dp e fontes1/2, A/B/A real somente
leitura e Back nativo; revisão independente NO_FINDINGS_WITH_GAPS. Evidências em
specs/029-attendance-mobile-design/android-evidence.md. Web tem evidência histórica
focada, sem reexecução nesta publicação; a API MOVE_LOCATION para mesa AVAILABLE
e o pacote completo ainda exigem gates e revisão R3 (REVIEW_BLOCKED para merge).
Primeiro passo: consultar estado/CI do PR169 e confirmar conflitos com a main,
que estava em b63b6111d66c640e8d4fde8ab2042743c9083eee. Planejar conciliação
semântica, especialmente repetição de rodada, preservando todas as alterações;
não executar merge de main nem deploy sem autorização aplicável. Depois executar
gates proporcionais API/PostgreSQL/Web/Android e revisão independente do conjunto.
Não alegar paridade global, provider/dispositivo, operação real ou produção.
Atualize este registro por etapa com resultados e próximos passos concretos.

## Retomada local para teste — 2026-10-15

Branch `codex/ux-teste-mobile`, HEAD `54c57808cec0098be2934faa964dd6dd9cd5b41d`.
API ASGI8000, dispatcher, Web3000 e cluster local PostgreSQL55460/banco
`rodada_ux_review` retomados sem reset/seed/migration. Receita e evidência em
`docs/development/attendance-local-test-2026-10-15.md`; verificar listeners e
processos antes de reiniciar. Não usar o cluster frontend-pilot-postgres para
esta continuidade. Android emulator-5556 usa reverse8000 → host8000.

APK instalado e seis fontes centrais iguais ao manifest final anterior.
Comparação real executou mesma mesa/comanda, catálogo, revisão, Conta e retorno;
rascunho de 400 centavos não alterou saldo canônico zero. Item local de ensaio
removido sem confirmar pedido. `NativeDraftReadbackTest` opt-in real: 1 PASS,
sem skip, pedidos canônicos antes/depois iguais. Android ONLINE verificado.

Port equivalente no fluxo principal, **não idêntico à Web**: Android não possui
os mesmos filtros/mapeamento de categorias nem assets ProductIcon publicados;
hierarquia visual difere. Conta Web permanece explicitamente sem pagamentos;
Android mantém operações existentes. GO somente para teste humano local;
paridade global/produção não aprovada. Nenhum código de produto alterado nesta
conferência; `apps/web/next-env.d.ts` foi atualizado automaticamente pelo Next dev.
Sem build/suítes completas novas, commit/push/merge/deploy. Próximo responsável:
operador testar o ambiente aberto; para corrigir paridade, detalhar primeiro
aceite na Spec029 e preservar recovery/permissões/drafts.

## Ajuste visual dos filtros Web — 2026-10-15

Mesmo HEAD/base da retomada acima, com diff local. Pedido: remover faixa lateral
nos filtros de mesas. Spec029 atualizada antes do CSS. mobile-design.css usa
2 colunas mobile/3 desktop, quebra de rotulos e alvos preservados. Teste existente
attendance-mobile-design.spec.ts verifica overflow/rotulos/alvos nas 4 larguras.
Build/TypeScript PASS; test:visual focado 15 PASS; navegador real confirmou grade
e selecao/vazio/retorno. Suite integral nao reexecutada. Detalhes em acceptance.md
da Spec029. Web3000 reiniciada para carregar CSS; API/banco/emulador preservados.
Sem commit/push/merge/deploy. Proximo responsavel: operador testar Web aberta.

### Decisao posterior: remover filtros Web

Operador pediu retirar a grade de filtros. Removidos UI, estado e CSS; busca e
estados das mesas preservados. Spec029/aceite e teste ajustados ao novo contrato.
Build/TypeScript e 15 testes visuais focados PASS; navegador confirmado sem
filtros. Esta decisao substitui o ajuste de grade anterior. Sem alterar Android,
banco ou API; sem commit/push/merge/deploy.

### Mesa Web em popup — 2026-10-15

Spec029 atualizada antes do codigo. AttendanceWeb usa ActionDialog para opcoes
da mesa, sem expansao da grade. Acoes e filhos preservados; erros na janela,
fechamento bloqueado durante operacoes existentes; retorno/foco validados.
CSS e attendance-mobile-design.spec.ts ajustados. Build/TypeScript PASS,
16 testes visuais focados PASS; suite integral nao reexecutada. Web3000 atualizada;
API/banco/Android preservados. Sem commit/push/merge/deploy. Proximo: operador
testar o popup e o fluxo Mesa -> Comanda -> Voltar. Detalhes na Spec029/acceptance.

### Clique fora do popup de mesa

Solicitacao atendida via dismissOnBackdrop opt-in no ActionDialog e somente mesa.
Preserva locked; clique interno/arraste iniciado dentro nao fecha. Spec029, teste
e aceite atualizados. Build/TypeScript e 16 testes focados PASS (20,6s).
Web3000 atualizada; demais servicos preservados. Sem publicacao.

## Android: tela de mesas alinhada com Web — 2026-10-15

Mesmo HEAD/base anterior + diff local, sem commit. Alterados TablesScreen,
AttendanceHeader/Navigation, posicionamento da navegacao em AttendanceScreen e
testes de apresentacao/fluxo. Spec029/design system/README sincronizados.
Filtros removidos, navegacao no topo, Venue canonico, painel e cartoes com faixa
semantica por estado; opcoes da mesa em Dialog nativo. Callbacks/VM/API/recovery
preservados. Build/JVM/lint PASS (89 JVM, zero erros lint); 45 execucoes Compose
em 360/390/430 x fontes1/2 PASS; A/B/A real somente leitura 1 PASS, sem mutacoes.
App instalado com dados preservados, ONLINE, popup/Back reais conferidos.
Emulador size/density/animacoes restaurados. Evidencia e limites no android-evidence.md
da Spec029. GO local da tela de mesas; sem paridade global/catalogo/ProductIcon,
homologacao fisica/producao ou suite Web integral. Sem push/merge/deploy.
Proximo responsavel: operador testar o Android aberto e comparar com a Web.

### Android bloqueado por intencao de mesa livre — corrigido

Causa: allowlist HTTP omitia service/open-tab, apesar de openFirstTableTab usar
essa rota. Intencao era salva e require local falhava antes do HTTP. Adicionada
somente a rota na regex, regressao TCP real reproduz FAIL antes/PASS depois;
build/lint e90JVM PASS. Revisao independente R3 /root/review_table_route:
NO_FINDINGS_WITH_GAPS, sem aprovacao GitHub. APK instalado preservando storage.
Apos autorizacao explicita do operador, recuperada intencao original pelo botao
existente; uma Tab/ocupacao/comando adicionados, nova Tab OPEN com zero pedidos.
UI ONLINE e Mesa2 clicavel, aviso pendente removido por sucesso canônico.
Sem limpeza de fila, nova chave, pagamentos, pedidos, reset ou publicacao.
Evidencia detalhada em Spec029/android-evidence.md. Proximo: operador testar.

## Limpeza direta Web/Android — 2026-10-15

Usuario solicitou menos cliques: liberar -> lista DIRTY; tocar -> apenas Concluir
limpeza; concluir -> lista AVAILABLE. API services.complete_cleaning aceita DIRTY
liberada ou CLEANING legado, preserva lock/atomic/geracao/audit e nao inventa inicio.
Contratos Spec004/027/029 atualizados; README Android e modelo de dominio tambem.
TablesScreen fecha por status canonico; VM nao cria modal de sucesso nessas2acoes.
Web fecha somente apos readback esperado, falha503 mantem contexto; foco delegado
somente a ActionDialog. Arquivos/testes em diff local, HEAD54c57808 inalterado.
Gates: API18 PostgreSQL+check+migrationsdryrun PASS; Webbuild+18focados PASS;
Androidbuild/90JVM/lint PASS;15Compose nas combinacoes registradas em Spec029/aceite.
Revisor independente /root/review_direct_cleaning: NO_FINDINGS_WITH_GAPS apos P2
corrigido. API8000/Web3000 reiniciadas com banco local preservado; APK instalado,
emulador restaurado e ONLINE. Nenhuma mesa da demonstracao foi alterada.
Sem publicacao. Proximo: operador testar Liberar -> Concluir limpeza no ambiente.

## Nome obrigatorio na abertura staff — 2026-10-15

Spec001/027/029 atualizadas. Android TablesScreen/OpenTabDialog sempre mostram
Nome ou apelido, max120, desabilitam vazio/espacos, trim envio. Web contextual e
OrderWorkspace iguais. API TabCreateSerializer required; contextual valida nome
apos recibo existente para nao quebrar replay legado vazio. Guest/Customer opcional
mantidos, dados preexistentes preservados. Tests positivos antigos de nome opcional
alinhados ao contrato novo; negativos auth preservados.
API96PostgreSQL PASS semskip; Webbuild+18focados PASS; Androidbuild/90JVM/lint e
13Compose PASS (390fonte1/360fonte2). Revisao independente required_name:
NO_FINDINGS_WITH_GAPS apos2P2 corrigidos. SuiteWebintegral nao verde: ampliacao com
roteiroslegados falhou em navegacao, interrompida e documentada na Spec029/aceite.
API/Weblocais reiniciadas, APKnovo preservando dados. Formulario Android aberto
sem criar comanda; tamanho/fonte/animacoes restaurados. Sem publicacao.
Proximo: operador preencher Nome ou apelido e testar a abertura autorizada.

## Integração com main — 2026-10-15

Branch reconciliada com TableGroups (#145), giro (#148), impressão S2 e confirmação direta de **Mais uma rodada** (#170). Android mantém o fluxo de repetição como Order independente, sem misturar com o carrinho manual; Web invoca `confirmRepeatedOrder` no diálogo. O merge de código não substitui CI Android/Web/API no HEAD final nem review R3 da experiência.

## Publicação dos refinamentos — 2026-10-15

Nova branch `codex/attendance-table-refinements`; implementação `33af9ff4`,
integração das correções remotas `54397cb0` em `a4828fe3`. Novo PR em rascunho
[#184](https://github.com/procopio420/rodada/pull/184), base `codex/ux-teste-mobile`,
dependente do #169 aberto. A branch anterior foi preservada.
Documentação consolidada: `docs/development/attendance-refinements-2026-10-15.md`.

Após integração: API109 PostgreSQL PASS, Web build/tipos+21 jornadas focadas PASS,
Android build/lint+93 JVM PASS e11 Compose PASS. A primeira captura Compose variou
entre frames; repetição determinística com animações suspensas passou e os valores
foram restaurados. Dois seletores Web ambíguos foram delimitados; histórico Android
usa descrição acessível. Revisor independente da integração sem achados reproduzíveis;
não executou testes, sem aprovação GitHub. CI e suíte Web integral permanecem gates.

Sem merge em main/deploy. Worktrees preexistentes preservados, next-env gerado
excluído. Próximo responsável: revisão e CI do novo PR, testes humanos locais e
resolução dos gates documentados antes de integração. Registros anteriores são
fotografias históricas e não certificam o SHA publicado agora.

## Retomada da integração PR184 — 2026-10-15

Autorização de merge na main mantida. Base publicada e763bb57; PR184 pronto,
base main. Android256 PASS e API424 PASS (983 testes). Web495 terminou com
106 PASS, 3 FAIL e 3 skip. Nenhum merge ou deploy executado nesta etapa.

Trace do artefato11981355904 confirmou listas de200 Tabs levando cerca de10s;
cinco consultas completas sobrepostas saturaram conexões e o GET da comanda ficou
na fila do navegador. AttendanceWeb passa a compartilhar leituras regulares em
andamento. Após mutation, aguarda leitura anterior e inicia outra, preservando
verificação de estado canônico antes de fechar. Abrange comandos de mesa,
serviço e movimento. Não altera regras financeiras nem autenticação.

Regressão determinística: código anterior executa três leituras em vez de uma
(FAIL); correção passa no build/tipos e23 jornadas focadas, incluindo leitura
pré-POST atrasada e leitura fresca pós-POST. Logs locais ignorados pr184-before,
pr184-refresh e pr184-final-build em visual-artifacts/android-native-port.
Roteiros attendance e tab-location-move alinhados ao popup e à limpeza direta;
asserts financeiros, autoria, replay, concorrência e isolamento preservados.

Integração Web local permanece bloqueada por fcntl ausente no Windows; nenhum
utilitário foi alterado para contornar o gate. Cluster descartável55462 encerrado.
Worktrees preexistentes preservados. Main avançou a5a53326d durante a pausa;
incorporar com cuidado antes de publicar e exigir CI/revisão no SHA final.
Próximo passo: revisão independente do patch e CI; se aprovado, concluir merge
PR184 com expected_head_sha e verificar SHA da main. Sem deploy autorizado.


## Cardápio por categorias — 2026-10-15

Branch `codex/attendance-category-catalog`, HEAD/base
`1705fa98279cff350776e55a0851698a3c61352c`, implementação local não commitada.
Objetivo atual: categoria → popup de produtos → popup de quantidade/Personalizar,
Android nativo e Web. Spec029/plan/tasks/acceptance e design system atualizados
antes do código. Inventário/evidência em
`specs/029-attendance-mobile-design/category-evidence.md`.

Implementados componentes CategoryCatalog/AttendanceCategoryCatalog, grade compacta,
quantidade sem inserção antecipada, configuração opcional, validação de máximo99
compartilhado e retorno de foco. Componentes de personalização e workspace existentes
reutilizados. Testes Compose/JVM/visuais novos e helpers de integração atualizados;
API/banco/recovery cifrado/ledger intactos. `.worktrees/` preexistente preservado.

Android build/lint/97JVM PASS;11Compose e mais2 em360dp/fonte2 e2 em430dp PASS.
Web build/tipos/30 jornadas atuais PASS; teste de ampliação de texto PASS. Lint
mantém erro preexistente no effect de recuperação em attendance-web.tsx:50, sem erro
novo nos componentes. Fullvisual interrompida ao encontrar roteiro antigo que procura
Contas; integração PostgreSQL Windows não reexecutada (fcntl). Não é aceite integral.
Revisão independente R3 NO_FINDINGS_WITH_GAPS, sem gate executado pelo revisor.

APK atualizado instalado com -r, reverse8000 e app aberto; Web3000 disponível.
Configurações temporárias de emulador restauradas. Sem reset/migration, nova
comanda/pedido/pagamento na demonstração, publicação Git ou deploy neste recorte.
Última ação: compilação e validação local do novo fluxo. Próximo passo: teste manual
local; antes de eventual publicação solicitada, conferir status/diff, gates Linux
e roteiro visual legado. GO para teste local; NO-GO de produção/homologação geral.


### Publicação e merge solicitados — PR195
Usuário autorizou novo PR e merge na main. PR195 aberto:
https://github.com/procopio420/rodada/pull/195. Branch de categorias publicada,
main atual integrada sem conflitos em `c1f6dab0978da9a4f3837abd4425320d543dcfb0`.
Revisão independente R3 desse SHA sem achados reproduzíveis; builds locais
pós-integração PASS e19 testes Web de segurança PASS. Ajustes posteriores somente
nos roteiros de teste (LiveComposeOrderTest e relógio do teste de leitura canônica),
com revisão adicional. Próximo passo: verificar o HEAD final remoto e a CI Web/Android,
resolver falhas reais e só então mergear. Sem deploy/Play autorizado.


## HANDOFF ATUAL — PR195 — 2026-10-15 19:31:50 UTC

Pedido autorizado: criar PR e mergear cardápio por categorias Android/Web na main.
PR: https://github.com/procopio420/rodada/pull/195. Branch:
`codex/attendance-category-catalog`; HEAD antes destas correções:
`2f996ecdc0cc0fec5b72196672a252c84a4e8634`, upstream igual. Main consultada
`2fc02bf7476bcf34cfcaca09f796e909fffc3813`, integrada sem conflitos em c1f6dab.
Sem merge/rebase em andamento. `.worktrees/` preexistente não rastreado preservado.
Handoff ativado por90% consumidos/10% restantes na janela oficial de300min.

Concluído: feature, Spec029/design/documentação, revisão independente R3 e PR.
Android build/lint/97JVM PASS;11Compose pós-integração e2regressões de busca/diálogo
externo PASS. Web build/tipos/30jornadas/19segurança PASS. CI do HEAD2f996ecd:
Android273 PASS,Web538 PASS (110integração PostgreSQL PASS/3skip). Android real123
passou POST perdido/restart/offline/replay e Compose real; continuação cross-surface
falhou5roteiros antigos,4passaram. Sem merge na main nem deploy.

Últimas correções:5specs em apps/web/tests/cross-surface (authorization,
browser-origins,concurrency-readback,qr-lifecycle,sse-recovery),
scripts/verify-qr-lifecycle.py e category-evidence.md. Usam helper addCatalogItem,
popup de mesa, fechamento antes de trocar mesa e limpeza direta DIRTY→AVAILABLE.
SQL exige cleaning_started_atNone,liberação/disponibilidade/ator conforme Spec004.
Auth/replay/saldos/concorrência preservados. Typecheck e ESLint desses arquivos PASS.
Revisão independente do delta por outro contexto: NO_FINDINGS_WITH_GAPS.
CI real das correções ainda pendente; não declarar PASS nem homologação geral.

Última ação: correções salvas e revisão concluída. Primeiro passo: verificar se
commit/push destas correções já terminou após este registro. Se sim, acompanhar
CI do novo HEAD, não do2f996ecd; não duplicar commit. MergePR195 explicitamente
autorizado apenas depois dos gates e conferência de conflitos/review. Sem reset,
force-push, cancelamento alheio ou teste mutável na demonstração. Web3000/API8000
ativos, Android aberto; logs locais ignorados category-pr-* e evidência Spec029.

### PROMPT PARA O PRÓXIMO AGENTE
Continue o PR195 e o merge autorizado na main no repositório atual Rodada.
https://github.com/procopio420/rodada/pull/195; branch codex/attendance-category-catalog.
Verifique CODEX_HOME e leia AGENTS global/override e local, PROCEDURES, Spec029,
adendo de limpeza direta Spec004, design system e este checkpoint. Confira Git,
HEAD/upstream/arquivos reais; preserve tudo e .worktrees/ não rastreado. Feature
categorias→popup de itens→popup de quantidade/Personalizar já pronta; não refazer.

Até2f996ecd: WebCI538110PASS/3skip,AndroidCI273PASS. POST Android/Compose passou
na123;5roteiros Webcrosssurface antigos falharam. Corrigidos os5specs listados e
verificador SQL para helper de catálogo,popup e limpeza direta sem inventar início.
Tipos/lintPASS, revisão independente sem achados. A primeira tentativa de publicar
o checkpoint foi rejeitada por caminho pessoal no texto; removido, não publicar
contexto pessoal ou contornar a revisão. Nenhuma mudança de produto nesta etapa.

Primeiro verifique se commit/push das correções já ocorreu após este checkpoint.
Acompanhe Web,Android e Android real POST disconnect pelo novo SHA; resolva falhas
causais com regressão e nova revisão, sem afrouxar asserts. Quando verdes no HEAD
final, confira main atual/reviews/conflitos, atualize descrição PR com resultados,
mergeie com expected_head_sha, confirme merged/mergeSHA e sincronize main local
por fast-forward. Sem autorização para deploy/Play/migration/seed/reset/dinheiro
real. Atualize este checkpoint e reporte resultado e limites sem alegar produção.
