# E03-07 / E06 — falha de Dispatch isolada dos pedidos

Fonte fd925a03, base PR246 ffa959b6. Antes, refresh agrupava fila de entregas e dados operacionais em Promise.all; um Dispatch503 tornava o Atendimento offline e bloqueava pedidos disponíveis. Agora a fila usa singleflight/freshness próprios e preserva os últimos dados com aviso e contagem não verificada. Atualização manual, polling e realtime reutilizam os mecanismos existentes.

Liberação de mesa continua bloqueada quando a fila não foi verificada, tanto na entrada quanto no diálogo e no handler. Nenhuma política de dinheiro, autorização ou idempotência muda. Dados cached podem ser consultados; operações continuam verificadas no backend.

## Evidência executada

- Build/typecheck/ESLint PASS.
- 18 testes browser PASS em 33,6s: indisponibilidade da fila, retorno, dados antigos explícitos, página de entrega e guards de liberação. Primeira tentativa 17/18 falhou porque o teste supunha bloqueio da consulta cached; corrigido para exigir bloqueio da ação de abrir nova comanda quando core indisponível. Produto não foi afrouxado.
- PostgreSQL55644/API8146/Web3146: 4/4 PASS em 51,9s, 360/390/430/1280. Pedido real de uma unidade/500 centavos durante Dispatch503; produção READY, reconexão e tarefa canônica navegável. Sem simulação de confirmação.
- Revisão independente root do produto escrito por web_delivery_parity: NO_FINDINGS_WITH_GAPS. Conferidos source/callers/singleflight, key=session.id, preservação do estado não verificado e guard da liberação. Sem achados reproduzíveis no escopo; sem aprovação GitHub/merge/deploy.

Aceite global E03 permanece pendente. Android ainda exige validação equivalente de falha isolada, restart e matriz conjunta. Não há aprovação implícita de diferenças intencionais frente ao protótipo.
