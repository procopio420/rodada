# Tasks — Spec 004

## API/Domain

- [x] Table model + status
- [x] Zone textual P0 + associação auditada Table -> Zone
- [ ] FloorPlan model + guest/staff projections
- [ ] TablePlacement model + active-placement invariant
- [ ] normalized x/y coordinates + placement history
- [ ] optimistic locking/version on placement mutation
- [ ] TableGroup temporary grouping
- [x] TableOccupancy model + invariants
- [ ] TablePlacement ↔ ServicePoint/Zone integration
- [x] Tab ↔ TableOccupancy optional association
- [x] enforce multiple Tabs per occupancy
- [x] release table service
- [x] cleaning start/complete services
- [x] increment `access_generation` on cleaning completion
- [x] GuestSession model
- [ ] TabIdentifier model
- [x] opaque Table public token
- [ ] short code identifier
- [ ] dynamic Tab QR identifier
- [ ] NFC_TAG association/revocation
- [x] guest ordering modes
- [x] guest block/unblock
- [x] server-side generation validation
- [x] rate limiting
- [x] audit events
- [ ] metrics queries

## Guest PWA

- [x] resolve QR
- [x] table context screen
- [ ] sanitized 2D floorplan
- [ ] "Onde vocês estão?" placement flow for unplaced Table
- [ ] handle placement conflict/stale version
- [x] create anonymous/named Tab
- [ ] join existing Tab by short code
- [ ] optional login/profile path
- [x] menu/catalog consumindo disponibilidade operacional compartilhada
- [x] item indisponível visualmente desabilitado
- [x] tratamento de carrinho stale quando disponibilidade muda antes do submit
- [x] add item / notes
- [x] submit order
- [x] persistent navigation: Cardápio / Pedidos / Conta
- [x] quick-add item; modifiers only when required
- [x] live order summary
- [x] simplified guest order status
- [x] reorder previous available items
- [x] structured service/bill requests to Dispatch
- [x] tab total / own-part projection when available
- [ ] show dynamic Tab QR

## Staff Web

- [ ] 2D floor canvas with movable Table markers
- [ ] place previously unplaced Table
- [ ] clear placement when Table is physically removed/stored
- [ ] drag/reposition active Table without touching occupancy/tab
- [ ] create/dissolve TableGroup
- [x] table board: AVAILABLE / OCCUPIED / DIRTY / CLEANING / OUT_OF_SERVICE
- [x] occupancy detail with multiple Tabs
- [x] release table
- [x] start cleaning
- [x] mark clean/available
- [x] guest ordering block toggle
- [x] associate/move Tab
- [ ] issue/revoke NFC tag
- [ ] show/copy short code

## Quality

- [x] cannot order against sequential/raw table id
- [x] old GuestSession rejected after occupancy release/generation change
- [x] guest block rejects guest mutation but staff still orders
- [x] two Tabs on same occupancy remain financially independent
- [x] closing last Tab does not release table
- [ ] cleaning timestamps produce deterministic metrics
- [ ] NFC reassignment revokes previous association
- [ ] moving a Table preserves occupancy, Tabs, Orders, ledger and QR
- [ ] guest floorplan does not expose internal operational state
- [ ] concurrent placement update rejects stale version
- [ ] grouping Tables never merges financial identity
- [x] rate limit tests
- [x] authorization tests

- [x] Round 2: guest service/bill buttons call persisted Dispatch requests without financial mutations.
- [x] Round 2: retain integrated browser/visual evidence at final release SHA.

## Reconciliação de 14/10/2026

Ver [matriz completa e gates por SHA](closeout.md). Checkboxes de roadmap
permanecem pendentes: FloorPlan/Placement #144; TableGroup #145;
TabIdentifier/código/QR/NFC #146; perfil Customer #147; métricas/queries #148.
Navegação/status foram gaps reais implementados neste fechamento; evidências executadas e gates por SHA
registrados em closeout.md. Não confundir inspeção com homologação de campo.

## Gestão de mesas
Contrato: [management-tables.md](management-tables.md). Implementar serviço transacional de quantidade/estado, API protegida, tela dedicada e testes PostgreSQL/mobile. Recorte implementado e validado localmente; evidência e limites em [management-tables-evidence.md](management-tables-evidence.md).


### #148 — métricas de giro (branch `codex/issue-148-table-turnover-metrics`)

- [x] Consulta canônica para períodos operacionais e isolamento Venue implementada.
- [x] Endpoint protegido, indicadores e cobertura na Gerência implementados.
- [x] Testes determinísticos para incompletos, cronologia, Guest/Staff, foreign Venue, corte e DST adicionados.
- [ ] Validar PostgreSQL, `manage.py check`, migrações, Web typecheck/build/integration/visual no HEAD final.
- [ ] Revisão independente R3 e merge condicionado a CI verde; então fechar #148.

A inclusão de testes **não comprova execução**; não marcar validações com base em código ou PR.


### #145 — TableGroup (branch `codex/issue-145-table-groups`)

- [x] Domínio/modelagem, migration, grupos/membros exclusivos e auditoria implementados.
- [x] API protegida, projeções staff/Guest e tela para criar/desfazer grupos implementadas.
- [x] Testes de isolamento, autorização, replay, integridade financeira e concorrência PostgreSQL escritos.
- [ ] Executar testes de API/PostgreSQL, migrações/qualidade, Web integration/visual e CI do HEAD final.
- [ ] Corrigir findings em revisão independente R3 e aceitar/mergear; só então fechar #145.

### #147 — Customer opcional (branch `codex/issue-147-optional-guest-customer`)

- [x] Modelos/migration de credencial e sessão de perfil separados do GuestSession/Tab.
- [x] Cadastro, login, contexto autenticado, claim condicionado à ocupação, logout e rotação de senha com revogação implementados.
- [x] BFF HttpOnly e UI Guest opcional implementados; fluxo anônimo mantido.
- [x] Testes de autenticação, account takeover, Venue, rotação, replay, ocupação alterada e concorrência PostgreSQL escritos.
- [ ] Executar Django/PostgreSQL, migrations, auth/BFF/Web/visual/E2E e qualidade no SHA final; corrigir failures.
- [ ] Revisão independente R3 sem P1/P0 aberto; aceite e merge autorizado; só então fechar #147.

Checkpoint de integração (2026-10-15): `main` com TableGroups #145 e pairing Windows S2 reconciliada sem descartar Customer; o aceite #147 permanece condicionado a CI do novo HEAD e revisão R3 independente.

### Spec025 preflight — concurrent profile rotation regression

- [x] Prove cross-Venue same-credential rotation failure on disposable PostgreSQL.
- [x] Lock global credential before per-visit authorization; revalidate revocation/version under locks.
- [ ] Verify old tokens denied and anonymous visits preserved; independent R3 review and final CI before merge.


## Cliente UX 2.0 — fechamento de especificação, execução ainda pendente

Fonte canônica: [guest-ux20-contract.md](guest-ux20-contract.md). A aprovação dos fluxos em 16/10/2026 não significa implementação em Django/Web/Manage.

### Slice A — configuração e acesso (backend/Manage)
- [ ] Mode tipado por Venue MESA / FICHA / HIBRIDO, capability gerencial, auditoria, migração e defaults compatíveis.
- [ ] AccessPoint tipado TABLE/BAR_PICKUP, geração e resolução de QR distintos; Híbrido por QR/área.
- [ ] Snapshot do tipo de serviço em Tab e regra para sessões existentes ao alterar modo.

### Slice B — bebida e fila BAR (backend/Web)
- [ ] Elegibilidade explícita BEVERAGE + BAR_PICKUP e revalidação transacional antes de confirmar Order.
- [ ] Bloquear comida, porções, combos mistos e manipulação de API na Ficha.
- [ ] FG84 legível, único entre fichas ativas, exibido ao cliente e na fila BAR; sem scan obrigatório.
- [ ] Tab de Ficha sem TableOccupancy, retirada opcional sem mutar estado canônico por confirmação guest.

### Slice C — interface Cliente e integração
- [ ] Implementar Web guest fiel ao protótipo aprovado: dois destinos, pedidos ativos, confirmação sem navegação, conta recolhida e Ficha.
- [ ] Unificar serviço/entrega por modo sem inventar terceira aba; preservar staff e cliente sem celular.
- [ ] Validar pagamento parcial/prepay, pendência PSP, autorização Tab e políticas de exposição invisíveis.

### Slice D — qualidade/fechamento técnico
- [ ] E2E UI/API/PostgreSQL em Mesa/Ficha/Híbrido, isolamento, mudança do Venue com sessões em aberto, auto bloqueio de comida Ficha, retry e código FG84.
- [ ] Screenshots Playwright 360/390/430/desktop; a11y e teclado; CI SHA final, R3 e merge.
- [ ] Go/no-go de rollout por Venue com rollback seguro, sem prejudicar Tabs antigas.

**Horários automáticos** devem virar spec/slice futura após validação comercial; não misturar com estes P0.
