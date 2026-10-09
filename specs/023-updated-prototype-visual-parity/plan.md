# Plano

Executar [V01–V07 no plano visual](../../docs/design/pixel-perfect-implementation-plan.md), começando por inventário/captura, medidas do design system e fixtures. Corrigir cozinha, implementar composição nativa, depois pico/recovery e gates de CI. Comparar geometria antes de refinar rasterização.

Referências e checks existentes da Spec 021 são base reutilizável, sem declarar que já há paridade completa. A Spec 022 permanece contexto funcional; dependências de backend são registradas por estado, não pré-requisito genérico para iniciar fidelidade visual.

## Execução documental parcial da Cozinha

1. Conferir Git e isolar origin/main, sem mover a branch de trabalho existente.
2. Verificar hash do ZIP/HTML/assets; abrir o export local sem alterá-lo.
3. Catalogar estados literais e testar controles demonstrativos; medir root e recortes a DPR 1.
4. Capturar a implementação da main com dados de inspeção explícitos, separando estados de extensão.
5. Registrar contrato, evidências, diferenças e próximos ajustes pequenos. Não implementar V02–V07 nem declarar aceite global.
