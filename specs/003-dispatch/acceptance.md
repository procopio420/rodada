# Acceptance — Spec 003

## Frontend piloto — 10/10/2026
- [ ] Web/Android mostram tipo/destino/idade/ownership sem inventar nome ou tempo.
- [ ] Outro operador bloqueia ações; conflito reconsulta, sem sucesso otimista.
- [ ] Resposta ambígua permite verificar mesma task/action; consulta falha não vira fila vazia confirmada.

- [ ] Ponto pode trocar de zona durante a noite.
- [x] READY cria/atualiza uma delivery task idempotentemente.
- [x] Staff vê idade e destino; ownership continua fora do slice inicial.
- [x] Fluxo normal não exige “peguei” ou “saí”; uma única conclusão explícita de entrega existe como exceção operacional P0.
- [ ] Sistema consegue registrar PICKED_UP/DELIVERED inferidos com source e confidence.
- [ ] Evento inferido não é apresentado como confirmação manual.
- [ ] Staff consegue corrigir uma inferência errada com ação curta e auditável.
- [ ] Correção não apaga o milestone/evento original.
- [ ] Ausência/falha de BLE ou outro sensor não impede venda, preparo ou entrega.
- [ ] Falha de telemetria degrada precisão da métrica, não recria passos obrigatórios.
- [ ] DeliveryRun agrupa entregas sem perder associação a cada Tab/OrderItem.
- [ ] Métricas conseguem separar MANUAL, INFERRED e CORRECTED.
- [ ] É possível medir taxa de correção dos eventos inferidos para calibrar confidence.
- [ ] POS continua funcional sem conexão realtime.
