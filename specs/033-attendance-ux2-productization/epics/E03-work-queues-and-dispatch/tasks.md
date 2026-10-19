# E03 — Tarefas executáveis

**Dependências:** E01 contrato de destino, Spec 003/004/026 e Spec 032 para QR futuro. Não duplicar FG84, pickup no balcão ou otimizador de mapa.

- [ ] **E03-01 Auditar payloads:** comparar dispatch/views.py, serializers, ServiceRequestQueue, AttendanceWeb.Delivery e Compose; mapear dados presentes e ausentes, reusar task state.
- [ ] **E03-02 DTO staff-safe:** aditivo e versionado com Tab/Occupancy/OrderItem/venue autorizado e destino dinâmico quando válido; não incluir session secret nem derivar IDs de label.
- [ ] **E03-03 Backend permission/refresh:** testar cross-Venue, occupancy geração antiga, staff revogado, Tab transferida, task em claim de outro, READY em Tab CLOSED.
- [ ] **E03-04 UI separada Web:** duas filas, contagem, stale/errors independentes, deep links de SERVICE→Tab, BILL→BillSummary, READY→delivery item.
- [ ] **E03-05 Compose:** paridade operacional de duas filas e acesso à Tab/Conta/Item, com lifecycle e volta à tarefa.
- [ ] **E03-06 Claims/exceções:** reusar dispatch mutations, não auto-claim na navegação; tratar pending response/unknown e permissão de outro operador; provenance preservada.
- [ ] **E03-07 Degradação:** sem realtime, usar refetch; fila indisponível não bloqueia novos pedidos; 50 READY + 50 chamados e múltiplas zonas.
- [ ] **E03-08 Gate:** tests API+PostgreSQL, Web+Android e 360/390/430; AC-08..11 PASS. Marca DeliveryRun por mapa como fora de escopo, sem task de implementação neste epic.

**PRs sugeridas:** E03-a projeção e revalidação, E03-b duas filas Web, E03-c Compose/QA.
