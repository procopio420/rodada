# Spec023 — campos críticos Android

Continuação validada depois do commit36f751b, em base isolada de main45c4742. Contratos foram registrados na spec/plano/tasks/aceite e design system antes das correções. Este recorte atende legibilidade V02, jornada V05, contratos responsivos/acessibilidade e gate V07; não encerra a Spec023.

## Diferenças comprovadas

- Catálogo360/font200: nome truncado e preço comprimido em caracteres verticais. Componente de produção reutiliza o botão/tokens existentes; nome completo e preço formatado em centavos têm linhas próprias. Routing, disponibilidade, busy, variantes/modificadores e callback conservados.
- Pagamento360/font200: conteúdo cortado e decisões sobrepostas. Conteúdo agora permite rolagem interna; fonte>1.3 usa decisões verticais. Confirmar conserva as mesmas condições de valor/caixa/busy; Cancelar mede pelo menos44dp nas duas variantes.
- Login com IME real aberto: Entrar inacessível. Rolagem habilitada somente enquanto o teclado está aberto; sem teclado, a geometria existente é preservada. Trim, limpeza do PIN, busy e autenticação conservados. login-before registra hipótese inicial de scroll sem clipping: não é prova de defeito. A prova efetiva está em login-keyboard-before.

## Validação atual

[Resultado estruturado](evidence/spec023-critical/checks.json): 51 testes unitários; build e lint aprovados; 8 testes instrumentados ×6 combinações =48, zero failures/errors/skips. API36, density160, altura844; larguras360/390/430 e fontes100/200%. Gate descarta XML gerado antigo, exige contagens exatas e IME real ativado no emulador separado. Não houve mudança de tolerância ou aceite de baseline para ocultar diferenças.

[Antes e depois](evidence/spec023-critical): 24 capturas finais de catálogo/pagamento/login/login com teclado. Cada captura foi repetida e exigida idêntica em bytes; screenshots de login precedem digitação de credenciais. Captura com teclado mostra viewport inicial; teste rola até Entrar, executa callback e verifica PIN limpo. Advertência de caixa é acessível por scroll, confirmação permanece desabilitada sem turno; fixture de caixa ativo envia exatamente300centavos/CASH/ponto original. Fixtures de componentes pertencem exclusivamente a androidTest.

Cabeçalho e navegação adjacentes: 36 capturas atuais coincidem byte a byte com a evidência anterior; testes funcionais também executados em todas as combinações. Isto comprova ausência de regressão nessas regiões, não paridade integral do Android.

## Reprodução e limites

Definir runtime Android e ANDROID_SERIAL do emulador isolado API36; configurar wm size largura×844, density160, font_scale1.0/2.0 e show_ime_with_hard_keyboard=1. Executar scripts/android-navigation-check.ps1 para cada combinação. Não usar hardware do operador. Para jornada integrada usar build com API10.0.2.2:8144 e scripts/spec023-native-demo.py no cluster de testes55523; readback usa --out para conservar evidências históricas.

Web não mudou neste recorte Android: gates Web197visual/13PostgreSQL/12auth-realtime, typecheck e build pertencem aos conteúdos descritos no relatório integrado e aos commits anteriores. Android CI executa unit/build; lint e instrumentação são locais. Hardware, provider, estorno nativo, todas as jornadas internas em fonte200% e paridade global continuam sem comprovação. V03tickets ainda apresenta diferença medida16.241%; próximo recorte é sua composição, sem refazer o acabamento compartilhado.

## Jornada real e versionamento

Build Android com API10.0.2.2:8144 instalado após a matriz. [Evidências nativas atuais](evidence/spec023-critical/native): login/Agora/Conta/Pico → nova Tab de teste → produto existente QA Wrong item → pedido600centavos → bloqueio sem caixa → abrir caixa0 → receber CASH600 → fechar Tab → contar600/fechar caixa. [Readback PostgreSQL real](evidence/spec023-critical/native/native-readback.json) confirma exatamente1Order, charges600,1CASH CONFIRMED600, ator/timestamp, nenhuma correção/estorno/provider; Tab CLOSED/exposição0 e caixa CLOSED/esperado600/contado600/diferença0. Pagamento MANUAL_TEST; cluster55523 separado do banco55459.

O roteiro encontrou CONTAS ausente ao sair do diálogo dentro da Tab; passou a usar o controle observado ← Comandas. Continuação retomou a mesma Tab; não repetiu pedido nem pagamento. Scroll do harness usa viewport observado no XML, inclusive o diálogo, sem gesto fixo dependente da tela. Nenhuma mudança de produto por falha do harness.

Contratos75669e6; implementação4b1a475. Relatórios e evidências publicados em commit separado, preservando baseline e gates falhos como diagnóstico. CI remota é consultada por head; instrumentação/lint seguem evidência local. Branch original6e2f4ca e serviços3119/18764/3123/8123/55459 rechecados e preservados. Sem merge, force push ou produção.
