# Acceptance — Spec 002

- [x] Staff busca regular por nome/telefone; seleção opcional na abertura Android.
- [x] Tab de `HOUSE` herda limite configurado e versão da política.
- [x] Exposure atual aparece após mutation por revalidação API; outras superfícies
  usam polling bounded de 15s, o fallback existente da Spec 014.
- [x] Ao atingir limite, novo consumo exige parcial/aprovação/reavaliação explícita.
- [x] Parcial confirmado reduz exposure sem fechar Tab.
- [x] Override registra ator, motivo, antes/depois, horário e expiração.
- [x] Histórico mostra visitas/tabs, pendências e decisões auditadas.

## Critérios verificáveis P0

Os testes de API/domínio abaixo estão em `apps/api/tests/test_house_account.py`.

| ID | Critério satisfeito | Prova executável |
| --- | --- | --- |
| HOU-001 | Anonymous Tab usa política VISITOR do Venue; identity optional | `test_anonymous_uses_venue_visitor_policy_and_snapshots_updates` |
| HOU-002 | HOUSE/RESTRICTED têm snapshot correto; limite zero bloqueia | `test_house_and_restricted_snapshots` |
| HOU-003 | Pedido abaixo/no limite confirma; excesso não cria Charge/OrderItem | `test_orders_below_limit_and_at_limit_then_no_effect_on_rejection` |
| HOU-004 | Duas confirmações concorrentes não excedem limite | `HouseConcurrencyTests.test_concurrent_orders_cannot_overspend` (PostgreSQL) |
| HOU-005 | Replays não duplicam efeitos, inclusive após atingir limite/fechar | `test_idempotent_replay_after_limit_policy_change_and_close`, `HouseConcurrencyTests.test_concurrent_replay_creates_one_order` |
| HOU-006 | Parcial restaura capacidade; Refund confirmado aumenta exposição | `test_partial_payment_restores_capacity_and_refund_increases_exposure` |
| HOU-007 | Waiter/Cashier não aprovam; serviço não confia em payload; PIN recente obrigatório | `test_unauthorized_override_payload_and_recent_reauth`, `test_direct_override_service_cannot_trust_a_waiter_actor` |
| HOU-008 | Override é idempotente, expira, audita e não cria Payment | `test_override_idempotency_expiration_and_no_fake_money` |
| HOU-009 | Resolver limite preserva outro motivo de REQUIRES_ACTION | `test_override_cannot_clear_another_unresolved_reason` |
| HOU-010 | Associação/mudança de relacionamento preservam snapshot/histórico; reavaliação é explícita | `test_customer_association_relationship_change_explicit_reassessment_preserves_history` |
| HOU-011 | Atualização de política não modifica pedido confirmado | `test_policy_update_preserves_existing_order` |
| HOU-012 | Guest/Staff/Cashier usam o mesmo enforcement | `test_guest_and_staff_share_same_tab_enforcement`, `test_spending_limit_is_source_agnostic` |
| HOU-013 | Busca/associação são isoladas por Venue e alterações exigem autorização | `test_staff_customer_search_is_venue_scoped`, `test_cross_venue_customer_cannot_be_associated` |
| HOU-014 | Solicitar aprovação não concede limite; warning a 80% | `test_request_approval_is_audited_without_granting_capacity`, `test_warning_at_eighty_percent` |
| HOU-015 | Comandas antigas não desaparecem depois da primeira página | `test_active_tab_pagination_does_not_hide_old_attention_tabs` |
| HOU-016 | Migração preserva ledger e atenção manual | `tests/test_house_account_migration.py` |
| HOU-017 | Open → Consume → Hit Limit → Block → Override/Partial → Continue → Pay → Close | Dois testes em `tests/test_house_account_e2e.py`, servidor real via HTTP |
| HOU-018 | Guest sem controles gerenciais, Gerência aprova com PIN; revalidação após reconnect em mobile | `scripts/house-account-browser-e2e.py`, Chromium real, 390×844 |
| HOU-019 | Android lê capacidade/limite canônicos, zero sem percentual, schema incompleto falha | Quatro testes em `HouseAccountContractTest.kt`; build/lint Android |

## Reprodução e resultados locais (2026-10-08)

Backend, de `apps/api`:

```sh
python manage.py check --settings=rodada_api.settings_test
python manage.py makemigrations --check --dry-run --settings=rodada_api.settings_test
python -m pytest
POSTGRES_DB=rodada_house_p0 python -m pytest tests/test_house_account.py tests/test_house_account_e2e.py --ds=rodada_api.settings
POSTGRES_DB=rodada_house_p0 python -m pytest tests/test_house_account_migration.py --ds=rodada_api.settings
```

- Suíte completa: **152 passaram, 2 skips** (concorrência não é comprovável em
  SQLite). O teste adicional de paginação passou separadamente em SQLite e
  PostgreSQL. Todos os 153 testes não dependentes de row locking foram verificados.
- PostgreSQL: **21 passaram** na suíte House Account/HTTP E2E, mais migração e
  paginação verificadas separadamente. Ambos os testes de concorrência passaram;
  o job `house-account-postgres` da CI executa todos juntos.
- Django check/migration drift e lint Python E/F/I do novo módulo/testes: passaram.
- Migração aplicada numa base PostgreSQL descartável, com `seed_demo` real.
- Web: `npm run typecheck`, `npm run build` passaram. Browser proof real passou
  sem mocks/interceptação, incluindo offline→online e ausência de overflow mobile.
- Android: `:app:testDebugUnitTest :app:assembleDebug :app:lintDebug` passaram;
  **19 testes JVM**, incluindo os quatro novos de contrato financeiro.

Para E2E HTTP: `bash scripts/house-account-e2e.sh` na raiz.

Para browser proof, usar uma base **local descartável**, aplicar migrations e
`seed_demo`, iniciar API em 8012 e Web em 3012 com
`RODADA_API_BASE_URL=http://127.0.0.1:8012`, então executar
`python scripts/house-account-browser-e2e.py`. Requer Python Playwright + Chromium.
O script cria mesa/comanda e configura VISITOR somente nesse ambiente local.

## Limites de validação e dependências externas

- Smoke Android em `rodada-api-37`/`emulator-5580` foi tentado, mas o emulador
  não completou boot em 90s. Não há prova de interação em dispositivo neste run.
  Build, lint e contrato JVM passaram; validar a interação nativa no aparelho
  do piloto antes do rollout.
- Tap on Phone/provider físico e garantia financeira continuam dependências
  próprias de Spec 006/ADR 0011, não são simulados nem apresentados como pagos.
- O slice usa HTTP/polling bounded; transporte SSE compartilhado não foi
  implementado aqui. Reconnect sempre revalida o estado canônico.
- Não modifica/dependente da PR visual #40: CSS, tokens e produção preservados.
