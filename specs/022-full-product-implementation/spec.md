# 022 — Entrega do produto completo a partir dos protótipos

> Foco esclarecido pelo usuário: a próxima implementação solicitada é fidelidade visual. Ver [Spec 023](../023-updated-prototype-visual-parity/spec.md). Este documento permanece contexto funcional, não o plano visual.

Estado: planejado. Data: 2026-10-08.

## Objetivo

Transformar as referências integradas na Spec 021 em jornadas reais de Rodada, completando contratos existentes e validando uma operação de turno inteira. O [plano canônico](../../docs/architecture/full-product-implementation-plan.md) define inventário, dependências, PRs, gates e rollout.

## Comportamento e regras

- Android Atendimento e Web/PWA Cozinha, Bar, Cliente e Gerência operam sobre a mesma API e domínio; runtime do export permanece referência.
- Todo pedido pertence a Tab; identidade é opcional e localização não é identidade financeira. Ocupação e fechamento de Tab são ciclos distintos.
- API revalida autorização, disponibilidade, preço, versão e políticas; ledger usa centavos, transação, idempotência e auditoria.
- HTTP confirma comandos; outbox transacional/SSE atualizam leituras com replay e snapshot em gap. Offline apresenta cache/intenção, nunca confirmação financeira ou de venda fictícia.
- Dispatch não exige taps de medição no happy path. Inferência declara source/confidence/provenance; desconhecido permanece desconhecido; correção preserva evento original.
- Design system é comum e mobile-first; cada jornada inclui estados de falha/recovery e revisão de superfície adjacente.
- Produto completo exige contratos aplicáveis das Specs 001–018, provider real homologado e gates de qualidade/operação. Piloto reduzido declara capacidades e limites explicitamente.
- Reusar implementação existente e atualizar a spec de domínio antes de novo comportamento. Este programa não altera implicitamente suas regras.

## Fora de escopo

Fiscal, ERP, estoque profundo, delivery externo, loyalty, promoção automática de relacionamento, sensors obrigatórios e migração para microserviços. Geração IA de ícones segue adiada; não é requisito de lançamento. Este planejamento não implementa o backlog nem publica o produto.

## Critérios de aceite

Ver [acceptance.md](acceptance.md). A conclusão do documento de planejamento não implica conclusão da entrega do produto.
