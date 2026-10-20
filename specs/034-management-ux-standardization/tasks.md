# Tarefas — Spec 034

Documento publicado não significa implementação. Itens de produto só fecham com
evidência da composição testada e ligação ao [aceite](acceptance.md).

## S0 — Baseline

- [x] S0.1 Conferir main, PRs concorrentes, ownership e o inventário de rotas (baseline de S1a).
- [x] S0.2 Capturar cinco áreas e página tocada em fixture isolada, com SHA (S1a: somente entrada Gestão).
- [ ] S0.3 Inventariar tokens/primitives, CSS compartilhado, capacidades e estados.
- [ ] S0.4 Registrar composição proposta para Gestão, tarefas de avaliação e decisão.

## S1 — Gestão

Recorte S1a implementa somente a entrada, sem fechar a etapa inteira. Subpáginas,
restauração de foco entre rotas e pesquisa com operador permanecem pendentes.

- [ ] S1.1 Implementar hierarquia/header/utilitários e linha de navegação reutilizável quando necessário.
- [ ] S1.2 Preservar todos os destinos, labels acessíveis e contexto de retorno.
- [ ] S1.3 Harmonizar setup/clientes/alertas/impressoras em sub-slices separadas após baseline; não redesenhar sessão compartilhada.
- [ ] S1.4 Validar estados, foco/teclado, zoom200%, quatro larguras e antes/depois.

## S2 — Agora e Operação

- [ ] S2.1 Priorizar exceção e próxima ação; resumos nunca ocultam pendências.
- [ ] S2.2 Harmonizar produção/entregas/salão com detalhes progressivos e destinos corretos.
- [ ] S2.3 Validar vazio/volume alto/stale/erro parcial/sem permissão sem métricas presumidas.

## S3 — Financeiro

- [ ] S3.1 Categorizar entrada de caixa, fechamento, ajustes/aprovações e relatórios.
- [ ] S3.2 Harmonizar uma rota por sub-slice, preservando contexto e calendário operacional.
- [ ] S3.3 Validar parcial/pendente/cancelado/quitado, erros, busy, reauth e intenção ambígua.
- [ ] S3.4 Executar integração real e review R3 se tocar apresentação de ações financeiras/recovery.

## S4 — Cardápio

- [ ] S4.1 Harmonizar entrada e formulários mantendo uma criação e edição por categorias.
- [ ] S4.2 Preservar busca/filtros/draft, erro de campo, pending e retorno ao produto correto.
- [ ] S4.3 Validar listas extensas, nome longo, polling durante edição e permissão negada.

## S5 — Composição e handoff

- [ ] S5.1 Rodar typecheck/build/lint focado/test:visual e regressões dos consumidores compartilhados.
- [ ] S5.2 Percorrer ida/volta/histórico/hash/aliases e comparar mesmos estados em quatro larguras.
- [ ] S5.3 Verificar teclado, leitor de tela, foco, zoom200%, safe areas e sem scroll horizontal.
- [ ] S5.4 Registrar evidência por AC/SHA, limitações, review e decisão de aceite visual.
- [ ] S5.5 Registrar próxima etapa e rollback; produção/piloto não derivados de CI.
