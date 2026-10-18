# Conta Android — evidência local, 2026-10-17

Base `fb3ea55d`, branch `codex/android-attendance-colors`, alterações locais.
Escopo de apresentação; regras, valores, callbacks e banco preservados.

| Achado na captura inicial | Ajuste | Evidência |
| --- | --- | --- |
| Saldo e textos com pouca hierarquia | Paper/Number no saldo e Muted nos rótulos | Fixture antes/depois no mesmo viewport |
| Três botões auxiliares desalinhados | Disclosure Ações da conta com linhas integrais | Teste de callbacks/online/busy/fechada |
| Histórico com botões pesados repetidos | Referência da Order, nome/subtotal alinhados e ações de texto | Teste de subtotal histórico e CANCELLED sem Corrigir |

Não houve alteração de fluxo de pagamentos, fechamento, correções ou rodadas.
Alertas de limite/serviço/pendências continuam fora do disclosure auxiliar.

## Executado

- PASS: assembleDebug, assembleDebugAndroidTest, 97 unitários e lintDebug.
- 16 casos Compose distintos aprovados entre AccountAppearanceTest,
  OrderWorkspaceTest, NativeAttendanceFlowTest e RepeatOrderDialogTest.
- A primeira execução conjunta teve 15 PASS e uma falha na igualdade binária
  entre duas capturas consecutivas de native-catalog; a repetição isolada desse
  teste passou sem alterar limiar, teste ou implementação. Registrar instabilidade,
  não declarar que a primeira rodada inteira passou.
- PASS: quatro execuções adicionais da jornada da Conta em 360/390/430dp e
  360dp com fonte200%, com capturas inspecionadas. Configuração original do AVD
  restaurada: resolução/densidade físicas, fontScale1.0.
- PASS: revisão independente após ajuste final de nome/preço, sem achados
  reproduzíveis. Não equivale a aprovação no GitHub.
- APK instalado; navegação real Mesa01 → comanda existente → Conta executada,
  sem confirmar pagamento, fechamento, correção, rodada ou qualquer outra escrita.

Capturas locais ignoradas: `visual-artifacts/android-native-port/account-before/`,
`account-after/`, `account-matrix/` e `account-overview-after.png`.
Antes/depois comparável em1080px/densidade420; matriz adicional em densidade320.

## Limites

Sem TalkBack, aparelho físico, Web, API/PostgreSQL financeiro ou produção nesta
rodada. Nenhuma alteração de Web; sem commit/push/merge/deploy. Próximo aceite:
avaliação visual do solicitante no Android local. Não implica GO de release.
