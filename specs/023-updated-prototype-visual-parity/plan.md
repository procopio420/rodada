# Plano

Executar [V01–V07 no plano visual](../../docs/design/pixel-perfect-implementation-plan.md), começando por inventário/captura, medidas do design system e fixtures. Corrigir cozinha, implementar composição nativa, depois pico/recovery e gates de CI. Comparar geometria antes de refinar rasterização.

Referências e checks existentes da Spec 021 são base reutilizável, sem declarar que já há paridade completa. A Spec 022 permanece contexto funcional; dependências de backend são registradas por estado, não pré-requisito genérico para iniciar fidelidade visual.

## Execução documental parcial da Cozinha

1. Conferir Git e isolar origin/main, sem mover a branch de trabalho existente.
2. Verificar hash do ZIP/HTML/assets; abrir o export local sem alterá-lo.
3. Catalogar estados literais e testar controles demonstrativos; medir root e recortes a DPR 1.
4. Capturar a implementação da main com dados de inspeção explícitos, separando estados de extensão.
5. Registrar contrato, evidências, diferenças e próximos ajustes pequenos. Não implementar V02–V07 nem declarar aceite global.

## Recorte Field/StatusBadge

1. Base isolada de origin/main; conferir hashes das fontes e entregas anteriores.
2. Medir Field atualizado e atual em recorte equivalente, com fontes locais e texto/largura determinísticos. Registrar diferenças antes do código.
3. Documentar variante confortável no design system; reutilizar Field e tokens no Quick Catalog de ambas as estações.
4. Acrescentar comparação estrita sem alterar o export, os testes compactos ou limiares. Comparar Cozinha com Bar adjacente em 360/430/768 px.
5. Executar typecheck, build, suíte visual e testes realtime; registrar resultados e limites. Sem merge/publicação.

Resultado do recorte: [inventário e validação](../../docs/design/v02-field-status.md). V02 global permanece pendente.

## V03 parcial — Cozinha

1. Revisar `fixtures.ts`, comparação/geometry/Product identity de `parity.spec.ts` e referência atualizada.
2. Versionar contrato antes do harness. Criar cenário comum test-only com relógio 23:14, items e produtos/ícones.
3. Reutilizar fixture HTTP/clock/stable e comparador existente; adicionar opção de relógio sem alterar cenários anteriores. Adaptar DTOs e dados no DOM da referência, sem mudar seus estilos.
4. Guardar literal, derivada, aplicação, diffs/overlay/stats; verificar dados equivalentes e estabilidade de duas capturas.
5. Typecheck/build/test:visual/test:realtime; registrar diferenças e preservar branch original. Sem merge/publicação.

Resultado do recorte V03: [comparação e diferenças](../../docs/design/v03-kitchen-comparison.md). V03 global e fidelidade total continuam pendentes.
