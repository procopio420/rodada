# Spec 003 — Dispatch Operacional

**Status:** Draft

## Objetivo

Transformar eventos do PDV/fulfillment em uma fila explícita de trabalho para a equipe durante horário de pico, **sem transformar a medição do trabalho em trabalho adicional para o staff**.

A regra de UX para entrega é:

> **happy path sem taps; interação humana para exceção.**

O sistema deve continuar sabendo — ou estimando com honestidade — quando um item foi retirado e entregue, mas não pode exigir que o garçom marque manualmente cada passagem de estado.

## Histórias

### DSP-001 — Zonas e pontos
Manager define Zones e ativa/move ServicePoints durante a noite.

### DSP-002 — Service request
Staff registra chamada de atendimento/conta para um ponto/tab.

### DSP-003 — Delivery task
Quando itens ficam `READY`, o sistema cria/atualiza uma tarefa de entrega com destino atual da Tab e a exibe na fila operacional.

### DSP-004 — Ownership sem bloquear o fluxo
Uma tarefa pode ter responsável explícito ou inferido. Claim manual é permitido quando ajuda coordenação, mas **não é pré-requisito para retirar ou entregar um item**.

### DSP-005 — SLA visual
Tarefas abertas ganham severidade por idade configurável. Itens `READY` mais antigos sobem na fila de atenção.

### DSP-006 — Retirada e entrega passivas
`PICKED_UP` e `DELIVERED` podem ser produzidos por inferência a partir de sinais operacionais.

Sinais possíveis, combináveis:

- presença/proximidade do dispositivo do staff na área de passe quando há item `READY`;
- saída da área de passe logo após o contato;
- deslocamento entre Zones;
- proximidade do destino atual da Tab, Table ou ServicePoint;
- permanência curta e plausível no destino;
- sequência temporal compatível com uma entrega;
- associação daquele staff a um DeliveryRun;
- confirmação natural do cliente quando já existir no fluxo guest;
- correções/exceções posteriores feitas pelo staff.

Nenhum sinal isolado precisa ser tratado como verdade absoluta.

### DSP-007 — Proveniência e confiança
Todo marco de retirada/entrega deve registrar como foi obtido.

```text
source:
  MANUAL
  INFERRED
  CORRECTED

confidence:
  0.0 .. 1.0
```

Para inferência, persistir pelo menos:

- `occurred_at` estimado;
- `source=INFERRED`;
- `confidence`;
- versão/regra do inferidor;
- sinais/evidências resumidos;
- staff provável quando houver confiança suficiente.

A UI pode mostrar linguagem como **“provavelmente retirado”** ou **“entrega inferida”** quando a confiança não justificar afirmação categórica.

### DSP-008 — Correção por exceção
O fluxo normal não pede confirmação.

Se algo estiver errado, staff pode corrigir rapidamente:

- `não foi retirado`;
- `não foi entregue`;
- `entregue em outro destino`;
- `marcar como entregue`.

Correção gera evento auditável e nunca apaga o evento inferido original.

### DSP-009 — Auto-resolução operacional
Uma DeliveryTask pode sair automaticamente da fila ativa quando a política do Venue considerar a inferência suficientemente confiável.

Baixa confiança não deve fabricar precisão. Nesses casos o sistema pode manter o item em atenção, degradar para estado “provável” ou usar apenas o dado para análise, conforme a política operacional.

### DSP-010 — Run por zona
Staff pode agrupar múltiplas deliveries próximas em um DeliveryRun.

### DSP-011 — Métricas
Sistema calcula, quando disponíveis:

- task open → ownership;
- item ready → picked up;
- picked up → delivered;
- item ready → delivered;
- taxa de inferência vs. confirmação/correção;
- distribuição de confidence;
- taxa de falsos positivos corrigidos.

Dashboards devem permitir separar eventos `MANUAL`, `INFERRED` e `CORRECTED`.

## Estratégia de rollout

### P0 — Zero hardware obrigatório
Rodada já elimina taps obrigatórios.

Com apenas eventos do sistema, tempo e contexto operacional, pode produzir estimativas de baixa confiança e destacar exceções. Métricas devem deixar explícito que são estimadas.

### P1 — Passe/cozinha
Adicionar presença BLE na área de retirada é o primeiro ganho de precisão.

Objetivo principal: inferir **`READY → PICKED_UP`** sem exigir ação do garçom.

### P2 — Zonas
Adicionar beacons por Zone, por exemplo:

- Bar principal;
- Cozinha/passe;
- Salão;
- Calçada;
- Rua;
- Imóvel 2.

Isso permite inferir deslocamento sem rastrear coordenadas exatas.

### P3 — Mesa/ponto físico quando justificar
Mesas ou ServicePoints que precisam de precisão extra podem receber beacon/tag associado ao recurso físico.

A adoção por mesa não é requisito do produto e só entra onde o ganho operacional justificar bateria, manutenção e inventário de hardware.

## Privacidade e arquitetura

Telemetria operacional existe para coordenar o serviço, não para criar vigilância de funcionário.

Regras:

- preferir presença por Zone a coordenadas contínuas;
- armazenar o mínimo necessário para inferir milestones;
- não exigir GPS indoor;
- não tornar BLE/hardware requisito para registrar venda ou preparar pedido;
- realtime e sensores não são fonte financeira de verdade;
- políticas de retenção dos sinais brutos devem ser menores que a retenção dos milestones derivados;
- métricas individuais de staff não devem nascer automaticamente desta telemetria sem spec própria.

## Fora de escopo inicial

- algoritmo automático de otimização de rotas;
- GPS indoor preciso;
- rastreamento contínuo de coordenadas como requisito;
- visão computacional/câmeras para identificar staff ou clientes;
- hardware proprietário obrigatório;
- IA preditiva complexa.

## Regra importante

Dispatch nunca pode ser requisito para registrar venda. Se realtime, BLE ou inferência falhar, o POS continua operando.

Falha da telemetria também **não pode reintroduzir taps obrigatórios no happy path**. O sistema degrada a precisão da métrica e mantém mecanismos simples de exceção.
