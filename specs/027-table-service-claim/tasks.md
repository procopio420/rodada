# Tasks — Spec 027

**Todas pendentes.** Atualizar para [x] somente com código, teste e evidência real; o PR de documentação não implementa tarefas.

## P0 — Contrato e domínio
- [ ] T027-01 Inventariar API/permission atuais, mapear conflitos com Specs 004/009/024 e revisar ADR 0018.
- [ ] T027-02 Definir serialização e storage de idempotência para start/open/claim com fingerprint, replay e recuperação durável.
- [ ] T027-03 Criar migração nullable de responsabilidade da `TableOccupancy` com versão e provenance/auditoria, sem backfill inferido.
- [ ] T027-04 Expor owner e Tabs da ocupação na projeção staff; manter payload guest sanitizado.
- [ ] T027-05 Implementar `start_table_service` (lock, estados, ownership inicial, audit/outbox, erros e replay).
- [ ] T027-06 Implementar `open_tab_in_occupancy` (atomicidade Tab+Assignment, validação de generation/venue, rollback, replay).
- [ ] T027-07 Registrar endpoints e permitir comandos mínimos no gateway Atendimento Web sem finanças.
- [ ] T027-08 Criar testes de concorrência PostgreSQL (start/start, release/open), autorização, QR e replays.
- [ ] T027-09 Integrar Android: ficha disponível/ocupada, botão start, nova comanda contextual, navegação direta Tab.
- [ ] T027-10 Integrar Web companion com paridade de fluxo sem pagamento e leitura canônica.
- [ ] T027-11 Proteger drafts e recuperação de start/open após timeout/kill/reload antes de declarar jornada segura.
- [ ] T027-12 Garantir que links de Tab na mesa desambiguam homônimos e não dependem de label para selecionar ID.

## P1 — Claim explícito e polimento
- [ ] T027-13 Implementar claim/takeover versionado com no-op do mesmo responsável, 409 e auditoria de transição.
- [ ] T027-14 Mostrar responsável atual e ações "Assumir atendimento" / "Atender sem assumir" sem exclusividade.
- [ ] T027-15 Testar ajuda de outro garçom: order confirmed_by diferente do responsible_staff, sem troca de ownership.
- [ ] T027-16 Testar race claim/claim, cliente QR primeiro e ocupações migradas sem responsável.
- [ ] T027-17 Corrigir rótulos "Pedir" vs "Nova comanda" e mover comanda já alocada via Spec 009.
- [ ] T027-18 Revalidar fluxos de liberação/limpeza/revogação, ownership da próxima ocupação e sessões stale.

## Gates
- [ ] T027-19 Executar suite Django + PostgreSQL integração, checar N+1/saldo na projeção de mesas.
- [ ] T027-20 Executar testes Android e UX de recuperação, incluindo offline e reinício de app.
- [ ] T027-21 Executar Web typecheck/build, `npm run test:visual`, testes integração/rota sem finanças.
- [ ] T027-22 Teste de turno isolado com duas contas na mesma mesa, QR guest, ajudante e movimentação entre mesas.
- [ ] T027-23 Registrar before/after com toques medidos e erros reais; documentar blockers/GO-NO-GO de piloto.
