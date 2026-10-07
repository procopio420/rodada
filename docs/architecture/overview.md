# Arquitetura Inicial

## Decisão

Começar como **modular monolith**. As fronteiras abaixo são capacidades de domínio, não microserviços e não exigem um app Django por tabela.

```text
Rodada Atendimento (Android nativo — Kotlin/Compose)
Rodada Cozinha / Bar / Cliente / Gerência (Web/PWA)
                 |
                 v
           Django + DRF
                 |
     +-----------+-----------+
     |                       |
  Venue/Floor              Catalog
     |                       |
     +-------> Ordering <-----+
                  |
             Fulfillment
                  |
               Dispatch

 Customers/Relationships --> Ordering

 Ordering --> Billing/Ledger --> Payments
                    |
                   Cash

             Audit atravessa mutations relevantes

 PostgreSQL = fonte de verdade
 SSE/event delivery = atualização realtime, nunca autoridade
```

## Superfícies de aplicação

As superfícies são separadas por função operacional, não apenas por rota/permissão de um frontend único:

| Superfície | Tecnologia alvo | Responsabilidade principal |
| --- | --- | --- |
| Rodada Atendimento | Android nativo — Kotlin + Jetpack Compose | Tab, pedidos, mapa/atendimento e cobrança no próprio celular |
| Rodada Cozinha | Web/PWA | produção, fila da cozinha e disponibilidade |
| Rodada Bar | Web/PWA | produção, fila do bar e disponibilidade |
| Rodada Cliente | Web/PWA | QR, pedido, acompanhamento e pagamento autorizado |
| Rodada Gerência | Web/PWA responsiva mobile-first | cockpit de exceções ao vivo, fechamento, pessoas e analytics |

As superfícies compartilham API, contratos, semântica visual e domínio, mas **não precisam compartilhar implementação de UI**. Em especial, o Atendimento não deve depender de bridge web para capacidades centrais do device.

## Regra de estrutura

**PDV é o produto; não precisa ser um módulo que concentra tudo.**

A versão anterior colocava Tab, Order e Charge juntos em `pos` ao mesmo tempo em que existia `ledger`. Isso cria ownership ambíguo. A divisão canônica passa a ser:

### venue

Venue, StaffMember e permissões operacionais.

### floor

Zone, ServicePoint, Table e TableOccupancy.

Mesa/ocupação são contexto físico e ciclo operacional; nunca ledger.

### catalog

Product, preço, ativação administrativa, disponibilidade operacional, ProductIcon e routing para FulfillmentStation.

`Product.active` responde "este produto faz parte/publica no catálogo?".
`ProductAvailability` responde "podemos vender este produto agora?".

Bar/Cozinha alteram disponibilidade uma vez; staff, caixa e guest consomem a mesma fonte de verdade.

Criação rápida, autocomplete/resolve-or-create e ícones gerados por IA continuam dentro da capacidade de Catalog. O catálogo resolve primeiro um Product existente por busca normalizada; só cria quando não houver match exato. O ProductIcon é 1:1 e estável com o Product. O domínio expõe uma porta `CatalogIconGenerator`; adapters de geração de imagem/storage ficam em infraestrutura. Novo Product dispara a geração automaticamente e falha do provider não impede criar Product nem fazer pedido.

### ordering

Tab, Order, OrderItem, snapshot de preço e regras de confirmação.

Ordering não é dono de pagamento e não é dono de mesa. Ele referencia esses contextos.

Na confirmação do Order, Ordering consulta/valida Catalog dentro da operação consistente. UI stale nunca pode vender item indisponível.

### fulfillment

Fila por estação e estados operacionais de OrderItem:

```text
NEW
ACCEPTED
PREPARING
READY
PICKED_UP
DELIVERED
CANCELLED
```

Fulfillment prepara pedidos já confirmados. Indisponibilizar Product não cancela item já confirmado.

### dispatch

Service requests, delivery tasks, ownership explícito ou inferido, prioridades, DeliveryRuns e métricas de deslocamento/entrega.

Dispatch também é dono da coordenação da **telemetria passiva** usada para inferir `PICKED_UP`/`DELIVERED`. Sinais de presença (por exemplo BLE no passe ou por Zone) entram por adapters e nunca viram dependência do domínio central.

A fronteira é:

```text
presence/sensor adapters
        |
        v
dispatch inference
        |
        v
FulfillmentMilestone (source + confidence)
        |
        v
fulfillment operational state
```

O happy path não exige taps de “peguei”/“entreguei”. Falha de sensor degrada confiança/métrica, não bloqueia serviço nem recria etapas obrigatórias.

### guest_access

GuestSession, TabIdentifier, QR de Table, QR dinâmico de Tab, código curto, NFC e autorização de guest ordering.

Guest Access resolve **quem pode agir em qual Tab/contexto**; não duplica regra de catálogo, financeiro ou fulfillment.

### customers

Customer + Relationship local do Venue.

### billing

Charge, Payment, Adjustment, Exposure, OperatingLimit e invariantes financeiras.

`OrderItem` confirmado pode originar Charge idempotente, mas Ordering não mantém saldo próprio.

### payments

Adapters de PSP, intents/records, idempotência e webhooks.

```text
PaymentProvider
  create_pix(...)
  authorize_card(...)
  capture(...)
  refund(...)
  get_status(...)
```

Para Tap on Phone, o **primeiro adapter do MVP é Paytime**:

```text
Rodada Atendimento
      |
      v
TapToPayProvider
      |
      +--> PaytimeTapProvider  (default inicial)
      +--> outros adapters     (futuros)
```

O SDK Paytime roda integrado ao aplicativo Android do Atendimento: o happy path não entrega a cobrança para outro aplicativo. Marca/provider não entram nas entidades centrais de Tab, Charge ou Payment além de referências técnicas necessárias para operação e auditoria.

A escolha é inicial, não exclusiva: a configuração de pagamentos é por Venue e a arquitetura deve permitir novos providers sem reescrever o fluxo do Atendimento.

Nem todo provider implementa todas as operações.

### cash

CashShift e reconciliação básica do PDV.

### management

Read models, alertas e relatórios gerenciais derivados dos fatos canônicos dos demais módulos.

Management **não é dono** de Tab, Order, Payment, Table ou Product. Ele projeta esses fatos para leitura rápida e análise.

Fluxo conceitual:

```text
domain transaction
      |
      v
persisted fact / outbox
      |
      v
management projection
      |
      +--> ManagementLiveSnapshot
      +--> DailyOperationsSummary
      +--> MonthlyManagementSummary
      |
      v
API + realtime invalidation
      |
      v
Rodada Gerência
```

Princípios:
- PostgreSQL continua fonte de verdade;
- projeções são idempotentes e reconstruíveis;
- SSE/Redis/event delivery não definem números financeiros;
- métricas financeiras vêm do ledger/estado canônico;
- milestones inferidos preservam provenance;
- relatórios usam `business_date` configurável por Venue para não quebrar operações que atravessam meia-noite;
- consultas da home não devem executar joins analíticos pesados em todos os módulos.

### audit

Registro imutável de mutations relevantes, incluindo cancelamentos, overrides e mudanças de disponibilidade.

## Dependências permitidas

Preferir dependências direcionais:

```text
floor ---------> ordering <--------- customers
catalog -------> ordering
ordering ------> fulfillment ------> dispatch
ordering ------> billing ----------> payments
billing -------> cash
ordering ------> management
fulfillment ---> management
dispatch ------> management
floor ---------> management
catalog -------> management
billing -------> management
payments ------> management
cash ----------> management
guest_access --> ordering
guest_access --> floor
```

Evitar:

- Catalog depender de Ordering;
- Floor depender de Billing;
- Guest Access duplicar regras de Catalog;
- Fulfillment alterar ledger diretamente;
- Dispatch ser requisito para registrar venda.

## Realtime

Catalog availability, fulfillment, table ops, dispatch e o cockpit de Gerência se beneficiam de realtime. Telemetria passiva pode usar eventos de presença adicionais, mas esses sinais são auxiliares e não substituem PostgreSQL como fonte de verdade dos milestones persistidos.

O contrato padrão é:
- comandos/mutations canônicas por HTTP;
- atualização server -> client por SSE (`text/event-stream`);
- snapshot inicial + cursor de resume/replay;
- transactional outbox gravada na mesma transação da mudança de domínio;
- Redis opcional para fan-out/coordenação efêmera, nunca como registro único do evento.

PostgreSQL continua sendo fonte de verdade. Se SSE/Redis cair e a API estiver saudável, mutations críticas continuam funcionando e os clientes degradam para revalidation/polling bounded. Ao reconectar, o cliente retoma do cursor quando possível; se a continuidade não puder ser provada, busca snapshot canônico antes de confiar em novos deltas.

WebSocket só deve ser introduzido para uma necessidade contínua realmente bidirecional que HTTP + SSE não atenda de forma limpa.

Mudança de disponibilidade deve invalidar/atualizar menus conectados rapidamente, mas a garantia final é a revalidação server-side no confirm Order.

## Monetário

- centavos, nunca float;
- ledger append-oriented;
- mudanças de exposure dentro de transação;
- idempotency key em comandos externos e webhooks.

## Integrações futuras

- adapters adicionais de adquirência/Tap on Phone além de Paytime;
- WhatsApp;
- impressão;
- fiscal;
- delivery;
- estoque por insumo.

NFC/tag já pertence ao modelo de Guest Access/TabIdentifier e não precisa esperar integração externa para existir conceitualmente.
