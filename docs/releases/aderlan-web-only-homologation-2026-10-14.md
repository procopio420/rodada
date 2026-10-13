# Rodada — roteiro e auditoria E2E Web do piloto (14/10/2026)

Data da auditoria: 13/10/2026. Escopo: piloto assistido **Web-only** na demo existente. Android, PSP/Tap/Pix integrado fora do caminho crítico. Não declarar GO por testes automatizados isolados. Usar Venue de teste isolada e contas autorizadas; nunca executar testes mutáveis automaticamente sobre comandas reais. Recebimento manual só após confirmação de dinheiro ou comprovante de maquininha externa. Fiscal/contingência com responsável aprovado e VR System disponível.

## Roteiro presencial (cada etapa: PASS/FAIL/BLOCKED, operador, hora, URL, SHA, IDs, evidência)

1. Login autorizado em /attendance, /bar, /kitchen, /manage, /cash; validar permissões de cada papel.
2. Atendimento Web: ocupar mesa livre, abrir comanda (com e sem apelido), associá-la à mesa; testar duas comandas na mesma ocupação.
3. Confirmar pedido com produto BAR e KITCHEN, quantidade e observação; conferir preço congelado, uma única cobrança e fila correta em cada estação. Repetir comando/reload sem duplicar.
4. Confirmar que item entra como NEW, **não PREPARING**; iniciar preparo explicitamente, marcar READY e concluir entrega no Atendimento Web.
5. Guest QR: abrir comanda e pedir antes de existir garçom responsável; verificar visibilidade para staff, ownership/claim, isolamento entre clientes e não duplicação.
6. Indisponibilizar item durante carrinho de outro operador/guest; pedido deve rejeitar indisponível sem cobrar ou perder pedidos já confirmados.
7. Registrar correção/cancelamento/remake com motivo e trilha auditável; conferir impacto em fila e ledger, sem apagar histórico.
8. Receber dinheiro ou maquininha externa **fora do Rodada**, conferir liquidação, registrar manualmente o método/valor; testar parcial, troco e saldo. Nunca registrar intenção/pending como pago.
9. Fechar comanda só com saldo/pending válidos; conferir que fechar última comanda não libera mesa automaticamente.
10. Encerrar caixa, contar, conferir recebimentos por método, diferenças e revisão gerencial; comparar relatório, recibos externos e comandas.
11. Liberar/limpar mesa explicitamente; QR/sessão antiga deve perder acesso e não poder fazer novos pedidos.
12. Simular queda de Wi-Fi, reload, expiração de sessão, queda de KDS e retorno; verificar recuperação sem perda/duplicação e contingência manual.
13. Verificar backup/restore, isolamento do estabelecimento, procedimento fiscal aprovado, treinamento e rollback para VR System antes de atender clientes reais.

## Matriz de cobertura observada no código em main (auditoria estática; NÃO executada agora)

| Etapa | Evidência de teste existente | Cobertura / lacuna |
| --- | --- | --- |
| Login e autorização | `apps/web/tests/integration/workflows.spec.ts` (login, 403, sessão expirada, revogação, refresh); `attendance.spec.ts` | **PARCIAL**: papéis/fluxos físicos na demo não homologados |
| Mesa/comanda no Atendimento | `attendance.spec.ts` (UI abrir comanda, ocupar/associar/liberar/limpar mesa); `frontend-pilot.spec.ts`; API `test_hospitality_tables.py` | **PARCIAL**: duas comandas/ocupação e claim por operador em browser integrado não comprovados aqui |
| Pedido BAR+KITCHEN | `workflows.spec.ts` (API confirma ambos, UI filas); `attendance.spec.ts` (UI confirma KITCHEN); `test_full_shift_smoke.py` | **PARCIAL**: falta jornada UI Atendimento com ambos e assert de cobrança única após retry/reload |
| NEW -> PREPARING -> READY -> entregue | `workflows.spec.ts` (estado NEW, clique Iniciar preparo, PREPARING/READY); `attendance.spec.ts` (entrega UI) | **PARCIAL**: transição ACCEPTED/PREPARING/READY feita por API no teste de entrega; unificar UI |
| QR e revogação | `workflows.spec.ts` (guest pede e recebe 403 após release); `service-requests.spec.ts`; `test_guest_access.py` | **PARCIAL**: QR antes do claim do garçom e ownership/atendimento não comprovados end-to-end |
| Item indisponível | `workflows.spec.ts` (UI desabilita, API confirma indisponibilidade); testes API de catálogo/concorrência | **PARCIAL**: corrida no carrinho e atomicidade do pedido via UI não comprovadas |
| Correção/remake | `apps/api/tests/test_corrections.py`, `test_partial_cancellation_concurrency.py`, testes visuais | **PARCIAL**: jornada operacional Web completa não demonstrada nesta auditoria |
| Pagamento externo/manual | `zz-pricing.spec.ts` (API pagamentos OTHER, parcial/final, UI pricing); `attendance.spec.ts` (403 em pagamento não autorizado); `test_full_shift_smoke.py` | **PARCIAL**: falta registro manual pela UI com comprovante externo e confirmação independente |
| Fechar comanda | `zz-pricing.spec.ts` (API close, saldo zero); `test_full_shift_smoke.py` | **PARCIAL**: UI Web fechar e mesa continuar ocupada não comprovados conjuntamente |
| Caixa/gerência/relatórios | `workflows.spec.ts` (UI abertura, divergência/revisão, CSV/relatório); `zz-pricing.spec.ts` (conciliação) | **PARCIAL**: não há turno Web unificado com conciliação de recebimentos externos reais |
| Liberar/limpar + QR antigo | `attendance.spec.ts` (UI liberação/limpeza); `workflows.spec.ts` (guest 403 revogado) | **PARCIAL**: testes separados, integração UI completa não comprovada |
| Offline/KDS/backup/fiscal/rollback | `test_full_shift_smoke.py`, `test_restore_rehearsal.py`, `docs/releases/aderlan-onsite-acceptance.md` | **NÃO COBERTO como E2E browser físico**; exigir ensaio onsite e aceite externo |

## Casos não felizes P0 para ampliar E2E

- Dois operadores disputam mesa/claim ou confirmam o mesmo pedido; um único resultado canônico e UI coerente.
- Cliente QR chega primeiro, abre comanda/pede sem responsável; atendimento assume sem criar comanda duplicada.
- Item esgota após entrar no carrinho; erro explícito, sem cobrança e sem perda do pedido anterior.
- Double click, resposta POST perdida, timeout, refresh, reconnect e replay da mesma chave; um Order/Charge/Payment, nunca dois.
- Produção não inicia automaticamente; botão Iniciar preparo é necessário. Correção/remake após preparo conserva origem, motivo e trilha.
- Estação BAR/KITCHEN desconecta e volta; itens não desaparecem, snapshot reconcilia sem duplicar.
- Sessão expira/revoga durante pedido; operação proibida não aparece como sucesso; isolamento entre Venue e guests.
- Pagamento externo falha, comprovante ausente, pagamento parcial, troco insuficiente, valor acima do saldo, tentativa de fechamento com saldo ou pending; nunca estado falso de pago.
- Fechamento de caixa com divergência, recontagem e revisão por gerente; totais por método batem com comprovantes e histórico.
- Mesa com duas comandas: fechar uma não libera mesa; liberar mesa revoga QR anterior; novo visitante não vê histórico.
- Rede cai após confirmação e antes da resposta; retorno mostra estado canônico sem pedido duplicado.
- Impressora/fiscal indisponível: contingência autorizada ou NO-GO, nunca tratar recibo não fiscal como documento fiscal.

## Resultado e prioridade

**Auditoria estática: cobertura PARCIAL; nenhuma execução nova de Playwright ou homologação na demo foi realizada por este documento.** Há testes browser reais, API, unitários e visuais, mas a existência de asserts dispersos não equivale a E2E único de turno Web.

P0: adicionar teste integrado Playwright `web-only-assisted-shift.spec.ts` em infraestrutura descartável, com cliques reais para mesa/comanda/pedido BAR+KITCHEN/preparo/entrega/recebimento manual/fechamento/caixa/revogação QR; asserts de ledger canônico e não duplicação. Adicionar testes separados de falha por cenário, não esconder falhas com mocks. Rodar contra banco isolado, nunca demo compartilhada. Em seguida realizar homologação presencial na demo atual com dados de teste identificados e signoff. Manter Android/PSP fora da trilha crítica.
