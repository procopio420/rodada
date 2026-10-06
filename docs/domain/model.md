# Modelo de Domínio

## Venue

Estabelecimento. Piloto: Bar do Aderlan.

## StaffMember

Funcionário autenticado com papel/permissões, por exemplo `STAFF`, `CASHIER`, `MANAGER`, `OWNER`.

## Zone

Agrupamento operacional mutável: `Rua`, `Calçada`, `Bar principal`, `Imóvel 2`.

## ServicePoint

Ponto físico efêmero opcional, por exemplo tag `P37`.

Pode ser movido de Zone sem afetar Tab, Customer ou histórico financeiro.

## Customer

Pessoa opcionalmente identificada pelo bar.

Campos mínimos:

- `id`
- `display_name`
- `phone` opcional
- `notes` opcional
- `created_at`

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

Sessão operacional e financeira de consumo.

Pode pertencer a:

- Customer;
- grupo/apelido;
- visitante anônimo.

Pode apontar para `ServicePoint`, mas não depende dele.

Estados mínimos:

```text
OPEN
REQUIRES_ACTION
SETTLING
CLOSED
CANCELLED
```

## Product

Item vendável com preço e estação de fulfillment.

## Order

Solicitação operacional associada a uma Tab.

Um mesmo Tab pode ter vários Orders ao longo da noite.

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

Métodos inicialmente:

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

Garantias e pré-autorização ficam fora do P0. Quando entrarem, a fórmula evolui por spec.

## Operating Limit

Máxima exposição que pode continuar sem ação adicional.

O relacionamento fornece um default. A Tab pode receber override temporário.

Quando:

```text
open_exposure >= operating_limit
```

novos lançamentos devem exigir uma ação:

- receber parcial;
- aumentar limite com permissão;
- encerrar/regularizar.

## AuditEvent

Evento imutável de auditoria para mutations relevantes.

Exemplos:

- relacionamento alterado;
- limite alterado;
- tab aberta/fechada;
- charge criada/cancelada;
- payment confirmado/revertido;
- override realizado.
