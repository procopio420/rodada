# API

Target: Django + DRF em **modular monolith**.

A organização sugerida por capacidade é:

```text
apps/
  venue/
  floor/
  catalog/
  ordering/
  fulfillment/
  dispatch/
  guest_access/
  customers/
  billing/
  payments/
  cash/
  audit/
```

Não criar um app Django por tabela e não transformar essas fronteiras em microserviços prematuramente.

## Ownership principal

- `venue`: estabelecimento, staff e permissões;
- `floor`: zonas, pontos, mesas e ocupações;
- `catalog`: produto, preço, disponibilidade operacional, autocomplete/resolve-or-create, ProductIcon e routing;
- `ordering`: Tab, Order, OrderItem e confirmação;
- `fulfillment`: preparo/estados por estação;
- `dispatch`: tasks, claims e runs;
- `guest_access`: GuestSession, QR, short code e NFC;
- `customers`: Customer + Relationship;
- `billing`: ledger, charges, payments de domínio, adjustments e exposure;
- `payments`: adapters/integrações de PSP;
- `cash`: turnos e reconciliação;
- `audit`: trilha imutável de mutations.

A Spec 001 deve começar por `venue + catalog + ordering + billing + cash`, com fulfillment mínimo.

Catalog deve expor operações equivalentes a:

```text
suggest_products(venue_id, query, station?) -> ProductSuggestion[]
resolve_or_create_product(venue_id, name, defaults) -> Product
```

`resolve_or_create_product` precisa ser transacional e respeitar a chave de nome normalizada do Venue. Product existente sempre mantém seu ProductIcon; Product novo cria sua identidade visual 1:1 e dispara geração assíncrona automaticamente.

Ver `docs/architecture/overview.md` e ADR 0005 antes de criar novos módulos.
