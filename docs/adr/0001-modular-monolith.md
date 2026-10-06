# ADR 0001 — Modular Monolith First

**Status:** Accepted

## Contexto

O produto ainda valida seu modelo operacional. Microserviços aumentariam custo de mudança, debugging e consistência transacional sem reduzir um risco relevante do piloto.

## Decisão

Usar Django como monólito modular, com fronteiras claras entre catalog, pos, fulfillment, dispatch, customers, relationships, ledger/payments, cash e audit.

Next.js fica como frontend separado no mesmo monorepo.

## Consequências

- deploy simples;
- transações financeiras e operacionais mais fáceis;
- realtime pode ser adicionado sem dividir serviços cedo demais;
- refactors de domínio baratos;
- possibilidade de extrair módulos depois se houver necessidade real.
