# Spec 033 / E06 — encerramento da auditoria #272, corte de 22/10/2026

**Objeto deste arquivo:** encerrar o trabalho de *inventariar, reconciliar e distribuir evidências* solicitado em [#272](https://github.com/procopio420/rodada/issues/272). **Não significa aceite da Spec 033 inteira, aprovação de segurança independente ou GO em produção.** O gate global de `acceptance.md` permanece PENDING.

## Snapshot e provas verificadas

Baseline de `main` da auditoria: `48d5ba7a5320129e2733a8a457e10bfad6a5ecdc` (merge do PR #312). Houve outros merges desde as evidências históricas de 20–21/10; prevalecem as provas mais recentes **no exato SHA de cada candidato**, sem transferir automaticamente seu PASS para builds distintos.

| Evidência | Commit/candidato | Resultado confirmado | Limite |
| --- | --- | --- | --- |
| [PR #294](https://github.com/procopio420/rodada/pull/294) rehearsal com IDs financeiros | `a3b42fd68f9f7aa77b11cc3e03844df0f74d2856` | API PostgreSQL / recibo canônico de três Tabs, pedidos, Payments e ocupações | Não é Web/Android físico |
| [PR #300](https://github.com/procopio420/rodada/pull/300) recuperação após commit | `a6130ee2559ff5efd3081bc77f293bdaa389778a` | [Web SUCCESS](https://github.com/procopio420/rodada/actions/runs/39691762284) e [Android POST-disconnect SUCCESS](https://github.com/procopio420/rodada/actions/runs/39691762276) | Não significa corte de uplink físico |
| [PR #301](https://github.com/procopio420/rodada/pull/301) teclado/fonte | `f4522e7a14c060c5bb4d2d542c0159574d522cf1` | [Web SUCCESS](https://github.com/procopio420/rodada/actions/runs/39711338305) | Não é TalkBack/aparelho |
| [PR #302](https://github.com/procopio420/rodada/pull/302) cutoff/tenant | `8e22101192cb3ec9f4f2e497d450cb7e5a0c3268` | [API SUCCESS](https://github.com/procopio420/rodada/actions/runs/39711618844), [Web SUCCESS](https://github.com/procopio420/rodada/actions/runs/39711618859) | Testes do candidato |
| [PR #311](https://github.com/procopio420/rodada/pull/311) intenção, recuperação, passos observados | `2fb6bb527a444519e81948dcb2eb0f8d0a5501c1` | [API](https://github.com/procopio420/rodada/actions/runs/39872456726), [Web](https://github.com/procopio420/rodada/actions/runs/39872456769), [Android](https://github.com/procopio420/rodada/actions/runs/39872456738): SUCCESS | Passos do carrinho, não jornada de navegação total |
| [PR #312](https://github.com/procopio420/rodada/pull/312) screen receipt Bar/Cozinha | `1e15b8bfa3712f9af804b9432f8c70753ed1bec1` | [API SUCCESS](https://github.com/procopio420/rodada/actions/runs/39882786496): 1085 testes PG; [Web SUCCESS](https://github.com/procopio420/rodada/actions/runs/39882786511): BFF/Chromium | Viewport reportado pelo browser, não atenção humana |
| Integração da `main` após #312 | `48d5ba7a5320129e2733a8a457e10bfad6a5ecdc` | Squash confirmado; workflows push [API](https://github.com/procopio420/rodada/actions/runs/39884641863), [Web](https://github.com/procopio420/rodada/actions/runs/39884641751) **em andamento na consulta inicial** | Não registrar PASS terminal da main antes de consultar seu resultado |

PRs #303–#310 também estão mergeados na `main`; implementam API agregada, autenticação e telemetria passiva sem mudar ledger nem a política de UX (UX 2.0 é o padrão; sem flag de versão antiga).

## Rastreabilidade AC-01..24

**Classificação:** `SLICE_PASS` = pelo menos uma prova automatizada real em recorte específico; `GLOBAL_PENDING` = critério inteiro não comprovado. Não interpretar `SLICE_PASS` como caixa concluída.

| AC | Recorte existente e prova rastreável | Estado global / próximo ticket |
| --- | --- | --- |
| 01 | Targets canônicos QR/Tab; testes Web/Android e isolamento históricos no inventário E06 | GLOBAL_PENDING: composição final cross-surface [#315](https://github.com/procopio420/rodada/issues/315) |
| 02 | Drafts A→B→A, mesas, Back/foco com testes Web/Compose existentes | GLOBAL_PENDING: candidato conjunto #315; físico #316 |
| 03 | Revogação, Venue, occupancy/epoch e fallback testados em recortes | GLOBAL_PENDING: #315 |
| 04 | Pedido direto, OrderId real e estação/readback Web/Android | GLOBAL_PENDING: #315 |
| 05 | Perda de ACK/commit/replay Web+Android; #300 SUCCESS | GLOBAL_PENDING: #315 |
| 06 | Repetir rodada e revalidação canônica por testes de pedido | GLOBAL_PENDING: modificadores e fluxo final #315 |
| 07 | Limites/erros definitivos, concorrência e replay em API PG e clientes | GLOBAL_PENDING: #315 |
| 08 | Filas Agora distintas e cenário pico 50 Web já testado | GLOBAL_PENDING: nativo/pico final #315/#316 |
| 09 | Serviço/conta navegam à Tab canônica sem claim automático | GLOBAL_PENDING: #315 |
| 10 | READY com provenance e fluxo de entrega por ID | GLOBAL_PENDING: #315 |
| 11 | Claim concorrente, sessão antiga, rede e tela de Dispatch | GLOBAL_PENDING: #315 |
| 12 | Saldo, parciais e recibos confirmados, sem draft financeiro | GLOBAL_PENDING: #315 |
| 13 | Payment canônico/retry/zero-close; rehearsal #294, Web/Android #300 | GLOBAL_PENDING: #315; PSP real não homologado |
| 14 | Três Tabs na mesma mesa; CLOSED sem liberação automática (#294) | SLICE_PASS API; GLOBAL_PENDING: #315 |
| 15 | Revogação Guest, giro DIRTY/CLEANING/AVAILABLE e nova geração (#294) | SLICE_PASS API; GLOBAL_PENDING: #315 |
| 16 | CashShift, permissões e ledger, testes PG concorrentes | GLOBAL_PENDING: #315/#317 |
| 17 | Barra de limite e estados/fronteiras/fonte em Web/Android | GLOBAL_PENDING: #316 e matriz de #315 |
| 18 | Política efetiva WARN_ONLY/ENFORCE por Venue na API e clientes (Spec031) | SLICE_PASS backend/Web; GLOBAL_PENDING: #315 |
| 19 | Sem garantia PSP fictícia, CAS/override auditado pelo servidor | GLOBAL_PENDING: #315/#317 |
| 20 | Rehearsal #294 + BFF PG + Android CI em candidatos verificáveis | GLOBAL_PENDING: integrar no mesmo candidato #315 |
| 21 | Web restart/retry e Android força-parada/POST disconnect (#300/#311) | GLOBAL_PENDING: cortes adversos finais #315 |
| 22 | Web fonte/teclado #301 e testes visuais parciais | GLOBAL_PENDING: físico/TalkBack #316 |
| 23 | Telemetria agregada v2 #311 e viewport receipt servidor #312; erro/recuperação e cobertura `missing` | SLICE_PASS técnico; GLOBAL_PENDING: coleta operacional e retenção agendada #318 |
| 24 | CIs e protocolo R3 documentados, UX2 padrão sem flag legada | GLOBAL_PENDING: R3 autenticado e rollback #317; aceite de piloto #318 |

## Revisão autorizada neste chat — SELF_REVIEW de riscos R3

**Base revisada:** `main@48d5ba7`, arquivos `apps/api/modules/management/{telemetry,production_screen,attendance_metrics}.py`, `apps/web/lib/server/auth-gateway.ts`, `apps/web/components/production-board.tsx`, `docs/agents/CODE-REVIEW.md` e testes dos PRs #311–#312. **Não é contexto independente nem aprovação autenticada de GitHub.** Classificação máxima R3 porque o diff abrange auth/tenant/PII/migração e recuperação de intenção.

- **P0/P1 comprovados nesta inspeção documental:** nenhum achado reproduzível novo; isto **não prova** ausência de falhas no produto inteiro.
- **P2 / integridade de métrica:** `ProductionScreenObservationView` exige sessão staff autenticada e Venue correto, mas não uma prova criptográfica de visualização. Um cliente staff malicioso pode tentar reportar IDs canônicos sem exibir o ticket; o dado representa **telemetria de viewport informada pelo cliente**, não atenção humana. Reavaliar permissões/proveniência no R3 independente [#317](https://github.com/procopio420/rodada/issues/317).
- **P2 / cobertura de telemetria:** `production-board.tsx` marca cada ID como enviado antes da confirmação HTTP e não força retry em falha transitória para não impactar a operação; report pode apresentar `missing` (não zero). Validar perda/confiabilidade no piloto [#318](https://github.com/procopio420/rodada/issues/318).
- **Bloqueio operacional de retenção:** o comando `prune_attendance_telemetry` remove receipts temporários, mas execução agendada não foi verificada. **Não afirmar retenção efetiva de 7 dias em ambiente operacional** até #318.
- **R3 independente:** `.github/workflows/chatgpt-r3-review.yml` depende da variável `RODADA_R3_AGENT_ENABLED` e credenciais de App qualificado; workflows posteriores ao PR #312 ficaram `skipped`. É **REVIEW_BLOCKED** até evidência autenticada, acompanhado em #317.
- **Sem prova física/release:** foco, TalkBack, operador, PSP, rollback e deploy de produção não foram executados nesta auditoria. Não confundir PASS em Chromium/emulador/PG com GO.

Resultado desta SELF_REVIEW: `NO_FINDINGS_WITH_GAPS` no material examinado; gate **R3 independente = REVIEW_BLOCKED**, global **NO-GO**.

## Transferência explícita dos gates externos

- [#315](https://github.com/procopio420/rodada/issues/315): AC-01..21, mesmo candidato Web+Android+Guest+Bar/Cozinha+Caixa, recovery/revocações.
- [#316](https://github.com/procopio420/rodada/issues/316): AC-22 e validação física de foco, TalkBack e toque.
- [#317](https://github.com/procopio420/rodada/issues/317): AC-24 revisão R3 independente, segurança, branch protection e rollback técnico.
- [#318](https://github.com/procopio420/rodada/issues/318): AC-23 em operação, agenda de retenção, piloto e decisão GO/NO-GO.

**Política de encerramento:** #272 pode ser fechada como **auditoria de evidências e reconciliação de trabalho concluída, pendências transferidas**, mas `acceptance.md` continua integralmente PENDING. Nenhuma caixa de AC deve virar PASS por transferência de issue. O tracker global de release passa a ser [#315–318], com GO condicionado a TODOS os gates aplicáveis.
