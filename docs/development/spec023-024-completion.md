# Specs023/024 — integração verificável

13/10/2026. Snapshot de QA local anterior à publicação; resultados posteriores da CI são mantidos na PR pelo head. Branch: codex/spec023-024-completion. Sem merge de PR ou deploy.

## Identidade e preservação

Base inicial b6d6ae10ddb3e3d822c5971a89cc3cd735218114. Recortes Web/API locais derivados de ad5d64f foram aplicados por patch de três vias em checkout isolado; conflitos documentais conservaram o histórico. Android/Spec026 incorporados somente no checkpoint estável T11c: patch172829bytes e manifesto dos15 arquivos novos. T11d continua sob edição concorrente, fora deste recorte. Checkout original, dados e trabalho concorrente preservados.

Main avançou durante a validação. db231ee3095080b95ab587a370e6d5a9b42748d2 integrada no commit7ac9389, preservando hosts/CI. Slices:2d2f6f2 contratos, c94d190 API,3af0426 Web,3fe0653 Android. Ler o head definitivo na PR; RC19dfc80 e PR68 não certificam esta composição.

## Matriz atual

| Critério | Estado | Prova / limite |
| --- | --- | --- |
| 023 V01 cinco exports | PASS |34 contratos/pares estáveis; hashes/fontes preservados, inventário atual em7ac9389 com dirty documentado |
| 023 V02 controles equivalentes | PASS parcial | Gates existentes≤0,1%; não certificam composição integral |
| 023 V03 fixtures | PASS | Snapshots explícitos; resumo4/2/2; legados sem snapshot independentes |
| 023 V03/V04 Cozinha integral | FAIL |11,7785%1280×800, limite0,1%; header3,2357%, resumo13,0527%, tickets16,1446%, passe6,7094% |
| 023 Bar/Cozinha operacional | PASS | Comandos/configuração/lotes/availability/pending, navegador e PostgreSQL reais |
| 023 jornada financeira nativa | PASS emulador | Login→Tab→BAR/KITCHEN→produção Web→entrega Android→pagamento→estorno→fechamentos; readback canônico |
| 023 fonte200%/teclado/componentes | PASS |198 testes, zero skips/falhas:33×360/390/430×fontes1/2; não estende a telas futuras/hardware |
| 023 HTML↔Compose integral | Não verificado | Navegação/controles acessíveis não provam igualdade de todas as telas |
| 023 V07 CI final | Não verificado neste snapshot local | Resultado posterior vinculado ao head da PR; Web/API/Android no PR, emulador pesado manual |
| 024 Atendimento cinco critérios Agora | PASS | PostgreSQL360/390/430: ownership,409/readback, resposta perdida/mesma ação,503 inicial/stale/recuperação,44px/accessibilidade |
| 024 Atendimento demais regressões | PASS por cenário; CI integral pendente |86 passaram no conjunto integrado; busca corrigida e revalidada com paginação nas três larguras; configuração/mesa/gateway financeiro excluído |
| 024 menuAC02–06/08 | PASS | Preview, atomicidade inclusive falha durante escrita, replay, update explícito, ícones/disponibilidade/escopo preservados;143 linhas campo a campo |
| 024 menuAC07 | PASS |143 produtos112BAR/31KITCHEN; três jornadas Web; Android/API1200+350centavos |
| 024 menuAC01 | EXTERNAL_BLOCKED | Homologação de preços/roteamento pelo estabelecimento; catálogo comercial não alterado |
| Android RST original | PASS atual / histórico PARTIAL | Queda após commit, PID/morte/offline/replay/exactly-once; episódio histórico sem PID não reproduzido |
| Cloud/aparelho/rede/impressora/fiscal/provider | EXTERNAL_BLOCKED | Exigem acesso e aceite próprios |

## Correções verificadas

- Operations/Corrections/Refunds classificam401/ACCESS_TOKEN_EXPIRED como AuthApiException. Renovação repete a requisição rejeitada uma vez, com mesma sessão/corpo/chave; rotação concorrente reutiliza a credencial já guardada.403 permanece negativa. Dois instrumentados de transporte/concorrência passaram; a mesma comanda continuou.
- Fixtures Web isoladas evitam contaminação de preço/availability/ownership. Somente deadlock40P01 da transação descartável de preparação pode repetir até três vezes, após rollback integral. Testes continuam retries=0. [Contrato](web-e2e-isolation.md).
- Esperas por confirmação canônica antes de reload, tratamento do redirect no POST perdido, seletores de comanda corrigidos. POS fechado oculta recebimento se não houver intenção pendente ambígua.
- Capturas nativas variavam após toque com animações Android. Harness fixa relógio Compose, espera repouso nativo e usa escalas de animação0 somente no emulador isolado, restaurando-as depois. Exige igualdade byte a byte; salva pares divergentes e nunca repete imagens até obter PASS.
- [ADR0020](../adr/0020-reference-parity-and-canonical-operations.md): domínio preservado, sem inventar cliente/SLA/recibo/ações, mudar export/limiar ou aprovar baseline. Spec023 global permanece aberta.

## Prova financeira

[Readback](../design/evidence/spec023-024-native/native-menu-readback.json):1Order,2OrderItems DELIVERED, charges1550,2pagamentos CASH1850,1Refund300, exposição0. Pagamento original1550 PARTIALLY_REFUNDED preservado; refund com ator/timestamp/auditoria/movimento−300. Tab/turnoCLOSED, caixa esperado1550/contado1550/discrepância0. Provider/hardwareNOT_RUN.
[Pedido](../design/evidence/spec023-024-native/native-order-confirmed.png), [pagamento](../design/evidence/spec023-024-native/native-payment-confirmed.png), [estorno](../design/evidence/spec023-024-native/native-refund-confirmed.png), [caixa fechado](../design/evidence/spec023-024-native/native-cash-closed.png).

## Checks e reprodução

Antes da atualização da main:662pytest PostgreSQL,575Django PostgreSQL,465visuais,87integrações Web+3CSV,17unitários Web, types/build; Android72unit/build/lint e2novos instrumentados passaram. Resultados da composição atual abaixo. Migrations/check sem drift. Lint API inicial:437achados contra443 na mesma main/configuração, zero novos/seis removidos; lint global continua FAIL preexistente, sem supressão.

Resultados atuais da composição7ac9389/665ad05/7ccddbf:

- API:677pytest PostgreSQL PASS em1235,77s, zero skips/falhas; XML atual no runtime. Check/migrations PASS, inclusive migration VenueDomain da main. Lint441 contra447 da main db231ee, zero novos/seis removidos;441preexistentes permanecem FAIL.
- Web:465visuais PASS em13,1min; types/build e17unitários PASS. Suíte integrada:86PASS/1FAIL por esperar a lista antes da consulta terminar. Trace comprova GETs de4,66–10,11s em carga concorrente; teste agora aguarda o200 canônico do offset0, sem retry/tolerância nova. Busca+paginação2PASS em1,7min e CSV3PASS em39,7s. CI deve executar o conjunto integral no head final.
- Android:72unitários/build/APK/lint PASS, zero erros de lint, oito warnings/dois hints;198instrumentados da matriz,2Auth e2APIRecovery PASS. Recovery API lê comanda/turno originais sem trocar contexto ou reenviar a intenção pendente.
- RST final:3fases instrumentadas PASS, processos16950/17047 comprovadamente encerrados, duas respostas perdidas com corpo/chave idênticos e um replay200. PostgreSQL1Order/1Item/1Charge/0Payments. [Readback](../design/evidence/spec023-024-native/native-rst-readback.json), [lifecycle](../design/evidence/spec023-024-native/native-rst-lifecycle.json). O episódio histórico sem PID não foi reproduzido e não é encerrado por retry verde.
- [Matriz nativa](../design/evidence/spec023-024-native/accessibility-matrix.json) e18capturas font200 versionadas. Captura login-keyboard antecede credenciais/rolagem; o teste exige IME real aberto e acesso a PIN/Entrar por scroll, não visibilidade simultânea de todos os campos.

Somente testes/workflows/documentação mudaram depois da composição de produto7ac9389. O head da PR identifica a entrega e seus resultados CI; não apresentar o86+2 local como uma execução integral87 verde.

Web: [README](../../apps/web/README.md), build antes de Playwright; PostgreSQL descartável rodada_web_e2e, flags opt-in e host loopback. API: pytest --ds=rodada_api.settings no banco de teste, manage.py check e makemigrations --check --dry-run. Android: ./gradlew testDebugUnitTest assembleDebug assembleDebugAndroidTest lintDebug. Matriz: scripts/android-accessibility-matrix.ps1 com -Adb/-Serial/-OutputDirectory, exige198 testes sem skips.

RST: scripts/android-live-post-drop.sh exige API/PostgreSQL/fixture/proxy reais, ADB/Python; launch/PID/lifecycle em artifacts/. Não relança para converter ausência de PID em PASS. RODADA_TEST_PYTHON permite runtime já instalado; shell Windows mínimo conserva sleep via Python. Logs anteriores preservados.

Demo nativa: spec023-native-demo.py --canonical-menu somente em emulador/Venue descartável seed_release_demo; produção por spec023-native-production.cjs. Consultar banco antes de retomar financeiro ambíguo. spec023-native-menu-readback.py --final é somente leitura, exige banco/host/porta explícitos. APK debug usa endpoint de teste; HTTPS/assinatura/AAB/aparelho físico são gates independentes.

[Manifesto do APK local](../design/evidence/spec023-024-native/debug-apk-manifest.json):13.429.445bytes, SHA2565d04b133f29e66542be9a71f295c0290f115eacf0c1c76040da50c7f84ac7a83, configuração de revisão10.0.2.2:8144. Arquivo local ignorado em artifacts/rodada-attendance-spec023-024-debug.apk. CI também retém APK debug por sete dias, usando seu endpoint padrão de teste8000; nenhum AAB assinado de produção é publicado.

## Entrega e pendências

A primeira CI do turno descartável em1f25df3 revelou uma expectativa antiga do harness: pagamento parcial1000 com exposição4300 não exige devolver o item600, conforme UX-34 da Spec017. O cenário de estorno agora recebe o saldo4300 por CASH antes da correção, exige estorno positivo600 e exposição final0, preservando relatório8900/600 e caixa14300. Não altera regras do produto, não aceita refund zero e conserva a falha anterior como evidência. Turno HTTP local corrigido PASS em PostgreSQL com dispatcher real, relatório incremental8900/600/8300 e caixa14300/discrepância0; a CI do novo head deve certificar o turno integral/restart/64Tabs. Tentativas locais anteriores: banco novo recusado pelo guard de seed sem criar identidades; execução sem dispatcher falhou antes de pagamentos. Registros mantidos, sem apagamento dos dados anteriores.

Branch para revisão; nenhum merge/publicação comercial/substituição de PDV declarados. Restam referência visual compatível e aceite integral023, conclusão do episódio histórico sem PID se reproduzido e gates externos da matriz. Logs completos em visual-artifacts/spec023-024/runtime ignorados; evidências sanitizadas versionadas e CI verificável pelo head da PR.
