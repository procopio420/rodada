# Retorno após pedido confirmado — Android

2026-10-18, branch `codex/management-navigation`, base `dbf3d5fa`; diff local não commitado. Contrato em `specs/029-attendance-mobile-design/spec.md`, seção Retorno após pedido confirmado.

## Implementação
`OperationsViewModel.kt`: sinal completedOrderTabId emitido apenas após ACK e tabDetail canônico, remoção da intenção e consumo do rascunho da Tab selecionada. returnAfterConfirmedOrder aguarda fim de loading/submitting, consome sinal uma vez e usa clearSelection com leitura das pendências. `TabDraftContexts.kt`: condição de retorno exclui outra Tab, rascunho e bloqueios existentes. `AttendanceScreen.kt`: efeito explícito retorna a Mesas e comandas quando a saída é confirmada; nenhuma comparação com mensagem textual. `TabDraftContextsTest.kt`: sucesso e negativos de contexto, loading/submitting, pendência e ausência do sinal. Spec/plan/tasks/acceptance atualizados. Não altera HTTP/payload/chave, dinheiro ou persistência; não cria pedidos no ambiente compartilhado para testar.

## Evidência
- APK debug compilado e instalado com atualização, aplicativo reaberto.
- `assembleDebug testDebugUnitTest lintDebug -ProdadaApiBaseUrl=http://127.0.0.1:8000/ --console=plain`: PASS,1m17s;101 testes JVM,zero falhas. Depreciações preexistentes permanecem. `git diff --check`: PASS.
- Revisão independente `/root/review_order_return`, somente leitura, base dbf3d5fa e diff local atual: NO_FINDINGS_WITH_GAPS, sem achados reproduzíveis. Confirmou emissão após readback, consumo seguro e efeito com loading/submitting. Não é aprovação GitHub.
- Limites da revisão/testes: não exercitada integração real entre emissão do replay após readback falho e consumo em Compose; teste JVM cobre condição de navegação. Sem pedido criado na demo, aparelho físico, CI ou homologação de produção.
- Log local: visual-artifacts/android-sync-runtime/order-return-build.log.

## Estado
Implementado localmente; validação completa do fluxo com servidor permanece pendente. Sem commit/push/merge/deploy. Alterações anteriores do Web e Android preservadas. Próxima etapa: homologação do retorno após pedido no ambiente de teste pelo operador.
