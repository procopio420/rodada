# Arquitetura Inicial

## Decisão

Começar como **modular monolith**. As fronteiras abaixo são capacidades de domínio, não microserviços e não exigem um app Django por tabela.

```text
Next.js / PWA
  /staff  /bar  /kitchen  /guest  /owner
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
 Redis/WebSocket = atualização realtime, nunca autoridade
```

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

Service requests, delivery tasks, claims, prioridades, DeliveryRuns e métricas de deslocamento/entrega.

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

Nem todo provider implementa todas as operações.

### cash

CashShift e reconciliação básica do PDV.

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

Catalog availability, fulfillment, table ops e dispatch se beneficiam de realtime.

O socket só avisa que algo mudou. PostgreSQL continua sendo fonte de verdade e toda mutation crítica funciona por API mesmo se Redis/WebSocket cair.

Mudança de disponibilidade deve invalidar/atualizar menus conectados rapidamente, mas a garantia final é a revalidação server-side no confirm Order.

## Monetário

- centavos, nunca float;
- ledger append-oriented;
- mudanças de exposure dentro de transação;
- idempotency key em comandos externos e webhooks.

## Integrações futuras

- Pix/adquirente;
- WhatsApp;
- impressão;
- fiscal;
- delivery;
- estoque por insumo.

NFC/tag já pertence ao modelo de Guest Access/TabIdentifier e não precisa esperar integração externa para existir conceitualmente.
