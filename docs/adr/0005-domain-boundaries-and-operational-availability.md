# ADR 0005 — Fronteiras de domínio e disponibilidade operacional

**Status:** Accepted

## Contexto

Rodada começou com um módulo conceitual `pos` contendo Tabs, Orders e Charges, enquanto Ledger também existia como fronteira própria. Depois, Table Ops/Guest Ordering adicionou mesa, ocupação e acesso guest, e a operação de Bar/Cozinha passou a exigir que produtos fossem indisponibilizados durante o serviço.

Sem uma decisão explícita, dois erros ficam prováveis:

1. transformar `pos` num módulo "Deus" que concentra venda, financeiro, salão e produção;
2. implementar "acabou o item" alterando `Product.active` ou apenas escondendo o botão em uma tela.

## Decisão

PDV é o produto/experiência, não uma única fronteira de domínio.

As capacidades canônicas são:

- Venue;
- Floor;
- Catalog;
- Ordering;
- Fulfillment;
- Dispatch;
- Guest Access;
- Customers/Relationships;
- Billing;
- Payments;
- Cash;
- Audit.

Continuamos em modular monolith.

### Disponibilidade

`Product.active` representa configuração/publicação administrativa.

`ProductAvailability` representa se o item pode ser vendido **agora**:

```text
AVAILABLE
UNAVAILABLE
```

A mudança operacional:

- pode ser feita por Bar/Cozinha com permissão na estação e por Manager;
- é auditada;
- é compartilhada por staff, caixa e guest;
- é revalidada server-side na confirmação do Order;
- não altera nem cancela OrderItem já confirmado.

A interface pode receber atualização em realtime, mas realtime não é a garantia de consistência.

## Consequências

### Positivas

- cozinha consegue tirar item do cardápio imediatamente;
- guest ordering não mantém catálogo paralelo;
- carrinho stale não gera venda impossível;
- ativação administrativa continua útil para lifecycle de produto;
- financeiro, salão e produção ficam com ownership mais claro;
- evolução futura para estoque/receita não exige redefinir o significado de `active`.

### Trade-offs

- confirmação do Order ganha uma validação adicional;
- UI precisa tratar item que ficou indisponível entre seleção e submit;
- permissões de estação precisam existir, ainda que com modelo simples no P0.

## Não decidido aqui

- baixa automática de disponibilidade por estoque;
- disponibilidade por horário;
- disponibilidade por variante/complemento;
- múltiplas estações produzindo o mesmo Product;
- previsão automática de ruptura.
