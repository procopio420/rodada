# S3/S4 — Clientes e editor gerencial

Depende da PR281 e do modo/version canônico em financial_position. Ausência ou
valor desconhecido continua ENFORCE; nenhum toggle staff. Web/Compose mostram
aviso sem alegar bloqueio em WARN_ONLY; Compose permite enviar draft acima da
referência somente quando DTO canônico WARN_ONLY e consumption_blocked=false.
Preço, disponibilidade, sessão, intenção e confirmação continuam no servidor.

Gerência: Configurações→Políticas de consumo, escrita versionada com PIN e motivo.
Congelar chave/payload/contexto antes do primeiro PUT; timeout recupera a mesma
intenção, enquanto 409 definitivo exige refresh e nova decisão. Enviar sempre
expected_venue_id e expected_session_id originais. Refresh não troca silenciosamente
contexto ou payload. Nunca armazenar PIN/tokens; só configuração e identidade de
intenção em sessionStorage. Readback atual pode ser mais recente que receipt de
replay; exibir ambos corretamente e não substituir estado canônico pelo receipt.

Gates: dois Venues WARN/ENFORCE, pedido excedente/rejeitado, versão stale e ACK
perdido na configuração, revogação/troca de sessão, Web/Guest/Compose e fonte2.
Sem alterar defaults ou configurar Venue de produção nesta execução.

## Reconciliação de 21/10/2026

Backend #281 integrado em `047807cb8008e009b3ac26cb00ebfe9a7b9d92ca`.
Composição preserva as regressões Compose de categoria Todos, offline e os três
casos de modo; navegação gerencial mantém products/customizations e spending.
O ensaio de fila com dois operadores inclui o fallback HTTP real de 15 segundos:
seu orçamento total passa a 60s, mantendo expectativas locais, zero retries,
claim concorrente/409 e exatamente um POST após ACK perdido. Não muda produto.
Revisão independente do delta original `f65660c6`: NO_FINDINGS_WITH_GAPS;
revisão da reconciliação, CI e validação no candidato ainda pendentes.
