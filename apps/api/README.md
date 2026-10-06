# API

Target: Django + DRF modular monolith.

Implementação começa pela Spec 001 e deve manter as fronteiras de domínio abaixo:

```text
apps/
  catalog/
  pos/
  fulfillment/
  dispatch/
  customers/
  relationships/
  ledger/
  payments/
  cash/
  audit/
```

Não criar um app Django por tabela. Os módulos acima representam capacidades de domínio.
