# Integração técnica — 21/10/2026

Status: **parcial, NO-GO global**. Não há deploy ou homologação física nesta missão.
Baseline inicial `87f5362208f310894f38a8755af43e5551056b47`; main após os merges
`767e19cc6b29040b267c18c0de44272bdf5d045c`.

## Merges e fonte

| PR | Entrega | Squash SHA |
|---|---|---|
| [281](https://github.com/procopio420/rodada/pull/281) | Spec031: política canônica por Venue, WARN_ONLY/ENFORCE, versão, auditoria e CAS | `047807cb8008e009b3ac26cb00ebfe9a7b9d92ca` |
| [286](https://github.com/procopio420/rodada/pull/286) | Escape/foco da personalização e contratos visuais atuais | `a0fa2b149b58b4b941a1561cde2dcee71de29e1e` |
| [284](https://github.com/procopio420/rodada/pull/284) | Web/Guest/Compose consomem modo efetivo; editor gerencial recuperável | `29f6a10a75348f5153d05cf9ce0c46b666b24b26` |
| [288](https://github.com/procopio420/rodada/pull/288) | Capacidade agregada99, foco após refresh/remover, Abrir e pedir direto, testes determinísticos | `767e19cc6b29040b267c18c0de44272bdf5d045c` |

Candidato CI288 `e3b05de49da864c8fc227ba60eaacc4edeca0bb7`, árvore
`8451ea78099ca27a114fd49941ffdce90e673c54`. Composição local `77bd3618`
com a mesma árvore; a reconciliação com main não alterou seu conteúdo.

## Resultados executados

- [Web CI288](https://github.com/procopio420/rodada/actions/runs/39612818611/job/119266666894):
  **162 PASS, 3 SKIP, 13,4min**, zero retries; Django/PostgreSQL17 + BFF + Chromium,
  runner Ubuntu24.04/Python3.12/Node22. Typecheck, lint incremental, build,
  auth/tenant/identity/gateway passaram. Os três skips são menu CSV opt-in;
  gate visual completo não foi acionado neste workflow.
- Android CI284, fonte `f0405107b434785712b9d78a1599f11dc4571531`:
  [unit/build/lint PASS](https://github.com/procopio420/rodada/actions/runs/39609630112/job/119254774983).
  `forced-stop-recovery` **SKIPPED**. Não transferir esse PASS para instrumentação
  ou aparelho, nem afirmar Android executado novamente no SHA288.
- API local composição `8bdd4916`: **27 PASS/48,39s** (rehearsal1, modos13,
  concorrência de policy3, intenção2, pagamentos8), PostgreSQL16.15/Python3.12.14/
  Django5.2.18. Rehearsal anterior da mesma missão também PASS1/15,25s.
- Visual dirigido: diálogos14 PASS, adjacentes22 PASS, mobile99/A→B→A/refresh
  retido3 PASS; remoção9 PASS/19,9s e fila PostgreSQL3 PASS/1,2min. Revisão
  independente do delta `6a8d9fc4…14c63aec` sem achados reproduzíveis.
- A regressão local ampla foi iniciada, mas seus arquivos temporários deixaram
  de estar disponíveis após a renovação do ambiente. Seu resultado terminal é
  **NOT_VERIFIABLE**; não contabilizar como PASS. CI288 acima é a evidência
  durável da regressão de integração. Não existe pacote final de IDs preservado
  desta rodada local; o rehearsal versionado anterior permanece válido em seu SHA.

Revisões independentes dos PRs281/284/286 e delta288: NO_FINDINGS_WITH_GAPS.
Não são aprovação GitHub autenticada nem aceite humano/piloto.

## AC-01..24 — resultado por recorte

Cada linha herda fonte/ambiente/links acima. PASS abaixo aceita somente o recorte
explicitado; nenhum checkbox global é encerrado com base em execução parcial.

| AC | Evidência aprovada neste corte | Resultado integral / próximo gate |
|---|---|---|
| 01 | CI288: ux2-now, destino canônico por UUID | Parcial; repetir composição Android/QR |
| 02 | CI288 drafts/contexto; visual A→B→A e foco após refresh | Parcial; Back/fontes nativos atuais |
| 03 | CI288 rejeição stale/sessão e contexto; tenant tests | Parcial; revogação nativa atual |
| 04 | CI288 pedido real, OrderID/estação após reload | Parcial; Compose integrado |
| 05 | CI288 commit+ACK perdido/reload, envelope original | Parcial; restart Android real corrente |
| 06 | CI288 repetir/revalidar; visual capacidade99 | Parcial; matriz nativa de modificadores |
| 07 | API27 PG concorrência; CI288 erro/limite | Parcial; negativas nativas correntes |
| 08 | CI288 Dispatch503 não bloqueia pedido; visual filas | Parcial; pico50/fontes/tempo conjunto |
| 09 | CI288 ux2-now navega sem claim/complete | Parcial; repetir Android |
| 10 | CI288 entrega READY/Tab CLOSED/ACK perdido, quatro larguras | Parcial; provenance e toque nativos |
| 11 | CI288 fila três larguras, outro operador, readback503 e ACK perdido | Parcial; sessão/concorrência nativa |
| 12 | CI288 parciais, saldo e histórico sem draft | Parcial; paridade nativa atual |
| 13 | CI288 um Payment, readback automático, zero-close | Parcial; dispositivo/rede/PSP externo |
| 14 | Rehearsal PG três Tabs, última CLOSED sem release automático | PASS API; AC global ainda aberto |
| 15 | CI288 release identidade imutável/A→B; rehearsal ciclo/epoch | Parcial; giro nativo integrado |
| 16 | API27 concorrência financeira; CI288 rejeição/caixa | Parcial; PSP externo não simulado |
| 17 | Visual projeção/fronteiras/fontes; CI284 modo efetivo nativo | Parcial; paridade corrente completa |
| 18 | API modos/concurrency e CI288 spending-policy: WARN_ONLY/ENFORCE | PASS backend/Web; não duplicou financial_position; paridade instrumental pendente |
| 19 | CI288 alteração gerencial auditável, CAS, lostACK, troca Venue | Parcial; sem alegar garantia/PSP real |
| 20 | Rehearsal API/DB e CI288 Web/Guest/produção/caixa | Parcial; pacote conjunto Android/IDs corrente |
| 21 | CI288 perda de rede/readback/replay/operador | Parcial; app morto real corrente |
| 22 | Visuais dirigidos 360/390/430 e foco/teclado | Parcial; matriz completa, aparelho/TalkBack/toque |
| 23 | Métricas canônicas de giro existentes | PENDENTE: fricção/intenção e comparativo medido antes/depois |
| 24 | Quatro merges com CI crítico e revisão independente do código | PENDENTE: flag UX por Venue/role, rollback ensaiado, aceite humano/piloto |

## Restante técnico e gates externos

Ainda há trabalho técnico: instrumentação de fricção/intenção (E06-07), flag UX
Venue/role com rollback comprovado (E06-10), pacote instrumental Android corrente,
matriz visual completa e pico50 atual. `table_service_enabled` é política de
serviço de mesa; não equivale a kill switch da UX033. Relatório de giro não
substitui latência de intenção nem comparativo antes/depois.

Gates externos: aparelho físico S24-class, TalkBack/toque, PSP/hardware quando
aplicável, operador/bar/piloto e GO humano; deploy de produção exige autorização.
Não afirmar que somente homologação física resta ou que a Spec033 foi concluída.

## Resultado posterior — evidência terminal e cortes adicionais

Esta seção complementa o registro anterior, mantendo a distinção entre recortes
aprovados e aceite global. **NO-GO global permanece; nenhum AC inteiro foi
fechado pela soma de execuções parciais de plataformas distintas.**

- PR292, candidato `22724f3524c0720e1c0c4fb532c09f235375280c`, squash
  `f1b512f249363c9323e007bbaae894039451da99`: relatório readonly de tempos
  canônicos, 31dias, capability MANAGEMENT_REPORTS_READ, Venue autenticado,
  cobertura missing/invalid/unverified e médias somente observadas. Não deriva
  intenção nem recebimento visual de produção; sem novos taps ou persistência.
  API **1069 PASS/546,98s**, PostgreSQL17; Web **162 PASS/3 SKIP/16,8min**.
  [API](https://github.com/procopio420/rodada/actions/runs/39654479066/job/119411731874)
  e [Web](https://github.com/procopio420/rodada/actions/runs/39654478748/job/119411754432).
  R3 independente sem achados após corrigir datas extremas fora do UTC.
- PR293, squash `bdb9cbee94dec83c8b2ae1f40d964a9b002eb927`: migração de três testes de mesa para a página atual, IDs determinísticos
  e foco no heading; preserva preview de destino ocupado/livre e a11y. Nenhuma
  mudança de produto/ledger. Três dirigidos **PASS/6,6s**; conjunto Attendance
  **97/97 PASS/3,1min**, sem skips/retries, fonte local `f6580e3`, Web tree
  `1ce18e80272c7799ec88a7211eec2b37013cb386` (mesma árvore Web do candidato
  `8cef607cce04a4eba004cb0c76731061c8dc69b3`). Node24.19, npm11.9,
  Playwright1.58.2, Chromium145.0.7632.6. Fixture browser, sem API real nesse
  comando. CI Web terminal **162 PASS/3 SKIP/16,3min**,
  [job119414702388](https://github.com/procopio420/rodada/actions/runs/39655550965/job/119414702388).
  A rodada anterior teve duas falhas de seletor legado e foi interrompida
  (exit130); seu log está preservado e não foi contabilizado como PASS.
- PR294, candidato `a3b42fd68f9f7aa77b11cc3e03844df0f74d2856`, squash
  `b0ad7eb126b9eccf979509e2d8de76f74eff08bf`: runner reutiliza o rehearsal original inteiro, com DB reservado de teste
  PostgreSQL loopback. Recibo somente após PASS/cardinalidades/estados terminais,
  sem segredos ou dados do bar. Artefato `spec033-api-rehearsal`, run
  [39656356004](https://github.com/procopio420/rodada/actions/runs/39656356004),
  [artefato12371028318](https://github.com/procopio420/rodada/actions/runs/39656356004/artifacts/12371028318), digest ZIP
  `fb5de6c0cf2b46a8988b77eb9197a47563e1db1b67d4d88feae47e54fa2de557`,
  expira em19/01/2027. Contém SHA/tree/ambiente e IDs de três Tabs/três Orders/
  seis itens/Charges/Payments/tasks, estados CLOSED/DELIVERED/CONFIRMED/DONE,
  mesa/ocupações/gerações. Consulte também o resultado terminal do workflow;
  upload isolado não aceita regressão posterior. Runner reproduzível em
  `scripts/spec033-rehearsal-receipt.py`. Três guards negativos locais PASS;
  R3 independente sem achados após incluir o runner nos dois filtros de CI.
  CI API terminal **1065 PASS/592,52s**, rehearsal1 PASS/2,221s (mais setup).
  Esse candidato partiu da base7cb; os quatro testes novos do relatório foram
  aprovados no candidato292 (1069), preservados pelo merge não sobreposto.

Evidência local versionada em [completion-20261021](evidence/completion-20261021/):
logs sanitizados, `manifest.json` com SHA256 e capturas fixture360/390/430 do
movimento de mesa. Capturas não equivalem a paridade pixel completa/aparelho.

### Delta da matriz AC

| AC | Evidência adicional aprovada | Gate integral restante |
|---|---|---|
| 02 | 97visuais; foco na linha após refresh e no título da Mesa | Compose atual/Back/fontes e pacote conjunto |
| 08 | CI288 também executou quatro casos peak-dispatch:50READY+50chamados persistidos,360/390/430/1280 | Pico/fonte/tempo nativo e operação de campo; não reimplementar o pico Web |
| 14/15/20 | Recibo PostgreSQL com IDs/estados após jornada original e giro explícito | Mesmo pacote completo Web+Compose/QR/caixa, não apenas API |
| 17/18 | Modos031 em main, testes concorrentes e Web162; sem motor financeiro novo | Instrumentação/paridade nativa atual |
| 22 | 97browser; três capturas de movimento e fonte2 nos casos existentes | Matriz pareada completa, TalkBack/toque/aparelho |
| 23 | Endpoint agregado canônico e quatro regressões PG novos | Início de intenção, passos, tentativas/erros e versãoUX Web/Compose; comparativo medido |
| 24 | PRs pequenos com CI crítico e revisão independente | Flag UX por Venue/role, destino e ensaio de rollback, GO de operador/piloto |

Correção do inventário anterior: pico Web50 existe e passou no CI288; não é gap de
implementação Web. O que falta é a composição nativa/operacional e medição de SLA.
`table_service_enabled` continua sendo política de serviço contextual, não flag
separada de apresentação/rollback033. Os gates técnicos remanescentes não devem
ser apresentados como se dependessem somente de aparelho físico.
