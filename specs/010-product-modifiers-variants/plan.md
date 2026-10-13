# Plan — Spec 010

## Independent closure — 2026-10-09

Add isolated `ordering/customization_mix.py` with snapshot-only gross selection
aggregation and regression tests for quantity, original prices/labels after edits,
Venue/time isolation, legacy items, cancellations and remake exclusion. No management
UI/report changes. Reexecute customization/availability locking and compatibility
suites; hand endpoint/business-date integration to Agent 2.

## Recommended sequence

1. **Migrations/domain**
   - ProductVariant;
   - ModifierGroup / ModifierOption;
   - ProductModifierGroup;
   - operational availability fields;
   - OrderItem customization snapshot.

2. **Ordering validator/pricer**
   - server-side cardinality;
   - availability;
   - exact cents;
   - idempotent snapshot + Charge.

3. **Catalog management**
   - configure variants/groups/options;
   - station/manager availability actions.

4. **Atendimento**
   - one-tap quick add when possible;
   - compact modifier sheet when needed.

5. **Guest**
   - same published schema and availability;
   - required-choice validation.

6. **Production surfaces**
   - compact, consistent rendering of variant/modifiers/removals/notes.

7. **Realtime/hardening**
   - availability invalidation;
   - stale cart recovery.

## API contracts

Stabilize a product ordering schema that exposes:
- effective selectable variant set;
- modifier groups/cardinality/defaults;
- price deltas;
- availability/version.

Confirmation sends IDs/selections only; backend computes price.

## Rollout

All existing products remain modifier-free. Add configuration incrementally per Product.

## Testing strategy

- pricing arithmetic;
- min/max and defaults;
- stale/unavailable selection;
- concurrent availability update vs confirmation;
- snapshot immutability;
- guest/staff parity;
- idempotent order confirmation.

## Dependencies first

Spec 001 order confirmation and price snapshot, Spec 005 Catalog identity and Spec 008 authorization.

## Implemented slices

- Catalog migration 0006 adds ProductVariant, ModifierGroup, ModifierOption and
  ProductModifierGroup with default uniqueness and cardinality constraints.
- Ordering migration 0006 adds customization and fulfillment-station snapshots.
- `catalog/customization.py` owns schema and pricing; configuration and optimistic
  availability commands are in `catalog/customization_views.py`.
- Existing confirmation, financial limit check and exactly-once Charge derivation
  consume calculated snapshots. Historical rendering and remakes use snapshots.
- Native Compose customization and complete encrypted intent recovery extend the
  existing Attendance cart. Guest and Web POS share the same selector/preview.
- Gerência configures existing Product IDs at `/manage/catalog`; Quick Catalog and
  ProductIcon ownership remain unchanged. Bar/Kitchen render options separately
  from exceptional notes and expose versioned option/variant availability actions.
- ADR 0013 records pricing, concurrency, authorization and polling decisions.

## Verification commands

From `apps/api`, use the repository Python environment:

```sh
python manage.py test --settings=rodada_api.settings_test
python manage.py makemigrations --check --dry-run --settings=rodada_api.settings_test
python manage.py migrate --settings=rodada_api.settings_customization_postgres
python manage.py test tests --settings=rodada_api.settings_customization_postgres
```

The customization PostgreSQL settings are test-only and require a dedicated local
PostgreSQL 17 container/database at 127.0.0.1:55449. Never point them at a live database.

```sh
ANDROID_HOME="$HOME/Android/Sdk" ./scripts/android-check.sh
cd apps/web
npm run typecheck
npm run build
RODADA_VISUAL_PORT=3130 RODADA_REFERENCE_PORT=3131 npm run test:visual
RODADA_TEST_PYTHON=/path/to/python npm run test:integration
```

Browser integration also supports the existing `RODADA_E2E_POSTGRES=1` contract with
a dedicated `rodada_web_e2e` database; this delivery verifies it in PostgreSQL as well.

### T08a — repetição Android
Reutilizar IDs históricos da configuração sem defaults silenciosos; revalidar seleções contra catálogo atual, informar preço/descrição anteriores e atuais e bloquear legado/configuração inválida. Não alterar snapshots confirmados.

### T08b — configuração na repetição Web
Snapshot conserva IDs opcionais na representação Web sem alterar exibição existente. Repetição exige metadados verificáveis, valida variantes/opções/grupos e usa preço atual; não usa defaults para substituir seleção histórica. Configurações distintas seguem linhas distintas no draft.
### T08c — repetição guest
Reutilizar revisão canônica compartilhada, IDs de produto/variant/options e nota
histórica; catálogo guest atual fornece preços e disponibilidade. Sem substituição
por defaults quando configuração está removida, inválida ou não verificável.
Releitura antes da inclusão exige revisão idêntica e visita original. Linhas com
configuração distinta permanecem distintas; envio mantém intenção T05b.

### T08d — revisão compartilhada no PDV
Habilitar guard de repetição nas duas superfícies de OrderWorkspace, exibir
histórico/revisão no PDV e nomear região do rascunho. Bloquear recibo durante
leitura/revisão e repetição durante personalização. Reutilizar autorização,
catálogo e intenção sem mutation nova. Testes PDV espelham os critérios comuns,
acrescentam recebimento ambíguo e encerramento durante revisão. Journeys reais
PostgreSQL validam preço atual, snapshot antigo, drafts por Tab e replay.

### T09a — quantidade e agrupamento guest
Agrupar localmente Product/variant/options/note idênticos, preservando unidades
na edição e repetição. Validar o resultado inteiro antes de substituir o draft;
limite 99 sem truncamento. Reutilizar grid/controles de quantidade existentes e
feedback acessível. Alterações de quantidade não modificam intenções pendentes.
Cobrir configuração distinta e ordem de opções, notas exatas, limite de inclusão/
edição/repetição, dados obsoletos, disponibilidade, bloqueios e jornadas reais em
PostgreSQL 360/390/430 com resposta perdida e replay. Sem regra/API nova.

### T09b — descoberta guest
Reutilizar helpers de busca/categoria do Atendimento e Product.category projetada
pela leitura guest. Filtrar apenas exibição; catálogo completo conserva revisão
por IDs, quantidades e seleção. Todos inicial, busca global, categoria ao limpar,
fallback quando removida e contagem/vazio. Acesso Pedido atual fica estável mesmo
vazio e foca o draft. Ensaiar 146 produtos (143 CSV + três fixtures existentes),
configuração, bloqueios/atualização/revogação/intent, Web/API PostgreSQL em três
larguras e visual completo, sem modificar referências ou tolerâncias.

T10b/Spec026: derivar resumo de produção a partir do snapshot operacional imutável, renderizar configuração e manter legado independente. Lote canônico posterior exige novo contrato de replay/precondições, sem fan-out.


T10c.1: journal por sessão/chave; lock Tab antes de Item também na transição individual; precondições atômicas e recibo por linha. Cobrir replay, autorização, conflitos, concorrência e rollback em PostgreSQL. T10c.2: seleção/revisão e intenção persistida Web.

T10c.2: hook de intenção persistida, ActionDialog de seleção/revisão e resultado por linha. Fixtures testam perda de resposta, readback, sessão, armazenamento, conflito e revisão obsoleta; PostgreSQL/Web real prova replay sem duplicar. Executar tipos/build/visual completo e mobile360/390/430.

T10c.2: diálogo recebe foco de origem explicitamente; leitura pós-recibo tem prioridade sobre refrescos concorrentes. Pendência só é liberada depois de recibo por linha validado e leitura atual. Próxima T10d: investigar e remover bloqueios independentes somente por escopo protegido (UX23); gate amplo continua aberto.

T10d.1: reutilizar validação/envelope/recibo de lote; journal browser de intenções individuais por item, coordenador de leituras pós-comando e botões verificados com lock por ID. Manter legado/lote/disponibilidade conservadores. Testar concorrência, erro de uma linha, estado obsoleto, reload/replay, sessão/storage e mobile em fixtures/Web/API PostgreSQL; visual completo sem relaxar baseline.
T10d.2: lock individual considera IDs do lote persistido; validar envelope e vínculo de sessão do lote antes de enviar item independente. Manter bloqueio global pré-persistência/revisão e demais escopos; testar coexistência/replay e regressões em PostgreSQL e visual completo.
