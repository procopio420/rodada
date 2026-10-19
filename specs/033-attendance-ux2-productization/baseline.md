# E06-01 — inventário real de implementação

Base: `origin/main@dcb3a79590904a2c289641d285eda639e1713c87`, 16/10/2026.
Contrato copiado sem depender de merge da PR216: `619c27182a0dc73f489514f127006511b99d2c0b`.
Worktree isolada `ux2-033`, branch `impl/033-e06-audit`. Sem `.codegraph/`.
Auditoria por inspeção independente de API, Android e contratos; Web pelo integrador.
**EXISTENTE significa código/testes encontrados, não PASS executado neste SHA.**
Nenhum AC novo aprovado nesta fotografia. IDs abaixo são dos arquivos `epics/*/tasks.md`;
o tasks.md agregado usa IDs divergentes e não deve ser usado sozinho para aceite.

## Matriz de reuso e delta

Paths API relativos a `apps/api/`; Android a `apps/attendance-android/app/src/`.

| Epic → Task | Status atual | Arquivos existentes | Delta necessário | Testes reutilizáveis | Dependências |
|---|---|---|---|---|---|
| E01 → 01 | Inventário por inspeção | attendance-web.tsx; AttendanceScreen.kt; TablesScreen.kt | Comparativo de jornada/pixels ainda não executado | attendance-mobile-design.spec.ts; NativeAttendanceFlowTest | E06 visual |
| E01 → 02 | Parcial | TableTabSelection; ServiceRequest.kt; dispatch/models.py | Destino typed staff-safe; snapshot Tab do chamado sem inferir por label | test_service_requests_round2.py; test_tab_location_safety.py | E03 DTO/R3 |
| E01 → 03 | Parcial | apps/web/components/attendance-web.tsx | Agora inicial; + Pedir central; preservar workspace montado | attendance-mobile-design.spec.ts; attendance-draft.spec.ts | Seleção existente |
| E01 → 04 | Existente parcialmente | order-workspace.tsx; TablesScreen.kt | Reusar diálogos/multi-Tab/balcão; seletor central Web | attendance-dialogs.spec.ts; TableServiceNavigationTest | E01-03 |
| E01 → 05 | Existente parcialmente | ui/AttendanceNavigation.kt; AttendanceScreen.kt | Entrada NOW; preservar Back e drafts | AttendanceNavigationTest; NativeDraftReadbackTest | DTO para deep links |
| E01 → 06 | Falta origem task | TableTabSelection; TabDraftContexts.kt | Retorno ao chamado/conta/delivery, validação de destino | OrderDestinationTest; OrderWorkspaceTest | E03 |
| E01 → 07 | Testes base existentes | suites Web visual/integration e Android | Acrescentar negativos dos novos destinos | TabDraftContextsTest; attendance-mobile-design.spec.ts | API/projeção |
| E01 → 08 | Gate pendente | infraestrutura visual/Compose | Capturas, CI e revisão | suites acima | E06 |
| E02 → 01 | Recovery existente | lib/client/order-intent.ts; PendingMutationIntentStore.kt | Revalidar baseline, não criar motor novo | order-intent.spec.ts; ForceStopOrderRecoveryTest | PostgreSQL/emulador |
| E02 → 02 | Parcial | ordering/views.py; HistoricalOrder; OperationsHttpClient.kt | Transportar/renderizar station snapshot e referência real | test_ordering.py; HouseAccountContractTest | Contrato canônico |
| E02 → 03 | Parcial | order-workspace.tsx; AttendanceScreen.kt | Confirmação persistente compacta com ID/itens/estação | attendance-history.spec.ts | E02-02 |
| E02 → 04 | Falta envio direto | AttendanceCategoryCatalog; CategoryCatalog | Enviar pelo catálogo via mesma intenção; resumo opcional | attendance-catalog.spec.ts; CategoryCatalogTest | Atualizar diretriz de revisão |
| E02 → 05 | Existente | repeat-order.tsx; RepeatOrderDialog.kt | Reusar seleção/quantidade e envio direto, validar | repeat-order tests; RepeatOrderTest | Sem nova engine |
| E02 → 06 | Existente | useOrderIntent, draft storage | Revalidar refresh/4xx/sessão/Tab | integration/order-intent.spec.ts | Infra #106 |
| E02 → 07 | Existente | OrderRecoveryPolicy.kt; ViewModel | Ajustar somente gaps comprovados | SessionBoundRecoveryIntentTest; LivePostDropReconciliationTest | Emulador |
| E02 → 08 | Existente | use-realtime.ts; Android realtime | Consumir projeções e validar fallback | realtime tests; #106 resilience | Snapshot canônico |
| E02 → 09 | Infra existente | API/Playwright/androidTest | Rodar cenários novos e herdados relevantes | #106 cross-surface/lost ACK | DB descartável |
| E02 → 10 | Gate pendente | protocolo R3 | Reviewer independente e CI | Revisão por SHA | E06 |
| E03 → 01 | Inventariado | dispatch/views.py; service-request-queue.tsx; ServiceRequest.kt | Não recriar filas existentes | test_dispatch.py; test_service_requests_round2.py | — |
| E03 → 02 | Falta identidade de chamado | DispatchTask; serializers.py | FK nullable requested_tab para novos chamados; DTO aditivo seguro | testes service requests | Migration sem backfill heurístico |
| E03 → 03 | Permissões existentes/parcial | views Venue-scoped; guest services | Negativos geração/release/movimento/revogação e delivery CLOSED | test_access_permissions.py; test_tab_location_safety.py | E03-02/R3 |
| E03 → 04 | Parcial Web | ServiceRequestQueue; AttendanceWeb deliveries | Separação/freshness independente, abrir destino sem mutar | attendance.spec.ts; integration/service-requests.spec.ts | E03-02 |
| E03 → 05 | Parcial Compose | NowQueues; ServiceRequest.kt | Deep links Tab/conta/item e volta | NowQueuesTest; ServiceRequestTest | E03-02 |
| E03 → 06 | Mutations existentes | update_service_request; complete_delivery_task | Reusar claim/complete/exceções explícitos | test_dispatch.py; RecoveryContextApiTest | Nenhum tap extra obrigatório |
| E03 → 07 | Parcial | filas limitadas a200; polling/SSE | Isolar falha Dispatch de venda e provar50+50 | #106 resilience | E06 pico |
| E03 → 08 | Gate pendente | Infra existente | PostgreSQL/clients/visual/review | suites acima | E06 |
| E04 → 01 | Backend e Android existentes | ledger/services.py; hospitality/services.py; PaymentDialog | Web companion atualmente exclui pagamentos | test_ledger_payments.py; PaymentsTest | Reconciliação024 abaixo |
| E04 → 02 | Existente/parcial | BillSummary; TabDetailView; BalanceCard | Reorganização compacta e histórico | attendance-history.spec.ts; MonetaryFieldsTest | Sem novo ledger |
| E04 → 03 | Backend/Android existentes; Web falta | collect_payment; PosCashReceipt | Integrar recebimento autorizado Web e reusar intent/readback | test_payments_concurrency.py; cash recovery | BFF/R3 |
| E04 → 04 | Sequência falta | collect_payment; close_tab; ViewModel | Payment confirmado/readback → close recuperável; nunca recobrar | payment/recovery tests | R3/restart |
| E04 → 05 | Close zero existente | TabCloseView; BalanceCard | Reduzir revisão e melhorar readback/retorno | NativeAttendanceFlowTest | Capability PAYMENT_COLLECT |
| E04 → 06 | Ciclo existente | release_table/start_cleaning/complete_cleaning; TablesScreen | Preservar close separado de release; caminho CLEANING explícito | test_hospitality_tables.py; test_guest_access.py | Reconciliação004/029 abaixo |
| E04 → 07 | Cobertura forte existente | locks/versions/idempotency/fingerprint | Regressões da sequência nova | test_payments_concurrency.py; test_tab_operations.py | PostgreSQL |
| E04 → 08 | Infra existente | #106 suites | Executar integrações alteradas | cross-surface E2E01..14 | PSP real externo |
| E04 → 09 | Gate pendente | protocolo R3 | Revisão financeira independente | CI+readback/SQL | E06 |
| E05 → 01 | DTO suficiente existente | house_account/services.py financial_position | Reusar snapshots/limite/exposição/capacidade | test_house_account.py | Spec002 |
| E05 → 02 | Barra falta | BillSummary; BalanceCard | Barra80% + draft distinto + excesso/zero textual | novos testes UI | Sem mudar policy |
| E05 → 03 | ENFORCE existente | ordering/services.py confirm_order | Preservar enforcement; sem toggle local | test_house_account.py | Spec031 não integrada |
| E05 → 04 | Recovery existente/parcial | LimitResolutionDialog | Preservar draft, pagamento/gerência legítimos | HouseAccountContractTest | WARN_ONLY bloqueado031 |
| E05 → 05 | BLOQUEADO externo | PR215 contrato apenas | Integrar modo/version depois do backend031 | Futuros testes031 | Não implementar policy paralela |
| E05 → 06 | Gate UI pendente | Infra visual/Compose | 0/79/80/99/100/120%, fonte ampliada | novos UI tests | E05-02 |
| E05 → 07 | Invariantes existentes/gate pendente | snapshots/associate_customer/reassess_tab | Validar UI sem garantia fictícia | test_house_account.py | AC18 depende031 |
| E06 → 01 | Inspeção concluída; execução baseline pendente | Este documento | Capturas/medição e evidência executada |026/029/#106 | Não declarar PASS |
| E06 → 02 | Fixture existente | #106 permanent runner | Expandir só cenários faltantes | scripts e cross-surface | Dois Venues descartáveis |
| E06 → 03 | Infra existente/gate pendente | cross-surface + Android instrumentado | Rodar jornada com mudanças033 | #106 E2E01..14 | E01–05 |
| E06 → 04 | Infra existente/gate pendente | android-live-post-drop workflow | Rodar lostACK/restart/revocation | ForceStop/LivePostDrop tests | Emulador/PostgreSQL |
| E06 → 05 | Infra existente/gate pendente | Playwright/Compose |360/390/430/desktop/font2/TalkBack | visual + androidTest | Aparelho físico indisponível |
| E06 → 06 | Falta prova nova pico | Queue limits200 |20 mesas/50+50 tasks, latency sem inferir métricas | fixtures carga | E03 |
| E06 → 07 | Parcial eventos domínio | AuditEvent/fulfillment milestones | Medir fricção/erro sem taps instrumentais | SQL/evidence runner | Retenção/provenance |
| E06 → 08 | Gate pendente | CODE-REVIEW/qualified-agent | Contexto independente e gate GitHub por SHA | CI/Review | Não simular aprovação |
| E06 → 09 | BLOQUEADO humano | onsite acceptance | Operador/piloto físico | roteiro de homologação | Autorização operacional |
| E06 → 10 | Preparação executável; ativação bloqueada | frontend gating existente a inventariar | Flag Venue/role/rollback apresentação | testes de flag | Sem merge/deploy autorizado |

## Contratos reconciliados para execução

- PR212 `ec26e26b`: protótipo isolado, sem evidência operacional; PR213 `bbc8deaa`/issue214 OPEN são Spec032/QR híbrido, fora deste rollout.
- PR215 `400c2a16`: contrato Spec031, não backend. Não alterar enforcement, não implementar WARN_ONLY no cliente.
- Spec024 companion proibia pagamentos; a missão atual autoriza explicitamente o novo fluxo033E04. Atualizar contrato024 e BFF no slice financeiro com R3, sem ativar PSP fictício.
- Specs004/029 permitem limpeza direta DIRTY→AVAILABLE desde15/10. A missão atual pede DIRTY→CLEANING→AVAILABLE: usar as duas operações reais existentes, sem fabricar início por conveniência; atualizar contratos/testes no slice proprietário. Preservar compatibilidade dos endpoints legados.
- Design system exige revisão integral obrigatória;033 autoriza envio direto com resumo opcional e026T08e já envia repetição diretamente. Atualizar diretriz no slice de envio; não criar segunda revisão.
-026 já entrega drafts A/B/A, recuperação staff/guest, CASH/refund e repetir rodada;029 já entrega popup mesa/comanda e catálogo por categorias nativo/Web. Nenhum desses motores é trabalho novo.

## Evidência histórica e limites

Issue106 CLOSED em consulta16/10, atualizada07:32UTC. Suíte automatizada histórica em `a24cd6bf`, squash `475acadd` com mesma tree. Há waiver do responsável para revisão final, **não aprovação independente nova**. Reusar infraestrutura permanente, não herdar PASS para HEAD033.
Specs026/029 têm relatórios por SHA; evidência histórica não prova esta branch.
Nenhum aparelho adb conectado; AVDs36/37 disponíveis. Aparelho físico/PSP/fiscal permanecem externos.

## Primeiros deltas funcionais

1. E01 Web/Compose: Agora inicial e +Pedir Web usando seleção/workspace existentes.
2. E03 API: snapshot requested_tab + destino seguro aditivo, base para deep links.
3. E02: status canônico e envio direto, preservando useOrderIntent/Keystore.

Todos AC01..24 permanecem PENDING até execução e revisão por SHA. Não confundir
inspeção, código, testes sintéticos, integração real e homologação no bar.

## Reconciliação da fila — 2026-10-19

Snapshot de integração: `main@20828711208ec3e991d5dca8808b37eacd07c81f`;
PR #253 em validação no SHA `aff4fffc9e350626bb051939423f015d79ea265e`.
Este PR #217 preserva os requisitos do #216 e acrescenta inventário/paridade.
Os snapshots e resultados anteriores são históricos e não representam a fila atual.
O #253 exige contexto original de ocupação na liberação em API/Web/Android;
os gates remotos e o merge ainda não estavam concluídos nesta anotação.
As reconciliações de implementação UX2 seguem separadas. Não marcar AC global,
homologação de aparelho, piloto ou produção como PASS por integração documental.
