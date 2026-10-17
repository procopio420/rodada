# Correções de apresentação Compose — Spec033

Referência: PR212, `prototype/ux-2-0/index.html` em `ec26e26b164692b1e22e0fc1b7c7c45d401a7ca0`. Comparação anterior: PR231.

Delta de apresentação:

- Cardápio: referência de consumo em duas colunas (usado/referência e capacidade), legenda e projeção na mesma linha, perfil Regular e ação em âmbar. Mantidos valores canônicos e bloqueios existentes.
- Resumo: destino com acento lateral, total horizontal; editar configuração aparece somente quando produto aceita variantes/modificadores.
- Recebimento: caixa único aberto continua selecionado por seu ID canônico; seu metadado fica abaixo do valor e ações. Vários caixas ainda exigem seleção explícita. Terminal externo e condições ficam em divulgação secundária após as ações; avisos de simulação Pix aparecem quando relevantes.

Fixtures de apresentação: Marina/Mesa08, exposição56/limite200/draft14 com os mesmos oito produtos do protótipo; recebimento Marina/Mesa08/saldo24. ID da Tab é uma fixture explícita, não inferido da mesa. Capturas de teste Compose são isoladas e não provam shell, API ou liquidação real. Diferenças de referência canônica e indisponibilidade de PSP não estão implicitamente aprovadas.

Fonte final: `a7298ee2` (inclui correção de revisão P2: observações/configurações restauradas mantêm edição). Controles pintados conforme protótipo: categorias40dp; quantidade39×42dp; detalhes36dp/compacto28dp, com alvo nativo mínimo e teste de toque fora da pintura. Categorias preservam ordem recebida; cabeçalho informa contagem real filtrada. Fonte200% adapta crédito para preservar legibilidade.

Execução: `ANDROID_HOME=/home/lucas/Android/Sdk JAVA_HOME=/home/lucas/.local/share/mise/installs/java/17.0.2 ./gradlew testDebugUnitTest assembleDebug lintDebug assembleDebugAndroidTest` no diretório Android; `python docs/development/evidence/spec033-native-parity-fixes/run-matrix.py` na raiz. O runner usa exclusivamente emulator-5558 e restaura dimensões/fontes no finally.

Validação final e hashes em manifest.json. As capturas são fixtures isoladas: sem shell, backend, PSP ou prova de liquidação. Sem aparelho físico, sem aceite global de paridade, sem merge/deploy. Tipografia/renderização nativa, espaços do sistema e os fluxos completos ainda precisam de comparação integrada; estas evidências não aprovam diferenças intencionais nem encerram épicos.
