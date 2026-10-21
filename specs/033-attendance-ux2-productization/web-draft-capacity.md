# E02-05 — capacidade de configuração no editor UX2

Na composição `b06d2774`, o teste de 60 unidades simples e 40 com observação
identificou que remover a observação tenta reunir 100 unidades. A guarda local
impede alterar o draft, mas seu erro fica atrás do diálogo modal; a página UX2
não fornece validationQuantity/quantityCapacity ao ProductCustomization existente.
Reutilizar essa validação para desabilitar o commit e mostrar o motivo dentro do
diálogo, preservando 60/40 e sem POST. Aumentar linhas do resumo também deve
respeitar a soma por produto/configuração, como o catálogo e o draft legado.
Não altera preços, ledger, pedido confirmado, idempotência ou limite financeiro.

Regressão: personalização inválida permanece no diálogo; reduzir/aumentar não
cria configuração com mais de 99 unidades. Migrar jornadas visuais da Spec029
para páginas033 preservando asserts de payload/replay/fences/limpeza. Liberação
exige Tabs fechadas, ocupa geração capturada; limpeza é start→complete explícito.
O teste de alvo da barra usa o verificador comum de 44px e hit ownership real,
sem confundir dimensões pintadas com a extensão interativa já contratada.

A migração também reproduziu perda de foco em Mesa→Tab→catálogo→Voltar:
o DOM da linha original é desmontado durante a página da Tab. O retorno deve
resolver novamente o botão pelo Tab.id após o refresh, sem focar o nó removido,
sem escolher por label e sem navegar/mutar automaticamente. Validar A→B→A com
rascunhos separados e foco na linha correspondente após o retorno.

O comando contextual “Abrir e pedir” também voltava à home da Tab, adicionando
um toque indevido. Após readback do comando de abertura (inclusive replay da
intenção original), entrar no catálogo da Tab retornada. Outros comandos que
retornam tab_id conservam seu destino de comanda; identificar o caso pela rota
canônica original, sem alterar envelope, UUID, payload, sessão ou ledger.
