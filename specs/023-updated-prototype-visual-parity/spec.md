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

## Recorte V02 — Field e StatusBadge Web (09/10/2026)

Comparar o Field `.inp`/`.fld` do export atualizado de Atendimento com o Field do Quick Catalog de Cozinha e Bar. Promover apenas medidas comprovadas em uma variante confortável compartilhada; o Field compacto existente mantém seu contrato. Preservar autocomplete, validação, foco visível e API.

StatusBadge deve ser inventariado por equivalência semântica: `.badge` do Atendimento é contador, `.rel`/`.casa` são relacionamento e NOVO é etiqueta de pedido. Nenhum deles autoriza mudar indisponibilidade para atraso ou redesenhar os badges de disponibilidade. Ausência de equivalente deve ser registrada, sem alegação de paridade. V02 completa e Compose permanecem fora deste recorte.

Evidências deste recorte: [Field / StatusBadge](../../docs/design/v02-field-status.md). A variante confortável foi verificada somente no controle e nos labels descritos; não declara equivalência de tela completa.
