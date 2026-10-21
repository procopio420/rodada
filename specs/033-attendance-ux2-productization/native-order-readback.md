# E02-04 / AC04-05 — recibo e readback nativos por Order.id

Gap reproduzível por inspeção do caminho atual: OperationsHttpClient.confirmOrder
ignora o JSON bem-sucedido; a fila no ViewModel remove a intenção após ler qualquer
TabDetail. Uma resposta200 sem id/tab_id correto ou uma leitura stale sem o novo
Order pode descartar a chave antes de comprovar a confirmação. A Web já exige
Order.id/Tab.id no recibo e presença desse Order no readback.

Contrato antes do código: preservar a mesma fila cifrada/UUID/payload e o backend.
ConfirmOrder devolve recibo tipado com UUID de Order e Tab esperada. JSON inválido,
Tab divergente ou readback que não contenha esse Order são resultado desconhecido
(502 local ORDER_CONFIRMATION_UNVERIFIED), não rejeição definitiva nem sucesso.
Só remover a intenção e limpar o carrinho depois de validar recibo e readback.
Não inferir confirmação pelo último Order, label, número de itens ou HTTP200.
CancellationException continua propagando; sessão e replay mantêm guards atuais.

Testes: cliente HTTP200 inválido/missing/mismatched com mesmo payload; recibo
válido e replay da mesma chave; readback Tab divergente/Order ausente e válido.
Unit/build/lint Android e revisão R3 por SHA. API não muda; não afirmar force-stop,
aparelho ou teste financeiro real a partir da fixture HTTP JVM.
