# Gerência e fluxo de pedidos — consolidação

Data:2026-10-18. Branch `codex/management-attendance-flow`. Base de implementação `dbf3d5fa067009cd9a255035a092f8c39c4507ac`. Esta entrega continua o [PR237](https://github.com/procopio420/rodada/pull/237), ainda aberto na consulta desta sessão. O novo PR tem como base `codex/android-attendance-colors` para apresentar apenas este incremento. Após integração do PR237, conferir/retargetear para main e executar novamente os gates do SHA resultante.

## Resultado

- Gerência Web: navegação em Agora, Operação, Financeiro, Cardápio e Gestão. Funções relacionadas agrupadas, retornos coerentes e compatibilidade com âncoras antigas.
- Cardápio gerencial: um único botão de adicionar produto; edição de produto/ícone como ação visível. Categorias/Todos, busca, cards e formulário só depois da escolha. Retorno/foco, upload e formulário em digitação preservados.
- Comandas na gerência: busca paginada de todas as abertas via active=true; não limitar a contagem às primeiras200 comandas misturadas ao histórico. Falha em página posterior não publica total parcial.
- Regressões API: abertura pelo staff, pedido, quitação parcial/integral/replay e cancelamento alimentam leitura gerencial; testes em PostgreSQL descartável, incluindo tenant/permissão e histórico. Não muda regras de pagamento no backend nesta entrega.
- Android Pedir: Nova comanda em mesa e sem mesa. Lista mesas livres e ocupadas com serviço habilitado; nome/apelido e confirmação explícitos. Mesa ocupada recebe outra Tab na mesma ocupação, sem unir contas. Mudança de ocupação/generation invalida escolha.
- Android: Cancelar alinhado abaixo das opções, sem sobreposição; testes e capturas com fonte200%.
- Android: pedido confirmado pelo servidor e releitura canônica retornam a Mesas e comandas. Erro/resultado desconhecido, outro contexto, rascunho ou pendências não provocam saída. Intenções/idempotência/persistência existentes preservadas.

## Contratos e evidências por recorte

- [Spec007](../../specs/007-management-cockpit/spec.md): [navegação](../../specs/007-management-cockpit/navigation-evidence.md), [editor de catálogo](../../specs/007-management-cockpit/catalog-editor-evidence.md), [auditoria de histórico](../../specs/007-management-cockpit/manager-history-audit.md).
- [Spec029](../../specs/029-attendance-mobile-design/spec.md): [seletor de mesa](../../specs/029-attendance-mobile-design/quick-order-table-evidence.md), [retorno após confirmação](../../specs/029-attendance-mobile-design/order-return-evidence.md).
- Spec023 e design system atualizados para a navegação gerencial; specs/plan/tasks/acceptance mantidos com a intenção e os limites da execução.
- Cores/conta Android, cancelamento por quantidade/PIN, histórico da noite, quitação automática e extrato pago já pertencem ao PR237; ver [consolidação anterior](attendance-bar-history-validation-2026-10-17.md). Não são duplicados como nova implementação.

## Validação local

Evidências anteriores nesta mesma base+diff, registradas nos arquivos acima:
- Web:30 Playwright de navegação/histórico e15 de catálogo/QuickCatalog PASS; build/typecheck/auth PASS. Diagnósticos legados de ESLint permanecem, sem novos/fatais no delta auditado.
- API:32 testes PostgreSQL PASS (lifecycle6, histórico3, pagamentos23), com banco de teste isolado.
- Android final: assembleDebug/testDebugUnitTest/lintDebug PASS;101 testes JVM,zero falhas. Sete Compose do seletor PASS; teste ocupado em360dp/fonte200% PASS. APK atualizado instalado.
- Revisões independentes dos recortes registradas com resultado sem achados reproduzíveis e gaps; não são aprovação GitHub. R3 no contato com recovery exige revisão qualificada do SHA de integração.

## Limites e decisão

A suíte visual global foi executada e não passou: seletor legado Contas em attendance-catalog.spec.ts:15;619 casos não executados por parada na primeira falha. Nenhuma baseline/tolerância foi alterada. Testes focados não equivalem a PASS global.

Paginação por offset não é snapshot transacional diante de mudanças concorrentes. Integração real de emissão/consumo do retorno após readback falho em Compose permanece pendente; condição de saída foi testada em JVM e revisada independentemente. Aparelho físico, TalkBack, produção e provedor real não verificados. Nenhuma mutation de pedidos/pagamentos foi feita na demo para validar esta entrega.

TESTADO_LOCAL por recorte; NO-GO para declarar homologação/produção. PR em rascunho para revisão e CI, condicionado à dependência237 e resolução dos gates. Sem merge, deploy, publicação Play ou mudança de banco remoto autorizados neste pedido. Excluídos do commit: worktrees, artefatos, banco/credenciais, checkpoint preexistente e next-env.d.ts gerado pelo servidor local. Próximo responsável: mantenedor para revisão do PR, dependência/base e CI; operador para aceite integrado.

## Revalidação para abertura do PR

2026-10-18, mesma árvore candidata: build Next.js PASS;45 testes Playwright PASS em1.1min (management-navigation, management-catalog-editor, management-tab-history e quick-catalog). KB PASS49documentos/297links/12skills; diff staged e padrões sensíveis PASS. Não repetida a suíte visual global após essa rodada; sua falha registrada permanece pendente. Não reexecutados PostgreSQL e Android nesta etapa de publicação: evidências por slice acima vinculadas à árvore de implementação.


## Follow-up de CI após integração do PR237 — 2026-10-18
O PR237 foi integrado à main em9754cc22. Merge local da main em8ac4b862 preservou os quatro blocos documentais da Spec029 de ambas as branches; sem conflito de código. As quatro falhas API e sete falhas Bar Web do CI13b5c5cb correspondiam exatamente às regressões corrigidas na main pelo PR237. Não afrouxar assertions nem reabrir automaticamente comandas quitadas.

A falha Web adicional de quick-catalog procurava o select Produto removido pelo editor por categorias. O teste agora percorre busca→Todos→card→formulário e procura o preview dentro do editor; mantém criação única, reuso normalizado, preço/estação, regeneração, upload128px, ID de ícone preservado e remoção. Aceite Spec007 atualizado antes do teste.

Build, validação visual pós-integração e novos checks ainda em execução nesta fotografia; resultados e revisão do SHA final serão registrados após conclusão. Integração BFF local requer fcntl, indisponível neste runtime; CI Linux permanece obrigatório, sem shim/SQLite. Aprovação qualificada R3 ainda não verificada; merge condicionado aos gates reais. Nenhum deploy, banco compartilhado ou root checkout alterado.
