# E01-05 — entrada operacional Android

Contrato: Spec033, PR216, E01 e AC01. Referência visual/de jornadas: PR212.
A Spec029 contratava Mesas como entrada padrão. A Spec033 passa a exigir Agora;
este recorte altera somente o valor inicial da navegação nativa existente.

## Critérios deste recorte

- Nova entrada após login mostra Agora selecionado, mantendo + Pedir e Mesas.
- Navegação restaurada continua usando rememberSaveable; não forçar Agora em
  recomposição, atualização ou retorno ao contexto.
- Selecionar + Pedir continua exigindo escolha explícita de Tab; não cria pedido.
- Drafts, intents, mutations e permissões mantêm seus componentes existentes.

O teste permanente LiveComposeOrderTest passa a conferir Agora selecionado e
Mesas não selecionado após login na API Django descartável, antes de escolher
explicitamente uma comanda e confirmar o pedido pelo fluxo nativo existente.
Este teste é opt-in: compilar o APK instrumentado não significa executar a jornada.

## Escopo de aceite

Este recorte não conclui E01 nem comprova paridade visual integral com PR212.
Comparação lado a lado em 360/390/430, todas as jornadas e sign-off operacional
permanecem gates da implementação completa. Aparelho físico não conectado.
Resultados executados serão anexados após os gates locais.

## Evidência local (2026-10-18)

Base: `dcb3a79590904a2c289641d285eda639e1713c87`; branch
`impl/033-e01-android-entry`. Fontes alteradas: apenas entrada NOW e teste
instrumentado da jornada existente. O teste espera o catálogo habilitado após
a revalidação canônica, sem remover asserts nem alterar regras de produção.

- `./gradlew testDebugUnitTest lintDebug assembleDebug`: PASS; 97 JVM,
  zero falhas/erros/skips. Build local executado antes do commit com este diff.
- `FrontlineNavigationTest`: PASS, 3 testes no emulador API36.
- `LiveComposeOrderTest` usando `expectedApiBaseUrl=http://10.0.2.2:18131/`:
  PASS em 360, 390 e 430dp, MainActivity e repositórios reais.
- Readback independente `scripts/verify-android-compose-order.py`: PASS em cada
  largura; uma Order, dois itens NEW (Bar/Cozinha), duas Charges somando 1700
  centavos e zero Payments. PostgreSQL descartável próprio em 55491.
- Primeira execução 430 falhou esperando confirmação; repetição após reinício
  frio do emulador apresentou ANR do SystemUI e perdeu a hierarquia Compose.
  Repetição com boot concluído e animações do emulador desativadas passou
  integralmente, sem modificar os asserts. Falhas anteriores preservadas.

Os JSONs anteriores contêm SHA da base porque foram gerados com diff pendente;
não representam execução da main limpa. Este registro vincula explicitamente os
resultados ao diff deste recorte. Evidência pós-commit será anexada separadamente.
Logs locais: `/tmp/rodada-033-android-entry-{build,navigation,live-360,live-390v4,live-430retry2}.log`.
Captura `/tmp/rodada-033-android-entry-now-390.png` comprova somente a seleção de
Agora, não paridade visual. Revisão independente e CI seguem gates pendentes.

| Tela/estado | Protótipo | Web | Android | Diferenças | Resultado |
| --- | --- | --- | --- | --- | --- |
| Entrada operacional | Agora, PR212 | Fora deste recorte | Agora selecionado após login | Shell/listas ainda não portados fielmente | Parcial; E01 aberto |
| Pedido existente | Confirmação/destino | Fora deste recorte | Pedido real confirmado + SQL Bar/Cozinha | Fluxo de cardápio/revisão ainda difere do protótipo | Integração PASS; paridade pendente |

Nenhum critério integral da Spec033 é marcado concluído por este recorte.
Paridade completa Web/Android/PR212, aparelho físico e aceite humano continuam
pendentes. Sem merge/deploy; próximos slices: shell nativo fiel e confirmação
persistente UX2, com comparação visual e revisão independente.
