# AGENTS.md — Rodada

Este repositório é desenvolvido de forma **spec-driven**.

## Regra principal

**Não implemente uma feature relevante antes de existir uma especificação que descreva comportamento, regras, fora de escopo e critérios de aceite.**

Código implementa specs. Código não é a fonte primária de intenção de produto.

## Ordem de leitura

Antes de alterar comportamento:

1. `README.md`
2. `docs/product/vision.md`
3. `docs/product/principles.md`
4. `docs/domain/model.md`
5. spec relevante em `specs/`
6. ADRs relacionados em `docs/adr/`

## Workflow

1. Identifique a spec existente ou crie uma pasta numerada em `specs/`.
2. Atualize `spec.md` antes do código.
3. Registre decisões arquiteturais duráveis em `docs/adr/`.
4. Mantenha `plan.md` com abordagem de implementação.
5. Quebre execução em `tasks.md`.
6. Defina critérios verificáveis em `acceptance.md`.
7. Implemente a menor vertical slice que satisfaça um critério de aceite.
8. Adicione testes alinhados aos critérios.
9. Atualize a spec se a descoberta durante implementação mudar o contrato.

## Guardrails de produto

- Rodada **é um PDV próprio**, não apenas uma integração com PDV existente.
- Não transformar Rodada num ERP genérico antes de validar o núcleo operacional.
- `Tab`/comanda não deve depender de mesa física.
- Mesa/localização é contexto mutável, não identidade financeira.
- Dispatch é parte do núcleo operacional, não um add-on cosmético.
- Não exigir app do cliente no MVP.
- Não exigir CPF no fluxo básico.
- Não chamar relacionamento de “score de crédito” na UX.
- Não automatizar promoção/rebaixamento de relacionamento sem spec explícita.
- Não acoplar pagamentos a um provider específico no domínio central.
- Pagamentos devem ser idempotentes e auditáveis.
- Override de limite deve registrar ator, horário, valor anterior, novo valor e motivo opcional.
- “Cliente da casa” é uma relação local entre cliente e estabelecimento.
- Fiscal, estoque profundo, delivery e loyalty não entram por reflexo: precisam de spec própria e justificativa.

## Convenções de domínio

- **Venue**: estabelecimento.
- **StaffMember**: usuário operacional.
- **Customer**: pessoa identificada opcionalmente.
- **Relationship**: relação Customer ↔ Venue.
- **Tab**: sessão operacional/financeira de consumo.
- **Order**: solicitação operacional de itens.
- **OrderItem**: item individual com rota/estado próprios quando necessário.
- **ServicePoint**: localização efêmera (mesa/tag/ponto), opcional.
- **Zone**: agrupamento operacional de pontos.
- **Task**: unidade de trabalho despachável.
- **Charge**: lançamento financeiro positivo derivado ou manual.
- **Payment**: valor recebido.
- **Adjustment**: cortesia/correção/reversão.
- **Open Exposure**: valor efetivamente aberto.
- **Operating Limit**: exposição máxima sem ação adicional.

## Qualidade financeira

Toda regra financeira precisa de:

- teste unitário;
- idempotência quando houver evento externo;
- trilha de auditoria;
- valores monetários em centavos, nunca `float`;
- transação de banco quando alterar saldo/exposição.

## Qualidade operacional

Mudanças de estado em pedido/task devem registrar timestamps suficientes para medir:

- pedido → aceito;
- aceito → pronto;
- pronto → retirado;
- retirado → entregue;
- chamada → claim → concluída.

Toda mutation relevante deve responder:

- quem fez;
- o que mudou;
- quando;
- por quê, quando aplicável.

## Commits/PRs

Preferir commits pequenos por slice. PR deve apontar para a spec e indicar quais critérios de aceite passam após a mudança.
