# Identificação operacional: mesa primeiro

**Data:** 2026-10-13  
**Escopo:** API, Atendimento Web/Android, bar, cozinha, QR, gestão, histórico e impressão.

## Contrato

- `Tab.id` continua a chave financeira. Mesa é apenas destino físico de uma ocupação.
- Quando houver vínculo de ocupação ativo, mostrar **Mesa XX** em destaque, depois o apelido opcional e uma referência curta **Comanda XXXXXXXX**.
- Quando não houver vínculo, mostrar apelido se informado; senão, referência da comanda. Não preencher `Tab.display_label` com o número da mesa.
- Uma mesma mesa pode ter várias comandas anônimas ou homônimas. A referência curta é obrigatória como distinção.
- Mudanças de mesa afetam `table_label` na consulta seguinte, sem modificar pedidos, saldo ou apelido.
- `last_table_label` existe somente como contexto histórico, visualizado como **(última)**; não deve ser confundido com ocupação atual.
- QR mantém identificação do visitante opcional. Nome é obrigatório apenas onde o domínio exige identidade (ex.: cadastro de cliente/fiado).
- Tickets impressos são *snapshots imutáveis*: mostram o local no momento da criação (ou último conhecido, devidamente rotulado). Reimpressões não recalculam a mesa e não alteram comprovantes anteriores.

## Projeções

`GET /tabs/` e `GET /tabs/:id/` incluem `table_label` e `last_table_label` (nullable).
`GET /production/BAR/` e `GET /production/KITCHEN/` incluem `table_label` (nullable) por item, sem perder `tab_id` ou `tab_label`.

A consulta é agregada para evitar N+1. A lista de comandas seleciona os IDs autorizados do venue antes de consultar vínculos de mesa. Evitar qualquer associação por nome: dois clientes homônimos não devem misturar saldo.

## Verificação

- `apps/api/tests/test_dispatch.py`: duas comandas na mesa, movimentação, projeção de produção, histórico sem mesa e fallback
- `cd apps/web && npm run test:identity && npm run typecheck`
- `cd apps/attendance-android && ./gradlew test`
- E2E do Atendimento e de fluxo de mesas/QR após deploy em ambiente de teste
