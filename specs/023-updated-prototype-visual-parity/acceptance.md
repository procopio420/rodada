# Aceite

## Continuação completa — gates da demo

- [x] Cinco fontes verificadas e34 contratos dos estados principais versionados, crops/medidas/fontes/normalizações e hashes idênticos entre execuções.
- [x] Alterações de componentes por clipping comprovado; callbacks/busy/targets/estados preservados, sem dados demonstrativos no produto.
- [x] Cozinha/Bar: testes de transição individual/disponibilidade e comparação atuais; diferenças integrais reportadas, sem ocultar regiões ou aceitar paridade.
- [x] Android: header/navegação sem clipping em fonte1/2, targets≥44dp, busy e callbacks; screenshots/matriz API36.
- [x] UI nativa contra API real: login, conta, pico, Tab, busca/carrinho/pedido, dinheiro manual600centavos, fechamento Tab/caixa. Readback PostgreSQL exige exatamente uma Order e um CASH CONFIRMED, ator/timestamp, saldo0, caixa600/600/discrepância0.
- [x] API offline: SSE reconnect conserva SEM SINAL; leitura confirmada após retorno produz ONLINE. Regra na Spec014, fronteira30s testada.
- [x] Web typecheck/build/auth/realtime/visual e13 integrações PostgreSQL; Android51unit/build/lint e4×6 instrumentados, zero skips/failures.
- [x] Roteiro distingue interceptação, emulador, protocolo HTTP e PostgreSQL real; sem claim de hardware/provider/produção.
- [ ] Todas telas/jornadas internas nativas com fonte200%/teclado e estorno em UI nativa.
- [ ] Publicação/CI final documentadas por head; critérios globais somente com confronto correspondente.

Evidência atual: [relatório](../../docs/design/spec023-demo-validation.md), conteúdo dos commits41a42bd/20e3649/bb29b5d/1d22393. Critérios globais abaixo continuam independentes e abertos onde não comprovados.
## Recorte anterior V01 — night/Agora e Bar

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



## V02/V05 — catálogo e cobrança com fonte ampliada

Verificar os componentes reais com instrumentação360/390/430 e fontes1/2 antes da correção. Linha de produto deve conservar nome completo, preço canônico em centavos, rota/disponibilidade e ação atual; não aceitar ellipsis ocultando identidade nem preço sem largura. Se confirmado clipping, nome e preço ganham linhas próprias nos tokens existentes. Diálogo de pagamento mantém decisões e footer/callbacks/busy, mas conteúdo longo deve permitir rolagem interna e preservar acesso às advertências/caixa/valor com fonte200%. Não alterar métodos, regras financeiras, provider ou confirmação offline. Extrair somente o botão de produto e tornar PaymentDialog interno para teste do componente de produção. Aceite: nomes sem ellipsis/clipping, preço legível; advertência acessível; caixa fechado não confirma; caixa ativo repassa exatamente300centavos/mesmo método/ponto; matriz nativa atual e screenshots. Paridade visual global continua aberta.

V05 login: verificar a tela real com fonte200% e teclado. Se conteúdo exceder viewport, permitir rolagem apenas na variante ampliada (>1.3, limiar existente), conservando geometria normal, campos/trim/PIN clearing/busy e callback de autenticação. Teste usa fixture somente em androidTest e captura antes de digitar PIN; não mudar política de autenticação ou persistência.

Resultado login: sem teclado a tela360/font200 já cabe; não alterar sua composição por hipótese. Com IME real aberto, captura confirma PIN/Entrar cortados e ausência de rolagem. Adaptação final habilita rolagem somente quando WindowInsets.ime>0, em todas as fontes; sem IME conserva layout central existente. Artefato login-before registra apenas a falta do recurso de scroll no teste inicial; login-keyboard-before é a prova de clipping efetivo.

Resultado atual do recorte crítico Android: catálogo, pagamento e login com IME real corrigidos; 51unit/build/lint e48 testes instrumentados (8×6) aprovados, zero skips. 36 capturas adjacentes permanecem idênticas. [Critérios, reprodução, evidências e limites](../../docs/design/spec023-critical-fields.md). Critérios globais de paridade/jornadas internas/hardware/provider permanecem abertos.

## Continuação10/10 — V04 tipografia de tickets

Base main45c4742/PR68 em b1fb704, original6e2f4ca preservada. Comparação atual revela título de item24px e margem metadata8px, divergentes dos21px/6px do export. Isso quebra Bolinho em duas linhas na coluna equivalente. Experimentar somente esses dois valores; aceitar apenas se reduzir a diferença integral, caso contrário descartar; conservar destaque lateral, headings, layout dos grupos, conteúdo canônico e ações individuais. Nenhum cliente, equipamento, SLA/meter ou ação coletiva será inventado para copiar o mock.

Verificação: fixture V03 antes/depois1280×800, títulos reais21px/line-height1.25/metadados6px e nome Bolinho completo numa linha; pares estáveis, hashes/fontes preservados e redução dos pixels divergentes em tickets sem tolerância nova. Cozinha/Bar adjacentes e ações individuais mantêm gates existentes. Executar types/build/auth/realtime/visual e integração PostgreSQL isolada. Comparação global ainda exige≤0.1%; regiões sem contrato funcional permanecem diferenças explícitas. Não reabrir acabamento das demais superfícies.

## V05 — estorno nativo e fonte ampliada

Validar jornada existente de estorno direto com dinheiro de teste e autorização do operador; não criar novo método/provider/endpoint. Antes: instrumentar RefundDialog real em360/font200 e verificar acesso a valor/motivo/PIN/decisões. Se clipping confirmado, aplicar o contrato rolável e footer ampliado já aprovado para PaymentDialog, mantendo valid/busy, PIN limpo após submit, chave idempotente estável durante a edição, centavos e caixa. Não capturar PIN/token. Testes devem conservar callback original e comando300centavos, motivo trim e mesma chave quando valor muda. Capturas antes/depois e matriz API36; fluxo real separado em PostgreSQL55523 com leitura de Refund/Payment/CashMovement/auditoria. Não alegar execução de hardware/provider nem reescrever pagamentos confirmados.

Resultado do experimento de tickets: fonte21px/metadata6px corrigiu quebra, mas aumentou região16.241→17.8714%. Candidata descartada; CSS e testes de apresentação restaurados byte a byte ao head. Não aceitar nova baseline. Diferenças estruturais incluem conectividade/heading/campos canônicos distintos e múltiplas ações de P08; dependências documentadas, não copiar metadados/SLA do mock.

Resultado parcial atual: estorno rolável/decisões acessíveis;51unit/build/lint e54instrumentados aprovados. Gates Web atuais types/build12auth/realtime197visual13PostgreSQL. [Detalhes e limites](../../docs/design/spec023-refund-validation.md). Jornada nativa financeira/readback atual são verificações separadas, sem usar HTTP como prova de UI.
