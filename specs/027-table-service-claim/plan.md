# Plan — Spec 027

**Status:** implementação local com backend verificado em SQLite; clientes aguardam gates externos conforme `evidence.md`.

## Sequência segura de implementação

### Fase 0 — Baseline e contrato
- Revisar `AGENTS.md`, Specs 004/008/009/014/024/026, ADR 0004, backend hospitality/ordering, Android `TablesScreen`/`AttendanceScreen` e Web `AttendanceWeb`/`OrderWorkspace`.
- Capturar journeys anteriores em fixture descartável com nomes duplicados, 0/1/3 comandas, mesa guest DIRECT e sem mesa. Reportar cliques como medidos ou estimados.
- Congelar API payload/errors/idempotência; validar se `table.manage` + `tab.open` existentes bastam.

### Fase 1 — Ownership opcional + leitura canônica
- Migração aditiva nullable: `TableOccupancy.responsible_staff`, `responsible_since`, `responsibility_version` com default seguro. Preservar ocupações antigas e QR.
- Criar trilha imutável de responsabilidade (eventos/auditoria, sem alterar `DispatchTask.claimed_by`). Projetar ownership na listagem/detalhe de mesa staff.
- Projetar no backend o estado staff `unassigned_service_attention` da ocupação + pedidos guest confirmados (contagem/antiguidade/readiness), evitando consultas N+1 e exposição no payload guest.
- Testes de isolamento por Venue, visibilidade, índices e não-vazamento guest.

### Fase 2 — Start e abertura contextual transacionais
- Serviço `start_table_service`: lock Table, verificações, occupancy única, ator responsável, audit/outbox e comando idempotente recuperável.
- Serviço `open_tab_in_occupancy`: lock serializado, validate generation, `open_tab` + vínculo em única transação, replay e erros canônicos.
- Adicionar rota `service/start/` e `occupancies/{id}/tabs/open/`; preservar aliases legados.
- Exercitar cenário QR DIRECT (guest iniciou primeiro), attach legado, release concorrente e PostgreSQL.

### Fase 3 — Claim/takeover explícito
- Serviço `claim_occupancy_responsibility` usando CAS/version, mesmo ator no-op, transferências com provenance e auditoria.
- Sem gate de ownership na confirmação de pedidos, recebimentos e dispatch. Não exigir PIN extra para claim ordinário da equipe.
- Teste de acesso revogado, staff inativo, takeover duplo e no-op.

### Fase 4 — UX Android / Web
- Ficha/lista de mesas com "Iniciar atendimento" em AVAILABLE, painel de comandas clicáveis em OCCUPIED, responsável e CTA contextual.
- Exibir `Sem responsável` discretamente em Mesa sem pedido confirmado e `Pedido via QR · Sem responsável` em destaque persistente no Agora/Atendimento quando houver pedido guest confirmado; priorizar item realmente pronto, 1 aviso agregado por ocupação, CTAs `Ver mesa` e `Assumir atendimento`.
- Nova comanda contextual leva direto à seleção de produtos; nome/customer opcionais. Sem roubar foco de pedidos já em rascunho.
- Android: intent persistente e estado de resultado desconhecido; Web: recuperação segura após reload. Não emitir novo UUID após timeout.
- BFF Web: allowlist estrita de start/claim/open e GET; proibir pagamento, cash, refunds. Ações irreversíveis de release continuam protegidas.
- Design System: fonte/contraste/toque, 360–430 px, mensagens curtas; não usar claim como login nem exigir tela de gestão.

### Fase 5 — Gates e rollout
- Testes unitários, API, PostgreSQL concorrente, Android instrumentado, Web integration/visual, regressões de specs adjacentes.
- Ensaio com 2 funcionários concorrentes, QR e comanda individual/compartilhada em banco descartável; não executar pagamentos reais.
- Verificar destaque do QR antes/depois de confirmação, segundo pedido, item pronto, claim por outro garçom, reload, release e nova geração da mesa; capturar evidência no Agora sem duplicar tarefas Dispatch.
- Flag/configuração por Venue com rollback de UI/rotas que preserve dados/auditoria.
- Validar no Bar do Aderlan com roteiro: mesa vazia, nova pessoa, garçom ajudante, QR anterior, mudança de mesa, rede ruim, abertura errada.

## Topologia técnica e regras

- `hospitality` é dono de TableOccupancy e ownership; `ordering` é dono de Tab; serviço coordenador importa serviços internos em `transaction.atomic`, **não** faz HTTP interno.
- Mesma transação cria registro e evento auditável. SSE só depois do commit.
- IDs e versão sempre vêm da API; UI jamais monta associations apenas usando `display_label`.
- `opened_by`/`confirmed_by` registram autoria de ação, sem trocar responsável da mesa.
- Replays persistidos (escopo Venue + action + actor + key + fingerprint) são requeridos para start, open, claim. Um resultado em dúvida mantém payload/intenção congelados até readback.
- Ordem de locks para novas mutations: `ServiceCommand -> Table -> TableOccupancy -> Tab`; auditar integrações existentes para evitar ciclos e travas reversas. PostgreSQL único meio de validar corrida real.

## Decisões externas à execução inicial

- Eventual "Cancelar início de mesa vazia" exige especificação própria de `OCCUPIED -> AVAILABLE` segura, revogação e auditoria; não fazer bypass de limpeza.
- Automação de atribuição por zona, escala, covers, turnos ou análise de performance fica fora.
- Mapa visual 2D permanece pertencente à Spec 004 e não bloqueia MVP.
