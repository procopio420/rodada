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
