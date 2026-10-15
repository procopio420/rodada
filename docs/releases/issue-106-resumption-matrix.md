# #106 — matriz de retomada local

Estado em 2026-10-15: **NO-GO**. `PASS` abaixo identifica uma prova parcial específica, nunca a aprovação automática da tarefa inteira. O pacote e3d59 passou o slice inicial; e2b0 passou recovery nativo, Compose, nove browsers e SQL, mas falhou no teste financeiro que esperava HTTP200 em replay cujo endpoint retorna201. Correções adicionais já constam de main em be5743d8. PRs191–193 foram integrados externamente durante a pausa; esta execução não efetuou merge/deploy.

## Tarefas A–F

| Tarefa | Estado | Prova existente / falta para aceite completo |
|---|---|---|
| A1 | Concluído | Inventário reconciliado no checkpoint191; integração não inferida do inventário. |
| A2 | Parcial | QR-first/claim Web/SQL executados; manter prova no SHA final. |
| A3 | Parcial | Guest/Web consomem duas Tabs; Android standalone; falta readback nativo das duas Tabs contextuais. |
| A4 | Parcial | Última Tab não libera, release/limpeza/nova visita executados; repetir no SHA final. |
| A5 | Parcial | Sessão Guest antiga negada após release e nova visita; repetir no SHA final. |
| A6 | Parcial | Receipts e SQL existem; índice final pendente. |
| B1 | Concluído | Testes127 reaproveitados e separação HTTP/storage versus Compose documentada. |
| B2 | Parcial | Fixture compartilhada real, cluster hash, dois atores/produtos/estações. |
| B3 | Parcial | Android Compose, Atendimento e Guest reais executados; head final pendente. |
| B4 | Parcial | NEW→PREPARING→READY por UI Bar/Cozinha executado; head final pendente. |
| B5 | Parcial | Web canônico comprovado; falta projeção nativa/gerencial pós-READY. |
| B6 | Parcial | PR194 Guest/Web; nativo em implementação/execução, sem PASS antecipado. |
| B7 | Parcial | SQL correlacionado; completar negativos e pacote final. |
| C1 | Concluído | Inventário financeiro existente reaproveitado. |
| C2 | Parcial | Somente dinheiro de teste e PostgreSQL exclusivo; pendência controlada sem PSP. |
| C3 | Parcial | Parcial/residual passou no baseline; replay CASH ampliado precisa ciclo final. |
| C4 | Parcial | Bug de fechamento PENDING reproduzido e corrigido; UI/SQL negativo passou em e2b0; financeiro completo pendente. |
| C5 | Parcial | Caixa/divergência/revisão executados; ampliar negativo de papéis/cutoff. |
| C6 | Parcial | Estorno compensatório implementado; validar ciclo final/SQL. |
| C7 | Parcial | Reconciliação independente existe; pacote final pendente. |
| D1 | Concluído | Inventário de concorrência/auth/tenant e harness de barreira reutilizado. |
| D2 | Parcial | HTTP simultâneo start/start, UI e SQL passaram; repetir head final. |
| D3 | Parcial | CAS claim/claim e release/open reais, UI e SQL passaram. |
| D4 | Parcial | Guest double click/body divergente, nativo recovery; falta negativo/divergência e double tap Compose. |
| D5 | Parcial | Web revogação/relogin preserva intenção; falta Android, expiry/refresh/SSE negativo. |
| D6 | Parcial | BFF A/A,B/B permitidos e A/B,B/A negados; Guest/native/Host não certificados. |
| D7 | Parcial | Receipts sanitizados e negativos SQL; manifest final pendente. |
| E1 | Concluído | Proxy RST, corte uplink emulador e Wi-Fi físico distinguidos. |
| E2 | Parcial | POST commitado/perda resposta/force-stop/offline/replay executados; head final pendente. |
| E3 | Parcial | Mesmo Order nativo→Bar e SQL; readback nativo pós-READY pendente. |
| E4 | Parcial | SSE-only Web, HTTP/polling/cursor/SQL passou; Android não comprovado nesse fault. |
| E5 | Parcial | Kitchen offline durante commits e recovery NEW executados. |
| E6 | Parcial | Ruptura nativa após cart em andamento; conflito de intenção offline/revogação requer revisão persistida ainda não comprovado. |
| E7 | Parcial | Transporte/PID/instrumentation/SQL existem; índice final pendente. |
| F1 | Concluído | InventárioCI/checks e gatilhos por paths documentados. |
| F2 | Parcial | Runner comum e identidade de cluster em produção de testes; suíte completa pendente. |
| F3 | Parcial | Checks seletivos existentes; smoke completo por risco pendente. |
| F4 | Parcial | Workflow integrado reutilizável; ainda não cobre todo A–E. |
| F5 | Parcial | Contrato/validador e compilador fail-closed; versões/review/vínculos finais pendentes. |
| F6 | Parcial | Esta matriz distingue prova de lacuna; relatório final ainda não existe. |
| F7 | Parcial | Validador nega GO sem14PASS/invariantes/review; nenhum GO integral. |
| F8 | Parcial | R3 independente por slice; review e documentação do SHA final pendentes. |

## E2E-01..14

Não existe ainda uma execução completa comprovada no SHA final. Contagem conservadora desse gate: **PASS0 / FAIL0 / SKIP0 / BLOCKED14**. Isso não apaga os testes parciais bem-sucedidos descritos acima.

| Cenário | Estado integral | Lacuna principal |
|---|---|---|
| E2E-01 | BLOCKED | Execução/review/artifact do head final |
| E2E-02 | BLOCKED | Duas Tabs contextuais lidas pelo Android |
| E2E-03 | BLOCKED | Execução/review/artifact do head final |
| E2E-04 | BLOCKED | Projeções após READY e head final |
| E2E-05 | BLOCKED | Android stale cart e preservação anterior; head final |
| E2E-06 | BLOCKED | Replay financeiro completo e reconciliação final |
| E2E-07 | BLOCKED | Negativos de papéis/cutoff; head final |
| E2E-08 | BLOCKED | Execução/review/artifact do head final |
| E2E-09 | BLOCKED | Double tap/payload divergente nativo |
| E2E-10 | BLOCKED | Auth nativa/expiry/refresh e cruzamentos Guest/Host |
| E2E-11 | BLOCKED | Execução/review/artifact do head final |
| E2E-12 | BLOCKED | Cobertura do fault exigido e head final |
| E2E-13 | BLOCKED | Execução/review/artifact do head final |
| E2E-14 | BLOCKED | Financeiro/compensação completo no head final |

Gates externos continuam separados: aparelho físico, Wi-Fi do bar, PSP/NFC/Tap/Pix, impressoras, fiscal, aceite presencial e ensaio de rollback VR System. Não são substituídos por emulador, testes de domínio ou CI genérica. Autodeploy externo ainda não verificado; não autorizar merge/deploy por este documento.
