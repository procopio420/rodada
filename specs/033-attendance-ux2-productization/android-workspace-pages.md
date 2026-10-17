# E01/E02/E05 — páginas nativas da comanda

Contrato incremental PR212: home Comanda abre explicitamente Adicionar itens;
catálogo com busca/categorias e quantidades inline envia direto pelo callback
existente. Resumo é opcional e independente dos filtros. Conta preserva a
superfície financeira existente neste recorte. Back percorre catálogo/resumo/home,
sem perder drafts por Tab e sem sair durante intenção pendente. requestedSection
é consumido uma vez. Repetição usa reviewRepeatedOrder/selectedRepeatedLines,
seleção por quantidade (zero exclui) e callback canônico existente.

Limite/exposição usam projeção canônica já disponível, sem política nova.
Perfil só aparece se relationship_snapshot canônico estiver disponível; não
inferir relacionamento de nome/consumo. Draft não soma ao saldo confirmado.

Aceite do recorte: home/catalog/review em Compose, callbacks e UUID originais,
sem edição durante pending; targets >=44dp, Archivo normal/JetBrains e tokens
PR212, fontScale2 com scroll. JVM/build/lint/compile de instrumentação; pixels
360/390/430 e runtime são gates separados, não presumidos por build.

## Retomada 17/10/2026

Implementação: `Ux2TabPages` concentra home/catalog/resumo/repetição nativos;
`TabWorkspace` encaminha páginas e preserva Conta existente. Intenções, drafts,
callbacks de envio, UUID e motores financeiros permanecem os existentes.
`relationship_snapshot` é lido do servidor; ausência não gera perfil inferido.
Barra mostra limite/exposição/capacidade canônicos e draft separado. A política
ENFORCE existente continua bloqueando envio acima da capacidade; não há WARN_ONLY
inventado. Resumo independe de filtros e quantidade zero exclui repetição usando
`selectedRepeatedLines`. Back retorna resumo→catálogo→home e Conta→home.

Gates deste recorte: testes JVM/build/lint/compileAndroidTest em execução;
novo teste comportamental `Ux2TabPagesTest` cobre resumo após filtro sem resultado
e intenção pendente bloqueando edição com replay pelo callback original.
Execução instrumentada, capturas 360/390/430/fontScale2, comparação visual com
PR212 e revisão R3 independente permanecem PENDENTES até evidência real. Os testes
históricos que assumem abertura direta de catálogo precisam adaptação ao contrato
home-first; não se declara suite instrumentada inteira aprovada.

### Revisão do freeze 3cf374e8 — CHANGES_REQUESTED

Root identificou divergências visuais: barra Material3 sem marcador/segmento de
rascunho, posição da barra no resumo, layout das linhas e status cru de itens.
Correção em andamento: Canvas nativo com marcador 80%, segmento listrado do draft,
excedente textual e header compacto home; catálogo usa nome/preço à esquerda e
quantidade à direita; resumo mostra total antes da barra; histórico usa ID real
e status localizado. DTO lê estação snapshot opcional, nunca Product atual.
Dependência API: PR219 `5c4eaef6` já expõe `fulfillment_station_snapshot`; API18131
usada durante matriz anterior ainda não compõe esse contrato. Ausência do campo
mostra destino não informado. Não foi alterado backend neste recorte.

Gates do freeze 3cf374e8: `ANDROID_HOME=/home/lucas/Android/Sdk ./gradlew
testDebugUnitTest assembleDebug lintDebug compileDebugAndroidTestKotlin --stacktrace`
terminou BUILD SUCCESSFUL (102 testes JVM, zero falhas/errors/skips). Este resultado
NÃO valida as correções posteriores nem substitui paridade reprovada.

### Gate local das correções — 894785b9

Em 17/10/2026, comando `ANDROID_HOME=/home/lucas/Android/Sdk ./gradlew
testDebugUnitTest assembleDebug lintDebug compileDebugAndroidTestKotlin
--max-workers=1 --stacktrace` terminou BUILD SUCCESSFUL em 3m36s.
XML JVM: 102 testes, zero falhas/errors/skips. APK debug montado; teste Android
compilado, ainda não executado. Depreciação de createComposeRule permanece warning.
Esse gate não aceita paridade visual, jornada real, API composta nem revisão R3.
Runtime5558 permaneceu com Matrix durante o build; nenhuma instalação ocorreu.

### Correções P1/P2 após revisão independente

- P1: verificar intenção pendente usa callback próprio ligado ao
  `revalidateConnection(session)` existente (readback canônico → fila durável →
  reconciliação). Não passa por `confirmOrder`, que exige draft não vazio;
  repetição ambígua com cart vazio continua verificável, sem criar intenção nova.
- P2: holder interno em TabWorkspace conserva os estados de Ux2TabPages quando
  Conta ocupa a composição. Home/catalog/resumo mantêm scrolls separados.
  Regressão cobre catálogo→home→Conta→home→catálogo, query e categoria.
- Primeiro runtime360/font1: 3/4 testes passaram; teste A/B/A falhou na asserção
  textual do campo vazio porque a semântica inclui placeholder. Corrigida para
  `EditableText`; falha e nova execução permanecem registradas, sem apagar prova.
