# E03/E06 — Native delivery task full page

Replace the native delivery AlertDialog with the approved viewDelivery page hierarchy. Opening remains a canonical read only; Back never completes. Product, quantity, station, destination and ownership use the existing DeliveryTask payload, even when the financial Tab is closed. No lookup by table text and no new financial or idempotency engine.

The prototype's fictional simulation CTA becomes the existing explicit delivery-by-exception action. Its original task ID and recovery pipeline remain authoritative. This technical difference removes simulation and mandatory KPI confirmation. Full acceptance awaits matched screenshots, regression and independent review.

## Existing recovery gap — NOT_ACCEPTED

The reused completion engine (OperationsViewModel.completeDelivery) persists original task intent but performs POST then queue-list read, without exact item/task terminal readback; the locally generated key is not sent in transport. This slice does not claim functional recovery equivalence or E03 acceptance. A separate hardening slice must prove lost ACK and canonical terminal state. Back during busy only changes presentation selection; persisted global intent and submitting state remain in the existing ViewModel/store, and the disabled completion action cannot be repeated from this page.
