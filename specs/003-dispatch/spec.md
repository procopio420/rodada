# Spec 003 — Dispatch Operacional

**Status:** Draft

## Objetivo

Transformar eventos do PDV/fulfillment em uma fila explícita de trabalho para a equipe durante horário de pico.

## Histórias

### DSP-001 — Zonas e pontos
Manager define Zones e ativa/move ServicePoints durante a noite.

### DSP-002 — Service request
Staff registra chamada de atendimento/conta para um ponto/tab.

### DSP-003 — Delivery task
Quando itens ficam `READY`, o sistema pode criar tarefa de entrega com destino atual da Tab.

### DSP-004 — Claim
Funcionário assume uma tarefa. Fica visível quem está responsável.

### DSP-005 — SLA visual
Tarefas abertas ganham severidade por idade configurável.

### DSP-006 — Conclusão
Concluir delivery marca timestamp e pode mover itens para `DELIVERED`.

### DSP-007 — Run por zona
Staff pode agrupar múltiplas deliveries próximas em um DeliveryRun.

### DSP-008 — Métricas
Sistema calcula tempos:

- task open → claim;
- claim → done;
- item ready → picked up;
- picked up → delivered.

## Fora de escopo

- algoritmo automático de otimização de rotas;
- GPS indoor;
- localização contínua de funcionário;
- IA de previsão;
- hardware proprietário.

## Regra importante

Dispatch nunca pode ser requisito para registrar venda. Se realtime falhar, o POS continua operando; tarefas podem ser reconstruídas da fonte de verdade.
