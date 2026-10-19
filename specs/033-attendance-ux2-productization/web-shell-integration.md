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

## Composição das páginas e conta

PR224 integrou o shell em25ae6645 e testes emd6815f40. Typecheck/ESLint/build
passaram (warning de setter sem uso removido depois). Rodada11:9PASS/2FAIL;
os dois casos dirigidos, após ajuste de seletor para página e espera pelo término
da limpeza da intenção, passaram2/2 em20,3s. Identidade/payload/ledger e zero
writes do caso negativo permanecem exigidos. Suíte ampla antiga ainda precisa
migração para páginas completas; não aceitar CI por estreitar seleção.

PR225 compôs sem remover receipt sempre montado nem fluxo CLEANING em ae73cfb4.
Typecheck/ESLint/build PASS. Três testes financeiros reais Attendance passaram
3/3 em24,1s após composição: PaymentACK perdido+Close503/ACK perdido, consumo
concorrente+keepOpen/callback503, e falha ao persistir fase confirmada. Mesmo
payment/UUID, readback canônico e ausência de cobrança adicional continuam
assertados. Revisão final de composição e CI ainda pendentes.
### Recuperação em páginas completas

E02-04/05,E06-02: helper passa pela página Comanda→Adicionar itens; catálogo usa
quantidade direta e resumo opcional. Três testes existentes de perda de ACK
foram migrados sem remover doubleclick/reload/mesmo payload/Order/ledger;
390 também retoma pelo POS para validar a intenção original entre superfícies.
Resultado real PG55638:3PASS/29,6s,360/390/430. A primeira tentativa falhou por
label de busca antigo; o seletor final usa Buscar produto. Typecheck/ESLint dos
arquivos modificados PASS. Testes amplos remanescentes em migração, CI nãoaceito.

Regressão funcional encontrada na migração: a página ocultava repetição histórica
na Conta e bloqueava atalho home quando havia rascunho, embora engine existente
já preservasse esse rascunho. Restaurada entrada histórica e atalho sem count gate;
a engine continua autorizando/revalidando intenção original. Ação histórica na
Conta preserva capacidade anterior e exige comparação/aprovação de diferença
visual; não constitui paridade aceita. Teste real de repetição ainda em execução.

A regressão de remoção identificou outra diferença involuntária: a Conta UX2
listava linha cancelada como consumo ativo, enquanto a superfície anterior já a
retirava. Restaurado filtro de linhas CANCELLED apenas na lista ativa; histórico
canônico e ledger não são alterados. O teste mantém a assertion de ausência da
linha cancelada e as provas de reversão financeira, sem enfraquecimento.
