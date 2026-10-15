# Port Android nativo — evidência local

Base: `codex/ux-teste-mobile` em `47043184408c090ddae33df17d4d72010603f764`
mais diff local. Mudanças Web/API preexistentes preservadas. Nenhum commit,
push, merge ou deploy nesta tarefa.

## Implementação

- Entrada Mesas e comandas: grade, busca/filtro, expansão contextual, outras Tabs
  e criação explícita. Reutiliza comandos e confirmações de mesa existentes.
- Janela Compose nativa com Cardápio/Pedido atual/Conta; filtros não escondem
  linhas do pedido; saldo vem exclusivamente da API. Sem WebView.
- Drafts em memória por Tab/sessão, com identidade/configuração da linha;
  intenção cifrada prevalece sobre draft e não é alterada por navegação.
- Back consulta registros atuais; bloqueio de operação ambígua não depende de
  cache de badges. Correção/estorno têm caminho explícito para a consulta original
  sem replay nem remoção de registro. Estado ilegível bloqueia com erro.
- A grade usa uma coluna com fonte ampliada. Produto conserva fallback genérico
  da Web; carregamento de assets ProductIcon publicados não foi adicionado.

## Validação incremental

Primeiro recorte: build/JVM/lint PASS. Após ajustes, 87 JVM PASS. Rodada Compose
390dp/fontScale1: 18 testes, dois pares de screenshots divergiram com animações
do sistema ativas. Reexecução com animações desativadas: **18 PASS**, preservando
assert de igualdade exata. Sem substituição de baseline nem relaxamento do teste.
Esses resultados são incrementais; execução do snapshot final registrada abaixo.

Revisão independente pela skill `rodada-code-review`: `NO_FINDINGS_WITH_GAPS`
após corrigir três cenários de bloqueio de navegação e tratar storage ilegível.
Revisor não executou testes; isso não é aprovação GitHub nem homologação.

## Ambiente e continuidade

Emulador de teste Pixel 10/API36. Banco local existente foi retomado sem reset,
migration ou seed após os serviços terem parado. API ASGI em localhost:8000;
dispatcher separado; adb reverse device8000 → host8000. Sem operação financeira
real ou alteração de domínio. Dados/credenciais não fazem parte desta evidência.

## Snapshot final validado

| Gate executado | Resultado |
| --- | --- |
| `assembleDebug assembleDebugAndroidTest testDebugUnitTest lintDebug` | PASS; 88 JVM, zero falhas/erros/skips |
| Compose 390dp / fonte 1 | 19 PASS: navegação, fluxos, histórico, mesa, conta, repetição e proteções |
| Compose 360/430dp / fonte 1; 360/390/430dp / fonte 2 | 3 PASS por combinação; 15 execuções PASS |
| Leitura real opt-in `NativeDraftReadbackTest` | 1 PASS, sem skip: drafts A/B/A com notas/IDs originais e pedidos canônicos inalterados |
| Capturas determinísticas / inspeção | Igualdade exata mantida; catálogo 360dp/200% e mesas 390dp inspecionados |
| `git diff --check` | PASS |
| Runtime final | App instalado/aberto, Mesas e comandas e ONLINE; readiness API 200 |
| Jornada real pelo ADB | Tab existente abriu após leitura canônica no Dialog; Back nativo retornou à lista, sem criar itens ou receber valores |

Executados pelo runner local `visual-artifacts/android-native-port/run-native-port.ps1`.
Logs finais separados em `visual-artifacts/android-native-port/final/`: build,
seis arquivos Compose, `matrix.json`, `read-only-drafts.log` e `manifest.json` com
SHA256 do APK e dos seis arquivos centrais de implementação. São artefatos locais
ignorados, não uploads de CI nem evidência remota. As rodadas incrementais anteriores
continuam preservadas fora de `final/`.

Dimensões físicas 1080x2424/densidade420, fonte1 e animações normais restauradas.
Nenhuma confirmação de pedido/pagamento/limpeza/liberação foi enviada à API pelo
ensaio real; as jornadas mutáveis Compose usam callbacks de fixture.

Decisão: TESTADO_LOCAL para o port de fluxo; pronto para teste humano no emulador,
sem GO de produção. Próximo responsável: operador revisar o fluxo instalado;
aprofundar IME/TalkBack, leitura negada, perda real de POST e assets publicados
antes de alegar paridade visual/global ou homologação.

Limites: TalkBack, aparelho físico, provider, morte de processo para drafts não
submetidos, homologação com operador e produção não demonstrados. Recovery cifrado
existente não foi reimplementado; fluxos financeiros reais não foram executados.

## Tela de mesas Android alinhada — 2026-10-15

Base: codex/ux-teste-mobile @ 54c57808cec0098be2934faa964dd6dd9cd5b41d + diff local.
Escopo R2 de apresentacao: TablesScreen, AttendanceHeader/Navigation e posicionamento
da navegacao em AttendanceScreen. Sem alterar ViewModel, API, permissoes, recovery,
pagamentos ou dados. Spec/plan/tasks/design system/README atualizados.

Resultado: navegacao no topo, destino ativo Paper/Ink, nome canonico do Venue,
fundo Ground e painel Surface, busca sem filtros, historico compacto e outras
comandas recolhidas. Cartoes Control com titulos Paper, icone e borda superior
semantica verde/azul/amarela/vermelha; texto de estado/contagem permanece.
Mesas abrem TableCard em Dialog rolavel com os callbacks e confirmacoes existentes.

| Gate final executado | Resultado |
| --- | --- |
| assembleDebug / assembleDebugAndroidTest / testDebugUnitTest / lintDebug | PASS; 89 JVM, zero failures/errors; lint zero errors, 9 warnings e 2 hints |
| Compose390/fonte1 | 15 PASS: apresentacao/estados, fluxo, cabecalho, navegacao, liberacao e servico |
| Compose360/430 fonte1, 360/390/430 fonte2 | 6 PASS por combinacao; 30 execucoes PASS |
| A/B/A real opt-in somente leitura | 1 PASS, sem skip; pedidos canonicos antes/depois iguais |
| App real | ONLINE; popup da Mesa 2 abriu e Back retornou sem executar comando |
| git diff --check | PASS |

Evidencia final local ignorada: visual-artifacts/android-native-port/web-align-verified-build.log,
web-align-final-*-f*.log, web-align-readonly.log, android-web-aligned.png,
android-table-popup.png. Capturas deterministicas dos cinco estados em
/data/local/tmp/rodada-critical-evidence no emulador; nenhum estado real de mesa
foi mudado para produzir a evidencia. Screenshot de estados fonte1 anterior ao
ultimo ajuste de contraste preservado em status-colors390.png.

Falha intermediaria em fonte200: performScrollTo no item virtualizado nao trouxe
a ultima mesa para a viewport. Diagnostico salvo em status-layout-failure.png;
teste usa agora performScrollToNode na LazyColumn e conserva assertIsDisplayed
para cada cartao, sem reduzir os criterios. Matriz completa final PASS.

APK instalado com install -r preservando sessao/dados. Emulador restaurado para
size/density normais, fonte1 e animacoes normais, reverse8000 -> host8000. API200.
Nao houve seed/reset/migration, pedido confirmado, pagamento, commit/push/merge/deploy.
GO para teste humano local desta tela. Nao e paridade visual/global de Android:
categorias/assets ProductIcon do catalogo e funcoes de Conta continuam com as
limitacoes ja documentadas. TalkBack/aparelho fisico/fornecedor/producao e suite
Web integral nao executados; Web nao foi alterada nesta slice.

## Correcao de rota e recuperacao local — 2026-10-15

Bug reproduzido: openFirstTableTab preserva intencao service/open-tab, mas a
allowlist OperationsHttpClient.tableService aceitava apenas service/start para
mesas. require falhava antes do HTTP e mantinha pendingTableService, bloqueando
navegacao. Corrigida somente a regex para service/(start|open-tab).
Regressao JVM com HttpServer loopback real: antes FAIL IllegalArgumentException;
depois PASS, dois envios com mesma rota/corpo/chave e rotas alheias rejeitadas.
Build/90 JVM/lint PASS; git diff --check PASS. Nao muda autenticacao/API/backend.

Revisao independente R3 /root/review_table_route (contexto separado) sobre
HEAD54c57808 + patch exato: NO_FINDINGS_WITH_GAPS. Revisor somente leitura nao
executou testes; nao equivale a aprovacao GitHub nem GO de producao.

APK corrigido instalado com -r, storage preservado. Recuperacao mutavel foi
inicialmente bloqueada pela revisao automatica; nenhum clique ocorreu nessa
tentativa. Apos autorizacao explicita do operador para concluir a intencao original,
executado Verificar mesma intencao, sem apagar registro/gerar nova chave.
Contagens locais antes/depois: Tabs9->10, ocupacoes8->9, comandos start_open2->3.
Readback identificou exatamente a nova Tab OPEN, zero pedidos. UI abriu a comanda,
aviso pendente sumiu, ONLINE voltou; Back retornou, toque na Mesa2 abriu popup,
confirmando interacao desbloqueada. Sem pagamentos/pedidos/seed/reset/migrations.

Logs locais ignorados: service-route-regression-before.log, service-route-fix-build.log,
recovered-tables.xml e recovered-popup.xml em visual-artifacts/android-native-port.
A recuperacao real concluiu a tentativa que o operador havia iniciado; nao e
um ensaio backend completo de dupla entrega/ACK perdido. Suite de UI integral
nao reexecutada nesta correcao de uma linha. Sem commit/push/merge/deploy.
