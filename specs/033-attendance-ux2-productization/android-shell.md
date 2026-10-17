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
