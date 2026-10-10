# Plano

## Continuação completa — ordem de execução

1. Completar inventário reproduzível de night (jornadas principais), system (espécimes), peak e connectivity (instâncias literais). Cozinha mantém contrato anterior; validar hashes atuais de todas as fontes.
2. Medir divergências antes de corrigir componentes; promover medidas aprovadas no design system.
3. Reexecutar fixture/comparação Cozinha/Bar e seus comandos individuais; nenhuma tolerância aumentada.
4. Extrair apenas componentes Android que precisam de instrumentação real: header, linha/contadores/contas existentes. Corrigir clipping comprovado, preservar viewmodel/callbacks/capabilities; testar uma jornada por vez.
5. Revalidar pico/recovery com snapshots e estado canônico; feedback não declara sincronização sem confirmação.
6. Revalidar matriz360/390/430 e fonte1/2 no API36, com texto/targets e capturas repetidas; comparar com regiões literais/derivadas identificadas.
7. Types/build/auth/realtime/visual/Web API PostgreSQL e Android unit/build/lint/instrumentação. Registrar falhas reais, correções e rodada final; ensaio integrado separado de fixture.
8. Documentar critérios efetivamente comprovados, dependências e diferenças restantes; publicar commits/PR rascunho sem merge.

## Recorte anterior V01 — night/Agora

1. Conferir remotos/worktrees/PRs e isolar main45c4742, preservando branches e banco.
2. Auditar V01–V07, código Android/ProductionBoard, manifesto e ADR de referências/fontes locais.
3. Registrar contrato antes do harness; medir estado inicial Agora e Bar adjacente em Chromium, DPR1, pt-BR/America-Sao_Paulo e relógio congelado.
4. Reutilizar Playwright e fontes locais já referenciadas pelo export importado. Servir somente arquivos locais em porta efêmera; bloquear rede externa. Não mudar o export nem substituir transporte/stylesheet no harness.
5. Validar SHA256 do ZIP/HTML/assets, unicidade dos seletores, recursos/fontes e estabilidade de duas capturas. Revisar imagens e registrar limites, ambiente e mapa atual de pendências.
6. Publicar somente documentação/contrato/harness/evidências validados em commit pequeno e PR rascunho. Gates Web de produto, Android e PostgreSQL não são evidência deste recorte documental.

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

## V04 parcial — tickets

1. Base isolada da main atual, reutilizando o commit local V03 apenas como infraestrutura de teste/documentação.
2. Atualizar contrato/design system antes do código; agrupar apresentação por order_id, com fallback por item.id.
3. Manter markup de cada stationTicket e handlers; envolver itens em stationOrder com destino comum. Reutilizar tokens e medidas desktop 84/116 px.
4. Adaptar a observação da Tab no teste V03 ao contexto do grupo, mantendo asserts dos mesmos dados. Acrescentar checks de grupos, geometria, fallback e transição individual.
5. Comparar Cozinha e Bar, repetir fixture V03 sem mudar referência ou limites; typecheck/build/test:visual/test:realtime. Registrar diferenças ainda abertas. Sem merge/push.

Resultado do recorte: [relatório V04 parcial](../../docs/design/v04-kitchen-tickets.md). V04 global permanece aberta.

## V05 parcial — navegação do Atendimento

Extrair navegação para composable usado por produção/instrumentação, promover medidas ao design system, comparar crop HTML e screenshot nativa antes de qualquer baseline.

Contrato: [V05](../../docs/design/v05-atendimento-shell-contract.md). V05 global permanece aberta.

Resultado: [relatório parcial](../../docs/design/v05-atendimento-shell.md), sem baseline nativa total aprovada.

## Continuação — integração e navegação acessível

Consolidar commits V01–V05 na branch de revisão sem mover main ou branch do usuário. Conflitos de append documental preservam todas as subseções; CSS preserva Field confortável e stationOrder. Reutilizar dois testes instrumentados e expandir checks de texto sem clipping. Executar matriz de seis configurações; revalidar Web integrado. Auditar evidências/hashes e documentar inventário/publicação.

## Hierarquia da Gerência — V02 parcial

1. Inventariar main/referências/PRs e capturar Gerência antes com fixture existente.
2. Versionar contrato e tokens antes do código; documentar ausência de export de Gerência.
3. Reutilizar sectionHeader/operationalMetric/surfaceNav, SVG local e tokens. Conservar labels/hrefs/cálculos; Impressoras permanece em Mais.
4. Expandir teste de navegação existente e fixture/parity para largura360/430/768, fonte ampliada, warnings/loading/erro. Comparar ícone Agora com SVG original imutável em0.1%; a tela da Gerência recebe revisão geométrica, não selo pixel-perfect.
5. Typecheck/build, suíte visual completa/realtime e integração real PostgreSQL; evidências antes/depois, adjacência Caixa/Cozinha, commit/documentação. Não integrar automaticamente em main nem substituir a stack/banco ativo.

Comparação do ícone isola posição e fundo somente nos espécimes durante o teste: ambos SVGs em (0,0), fundo surface-1/g1 equivalente. Capturas literais em coordenadas fracionadas distintas deram14.72%; posicionamento comum deu0%. Geometria, stroke, cor, export original e limiar0.1% permanecem. Esse resultado não mede a barra inteira ou fidelidade da Gerência.

## Todas as superfícies Web — abordagem

Reutilizar branch isolada já atualizada com main ae416da e preservar PR65/trabalho anterior. Inventariar headings e componentes compartilhados; promover OperationalHeading baseado em OperationalIcon com nomes acessíveis inalterados. Evitar dupla iconografia onde a referência já tem SVG. Aplicar tokens compartilhados de hierarquia/profundidade, completar navegação do Atendimento e leitura dos tickets. Capturar antes/depois usando fixtures existentes, reaproveitar matriz visual/estados/fluxos e integrações PostgreSQL. Preservar stack3119 e banco ativo. Atualizar apenas prévia isolada após build/checks; versionar evidências e ampliar PR65, sem merge na main.

Para disponibilizar o acabamento na demo3119, transpor somente mudanças de apresentação para a branch própria demo-functional: componentes compartilhados/títulos/CSS, sem absorver rotas ou contratos recentes de Atendimento/alertas ainda ausentes nessa base. Preservar autenticação entregue, backend e banco; revalidar build/visual/fluxo focado dessa composição antes de reconstruir somente Web. Essa adaptação é distinta da branch principal de revisão baseada na main e será documentada por commit. Serviços encontrados parados podem ser reabertos com os caminhos/dados existentes, sem reset.


## Resultado da sequência atual

Execução/reprodução e diferenças por etapa no [relatório atual](../../docs/design/spec023-demo-validation.md). Commitar contratos, header/matriz, OFFLINE/reconnect e gate guest em slices separados; ensaio real/readback e aceites em commit documental final. Próximo trabalho visual: região de tickets16,241% sem refazer acabamento entregue; próxima jornada nativa de verificação: estorno e adaptação interna200%/teclado. Nenhuma aprovação global por checkbox histórico.

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
