# Tasks — Spec 003

## Frontend piloto — 10/10/2026
- [x] Fila de chamadas Web com freshness/conflito/retry mesma identidade.
- [x] Fila de chamadas Android com ownership, leitura independente e resultado ambíguo.
- [x] Testes e evidência do recorte; navegação exata depende do contrato backend.

- [x] Zone CRUD/config (P0: criação/listagem por Venue e associação auditada da mesa)
- [ ] ServicePoint ativar/mover/desativar
- [x] DispatchTask
- [ ] SLA/severity
- [ ] WebSocket updates
- [x] READY -> delivery task idempotente
- [x] happy path READY -> entrega concluída em uma ação explícita.
- [ ] FulfillmentMilestone com source/confidence/provenance
- [ ] correção auditável de milestone inferido
- [ ] inferência P0 sem hardware com semântica de baixa confiança
- [ ] interface de sinais de presença desacoplada do provider/hardware
- [ ] presença BLE do passe como primeira integração opcional
- [ ] Zone presence opcional
- [ ] política configurável de auto-resolução por confidence
- [ ] DeliveryRun
- [x] timeline/timestamps
- [ ] dashboard operacional
- [ ] métricas segmentadas por MANUAL/INFERRED/CORRECTED
- [ ] métrica de correção/falso positivo da inferência
- [x] tests concorrência/idempotência de task
- [x] tests reconstrução/retry de eventos
- [ ] tests de inferência sem duplicar milestones
- [ ] tests de correção preservando histórico

- [x] Round 2: structured staff/guest requests, safe claim/completion and PostgreSQL concurrent identity test.
