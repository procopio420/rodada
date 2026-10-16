# Epic E03 — Agora: Atendimentos separados de Entregas

**Prioridade P0** · Owner: Dispatch + Attendance Web/Compose · Depende de E01 para navegação contextual. **Somente contrato.**

## Motivação
Na Web atual, ServiceRequestQueue retorna id, task_type, state, destination_label e claimed_by_id; não oferece Tab/Occupancy navegável. DeliveryQueue tem task/Item mas UI de staff usa labels. É proibido inferir TabId pelo texto “Mesa 08”. A UX 2.0 quer abrir o **trabalho específico**.

## Comportamento
- Agora tem duas filas/tabs: **Atendimentos** = SERVICE_REQUEST/BILL_REQUEST; **Entregas** = DeliveryTasks READY. Contadores, prioridades e freshness independentes. No pico, 50+ tasks com estado vazio/loading/erro/atualização.
- Chamada de sessão Guest com vínculo autorizado abre **Tab** no contexto do pedido de atendimento; pedido de conta abre **BillSummary da Tab**. Se não há Tab segura, navegar a Mesa ativa e escolher explicitamente; se occupancy revogada, revalidar/mostrar estado indisponível, sem escolha por nome.
- Uma delivery READY abre item/quantidade/estação/destino e tarefa exatos, inclusive Tab já financeiramente CLOSED. Abrir não assume nem conclui. Se produção/destino mudou, stale state e recovery sem mutation.
- Claim e completion usam regras canônicas de autoria e idempotência, com reauth/roles já existentes quando pertinentes. “PICKED_UP”/“DELIVERED” podem ser inferidos ou registrados por exceção conforme Spec 003; **não introduzir toque obrigatório somente para telemetria**.
- Entregas em lote por zona e mapa ótimo **não são gate desta integração**. Mostrar individual corretamente agora; reservar arquitetura para DeliveryRun futuro sem simular ganho de rota.
- A fila não desaparece quando o staff navega ou quando reconnect falha. Outro operador pode assumir a tarefa; o staff recebe estado atualizado, não conclui tarefa alheia.

## API mínima
Adicionar projeção staff-safe com task_id/type/state, tab_id quando válido, occupancy_id/generation, table_id/zone, OrderItemID para READY e capability/status. Preferir identificadores canônicos existentes do DispatchTask e assignment; revalidar no servidor no momento da operação, com Venue-scoped queries. Guest tokens/QR públicos não são retornados a staff.

## Negativos
Nenhum pagamento é confirmado por um BILL_REQUEST; nenhum entrega por abrir tela; nenhum texto/label revela Tab privada. Dispatch indisponível não bloqueia API de venda.

## Aceite
AC-08..11 geral. Replay de request_id Guest não duplica chamada. Cenário QR da Tab A e B na mesma Mesa, tasks velhas após release, rota sem destino e staff rival.
