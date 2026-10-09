# Plano de paridade visual com os protótipos atualizados

Data: 2026-10-08. Estado: planejamento, implementação pendente.
Contrato: [Spec 023](../../specs/023-updated-prototype-visual-parity/spec.md).

## Objetivo e definição de pronto

Reproduzir os cinco protótipos atualizados no produto real, incluindo composição, densidade, tipografia, ícones, hierarquia, dimensões e estados interativos. Compartilhar paleta é apenas o início. O plano de produto 022 continua contexto funcional; este documento é a sequência de implementação da fidelidade visual solicitada.

Pixel-perfect significa comparar **a mesma tela, os mesmos dados, o mesmo estado e as mesmas dimensões**, com rasterização controlada. No Web, exigir geometria correspondente e no máximo 0,1% de pixels divergentes no conteúdo equivalente, com parâmetros fixos de comparação e revisão do diff. Zero diferença continua o objetivo; 0,1% é tolerância técnica, não orçamento para redesenhar. Nenhuma região crítica pode diferir estruturalmente mesmo se a média da tela passar.

Android e Chromium rasterizam texto de modo diferente. Validar Android contra o HTML por geometria, cores, tipografia e composição; depois bloquear regressões por screenshots nativas no mesmo emulador. Não prometer igualdade binária de texto entre plataformas nem usar tolerância global ampla para escondê-lo. Documentar diferenças de rasterização por região; não excluir blocos inteiros de texto.

## Estado atual — o que ainda não é pixel-perfect

- Tokens/fontes locais e tema Android foram integrados na Spec 021.
- Um botão atualizado de produção mediu 0 pixels diferentes. As sete primitives legadas também têm gates, mas não comprovam correspondência com todas as primitives novas.
- Cozinha atual versus export atualizado em 1280 × 800 mede **11,2106%** de diferença. O teste gera auditoria e não falha por essa diferença.
- Atendimento Android ainda não reproduz a composição/jornada visual dos telefones do export.
- Screenshots repetidas do produto comprovam estabilidade; sem confronto com a referência, não comprovam fidelidade.

Não promover os screenshots atuais do produto a baseline de aprovação. A fonte de comparação são os exports identificados por hash no [manifesto](../../prototype/references/manifest.json).

## Matriz de referências e recortes

| Referência executável | Alvo a reproduzir | Recorte e estados | Destino |
| --- | --- | --- | --- |
| `night/Main.dc.html` | Telefones de atendimento e painel operacional presentes no export | `.phone` de 390 × 844; inventariar cada estado navegável do fluxo, inclusive contas/pedido/cobrança/overlays | Android Atendimento; painel Bar onde correspondente |
| `system/Sistema.dc.html` | Componentes e composição tipográfica atualizados | Cada espécime com limites próprios e tamanho original, não a página de apresentação inteira | Design system Web/Compose |
| `kitchen/Cozinha.dc.html` | Resumo, tickets, passe, cabeçalho/divisórias e ações | Conteúdo `.k`; começar pela captura existente 1280 × 800 e medir dimensões reais do root antes de fechar o contrato | Web Cozinha; Bar reutiliza a composição quando equivalente |
| `peak/Pico.dc.html` | Header, contadores, filas de prioridade e navegação em pico | `.ph`, 390 × 844, estado demonstrado; inventariar outros estados se houver | Android Atendimento |
| `connectivity/Offline.dc.html` | Banner, pending, feedback e recuperação | `.ph`, 390 × 844; estados sem sinal, reconectando e sincronizado disponíveis | Android; Web usa os componentes equivalentes onde aplicável |

Caminhos relativos à [galeria importada](../../prototype/references/index.html). V01 deve registrar selector único por instância/estado, porque `.phone` pode selecionar vários aparelhos. Capturar conteúdo de produto; rail de apresentação, moldura externa, sombra do mockup e legendas do artboard não entram na UI. Status bar desenhada e safe areas precisam classificação explícita: comparar app-content separadamente e validar chrome do sistema no Android, sem duplicar uma barra real com barra fake.

Telas Guest, Gerência, caixa e demais estados sem referência correspondente não podem receber selo de pixel-perfect por analogia. Reutilizar os componentes aprovados e criar referência complementar versionada antes de exigir equivalência completa dessas telas. Não adaptar um screenshot de Atendimento para justificar outra superfície.

## V01 — Congelar o contrato de comparação

Criar inventário versionado, por exemplo `prototype/references/visual-contracts.json`, com reference ID/hash, entry, selector, sequência de interação, viewport, crop, fixture ID, estado, fonte/tamanho/peso/axis, destino e exceções. Preservar ZIPs e HTMLs importados; novos contratos não alteram o original.

Abrir cada export e capturar todos os estados relevantes: navegação, comanda selecionada, busca, carrinho, revisão, cobrança/aprovação, filas, pico e conectividade. Registrar estado inicial e como alcançá-lo usando interações determinísticas. Catalogar limites e texto real em vez de adivinhar a partir de uma imagem.

Saída: capturas PNG de referência, mapa de estados, bounding boxes das regiões e relatório de medidas. Fechar dimensões e insets antes de escrever CSS/Compose. Estados inexistentes no export ficam identificados como extensão, não referência literal.

## V02 — Extrair medidas e fechar o design system

Medir `getComputedStyle` e `getBoundingClientRect` no export: layout/grid, largura de coluna, padding/gap, altura de linha/controle, borda, radius, shadow, posição de texto, line-height, letter-spacing, uppercase, font-weight e font-stretch. Classificar valores repetidos em tokens semânticos e variantes de componente em [system.md](system.md).

Dar atenção a Archivo variável: peso correto sem condensação correta muda largura, quebra de linha e densidade. Registrar `wdth`/`wght`, verificar seleção da fonte e ausência de fallback; não simular condensação com `transform: scaleX`. JetBrains Mono é usada nos números/tempos específicos da referência, não indiscriminadamente. Não derivar line-height de defaults do browser ou Material.

O export de pico, por exemplo, usa ação de 60 px, enquanto o sistema possui ações de 56/68 px. Resolver como variante semântica documentada quando necessária; não forçar todas as referências a uma medida única. Resolver também tokens divergentes entre exports em uma tabela de decisões: fidelidade literal daquela variante ou correção complementar aprovada e versionada, nunca alteração silenciosa do original.

Definir os componentes necessários: header, navegação inferior, linha operacional, contador, age, destino, Tab/relationship badge, dinheiro/limite, ticket, resumo de preparo, item de passe, ProductIcon, CatalogCombobox, botões, field, banner de conexão e pending row. Cada componente recebe estados normal/selecionado/disabled/loading/error conforme referência e comportamento real.

Saída: tabela fonte→token→componente Web/Compose, specimens executáveis e comparação estrita de cada primitive atualizada. Não adicionar hex/spacing ad hoc nas telas.

## V03 — Preparar fixtures realmente equivalentes

Usar um modelo de fixture comum para os textos, quantidades, preços, destinos, avatares/ícones, flags, timestamps e estados exibidos. Adaptar esse modelo para os DTOs reais e para o estado da referência no harness de teste. Fixture visual pode simular dados; produção continua usando API. Não inserir IDs/nome de cliente demonstrativo como regra do produto.

Fixar relógio, locale, timezone, viewport, DPR, fontes e ordem dos itens. Esperar fonts/images/network e o estado esperado; desabilitar animações/caret apenas no harness. Fixar timers nas mesmas idades. Usar os mesmos assets quando licenciados; assets não disponíveis exigem decisão explícita antes do aceite, porque um ícone diferente altera pixels.

Na cozinha há inconsistência entre números demonstrativos do resumo e os tickets. Registrar o screenshot literal como evidência preservada, mas comparar a tela com um estado coerente: alimentar referência e produto com o mesmo conjunto de itens no harness, ou separar regiões de resumo/tickets em contratos coerentes. Nunca fabricar total incorreto na aplicação nem esconder o resumo com mask. Identificar a referência normalizada como fixture derivada, com transformação e motivo versionados.

Também distinguir visualização de comportamento: incluir loading/erro/retry reais sem fingir confirmação de pedido/pagamento offline. Quando o demo mostra ação incompatível com estados canônicos, preservar composição e adaptar rótulo/estado numa referência derivada identificada. Exceções devem ser pequenas, enumeradas e visíveis no relatório; um layout inteiro diferente continua pendente.

## V04 — Refazer a composição Web da cozinha

Começar pela maior diferença já medida. Ajustar de fora para dentro:

1. Root, conteúdo do header, margens e altura útil; separar navegação/auth do produto da região equivalente quando a referência não as contém.
2. Grid: larguras relativas/exatas das três regiões no tamanho canônico, divisórias e alinhamento vertical.
3. Resumo: escala do nome/quantidade, espaçamento, separadores, chips e metadados.
4. Tickets: agrupamento visual, bordas, destino/idade, linhas de item, quebras e ações.
5. Passe: estrutura de linhas, timer, destino, ownership quando dado real existir e ação autorizada.
6. Ajustes finos: axes da fonte, baselines, tracking, stroke de ícone, border/shadow.

Usar `production-board.tsx` e CSS existentes como implementação real, extraindo componentes semânticos onde útil. Não copiar a tela inteira como HTML estático, não substituir por imagem e não criar rota de teste com UI diferente da produção. O harness altera dados/relógio, não classes/layout.

Dados ausentes de equipamento/capacidade/ownership não podem ser inventados na produção. V01/V03 devem decidir o contrato: entregar campos canônicos sob spec de domínio, estado desconhecido documentado ou referência derivada explícita. Enquanto a diferença não for resolvida, a região não tem equivalência completa. Quick Catalog e disponibilidade continuam acessíveis sem dominar a composição; definir onde ficam no produto e comparar essa extensão separadamente.

Saída: comparação da cozinha deixa de ser auditoria permissiva e vira assertion; repetir em Bar com fixture e referência equivalentes. Preservar testes de transição individual e disponibilidade.

## V05 — Reproduzir Atendimento em Compose

Implementar shell, insets, header, bottom nav e regiões do telefone antes das telas internas. Mapear 390 CSS px para 390 dp de conteúdo como contrato de layout; capturar emulador com densidade conhecida e documentar conversão física. Não redimensionar arbitrariamente uma imagem para parecer equivalente.

Configurar fontes variáveis com suporte da plataforma e fallback verificado na API mínima. Medir `fontPadding`, baseline, lineHeight, letterSpacing, largura da glyph e rounding dp→px. Evitar tamanhos, paddings, ripple, elevations e altura mínima implícitos do Material quando diferirem da referência; preservar acessibilidade e alvo de toque.

Entregar em slices: Agora → Contas/busca → detalhe Tab → Pedir/carrinho/revisão → cobrança/limite/aprovação → overlays e erro. Usar os mesmos componentes em Pico e recovery, sem criar outra identidade visual. Separar visual state de service/API: componentes recebem estado tipado, e navegação/comandos reais permanecem conectados. Previews usam fixtures; screens reais usam os mesmos composables.

Criar instrumentação/screenshot tests no emulador fixado. Comparação HTML→Android gera overlay e relatório de geometria por região. Baseline nativa só entra após revisão lado a lado com referência, não após gerar imagem do app atual. Verificar também device físico, teclado, fontes ampliadas e safe areas; esses cenários validam adaptação/acessibilidade, não igualdade ao telefone de 390 px.

## V06 — Pico e conectividade

Reproduzir a tela de pico no mesmo shell: contadores, row grid, largura do age/destino, linhas, prioridade e ações. Valores/categorias vêm de estado real; timers/SLA do demo são fixtures, não política global.

Reproduzir cada estado de conectividade com o mesmo banner, spacing e feedback. Capturar transição antes/depois sem animação para confronto; testar a animação separadamente se a referência a define. Texto “sincronizado” só aparece quando o estado canônico confirma a reconciliação. Intenção pendente não vira pedido confirmado para reproduzir a imagem.

## V07 — Gates e relatório de diferenças

Estender a suíte existente em `apps/web/tests/visual/parity.spec.ts`, fixtures e servidor de referência de Playwright. Usar o helper de diff existente como ponto de partida; hoje ele mede com `pixelmatch threshold: 0.1, includeAA: false`. Registrar esses parâmetros e o percentual permitido separadamente; não aumentar nenhum dos dois para passar uma tela.

Para cada contrato gerar reference, actual, diff, overlay 50%, side-by-side e JSON com dimensões, changed pixels/percent, regiões, hash da fonte e versão do ambiente. Verificar bounding boxes e linhas de texto para que a tolerância não esconda deslocamento de 1–2 px numa região pequena. Rodar comparação duas vezes para detectar nondeterminismo. Não usar máscaras abrangentes; exclusão de chrome externo tem recorte explícito, nunca conteúdo operacional.

Fixar ambiente Web no CI (OS/container, Chromium/Playwright, locale, DPR); fixar API/emulador/densidade/font scale nos testes Android. Manter baseline por plataforma quando necessário, com a cadeia de evidência que o liga ao export. Builds diferentes ou Windows/Linux não são prova de regressão percentual entre si.

Na dimensão canônica, igualdade visual é obrigatória. Em 360/430/768 px, criar contratos responsivos derivados com medidas e screenshots versionados antes de exigir pixel-perfect: os artboards fixos não definem esses layouts. Nomes longos, teclado, loading, erro e scroll continuam gates de acessibilidade/layout. Não esticar a screenshot de 390 px para definir responsividade.

Revisão de falha segue ordem: fixture/estado → geometria externa → typography → componentes → pixels finos. Corrigir implementação; só atualizar referência quando a intenção visual mudar explicitamente, com diff e motivo. Manter os ZIPs originais.

## Sequência de PRs e aceite

| Pacote | Arquivos/resultado | Depende de | Aceite |
| --- | --- | --- | --- |
| V01 | Inventário, visual contracts e capturas por estado | — | Todos os cinco exports mapeados; dimensões/crops conhecidos |
| V02 | Design system, tokens e primitives atualizadas Web/Compose | V01 | Geometria/typography documentadas; primitives Web ≤0,1% |
| V03 | Fixture comum, adapters e normalizações explícitas | V01 | Dados/tempo/assets equivalentes; transformações reproduzíveis |
| V04 | Cozinha/Bar conectados com composição fiel | V02/V03 | Full-screen/regiões equivalentes passam assertions, não só geram relatório |
| V05 | Atendimento Compose por slices e screenshots | V02/V03 | Estados do fluxo comparados; baseline nativa aprovada contra HTML |
| V06 | Pico/offline/recovery fiéis e conectados | V05 | Todos os estados de referência cobertos sem mentira operacional |
| V07 | CI, referências responsivas e fechamento do audit | V04/V06 | Gates obrigatórios; nenhum diff estrutural oculto; evidência por superfície |

PRs pequenos por tela/estado: cada PR mostra referência/antes/depois/diff e registra comandos de validação. Mudança Web executa typecheck/build e `npm run test:visual`; Android executa unit/build/lint e screenshots apropriadas. Não exigir terminar todos os módulos de produto para começar V01–V05; quando faltar contrato/API, registrar a dependência de domínio daquele estado específico.

## Atualização da KB e conclusão

[Spec 023](../../specs/023-updated-prototype-visual-parity/spec.md) acompanha execução. Atualizar [audit](visual-parity-audit.md) com cobertura, métricas e diferenças abertas; atualizar [KB](prototype-integration.md) e design system quando promover padrões. Conclusão exige evidência por tela/estado, não apenas uma média de pixels do produto inteiro.

Esta entrega contém o plano. Nenhuma nova fidelidade de tela foi implementada ou medida aqui; 11,2106% é evidência anterior, não resultado novo.
