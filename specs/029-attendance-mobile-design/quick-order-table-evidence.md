# Pedir: nova comanda em mesa — evidência local

2026-10-18. Branch `codex/management-navigation`, base `dbf3d5fa`; alterações locais não commitadas. Spec: `specs/029-attendance-mobile-design/spec.md`, seção Nova comanda em mesa pelo Pedir. Risco R2: apresentação e encaminhamento ao comando existente; sem alteração da API, autorização, ledger ou recuperação.

## Implementação
`AttendanceScreen.kt`: opção em mesa no seletor Pedir, lista de AVAILABLE com serviço habilitado e sem ocupação, nome obrigatório, confirmação explícita, voltar/cancelar, lista vazia e invalidação da mesa selecionada. Reutiliza `openFirstTableTab`, sua intenção persistida e leitura canônica. Exige as capacidades já requeridas pelo endpoint. `NativeAttendanceFlowTest.kt`: cinco cenários novos e regressão da seleção existente. Spec/plan/tasks/acceptance atualizados. Alterações Web anteriores preservadas.

## Execução
- `assembleDebug testDebugUnitTest lintDebug assembleDebugAndroidTest -ProdadaApiBaseUrl=http://127.0.0.1:8000/ --console=plain`: PASS; build final59s. JVM100 testes, zero falhas. Avisos de depreciação preexistentes permanecem.
- Seis cenários Compose focalizados: PASS no emulador,25.553s; confirmação apenas após nome, seleção sem mutação, vazio/voltar, indisponibilidade concorrente, permissão e busy.
- Apresentação inicial:390/430dp fonte100% e360dp fonte200% executadas com1 teste por perfil. Fonte200% revelou corte no Cancelar; corrigido movendo Voltar para conteúdo rolável.
- Após correção: seis testes focalizados repetidos e360dp fonte200% repetido: PASS. Captura final inspecionada com campo e Abrir e pedir/Cancelar íntegros.390/430dp não repetidos após o ajuste final. Configuração do emulador restaurada.
- APK debug instalado com atualização preservando dados; app reaberto. Não houve criação de comanda no banco compartilhado: testes exercitam callbacks isolados.
- `git diff --check`: PASS. Logs/capturas locais em `visual-artifacts/android-sync-runtime/quick-table-*` e `quick-order-table-*` (ignorados).

## Limites e próximo passo
TESTADO_LOCAL. Sem prova de criação real nesta sessão, aparelho físico ou TalkBack. A revisão desta slice é R2 local; não representa sign-off de produção. Sem Web UI modificada, suíte visual Web não aplicável. Nenhum commit/push/merge/deploy. Próximo responsável: homologação do fluxo no app com ambiente de teste e decisão de integração.

## Correção após retorno visual — 2026-10-18

A captura do operador mostrou sobreposição no seletor inicial, que não era coberta pela captura anterior do formulário de nome. Causa: a coluna de criação ocupava confirmButton e Cancelar usava dismissButton separado. Agora as três ações pertencem à mesma coluna.

Lista inclui AVAILABLE sem ocupação e OCCUPIED com ocupação ativa/serviço habilitado. Exibe Livre/Ocupada; confirmação ocupada encaminha o TableSummary selecionado para openTableTab, livre para openFirstTableTab. ID/generation da ocupação capturados no clique são revalidados antes de confirmar. Não há alteração de API/persistência/ledger ou fusão de comandas.

Build/JVM/lint/APK de teste: PASS,58s,100 testes unitários/zero falhas. Sete cenários Compose: PASS,26.298s. Inclui regressão geométrica Cancelar abaixo da opção sem mesa, seleção de mesa ocupada sem comando antecipado, callback com ocupação e bloqueio por mudança de geração. O cenário ocupado repetido em360dp/fonte200%: PASS,6.292s; captura inicial inspecionada, todos os botões íntegros e separados. APK instalado; configuração do emulador restaurada. Logs quick-table-occupied-*, capturas quick-order-actions*. Sem criação de comanda no banco compartilhado. Limites de aparelho/TalkBack/criação real e estado Git anteriores permanecem.
