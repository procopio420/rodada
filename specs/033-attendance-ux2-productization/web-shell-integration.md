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

## Correção revisada de contexto — 2026-10-17

E01-03/05, E03-03/05, E06-02/06 (avanço parcial). O contexto de chamado é
vinculado ao ID canônico da Tab. Falha de readback remove a origem; entradas
manuais e criação também redefinem a origem e o retorno contextual. Nova comanda
aberta na mesa retorna à sua mesa. Nenhuma dessas navegações faz claim/complete.

Revisão independente `review_web_shell_context`: finding P2 corrigido;
NO_FINDINGS_WITH_GAPS após releitura do patch e regressão. Sem aprovação GitHub.

Evidências locais, API Django e PostgreSQL isolado em 55638:
- `attendance-removal`, `attendance`, `order-intent`, `tab-drafts`: 12 PASS,
  incluindo Guest selecionado pelo padrão do runner; 1,9 min.
- `ux2-now`: cinco cenários existentes PASS em 360/390/430/1280 e fallback.
- Novo caso negativo: 1 PASS, 12,9 s. GET contextual da Tab A recebe 409;
  abrir B manualmente não mostra contexto de A, não escreve e mantém task OPEN.
- Typecheck, ESLint do componente e build PASS. Typecheck também após novo teste.

Falhas de preparação do novo teste foram preservadas nos artefatos locais:
fixture sem chave obrigatória, URL sem query e seletor ambíguo. O teste final
usa chaves próprias da preparação e intercepta apenas o readback com query.
Não são evidências de operação simulada nem substituem o backend real.

A execução inicial de 36 teve 28 PASS/8 FAIL, corrigidas nesta rodada dirigida;
a suíte ampla e o CI do novo commit ainda precisam rodar. Paridade integral Web/
Android, acessibilidade e homologação continuam pendentes. Nenhuma task ou AC
integralmente aceita apenas por estes testes.
