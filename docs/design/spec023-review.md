# Spec 023 — integração e navegação acessível

## O que foi adiantado

A branch codex/spec023-review reúne as entregas V01–V05 anteriormente isoladas. Base origin/main 742faac639adc998f3a4da6d8af485b407317851; branch original codex/ux-operational-polish em 6e2f4ca preservada e já sincronizada com origin. Conflitos eram acréscimos concorrentes de documentação e o fim do CSS: preservados todos os contratos e ambos os estilos Field confortável/stationOrder. Não houve merge em main.

A descoberta adicional foi visual/funcional: no Android de 360 px com fonte 200%, Contas quebrava e ficava cortado. [Antes](evidence/spec023-review/before/nav-now-w360-f200-0.png) e [depois](evidence/spec023-review/after/nav-now-w360-f200-0.png). Para fontScale >1.3, barra passa a 112 dp e centro 104 dp, com ícone Pedir acima do label; labels laterais usam lineHeight 16 sp. Não se reduz a fonte escolhida pelo usuário. Font scale normal mantém altura 84/centro136, com captura 390 px byte-idêntica à V05 original.

Os dois testes instrumentados existentes foram ampliados, sem criar um fluxo de UI paralelo: verificam geometria, alvos, seleção, callbacks, busy e contenção das linhas de texto. A captura repete duas vezes e exige bytes iguais. O flag hasVisualOverflow foi diagnosticado como inadequado neste runtime: reportava largura do container de parágrafo (128) contra tamanho medido do texto Agora (99), apesar de o desenho caber. O teste definitivo verifica diretamente left/right/top/bottom de cada linha contra o tamanho do texto, usando floor/ceil de pixel e nenhuma tolerância adicional. A evidência visual anterior registra o problema real; esse detalhe do harness não é tratado como fidelidade do produto.

O gate local agora valida a resolução efetiva (override prevalece sobre física), fonte solicitada e descarta apenas XMLs gerados anteriormente antes da execução. Exige exatamente dois testes atuais, zero falhas/erros/skips; sucesso do Gradle sem testes não é suficiente.

## Checks do conjunto

- Web typecheck e build padrão: passaram.
- Web visual: 160 testes passaram; realtime: 8 passaram. Field V02 e tickets V04 coexistem; Cozinha/Bar e superfícies adjacentes mantêm gates existentes.
- Android unitários existentes: 38 passaram; assembleDebug e lintDebug passaram.
- Android API36: seis configurações 360/390/430 px × font scale 1/2, dois testes em cada configuração; total 12 execuções sem falhas/skips. [Resultados](evidence/spec023-review/android-matrix/results.json).
- Captura canônica 390/fontScale1 preservada: SHA256 61d418c01cbc542749e6038326bddf5f785ae1ecb10e23af7c2da97742880011.
- Evidências anteriores auditadas: 137 entradas dos cinco manifestos, todas válidas. V01 recebeu .gitattributes e os bytes LF originais de dois JSONs foram restaurados, evitando conversão automática CRLF no checkout. Os hashes e o conteúdo histórico foram preservados; não se substituiu referência para esconder diferença.

Logs, PNGs de cada configuração, ambiente, XMLs e hashes ficam em [evidências integradas](evidence/spec023-review/sha256.json). A integração não alterou contratos da API, disponibilidade, pedidos, transições individuais, pagamentos ou ledger. Fixtures continuam restritas a testes.

## Limites e próximos ajustes pequenos

V01–V05 globais permanecem abertos. A comparação de tickets ainda diverge 16,6898%; a navegação canônica ainda diverge 1,746% em pixels entre HTML/Android. Esta entrega resolve fonte ampliada, não reduz esses números por baseline novo ou máscara. Dados canônicos ausentes de cliente/localização/SLA continuam ausentes.

A fonte ampliada foi verificada somente na navegação. Header e telas internas, safe areas no app autenticado, teclado, API mínima26 e device físico continuam pendentes. Native screenshot regression CI e baseline nativa total ainda não foram aprovados. Android local usa JDK21 disponível com source/target17; CI é evidência separada.

Próximos recortes úteis: header/safe areas com fixture real de sessão; medir tipografia variável por região; posicionamento do aviso de conectividade da Cozinha. Todas essas mudanças precisam do contrato correspondente antes do código.
