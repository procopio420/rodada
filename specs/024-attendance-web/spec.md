# Spec 024 — Atendimento Web for operational testing

## Behavior
Provide a browser companion to Atendimento Android at `/attendance` and
`atendimento.rodada.ai`, sharing canonical API contracts, staff login and design
primitives. Agora shows READY delivery work and completion. Contas opens/searches
comandas, displays balances and order history, configures quantities/variants/
modifiers/notes, and confirms orders. Mesas supports occupation, attaching multiple
comandas, release, cleaning and zone assignment. Closing remains server validated.

## Rules
Authentication, membership, capability and revocation remain enforced by the API.
No payments, refunds, cash management, provider SDKs or simulated settlements in this
surface. A restricted `/api/attendance` gateway accepts only listed operational
commands; it rejects financial routes before forwarding. Existing surfaces retain
their capabilities. Balances remain real, so unpaid comandas cannot be closed.
Ambiguous orders retain the exact payload/key for retry and freeze cart/Tab changes.
Network failures display stale state, never success. Polling revalidates every 15s.

## Out of scope
Native NFC/BLE, offline mutation queues, payment certification, full Android pixel
parity, and operations absent from the current native core (corrections/split/merge).

## Acceptance
See acceptance.md. This companion enables testing without installing Android;
it does not replace the native payment application.

## Pilot frontend slice — 2026-10-10
Agora also lists canonical SERVICE_REQUEST/BILL_REQUEST work from
`dispatch/requests/`, retaining server order, destination text, age and
ownership. Staff may claim or complete by task ID; another actor's claim disables
both actions. A missing age is unknown. A failed/ambiguous command never removes
the task or shows success; refresh/retry reuses that same task/action. Reload the
queue after conflicts. Stale/initial-error reads disable commands and do not show
an empty queue as fact. Polling is serialized and stops when this surface unmounts.
The gateway allows only queue GET and task claim/complete POST, preserving its
financial exclusions. Exact navigation is blocked until the canonical response
includes destination table/occupancy IDs; never resolve by display label.

Active occupancy party-size GET/POST is allowed under Spec016, capability
`table.manage`; capture is optional, preserves idempotency/version and never
changes financial state. No historical edit or other occupancy commands added.

## Integração de 13/10/2026

Executar os contratos existentes na main atual e registrar provas em [matriz de conclusão](../../docs/development/spec023-024-completion.md). Preservar regras canônicas, referências/tolerâncias, dados e gates externos. Não marcar aceite por presença de código ou execução histórica.

## Spec033 E04 — recebimento CASH e encerramento recuperável (2026-10-16)

A autorização explícita da missão Spec033 amplia o companion apenas para
recebimento manual CASH real. GET cash/points e POST tabs/{id}/payments são
permitidos pelo BFF; métodos diferentes de CASH, refund e outras operações de
caixa continuam excluídos. Sessão, Venue, payment.collect, caixa aberto, versão,
valor e idempotência são revalidados pela API canônica. Não habilita PSP/Pix/cartão.

O componente PosCashReceipt reutilizado mantém o comportamento POS por padrão.
Apresentação attendance é opt-in. Receber integralmente e encerrar captura a
intenção explícita em envelope v2, com gateway original e sessão/ator/Venue/Tab.
Payment confirmado persiste ID/fase antes de leitura/close. Readback confere
Payment por ID/método/valor/status; saldo zero permite close naturalmente
idempotente. Falha de close/reload retoma leitura/close, nunca novo Payment.
Lost ACK de Payment mantém payload/chave originais. Envelope v1 continua com
gateway POS original; nova sessão não adota uma intenção antiga.

Encerramento não libera mesa nem fecha caixa. Enquanto close estiver pendente,
a intenção permanece bloqueante e visível mesmo sem Tab selecionada. Não há
autoenvio após reload. AC-12/13/16 da Spec033 exigem testes reais e revisão R3;
esta atualização de contrato não comprova aceite/paridade ou rollout.
