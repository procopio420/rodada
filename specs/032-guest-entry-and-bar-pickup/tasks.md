# Spec 032 — Tasks de implementação

**Todas pendentes.** Marcação somente após código, teste e evidência no mesmo SHA. Não transformar checklist em prova de implementação.

## S0 — Design, domínio e auditoria de contratos
- [ ] S032-T00 Ler specs 004/009/014/026/029, #146, PRs #211/#212 e evidência do código atual; identificar gaps vs. funcionalidades já feitas.
- [ ] S032-T01 Aprovar matriz de estados e texto dos fluxos `flows.md`; acompanhar UX com `rodada-ux-handoff`/`rodada-ux-critique`.
- [ ] S032-T02 Definir contratos `PhysicalTag`, `GuestVisit`/provisional occupancy, `PickupGroup`, `PickupCode`, `ReleaseBasis` e eventos de provenance; ADR se exigir decisão arquitetural durável.

## S1 — Mesa/QR configurável
- [ ] S032-T03 API: registrar tags em lote do Venue, validação de token opaco, migração/backward-compatible e resolução legado/novo.
- [ ] S032-T04 API: criar Table sem obrigar tag física, bind/unbind/transfer transacional e auditado com constraint de vínculo único, CAS, tenant e capability.
- [ ] S032-T05 Atendimento Android/Web: criar mesa imediatamente; sheet `Vincular QR`/`Agora não`; indicador discreto `Sem QR`; retry seguro.
- [ ] S032-T06 Testar scanner recusado, QR inválido, tag já em uso, duas vinculações concorrentes e substituição sem alterar Tab/Occupancy.

## S2 — Autoabertura na mesa
- [ ] S032-T07 API: resolver QR read-only sem ocupação e CTA que cria/adere atomicamente à ocupação, associando GuestSession/generation.
- [ ] S032-T08 Política TTL de início provisório sem pedido; proibir expiração se existir fato financeiro/atendimento/pedido pendente.
- [ ] S032-T09 Guest UI: `Começar nesta mesa`, ocupar quando permitido, segundo cliente gera Tab privada, convite explícito para comanda compartilhada.
- [ ] S032-T10 Negativos: URL fotografada/reutilizada, QR revogado, rate limit, bloqueio staff, Venue estranho, dois scans simultâneos, `DIRTY/CLEANING/OUT_OF_SERVICE`.

## S3 — QR geral e continuidade
- [ ] S032-T11 QR geral Venue-scoped e landing guest sem mesa; preservar host/tenant/CSRF.
- [ ] S032-T12 Resolver/retomar Tab autorizada em qualquer entrada, nova Tab explícita, troca segura de localização segundo Spec 009.
- [ ] S032-T13 Recuperação por token opaco armazenado de forma segura/link privado, não por FG84, com revogação e rotação.

## S4 — Pedido e liberação de retirada
- [ ] S032-T14 Implementar modalidade AT_TABLE/PICKUP por Order e snapshot imutável na aceitação; preservar destinos BAR/KITCHEN.
- [ ] S032-T15 Autorizar pedido/retirada com fonte canônica: paid confirmed ou authorized-on-tab conforme limite; pending/error/unknown falham fechado, sem débito duplicado.
- [ ] S032-T16 Implementar PickupGroup e PickupCode único por Venue com janela/quarentena, auditoria e política antifraude; QR de ficha, se existir, não deve expor credenciais.
- [ ] S032-T17 Guest pickup UI responsiva com código gigante, estado verdadeiro, itens/grupos parciais, lugar e aviso para mostrar no balcão.
- [ ] S032-T18 Bar/Kitchen queue: mostrar código, status e busca instantânea; itens de grupos separados; legacy/printed fallback.
- [ ] S032-T19 Testar mudança modo 21:59/22:00, dois modos coexistentes, conta a prazo autorizada/negada, webhook duplo, duplicidade de código.

## S5 — Retirada sem taps compulsórios
- [ ] S032-T20 Registrar milestones GUEST_DECLARED/STAFF_CONFIRMED/INFERRED/UNKNOWN com source, actor, confidence e provenance auditáveis; não confundir observação com fato.
- [ ] S032-T21 `Já retirei` e `Entregue` opcionais, `Não recebi` e correções por exceção; não bloquear produção.
- [ ] S032-T22 Retirada parcial por PickupGroup e itens/quantidades; fila principal esconde expirados mantendo busca/histórico/pendência canônica.
- [ ] S032-T23 Testar captura de tela repetida, código reapresentado, pessoa pede segunda vez, ninguém confirma, partial/unknown, prova exigida em modo de risco.

## S6 — Conta, saída e recuperação
- [ ] S032-T24 Cliente vê somente sua Tab/partes autorizadas; pagamento parcial e compartilhado sem exposição indevida; fechamento da Tab não libera Table.
- [ ] S032-T25 Estados payment pending/confirmed/failed provenientes do provider/cashier; modo externo não credita dinheiro sem registro autorizado.
- [ ] S032-T26 Recuperação após fechar navegador/perder celular/trocar dispositivo; caixa localiza pedido sem acessar dados de outra Tab sem capability.
- [ ] S032-T27 PWA offline/lost-ACK/restart: reusar idempotency key e recuperar resposta canônica, sem duplicar order/payment/pickup.
- [ ] S032-T28 Testar quarto participante, split, pessoa mudou de mesa, última Tab fechada ainda na mesa, retirada com pedido já pago.

## S7 — QA, acessibilidade e release gates
- [ ] S032-T29 Unit/integration PostgreSQL concurrency, replay, money, tenant/host, auth/CSRF e mutation/audit tests por slice.
- [ ] S032-T30 E2E turno 20h→2h Web guest, Atendimento, Bar, Caixa, com pedidos de mesa e pickup simultâneos, cartões/pix simulados seguros.
- [ ] S032-T31 Screenshot real 360/390/430, fontScale 1/2, teclado/TalkBack, desktop, safe area e contraste; UX tasks sob carga com medidas reais.
- [ ] S032-T32 Revisão R3 independente para mutações auth/money/tenant/migrations; separação entre CODED, TESTED, CI, HOMOLOGATED, DEPLOYED.
- [ ] S032-T33 Documentar flags, rollout, rollback, métricas e riscos residuais; rollout piloto apenas por autorização específica.

## Não duplicar trabalho

- #146 é owner da identidade e das tags NFC de Tab, enquanto esta spec é owner do **binding de tag de mesa** e pickup code. Compatibilizar APIs antes de alterar schema.
- PR #211 / Spec 031 é owner de feedback de **entrega à mesa**. Esta spec cuida da **retirada no balcão**, alinhando provenance.
- PR #212 permanece protótipo de UX do Atendimento, não implementação de produção.
