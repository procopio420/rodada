# Aceite

## Planejamento

- [x] Plano identifica fontes, estado atual, sequência, arquivos-alvo, métricas e limites de comparação entre plataformas.

## Implementação pendente

- [ ] Cinco exports têm contratos versionados por estado, selector, dimensão, crop, fixture e hash.
- [ ] Primitives novas usam typography/axes e medidas da referência, com comparação estrita.
- [ ] Cozinha/Bar equivalentes passam assertions ≤0,1% e revisão de geometria por região; teste não é apenas auditoria.
- [ ] Atendimento, pico e recovery Android possuem evidência HTML↔Compose e gates nativos no emulador fixado.
- [ ] Fixtures reproduzem dados/relógio/assets; inconsistências do export têm derivação documentada, sem produção incorreta.
- [ ] Responsive 360/430/768 tem contratos derivados; acessibilidade, toque, foco e conteúdo longo passam.
- [ ] CI retém referência/actual/diff/overlay/stats e falha em regressão; não usa baseline atual ou masks para ocultar diferenças.
- [ ] Audit/KB registram cobertura completa e diferenças restantes; nenhuma tela sem referência é declarada pixel-perfect.

## V03 parcial — Cozinha

- [x] Apenas testes/documentação alterados, branch original preservada.
- [x] Fixture comum fornece produtos/identidades, quantidades, NEW/PREPARING/READY/PICKED_UP e timestamps fixos; READY/PICKED_UP não entram no resumo.
- [x] Referência literal preservada; derivação altera somente dados/linhas derivadas e enumera alterações, sem stylesheet/masks para esconder composição.
- [x] Assert de DTO e conteúdo de ambas as páginas verifica igualdade de dados; captures repetidas têm hash idêntico.
- [x] Métricas pixelmatch threshold 0.1/includeAA false e gate 0,1% existentes inalterados; divergência total permanece reportada como pendência.
- [x] Typecheck/build/test e relatório de diferenças entregues, sem merge/publicação.

## V04 parcial — agrupamento de tickets

- [x] Fixture V03: cinco grupos de pedido, seis itens e seis ações; P08 exibe destino uma vez, Fritas/Calabresa com ações independentes.
- [x] POST de Fritas/P08 afeta somente aquele OrderItem; Calabresa/P08 permanece em preparo.
- [x] Orders diferentes com mesma Tab e itens sem order_id permanecem grupos independentes.
- [x] Desktop conserva coluna destino 84 px, ação 116×56; mobile mantém alvo ≥44, sem overflow; Cozinha/Bar consistentes.
- [x] Referência, limite 0,1% e dados V03 preservados; relatório mostra métricas e diferenças restantes.
- [x] Typecheck/build/test:visual/test:realtime passam; branch original preservada, sem merge/publicação.

Resultados: [relatório V04 parcial](../../docs/design/v04-kitchen-tickets.md).
