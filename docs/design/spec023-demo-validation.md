# Spec023 — demo validada e limites atuais (09/10/2026)

Base: origin/main45c4742, branch isolada codex/spec023-next, PR68 em rascunho. Branch original ux-operational-polish6e2f4ca, Lucas, outros worktrees e serviços existentes preservados. Nenhum merge, force push ou produção. PR61 permanece independente: sobreposição de apresentação/sessão Web, sem importar mudanças; nenhuma sobreposição em código Android na comparação dos heads auditados.

## Entregas em ordem V01–V07

| Etapa | Resultado atual | Limite |
|---|---|---|
| V01 | Cinco exports com34 contratos/capturas:19 passos da rail night + pico/offline/retorno;8 espécimes system;1 cozinha;1 pico;2 connectivity. Hashes/fontes/originais verificados antes/depois,34 pares byte-idênticos, execuções independentes com hashes idênticos. | Rail reproduz mocks literais; controles estáticos não provam operação real. Não cobre toda combinação de overlay. |
| V02 | Componentes existentes revalidados; header Android extraído e adaptado em identidade + ações FlowRow; catálogo conserva nome completo e preço em linhas próprias, mesmos tokens/callbacks. | Header adaptado é extensão responsiva, não paridade literal do header60px do export. |
| V03–V04 | Comparação atual e197 testes Web, incluindo Cozinha/Bar adjacente, transição individual, disponibilidade, identidade, responsive e acessibilidade. | Gate de fidelidade integral≤0,1% não comprovado. Métricas abaixo. Não refazer acabamento compartilhado entregue. |
| V05 | App instalado contra API real: login, Agora, conta, pico, abertura de Tab, busca, carrinho, pedido600centavos confirmado, proteção sem caixa, abertura/recebimento manual600centavos, fechamento de Tab e contagem/fechamento de caixa. | Recebimento e fechamento executados no app com readback PostgreSQL; estorno nativo não executado, coberto por HTTP/Web. Hardware/provider não executados. |
| V06 | Ensaio real detectou SSE Reconnecting sobrescrevendo OFFLINE. Correção mantém SEM SINAL até leitura confirmada; API separada parada/restaurada e app voltou ONLINE. Pico real1366requests/1043mutations aprovado. | Nenhum pagamento offline, replay automático ou confirmação fictícia. Regra proprietária Spec014. |
| Responsivo | Header, navegação, catálogo, pagamento e login instrumentados em360/390/430dp,160dpi, fontScale1/2, API36. IME real, texto longo, targets≥44dp, busy e callbacks. | Não prova todas telas internas com fonte200%, teclado ou hardware. |
| V07 | Types/build, auth/realtime12, visual197, PostgreSQL13, Android unit51/build/lint e matriz nativa8×6=48. | Gates locais; CI remota deve ser consultada por commit. Não é conclusão global023. |

## Diferenças integrais preservadas

Comparador existente pixelmatch threshold0.1/includeAAfalse; nenhuma máscara, tolerância ou baseline nova. V03 atual: header2,4946%; resumo12,8889%; tickets16,241%; passe6,7312%; viewport11,7038%. Os testes de auditoria passam sem transformar esses valores em aceite de fidelidade. Fontes e referência derivada anteriores mantidas. Próximo recorte visual: maior diferença comprovada nos tickets, com contrato de hierarquia compartilhada e fixture equivalente; não introduzir ownership/equipamento fictício ou backend novo.

## Ambiente e evidência

Windows, Node24.19.0, Playwright1.58.2/Chromium145, pt-BR, America/Sao_Paulo, DPR1. Emulador AVD rodada-v05-api36, serialemulator-5572, API36, iniciado read-only separado; JDK21 com target17. Header baseline360/font2 falhou em dois testes por clipping de ● rodada. Capturas antes usam host de geometria sem Surface; depois usa Surface real, portanto não comparar seus pixels como equivalência de cor. Instrumentação valida linhas de texto,44dp e callbacks; capturas são repetidas sem tolerância. XML por configuração preservado e gate atual exige2 testes header +2 navegação +3 campos críticos +1 login com IME, zero falhas/errors/skips.

PostgreSQL real55523 em cluster novo visual-artifacts/spec023-gates/pgdata. Bases rodada_web_e2e, rodada_web_e2e_before_guest_retry e rodada_demo são somente testes neste cluster; não são o banco demonstrativo55459. Web integrado3142/API8142; demo HTTP/nativeAPI8144 +dispatcher próprios. Serviços anteriores3119/18764/3123/8123/55459 mantidos. Nenhum reset/drop do banco anterior. Dados de tentativas preservados. Pagamentos sempre MANUAL_TEST, sem dinheiro/provedor externo.

[Evidências nativas](evidence/spec023-header/native), [matriz e baseline](evidence/spec023-header), [contratos de referência](evidence/spec023-reference-journeys/contracts.json), [turno completo HTTP](evidence/spec023-header/full-shift.json), [pico HTTP](evidence/spec023-header/busy-shift.json). Turno: caixa esperado14300centavos/discrepância0,87 eventos auditados, SSE replay, duplicatas de pedido/pagamento sem duplicação. Pico:64Tabs,8workers; p95 local407ms, sem SLA contratado. A evidência HTTP conserva native_android_ui=NOT_RUN: screenshots nativos são ensaio separado, nunca renomear protocolo como UI.

## Falhas e correções comprovadas

- Header360/font200 cortava marca: reproduzido antes, layout corrigido e matriz repetida.
- Primeiro PostgreSQL12/13: controle Atualizar comanda removido por SSE após revogação. Teste corrigido para exigir403/GUEST_SESSION_REVOKED da sessão antiga, recarregar e exigir erro explícito; rodada completa13/13. API e Web de produto inalteradas; contrato Spec004 registrado.
- Ensaio native detectou OFFLINE trocado por SSE reconnect; Spec014 atualizada antes do código, redução testada na fronteira30s, API36offline/recovery real aprovado.
- Harness Windows precisou decodificar ADB comoUTF-8 e reconhecer avisos reais; aviso Comanda aberta é transitório e não serve como prova. Abertura exige label único e ABERTA versão1; pedido exige total confirmado600centavos.
- Referência night13 tinha pulso animado: duas capturas de diagnóstico preservadas. Normalização é somente clock/animação/caret no harness; fonte/layout/dados e export original não alterados.34 pares finais idênticos.

## Reprodução

1. Preservar serviços e iniciar cluster/test API em portas separadas como descrito; seed_release_demo exige rodada_demo, obrigatoriamente em cluster isolado. Não usar demo-start-windows.ps1 sobre serviços existentes.
2. Web: apps/web — scripts typecheck/build/test:auth/test:realtime/test:visual/test:integration do package.json. Nesta máquina sem npm foi usado o executável Node e os entrypoints equivalentes; python3 do servidor de referência é wrapper local do Python gerenciado. Build precede visual. Integração exige env PostgreSQL55523, bases de teste e portas3142/8142.
3. Referências: node scripts/spec023-reference-journeys.cjs com browsers Playwright instalados. Captura servidor efêmero apenas de prototype, bloqueia rede externa, valida hashes e pares.
4. Android: definir JAVA_HOME/ANDROID_HOME/GRADLE_USER_HOME/ANDROID_SERIAL; configurar API36/160dpi/w×844/font1ou2, executar scripts/android-navigation-check.ps1 para cada combinação. Build/unit/lint/instrumentação real; XML antigo removido pelo gate antes da execução.
5. Native real: assembleDebug -ProdadaApiBaseUrl=http://10.0.2.2:8144/, instalar no emulador separado. scripts/spec023-native-demo.py exige --adb/--serial/--out e fases login,tab,order,payment-guard,cash-open,payment,cash-close. Produto QA Wrong item vem do turno HTTP existente. Offline/recovery exigem parar/restaurar somente API8144; não mudar o banco nem dispatcher. Cada fase só publica screenshots sem PIN/token; intenções financeiras não são simuladas pelo harness.
6. HTTP: scripts/demo-full-shift.py e scripts/release-busy-shift.py --url http://127.0.0.1:8144 --evidence arquivo.json. --verify exige snapshot sem escritas posteriores; o ensaio nativo criou Tabs depois, portanto não comparar os totais antigos como se o banco ainda estivesse congelado.

## Pendências concretas

Paridade integral de regiões Web/Android e referências complementares sem export; jornadas internas adicionais Android em fonte200%/teclado (login e campos críticos já validados); estorno em UI nativa; hardware e provider com SDK/configuração real; artefatos/CI por head publicado. Estes pontos permanecem abertos nos critérios globais. Nada aqui declara Spec023 completa ou fidelidade total.


## Readback nativo e commits

[Readback PostgreSQL](evidence/spec023-header/native/native-readback.json): uma Order, charges600centavos, um CASH CONFIRMED de600centavos, ator da Tab e timestamp confirmados, nenhuma correção/estorno/provedor externo, Tab CLOSED/saldo0. Caixa CLOSED, esperado/contado600 e diferença0. O script de UI foi corrigido para identificar MANUAL_TEST após o recebimento; o texto inicial none made não descrevia a fase payment e não é usado como evidência. Caixa conserva NBSP literal do NumberFormat, sem normalização de texto do produto.

Contratos/referências41a42bd; header/matriz20e3649; OFFLINE/reconnectbb29b5d; revogação guest1d22393. Gates Web/HTTP executados sobre esses conteúdos; Android recebeu posteriormente o recorte crítico abaixo, com gates próprios atuais. Clock/status bar do emulador é chrome do dispositivo, não prova da hora/business date da API. CI Android atual executa unit/build; lint/instrumentação são locais, não declarar cobertura nativa da CI.

## Continuação — campos críticos Android

[Relatório atual](spec023-critical-fields.md): nome/preço de catálogo, diálogo de pagamento e acesso ao login com IME real. Matriz final ampliada para8 testes×6=48; 51unit/build/lint aprovados. 36 capturas adjacentes idênticas ao commit anterior. Evidências anteriores conservam seu escopo/commit; não reutilizar24 testes como gate desta revisão.

Jornada nativa repetida após4b1a475: [readback atual](evidence/spec023-critical/native/native-readback.json) e [capturas](evidence/spec023-critical/native). Uma Order/pagamento CASH600, Tab CLOSED/saldo0, caixa600/600/diferença0. Histórico anterior não sobrescrito. Contratos75669e6 e implementação4b1a475; pagamentos MANUAL_TEST, API8144/PostgreSQL55523 reais, emulador API36.

## Continuação10/10 — pendências da demo

[Resultado atual e reprodução](spec023-refund-validation.md): diálogo de estorno corrigido após baseline real de clipping/PIN inacessível;54instrumentados/51unit/build/lint. Web final197visual13PostgreSQL12auth/realtime/types/build. [Tickets](spec023-tickets-review.md): experimento descartado, referência/hash e composição anterior conservados. Relatórios anteriores conservam seus commits; serviços anteriores encontrados parados nesta execução, banco demonstrativo55459 não reiniciado nem alterado. API/dispatcher próprios8144/cluster55523 e dados anteriores preservados.

Estorno nativo real10/10 aprovado: [readback](evidence/spec023-refund/native/native-refund-readback.json). Recebimentos900, estorno300, charges600, exposição0; pagamento original preservado, auditoria/movimento de caixa, caixa600/600/diferença0. Essa pendência específica V05 está atendida; demais limites globais continuam discriminados no relatório atual.
