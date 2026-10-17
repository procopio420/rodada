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

## Additive staff identity copy — 2026-10-16

E03 queue parity needs the authorized Tab name/reference in addition to IDs.
The staff target projection now includes `tab_display_label` and
`tab_display_reference` only when its validated target is `TAB`. Reference uses
existing `Comanda <UUID first8 uppercase>` convention; no fictitious numeric
account/order number. `TABLE`/`UNAVAILABLE` expose null copy, including revoked,
expired or moved Guest bindings; names never establish financial identity.
Existing select_related joins supply the copy with no per-task query.

Executed against disposable local PostgreSQL port55635 (test database only):
`manage.py check` clean; `makemigrations --check --dry-run` no changes;
`pytest tests/test_dispatch_targets.py --ds=rodada_api.settings -q`15 PASS.
Tests include scoped list/detail, invalid foreign Tab, revoked Guest fallback,
released occupancy, closed financial Tab delivery and100tasks/3queries with the
full identity projection. Prior target concurrency/security regressions remain.
Independent R3 review, CI and Web/Android same-state screenshot parity are gates;
this additive copy is not an epic acceptance or rollout approval.

## Rival delivery completion regression — 2026-10-16

Spec033 E03 requires that an operator cannot complete another operator's live
claimed task. Spec003 DSP-004 keeps claim optional. The delivery service now
rejects a live task whose `claimed_by_id` differs from the actor with HTTP409
`DELIVERY_TASK_ALREADY_CLAIMED`, inside the existing OrderItem/task locks. DONE
replay remains a harmless canonical readback with original completion author and
timestamp; unclaimed completion remains available. No ledger, claim endpoint,
telemetry requirement, financial policy or schema changed in this followup.

Code/test SHA: `f332a5184e1e2a4580c75eeccc7b5f3f8388c52b`.
Environment: newly initialized disposable PostgreSQL17.6 on localhost55636,
DB `rodada033guard`, cluster `/home/lucas/.cache/rodada033guard-pg`.
Docker was unresponsive; no shared/remote database was used.

Executed with POSTGRES_HOST=127.0.0.1, POSTGRES_PORT=55636,
POSTGRES_USER=rodada, POSTGRES_DB=rodada033guard and dedicated Python3.12 venv:

- `manage.py check`: PASS; `makemigrations --check --dry-run`: no changes.
- `pytest tests/test_dispatch.py tests/test_dispatch_targets.py
  tests/test_service_requests_round2.py tests/test_tab_location_safety.py
  --ds=rodada_api.settings -q`: exit0,63 passed, no skips. Log:
  `/home/lucas/.cache/rodada033guard-tests.log`. The full run began before a
  test-only Barrier was added to synchronize the new concurrency workers; the
  final three regressions were then rerun on the frozen code/test SHA below.
- `git diff --check`: PASS. Ruff services clean; test file retains three prior
  RUF059/B009 findings (lines unrelated to this followup); imports pass.

Independent review: separate context `review_dispatch_followup` inspected
`52244ecd..f332a518` (authorized identity copy, exact delivery DTO expectation,
completion guard and regressions), result `NO_FINDINGS_WITH_GAPS`. This is code
review evidence, not authenticated GitHub R3 approval. Review gaps remain CI,
real Web/Compose parity and authorized operational/device acceptance.

Merge dependency: PR218 supplies the canonical target API. This followup is
stacked against `impl/033-dispatch-targets`; retarget after its authorized merge.
No merge/deploy performed. AC09/10/11 remain partial across the full clients;
this backend result does not complete E03 or authorize rollout.

Final frozen-SHA regression command: `pytest
 tests/test_dispatch.py::DispatchFoundationTests::test_delivery_rival_claim_rejected_without_item_or_audit_mutation
 tests/test_dispatch.py::DispatchFoundationTests::test_delivery_claim_owner_completes_and_rival_terminal_replay_is_harmless
 tests/test_dispatch.py::DeliveryCompletionConcurrencyTests
 --ds=rodada_api.settings -q --junitxml=/home/lucas/.cache/rodada033guard-final.xml`:
 **3 PASS,0 failures/errors/skips**, including synchronized PostgreSQL workers.
 Log: `/home/lucas/.cache/rodada033guard-final.log`.
