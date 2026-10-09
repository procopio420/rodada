# V05 parcial — navegação inferior do Atendimento

## Entrega

Componente AttendanceNavigation integrado à tela real. Barra Agora/Pedir/Contas segue o contrato geométrico do export night: 390×84 dp, laterais 127×75 e região central 136 dp, com botão útil 128×63. Ícones, marcador ativo, radius e spacing vêm das medidas documentadas. Seleção usa semântica de Tab; busy mantém Pedir desabilitado. Os callbacks existentes continuam abrindo comanda e selecionando as mesmas seções. Não foi alterada API, viewmodel, autorização, ledger, confirmação de pedido ou pagamento.

Mesas e Caixa permanecem em extensão acima da região canônica; Caixa respeita a capability anterior. SafeDrawingPadding continua no AuthApp, sem insets duplicados. O shell completo, header e telas internas ainda não foram reproduzidos nesta entrega.

[Contrato anterior ao código](v05-atendimento-shell-contract.md). Spec/plano/tarefas/aceite e design system atualizados antes da implementação. Sem alteração Web ou reaplicação das branches V03/V04.

## Base

Origin/main conferida via fetch: 742faac639adc998f3a4da6d8af485b407317851. Worktree isolada codex/v05-atendimento-shell. Branch do usuário codex/ux-operational-polish preservada em 6e2f4ca4f386f6ee54325cbff2fdf09b05bef597. Sem merge/push/publicação.

## Comparação

Fonte original prototype/references/night/Main.dc.html preservada. Captura literal inclui os cantos arredondados da moldura do telefone. Para comparar apenas a UI, a captura derivada remove somente border-radius da .phone em memória; fonte e estilos .nav/.nb/.ngo permanecem intactos. Não houve resize, máscara ou troca pela imagem da aplicação.

No emulador API 36 x86_64, display 390×844, densidade 160 e fontScale 1, cada dp corresponde a um pixel físico. A instrumentação renderiza o mesmo composable usado por produção; dados demonstrativos e callbacks locais ficam exclusivamente em androidTest.

[Referência/aplicação lado a lado](evidence/v05-atendimento-shell/nav.pair.png), [diff](evidence/v05-atendimento-shell/nav.diff.png), [estatísticas](evidence/v05-atendimento-shell/nav.stats.json). Em 390×84, pixelmatch threshold 0.1/includeAA false registra 572 pixels diferentes (1,746031746%). Essa métrica é diagnóstico entre plataformas, não um gate aprovado nem uma tolerância ampliada. Geometria principal comprovada; detalhes de glifos, baseline/linha e desenho de ícones/sombra ainda precisam de análise por região. Não atribuímos toda diferença automaticamente à rasterização.

Capturas Agora e Contas/busy repetidas foram byte-idênticas, com assertion no teste e hashes retidos. Ambos os estados foram abertos e revisados visualmente. Contas/busy e os controles Mesas/Caixa formam a verificação adjacente deste recorte; nenhuma jornada completa foi declarada verificada.

## Checks

38 testes unitários existentes passaram (zero falhas/erros). Dois testes instrumentados passaram (zero falhas/erros/skips). AssembleDebug e lintDebug passaram. Evidências: [log final](evidence/v05-atendimento-shell/android-verified.log), [XML nativo](evidence/v05-atendimento-shell/instrumentation.xml), [unitários](evidence/v05-atendimento-shell/unit-results.json), [ambiente](evidence/v05-atendimento-shell/environment.json), [hashes](evidence/v05-atendimento-shell/sha256.json).

Runtime disponível Microsoft JDK 21; source/target Java 17 preservados. Portanto o comando foi validado com JDK 21, não há alegação de execução local em JDK 17. Dependências novas de screenshot/runner ficam em androidTest/debug; variante release não recebe fixture.

A primeira instrumentação API 37 falhou por InputManager.getInstance ausente no runner. API 36 foi provisionada conforme a referência de ambiente do projeto. Uma tentativa antes do boot não executou testes apesar de Gradle indicar sucesso; o novo script exige boot concluído e XML com exatamente dois testes executados e nenhum skip. A captura inicial após cliques incluía ripple; a fixture agora captura estado estável antes das ações e espera o relógio/idle, mantendo assertion de bytes idênticos. A retenção de PNGs usa stdin do shell via [UiAutomation.executeShellCommandRw](https://developer.android.com/reference/android/app/UiAutomation#executeShellCommandRw(java.lang.String)) e verifica a gravação; não depende de dados que AGP remove ao desinstalar o APK de testes.

## Reprodução e limites

Com API 36 já iniciada em 390×844/dpi160, JAVA_HOME/ANDROID_HOME/ANDROID_SERIAL configurados: executar scripts/android-navigation-check.ps1 da raiz. O script exige configuração canônica e execução real dos dois testes. Retirar /data/local/tmp/rodada-v05-evidence para visual-artifacts/native/rodada-v05-evidence. Com servidor estático local em 3151 e node_modules Web disponíveis, scripts/android-navigation-reference.cjs captura HTML; scripts/android-navigation-compare.cjs gera par/diff/stats sem alterar thresholds.

Device físico, API mínima 26, teclado/fontes ampliadas e UI real autenticada com backend não foram verificados. Não existe baseline nativa visual aprovada; o gate atual cobre geometria/comportamento/estabilidade deste componente. Próximos recortes: medir fontes variáveis e baselines por label, completar header/regiões/safe areas contra o telefone e então Agora interno com fixture canônica. V05 global continua aberta.
