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

## FulfillmentStation

Destino operacional de preparo. No P0 pode começar com identificadores simples como:

```text
BAR
KITCHEN
```

A fronteira importante é conceitual: routing diz **onde preparar**, não se o item está disponível para venda.

## Product

Item configurado no catálogo de um Venue.

Campos conceituais mínimos:

- `id`;
- `venue_id`;
- `name`;
- `normalized_name`/chave equivalente de busca;
- `price_cents`;
- `active` para configuração/publicação administrativa;
- `fulfillment_station`.

Regras de identidade:

- o campo de nome nas telas de criação usa autocomplete/typeahead do catálogo do Venue;
- correspondência exata por nome normalizado resolve o Product existente;
- se não houver correspondência exata, o Catalog pode criar automaticamente um novo Product ao confirmar a opção **Criar "{nome}"**;
- `resolve_or_create` deve ser transacional para evitar duplicatas em corrida concorrente;
- fuzzy search serve para sugerir, nunca para mesclar Products automaticamente;
- itens realmente diferentes devem ser nomeados de forma distinta, por exemplo `Coca-Cola 350 ml` e `Coca-Cola 600 ml`.

`active=false` não deve ser usado como botão de "acabou agora". Ativação administrativa e disponibilidade operacional têm ciclos de vida diferentes.

## ProductIcon

Identidade visual estável **1:1** pertencente a um Product. O registro nasce junto com o Product, ainda que inicialmente esteja em placeholder/`GENERATING`.

Campos conceituais:

- `product_id` único;
- `source`: `AI_GENERATED | UPLOADED | NONE`;
- `status`: `NONE | GENERATING | READY | FAILED`;
- referência do asset atualmente publicado;
- referência opcional a candidato em geração/revisão;
- `prompt` quando aplicável;
- `style_version`;
- provider/model quando gerado;
- ator/timestamps.

Regras:

- Product e ProductIcon mantêm o mesmo vínculo durante todo o lifecycle do item;
- selecionar Product existente no autocomplete reutiliza seu ProductIcon;
- renomear Product, alterar preço, estação ou disponibilidade não cria outro ProductIcon;
- Product pode ser vendido enquanto o asset ainda não existe, usando placeholder;
- criação sem upload manual dispara geração automaticamente; não existe botão obrigatório de "gerar";
- regenerar preserva o asset publicado até a nova versão estar pronta;
- autocomplete, staff, Bar/Cozinha e Guest resolvem o mesmo asset publicado;
- ProductIcon não deve ser compartilhado entre Products distintos por padrão;
- geração usa o style contract versionado em `docs/product/icon-style.md`;
- dados de Customer, Tab ou Order não fazem parte do contexto de geração.

## ProductAvailability

Estado operacional atual de venda de um Product no Venue.

Estados iniciais:

```text
AVAILABLE
UNAVAILABLE
```

Campos conceituais:

- `product_id`;
- `state`;
- `changed_at`;
- `changed_by`;
- `reason` opcional;
- `version`/mecanismo equivalente para concorrência quando necessário.

Regras:

- cozinha/bar com permissão pode alternar disponibilidade dos produtos da estação;
- manager pode gerenciar disponibilidade de qualquer estação;
- staff, caixa e guest consomem a mesma fonte de verdade;
- item `UNAVAILABLE` não pode ser confirmado em novo Order, independentemente de `source`;
- a API revalida disponibilidade no momento da confirmação do Order;
- carrinho aberto pode ficar stale; a confirmação deve retornar quais itens deixaram de estar disponíveis;
- OrderItem já confirmado preserva histórico, preço e fulfillment mesmo se o Product ficar indisponível depois;
- toda mudança é auditável e deve propagar para as superfícies operacionais em realtime quando o canal existir.


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

A confirmação do Order valida a disponibilidade operacional de todos os produtos. Um item que ficou indisponível depois de ser adicionado ao carrinho deve ser rejeitado explicitamente antes de gerar OrderItem/Charge.

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

`PICKED_UP` e `DELIVERED` não implicam necessariamente confirmação manual do staff. A origem da transição deve ser rastreável por milestone.

## FulfillmentMilestone

Registro auditável de um marco operacional observado, inferido ou corrigido.

Tipos iniciais:

```text
PICKED_UP
DELIVERED
```

Campos conceituais:

- `order_item_id`;
- `kind`;
- `occurred_at`;
- `source: MANUAL | INFERRED | CORRECTED`;
- `confidence` opcional, obrigatório quando `source=INFERRED`;
- `staff_member_id` opcional;
- `inference_version` opcional;
- `evidence_summary` opcional;
- `supersedes_id` opcional para correção.

Regras:

- milestone inferido nunca deve ser indistinguível de confirmação humana;
- correção cria novo registro e preserva o histórico anterior;
- sinais brutos de presença não precisam ter a mesma retenção do milestone derivado;
- `OrderItem.state` pode avançar automaticamente por política operacional, desde que a transição seja rastreável ao milestone;
- ausência de telemetria não impede o fluxo de pedido/preparo/entrega;
- métricas devem conseguir filtrar por `source` e `confidence`.

## DispatchTask

Trabalho operacional que precisa ser coordenado/concluído. Claim explícito pode existir, mas não é obrigatório no happy path de delivery quando ownership/progresso puder ser inferido.

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
