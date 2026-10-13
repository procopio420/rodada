# Rodada API — AGENTS.md

Herde `../../AGENTS.md`, a [KB](../../docs/agents/README.md) e os [procedimentos](../../docs/agents/PROCEDURES.md). Antes de alterar comportamento, leia `README.md`, `../../docs/architecture/overview.md`, `../../docs/domain/model.md`, spec completa e ADRs associados.

## Fronteiras e invariantes

- Django/DRF é o **modular monolith**; respeite ownership de `modules/` em vez de criar módulos transversais para contornar contratos.
- `Venue` é a fronteira de isolamento. Queries, mutations, capabilities, sessões, refresh, SSE/outbox, guest e idempotência não podem vazar entre Venues. Host e headers de cliente não conferem auth.
- `Tab` é a unidade de pedidos/finanças; mesa/ocupação não vira ledger. `Order` aponta para Tab. Histórico confirmado não é reescrito ou apagado para simplificar recuperação.
- Estado de `ProductAvailability` é operacional, independente de `Product.active`; confirmação valida o servidor. `OrderItem` confirmado não é cancelado porque o produto esgotou depois.
- Dinheiro em centavos inteiros, transações atômicas/locks necessários, operações financeiras append-only/auditáveis, idempotência e reconciliação; timeout/provider pendente **não** significa pago.
- A API é autoridade para permissões, transições e readback. Não tornar segura uma mutation apenas escondendo um botão no cliente.
- Correções, estornos, compensações e overrides preservam ator, motivo, vínculo e evidência de autorização; concorrência precisa de testes reais em PostgreSQL.

## Procedimento obrigatório

1. Mapear contrato `specs/<pasta-completa>/{spec,acceptance}.md`, models/services/endpoints e testes existentes.
2. Adicionar regressão negativa além do caminho feliz; para financeiro/tenant/async testar duplicidade, conflito e resposta perdida com mesma intenção.
3. Validar em Postgres descartável como no workflow de API (SQLite não comprova locking).
4. Com ambiente preparado: `cd apps/api && python manage.py check --settings=rodada_api.settings && python manage.py makemigrations --check --dry-run --settings=rodada_api.settings && pytest --ds=rodada_api.settings`.
5. Registrar comando/resultado/SHA e limitações no PR. Migrations exigem revisão de impacto e rollback; nunca aplicar em banco remoto sem aprovação.

Não executar `seed_demo`, `reset-local-tests`, migrations ou scripts de restore contra a demo compartilhada/produção.
