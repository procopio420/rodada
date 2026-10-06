# Modelo de Domínio

## Venue

Estabelecimento. Piloto: Bar do Aderlan.

## StaffMember

Funcionário autenticado com papel/permissões, por exemplo `STAFF`, `CASHIER`, `MANAGER`, `OWNER`.

## Zone

Agrupamento operacional mutável: `Rua`, `Calçada`, `Bar principal`, `Imóvel 2`.

## ServicePoint

Ponto/localização operacional genérico e opcional, especialmente útil para dispatch fora do modelo de mesa, por exemplo tag `P37`, balcão ou ponto móvel.

Pode ser movido de Zone sem afetar Tab, Customer ou histórico financeiro.

## Table

Recurso físico do salão.

Campos conceituais mínimos:

- `id` interno;
- `label` humano, por exemplo `24`;
- `zone_id` opcional;
- `service_point_id` opcional para integração com dispatch;
- `public_token` aleatório/opaco usado no QR físico;
- `access_generation` inteiro incrementado ao concluir o ciclo de liberação/limpeza;
- `guest_ordering_mode`;
- `status`;
- timestamps operacionais.

Estados iniciais:

```text
AVAILABLE
OCCUPIED
DIRTY
CLEANING
OUT_OF_SERVICE
```

`Table.status` nunca representa pagamento.

## TableOccupancy

Período em que um grupo usa uma Table.

Campos conceituais:

- `table_id`;
- `generation`;
- `started_at`;
- `released_at`;
- `released_by`;
- `cleaning_started_at`;
- `cleaning_started_by`;
- `ready_at`;
- `ready_by`.

Regras:

- uma Table possui no máximo uma ocupação ativa;
- uma ocupação pode conter zero, uma ou várias Tabs;
- fechar a última Tab **não encerra automaticamente** a ocupação;
- `release table` encerra a presença do grupo e move a mesa para `DIRTY`;
- concluir limpeza move para `AVAILABLE` e incrementa `access_generation`;
- sessões guest da geração anterior deixam de autorizar pedidos.

## Customer

Pessoa opcionalmente identificada pelo bar.

Campos mínimos:

- `id`;
- `display_name`;
- `phone` opcional;
- `notes` opcional;
- `created_at`.

## Relationship

Relação Customer ↔ Venue.

```text
VISITOR
KNOWN
REGULAR
HOUSE
RESTRICTED
```

Possui política/limite default.

## Tab

Sessão operacional e financeira de consumo. **Todo Order pertence a uma Tab.**

Uma Tab pode ser:

- anônima;
- identificada apenas por `display_label`/apelido;
- ligada a Customer/Relationship;
- associada opcionalmente a uma TableOccupancy;
- associada a ServicePoint sem mesa;
- acessada por zero ou vários TabIdentifiers.

Estados mínimos:

```text
OPEN
REQUIRES_ACTION
SETTLING
CLOSED
CANCELLED
```

Regras:

- não depende de Table;
- várias Tabs podem compartilhar a mesma TableOccupancy;
- uma Tab pode mudar de localização/ocupação sem mudar de identidade financeira;
- fechar uma Tab não implica liberar a mesa;
- identidade do cliente pode ser adicionada depois sem migrar pedidos/ledger.

## TabIdentifier

Identificador técnico opcional usado para resolver ou autorizar acesso a uma Tab.

Tipos iniciais:

```text
SHORT_CODE
GUEST_SESSION
QR_TOKEN
NFC_TAG
```

Campos conceituais:

- `tab_id`;
- `kind`;
- `token_hash` ou referência segura equivalente;
- `valid_from`;
- `expires_at` opcional;
- `revoked_at` opcional;
- `table_occupancy_id` opcional;
- `access_generation` opcional;
- metadata/auditoria.

Observações:

- nome/apelido é `Tab.display_label`, não segredo;
- perfil Rodada resolve Tab via Customer/session autenticada, não precisa ser duplicado como token;
- NFC é conveniência operacional e deve ser revogável/reutilizável;
- tokens públicos devem ser aleatórios, não sequenciais;
- token bruto sensível não deve ser persistido quando hash é suficiente.

## GuestSession

Sessão do navegador do cliente.

Pode:

- nascer após scan do QR da mesa;
- criar uma nova Tab quando permitido;
- assumir uma Tab existente por código/fluxo autorizado;
- ficar ligada a `TableOccupancy + access_generation`;
- ser revogada pelo staff ou automaticamente no fim da ocupação.

Não exige Customer.

## Product

Item vendável com preço e estação de fulfillment.

## Order

Solicitação operacional **sempre associada a uma Tab**.

Um mesmo Tab pode ter vários Orders ao longo da noite.

Campos relevantes incluem `source`:

```text
STAFF
CASHIER
GUEST
```

Origem não altera o modelo financeiro nem a fila de fulfillment.

## OrderItem

Produto + quantidade + preço capturado + estado operacional.

Estados iniciais:

```text
NEW
ACCEPTED
PREPARING
READY
PICKED_UP
DELIVERED
CANCELLED
```

Nem todo item precisa percorrer todos os estados; uma cerveja pode ir de `ACCEPTED` para `READY` imediatamente.

## DispatchTask

Trabalho operacional que precisa ser assumido/concluído.

Tipos iniciais:

```text
SERVICE_REQUEST
DELIVERY
BILL_REQUEST
EXCEPTION
```

Estados:

```text
OPEN
CLAIMED
DONE
CANCELLED
```

## DeliveryRun

Agrupamento de múltiplas entregas, preferencialmente por Zone.

## Charge

Lançamento positivo no ledger, normalmente derivado de OrderItem confirmado.

## Payment

Valor recebido.

```text
PENDING
CONFIRMED
FAILED
REVERSED
```

Métodos iniciais:

```text
PIX
CARD
CASH
OTHER
```

## Adjustment

```text
COURTESY
CORRECTION
REVERSAL
```

## Exposure

```text
open_exposure = confirmed_charges - confirmed_payments + adjustments_effect
```

Garantia/pré-autorização entra em spec futura.

## Operating Limit

Máxima exposição permitida sem ação adicional. Pode vir do Relationship e receber override na Tab.

## CashShift

Sessão de caixa usada para registrar abertura, recebimentos e fechamento/reconciliação básica.

## AuditEvent

Evento imutável para mutations relevantes.
