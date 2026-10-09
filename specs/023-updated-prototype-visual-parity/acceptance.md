# Aceite

## Planejamento

- [x] Plano identifica fontes, estado atual, sequÃªncia, arquivos-alvo, mÃ©tricas e limites de comparaÃ§Ã£o entre plataformas.

## ImplementaÃ§Ã£o pendente

- [ ] Cinco exports têm contratos versionados por estado, selector, dimensão, crop, fixture e hash.
- [ ] Primitives novas usam typography/axes e medidas da referência, com comparação estrita.
- [ ] Cozinha/Bar equivalentes passam assertions ≤0,1% e revisão de geometria por região; teste não é apenas auditoria.
- [ ] Atendimento, pico e recovery Android possuem evidência HTML↔Compose e gates nativos no emulador fixado.
- [ ] Fixtures reproduzem dados/relógio/assets; inconsistências do export têm derivação documentada, sem produção incorreta.
- [ ] Responsive 360/430/768 tem contratos derivados; acessibilidade, toque, foco e conteúdo longo passam.
- [ ] CI retém referência/actual/diff/overlay/stats e falha em regressão; não usa baseline atual ou masks para ocultar diferenças.
- [ ] Audit/KB registram cobertura completa e diferenças restantes; nenhuma tela sem referência é declarada pixel-perfect.

## Inventário parcial da Cozinha

- [x] Referência/hash e ambiente identificados; selector único `.k` e recortes medidos.
- [x] Estado literal e comportamento dos controles observados; estados não disponíveis explicitados.
- [x] Evidência da implementação identifica base Git, fixture, geometria e diferenças sem alegação de equivalência.
- [x] Aplicação/exports originais e branch anterior preservados; V01 global permanece pendente.

Evidências e limites: [inventário](../../docs/design/v01-kitchen-inventory.md). Somente os itens desta subseção foram verificados; os critérios globais permanecem pendentes.

## Aceite do recorte V02 — Field / StatusBadge

- [x] Field confortável: 56 px, raio 10 px, padding horizontal 16 px, Archivo 20/600, borda interna 1,5 px; foco interno 2 px papel. Label 14/800, tracking 0,1em, gap 6 px.
- [x] Controle normal/foco/placeholder compara com `.inp` atualizado em ≤0,1%, pixelmatch threshold 0.1 / includeAA false; nenhuma referência ou tolerância substituída.
- [x] StatusBadge tem diferenças e ausência de equivalências documentadas; estados operacionais preservados.
- [x] Cozinha/Bar em 360/430/768 sem overflow, labels/foco preservados; fluxo de criação/reutilização continua passando.
- [x] Typecheck/build/test registrados com evidências e limitações; branch original preservada, sem merge/push.

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

- [ ] Cinco exports tÃªm contratos versionados por estado, selector, dimensÃ£o, crop, fixture e hash.
- [ ] Primitives novas usam typography/axes e medidas da referÃªncia, com comparaÃ§Ã£o estrita.
- [ ] Cozinha/Bar equivalentes passam assertions â‰¤0,1% e revisÃ£o de geometria por regiÃ£o; teste nÃ£o Ã© apenas auditoria.
- [ ] Atendimento, pico e recovery Android possuem evidÃªncia HTMLâ†”Compose e gates nativos no emulador fixado.
- [ ] Fixtures reproduzem dados/relÃ³gio/assets; inconsistÃªncias do export tÃªm derivaÃ§Ã£o documentada, sem produÃ§Ã£o incorreta.
- [ ] Responsive 360/430/768 tem contratos derivados; acessibilidade, toque, foco e conteÃºdo longo passam.
- [ ] CI retÃ©m referÃªncia/actual/diff/overlay/stats e falha em regressÃ£o; nÃ£o usa baseline atual ou masks para ocultar diferenÃ§as.
- [ ] Audit/KB registram cobertura completa e diferenÃ§as restantes; nenhuma tela sem referÃªncia Ã© declarada pixel-perfect.

## V05 parcial â€” navegaÃ§Ã£o do Atendimento

- [x] RegiÃ£o nativa 84 dp, centro 136 dp no telefone de 390 dp; alvos â‰¥44 dp.
- [x] Agora/Contas/Pedir mantÃªm callbacks; seleÃ§Ã£o explÃ­cita; busy bloqueia Pedir.
- [x] Mesas/Caixa preservados por capability; evidÃªncia adjacente.
- [x] ReferÃªncia original preservada; comparaÃ§Ã£o documentada sem baseline aprovado por aparÃªncia atual.

Contrato: [V05](../../docs/design/v05-atendimento-shell-contract.md). V05 global permanece aberta.

Resultado: [relatório parcial](../../docs/design/v05-atendimento-shell.md).
