# Tasks — Spec 027

**Implementação local em validação.** Itens marcados têm código e evidência local em `evidence.md`; gates PostgreSQL/UI/aparelho continuam pendentes. Atualizar para [x] somente com código, teste e evidência real; o PR de documentação não implementa tarefas.

## P0 — Contrato e domínio
- [x] T027-01 Inventariar API/permission atuais, mapear conflitos com Specs 004/009/024 e revisar ADR 0018.
- [x] T027-02 Definir serialização e storage de idempotência para start/open/claim com fingerprint, replay e recuperação durável.
- [x] T027-03 Criar migração nullable de responsabilidade da `TableOccupancy` com versão e provenance/auditoria, sem backfill inferido.
- [x] T027-04 Expor owner e Tabs da ocupação na projeção staff; manter payload guest sanitizado.
- [x] T027-05 Implementar `start_table_service` (lock, estados, ownership inicial, audit/outbox, erros e replay).
- [x] T027-06 Implementar `open_tab_in_occupancy` (atomicidade Tab+Assignment, validação de generation/venue, rollback, replay).
- [x] T027-07 Registrar endpoints e permitir comandos mínimos no gateway Atendimento Web sem finanças.
- [ ] T027-08 Criar testes de concorrência PostgreSQL (start/start, release/open), autorização, QR e replays.
- [ ] T027-09 Integrar Android: ficha disponível/ocupada, botão start, nova comanda contextual, navegação direta Tab.
- [ ] T027-10 Integrar Web companion com paridade de fluxo sem pagamento e leitura canônica.
- [ ] T027-11 Proteger drafts e recuperação de start/open após timeout/kill/reload antes de declarar jornada segura.
- [ ] T027-12 Garantir que links de Tab na mesa desambiguam homônimos e não dependem de label para selecionar ID.
- [x] T027-24 Projetar no backend `unassigned_service_attention` derivado por ocupação, com contagem/antiguidade de pedidos `GUEST` confirmados e prontidão canônica; sem leaks e sem N+1.
- [ ] T027-25 Exibir destaque persistente `Pedido via QR · Sem responsável` em Agora/Atendimento Android e Web, indicação discreta na mesa sem pedido e CTA `Ver mesa` / `Assumir atendimento`.
- [ ] T027-26 Testar deduplicação por occupancy/generation, reconexão/reload, claim/release, guest DIRECT, fila de produção e 2 pedidos concorrentes sem geração de DispatchTask.

## P1 — Claim explícito e polimento
- [x] T027-13 Implementar claim/takeover versionado com no-op do mesmo responsável, 409 e auditoria de transição.
- [ ] T027-14 Mostrar responsável atual e ações "Assumir atendimento" / "Atender sem assumir" sem exclusividade.
- [x] T027-15 Testar ajuda de outro garçom: order confirmed_by diferente do responsible_staff, sem troca de ownership.
- [ ] T027-16 Testar race claim/claim, cliente QR primeiro e ocupações migradas sem responsável.
- [ ] T027-17 Corrigir rótulos "Pedir" vs "Nova comanda" e mover comanda já alocada via Spec 009.
- [x] T027-18 Revalidar fluxos de liberação/limpeza/revogação, ownership da próxima ocupação e sessões stale.

## Gates
- [ ] T027-19 Executar suite Django + PostgreSQL integração, checar N+1/saldo na projeção de mesas.
- [ ] T027-20 Executar testes Android e UX de recuperação, incluindo offline e reinício de app.
- [ ] T027-21 Executar Web typecheck/build, `npm run test:visual`, testes integração/rota sem finanças.
- [ ] T027-22 Teste de turno isolado com duas contas na mesma mesa, QR guest, ajudante e movimentação entre mesas.
- [ ] T027-23 Registrar before/after com toques medidos e erros reais; documentar blockers/GO-NO-GO de piloto.

## Estado dos clientes

Código para T027-09/10/11/12/14/25 e testes para T027-08/16/26 entregue, mas checklist mantido pendente até execução dos gates específicos. T027-17 (mover comanda/rótulo global), rollout por Venue e ensaio do piloto ainda requerem trabalho. Ver `evidence.md` para os limites exatos.
