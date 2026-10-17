# E01-05 / E03-05 — shell e Agora nativos UX2 (parcial)

Contrato: Spec033 e protótipo PR212 `prototype/ux-2-0/index.html`.
Dependências: entrada Agora PR220; projeção staff-safe PR218. Branch de main,
com cherry-pick explícito do commit de entrada 27ed61f2. Sem merge/deploy.

## Antes / depois esperado

Antes: header alto, navegação superior, três filtros Prontos/Chamadas/Pendências,
contas abertas misturadas em Agora, entrega com conclusão direta obrigatória.
Depois: header 72dp, wordmark aprovado, footer de três ações, Agora com duas
filas Atendimentos/Entregas e linhas compactas do protótipo. Dados vêm dos
repositórios reais. Abrir linha não assume nem conclui tarefa.

## Critérios deste slice (não concluem E01/E03)

- Header 72dp, logo113x42, margens22; conteúdo20dp e footer7dp/61dp,
  Atendimentos/Entregas50dp com contadores canônicos/freshness.
- Tipografia Archivo com largura100 neste shell; tokens de cor existentes.
- Filtros/scroll preservados; seleção de Tab é explícita, por ID de target v1.
- TABLE requer table/occupancy/generation ainda correspondentes ao readback;
  UNAVAILABLE e target ausente/desconhecido não inferem Tab de destination_label.
- BILL abre Conta da Tab autorizada; SERVICE abre contexto da Tab; READY abre
  detalhe do item, quantidade, estação e destino. Nenhuma mutation ao abrir.
- Cada abertura reconsulta `GET /dispatch/tasks/{id}/` e valida ID, tipo, estado
  e target canônico; READY exige item ainda READY. A seleção explícita após
  fallback TABLE reconsulta a chamada e a ocupação/generation antes de abrir.
  Contexto de chamada e ações continuam disponíveis nessa Tab escolhida, com
  Conta como seção inicial para BILL. Navegação manual limpa a origem da tarefa.
  Voltar do workspace (botão ou dismiss) também encerra essa origem, somente
  quando a saída foi permitida; a primeira seleção explícita TABLE a preserva.
- Recuperação original permanece acessível. Conta/Atualizar/Pico/Caixa existentes
  continuam acessíveis em menu operacional na área meta do header. Essa adaptação
  necessária ao app real é diferença intencional proposta, sem aprovação implícita;
  paridade/sign-off seguem pendentes até decisão explícita.
- Estados sem dados/erro/loading/stale não mostram sucesso otimista.
- JVM/lint/build, instrumentação das ações e pixels em360/390/430; integração
  real Django/PostgreSQL separado de fixture visual. FontScale2 e dispositivo
  físico são gates próprios e devem ser registrados honestamente.

Não altera motores de pedidos, pagamentos, recovery, políticas nem autenticação.
Home da comanda, catálogo, resumo/pedido e Mesas ficam nos próximos recortes;
não apresentar shell como paridade integral.

## Revisão independente — primeira passagem

`646bb629` / `2b2b1b06`, revisor em outro contexto `dispatch_finish_guard`:

- P1: fila tinha target autorizado na leitura, mas abrir não revalidava a task;
  Guest revogado após a fila poderia manter o deep link antigo. Correção neste
  recorte: leitura exata antes de SERVICE/BILL/READY e novamente na seleção TABLE
  ou ação Abrir comanda da entrega. Sessão original conferida antes/depois do IO.
- P2: fallback TABLE perdia ações da chamada e BILL não selecionava Conta após
  escolha explícita. Correção: origem preservada por IDs/occupancy/generation,
  novo readback na escolha e contexto vinculado somente à Tab escolhida.

Correções exigem reexecução e nova revisão; este registro não é aprovação.
API218 ainda não publica `claimed_by_id` no serializer DELIVERY; completar a
projeção é dependência da identificação visual do outro responsável. A API
continua autorizando/negando a mutation canônica; este cliente não cria bypass.

## Correção da segunda passagem — origem após voltar

A revisão independente de `ffcf8533` encontrou P2: voltar do workspace mantinha
`serviceTableTarget`, bloqueando outra Tab ou reaplicando ações da chamada em
seleção manual. O botão de retorno e dismiss agora encerram a origem somente
após `clearSelection` efetivar a saída; uma pendência que bloqueia saída mantém
o contexto. A primeira seleção TABLE continua revalidada e preserva chamada/Conta.

Regressão: `LiveAgoraUx2Test`, variante `revokeBeforeOpen` com `fallbackTabName`,
confere ações após seleção explícita e ausência delas após voltar/reabrir
manualmente a mesma Tab. Compilação do teste não equivale à execução em dispositivo.

Validação local da correção: `testDebugUnitTest assembleDebug lintDebug
compileDebugAndroidTestKotlin --stacktrace` PASS (102 testes JVM, zero falhas).
A regressão Compose foi compilada, mas não executada; nenhum emulador, aparelho,
API real, PR ou operação GitHub nesta correção. Exige revisão independente do
novo SHA e execução do cenário isolado antes de alegar aceite de navegação.

Revisão estática independente do fix `749ca37f` pelo contexto integrador/root:
`NO_FINDINGS_WITH_GAPS`. Conferiu `clearSelection` síncrono: bloqueio/pendência
mantém `selectedTab`, preservando origem; saída efetivada limpa origem. Fallback
da primeira seleção não mudou. Regressão Compose adequada, ainda não executada.
Não corresponde a aprovação GitHub nem autorização de merge/deploy.

Checagem posterior de runtime: `adb devices` sem dispositivos; nenhum processo
da API isolada 18131, emulador 5558 ou runner live-agora encontrado. Ensaio real
`NOT_RUN` por runtime indisponível; nenhuma stack foi recriada/resetada. Fix
mantido na worktree isolada para integração pelo responsável.

## Readback durante atualização concorrente

Ensaio nativo real do fix de origem: 360 dp/font1 passou; 390 dp/font1
falhou ao exibir vínculo desatualizado após leitura exata. A abertura TABLE
consultava `loading`/conectividade do snapshot da composição anterior ao IO,
ao mesmo tempo que validava a mesa recém-lida. Correção: avaliar esses três
campos do mesmo estado atual após o IO; verificações de sessão, ID/tipo/estado
e occupancy/generation permanecem.

A variante de teste `refreshBeforeTask` inicia atualização explícita, comprova
que Atualizar está indisponível enquanto ela ocorre e então abre a chamada.
O runner local usa delays ASGI em reads (tables 800 ms/task exata 2 s) para
exercitar a conclusão da atualização durante o readback, sem alterar respostas
nem enfraquecer os casos negativos. Captura também a seleção fallback e o
retorno manual. Resultados e SHA final devem acompanhar o novo ensaio.
