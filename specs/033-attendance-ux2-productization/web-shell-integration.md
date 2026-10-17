# Shell UX2 — integração das operações existentes

E01/E03/E06, continuação da PR221. Base local inclui contratos de destinos das
PR218/222. Reutiliza AttendanceTaskContext e engines existentes; navegação não
assume nem conclui tarefas. Injeta contexto também no workspace legado até a
integração das páginas de PR224. Back é bloqueado enquanto houver intenção ambígua.

Menu operacional preserva Atualizar e Sair no cabeçalho, como no Android real.
A aparência dos metadados do cabeçalho permanece; a interação adicional é uma
diferença proposta para avaliação de paridade, sem aprovação implícita.
Helper de fixture usa Atualizar real, preservando drafts em vez de reload.

Snapshot inicial compila e passa typecheck/lint. Execução real36testes PG55638 em
andamento: os três cenários de fila com conflito, ACK perdido e replay passaram;
duas falhas iniciais estão em investigação. Nenhuma suíte completa declarada
verde. Revisão independente encontrou origem de chamado persistindo após falha
de seleção; correção e regressão ainda obrigatórias. CI/paridade/aceite pendentes.
