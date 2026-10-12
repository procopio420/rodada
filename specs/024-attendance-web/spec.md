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
