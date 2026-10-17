# E01-05 / E03-05 — shell e Agora nativos UX2 (parcial)

Contrato: Spec033 e protótipo PR212 `prototype/ux-2-0/index.html`.
Dependências: entrada Agora PR220; projeção staff-safe PR218. Branch de main,
com cherry-pick explícito do commit de entrada 27ed61f2. Sem merge/deploy.

## Antes / depois esperado

Antes: header alto, navegação superior, três filtros Prontos/Chamadas/Pendências,
contas abertas misturadas em Agora, entrega com conclusão direta obrigatória.
Depois: header 72dp, wordmark aprovado, footer de três ações, Agora com duas
filas Atendimentos/Entregas e linhas compactas do protótipo. Dados vêm dos
repositórios reais. Abrir linha não assume nem conclui tarefa.

## Critérios deste slice (não concluem E01/E03)

- Header 72dp, logo113x42, margens22; conteúdo20dp e footer7dp/61dp,
  Atendimentos/Entregas50dp com contadores canônicos/freshness.
- Tipografia Archivo com largura100 neste shell; tokens de cor existentes.
- Filtros/scroll preservados; seleção de Tab é explícita, por ID de target v1.
- TABLE requer table/occupancy/generation ainda correspondentes ao readback;
  UNAVAILABLE e target ausente/desconhecido não inferem Tab de destination_label.
- BILL abre Conta da Tab autorizada; SERVICE abre contexto da Tab; READY abre
  detalhe do item, quantidade, estação e destino. Nenhuma mutation ao abrir.
- Cada abertura reconsulta `GET /dispatch/tasks/{id}/` e valida ID, tipo, estado
  e target canônico; READY exige item ainda READY. A seleção explícita após
  fallback TABLE reconsulta a chamada e a ocupação/generation antes de abrir.
  Contexto de chamada e ações continuam disponíveis nessa Tab escolhida, com
  Conta como seção inicial para BILL. Navegação manual limpa a origem da tarefa.
- Recuperação original permanece acessível. Conta/Atualizar/Pico/Caixa existentes
  continuam acessíveis em menu operacional na área meta do header. Essa adaptação
  necessária ao app real é diferença intencional proposta, sem aprovação implícita;
  paridade/sign-off seguem pendentes até decisão explícita.
- Estados sem dados/erro/loading/stale não mostram sucesso otimista.
- JVM/lint/build, instrumentação das ações e pixels em360/390/430; integração
  real Django/PostgreSQL separado de fixture visual. FontScale2 e dispositivo
  físico são gates próprios e devem ser registrados honestamente.

Não altera motores de pedidos, pagamentos, recovery, políticas nem autenticação.
Home da comanda, catálogo, resumo/pedido e Mesas ficam nos próximos recortes;
não apresentar shell como paridade integral.

## Revisão independente — primeira passagem

`646bb629` / `2b2b1b06`, revisor em outro contexto `dispatch_finish_guard`:

- P1: fila tinha target autorizado na leitura, mas abrir não revalidava a task;
  Guest revogado após a fila poderia manter o deep link antigo. Correção neste
  recorte: leitura exata antes de SERVICE/BILL/READY e novamente na seleção TABLE
  ou ação Abrir comanda da entrega. Sessão original conferida antes/depois do IO.
- P2: fallback TABLE perdia ações da chamada e BILL não selecionava Conta após
  escolha explícita. Correção: origem preservada por IDs/occupancy/generation,
  novo readback na escolha e contexto vinculado somente à Tab escolhida.

Correções exigem reexecução e nova revisão; este registro não é aprovação.
API218 ainda não publica `claimed_by_id` no serializer DELIVERY; completar a
projeção é dependência da identificação visual do outro responsável. A API
continua autorizando/negando a mutation canônica; este cliente não cria bypass.
