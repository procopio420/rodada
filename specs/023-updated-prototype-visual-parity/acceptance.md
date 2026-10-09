# Aceite

## Continuação completa — gates da demo

- [ ] Cinco fontes verificadas e contratos dos estados principais versionados, com crops/medidas/fontes/normalizações.
- [ ] Alterações de componentes baseadas em medidas, callbacks e estados preservados; sem dados fictícios no produto.
- [ ] Cozinha/Bar: testes de transição individual/disponibilidade e comparação atuais, diferenças integrais reportadas sem esconder regiões.
- [ ] Android: header/jornadas existentes sem clipping em fonte1/2, alvos44dp, busy/capabilities e estado de conexão preservados, screenshots no API36.
- [ ] Web types/build/auth/realtime/visual e integração PostgreSQL; Android unit/build/lint/instrumentação com resultados atuais.
- [ ] Roteiro integrado distingue testes interceptados, emulador e API/PostgreSQL real; sem claim de hardware/provider/produção.
- [ ] Publicação/limites documentados por commit; critérios globais de paridade só marcados com confronto correspondente.

## Recorte atual V01 — night/Agora e Bar

- [x] ZIP corresponde ao manifesto; HTML/assets originais mantêm hashes antes/depois.
- [x] Estado inicial Agora e painel Bar têm seletores únicos, dimensões/crops e estilos medidos; moldura/status bar simulada são classificados.
- [x] Fontes locais carregadas sem fallback/rede externa; duas capturas por região principal possuem bytes idênticos.
- [x] Auditoria distingue presença de código, checks históricos e validação atual; demais jornadas/exports e V02–V07 permanecem abertos.
- [x] Evidências identificam base, ambiente e reprodução; publicação SHA remoto/PR rascunho comprovada.

Evidência bc9575b confirmada em origin/codex/spec023-next, [PR68 em rascunho](https://github.com/procopio420/rodada/pull/68). Somente aceite parcial V01; nenhum gate de paridade integral do produto foi concluído.

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

## Continuação — integração e navegação acessível

- [x] Navegação mantém Agora/Contas/Mesas/Caixa/Pedir e autorização/busy; labels não têm overflow nas seis configurações.
- [x] Canonical 390/fontScale1 mantém geometria e captura; fonte ampliada possui contrato de adaptação separado.
- [x] Gate remove somente XMLs descartáveis de instrumentação anterior e exige dois testes atuais sem skip/falhas.
- [x] Entregas anteriores permanecem documentadas; nenhuma fidelidade total declarada.
- [ ] Branch original intacta e publicação confirmada por SHA remoto.

Resultado: [validação integrada](../../docs/design/spec023-review.md).

## Hierarquia da Gerência — aceite parcial

- [x] Cinco links em uma única linha em360/430/768; cada um tem ícone24 e label legível, alvo≥44 e seleção por hash/aria-current preservada. Impressoras continua acessível em Mais.
- [x] Agora SVG corresponde ao original night (hash912b59ca1bfc6f0f7c92927ac6e0d8f4f663963f34f7adbb6a228e48c98d0a2f) em≤0.1%, sem alterar o export/limiar. Pictogramas novos são extensões documentadas.
- [x] Exposição usa valor canônico existente, destaque34px, largura total e cor financeira. Exceções precedem Agora; loading/erro inicial não exibem zeros medidos.
- [x] Cabeçalhos/ícones não alteram nomes acessíveis e preservam callbacks, hrefs, dados e permissões. Fonte ampliada não corta labels nem deixa rodapé/campos sob a barra.
- [x] Testes existentes/novos, types/build e adjacentes passam; evidências não declaram Gerência ou023 integralmente pixel-perfect.

Comparação do ícone isola posição e fundo somente nos espécimes durante o teste: ambos SVGs em (0,0), fundo surface-1/g1 equivalente. Capturas literais em coordenadas fracionadas distintas deram14.72%; posicionamento comum deu0%. Geometria, stroke, cor, export original e limiar0.1% permanecem. Esse resultado não mede a barra inteira ou fidelidade da Gerência.

Resultado deste recorte: [evidências e limites](../../docs/design/spec023-management-hierarchy.md). Gates locais passaram; não conclui V02 ou023 global.

## Acabamento compartilhado Web — aceite

- [x] Todas as rotas Web existentes possuem heading contextual ou usam componente compartilhado coberto; redirecionamento / mantém destino.
- [x] Headings mantêm texto/nível/id/foco, ícones são aria-hidden e labels/contratos/ações permanecem.
- [x] Títulos, seções e subseções têm hierarquia coerente, sombras discretas e foco visível; alvos≥44 e sem overflow nas configurações verificadas: matriz principal360–1440 e subpáginas nas larguras discriminadas no relatório. Font scale/zoom global200% permanece pendente.
- [x] Bar/Cozinha mantêm lote/fila/passe, quantidade/destino/estado/callbacks; mesmos SVGs literais existentes. Cliente mantém disponibilidade e saldo canônicos.
- [x] Impressos/HTML histórico não são redesenhados; só sua superfície Web. Sem alteração API/financeira/auth.
- [x] Typecheck/build, suíte visual/realtime e integração PostgreSQL passam; comparação/regiões/limitações registradas sem baseline/tolerância novos.

Resultado: [cobertura, evidências e limites](../../docs/design/spec023-all-web-hierarchy.md). Acabamento compartilhado entregue; Spec023 global permanece aberta.
