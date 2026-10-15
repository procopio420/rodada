# Evidência local — categorias e quantidade

Registro de 2026-10-15. Base `1705fa98279cff350776e55a0851698a3c61352c`; branch
`codex/attendance-category-catalog`, diff local sem commit/publicação.

## Escopo
Android Compose e Atendimento Web: busca/categorias na entrada, grade da categoria
em popup, produto em popup de quantidade e personalização, retorno à categoria e
revisão integral. Não altera API, banco, auth, ledger, pagamento ou persistência.
POS/Guest mantêm o fluxo existente. Agrupamento de categorias preexistente de cada
plataforma preservado; não é uma nova taxonomia compartilhada no backend.

## Implementação
Android: `CategoryCatalog`, `AttendanceCatalogCard`, `ProductCustomizationSheet`,
`TabWorkspace` e `CartQuantities`/ViewModel. Web: `AttendanceCategoryCatalog`,
`ProductCustomization`, `OrderWorkspace`, `AttendanceDraft`, CSS e retorno de foco
capturado antes da seleção assíncrona. Mesmo produto/configuração agrega sem perder
quantidade; máximo de 99 compartilhado por configuração, inclusive edição/incremento.
Cancelamento não adiciona. Disponibilidade/opções/contexto revalidados na inserção.
Os controles de envio e a intenção original continuam separados da navegação.

## Validação executada
- Android assembleDebug/assembleDebugAndroidTest/testDebugUnitTest/lintDebug: PASS.
  97 testes JVM, incluindo 4 CartQuantities, sem falhas.
- Emulador: 11 Compose PASS (`CategoryCatalogTest`, `OrderWorkspaceTest`,
  `NativeAttendanceFlowTest`). Mais 2 em 360 dp/fonte 2 e 2 em 430 dp/fonte 1 PASS.
  Tela física original equivale a 411 dp, fonte 1. Não declarar matriz de 390 dp nativa.
- Capturas dos três estados com fixture e inspeção visual, incluindo fonte 2.
  Uma primeira execução teve divergência entre frames na captura exata legada;
  repetição com animações suspensas passou. Tamanho/densidade/fonte/animações
  restaurados; APK instalado com `-r` e app real aberto, sem limpar dados.
- Web build/tipos: PASS. Lint dos componentes e testes deste recorte não aponta
  erro novo. `attendance-web.tsx:50` mantém erro preexistente de
  `react-hooks/set-state-in-effect` e aviso de dependência do effect. Lint global
  não é PASS; contrato de recuperação desse trecho não alterado.
- Web fluxo atual: 30 testes PASS na execução final (45,1s). Execução anterior
  teve 1 falha intermitente de contagem de leituras em liberação de mesa (3 vs 2);
  repetição isolada e execução final passaram, sem relaxar assert.
  Inclui 360/390/430/1280, cancelamento, personalização, limites/edição, foco A/B/A,
  catálogo atualizado/indisponível, intenção original e navegação sem envio.
  Teste separado de ampliação efetiva de texto do popup PASS. Após ajuste final
  de foco com estado React, build/tipos e5 jornadas de foco/abertura PASS.
- Revisão independente R3: NO_FINDINGS_WITH_GAPS no diff local; sem gates executados
  pelo revisor e sem homologação de produção. Achados anteriores sobre limite de
  edição/incremento corrigidos com regressão.

## Limites e reprodução
`test:visual` integral executado e interrompido no primeiro roteiro legado:
`attendance-catalog.spec.ts` procura “Contas”, removido antes desta mudança.
Não é PASS global; migração desses roteiros e comparações gerais permanece pendente.
Helpers de jornadas PostgreSQL ajustados ao popup, mantendo asserts financeiros.
Integração real não reexecutada: o coordenador de resets usa `fcntl`, indisponível
no Windows conforme tentativa documentada anterior. Não modificar esse utilitário
nem usar a base de demonstração como fixture. CI/Linux continua necessário.

Logs/capturas locais ignorados em `visual-artifacts/android-native-port/category-*`
e `apps/web/visual-artifacts/029/categories/`. Relatórios em `apps/web/test-results/`.
Para reproduzir, construir Web antes de Playwright e executar
`playwright test attendance-mobile-design.spec.ts`; Android usa os três testes
Compose listados e teste JVM CartQuantities. Configuração debug local com
`adb reverse tcp:8000 tcp:8000` e API `127.0.0.1:8000`.

GO para teste local assistido do fluxo; NO-GO para declarar homologação integral
ou produção. Sem novo pedido/comanda/pagamento na demonstração, migrations/reset,
commit/push/PR/merge/deploy neste recorte. Próximo responsável: validação manual
local e gates Linux antes de eventual pedido de publicação.

## Publicação autorizada

Em 2026-10-15, após o teste local, solicitado novo PR com estas alterações e
merge na main. Validar integração da main atual, revisão independente e CI do
HEAD publicado antes do merge; os limites de homologação acima permanecem.

### PR195 e integração da main
PR: https://github.com/procopio420/rodada/pull/195. Implementação `f6dbec92`,
main `2fc02bf7476bcf34cfcaca09f796e909fffc3813` integrada sem conflitos em
`c1f6dab0978da9a4f3837abd4425320d543dcfb0`. Builds Web e Android/JVM/lint
reexecutados PASS; segurança Web (sessão/tenant/backend/identidade/gateway):19 PASS.
Revisão independente do commit integrado: NO_FINDINGS_WITH_GAPS, sem testes
executados pelo revisor e sem aprovação GitHub simulada.

Roteiro Android real recém-integrado da main alinhado ao nome obrigatório e ao
novo fluxo por categorias, preservando uso de repositórios reais e confirmação
canônica. Compilação AndroidTest PASS; não executado contra a demonstração. Teste
Web de leitura canônica congela o relógio antes do mount para que somente o polling
explícito avance; mantém duas leituras obrigatórias e confirmação após leitura nova.
CI Web/Android do HEAD do PR precisa ser consultada antes do merge. Esses resultados
não autorizam Play/deploy nem comprovam homologação integral.
