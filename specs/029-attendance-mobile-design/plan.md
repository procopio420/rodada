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
