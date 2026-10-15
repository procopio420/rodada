# #106 — matriz verificável de execução

Execução local integrada **TESTED** no SHA `899255b1406fc3fe51ace2977c7789fc65cf68d0`,
15/10/2026, pacote `artifacts/runs/899255b1406f-20261015T221922Z` na worktree
`issue106-ci-package`. Android Compose real em emulador API36/KVM, Chromium,
Next/BFF, Django e um PostgreSQL17 descartável compartilhado. Nenhuma prova foi
importada de outro SHA/cluster. **14 PASS / 0 FAIL / 0 SKIP / 0 BLOCKED** em cenários;
a decisão global exige também invariantes e revisão independente do pacote.
O validador retornou **GO automatizado, errors=[]**, após a [R3 independente](https://github.com/procopio420/rodada/issues/106#issuecomment-6203562103).
Essa revisão local em contexto separado não é aprovação GitHub.

O pacote anterior a9cf6007 chegou aos 14 PASS mas falhou no SQL agregado por exigir
`revoked_at`, enquanto o contrato Guest invalida por geração/ocupação. A falha
foi preservada. 899255b1 verifica geração antiga, ocupação liberada,403 real e
nova sessão válida. bff3fc31 falhou antes por expectativa incorreta de movimento
zero; o serviço não cria OPENING_FLOAT quando o fundo é zero. Não houve mudança
de produto para acomodar esses asserts.

## Tarefas A–F

`TESTED` significa execução local real no SHA acima, com receipts correlacionados;
`CI_PENDING` exige confirmação do workflow correspondente. Gates físicos continuam
separados, sem transformar automação em aceite presencial.

| Tarefa | Estado | Prova/escopo |
|---|---|---|
| A1 | RECONCILIADO | Inventário reconciliado; fundações #185 e contrato #186 preservados sem diff incidental. |
| A2 | TESTED | QR-first, claim Web, mesma ocupação/geração e auditoria; claim sem ledger. |
| A3 | TESTED | Duas Tabs Guest/Web na mesma ocupação, pedidos/saldos separados; ambas lidas no Compose; Tab standalone nativa. |
| A4 | TESTED | Última Tab fechada não libera; release explícito, DIRTY/CLEANING/AVAILABLE e novo ciclo com mesmo QR. |
| A5 | TESTED | 403 da GuestSession antiga; nova visita/geração válida, sem Order/Charge indevido. |
| A6 | TESTED | qr-lifecycle-sql, browser-origins-sql e android-context-readback-sql. |
| B1 | RECONCILIADO | Harness #127 reaproveitado; HTTP/storage distinguido da confirmação Compose. |
| B2 | TESTED | Fixture única, cluster hash, Venue/produtos BAR 700 / KITCHEN 1000 e múltiplos atores. |
| B3 | TESTED | Pedidos confirmados pela UI Compose, Atendimento Web e Guest; IDs correlacionados. |
| B4 | TESTED | NEW→PREPARING→READY por UI explícita nas estações; Guest mostra Pronto/chegando. |
| B5 | TESTED | Android lê ambas Tabs prontas; Atendimento/Gerência mostram 7 DispatchTasks; OPEN sem conclusão ou provenance inventada. |
| B6 | TESTED | Carrinhos stale Guest/Web/Compose negados com 409; offline ACTION_REQUIRED e pedidos anteriores preservados. |
| B7 | TESTED | SQL final: 5 Orders / 8 Items / 8 Charges, 6800 centavos; estações/centavos/quantidades e zero pagamento por preparo. |
| C1 | RECONCILIADO | Inventário cash/ledger/concurrency existente reutilizado. |
| C2 | TESTED | Somente CASH de teste e PENDING controlado sem PSP, PostgreSQL descartável. |
| C3 | TESTED | Parcial de 300, refund de 100 e residual de 1500 centavos; resposta perdida e replay com mesmo Payment ID; demais Tabs sem pagamento. |
| C4 | TESTED | Fechamento com saldo retorna 409; PENDING sem confirmação bloqueia, sem CashMovement/PaymentAttempt. |
| C5 | TESTED | Abertura 10000 / suprimento 2000 / sangria 1000; esperado 12700 / contado 11700 / divergência -1000 centavos revisada; STAFF/CASHIER recebem 403; cutoff nos dois lados. |
| C6 | TESTED | Refund compensatório de 100 centavos preserva Payment/Charge, confirmação e auditoria. |
| C7 | TESTED | financial-sql/cash-cutoff-sql/financial-roles-sql/final-state-sql; recebido 1800 − refund 100, exposição 5100 centavos. |
| D1 | RECONCILIADO | Auditoria #130 reutilizada; controles limitados à jornada local #106. |
| D2 | TESTED | start/start simultâneo com barreira/conexões PostgreSQL; uma ocupação/owner. |
| D3 | TESTED | claim com CAS e release/open atômicos; auditoria única, sem Tab órfã/ledger. |
| D4 | TESTED | Double tap Compose; perda de resposta/replay nativo e Guest; key/body idênticos e divergência retorna 409. |
| D5 | TESTED | Revogação Web/nativa GET/POST/refresh/SSE; expiração 401 → refresh 200; intenção antiga exige revisão após novo login. |
| D6 | TESTED | A/B próprio 200 / cruzado 404; Guest selectors/produtos negados; Host local assinado no BFF e Android direto negado. Não certifica ingress externo #130. |
| D7 | TESTED | Receipts, instrumentation e SQL negativo: ausência de efeitos após 403/409/timeouts. |
| E1 | RECONCILIADO | RST, uplink do emulador e Wi-Fi físico separados; histórico CI documentado. |
| E2 | TESTED | POST commitado / resposta perdida/force-stop/offline/replay; Order 1 / Item 1 / Charge 1 / Payment 0. |
| E3 | TESTED | Mesmo Order recuperado → Bar READY; Compose contextual pós READY sem novo comando. |
| E4 | TESTED | Somente SSE interrompido, HTTP saudável/polling/cursor retomado, item NEW único sem preparar sozinho. |
| E5 | TESTED | Cozinha offline durante commits Guest/Web, recuperação NEW por snapshot e ações explícitas. |
| E6 | TESTED | Offline PENDING → catálogo alterado → ACTION_REQUIRED; revogação e comando dependente bloqueado, histórico preservado. |
| E7 | TESTED | Logs nativos/PIDs/interface, receipts SQL e 15 traces sanitizados; nenhum aceite de Wi-Fi físico inferido. |
| F1 | RECONCILIADO | Gatilhos CI / filtros de paths e dispatch manual inventariados; proteção/autodeploy externo não inferidos. |
| F2 | TESTED | Runner/fixture únicos, guards de DB e hash do cluster; execução completa local 899255b1. |
| F3 | CI_PENDING | Smokes seletivos e gate pesado por paths; KB/Web e CI Android por SHA, sem ruleset alterado. |
| F4 | CI_PENDING | Workflow manual A–E com upload always, exit real e corte de uplink separado; CI final pendente. |
| F5 | TESTED | Schema/validador/manifest de 14 casos, versões reais, IDs / hashes de artefatos, SQL final e source_sha256. |
| F6 | TESTED | Esta matriz e manifest por cenário; históricos FAIL preservados sem promover novo HEAD. |
| F7 | TESTED | Gate automatizado exige 14 PASS / 10 invariantes / review; físico / PSP/fiscal separado. |
| F8 | TESTED | R3 independente por slices/contexto; inspeção sanitização/IDs/pacote final e KB. |

## E2E-01..14

Todos os cenários abaixo usam o SHA/cluster da execução citada, com traces de UI,
instrumentação nativa quando aplicável e SQL independente. O manifesto contém
IDs completos, tempos, versões, hashes e referências por cenário.

| Cenário | Execução | Tarefas | SQL correlacionado |
|---|---|---|---|
| E2E-01 | PASS | A2, A5, A6 | `qr-lifecycle-sql.json`, `final-state-sql.json` |
| E2E-02 | PASS | A3, A6 | `browser-origins-sql.json`, `android-context-readback-sql.json`, `final-state-sql.json` |
| E2E-03 | PASS | B2, B3, B7 | `browser-origins-sql.json`, `android-compose-web-sql.json`, `final-state-sql.json` |
| E2E-04 | PASS | B4, B5, B7 | `browser-origins-sql.json`, `android-compose-web-sql.json`, `android-context-readback-sql.json`, `projection-sql.json`, `final-state-sql.json` |
| E2E-05 | PASS | B6, B7 | `unavailable-cart-sql.json`, `unavailable-staff-sql.json`, `android-catalog-sql.json`, `android-offline-conflict-sql.json`, `final-state-sql.json` |
| E2E-06 | PASS | C3, C7 | `financial-sql.json`, `final-state-sql.json` |
| E2E-07 | PASS | C5, C7 | `financial-sql.json`, `financial-roles-sql.json`, `cash-cutoff-sql.json`, `final-state-sql.json` |
| E2E-08 | PASS | D2, D3, D7 | `concurrency-sql.json`, `final-state-sql.json` |
| E2E-09 | PASS | D4, D7 | `browser-origins-sql.json`, `android-web-cross-surface.json`, `final-state-sql.json` |
| E2E-10 | PASS | D5, D6, D7 | `revocation-sql.json`, `isolation-sql.json`, `guest-isolation-sql.json`, `android-offline-revocation-sql.json`, `final-state-sql.json` |
| E2E-11 | PASS | E2, E3, E7 | `android-web-cross-surface.json`, `final-state-sql.json` |
| E2E-12 | PASS | E4, E5, E7 | `sse-sql.json`, `browser-origins-sql.json`, `final-state-sql.json` |
| E2E-13 | PASS | A4, A5, A6 | `qr-lifecycle-sql.json`, `final-state-sql.json` |
| E2E-14 | PASS | C4, C6, C7 | `pending-payment-sql.json`, `financial-sql.json`, `final-state-sql.json` |

## Estado de integração e gates

PRs196→197→198→199→200→201→202 são slices empilhados; não foram mergeados por
esta execução. PRs191–193 foram integrados externamente. PR185 integrado e186
fechado; somente o contrato legítimo de186 foi reaproveitado. main observado:
2fc02bf7. Revalidar base/conflitos antes da integração, sem descartar worktrees.

Corte real de uplink comprovado em [workflow38797806054](https://github.com/procopio420/rodada/actions/runs/38797806054),
SHA 7cb08ad7; nova prova a9cf em [workflow38815589150](https://github.com/procopio420/rodada/actions/runs/38815589150).
São provas separadas do turno local e de Wi-Fi físico. CI 899255b1:
[workflow38816278767](https://github.com/procopio420/rodada/actions/runs/38816278767).

Pendências externas: dispositivo físico, rede do bar, PSP/Tap/NFC/Pix reais,
impressoras, fiscal, aceite presencial e rollback VR System. Host probes locais
não certificam DNS/TLS/ingress/cookies entre subdomínios. Autodeploy não foi
certificado; integração deve permanecer atrás desse gate. Sem merge/deploy,
Play Store, Railway, pagamento real ou fechamento artificial da issue.
