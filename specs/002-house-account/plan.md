# Plan — Spec 002

## Implementação

1. Módulo Django `house_account` persiste Customer, Relationship local,
   VenueRelationshipPolicy e LimitOverride. Tab guarda identidade opcional,
   snapshot e motivos independentes de atenção.
2. Aberturas Staff e Guest usam `snapshot()`, com os cinco defaults demo
   persistidos por Venue. Migração aplica VISITOR ao legado e preserva ledger.
3. `confirm_order()` bloqueia apenas Tab, resolve replay e bloqueia produtos
   em ordem determinística; valida exposição projetada antes do primeiro write
   de Order/OrderItem/Charge. Ledger continua única fonte financeira.
4. Refund e confirmação de provider seguem lock order Tab → Payment; estados
   de atenção são derivados e auditados. Pagamento confirmado reduz exposição,
   estorno confirmado a aumenta; autorização manual nunca cria dinheiro.
5. Serviços de override/associação/reavaliação verificam ator e authority
   canônicos. Aprovação requer capability + PIN recente e tem expiração <=24h.
6. APIs reais são expostas pelo proxy Web existente, com PATCH/PUT e proteção
   de origem preservada. Gerência mostra solicitações/exceções, limites e
   auditoria; Guest revalida e mostra bloqueio; Android oferece busca de cliente,
   exposição/capacidade, pagamento existente e solicitação/aprovação com PIN.
7. Testes cobrem API, domínio, migração, concorrência PostgreSQL e dois ciclos
   HTTP completos. Browser proof real roda em 390px com reconnect. Android
   valida contrato JSON, testes JVM, build e lint. CI inclui PostgreSQL.

## Coordenação e rollout

- Não depende da PR #40. Não altera CSS/tokens/nav/produção. Gerência recebe
  somente o componente Conta da Casa; eventual conflito de import é local.
- Executar `python manage.py migrate` antes de publicar clientes. Não publicar
  clientes novos contra uma API sem os campos financeiros obrigatórios.
- Revisar comandas legadas acima de R$30: preservar dívida e resolver com
  parcial/override/reavaliação explícita. Não há grandfathering silencioso.
- Limite e approval não são balance/garantia. Preauth/caução precisam de adapter
  homologado e/ou ledger de passivo próprio; não são simulados neste P0.
