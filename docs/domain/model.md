# Modelo de Domínio

## Venue

Estabelecimento. Piloto: Bar do Aderlan.

Mantém configuração operacional tipada, como timezone/business-date cutoff e referências às políticas dos domínios que as possuem. Não existe um "settings JSON" arbitrário capaz de contornar validações de domínio.

## StaffMember

Identidade humana de um funcionário. Papel e autorização são definidos por membership no Venue, não por confiança na UI nem pelo dispositivo.

## VenueStaffMembership

Relação StaffMember ↔ Venue, com status `ACTIVE | SUSPENDED | REVOKED`, papel-base `STAFF | CASHIER | MANAGER | OWNER` e overrides explícitos de capability quando realmente necessários.

## StaffSession

Sessão autenticada e revogável de StaffMember, opcionalmente ligada a um DeviceRegistration. Comandos pendentes capturados durante perda de rede são reautorizados no servidor antes de aplicação.

## DeviceRegistration

Instalação/dispositivo operacional conhecido por um Venue, com trust state `UNTRUSTED | TRUSTED | REVOKED`.

Device trust acelera a operação e a troca de operador, mas **não substitui autenticação nem concede capability**.

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

## PartySizeObservation

Observação explícita e versionada da quantidade de pessoas/covers. O alvo canônico é `TableOccupancy`; uma `Tab` sem ocupação pode receber a observação como fallback.

Ausência de observação significa `UNKNOWN`, nunca 0 ou 1 inferido. Múltiplas Tabs na mesma ocupação compartilham o mesmo contexto de covers, e analytics por cover devem expor a cobertura de dados conhecidos/desconhecidos.

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

## TabTransfer

Operação imutável que move **responsabilidade financeira aberta** entre Tabs sem reescrever a origem histórica de Order, OrderItem, Charge, Payment ou Refund.

Split, movimento de itens/responsabilidade e merge de duplicatas geram efeitos balanceados entre source/destination. No P0, Payment ou Refund confirmado bloqueia transferências financeiras de Tab.

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


## ProductVariant

Escolha única da forma-base vendável de um Product, por exemplo tamanho 300/500 ml ou normal/duplo. Pode possuir delta de preço e disponibilidade operacional próprios.

## ModifierGroup

Grupo estruturado de customização de Product com modo `SINGLE | MULTI`, limites mínimo/máximo, ordenação e defaults.

## ModifierOption

Escolha dentro de ModifierGroup, com delta de preço em centavos, ativação e disponibilidade operacional. Adicionais, sabores e remoções como `SEM cebola` são modifiers; trabalho independente em outra estação deve virar OrderItem próprio.

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

## OrderCorrection

Registro imutável de correção após confirmação: cancelamento, item errado, mudança do cliente, remake, replacement, rejeição, complaint ou outra exceção.

Nunca edita o snapshot original. Remake/replacement gera **novo OrderItem** ligado ao original; efeitos financeiros são append-only via Adjustment/Refund.

## WasteMarker

Marcador operacional opcional para item preparado e não servido, remake descartado, spoilage ou exceção similar. Não representa automaticamente baixa de estoque nem lançamento contábil.

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

Valor recebido ou em processo de recebimento contra uma Tab. Payment nunca pertence à Table.

Estados conceituais:

```text
CREATED
PENDING
PROCESSING
AUTHORIZED
CONFIRMATION_PENDING
CONFIRMED
FAILED
CANCELLED
PARTIALLY_REFUNDED
REFUNDED
```

Métodos iniciais:

```text
TAP_TO_PAY
PIX
CARD_ONLINE
CASH
EXTERNAL_TERMINAL
OTHER
```

Campos conceituais incluem valor/moeda, método, provider opcional, referência externa, timestamps de lifecycle, ator e separação entre principal e gorjeta quando aplicável.

Regras:

- uma Tab pode receber múltiplos Payments;
- pagamento parcial é nativo;
- saldo deriva do ledger, não de booleano `paid`;
- frontend não confirma pagamento por conta própria;
- `CONFIRMATION_PENDING` representa estado externo ambíguo e bloqueia retry cego equivalente;
- provider/adquirente fica atrás de adapter/porta própria;
- pagar/fechar a última Tab não libera TableOccupancy;
- Payment confirmado não é apagado para representar estorno.

## PaymentAttempt

Tentativa idempotente de execução de um Payment por provider/método.

Mantém pelo menos `payment_id`, `idempotency_key`, referência do provider, status, timestamps e erro normalizado quando houver.

Retries não podem duplicar cobrança já confirmada.

## ProviderEvent

Inbox idempotente de webhook/evento externo, identificada por provider + provider_event_id e protegida contra processamento duplicado.

## Refund

Estorno total ou parcial de Payment confirmado.

Refund preserva o Payment original, registra valor/ator/status/referência externa e produz o efeito financeiro reverso no ledger.

## Adjustment

Efeito financeiro append-only que altera responsabilidade da Tab sem reescrever Charge/Product/OrderItem.

Kinds canônicos:

```text
ITEM_DISCOUNT
TAB_DISCOUNT
COURTESY
SERVICE_CHARGE
SERVICE_CHARGE_REDUCTION
CORRECTION
REVERSAL
```

Percentuais usam basis points inteiros e valores monetários usam centavos. Taxa de serviço **não é Product**.

## AdjustmentAllocation

Alocação persistida e determinística de Adjustment de Tab entre Charges elegíveis, usada para reporting, transferências e refunds.

## Exposure

```text
open_exposure = confirmed_charges - confirmed_payments + adjustments_effect
```

Garantia/pré-autorização entra em spec futura.

## Operating Limit

Máxima exposição permitida sem ação adicional. Pode vir do Relationship e receber override na Tab.

## CashPoint

Ponto físico/gaveta onde dinheiro é mantido. Um Venue pode começar com um único CashPoint.

## CashShift

Período de custódia operacional de um CashPoint, com estados `OPEN | COUNTING | CLOSED`, fundo inicial, snapshot de valor esperado, contagem, divergência e estado de revisão.

Há no máximo um shift ativo por CashPoint.

## CashMovement

Movimento físico append-only ligado a CashShift:

```text
OPENING_FLOAT
CASH_PAYMENT
CASH_REFUND
SUPPLY
WITHDRAWAL
CORRECTION
```

Troco não infla valor esperado: `amount_tendered - change_given = payment amount`. Fechamento histórico não é reescrito por correção tardia.

## ReceiptDocument

Snapshot/referência reproduzível de documento derivado de fatos canônicos: `CUSTOMER_CHECK | PAYMENT_RECEIPT | DIGITAL_RECEIPT | PRODUCTION_TICKET`.

No P0 é não fiscal. Recibo definitivo de pagamento exige Payment canonicamente confirmado.

## PrinterEndpoint

Dispositivo de impressão atrás de adapter. Impressora nunca é fonte de verdade de Order, Fulfillment ou Payment.

## PrintJob

Entrega idempotente de ReceiptDocument a PrinterEndpoint. Retry preserva a mesma identidade lógica; reprint explícito cria novo job ligado ao anterior e é marcado como reimpressão.

## OperationalAlert

Episódio persistido de condição acionável derivada de fatos canônicos.

Severidade: `INFO | WARNING | DANGER`.

Lifecycle: `ACTIVE | ACKNOWLEDGED | RESOLVED | EXPIRED`.

Acknowledgement não resolve a condição. Dedupe/cooldown evitam ruído; auto-resolution depende da condição canônica deixar de existir. Gerência, alertas in-app e push usam o mesmo OperationalAlert.

## NotificationDelivery

Tentativa idempotente de entregar um OperationalAlert por `IN_APP` ou `PUSH`. Falha/supressão de entrega nunca altera o estado canônico do alerta.

## AuditEvent

Evento imutável para mutations relevantes.
