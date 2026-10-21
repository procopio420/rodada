# E06-05 — observador Compose de confirmação

Recorte cliente do contrato `client-observations.md` (PR297). Sem novas telas,
taps ou alteração do schema cifrado, UUID/payload financeiro e regras de replay.
INTENT_SAVED depois de preserveIntent; tentativa após guards de sessão/filas,
resultado CONFIRMED apenas após recibo e readback do Order exato (PR296).
Duração System.nanoTime somente dessa execução, nunca createdAtMillis/restart.

Worker dedicado limitado a uma chamada ativa e sete pendentes; descarte quando
cheio, sem retry e sem await/coroutine compartilhada com venda. SHA256 da chave
aleatória calculado no worker; nenhum payload/Tab/Order/ator/device é transmitido.
Sessão original validada novamente ao iniciar cada envio usando apenas acesso
atual do SecureSessionStore, sem refresh/save/clear. Token nunca fica na fila.
Sessão trocada ou indisponível descarta a observação; backend ainda valida origem.
POST destino fixo sem redirects; connect/read limitados e disconnect agendado em
1500ms. Nada desse transporte pode atualizar erro/UI/estado da intenção.

Testes JVM com servidor local: hash/correlação sem chave/payload; timeout/falha
sem replay; fila cheia não bloqueia; contexto trocado antes de executar descarta
sem HTTP. Android unit/build/lint/force-stop em CI; não equivale a aparelho ou
POST real/ledger e não fecha AC23 global.
