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
