# E06 — Tarefas executáveis

**Auditoria #272 encerrada somente como inventário técnico.** Recibo/matriz por AC e revisão própria em [e06-audit-closeout-20261022.md](../../e06-audit-closeout-20261022.md). Execução restante: [#315](https://github.com/procopio420/rodada/issues/315), [#316](https://github.com/procopio420/rodada/issues/316), [#317](https://github.com/procopio420/rodada/issues/317), [#318](https://github.com/procopio420/rodada/issues/318). Manter este checklist aberto para aceite global; não declarar AC-20..24 PASS.

**Dono:** QA/integrador. Executar parte baseline imediatamente e matriz final após epics proprietárias.

- [x] **E06-01 Baseline com SHA:** listar endpoints/código/suites já existentes e claims que podem ser testados agora; issue #106 e Spec 026/029; elaborar matriz de reuso/lacuna.
- [ ] **E06-02 Planos de teste:** fixture isolada com dois Venues, staff de roles distintos, 3 Tabs na mesma mesa, balcao, Guest, pedidos em Bar/Cozinha, CashShift e READY tasks.
- [ ] **E06-03 E2E feliz:** Web + Compose / QR + Django/Postgres + produção/dispatch + Caixa + Table/clean, verificar ids/ledger/version/epoch.
- [ ] **E06-04 E2E adverso:** POST commit + ACK perdido, restart Android, refresh Web, rede flapping, 409/replay, manager override expirado, operador trocado, stale occupancy, PSP pending.
- [ ] **E06-05 Visual:** Playwright screenshots 360/390/430/desktop com diffs, Compose screenshots emulator 360/390/430 equivalentes, um Android físico S24-class, TalkBack/fonte grande.
- [ ] **E06-06 Performance em pico:** 20 mesas/50 tarefas simultâneas, sem bloqueio de pedido por falha Dispatch, SLA de interação, sem N+1/scroll repetitivo.
- [ ] **E06-07 Instrumentação:** métricas reais de intenção→produção, passos, erro, duplicações e giro; provenance/retention e ausência de taps adicionais.
- [ ] **E06-08 Review:** reviewer independente R3 em endpoints/ledger e security; fixes P0/P1, checks repo branch protection, evidências de versão e logs.
- [ ] **E06-09 Piloto:** rehearsal com operador/bar, registrar feedback de gargalos; definir GO/NO-GO assinado, rollback e observação inicial pós-release.
- [ ] **E06-10 Release:** UX 2.0 é padrão único, sem flag para UX antiga. Validar políticas de domínio/capabilities por Venue/role e plano de reversão técnica de deploy/migrações sem apagar pedidos, alterar ledger ou mover versões de Tab; documentação e evidência final somente após release autorizado.

**Gate:** AC-20..24 PASS + todas AC-01..19 aplicáveis PASS; execução real exige autorização de merge/deploy separada. Capturas do protótipo não contam como validação integrada.

Inventário E06-01: [matriz atual](../../e06-current-evidence.md), baseline `b824d2e2`, CI Web39484200340. Conclusão do inventário não encerra ACs; demais gates permanecem abertos.


21/10: [evidência terminal e matriz](../../completion-20261021.md),
[tempos observados — slice1](../../observed-metrics.md) e
[recibo API reproduzível](../../rehearsal-receipt.md). API1069/1065 nos candidatos
respectivos, Web162 e visual97PASS; pico Web50READY+50chamados passou em quatro
larguras. E06-07 permanece parcial (cliente/comparativo) e E06-10 sem flag UX/
rollback ensaiado; Android instrumental atual/aparelho/piloto permanecem gates.
