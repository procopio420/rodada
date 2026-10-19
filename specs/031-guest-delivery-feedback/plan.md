# Plano — Spec 031 (proposta, não execução)

## Slice 1 — Contrato e dados

- Revisar modelo de milestones, source/provenance e política de transição (ADR 0009, Spec 003).
- Definir `GuestDeliveryFeedback` append-only ou extensão compatível do evento existente, com intent UUID, alvo granular, quantidade, contexto e hora servidor.
- Definir semântica para feedback, milestone e correção; garantir que confirmação tardia não inventa `delivered_at`.
- Validar se feedback de pedido iniciado pelo staff pode ser recebido por GuestSession autorizada à Tab.

## Slice 2 — API

- GET elegibilidade/feedback para sessão guest autorizada; POST idempotente e auditável.
- Revalidação de Venue/Tab/Table/occupancy/generation/Order/itens/quantidades e revogação.
- Deduplicação, conflito de payload, controle de concorrência, falhas e retry seguro.
- Sem mudanças financeiras.

## Slice 3 — PWA Guest

- Card sutil em Pedidos para itens/lotes elegíveis; ações `Sim`, `Parte`, `Ainda não`, `Veio errado`; dispensar.
- Enviar só após ação explícita; preservar draft e recuperação de resposta ambígua.
- Acessibilidade 360/390/430 px, sem modais bloqueantes nem repetição excessiva.

## Slice 4 — Dispatch e observabilidade

- Feedback negativo/erro pode criar/atualizar exceção idempotente conforme limiar e disponibilidade da operação.
- Analytics segmenta `GUEST_CONFIRMED`, `INFERRED`, `MANUAL`, `CORRECTED` e não resposta; dashboard mostra cobertura/amostra.
- Calibrar com observação operacional supervisionada antes de usar confirmação como proxy de entrega.

## Rollout

Feature flag por Venue, primeiro piloto assistido. Sem tornar a confirmação pré-requisito do POS; desligável sem perder registro histórico. Testar taxa de adoção, efeitos no atendimento e falsos positivos; comparar turnos equivalentes.
