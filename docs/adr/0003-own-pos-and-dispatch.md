# ADR 0003 — Own the POS and Dispatch Core

**Status:** Accepted

## Contexto

A primeira exploração tratava Rodada como uma camada de relacionamento/house account que poderia viver sobre PDVs existentes. Isso reduziria escopo, mas também limitaria justamente os experimentos de operação que queremos fazer no Bar do Aderlan.

## Decisão

Rodada terá seu próprio núcleo transacional de PDV e seu próprio modelo de dispatch.

Integrações com PDVs externos continuam possíveis no futuro, mas não serão a fonte primária de verdade nem definirão o modelo interno do piloto.

## Consequências

- podemos experimentar Tab sem mesa fixa, fulfillment e dispatch de ponta a ponta;
- assumimos responsabilidade por catálogo, pedido, ledger, pagamento, caixa básico e auditoria;
- fiscal, estoque profundo, delivery e contabilidade continuam fora do P0;
- interoperabilidade futura deve acontecer por adapters/events, não vazando modelos externos para o domínio central.
