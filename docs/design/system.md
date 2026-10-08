# Rodada Design System

Este documento é a fonte de verdade visual e de interação para todas as superfícies do Rodada.

O objetivo não é criar uma biblioteca bonita por si só. O sistema existe para manter **PDV, Cozinha/Bar, Dispatch, Conta da Casa e Guest Ordering** reconhecíveis como o mesmo produto durante operação de bar cheio.

## Princípios

1. **Operacional antes de ornamental.** Informação acionável deve ganhar de decoração.
2. **Uma semântica, várias superfícies.** Cor, estado, botão e hierarquia significam a mesma coisa em todos os módulos.
3. **Mobile-first real.** O baseline é 360–430 px, uso com uma mão, movimento e baixa atenção disponível.
4. **Densidade controlada.** Staff pode ter mais informação por tela; guest recebe menos opções e mais orientação. Os componentes continuam os mesmos.
5. **Pico é o estado principal.** Nada essencial deve depender de hover, gestos escondidos ou leitura longa.
6. **Estado nunca depende só de cor.** Badge, texto ou ícone sempre acompanha a cor.
7. **Sem “SaaS genérico”.** Evitar glassmorphism, cards decorativos, dashboards de vaidade, gradientes sem função e navegação de ERP.
8. **Dinheiro e risco têm hierarquia própria.** Saldo, exposição, limite, pagamento e bloqueio devem ser legíveis em um relance.
9. **Touch primeiro.** Alvos interativos devem ter pelo menos 44 px; ações principais preferem 48–52 px.
10. **Português operacional.** Rótulos curtos, concretos e orientados à ação.

## Linguagem visual

Rodada usa uma estética de bar noturno: neutros quentes, contraste alto e acento tungstênio/âmbar.

A identidade deve parecer robusta, rápida e humana — não fintech fria nem software corporativo.

### Tokens de cor

Use tokens semânticos; não use hex diretamente em componentes de produto.

| Token | Uso |
| --- | --- |
| `--color-bg` | fundo geral |
| `--color-surface-1` | superfície principal |
| `--color-surface-2` | superfície elevada/controle |
| `--color-border` | divisores e bordas |
| `--color-text` | texto principal |
| `--color-text-muted` | metadado/apoio |
| `--color-accent` | seleção, trabalho pendente e marca Rodada |
| `--color-success` | disponível, pronto, confirmado |
| `--color-danger` | indisponível, erro, bloqueio, atraso crítico |
| `--color-info` | informação, claim/ownership e estado neutro ativo |
| `--color-warning` | atenção operacional, preparando, limite próximo |

### Semântica de estado

A mesma semântica vale em todo o produto:

- **neutral** — existe, mas não requer atenção;
- **info** — ativo/assumido/em andamento sem risco;
- **warning** — atenção ou trabalho pendente;
- **success** — pronto, disponível, confirmado, concluído;
- **danger** — bloqueado, indisponível, erro, vencido ou ação destrutiva.

Não reutilizar `success` para “da casa” ou `danger` para decoração.

## Tipografia

Archivo variável (peso 400–900, largura 62–125%) é a fonte do produto. JetBrains Mono é usada para quantidades, tempos e valores. Ambas são locais e licenciadas sob OFL. Prioridades:

- títulos curtos e pesados;
- números financeiros com peso forte e `font-variant-numeric: tabular-nums`;
- metadados em caixa alta apenas quando funcionarem como label operacional;
- corpo nunca menor que 14 px em informação importante;
- evitar blocos longos de texto em telas operacionais.

### Referência aprovada em 08/10/2026

Os cinco HTMLs fornecidos pelo usuário estão preservados em `prototype/material-reference`; a spec 022 adota sua identidade. Tokens canônicos: fundo `#120F0C`, estação `#0A0806`, passe `#100D0A`, superfícies `#1B1713 / #252019 / #312A21`, bordas `#3A3228 / #4D4335`, papel `#F3ECE1`, apoio `#BBAE9B`, sutil `#A39686`, ink `#17130F`, âmbar `#F5A524`, success `#93DB8C`, danger `#FF5D47`, info `#82B8FF`, financeiro `#C3A6FF`.

Button primário usa papel/ink, altura 56px, raio 8px, Archivo 18px/850 com largura 84%, uppercase e tracking .06em; sombra interna inferior de 4px a 20%. Seleção continua âmbar. Badge e chip usam raio 4px. Painéis usam raio 12px; filas usam divisórias e não cards individuais. Cabeçalho operacional desktop usa 72px. Títulos de estação usam 38px/900 e largura 66%; pratos 44px/900 e largura 64%; quantidades 52px/800 mono. Mobile reduz títulos quando necessário, preservando nomes completos e alvos 44px.

Contadores financeiros nunca recebem a cor de atraso apenas por representar dinheiro. A identidade visual não autoriza inventar SLA, responsável, equipamento, cliente ou sucesso de sincronização.

Escala base:

- `--text-xs`: 12 px
- `--text-sm`: 14 px
- `--text-md`: 16 px
- `--text-lg`: 20 px
- `--text-xl`: 28 px
- `--text-2xl`: 34 px

## Espaçamento e forma

Escala base: 4, 8, 12, 16, 24, 32 px.

- `--radius-sm`: controles compactos;
- `--radius-md`: botões, badges e linhas;
- `--radius-lg`: painéis;
- `--radius-pill`: status/chips.

Não criar um novo raio, sombra ou espaçamento para cada feature.

## Componentes canônicos

### AppShell

Container da superfície. Define largura, safe area e padding. No mobile de staff, prioriza 360–520 px; no desktop pode expandir sem alterar hierarquia.

### ProductHeader

Marca + contexto do ambiente. Ex.: `RODADA / PILOTO`, venue, turno ou status online.

### SurfaceNav

Navegação entre grandes superfícies. Deve comunicar claramente qual módulo está ativo.

### SectionHeader

Título, eyebrow/metadado e ação/status opcional. Mesma estrutura em PDV, cozinha, dispatch, house e guest.

### Panel

Superfície agrupadora. Só usar quando os itens dentro realmente pertencem ao mesmo contexto.

Variantes:
- `panel--default`
- `panel--accent`
- `panel--warning`
- `panel--success`
- `panel--danger`

### DataRow

Linha de informação ou item acionável. Tem label, supporting text e trailing value/status.

### Field

Campos de criação/edição usam uma estrutura única: label, controle, hint/erro opcional.

### CatalogCombobox

O nome do produto no Quick Catalog não é um campo livre isolado: é autocomplete do catálogo do Venue.

Estados mínimos:

- query vazia;
- buscando;
- resultados existentes;
- correspondência exata existente;
- sem correspondência exata + ação **Criar "{nome}"**;
- item selecionado.

Resultado existente deve mostrar, quando útil, ProductIcon, nome, preço, estação e disponibilidade. Selecionar um resultado reutiliza o Product e o ProductIcon existentes.

Fuzzy match serve para sugerir; nunca deve parecer que itens parecidos serão mesclados automaticamente.

- input deve ter alvo de toque mínimo de 44 px;
- preço usa entrada numérica apropriada e valor em centavos no domínio;
- estação herdada pode ser exibida como contexto read-only em vez de campo editável;
- erro e loading devem aparecer junto ao campo/ação, não apenas em toast.

### ProductIcon

Componente visual compartilhado para o asset publicado de Product.

- canvas 1:1;
- placeholder consistente quando não existe asset;
- novo Product cria seu ProductIcon 1:1 e inicia geração automaticamente quando não houver upload manual;
- `GENERATING` mantém placeholder/asset anterior e mostra estado separado;
- `FAILED` não torna o produto indisponível nem bloqueia venda;
- `UNAVAILABLE` é estado da UI/catalog, não deve ser gravado no asset;
- o asset segue `docs/product/icon-style.md` (`rodada-icon-v1`), enquanto borda, raio, seleção e estados pertencem ao componente da UI.

### Button

Hierarquia fixa:

- `button--primary`: próxima ação principal da tela;
- `button--secondary`: ação segura alternativa;
- `button--quiet`: navegação/ação de baixa ênfase;
- `button--danger`: ação destrutiva ou bloqueio explícito.

Uma região não deve ter vários botões primários concorrendo.

### StatusBadge

Sempre combina texto + cor semântica. Exemplos:

- DISPONÍVEL → success
- PREPARANDO → warning
- PRONTO → success
- INDISPONÍVEL → danger
- BLOQUEADO → danger
- ASSUMIDO → info
- PENDENTE → warning

### Metric

Valor + label + supporting text opcional. Usado para saldo, exposição, fila, visitas e tempos.

### MoneyValue

Valor financeiro em destaque. Sempre usa números tabulares e contexto textual: `aberto`, `exposição`, `recebido`, `limite`.

### WorkCard

Unifica cartões operacionais de pedido/task/run. A diferença é o domínio, não o layout base.

Estrutura:
- kicker/contexto;
- título;
- status/time;
- itens ou metadados;
- próxima ação.

### EmptyState / InlineNotice / Toast

Feedback curto, operacional e acionável. Nunca depender apenas de `alert()` na implementação real.

## Mapeamento por superfície

### PDV

Prioridade: **Tab → pedido → total → próxima ação**.

- cabeçalho mostra contexto da Tab e localização atual;
- saldo/exposure aparece como Metric/MoneyValue;
- pedido usa WorkCard;
- disponibilidade usa StatusBadge e estado disabled;
- pagamento/fechamento é ação primária contextual.

### Cozinha / Bar

Prioridade: **fila de produção + disponibilidade da estação**.

No Web, nomes longos podem ocupar várias linhas: conteúdo e ações usam duas
linhas no celular e colunas quando houver espaço. Sem truncar o produto ou
reduzir o alvo de toque. A fila e o passe ficam antes do aviso compacto de
Quick Catalog indisponível enquanto Spec 005 não estiver conectada. Esse aviso
não contém formulário de criação aparentemente funcional.

Quick Catalog usa os mesmos componentes da superfície: Button, Field, CatalogCombobox, ProductIcon, StatusBadge e InlineNotice. Não existe botão obrigatório de “Gerar ícone”: ao criar Product novo, o ProductIcon nasce junto e a geração começa automaticamente. Criar item não deve parecer um mini-app separado dentro da cozinha.

- item indisponível usa danger;
- item pronto usa success;
- preparando usa warning;
- mudança de disponibilidade usa Button secundário/danger conforme ação;
- pedidos já confirmados continuam visualmente válidos.

### Dispatch

Prioridade: **o que precisa acontecer agora**.

- tempo em aberto deve ser escaneável;
- claim/ownership usa info;
- pronto para retirada usa success;
- atraso real pode escalar warning → danger;
- runs usam o mesmo WorkCard, com agrupamento de destinos.

### Conta da Casa

Prioridade: **exposição + limite + recebimento + histórico**.

- relacionamento `HOUSE` não deve sequestrar a cor de success;
- exposição próxima do limite usa warning; acima do permitido usa danger;
- pagamento confirmado usa success;
- override de limite é ação separada e auditável.

### Table Ops

Prioridade: **estado físico da mesa**.

Mapeamento recomendado:

- `AVAILABLE` → success / “Disponível”
- `OCCUPIED` → info / “Em uso”
- `DIRTY` → warning / “Suja”
- `CLEANING` → info / “Em limpeza”
- `OUT_OF_SERVICE` → danger / “Fora de serviço”

A transição de limpeza deve usar os mesmos Button, StatusBadge e WorkCard.

### Guest Ordering

Usa a mesma identidade, mas menor densidade:

- navegação mínima;
- contexto da mesa visível;
- comanda resolvida antes de expor ações financeiras;
- cards de produto usam tokens e estados iguais aos do staff;
- item indisponível permanece visível, porém não confirmável;
- status do pedido reaproveita a semântica operacional;
- CTA primário único por etapa.

### Gerência

Prioridade durante o serviço: **exceção → contexto → próxima ação → pulso da operação**.

Gerência é mobile-first de verdade:
- baseline 360–430 px;
- bottom navigation: **Agora / Operação / Vendas / Gestão / Mais**;
- números grandes e poucos por viewport;
- um gráfico por contexto no celular, não mosaico de mini-gráficos;
- alertas acionáveis aparecem antes de analytics histórico;
- mapa 2D é drill-down de Mesas/Ambientes, não a home;
- timeline usa DataRow e filtros simples;
- “Ver só problemas” reduz ruído durante o pico.

A home **Agora** deve reutilizar `Metric`, `MoneyValue`, `Panel`, `DataRow`, `StatusBadge` e `InlineNotice`. Evitar criar cards decorativos apenas para “encher dashboard”.

Divergências de caixa e estornos pendentes aparecem antes do pulso operacional.
Antes do primeiro snapshot confirmado, mostrar carregamento ou erro, sem números
que aparentem zero medido. Falha de atualização preserva o último snapshot com
aviso explícito. Rodapé discreto usa texto muted de 12 px, link com alvo de 44 px
e espaço suficiente para não ficar atrás da navegação ou carrinho fixos.

Durante operação, Gerência funciona como cockpit. Fora do pico, a mesma superfície pode aumentar densidade para fechamento e analytics.

Estados de conectividade precisam ser explícitos:
- realtime saudável;
- atualizando;
- stale;
- offline.

Métricas de equipe podem apoiar diagnóstico, mas o design não deve gamificar nem criar leaderboard simplista de velocidade/performance.

## Estados interativos

Todo controle deve cobrir:

- default;
- pressed/active;
- focus-visible;
- disabled;
- loading quando aplicável.

Hover nunca pode ser requisito funcional.

## Acessibilidade

- contraste suficiente para texto e status;
- foco visível;
- botões com label textual;
- ícones complementam, não substituem o significado;
- targets mínimos de 44 px;
- respeitar `prefers-reduced-motion`;
- não comunicar indisponibilidade apenas reduzindo opacidade.

## Responsividade

### 360–430 px

Baseline do produto. Ações principais ocupam largura útil quando isso reduz erro.

### 431–767 px

Pode aumentar respiro e usar grids de duas colunas para métricas.

### 768 px+

Pode usar layout split para operação, sem transformar cada módulo em dashboard diferente.

## Regras para implementação

1. Componentes novos devem consumir tokens semânticos.
2. Não adicionar hex, radius ou spacing ad hoc sem atualizar o sistema.
3. Estado de domínio deve mapear para variantes semânticas compartilhadas.
4. Novos módulos devem reutilizar componentes antes de criar novos.
5. Se um padrão aparecer duas vezes, considerar promovê-lo a componente.
6. Protótipos devem usar o mesmo vocabulário visual do app real.
7. Assets de catálogo gerados por IA seguem `docs/product/icon-style.md`; o design system governa como esses assets aparecem e interagem na UI.
8. Quick Catalog deve buscar/autocompletar antes de criar; Product existente reutiliza ProductIcon existente e Product novo inicia geração automaticamente.
9. Mudanças que alterem comportamento continuam exigindo spec; este documento governa UI/UX transversal.
10. Design review deve checar consistência entre superfícies, não só a tela isolada.

## Referência executável

O protótipo em `prototype/index.html` consome `prototype/design-system.css` e serve como referência visual inicial.

Ele não é a implementação final do frontend, mas mudanças visuais de alto nível devem primeiro preservar este contrato para evitar drift entre protótipo, Codex/Claude e o futuro app Next.js.

## Implementação Web — Spec 020

Quick Catalog combina Field, CatalogCombobox, ProductIcon, StatusBadge/semântica de estado e Button. Resultados mostram preço, destino e ativação/disponibilidade; selecionar reutiliza o produto. Criação é ação explícita com preço e destino, após a busca. Ícone de fallback usa as iniciais no mesmo espaço do asset e não representa disponibilidade. A fila de produção continua antes do cadastro.

Relatórios seguem o mesmo padrão de Field para datas, Button para consulta/CSV, Panel para grupos de fatos e estados semânticos para conferência/divergência. Valores históricos e exposição atual são rotulados separadamente. Histórico de caixa usa seletor com data/estado e retorno explícito ao turno ativo; consultar histórico não altera estado financeiro. Todas as superfícies mantêm foco visível, targets 44 px e tokens existentes. Ver [Spec 020](../../specs/020-web-operational-completion/spec.md).

## Hierarquia operacional — Spec 021

Na estação, fila e passe precedem disponibilidade/cadastro. `SectionHeader` combina título e contagem de linhas do snapshot; loading/erro inicial não recebem contagem zero. Nomes/quantidades de produção usam `text-lg`, sem truncar contexto. A partir de 768 px, `AppShell` da estação expande até 1280 px e apresenta fila/passe em duas colunas; mobile conserva a mesma ordem em coluna única. Escalas, cores e controles existentes permanecem.

Gerência apresenta exceções, pulso e produção antes dos formulários de relacionamento/políticas. Conta da Casa permanece em Gestão, após caixa/salão. Rótulos operacionais usam português; itens prontos não contam como "em preparo". Revisão adjacente: Bar/Cozinha/produção gerencial e Caixa/Gestão.
