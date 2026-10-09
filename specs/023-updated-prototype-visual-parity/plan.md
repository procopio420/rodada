# Plano

Executar [V01–V07 no plano visual](../../docs/design/pixel-perfect-implementation-plan.md), começando por inventário/captura, medidas do design system e fixtures. Corrigir cozinha, implementar composição nativa, depois pico/recovery e gates de CI. Comparar geometria antes de refinar rasterização.

Referências e checks existentes da Spec 021 são base reutilizável, sem declarar que já há paridade completa. A Spec 022 permanece contexto funcional; dependências de backend são registradas por estado, não pré-requisito genérico para iniciar fidelidade visual.

## Recorte Field/StatusBadge

1. Base isolada de origin/main; conferir hashes das fontes e entregas anteriores.
2. Medir Field atualizado e atual em recorte equivalente, com fontes locais e texto/largura determinísticos. Registrar diferenças antes do código.
3. Documentar variante confortável no design system; reutilizar Field e tokens no Quick Catalog de ambas as estações.
4. Acrescentar comparação estrita sem alterar o export, os testes compactos ou limiares. Comparar Cozinha com Bar adjacente em 360/430/768 px.
5. Executar typecheck, build, suíte visual e testes realtime; registrar resultados e limites. Sem merge/publicação.

Resultado do recorte: [inventário e validação](../../docs/design/v02-field-status.md). V02 global permanece pendente.
