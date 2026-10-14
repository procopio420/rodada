# Rodada Atendimento Android — AGENTS.md

Herde `../../AGENTS.md`, [KB](../../docs/agents/README.md), [procedimentos](../../docs/agents/PROCEDURES.md), `README.md` local, design system e spec completa relevante.

## Regras locais

- App é Kotlin/Jetpack Compose nativo, não bridge Web. UX em telefone BYOD: toque, navegação, 360–430 dp, teclado/scroll, estados acessíveis, zero tarefas artificiais no pico.
- Pedidos, recebimentos, caixa, tabs, mesas e produção dependem do estado canônico da API. Operação "enviando" não é "sem conexão"; só indicar falha quando houver evidência.
- Em timeout/restart/force-stop/reconnect, manter Venue, operador, payload e UUID de intenção imutáveis, armazenamento cifrado e reconsulta; nunca gerar outro pagamento ou pedido por retry cego.
- Não declarar `pago` ou `enviado` por UI otimista. Pagamentos reais e Tap on Phone só podem ser ativados após provider/merchant/dispositivo e aceite explícitos; piloto Web-only não exige Android.
- Nunca guardar PIN/credenciais em texto, imprimir tokens, extrair o Keystore ou commitar upload keys. BYOD não concede privilégios extras por device.
- Design e catálogo respeitam categorias, disponibilidade, quantidade no item, componentes/tokens existentes e contrato da Spec; não recriar carrinho distante da ação sem justificativa.

## Gates

- Em `apps/attendance-android`: `./gradlew testDebugUnitTest assembleDebug --stacktrace`; executar `lintDebug` para mudanças UI/nativas quando disponível.
- Mudanças de lifecycle/recovery exigem testes Android e o ensaio manual `Android real POST disconnect` / force-stop de `.github/workflows/android.yml` em ambiente isolado; aprovação JVM isolada não equivale a aparelho.
- AAB/upload/produção/Play são operações distintas e opt-in. Não gerar ou publicar release como efeito colateral de PR.
- Handoff registra versão/SHA, teste JVM/Android real, emulador vs aparelho, limitações e risco de perda/duplicidade.

## Skill sob demanda

Ative [`rodada-android-compose`](../../.agents/skills/rodada-android-compose/SKILL.md) para Kotlin/Compose e recuperação; combine [`rodada-ui-design`](../../.agents/skills/rodada-ui-design/SKILL.md) para UI e [`rodada-pos-safety`](../../.agents/skills/rodada-pos-safety/SKILL.md) para ordem/pagamento/tenant/replay.
