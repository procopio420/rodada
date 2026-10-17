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
