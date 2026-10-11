# Rodada — plano de fechamento das quatro lacunas de operação
**Data:** 2026-10-11 (America/Sao_Paulo)  
**Base auditada:** `main` em `2aef9d3663db0a34ece49c87299b5ff3e37596dd`; matriz de aceite de 2026-10-09, round 2.  
**Objetivo:** preparar uma release candidate segura para um turno supervisionado no Bar do Aderlan, sem afirmar homologação de meios de pagamento, dispositivos ou impressão física.

> Este é um plano, não uma declaração de implementação. Cada critério continua com o status atual da matriz até existir código, testes e evidência específica no SHA integrado. Não reinterpretar `PARTIAL` como `PASS`. Não ativar pagamentos reais nem usar banco de produção na validação.

## Estado de partida e trabalhos em andamento

| Frente | Escopo | Status histórico da matriz (PASS/PARTIAL/MISSING/EXTERNAL_BLOCKED) | Primeiro resultado buscado |
|---|---|---|---|
| A — Conectividade/recuperação | Spec 014 | 4 / 14 / 5 / 2 | Intenções persistidas e replay seguro, inclusive conflito de dinheiro |
| B — Configuração segura | Spec 013 | 4 / 8 / 1 / 0 | Não desativar estação com trabalho ativo |
| C — Fechamento e auditoria | Specs 007 + 012 | 18 / 9 / 4 / 0 | Daily Close canônico, imutável, revisável |
| D — Impressão/contingência | Spec 015 | 13 / 0 / 1 / 1 | AUTO_FALLBACK com heartbeat confiável e dedupe |

Os números são da auditoria de 09/10, não de uma nova execução nem de uma contagem exaustiva da Spec 024. As Specs 006, 018 e a homologação física/PSP continuam com bloqueios independentes.

**PRs em curso no início deste plano:** [#71 — recebimentos por método](https://github.com/procopio420/rodada/pull/71), tocando Caixa/API e Web, e [#72 — chamados de clientes no Atendimento](https://github.com/procopio420/rodada/pull/72), tocando Atendimento Web e proxy. Primeiro decidir ambos com CI; agentes não devem sobrescrever suas alterações ou assumir que foram mesclados. Planejar branches novas sempre a partir de `origin/main` atualizado.

## Regras globais de engenharia e integração

1. Um agente por frente, branches `feat/spec014-safe-recovery`, `feat/spec013-safe-config`, `feat/spec007-012-daily-close` e `feat/spec015-kds-fallback`. Sub-PRs pequenos por milestone; não trabalhar em um único PR gigante.
2. Cada mudança deve atualizar primeiro a spec/acceptance/tasks relacionada **sem marcar PASS prematuramente**, ADR se mudar regra, migration se necessária, teste automatizado + cenário reproduzível. Documentar SHA, ambiente, comando, log sanitizado, AC exatos cobertos e riscos residuais.
3. DB PostgreSQL de teste isolado para concorrência/transações/row locks; testar permissões por Venue, perfis, idempotency keys, colisões e retry. UI: typecheck/build, Playwright mobile 360/390/430, acessibilidade e estados offline/loading/error. Android: testes de unidade, lint, assemble, emulador API 36 e process death quando aplicável.
4. Contratos do domínio prevalecem sobre UI: nenhum frontend cria diretamente Payment, Charge, CashMovement, PrintJob ou o estado final de uma Order. HTTP/DB são fonte de verdade; SSE é notificação, não autorização.
5. Não reutilizar/rotacionar credentials/segredos da demo; não usar dinheiro real, PSP real, impressão física ou tabela de produção para provar uma suíte simulada. AUTO_FALLBACK e Classe C offline ficam **desabilitados por padrão** até gates específicos.
6. Merge sequencial com CI verde e revisão de efeitos financeiros; integrar A, B, C, D sobre a main mais recente e repetir smoke do fluxo completo após cada integração. Não fazer deploy da demo Railway somente porque o PR foi mesclado.
7. Critério `PASS` = evidência objetiva reproduzível para o comportamento completo no ambiente alegado. Caso exija periférico, credencial de PSP ou operação real, manter `EXTERNAL_BLOCKED` ou `PARTIAL`, com uma evidência de simulação separada.

## A — Spec 014: Recuperação após perda de conexão

**Problema:** o transporte HTTP/SSE e boa parte da idempotência já existem; falta concluir o ciclo de vida de intenção pendente e da evidência financeira offline, e provar reinício/revogação/conflito entre Android, backend e gerência. Não construir uma fila genérica que execute qualquer POST após reconectar.

**Arquivos/áreas iniciais:** `apps/attendance-android/.../operations/PendingMutationIntentStore.kt`, `OperationsRepository.kt`, `OperationsViewModel.kt`, `cash/`, `auth/`; `apps/api/modules/ordering/`, `ledger/`, `cash/`, `audit/`; `docs/development/operational-realtime.md`; testes de realtime, payments concurrency e Android.

### A1 — Persistência e replay de pedidos (primeiro PR)
- Envelopes **tipados e versionados** com `recovery_id`, `idempotency_key` original, `tab_id`, versão/snapshot, `actor/session/device`, `captured_at`, dependências e status local. Criptografia local; nunca armazenar PIN, PAN, CVV ou chaves de PSP.
- Máquina de estados explícita `DRAFT_LOCAL` → `PENDING_SYNC` → `RECONCILING` → `CONFIRMED` | `REQUIRES_REVIEW` | `REJECTED`. `PENDING` jamais entra em saldo/receita/comanda confirmada.
- Ao reiniciar/matar processo, reabrir exatamente as mesmas intenções e chaves. Reconsultar o canônico antes de reenviar. Retry em timeout pós-commit retorna a mesma Order/Charge; produto que ficou indisponível produz conflito sem pedido parcial.
- Revalidar sessão/capabilities antes de replay; associação ao ator original. Se comando 1 conflita, interromper as ações dependentes da mesma Tab (sem perder outros itens independentes).
- **Aceite:** 014-002/003/004/005/013/014/015, com teste API 36 + PostgreSQL: timeout depois do commit, kill/restart, indisponibilidade de produto, revogação de funcionário, conflitos sequenciais e UI de revisão.

### A2 — Contingência financeira auditável (segundo PR)
- `EmergencyCashEvidence` e `ExternalTerminalEvidence` (ou modelos tipados equivalentes) como **evidências**, nunca como pagamentos confirmados. Preservar valor, Tab, terminal/referência se existir, data de captura, device, operador, anexos permitidos e origem.
- Na reconexão, reconsultar **saldo canônico e permissões sob transação/lock**, conferir duplicidade por `recovery_id`/referência. Se evidencia R$ 50 e restam R$ 30, **REQUIRES_REVIEW** e zero lançamento automático de R$ 50. Terminal externo nunca recebe novo débito automático.
- Fluxo de gerente para aprovar/rejeitar com motivo, `reviewer`, `applied_at`, conflito visível, trilha imutável e nenhuma reatribuição silenciosa. Pix/Tap `CONFIRMATION_PENDING` são apenas reconciliados com backend/provedor, nunca repetidos como cobrança nova.
- **Aceite:** 014-008/009/010/016 e 012-015; negativa de acesso cross-Venue; testes de corrida entre pagamento, reconciliação e fechamento.

### A3 — Falhas reais e observabilidade (terceiro PR)
- Provar API offline com SSE online e o inverso; queda de internet, restart do app, restart dispatcher/Redis, cursor expirado, cache stale, revalidação e fallback limitado de polling. Cozinha/Bar continuam podendo ler dados seguros e não inventam evento.
- Métricas não sensíveis: quantidade de `PENDING_SYNC`, idade de intenção, tentativas e conflitos, `REQUIRES_REVIEW` e tempo até confirmação. Flags/alertas para fila travada.
- **Aceite:** revalidar 014-001/011/018/019/021/023/024 no head integrado. Classe C READY não deve ser habilitada sem replay/cancelamento demonstrado.

**Não fazer:** nova cobrança integrada automática, inferir sucesso de pagamento por resposta local, reconciliar item por quantidade/preço aproximados, transferir intenção a outro operador.

## B — Spec 013: Configuração operacional segura

**Problema:** configurações são parcialmente tipadas, mas uma troca de estação com pedidos ativos ainda não tem bloqueio demonstrado. Mudanças durante turno precisam de **preview + confirmação atômica + versão**, não de updates diretos sem validação.

**Arquivos/áreas iniciais:** `apps/api/modules/catalog/`, `ordering/`, `hospitality/`, `venue/`, `management/`; views de Gerência, telas de configuração e testes de permissão/concorrência.

### B1 — Station safe-change (primeiro PR e P0)
- Recurso tipado `StationConfiguration` (ou estrutura equivalente já existente), com status, versão, responsabilidade por BAR/KITCHEN e mecanismo de preview/read blockers.
- `preview` mostra **OrderItems** pendentes/em preparo, tickets e bindings ativos; `apply` revalida blockers sob lock/transação e exige versão atual (`409` com estado atual quando stale). Não permitir desativar a última estação responsável enquanto há trabalho ativo. Se houver remapeamento explícito, preservar itens/histórico e a responsabilidade até efetivação.
- Registrar ator, motivo, antes/depois, versão, `applied_at/effective_at`. Gerência exibe bloqueio e link para a fila correspondente.
- **Aceite:** 013-003; tests: KITCHEN única ativa com fila → 409 e fila intacta, dois gerentes concorrentes → 1 vitória/1 conflito, outra Venue sem acesso, nenhuma fila órfã.

### B2 — Guest emergency switch e políticas (segundo PR)
- Bloqueio **global por Venue** independente dos bloqueios individuais de mesa; checagem no backend em toda mutação guest (pedido, nova sessão se pertinente, serviço), com resposta explícita e revogação/revalidação de cache. Pedidos já confirmados continuam; staff continua atendendo.
- Revisar as seções tipadas e o versionamento de serviço: Tabs antigas conservam contexto/política enquanto novas recebem alteração na boundary escolhida; não recalcular silenciosamente.
- **Aceite:** 013-001/004/005, incluindo tentativa de bypass direto pela API.

### B3 — Mudanças com efeito futuro e integrações (terceiro PR)
- Calendário com versões `effective_from`, migrando leitura histórica sem reclassificação silenciosa; **não** simplesmente liberar edição retroativa em Venue com fatos anteriores.
- Status/capabilities do provedor com **secret redaction**, bloqueio de desativação enquanto houver `CONFIRMATION_PENDING`, auditoria; histórico de mesa permanece intacto em desativação.
- **Aceite:** 013-006/007/010/011/013. O teste de segredo nunca deve imprimir valor real. Pendente de PSP físico continua externo.

**Não fazer:** configurações genéricas JSON sem contrato tipado, apagar mesa com histórico, mutação retroativa que mude `business_date`, bypass de autorização na UI.

## C — Specs 007/012: Fechamento e auditoria

**Problema:** CashShift e movimentos/estornos já têm semântica financeira robusta e snapshot de fechamento de gaveta; falta um **Daily Close de Venue** persistido/revisado que consolide os vários caixas e explicite pendências, com correções posteriores separadas. Não confundir fechamento de turno de um caixa com fechamento do dia.

**Arquivos/áreas iniciais:** `apps/api/modules/cash/{models,services,views}.py`, `management/views.py`, `venue/calendar.py`, `ledger/`, `audit/`; `apps/web/app/manage/`, `apps/web/app/reports/`, `apps/web/app/cash/` (aguardar integração do PR #71 antes de editar esta tela).

### C1 — Snapshot auditável de fechamento diário (primeiro PR e P0)
- `DailyClose` por `(venue, business_date)` com versionamento/identidade imutável; capturar `generated_at`, cutoff/timezone **vigentes naquele dia**, snapshot de movimentos, venda líquida, pagamentos confirmados por método, estornos/ajustes, abertas/remanescentes, CashPoints/CashShifts e divergências.
- Distinguir `PREVIEW`, `INCOMPLETE`, `READY_FOR_REVIEW`, `REVIEWED` ou estados equivalentes; fechamento não pode marcar reconciliado se existe Shift OPEN/COUNTING, revisão pendente ou cobrança ambígua. Validar via transação/lock e utilizar consultas canônicas, nunca totalizar somente dados do navegador.
- A operação de revisão exige capability + reautenticação adequada e preserva assinatura de autoria, timestamp e versão consultada.
- **Aceite:** 007-007 e 012-009/012; turno não fechado após cutoff produz `INCOMPLETE`, não lança contagem fake; múltiplos caixas conferidos sem dupla contagem.

### C2 — Correções pós-fechamento (segundo PR)
- Correção tardia gera novo evento/ajuste versionado apontando para `DailyClose` original; jamais altera snapshot assinado ou `CashShift.expected_amount_cents_snapshot`. Exibir `original`, `post_close_adjustments`, `corrected_view` separadamente, com causa/operador/aprovação.
- Verificar corridas de `CASH payment vs shift close`, estorno confirmado em data posterior e retry da correção. Saldo de drawer e pagamentos por método não se confundem.
- **Aceite:** 007-008, 012-011, 012-013 permanece PASS, cross-day refund preserva provenance.

### C3 — Gerência e evidências (terceiro PR)
- Tela mobile-first de fechamento: resumo de recebimentos por método, tabs em aberto, discrepâncias por caixa, bloqueios navegáveis para turno/revisão, timeline de auditoria; estados `stale/offline`.
- A tabela mensal e comparação ocupação×receita (007-009/010), além de insights/push reais, são follow-ons P1 separados: **não** declarar toda Spec 007 concluída com este P0.
- **Aceite:** revisão com gerente e cashier em browsers reais, PostgreSQL isolado, relatório de período correto inclusive virada de dia.

**Não fazer:** reconciliar abertura/fechamento inventando movimentos, usar estado local como recebimento, sobrescrever histórico, mascarar dinheiro em trânsito como liquidado.

## D — Spec 015: Impressão e contingência com KDS indisponível

**Problema:** produção de documentos e PrintJob já têm dedupe, retry e reimpressão explícita testados; **não** reconstruir o módulo. A lacuna é o gatilho AUTO_FALLBACK baseado em saúde real do KDS, mais o hardware não testado.

**Arquivos/áreas iniciais:** `apps/api/modules/documents_printing/{models,services,views}.py`, `management/commands/recover_print_jobs.py`, `modules/realtime/`, `modules/ordering/`, `apps/web/app/kitchen/`, `bar/`, `manage/printing/`, `apps/api/tests/test_printing*.py`.

### D1 — Contrato de saúde KDS (primeiro PR)
- Heartbeat **autenticado e por estação/dispositivo**, timestamps e TTL no servidor, versão do KDS e estado atualizado. Definir estado operacional `HEALTHY`, `SUSPECT`, `UNHEALTHY`, `RECOVERING` e histerese; não confundir desconexão de **um navegador** com indisponibilidade de toda a estação.
- Configuração tipada por Venue/estação com fallback desligado por padrão, mínimo de tempo de ausência e período de recuperação. Não inferir falha do KDS só por falta de entrega de SSE.
- **Aceite:** detector estável contra perda/retorno intermitentes, múltiplos devices, relógio errado no cliente, restart, e privilégios de configuração.

### D2 — Enfileiramento automático idempotente (segundo PR)
- Somente confirmar fallback para OrderItems **já confirmados** e pertencentes àquela estação/generation. Identidade determinística por `(venue, station, order/generation, document_kind, initial)` ou constraint equivalente; inserir sob lock + unique index. Heartbeats duplicados e workers concorrentes não geram segundo ticket lógico.
- Vincular PrintJob inicial aos snapshots imutáveis e bindings, sem misturar BAR e KITCHEN. Falha do spool/printer mantém Order válida e gera alerta operacional. Tratamento separado de `ACK_SPOOL`, `DELIVERY_UNCERTAIN` e `PAPER_CONFIRMED`: ACK do SO não significa impressão física.
- Reimpressão manual continua outro fluxo, com marca `REIMPRESSÃO`, autorização, ator, motivo e audit.
- **Aceite:** 015-009; 100 checks repetidos/2 workers → exatamente 1 ticket inicial lógico, sem pedido/OrderItem adicional; fallbacks por estação corretos; printer offline não desfaz Order.

### D3 — Ativação controlada e hardware (terceiro PR/gate externo)
- Gerência: modo desabilitado por padrão, condição que levou ao fallback, job/erros, reimpressão/manual override e procedimento para evitar duas vias no retorno do KDS.
- Checklist físico no Aderlan: marca/modelo, driver, SO, rede/CUPS/USB, largura 58/80 mm, acentuação e codepage, corte, status, alimentação e papel **na cozinha e bar**; fotos/logs sanitizados e aceite operador.
- **Aceite:** 015-010 permanece EXTERNAL_BLOCKED até impressão física realizada; sem hardware, declarar somente qualidade de simulação, não operação certificada.

**Não fazer:** impressão automática na primeira oscilação de rede, confundir pedido confirmado com cesta local, duplicar ticket inicial em cada poll, afirmar papel entregue pela confirmação do bridge.

## Ordem de execução e divisão entre quatro agentes

| Etapa | Agente A — Offline | Agente B — Config | Agente C — Close | Agente D — Print |
|---|---|---|---|---|
| Gate 0 | Validar status #71/#72 e `origin/main`; fixar contratos partilhados | Igual | Igual; esperar #71 para mexer em Caixa Web | Igual |
| Slice 1, paralelo | A1: intent e replay de Order | B1: station preview/apply | C1: daily close persistido | D1: heartbeat KDS |
| Slice 2, após contratos | A2: cash/terminal evidence + manager review | B2: global guest block/policy | C2: post-close correction | D2: AUTO_FALLBACK deduped |
| Slice 3, integração | A3: falha real + métricas | B3: policy effective-date/provedor | C3: UI gerencial/timeline | D3: toggles e física |
| Gate final | Android process death e API/SSE loss | Estação ativa + dois gerentes | Fechamento/estorno multi-caixa | KDS flaps + print uncertainty |

**Isolamento de arquivos:** A é dono do Android/recovery e contrato de reconciliação; B das configurações/stations/guest-switch; C de DailyClose/financeiro gerencial; D da impressão/heartbeat. Mudanças em `venue/models.py`, `management/views.py`, `urls.py` e `cash/services.py` precisam de contrato acordado e integração sequencial (não editar simultaneamente nas quatro worktrees). D consome a API de station config de B em integração, sem bloquear D1/D2 de prosseguir com interface temporária tipada. A e C compartilham política financeira de recuperação: A não fecha DailyClose; C não executa replay offline.

### Critério de saída antes de liberar um turno supervisionado
1. CI dos PRs integrados verde no SHA da `main`; migrations limpas e restores testados num banco isolado.
2. API/PostgreSQL/Android/Web: repetir turno de duas estações com mesa QR, atendimento, pedido, preparo/entrega, pagamento manual de teste, estorno, fechamento de caixa e DailyClose.
3. Injetar: timeout **após commit** de pedido, kill/restart Android, revogação do operador, objeto offline conflictante, SSE fora/API saudável, API fora/SSE reconnectando; demonstrar **zero pedidos/recebimentos duplicados**.
4. Desativação da KITCHEN única com fila deve gerar bloqueio sem órfãos; gerente vê motivo. Dois gerentes em concorrência nunca sobrescrevem alteração de versão.
5. KDS unhealthy sustentado gera **um** PrintJob lógico inicial; oscillação não cria novos; printer offline não reverte venda. Sem hardware, manter AUTO_FALLBACK OFF na demo pública.
6. Caixa de R$ 50 offline para Tab com R$ 30 restante vira review, não pagamento automático; close incompleto não aparece reconciliado; correção preserva snapshot.
7. Atualizar matriz AC por AC com `PASS`/`PARTIAL`/`MISSING`/`EXTERNAL_BLOCKED`, SHA/ambiente/log; registrar lacunas externas explicitamente.
8. Só depois avaliar uma nova imagem/deploy Railway em ambiente **isolado de produção**, com migração/seed verificadas, backup/restauração e rollback. O deploy existente não é automaticamente atualizado por merge.

## Decisões e exclusões explícitas

- **Escopo da release supervisionada:** operações canônicas, impressão manual/contingência observada e pagamentos simulados/manuais de teste; sem ativar Paytime/SumUp/Tap, sem alegar homologação fiscal ou de impressora.
- **Não confundir escopo:** concluir estes quatro pacotes P0 **não** encerra todas as Specs 007, 013, 014 e 015: métricas mensais, floorplan, push real, hardware e providers permanecem com critérios específicos.
- **Bloqueador externo:** obter disponibilidade efetiva de celular BYOD e impressora do Aderlan e autorização/credenciais de PSP antes de qualquer gate que dependa disso.
- **Done = aceites verificados, não checkbox marcado.** Se um pacote mudar comportamento financeiro ou de configuração crítica, exigir revisor independente e teste de rollback/reconciliação.
