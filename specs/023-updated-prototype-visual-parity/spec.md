# 023 — Paridade visual com os protótipos atualizados

Estado: em implementação; demo validada nos fluxos discriminados, paridade global aberta. Data: 2026-10-08.

## Continuação autorizada — sequência completa da demo importante

Primeira correção V02/V05 a verificar: Header Android atual põe identidade e três ações na mesma Row. Extrair sem alterar comportamento para teste instrumentado; reproduzir nomes longos/fonte200% antes da correção. Contrato responsivo: identidade em região superior e ações FlowRow abaixo, tokens16/12/8, targets44, callbacks/busy existentes. Instrumentação verifica cada linha de texto e ações nas seis configurações; comparar regiões com header night60px e declarar extensão, não paridade integral.

O pedido posterior amplia a execução além de um único recorte. Priorizar: contratos dos cinco exports e jornadas principais; componentes/legibilidade sem refazer acabamento; Cozinha/Bar com comparações honestas; Atendimento por jornada; pico/recovery; responsividade/acessibilidade; gates e roteiro integrado. A ordem V01–V07 permanece. Cada mudança tem contrato e critério antes do código. Reutilizar a base isolada main45c4742 e PR68, com commits por slice.

O objetivo demonstrativo é concluir os gates verificáveis dos fluxos existentes; não transforma diferenças visuais ainda não resolvidas em fidelidade total. Contratos de backend ausentes são dependências nas specs proprietárias. Simulações dos exports (pagamento offline, entrega/ownership sem provenance) não autorizam copiar semântica para domínio. Fontes ampliadas/header/linhas Android devem conservar conteúdo completo e alvos44dp; controles e callbacks reais preservados.

Validação desta sequência usa ambiente de teste isolado: PostgreSQL dedicado separado do55459 e do banco demonstrativo, serviços Web/API em portas livres, emulador API36 isolado. Sem reset de dados existentes, merge ou implantação. Hardware, SDK privado/provider e produção exigem evidência própria e não serão declarados comprovados.

## Recorte anterior — V01, night/Agora e Bar adjacente (09/10/2026)

Base isolada `origin/main` em `45c4742`. Prioridade: completar o contrato de referência ausente antes de novas alterações de composição. Inventariar somente o estado inicial Agora e o painel Bar simultâneo de `night/Main.dc.html`: seletores únicos, regiões, medidas, tipografia, assets, hashes e duas capturas determinísticas. Congelar o relógio no harness; não alterar dados, estilos, HTML ou ZIP original. Classificar moldura/status bar simulada separadamente do conteúdo.

Auditar V01–V07 contra código e relatórios versionados nessa base. Relatórios históricos comprovam apenas seus commits. PR61 sobrepõe apresentação Web e sessão em base própria; não importar seu trabalho. Não alterar produto/API/Android, gerar dados no banco ou executar a demo integrada neste recorte. Os demais estados night, exports system/peak/connectivity, paridade de tela e gates nativos continuam pendentes.

Aceite parcial: contrato reproduzível de Agora/Bar com hashes verificados, regiões medidas e capturas repetidas byte-idênticas, acompanhado de mapa das pendências e próximo recorte. A captura HTML é simulação de referência, nunca evidência Android, hardware ou serviço real. A validação usa Chromium com fontes locais e falha em seletor ambíguo, asset ausente ou captura instável; nenhuma tolerância/baseline é alterada.

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

## V01 parcial — inventário da Cozinha (09/10/2026)

Escopo autorizado: somente identificar a referência executável da Cozinha, seus estados, seletores, recortes, dimensões e diferenças perante a implementação na main `1dfdf8a`. Trabalho documental em `codex/v01-kitchen-inventory`, sem alterar aplicação, exports, tokens, fixtures de produção ou comportamento. A branch `codex/ux-operational-polish` em `6e2f4ca` deve permanecer intacta.

Capturas da aplicação usam interceptação de API exclusivamente no navegador para observar a composição existente; não comprovam backend, autenticação real ou transições operacionais. Dados demonstrativos do export permanecem identificados como tal. Equipamento, SLA e ownership ausentes não serão inventados. V01 global, V02–V07 e paridade visual continuam pendentes.

Evidência e cobertura desta parte: [inventário da Cozinha](../../docs/design/v01-kitchen-inventory.md) e contrato `prototype/references/kitchen/visual-contract.json`. Só marcar verificações com captura ou medição registrada; extensões sem referência são enumeradas separadamente.

## Recorte V02 — Field e StatusBadge Web (09/10/2026)

Comparar o Field `.inp`/`.fld` do export atualizado de Atendimento com o Field do Quick Catalog de Cozinha e Bar. Promover apenas medidas comprovadas em uma variante confortável compartilhada; o Field compacto existente mantém seu contrato. Preservar autocomplete, validação, foco visível e API.

StatusBadge deve ser inventariado por equivalência semântica: `.badge` do Atendimento é contador, `.rel`/`.casa` são relacionamento e NOVO é etiqueta de pedido. Nenhum deles autoriza mudar indisponibilidade para atraso ou redesenhar os badges de disponibilidade. Ausência de equivalente deve ser registrada, sem alegação de paridade. V02 completa e Compose permanecem fora deste recorte.

Evidências deste recorte: [Field / StatusBadge](../../docs/design/v02-field-status.md). A variante confortável foi verificada somente no controle e nos labels descritos; não declara equivalência de tela completa.

## V03 parcial — fixture equivalente da Cozinha

Este recorte entrega somente dados/harness de teste e documentação, sem mudar a aplicação. Um cenário comum gera DTOs reais e normalização de dados do export atualizado. Produtos, quantidades, estados e timestamps são compartilhados; resumo inclui apenas NEW/ACCEPTED/PREPARING, passe apenas READY e retirada PICKED_UP separada. Fixture não é seed, fallback de produção ou prova de API real.

Preservar o export literal e registrar toda derivação em [contrato da fixture](../../docs/design/v03-kitchen-comparison-contract.md). Comparação de tela mede divergências, não aceita fidelidade total: composição/metadata sem campos canônicos continuam pendências V04. Limites e gates existentes permanecem intactos.

Resultado do recorte V03: [comparação e diferenças](../../docs/design/v03-kitchen-comparison.md). V03 global e fidelidade total continuam pendentes.

## V04 parcial — agrupamento visual dos tickets da Cozinha

A fila passa a reunir OrderItems de um mesmo `order_id` em um bloco de pedido, com destino/Tab exibido uma vez, preservando cada item, customização, estado, tempo e botão de transição. Sem `order_id`, manter bloco independente por `item.id`; não agrupar por nome de produto ou rótulo da Tab. O grupo segue a primeira ocorrência na fila recebida; itens seguem sua ordem recebida.

Agrupamento é somente visual: cada mutation continua no endpoint de um único OrderItem, com payload/guardas atuais. Um item pronto sai da fila sem concluir os demais. Não adicionar mutation coletiva, dados de cliente/localização/equipamento/SLA, nem copiar barras ilustrativas do export. Cozinha e Bar compartilham ProductionBoard e devem permanecer consistentes.

Referência e fixture V03 permanecem intactas. Este recorte mede agrupamento, geometria e ações individuais; a diferença dos dois botões reais de P08 contra um botão ilustrativo do export permanece explícita. V04 completa e equivalência integral continuam fora do aceite parcial.

Resultado do recorte: [relatório V04 parcial](../../docs/design/v04-kitchen-tickets.md). V04 global permanece aberta.

## V05 parcial — navegação do Atendimento

Navegação canônica de 84 dp com região central de 136 dp em 390 dp; seleção semântica e callbacks atuais preservados. Mesas/Caixa seguem acessíveis em extensão identificada, sem inventar dados.

Contrato: [V05](../../docs/design/v05-atendimento-shell-contract.md). V05 global permanece aberta.

Resultado: [relatório parcial](../../docs/design/v05-atendimento-shell.md), sem baseline nativa total aprovada.

## Continuação — integração e navegação acessível

Completar navegação nativa em 360/390/430 dp e font scale 1/2, sem clipping de texto nem targets abaixo de 44. Caso fonte ampliada comprove overflow, adaptar apenas a barra: ícone Pedir acima do texto e altura de 112 dp acima de fontScale 1.3; layout canônico 390/fontScale1 continua 84 dp e não muda. Preservar todos os callbacks e estado busy.

Descoberta na fixture 360 dp/fontScale2: CONTAS quebra e labels têm overflow. Para fonte ampliada, centro adapta para 104 dp e barra 112 dp; laterais ganham largura, Pedir usa ícone acima, label lateral lineHeight 16 sp. Centro 136 e altura 84 permanecem em fontScale normal; captura canônica deve permanecer idêntica.

## V02 parcial — hierarquia da Gerência e ícones operacionais (09/10/2026)

Retomar em base isolada main9b8e5e5. Gerência não possui export equivalente entre as cinco referências023: este recorte é uma extensão explícita de composição usando o design system, sem alegar equivalência completa. Corrigir seis links em cinco colunas: manter Agora/Operação/Vendas/Gestão/Mais na barra, mover Impressoras para Mais mantendo seu destino.

Navegação usa ícone24px + texto e marcador ativo3px; o ícone Agora reutiliza exatamente o SVG do export night. Outros pictogramas são extensões vetoriais semânticas locais, com o mesmo stroke2.2/round; não são ProductIcon e não geram assets por IA. Cabeçalhos das seções reusam sectionHeader, com ícone20px e título. Exposição em aberto ganha hierarquia em uma região financeira de largura total, número34px e tokens money existentes. Contadores permanecem menores e sem mudar fatos/cálculos. Exceções continuam antes do pulso.

Profundidade é restrita ao limite da barra e à região financeira, com token semântico de sombra discreta e borda; não copiar sombra de moldura/artboard nem criar gradiente/glassmorphism. Preservar loading/erro/vazio, snapshots, capabilities e ações. APIs, Android, pagamentos e páginas completas restantes ficam fora desta slice.

Comparação do ícone isola posição e fundo somente nos espécimes durante o teste: ambos SVGs em (0,0), fundo surface-1/g1 equivalente. Capturas literais em coordenadas fracionadas distintas deram14.72%; posicionamento comum deu0%. Geometria, stroke, cor, export original e limiar0.1% permanecem. Esse resultado não mede a barra inteira ou fidelidade da Gerência.

## Continuação — acabamento compartilhado de todas as telas Web

Aplicar o vocabulário já aceito na Gerência às superfícies Web existentes: entrada/sessão, Atendimento, PDV, Bar/Cozinha, Cliente, Caixa, Gerência e subpáginas de catálogo/preços/impressão/alertas, relatórios, estornos, recibo e documento histórico. Não criar ações/dados/rotas. Títulos conservam nível, texto, id, foco e nome acessível; ícones decorativos distinguem contexto operacional sem substituir ProductIcon ou rótulo. Hierarquia título/seção/subseção, bordas e sombras funcionais usam tokens. Estações conservam composição de lote/fila/passe e SVGs literais existentes; destaque de quantidade/destino/estado não muda transições. Impressos canônicos e HTML histórico no iframe permanecem intocados; só a moldura Web recebe acabamento. Nenhum contrato de API, regra financeira, autenticação ou auditoria muda. Não declarar paridade integral nas superfícies sem export. Android depende de confirmação de escopo e validação nativa própria.

V06: perda real da API revelou SSE Reconnecting substituindo OFFLINE; o contrato e verificação da menor correção estão na Spec014. Manter SEM SINAL até leitura confirmada, sem executar/confirmar cobrança offline.


## Evidência da demo atual

[Relatório](../../docs/design/spec023-demo-validation.md) discrimina gates/artefatos e limites atuais. Núcleo da demo passou Web/PostgreSQL e UI Android real até fechamento de Tab/caixa de teste, incluindo OFFLINE/recovery. Paridade integral e todas jornadas internas ampliadas continuam fora do aceite comprovado; não declarar Spec023 concluída.

## V02/V05 — catálogo e cobrança com fonte ampliada

Verificar os componentes reais com instrumentação360/390/430 e fontes1/2 antes da correção. Linha de produto deve conservar nome completo, preço canônico em centavos, rota/disponibilidade e ação atual; não aceitar ellipsis ocultando identidade nem preço sem largura. Se confirmado clipping, nome e preço ganham linhas próprias nos tokens existentes. Diálogo de pagamento mantém decisões e footer/callbacks/busy, mas conteúdo longo deve permitir rolagem interna e preservar acesso às advertências/caixa/valor com fonte200%. Não alterar métodos, regras financeiras, provider ou confirmação offline. Extrair somente o botão de produto e tornar PaymentDialog interno para teste do componente de produção. Aceite: nomes sem ellipsis/clipping, preço legível; advertência acessível; caixa fechado não confirma; caixa ativo repassa exatamente300centavos/mesmo método/ponto; matriz nativa atual e screenshots. Paridade visual global continua aberta.

Baseline360/font200 comprovou dois erros: nome de produto ellipsized e preço em coluna de caracteres; pagamento cortou métodos/advertências e footer sobreposto. Em fontScale>1.3 (mesmo limiar da navegação), footer da cobrança empilha confirmar/cancelar em largura total, gap8 existente; fonte normal conserva disposição. Conteúdo sempre rolável, sem alterar flags/decisões.

V05 login: verificar a tela real com fonte200% e teclado. Se conteúdo exceder viewport, permitir rolagem apenas na variante ampliada (>1.3, limiar existente), conservando geometria normal, campos/trim/PIN clearing/busy e callback de autenticação. Teste usa fixture somente em androidTest e captura antes de digitar PIN; não mudar política de autenticação ou persistência.

Resultado login: sem teclado a tela360/font200 já cabe; não alterar sua composição por hipótese. Com IME real aberto, captura confirma PIN/Entrar cortados e ausência de rolagem. Adaptação final habilita rolagem somente quando WindowInsets.ime>0, em todas as fontes; sem IME conserva layout central existente. Artefato login-before registra apenas a falta do recurso de scroll no teste inicial; login-keyboard-before é a prova de clipping efetivo.

Resultado atual do recorte crítico Android: catálogo, pagamento e login com IME real corrigidos; 51unit/build/lint e48 testes instrumentados (8×6) aprovados, zero skips. 36 capturas adjacentes permanecem idênticas. [Critérios, reprodução, evidências e limites](../../docs/design/spec023-critical-fields.md). Critérios globais de paridade/jornadas internas/hardware/provider permanecem abertos.
