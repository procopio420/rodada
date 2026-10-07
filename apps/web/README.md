# Web

Target: Next.js responsive/PWA, staff-first.

## Production screens

- `/bar` — focused Bar queue.
- `/kitchen` — focused Kitchen queue.

Both routes poll the persisted API every five seconds and progress confirmed
`OrderItem`s through `NEW → ACCEPTED → PREPARING → READY`. They use the same
`NEXT_PUBLIC_API_URL` and persisted staff PIN session as the staff interface.
The availability control calls the canonical catalog API; the server only permits
a manager/owner identity to make that change.

Primeira interface deve funcionar bem em celular Android, com botões grandes e fluxo rápido.

O protótipo sem backend está em `prototype/`.
