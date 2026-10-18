# Rodada Design System

Conta Android: resumo em Surface/Border sem elevação, saldo Paper em Number;
detalhes com rótulos Muted e valores alinhados. Ações secundárias agrupadas em
disclosure, avisos críticos sempre visíveis. Histórico preserva nome/subtotal
confirmados e usa ações de texto com alvo48dp. Fonte ampliada empilha valores
e controles. Referência e aceite: Spec029, adendo Conta de 2026-10-17.

Disponibilidade do Bar: ações compactas abrem ActionDialog; categorias/Todos
reutilizam a grade de duas colunas do Cardápio, ProductIcon e botões semânticos.
Produtos rolam dentro do popup limitado à viewport. Confirmação nomeada não
exibe quantidade/carrinho; sucesso canônico retorna foco/rolagem ao início da
estação. Reativação usa o mesmo padrão. Ver Spec026, adendo de 2026-10-17.

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
9. **Touch primeiro.** Alvos interativos devem ter pelo menos 44 px; ações de produção usam 56 px.
10. **Português operacional.** Rótulos curtos, concretos e orientados à ação.

## UX operacional — task-first, padrões transversais (14/10/2026)

**Diretriz de design para propostas e redesigns, não confirmação de implementação.** Aplica-se ao Android nativo, Web/PWA e às demais superfícies com trabalho operacional análogo. A spec relevante define o comportamento do domínio; mudança de jornada precisa ser especificada e validada antes de alterar código. Conservar marca, tokens, permissões e regras financeiras.

### Dez premissas de UX

1. **Tarefa antes da tela:** identificar operador, gatilho, objetivo, contexto, frequência, próxima decisão, custo do erro e recuperação. Mapear normal, vazio, loading, pico, erro, interrupção e reconexão.
2. **Uma tarefa dominante por viewport:** contexto e CTA devem ser visíveis sem procurar; nunca obrigar o garçom a atravessar financeiro, histórico ou controles administrativos para pedir.
3. **Profundidade sob demanda:** detalhamento financeiro, registros longos, filtros raros, limites e operações especiais ficam em contexto, disclosure, diálogo curto ou tela própria; alertas e bloqueios relevantes continuam visíveis.
4. **Scroll é para explorar, não navegar:** listas e catálogos podem rolar, mas abrir, adicionar, revisar, cobrar e voltar não dependem de scroll manual para achar o botão. Preservar filtro/foco/posição ao retornar; evitar rolagem aninhada conflitante.
5. **Reconhecimento antes da memória:** busca, categorias, recentes, nomes legíveis e referências canônicas. Nunca escolher homônimos por nome ou tratar Table como identidade de Tab.
6. **Interrupção é normal:** o operador pode alternar de tarefa, mesa e comanda mantendo rascunhos não enviados separados por escopo; intenções já enviadas e respostas ambíguas continuam congeladas até reconciliação.
7. **Densidade operacional, sem ruído:** linhas compactas e acionáveis em vez de cards altos e repetitivos. Um painel só agrupa informações relacionadas; não empilhar toda a aplicação na mesma página.
8. **Ação proporcional ao risco:** operações frequentes com pouco atrito; alterações destrutivas, limites, estorno, transferência e pagamentos conservam verificação/confirmação/autorização apropriadas.
9. **Mesmo significado, UI adaptativa:** labels e efeitos consistentes entre Android e Web; formato próprio de cada plataforma. Mobile-first 360/390/430dp, fontScale 1x e 2x, IME, safe areas, foco, leitor de tela, contraste e alvos >=44px (preferir 48dp para ações Android e 56px nas ações de produção).
10. **Evidência e validação:** separar tela observada, código lido, hipótese e meta; comparar screenshots reais antes/depois na mesma fixture/versão, medir toques e scroll só quando executados, nunca declarar UX aprovada por CI verde.

### Atendimento — arquitetura de tarefas

- **Agora**: trabalho imediato (prontos, chamadas, QR sem responsável e pendências). No pico, próxima tarefa real e ação devem aparecer no primeiro viewport da fixture; informações complementares não empurram a fila para baixo. Não exigir botões de entrega apenas para telemetria.
- **Comandas**: localizar, abrir e acompanhar; busca por nome/código/mesa com identificação estável, mesa atual opcional, estado e saldo canônico; homônimos e anônimas distinguíveis. A abertura não fica como formulário permanente dentro da lista.
- **Mesas**: contexto físico, ocupação, responsável e comandas acionáveis da ocupação. Múltiplas Tabs na mesma mesa nunca são fundidas; retorno à mesa preserva o contexto.
- **Caixa**: módulo separado por permissão; cobrança da Tab é ação contextual.
- **Comanda selecionada**: workspace compacto, não página monolítica. Primeira área: referência/nome, mesa se houver, estado, saldo canônico, avisos críticos, ações ADICIONAR ITENS e COBRAR (quando habilitadas). Histórico, ver conta, limite e operações ficam em telas/disclosures contextuais, sem perder visibilidade de bloqueio importante.

### Ações principais e padrões de entrada

1. **Abrir comanda**: botão explícito na lista ou na mesa; abre diálogo curto para nome/apelido opcional e contexto de mesa quando pertinente, com decisão Abrir. Sem CPF ou cadastro obrigatório, sem criação implícita, Tab sem mesa é válida.
2. **Ação central + = Adicionar itens**: com Tab selecionada abre catálogo daquela Tab; sem Tab selecionada abre seletor rápido (busca por nome/código/mesa e recentes), com Abrir nova comanda como ação SEPARADA. Toque no + não deve criar comanda silenciosamente.
3. **Catálogo como workspace próprio**: no mobile tela ou sheet grande/fullscreen, não diálogo minúsculo com cardápio extenso. Busca global, categorias, disponibilidade, preço, quantidade -/N/+ ao lado do produto, personalização/nota contextual inclusive item simples. Configurações diferentes ficam distintas.
4. **Carrinho sempre alcançável**: barra/resumo persistente de quantidade e valor durante o catálogo; nunca deixar a única entrada do carrinho depois de todos os produtos. Uma única fonte de draft.
5. **Revisão integral antes de enviar**: mostrar TODAS as linhas, variantes, notas, quantidades, destino e total, mesmo com busca/categoria filtrando o catálogo. Voltar à edição preserva a composição; confirmar envia a intenção exata revisada.
6. **Última rodada e repetir**: histórico separado com hora/referência canônicas; repetir gera novo draft e revalida preço, disponibilidade e modificadores, sem reutilizar chave de intenção anterior.
7. **Troca A → B → A**: conservar draft local por Venue, operador/sessão e Tab. Intenção submetida/conclusão desconhecida exige reconciliação do mesmo UUID/payload; nunca transferir pedido entre Tabs/sessões ou repetir às cegas.
8. **Item esgotado no draft**: permitir remoção/redução da linha local NÃO submetida, impedir aumento/envio e revalidar com servidor. Jamais mutar item confirmado por este atalho.
9. **Estado e feedback**: Enviando, Verificando, Offline/desatualizado, Ação necessária e Confirmado são estados diferentes. Loading normal não é falta de conexão. Sucesso ordinário usa feedback não bloqueante; erro fornece próxima ação segura; só API canônica confirma pedido ou pagamento.

### Gates de UX verificáveis

| Jornada | Aceite proposto |
| --- | --- |
| Primeira dobra | Contexto e CTA imediatamente visíveis; Agora/Pico mostra primeira tarefa real sem scroll |
| Comanda | Abrir explicitamente; selecionar homônimos por referência e ID, não pelo nome |
| Pedido de três produtos | Selecionar e adicionar sem cruzar histórico ou financeiro; quantidade junto do item |
| Revisão | Todas as linhas e observações visíveis com qualquer filtro de catálogo ativo |
| Interrupção | A → B → A preserva draft sem misturar destino; freeze/retry não duplica |
| Estados adversos | Invalidez, timeout, perda de ACK, logout, offline e force-stop têm retomada segura |
| Visual real | Android 360/390/430dp x fontScale 1 e 2; IME; Web mobile+desktop, teclado, toque, leitor de tela |
| Evidência | Capturas antes/depois da mesma fixture/SHA, testes de jornada e medidas executadas separadas de estimativas |

Base: docs/design/ux-friction-audit-2026-10-12.md, auditoria Android de 13/10 (preservada em branch de evidências), specs relevantes 023, 026 e 027 por caminho completo. Revisar também heurísticas de Nielsen Norman Group, WCAG 2.2 e diretrizes de interface Android. Os fluxos existentes não mudam automaticamente por este texto; divergências demandam spec e PR de implementação.

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

Escala base: 4, 8, 12, 16, 20, 24, 32 px. Margem mobile: `--space-mobile` (20 px). Botões: raio 8 px; badges: 4 px; listas de produção: raio 0.

- `--radius-sm`: controles compactos;
- `--radius-md`: botões, badges e linhas;
- `--radius-lg`: painéis;
- `--radius-pill`: status/chips.

Não criar um novo raio, sombra ou espaçamento para cada feature.

## Componentes canônicos

### Atendimento mobile — experimento Spec 029

Em `/attendance`, Mesas usa grade de duas colunas no mobile e três a partir de
768px; detalhes expandidos ocupam a linha inteira. Número, ícone e estado textual
acompanham a cor: disponível/success, ocupada/info, limpeza/warning e fora de
serviço/danger. Busca e filtros por estado não alteram dados operacionais.

Mesas e comandas formam uma área única. A criação parte da mesa; selecionar Tab
abre sheet grande com título identificável, saldo e catálogo. ActionDialog pode
ficar fechado sem desmontar o workspace, preservando drafts. Cardápio, Pedido atual
e Conta são regiões exclusivas nesse sheet; a barra de navegação/resumo permanece
alcançável enquanto os produtos rolam e Voltar fica fora da área de rolagem.
ProductIcon, Field, botões e BillSummary continuam canônicos. Quantidade e
personalização aparecem junto do produto; configurações múltiplas exigem revisão
para reduzir uma linha específica. O pedido mostra “não enviado”; valores
registrados vêm da API, e preço confirmado usa snapshot histórico. Histórico e
ações especiais ficam sob demanda; Escape e retorno conservam foco/rascunho,
com saída bloqueada enquanto houver operação pendente. Contrato experimental:
`specs/029-attendance-mobile-design`; não é declaração de implantação global.

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

- `button--primary`: próxima ação principal da tela, fundo papel creme;
- `button--work` / `buttonWork`: ação de produção de 56 px, papel, largura condensada e sombra de tecla;
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

Resumo por produto → fila individual → passe vêm antes da disponibilidade e Quick Catalog. No desktop largo são três colunas; no mobile, regiões empilhadas. Resumo apenas soma quantidades em produção, sem mutations agrupadas. Tempo desde o pedido usa created_at; no passe usa ready_at, com “Tempo não informado” quando ausente.

No Web, nomes longos podem ocupar várias linhas: conteúdo e ações usam duas
linhas no celular e colunas quando houver espaço. Sem truncar o produto ou
reduzir o alvo de toque. A fila e o passe ficam antes do cadastro conectado da Spec 020.

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

## V02 parcial — Field confortável e limites de StatusBadge

`field fieldComfortable` reutiliza o Field no Quick Catalog de Cozinha/Bar. A variante compacta continua disponível nas demais telas. Fonte: `.inp` e `.fld` em `prototype/references/night/Main.dc.html`, ZIP registrado no manifest. Medidas do controle sem ícone: altura 56, padding horizontal 16, raio 10, Archivo 20/600, largura normal, borda interna 1,5 em border-strong; foco interno 2 em text; placeholder text-subtle. Label 14/800, tracking 0,1em, gap 6. O input não herda caixa alta/tracking do label: os valores digitados preservam sua leitura.

Tokens específicos reutilizáveis: `--radius-field`, `--space-field-gap`, `--stroke-field`, `--stroke-field-focus`, `--tracking-field-label`; altura, padding, fontes e cores reutilizam tokens existentes. O foco interno em papel continua visível no teclado e no toque; o recorte de pixels mede o controle.

StatusBadge de disponibilidade mantém seu contrato: raio 4, texto 12/900, padding 5/9, min-height 28, texto + estado. `.badge` do export é contador de navegação, `.rel`/`.casa` são relacionamento e NOVO é etiqueta de pedido. Não são referências equivalentes para Disponível/Indisponível; paridade completa desses badges permanece não verificada.

## V04 parcial — bloco de pedido em produção

`stationOrder` agrupa visualmente itens pelo Order, com uma única Tab/destino e `stationOrderItems`. Cada `stationTicket` mantém produto/quantidade/customização, estado, tempo e ação individual; um bloco não oferece confirmação em lote. Sem identidade de Order, cada item permanece separado.

Mobile: destino acima dos itens, ação de largura útil e altura mínima 56. Desktop ≥1200: destino 84 px, conteúdo flexível e ação 116 px, gaps 16; o grupo tem padding 12/20/12/24 e uma divisória externa, com gap 12 entre itens. Reutilizar tokens de cor/espaço/toque/fontes; `--production-ticket-destination` e `--production-ticket-action` promovem as medidas existentes 84/116 para compartilhamento. Não suprimir estado, tempo ou customização para imitar o export.

## V05 parcial — navegação nativa

AttendanceNavigation usa Ground/Surface/Paper/Ink/Muted existentes, Archivo Label, barra 84 dp com padding inferior 8, centro 136, margens centrais 10/4/2 e raio 12; ícones 24, gap 5, label 14 e marcador ativo 3. Medidas promovidas em AttendanceNavTokens, baseadas em .nav/.nb/.ngo do export night. Mesas/Caixa ficam na extensão operacional anterior, com targets mínimos 44 dp; insets pertencem ao AuthApp.

Medição executável confirmou borda superior 1 px: laterais 127×75, botão central 128×63 no conteúdo 390. Token Subtle (já canônico no sistema) usado nas laterais inativas. Sombra de tecla 4 dp. A referência literal inclui cantos da moldura; crop derivado remove apenas border-radius da .phone, não a região .nav, para separar chrome de apresentação.

## Navegação nativa com fonte ampliada

### Header operacional Android — contrato responsivo da demo

O header conserva marca, nome real do operador e estado textual de conexão. Ações Pico/Atualizar/Conta são extensão operacional ausente do header literal60px do night. Em celular360–430dp, promover agrupamento em duas regiões: identidade/conexão acima e ações em FlowRow abaixo, padding horizontal16/vertical12, gap8, alvo mínimo44dp. Fonte ampliada pode aumentar altura e quebrar o nome, sem ellipsis/clipping ou redução da fonte escolhida. Busy desabilita Atualizar/Conta, mantendo toggle Pico como antes. A própria coluna mede sua altura; insets continuam no AuthApp. Nenhuma alegação de equivalência literal do header completo.

Contrato de adaptação: fontScale acima de 1.3 usa AttendanceNavTokens.ExpandedHeight de 112 dp e Pedir com ícone acima do label. Até 1.3 mantém barra 84 dp. Centro 136 dp na fonte normal e 104 dp na ampliada; margens existentes permanecem, sem encolhimento artificial da fonte. Comparação HTML canônica segue em 390 dp/fontScale1. Testar 360/390/430 dp com fontScale 1 e 2 para overflow, ações e seleção.

Descoberta na fixture 360 dp/fontScale2: CONTAS quebra e labels têm overflow. Para fonte ampliada, centro adapta para 104 dp e barra 112 dp; laterais ganham largura, Pedir usa ícone acima, label lateral lineHeight 16 sp. Centro 136 e altura 84 permanecem em fontScale normal; captura canônica deve permanecer idêntica.

## Gerência — hierarquia e ícones operacionais (V02 parcial023)

OperationalIcon é SVG decorativo com viewBox24, stroke2.2, round caps/joins, currentColor e aria-hidden/focusable=false; size padrão24 para navegação e20 para sectionHeader. Agora reutiliza os paths do export night; operation/sales/settings/more/printer/wallet são extensões explícitas do mesmo vocabulário, sem alegação de referência literal. Label textual obrigatório; nunca usar este componente para substituir ProductIcon.

SurfaceNav da Gerência tem exatamente cinco destinos, altura mínima84 + safe area, ícone acima do label14/800 com gap4 e marcador ativo3px. Fonte ampliada pode aumentar altura; reserva de conteúdo usa medida real da barra (ResizeObserver), mantendo mínimo84 e safe area. Impressoras fica em Mais. A seção usa sectionHeader existente, título20/800 e ícone20 em accent. Região financialMetric ocupa largura total no grid e valor34px/money; números auxiliares28px.

Token --shadow-operational: 0 4px 12px rgb(0 0 0 / .2), para camada financeira; --shadow-navigation: 0 -4px 12px rgb(0 0 0 / .2), para limite de navegação. Sombras são extensões funcionais discretas, não copiadas do artboard. Cor/espaçamento/raios seguem tokens atuais. Sem alterar estilos das estações, caixa ou demais métricas globais.

### Hierarquia compartilhada Web (Spec023)

OperationalHeading conserva h1/h2 e atributos, adiciona ícone decorativo24/20px com stroke2.2/round/currentColor; identificação do título usa accent, seções usam text-muted salvo estados danger/warning já definidos. Título34px no telefone, seção20px, subseção16px; espaçamento existente8/12/16/24. Cabeçalho com separador border e espaço16; panel funcional reutiliza shadow-operational, sem sombra cumulativa em panel aninhado. Estações conservam SVGs da referência e zonas existentes: quantidade com font-number, destino legível e estado secundário. Não alterar geometria de Field/StatusBadge ou recibo canônico. Ícones contextualizam operação; produto continua usando seu ProductIcon. Navbar do Atendimento mantém labels/callbacks e ganha icon24 + texto, sem nova navegação.

### Catálogo e cobrança nativos com fonte ampliada

Produto: nome completo e preço canônico em linhas próprias, sem ellipsis, dentro do OutlinedButton/Column existentes; fontes, semibold, padding e rota/disponibilidade atuais. O diálogo de pagamento conserva footer e decisões, com conteúdo vertical rolável para fontes ampliadas/teclado; sem redução de fonte, sem esconder warning e sem autorização nova. Comparar componente real e medir clipping antes/depois em API36.

Cobrança: fontScale>1.3 reutiliza limiar da navegação e empilha confirmar/cancelar com largura total/gap8; até1.3 mantém footer atual. Conteúdo vertical rolável em ambas variantes. Não esconder controles/advertências ou reduzir fonte para caber. Capturar antes/depois; labels/formatadores canônicos preservados.

V05 login: verificar a tela real com fonte200% e teclado. Se conteúdo exceder viewport, permitir rolagem apenas na variante ampliada (>1.3, limiar existente), conservando geometria normal, campos/trim/PIN clearing/busy e callback de autenticação. Teste usa fixture somente em androidTest e captura antes de digitar PIN; não mudar política de autenticação ou persistência.

Resultado login: sem teclado a tela360/font200 já cabe; não alterar sua composição por hipótese. Com IME real aberto, captura confirma PIN/Entrar cortados e ausência de rolagem. Adaptação final habilita rolagem somente quando WindowInsets.ime>0, em todas as fontes; sem IME conserva layout central existente. Artefato login-before registra apenas a falta do recurso de scroll no teste inicial; login-keyboard-before é a prova de clipping efetivo.


## Gerência progressiva e DEV local (Spec025)

Gerência monta uma única seção da navegação por vez. Agora prioriza exceções,
comandas abertas e exposição; detalhes auxiliares ficam em details/summary com
alvo mínimo44, sem retirar a indicação de pendências. Cadastros têm páginas
próprias e retorno para Mais. Histórico encerrado é disclosure explícito no PDV.
DEV reutiliza os mesmos Field, panel, OperationalHeading e botões; confirmação
local informa revogação de sessões e preservação de histórico.
buttonDangerReadable conserva borda/tinta danger e usa color-text no label para
contraste AA sobre Surface2. É variante semântica de ação destrutiva usada no DEV;
não altera o raster canônico do botão danger nem tolerâncias das referências.


## Attendance catalog hierarchy

Attendance section headings reuse accent/surface color-mix, border, radius and spacing tokens; selected Tab title keeps its centered disclosure treatment. Confirmed rows use Surface2, border-strong, radius-md and space-3, with wrapping descriptions and compact status pills. The icon-only removal button uses danger color, a subtle danger-tinted surface and touch-min width/height, with a product-specific accessible name and visible focus. Fechar comanda uses a restrained accent-tinted bordered secondary button with receipt icon. These are scoped Attendance variants; canonical reference primitives and POS remain unchanged.
Use existing category buttons with pressed state and counts, global search Field and ProductIcon cards. Only one category is shown outside search; changing category preserves the draft. Cart quantities/actions wrap below long item names on mobile. Attendance financial summary follows the ordering flow: canonical net Subtotal, then a native Mais detalhes disclosure containing original subtotal and the existing breakdown. Cash/POS keeps full monetary visibility. Use existing tokens/touch targets; no new visual identity.

Attendance follow-up: selected Tab title is centered with no decorative cart. Category buttons remain available while a second tap collapses their product list while search remains visible. Compact Subtotal uses canonical payable total; original gross and breakdown sit inside Mais detalhes, rendered with quiet-button border, padding, focus and touch tokens. Confirmed removal has a reason and explicit confirmation, preserves cancellation history and disables switching while unresolved.

Confirmed-item removal uses a native modal dialog with a labelled title, trapped focus and focus restoration. Escape closes only before submission or after a resolved rejection; pending, ambiguous or applied-but-unrefreshed corrections cannot be dismissed. Existing cancellation rules remain unchanged. Dialog uses existing surface, border, spacing and radius tokens; backdrop uses the background token.

Attendance action dialogs reuse the native modal and removalDialog tokens: labelled title, bounded mobile scrolling, inert background, Escape when idle and focus restoration. Organizar mesa discloses location/association; release and close require explicit confirmation. Product customization is modal only in Attendance. Success uses role=status without blocking; errors use persistent role=alert, also visible inside active dialogs.

Attendance selected Tab: use an accent-derived tinted surface/border and a centered labelled disclosure heading. Its caption and expand/retract cue communicate selection without depending on color. Draft lines precede catalog: name/customization, cent-based line total and grouped minus/output/plus controls. Minus and plus meet 44px touch minimum. Draft surface and active category use restrained color-mix from existing accent/surface tokens. POS retains its layout.

### Navegação de regiões na produção (Spec 026 T10a)
Em mobile (<768 px), navegação sticky no topo usa três colunas, controles
buttonSecondary, tokens de superfície/borda/spacing e foco existente. Cada
controle usa text-xs para o nome sem quebra e text-sm para a contagem em linha
separada, mantendo o alvo mínimo de toque. Destinos focáveis usam
scroll-margin de quatro space-5 para permanecer abaixo da navegação.
Desktop mantém as regiões simultâneas. Não expressa seleção exclusiva nem tabs.

### Resumo de produção por configuração (Spec026 T10b)
stationDish reutiliza CustomizationText (variação/modificadores/observação),
stationDishContext para contagens de estado e muted para histórico incompleto.
A quantidade é do grupo compatível; os chips mantêm cada destino. Nenhuma
seleção ou nova ação de lote é apresentada neste recorte.

### Revisão de lote de produção (Spec026 T10c.2)
Usar ActionDialog/removalDialog e customizationChoice para checkbox com alvo44px.
Buttons secondary abrem seleção, primary confirma ação humana, CustomizationText
mostra snapshot; notice/status apresenta pendência/resultado por linha. Nenhuma
linha selecionada por padrão; quantidade inteira, estados/destinos/estação explícitos.

### Pendência individual de produção (Spec026 T10d.1)
Reutilizar buttonPrimary para ação humana do item e notice/status para sua pendência.
buttonSecondary recupera o mesmo item pelo identificador curto, mesmo após saída
da fila. Estado ocupado/desabilitado pertence ao item verificável; outra linha
verificável mantém seu controle. Lote, legado e disponibilidade conservam barreiras.
Resultado identifica a linha; nenhuma nova cor, token ou inferência de preparo.

T10d.2: lote persistido desabilita controles individuais das linhas selecionadas;
outros itens verificáveis mantêm seu controle e sua própria pendência/recuperação.
Durante revisão ou antes da persistência permanece bloqueio global. Reutilizar
os mesmos buttons/notice/status; demais ferramentas conservam as barreiras.

T10d.4: disponibilidade versionada reutiliza os controles existentes e notice/status
por produto, com ação "Verificar mesma disponibilidade" após resultado ambíguo.
Somente o produto pendente fica bloqueado; outros produtos versionados e itens
verificáveis podem operar. Revisão/legado, modificadores e QuickCatalog mantêm
barreiras. Não mostrar sucesso antes de recibo validado e leitura canônica.

T11a/T11b Android: filtros Prontos/Chamadas/Pendências reutilizam RodadaOutlinedButton, seleção semântica e alvo mínimo de 48dp. Contagem não consultada usa —. Pendências exibem evidência e revisão explícita. Entrega dispõe status, produto/destino e ação em coluna para preservar leitura com fonte ampliada, sem mudar a semântica de confirmação.
Com fontScale > 1.3, os três filtros usam coluna com largura total; na fonte padrão usam linha. O texto não deve ser comprimido para manter os filtros lado a lado.

T11c Android: conferência de caixa usa Surface sobre a fila existente e LazyColumn com os tokens tipográficos/semânticos existentes, retorno e atualização em RodadaOutlinedButton de largura total, alvo mínimo48dp. Não apresentar botões de mutation na conferência de resultado ambíguo.

T11d Android: conferência de correção/estorno usa Surface sobre a fila existente, LazyColumn, tokens e os mesmos rótulos de comanda/pagamento da superfície adjacente. Item/pagamento original têm destaque semântico; estado guardado e consultado são distintos. Retorno/consulta em RodadaOutlinedButton com largura total e mínimo48dp; não apresentar ação financeira em conferência de resultado ambíguo.

### Atalhos Guest por região (Spec004)

Cardápio, Pedidos e Conta usam navegação sticky de três botões semânticos,
com os mesmos tokens, espaçamento e alvo de toque dos atalhos de produção.
Disponível também no desktop. Atalho rola e transfere foco; região montada
preserva rascunho/intenção. Margem de rolagem evita ocultar o título sob a barra.

### Mesas Android — alinhamento com Atendimento Web

Usar Ground no fundo, Surface no painel, Control nos cartoes e Paper nos titulos.
A faixa superior de estado e o icone reutilizam Success (AVAILABLE), Info
(OCCUPIED), Amber (DIRTY/CLEANING), Danger (OUT_OF_SERVICE) e Muted (desconhecido).
Estado sempre tambem textual. Grade em duas colunas, uma com fonte ampliada;
nao reintroduzir filtros horizontais. Acoes detalhadas usam Dialog nativo rolavel,
com dismiss bloqueado durante operacao pendente. Navegacao no topo com destino
ativo Paper/Ink, preservando Caixa e demais capacidades existentes.


### Atendimento — categorias e seleção de item (2026-10-15)
Cardápio inicia com categorias e busca. Categoria abre janela grande com grade
de produtos; produto abre quantidade e personalização, sem ações repetidas sob
cada card. Manter nome/preço/estado/draft e Ver pedido atual acessível. Reutilizar
ActionDialog/Dialog, superfícies, bordas, radius, tipografia e alvos existentes;
Back fecha só a camada ativa e restaura foco. Opções obrigatórias não são ocultas.
Este fluxo substitui os steppers do catálogo no Atendimento, preservando revisão
integral, disponibilidade, limite99 e isolamento por Tab. POS/Guest inalterados.


### Receitas cromáticas do Atendimento nativo
O port Android deve reutilizar as cores aplicadas em `/attendance`: controle
neutro Surface2/BorderStrong; contexto selecionado Amber12% sobre Surface2 com
bordaAmber; produto no rascunho Amber8% sobre Surface2; ação contextual Amber8%
sobre Surface1/bordaAmber40% sobre Border; mesa ocupada bordaAmber45% sobre Border,
sem substituir faixa/íconeInfo. Misturas sRGB com tokens canônicos, sem novas cores
hexadecimais independentes. Campos Surface2/BorderStrong/focoAmber; primárioPaper/Ink.

Gerência: histórico usa botão quiet apenas com ícone history20, alvo touch-min e nome acessível. No grupo actions, o controle mantém largura touch-min e o botão textual ocupa o espaço restante. O diálogo reutiliza ActionDialog, campos, dataRow, BillSummary e dialogReturn; sem paleta ou escala paralela.
