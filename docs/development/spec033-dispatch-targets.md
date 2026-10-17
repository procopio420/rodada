# Spec033 — E01-02 / E03-02/03: destinos canônicos de Dispatch

Base: `origin/main@dcb3a79590904a2c289641d285eda639e1713c87`.
Contrato: Spec033 da branch `spec/033-attendance-ux2-productization`, E03;
Specs003/004 e ADR0004. Risco R3 (Guest/tenant, migration).

Antes: chamadas possuíam somente destino textual e vínculo físico histórico;
entregas já possuíam OrderItem canônico e atualização do destino pela Spec029.
Não havia identidade exata da Tab solicitante nem leitura individual da tarefa.

Depois: campos aditivos `target_version: 1`, `target` e `zone_id` nas respostas
staff; entregas também expõem `task_type`, `order_id`, `fulfillment_station`
(snapshot confirmado, null no legado desconhecido) e `item_state`.

`target` mantém chaves `kind`, `tab_id`, `table_id`, `occupancy_id`, `generation`.
Kinds: `TAB`, `TABLE`, `UNAVAILABLE`. IDs ausentes são null. A projeção consulta
vínculos atuais por Venue, geração, ocupação e estado físico; não interpreta labels.
`GET /dispatch/tasks/{id}/` revalida a tarefa exata, incluindo ownership/estado
terminal, sem claim/completion/mutation. O consumidor ainda revalida a leitura de
Tab pelo endpoint contextual existente antes de abrir conta/pedido.

A migration adiciona `requested_tab` e `requesting_guest_session` nullable, sem
backfill por heurística. A origem Guest é capturada sob os locks existentes de
Venue/sessão/mesa. Sessão revogada/expirada/reassociada ou Tab movida impede deep
link para a conta original; se a ocupação original permanece válida, o fallback
é escolha explícita na mesa. Ocupação encerrada/geração antiga: UNAVAILABLE.
Legado e chamadas sem Tab nunca selecionam automaticamente a única Tab da mesa.
Provenance da sessão é interna; token/session ID não são expostos no DTO staff.
Resposta Guest permanece somente id/task_type/state.

Entregas navegam pela Tab de OrderItem mesmo financeiramente CLOSED; a mesa é
contexto atual opcional. Nenhuma mudança no ledger, política, claim/completion,
limpeza, telemetria ou obrigação de confirmar entrega.

## Verificação

Ambiente: PostgreSQL16 descartável exclusivo `rodada-033-dispatch-pg`, porta local
55633, Python3.12 em venv dedicada; nenhum banco compartilhado foi usado.

- Django `check` com settings PostgreSQL: PASS.
- `makemigrations --check --dry-run` com settings PostgreSQL: PASS.
- Ruff arquivos novos e urls: PASS; arquivos antigos preservam dívida preexistente.
- Suíte PostgreSQL final em `c6352bf0`: **54 PASS em 99.09s**, sem skips.
  Comando em `apps/api` (POSTGRES_* apontando exclusivamente ao container acima):
  `python -m pytest tests/test_dispatch_targets.py tests/test_dispatch.py tests/test_service_requests_round2.py tests/test_tab_location_safety.py --ds=rodada_api.settings --no-header`.
  Log local: `/tmp/rodada-033-dispatch-final.log`. Treze testes novos incluem
  concorrência Guest real com duas conexões e volume de 100 tarefas em três queries.
  Tentativas anteriores detectaram expectativa do DTO desatualizada e fixture de
  Product duplicada; corrigidas sem remover campos/asertivas nem alterar constraints.
  Uma rodada intermediária capturou imports antes da adição final de zone_id;
  a rodada final foi executada com código congelado.
- Revisão independente R3: PENDING, a cargo do integrador.
- Web/Compose, visual, emulador/aparelho e CI: NOT_RUN nesta slice de API.

Os testes cobrem duas Tabs homônimas na mesma mesa, chamadas legadas/sem Tab,
revogação/expiração/reassociação, release/geração/movimento, READY em Tab CLOSED,
isolamento Venue/auth, estação histórica, claim rival, não mutação na leitura,
replay concorrente Guest e 50 chamadas + 50 entregas com projeção em lote.

AC01/03/09/10/11 têm cobertura backend parcial; permanecem pendentes até jornadas
Web e Android, CI e revisão independente. Esta slice não declara GO operacional.

Rollout: aplicar migration antes de publicar clientes consumidores. Campos antigos
permanecem compatíveis. Rollback de cliente preserva campos de provenance e fatos;
não remover migration/dados durante operação. Sem merge/deploy autorizados.
