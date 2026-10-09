# Plano

Executar [V01–V07 no plano visual](../../docs/design/pixel-perfect-implementation-plan.md), começando por inventário/captura, medidas do design system e fixtures. Corrigir cozinha, implementar composição nativa, depois pico/recovery e gates de CI. Comparar geometria antes de refinar rasterização.

Referências e checks existentes da Spec 021 são base reutilizável, sem declarar que já há paridade completa. A Spec 022 permanece contexto funcional; dependências de backend são registradas por estado, não pré-requisito genérico para iniciar fidelidade visual.

## V03 parcial — Cozinha

1. Revisar `fixtures.ts`, comparação/geometry/Product identity de `parity.spec.ts` e referência atualizada.
2. Versionar contrato antes do harness. Criar cenário comum test-only com relógio 23:14, items e produtos/ícones.
3. Reutilizar fixture HTTP/clock/stable e comparador existente; adicionar opção de relógio sem alterar cenários anteriores. Adaptar DTOs e dados no DOM da referência, sem mudar seus estilos.
4. Guardar literal, derivada, aplicação, diffs/overlay/stats; verificar dados equivalentes e estabilidade de duas capturas.
5. Typecheck/build/test:visual/test:realtime; registrar diferenças e preservar branch original. Sem merge/publicação.

Resultado do recorte V03: [comparação e diferenças](../../docs/design/v03-kitchen-comparison.md). V03 global e fidelidade total continuam pendentes.

## V04 parcial — tickets

1. Base isolada da main atual, reutilizando o commit local V03 apenas como infraestrutura de teste/documentação.
2. Atualizar contrato/design system antes do código; agrupar apresentação por order_id, com fallback por item.id.
3. Manter markup de cada stationTicket e handlers; envolver itens em stationOrder com destino comum. Reutilizar tokens e medidas desktop 84/116 px.
4. Adaptar a observação da Tab no teste V03 ao contexto do grupo, mantendo asserts dos mesmos dados. Acrescentar checks de grupos, geometria, fallback e transição individual.
5. Comparar Cozinha e Bar, repetir fixture V03 sem mudar referência ou limites; typecheck/build/test:visual/test:realtime. Registrar diferenças ainda abertas. Sem merge/push.

Resultado do recorte: [relatório V04 parcial](../../docs/design/v04-kitchen-tickets.md). V04 global permanece aberta.
