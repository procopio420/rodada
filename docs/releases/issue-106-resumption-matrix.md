# #106 — matriz verificável de execução

## Estado técnico atual — 16/10/2026

A issue foi fechada administrativamente pelo responsável; #205 e #206 foram
integrados por outra execução. Isso não equivale a aprovação R3 independente ou
GO de produção. Após liberação explícita do mantenedor, o PR #207 foi
integrado em `main` no commit `513de6a20f1cc2abc1521532602a66c83712081b`.
A integração não é uma aprovação independente autenticada.

O [run do #206](https://github.com/procopio420/rodada/actions/runs/38848540935)
executou `956f2139ef782277a3a23de3a3ae05cef9265e8f`: **14 PASS / 0 FAIL /
0 SKIP / 0 BLOCKED**, execução global e hashes verificados no pacote baixado.
Seu gate permanece **NO-GO**, somente por ausência de revisão independente
registrada. A árvore do merge307ec5d7 é idêntica à árvore956f2139; não se atribui
execução ao SHA do merge por essa equivalência.

A revisão independente posterior identificou um **P1 no gate R3**: COMMENTED ou
PENDING sobrescrevia CHANGES_REQUESTED do mesmo reviewer, apagando um veto ainda
válido. O [PR207](https://github.com/procopio420/rodada/pull/207), já integrado,
corrigiu a redução para considerar somente estados decisórios. R3 cumulativa de main+patch:
NO_FINDINGS_WITH_GAPS, zero P0/P1 abertos no código corrigido; **32 testes PASS**.
O SHA da correção é `67fcaacaa7d7919a6ab3fa3a03f0dc6c206a438e`; seu
[workflow](https://github.com/procopio420/rodada/actions/runs/38857293536) passou
em **13m55s**. O [artefato12028032853](https://github.com/procopio420/rodada/actions/runs/38857293536/artifacts/12028032853)
foi baixado e verificado: **14 PASS / 0 FAIL / 0 SKIP / 0 BLOCKED**, execução
global PASS, 58 artefatos e 21 hashes de fontes íntegros, oito snapshots SQL. A R3 independente
do código e pacote em `/root/review_foundations` confirmou zero P0/P1 técnicos
abertos. Inspecionou 15 ZIPs sem campos sensíveis/JWT/PIN textual encontrados;
sem traces brutos CI, não houve comparação literal de tokens nem inspeção visual
dos binários. Essa limitação não é omitida do aceite.
[Resumo machine-readable](evidence/issue-106-67fcaaca/ci-summary.json) registra
SHA, ambiente, cenários/IDs, SQL, execução e gate. Não substitui os ZIPs completos.

**NO-GO formal:** o manifesto gerado para o SHA `67fcaaca` contém somente o erro
de revisão independente autenticada ausente. A consulta real ao GitHub para
PR207 retornou REVIEW_BLOCKED, sem aprovação de reviewer diferente do autor.
O código corrigido tem R3 local em contexto separado, sem P0/P1, mas isso não
cria aprovação GitHub. O mantenedor autorizou o merge do PR207 e o código foi
integrado em `main` no commit `513de6a2`; esse ato **não** substitui o gate R3.
O deploy automático da demo no Railway retornou SUCCESS para `rodada-web` e
`rodada-landing` nesse commit; isso não comprova aceite presencial ou GO.
A matriz histórica abaixo permanece atribuída ao SHA 899255b1; a última
execução integrada verificada reconfirmou os 14 cenários em `67fcaaca`, incluindo
exclusão de estação e snapshots B4/B7. Não se atribui esse teste ao SHA do merge.
F4 está implementada, mas a liberação formal permanece REVIEW_BLOCKED; os gates
externos abaixo não são substituídos por CI verde.

A revisão local em outro contexto não fabrica uma aprovação GitHub. O workflow
manual consulta uma aprovação real do SHA por reviewer diferente do autor;
`review_pr_number` não pode substituir esse requisito. Gates de aparelho/rede,
PSP, impressão, fiscal e aceite/rollback presenciais continuam separados.

## Execução histórica preservada

Execução local integrada **TESTED** no SHA `899255b1406fc3fe51ace2977c7789fc65cf68d0`,
15/10/2026, pacote `artifacts/runs/899255b1406f-20261015T221922Z` na worktree
`issue106-ci-package`. Android Compose real em emulador API36/KVM, Chromium,
Next/BFF, Django e um PostgreSQL17 descartável compartilhado. Nenhuma prova foi
importada de outro SHA/cluster. **14 PASS / 0 FAIL / 0 SKIP / 0 BLOCKED** em cenários;
a decisão global exige também invariantes e revisão independente do pacote.
O validador retornou **GO automatizado, errors=[]**, após a [R3 independente](https://github.com/procopio420/rodada/issues/106#issuecomment-6203562103).
Essa revisão local em contexto separado não é aprovação GitHub.
[Resumo machine-readable](evidence/issue-106-899255b1/local-reviewed-summary.json)
contém execução, versões, gate, revisão e SQL final; não substitui os ZIPs do
pacote completo local/CI nem atribui execução ao commit documental.

O pacote anterior a9cf6007 chegou aos 14 PASS mas falhou no SQL agregado por exigir
`revoked_at`, enquanto o contrato Guest invalida por geração/ocupação. A falha
foi preservada. 899255b1 verifica geração antiga, ocupação liberada,403 real e
nova sessão válida. bff3fc31 falhou antes por expectativa incorreta de movimento
zero; o serviço não cria OPENING_FLOAT quando o fundo é zero. Não houve mudança
de produto para acomodar esses asserts.

## Matriz atual A–F — candidato 67fcaaca

`CI_VERIFIED` nesta tabela significa reconfirmação no candidato 67fcaaca pelo run
38857293536 e revisão independente de seu pacote. Inventários preservam sua
origem documentada. `REVIEW_BLOCKED` distingue o gate formal autenticado da prova
de execução. O código corrigido já foi integrado à `main` no merge `513de6a2`;
esta prova automatizada continua vinculada ao SHA `67fcaaca`, sem atribuir teste
inexistente ao merge. Gates físicos continuam separados.

| Tarefa | Estado | Prova/escopo |
|---|---|---|
| A1 | RECONCILIADO | Inventário reconciliado; fundações #185 e contrato #186 preservados sem diff incidental. |
| A2 | CI_VERIFIED | QR-first, claim Web, mesma ocupação/geração e auditoria; claim sem ledger. |
| A3 | CI_VERIFIED | Duas Tabs Guest/Web na mesma ocupação, pedidos/saldos separados; ambas lidas no Compose; Tab standalone nativa. |
| A4 | CI_VERIFIED | Última Tab fechada não libera; release explícito, DIRTY/CLEANING/AVAILABLE e novo ciclo com mesmo QR. |
| A5 | CI_VERIFIED | 403 da GuestSession antiga; nova visita/geração válida, sem Order/Charge indevido. |
| A6 | CI_VERIFIED | qr-lifecycle-sql, browser-origins-sql e android-context-readback-sql. |
| B1 | RECONCILIADO | Harness #127 reaproveitado; HTTP/storage distinguido da confirmação Compose. |
| B2 | CI_VERIFIED | Fixture única, cluster hash, Venue/produtos BAR 700 / KITCHEN 1000 e múltiplos atores. |
| B3 | CI_VERIFIED | Pedidos confirmados pela UI Compose, Atendimento Web e Guest; IDs correlacionados. |
| B4 | CI_VERIFIED | NEW→PREPARING→READY por UI explícita nas estações; Guest mostra Pronto/chegando. |
| B5 | CI_VERIFIED | Android lê ambas Tabs prontas; Atendimento/Gerência mostram 7 DispatchTasks; OPEN sem conclusão ou provenance inventada. |
| B6 | CI_VERIFIED | Carrinhos stale Guest/Web/Compose negados com 409; offline ACTION_REQUIRED e pedidos anteriores preservados. |
| B7 | CI_VERIFIED | SQL final: 5 Orders / 8 Items / 8 Charges, 6800 centavos; estações/centavos/quantidades e zero pagamento por preparo. |
| C1 | RECONCILIADO | Inventário cash/ledger/concurrency existente reutilizado. |
| C2 | CI_VERIFIED | Somente CASH de teste e PENDING controlado sem PSP, PostgreSQL descartável. |
| C3 | CI_VERIFIED | Parcial de 300, refund de 100 e residual de 1500 centavos; resposta perdida e replay com mesmo Payment ID; demais Tabs sem pagamento. |
| C4 | CI_VERIFIED | Fechamento com saldo retorna 409; PENDING sem confirmação bloqueia, sem CashMovement/PaymentAttempt. |
| C5 | CI_VERIFIED | Abertura 10000 / suprimento 2000 / sangria 1000; esperado 12700 / contado 11700 / divergência -1000 centavos revisada; STAFF/CASHIER recebem 403; cutoff nos dois lados. |
| C6 | CI_VERIFIED | Refund compensatório de 100 centavos preserva Payment/Charge, confirmação e auditoria. |
| C7 | CI_VERIFIED | financial-sql/cash-cutoff-sql/financial-roles-sql/final-state-sql; recebido 1800 − refund 100, exposição 5100 centavos. |
| D1 | RECONCILIADO | Auditoria #130 reutilizada; controles limitados à jornada local #106. |
| D2 | CI_VERIFIED | start/start simultâneo com barreira/conexões PostgreSQL; uma ocupação/owner. |
| D3 | CI_VERIFIED | claim com CAS e release/open atômicos; auditoria única, sem Tab órfã/ledger. |
| D4 | CI_VERIFIED | Double tap Compose; perda de resposta/replay nativo e Guest; key/body idênticos e divergência retorna 409. |
| D5 | CI_VERIFIED | Revogação Web/nativa GET/POST/refresh/SSE; expiração 401 → refresh 200; intenção antiga exige revisão após novo login. |
| D6 | CI_VERIFIED | A/B próprio 200 / cruzado 404; Guest selectors/produtos negados; Host local assinado no BFF e Android direto negado. Não certifica ingress externo #130. |
| D7 | CI_VERIFIED | Receipts, instrumentation e SQL negativo: ausência de efeitos após 403/409/timeouts. |
| E1 | RECONCILIADO | RST, uplink do emulador e Wi-Fi físico separados; histórico CI documentado. |
| E2 | CI_VERIFIED | POST commitado / resposta perdida/force-stop/offline/replay; Order 1 / Item 1 / Charge 1 / Payment 0. |
| E3 | CI_VERIFIED | Mesmo Order recuperado → Bar READY; Compose contextual pós READY sem novo comando. |
| E4 | CI_VERIFIED | Somente SSE interrompido, HTTP saudável/polling/cursor retomado, item NEW único sem preparar sozinho. |
| E5 | CI_VERIFIED | Cozinha offline durante commits Guest/Web, recuperação NEW por snapshot e ações explícitas. |
| E6 | CI_VERIFIED | Offline PENDING → catálogo alterado → ACTION_REQUIRED; revogação e comando dependente bloqueado, histórico preservado. |
| E7 | CI_VERIFIED | Logs nativos/PIDs/interface, receipts SQL e 15 traces sanitizados; nenhum aceite de Wi-Fi físico inferido. |
| F1 | RECONCILIADO | Gatilhos CI / filtros de paths e dispatch manual inventariados; proteção/autodeploy externo não inferidos. |
| F2 | CI_VERIFIED | Runner/fixture únicos, guards de DB e hash do cluster; execução completa CI 67fcaaca, mantendo a prova local histórica 899255b1. |
| F3 | CI_VERIFIED | Smokes seletivos e gate pesado por paths; KB/Web e CI Android por SHA, sem ruleset alterado. |
| F4 | REVIEW_BLOCKED | Workflow manual A–E com upload always, exit real e corte de uplink separado; execução de PR comprovada; review GitHub autenticada e GO manual pendentes. |
| F5 | CI_VERIFIED | Schema/validador/manifest de 14 casos, versões reais, IDs / hashes de artefatos, SQL final e source_sha256. |
| F6 | CI_VERIFIED | Esta matriz e manifest por cenário; históricos FAIL preservados sem promover novo HEAD. |
| F7 | CI_VERIFIED | Gate automatizado exige 14 PASS / 10 invariantes / review; físico / PSP/fiscal separado. |
| F8 | R3_LOCAL_AUTH_BLOCKED | R3 independente por slices/contexto; inspeção sanitização/IDs/pacote final e KB. |

A auditoria posterior encontrou 53 observações corretas das filas no pacote 899,
mas faltavam asserts permanentes de exclusão de estação e SQL completo de
source/route/snapshot. [PR205](https://github.com/procopio420/rodada/pull/205)
acrescentou essas proteções a partir do SHA 7f04f803; a execução final do PR passou. B4/B7 foram
reabertas durante a auditoria e depois comprovadas por snapshot/exclusão de estação
na execução #205 e novamente em 67fcaaca. O GO do contrato 899255b1 permanece histórico;
o gate formal do candidato atual continua NO-GO por revisão autenticada ausente.

## Matriz atual E2E-01..14 — candidato 67fcaaca

Todos os cenários abaixo foram reconfirmados no SHA/cluster do candidato 67fcaaca, com traces de UI,
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

O responsável integrou #205 (incluindo os slices #196–#204) em 475acadd e #206
em 307ec5d7, fechando as branches supersedidas. Posteriormente, o
[PR207](https://github.com/procopio420/rodada/pull/207) foi integrado em
`513de6a2`, após autorização explícita do mantenedor e CI integrada verde.
Não houve aprovação independente autenticada registrada para o PR207; o
NO-GO formal permanece. O Railway confirmou SUCCESS da demo para o mesmo
commit, sem homologação física. O [PR208](https://github.com/procopio420/rodada/pull/208)
contém a documentação atualizada e ainda precisa de integração separada.
Revalidar bases antes de integrar; preservar worktrees e trabalho não commitado.

Corte real de uplink comprovado em [workflow38797806054](https://github.com/procopio420/rodada/actions/runs/38797806054),
SHA 7cb08ad7; nova prova a9cf em [workflow38815589150](https://github.com/procopio420/rodada/actions/runs/38815589150).
São provas separadas do turno local e de Wi-Fi físico. O [workflow 38816278767](https://github.com/procopio420/rodada/actions/runs/38816278767)
terminou com sucesso, mas o checkout de PR executou o merge sintético
`43cf60ca3b0cd8d444ea299e1430289799c8b8ff`, não 899255b1. Seu artefato
[12010989591](https://github.com/procopio420/rodada/actions/runs/38816278767/artifacts/12010989591)
contém 14 PASS e hashes válidos, porém NO-GO por branch ausente e revisão ausente.
Não se atribui essa execução ao head local. O [PR204](https://github.com/procopio420/rodada/pull/204)
corrige checkout/head/SHA efetivo/branch detached; execuções do novo SHA 78e04816
[PR38818247857](https://github.com/procopio420/rodada/actions/runs/38818247857) e
[manual38818268628](https://github.com/procopio420/rodada/actions/runs/38818268628)
foram concluídas: suíte de PR PASS e manual NO-GO por revisão ausente, com corte
de uplink PASS no mesmo SHA 78e04816. São provas históricas; o resultado atual
é o pacote 67fcaaca e seu gate NO-GO formal descrito no início.

Pendências externas: dispositivo físico, rede do bar, PSP/Tap/NFC/Pix reais,
impressoras, fiscal, aceite presencial e rollback VR System. Host probes locais
não certificam DNS/TLS/ingress/cookies entre subdomínios. O autodeploy da demo foi observado no Railway no commit `513de6a2`, com SUCCESS
para web e landing, mas não constitui aceite/GO de release. Nenhum teste em
pagamento real, publicação Play Store, PSP, impressão ou operação física foi
inferido desses merges.
