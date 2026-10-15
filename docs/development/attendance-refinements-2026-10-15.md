# Atendimento — refinamentos Web e Android

Data: 2026-10-15. Branch: `codex/attendance-table-refinements`.
PR: [#184](https://github.com/procopio420/rodada/pull/184), em rascunho.

## Resultado

- Mesas abrem opções em popup; clique fora/Voltar fecha quando não há operação bloqueante. Filtros de estado removidos, busca preservada.
- Android reutiliza cores semânticas nas bordas e ícones de mesa, com painel e navegação no topo. Mantém a ação central **Pedir** incorporada pelo PR anterior.
- Liberar retorna à lista com mesa aguardando limpeza. Tocar nessa mesa oferece **Concluir limpeza**; confirmação e leitura canônica retornam à lista com mesa disponível.
- Nome ou apelido sempre visível e obrigatório nas novas comandas staff, até 120 caracteres. Customer/cadastro continua opcional; comandas antigas e replay de recibo legado são preservados.
- Corrigida a allowlist Android de `service/open-tab`, mantendo a chave e o corpo originais na recuperação.

Contratos: `specs/001-core-pos/spec.md`, `specs/004-table-guest-ordering/spec.md`,
`specs/027-table-service-claim/spec.md` e `specs/029-attendance-mobile-design/`.
Design e domínio: `docs/design/system.md` e `docs/domain/model.md`.

## Histórico e integração

Implementação registrada em `33af9ff4cebb4191020e598d8fcd00489151c527`.
O PR #169 permanece aberto; este novo PR tem como base `codex/ux-teste-mobile`,
preservando suas correções em `54397cb08f66672d66f259123e40dcf298c3db45`.
Integração registrada em `a4828fe3`; conflitos foram conciliados preservando
histórico sob demanda, busca normalizada, seleção por ID, repetição direta e
novos popups. Não houve alteração da branch anterior nem merge em main.

## Evidência e limites

Antes da integração: 96 testes API/PostgreSQL, build/tipos Web e 18 jornadas
focadas, build/lint Android e 90 testes JVM; 13 execuções Compose finais passaram.
Detalhes históricos e comandos estão no aceite/evidência da Spec 029.

Após integração: build/tipos Web passou; 21 jornadas focadas passaram (26,6s).
A primeira execução encontrou dois seletores ambíguos de Voltar, corrigidos
delimitando a região de personalização, sem remover asserções.
Android assembleDebug/assembleDebugAndroidTest, lint e 93 testes JVM passaram.
API/PostgreSQL isolado: 109 testes, zero falhas/erros/skips.
Compose: 11 testes passaram; a primeira execução teve uma falha de igualdade
entre frames consecutivos com animações ativas. Repetição com animações
suspensas passou, sem alterar a comparação; valores originais foram restaurados
e o app reaberto. Não representa comparação com baseline de referência.
Seleção do histórico em teste Android usa sua descrição acessível.

Logs locais ignorados: `visual-artifacts/android-native-port/pr-integration-*`.
Comandos: build Web e teste `attendance-mobile-design.spec.ts`; Gradle
`assembleDebug assembleDebugAndroidTest testDebugUnitTest lintDebug`; instrumentação
`NativeAttendanceFlowTest`, `TablePresentationInstrumentedTest` e
`TableServiceNavigationTest`. API: testes table_service, concorrência, access,
paytime, house_account, ordering, guest_access e hospitality_tables no PostgreSQL
de testes. `git diff --check` contra a base do novo PR passou; whitespace herdado
de integração em arquivo fora do diff deste PR não foi reescrito.

Revisões independentes R3 dos recortes rota, limpeza e nome:
`NO_FINDINGS_WITH_GAPS`, após correções. Revisão independente da resolução de
integração também sem achados reproduzíveis; testes não foram executados pelo
revisor. Isso não constitui aprovação no GitHub.

Suíte Web integral não está certificada: a execução ampliada anterior encontrou
roteiros legados incompatíveis com a navegação em popup e foi interrompida.
CI do novo SHA, revisão integrada completa, aparelho físico, TalkBack/IME e
aceite humano permanecem pendentes. Catálogo/ProductIcon Android ainda têm
diferenças documentadas; não se declara paridade global nem GO de produção.

Logs, APKs e bancos permanecem locais/ignorados. Worktrees preexistentes e
arquivo gerado next-env não integram o pacote. Sem reset de dados, seed,
migration de demonstração, merge em main ou deploy.

## Continuidade

PR em rascunho, dependente do #169. Próximo responsável: revisão/CI do PR,
seguido de validação humana dos fluxos no ambiente local. A receita histórica
está em `docs/development/attendance-local-test-2026-10-15.md`; verificar estado
real dos serviços e banco antes de retomá-los. Não aplicar migrations novas no
banco compartilhado apenas para reproduzir testes; usar banco descartável.

## Integração autorizada na main — 2026-10-15

Operador solicitou merge do PR #184 na main. PR retargetado e retirado de draft;
main `c589ff08` incorporada sem conflitos em `6b382583`. Esse pacote inclui o
trabalho do #169; não houve escrita na branch anterior. Revisão independente R3
do diff integrado contra main: `NO_FINDINGS_WITH_GAPS`, sem achados reproduzíveis,
sem execução de gates pelo revisor. Estado anterior de PR encadeado é histórico.

CI Android252 passou. API419: 962 testes passaram e seis falharam porque fixtures
positivas antigas abriam Tab sem nome; corrigidos somente os corpos de criação em
test_web_completion, test_house_account_e2e e test_tab_operations_e2e, preservando
asserts financeiros/audit/ocupação e negativos. Helpers Web usam Nome ou apelido
sempre visível e fecham o popup da mesa antes de navegar para outra mesa; jornada
de cardápio canônico também usa o campo obrigatório visível.

Tentativa local da integração Web bloqueada por `fcntl` no utilitário Linux de
coordenação de resets, ausente no Windows. Não alterar esse utilitário neste
recorte nem declarar PASS. Cluster PostgreSQL descartável específico da tentativa
foi encerrado, preservando o banco de demonstração. Fechamento depende do novo CI.
