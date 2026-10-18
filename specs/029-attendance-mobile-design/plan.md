# Plano
1. Preservar diff preexistente; estilos exclusivos de `/attendance` em arquivo próprio.
2. Reutilizar OperationalIcon/Heading, ProductIcon, AttendanceDraft, BillSummary,
   ProductCustomization e ActionDialog. Usar somente tokens canônicos.
3. Grade de mesas e filtro puramente local; atalhos por foco/scroll sem alterar comandos.
4. Evidência visual antes/depois com a mesma fixture, 360/390/430 e desktop.
5. Typecheck, lint focado, auth, build e suíte visual; registrar falhas e limites.

Risco R2: UX operacional. Valores históricos são somente apresentação dos campos
existentes; nenhum cálculo financeiro canônico é alterado. Trabalho concorrente em
globals.css, tab-location-move, gateway e API permanece fora da autoria desta slice.

## Revisão após rebase — 2026-10-14
Base atualizada para `origin/main@47043184408c090ddae33df17d4d72010603f764`,
incluindo novas diretrizes task-first e correção de seleção de comanda contextual.
Conflito resolvido semanticamente: seleção serializada conserva validação do ID,
rascunhos por Tab e abertura de outra Tab mesmo com draft anterior. Popup permanece
montado fechado; ActionDialog agora permite `open=false` sem perder estado interno.

Fluxo: Mesas e comandas → expandir mesa → abrir/criar Tab → catálogo em sheet grande
→ revisão integral → confirmar → resultado canônico → voltar à mesa. Conta é uma
região explícita, separada do catálogo; histórico/personalização ficam sob demanda.
Sem refazer regras de recovery, chaves ou persistência; somente apresentação/roteamento.
Quantidade do catálogo vem do mesmo draft. Com configurações múltiplas, reduzir pelo
cartão leva à revisão em vez de escolher uma linha arbitrária.

Estados a validar: livre/ocupada/limpeza/indisponível, criação busy/erro/ACK perdido,
leitura negada, catálogo/rascunho/conta, filho modal, retorno/Escape, A/B/A, pendência
após reload, flag contextual desligada, ausência de capability e produto esgotado.

## Android nativo
1. Reutilizar TablesScreen e seus comandos/diálogos para a entrada unificada.
2. Separar a janela de Tab em Cardápio, Pedido atual e Conta, sem alterar comandos.
3. Guardar drafts locais por Tab no ViewModel, limpar na troca de sessão e priorizar
   intenções cifradas. Seleção falha não substitui o contexto anterior.
4. Validar isolamento A/B/A, navegação sem POST, bloqueios de ambiguidade, grade,
   fonte ampliada e seleção indisponível por JVM/Compose e emulador.
5. Executar build/JVM/lint, revisão independente e registrar evidências e limites.

## Android: alinhamento da tela de mesas com Web atual

- Preservar callbacks, sessoes, drafts, recovery e permissoes; slice de apresentacao.
- Navegacao no topo e selecao com Paper/Ink; cabecalho recebe nome canonico do Venue.
- TablesScreen: painel, busca sem filtros, historico compacto, outras comandas recolhidas.
- Cartoes com faixa superior semantica e icone/texto; TableCard existente em Dialog.
- Validar cores por teste JVM, estados/dialogo por Compose, tamanhos/fonte e UI real.
- Catalogo, ProductIcon publicado e pagamentos continuam fora desta slice.


## Categorias em popup
1. Substituir lista longa por categorias, preservando busca e draft.
2. Reutilizar cards sem ações repetidas e personalização com quantidade explícita.
3. Adição local de múltiplas unidades com limite e revalidação; API inalterada.
4. Testar cancelamento, quantidade3, personalização, indisponibilidade, A/B/A,
   Back/foco e larguras360/390/430 com fonte1/2. Instalar debug para teste local.


## Categoria Todos — Android, 2026-10-17
Adicionar agrupamento virtual antes das categorias reais, reutilizar busca,
popup e callbacks; validar agregação/busca em Compose e instalar debug local.

## Ajuste cromático Android
Conferir Web/Android reais, reutilizar receitas de mistura sRGB no tema/controles,
aplicar aos estados existentes de mesas/comandas/catalogo, validar build/lint e
capturas com fixtures existentes. Preservar todas as regras e os callbacks.
## Conta Android — 2026-10-17
1. Capturar fixture real antes; reutilizar tokens e separar apresentação da conta.
2. Compactar resumo, disclosure de ações e linhas históricas sem mudar contratos.
3. Validar capturas, guards/callbacks, fonte ampliada, build/lint e revisão.

Histórico da noite Android: extender leitura GET tabs com history_day=current/data e metadata history_business_date; fixar data entre páginas. Separar historyDetail de selectedTab, geração de leitura para respostas fora de ordem. Diálogo com componentes/tokens existentes e nenhuma mutation. Reutilizar endpoints de detalhe autenticados.

## Pedir: nova comanda em mesa — 2026-10-18
Reutilizar comando existente em seletor de mesa disponível → nome/apelido → Abrir e pedir. Validar navegação sem mutação, permissão/busy, vazio e mesa alterada, callback ID/nome e build/JVM/lint/Compose. Evidência de execução registrada após os testes.

### Revisão: mesas ocupadas e rodapé do seletor
Mesas ocupadas com ocupação ativa abrem uma Tab separada pelo comando existente; ID/generation capturados revalidados. Testar ocupação trocada e botões separados verticalmente, inclusive fonte200%; Cancelar integra a mesma coluna das opções de criação.

### Retorno após pedido confirmado
Sinal explícito emitido somente após ACK/readback; consumir após fim do envio/leitura e retornar a Mesas e comandas via clearSelection. Validar rascunho, pendências, outro contexto e ausência de sucesso; preservar confirmação/recovery.


## Manutenção Web PR237
Reutilizar catálogo por categorias e ActionDialog; restaurar somente contratos perdidos na migração (Todos, Escape/foco, retorno do histórico). Migrar testes de navegação para as superfícies reais, preservando cenários de pendência e comandos idempotentes. Alvos de toque usam touch-min. Validar build, lint proporcional, regressões de catálogo/draft/histórico/removals, fluxos de mesa e suíte visual global. Não alterar ledger/API, CI ou tolerâncias/baselines.
