# E03/E06 — Native delivery task full page

Replace the native delivery AlertDialog with the approved viewDelivery page hierarchy. Opening remains a canonical read only; Back never completes. Product, quantity, station, destination and ownership use the existing DeliveryTask payload, even when the financial Tab is closed. No lookup by table text and no new financial or idempotency engine.

The prototype's fictional simulation CTA becomes the existing explicit delivery-by-exception action. Its original task ID and recovery pipeline remain authoritative. This technical difference removes simulation and mandatory KPI confirmation. Full acceptance awaits matched screenshots, regression and independent review.

## Existing recovery gap — NOT_ACCEPTED

The reused completion engine (OperationsViewModel.completeDelivery) persists original task intent but performs POST then queue-list read, without exact item/task terminal readback; the locally generated key is not sent in transport. This slice does not claim functional recovery equivalence or E03 acceptance. A separate hardening slice must prove lost ACK and canonical terminal state. Back during busy only changes presentation selection; persisted global intent and submitting state remain in the existing ViewModel/store, and the disabled completion action cannot be repeated from this page.


## Hardening de recuperação na composição desta branch

O delta86162c01 corrige as lacunas acima com GET exato da tarefa/item terminal e fence de geração de sessão; não infere conclusão pela ausência na fila. A composição com a página74643eb6 passou128JVM/build/lint e dois cenários ViewModel/API reais. O ensaio adicional em duas fases confirmou retomada da mesma intenção cifrada após force-stop real, sem novo POST. Evidências completas em docs/development/evidence/spec033-native-delivery-recovery. Aceite global E03, cenários revogados, aparelho físico e revisão independente do novo harness continuam pendentes; não alterar checkboxes globais apenas por este recorte.

## E03-07/E06 — freshness independente da fila

Falha do GET da fila de entregas preserva a última lista com aviso e contagem —,
sem invalidar leitura canônica bem-sucedida de pedidos/catálogo/comanda. Atualizar,
realtime e polling existentes reconsultam a fila; sucesso restaura freshness.
Leitura HTTP canônica autoriza core ONLINE também no fallback sem SSE. Falha do
core continua seguindo os bloqueios de conectividade existentes. Dispatch desconhecido
nunca autoriza liberar mesa: validar freshness na entrada, confirmação já aberta
e ViewModel. Refresh cancelado ou de geração de sessão anterior não publica estado,
inclusive A→B→A. Não alterar políticas financeiras nem o motor de recovery.

Critérios:503 da fila permite pedido real com core saudável; lista antiga permanece
com aviso/—; reconexão restaura READY; falha core bloqueia o que exige ONLINE;
release desconhecido bloqueado inclusive diálogo aberto; troca de sessão rejeita
resposta antiga. Evidência automatizada e dispositivo deve declarar seus limites.
