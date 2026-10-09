# 023 — Paridade visual com os protótipos atualizados

Estado: planejado. Data: 2026-10-08.

## Objetivo

Implementar fidelidade visual das telas e estados dos cinco exports atualizados no Web e Atendimento Android. O [plano canônico](../../docs/design/pixel-perfect-implementation-plan.md) define contratos de comparação e execução V01–V07.

## Comportamento e regras

- Referência é o export atualizado com hash, estado, dados, assets, dimensão e recorte identificados; não o screenshot atual do produto.
- Comparações equivalentes Web exigem no máximo 0,1% de pixels divergentes com parâmetros fixados e nenhum desvio estrutural crítico. Zero diferença é o objetivo.
- Android exige equivalência de geometria, typography, cores e composição com HTML, seguida de baseline nativa revisada e regression gates no mesmo emulador. Diferença de rasterização é documentada por região.
- Mesmos componentes em fixture/preview e produção; não usar screenshots como UI nem esconder layout diferente numa rota de testes.
- Tokens/componentes são promovidos ao design system antes de replicação; não introduzir estilo ad hoc.
- Preservar autoridade da API, disponibilidade, ledger, estados de pedido, autenticidade de inferência e confirmação offline. Diferença funcional necessária usa referência derivada explícita e rastreável.
- Artboards e molduras de apresentação não viram chrome da aplicação; responsive adaptations precisam contratos próprios.

## Fora de escopo

Implementação de todo backlog funcional da Spec 022, geração IA adiada, publicação e redesenho silencioso dos exports. Telas sem referência não recebem alegação de equivalência completa.

## Critérios

Ver [acceptance.md](acceptance.md); execução em [plan.md](plan.md) e [tasks.md](tasks.md).

## V03 parcial — fixture equivalente da Cozinha

Este recorte entrega somente dados/harness de teste e documentação, sem mudar a aplicação. Um cenário comum gera DTOs reais e normalização de dados do export atualizado. Produtos, quantidades, estados e timestamps são compartilhados; resumo inclui apenas NEW/ACCEPTED/PREPARING, passe apenas READY e retirada PICKED_UP separada. Fixture não é seed, fallback de produção ou prova de API real.

Preservar o export literal e registrar toda derivação em [contrato da fixture](../../docs/design/v03-kitchen-comparison-contract.md). Comparação de tela mede divergências, não aceita fidelidade total: composição/metadata sem campos canônicos continuam pendências V04. Limites e gates existentes permanecem intactos.

Resultado do recorte V03: [comparação e diferenças](../../docs/design/v03-kitchen-comparison.md). V03 global e fidelidade total continuam pendentes.
