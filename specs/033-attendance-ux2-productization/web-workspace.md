# E01/E02 — workspace de páginas fiel à UX2

Contrato033/PR216, adendo do responsável16/10:PR212ec26e26b define organização
visual e jornadas. Este slice substitui a apresentação029 por páginas de comanda,
cardápio e resumo opcional quando presentation=ux2, preservando o controller
OrderWorkspace,useOrderIntent,drafts porTab e validações canônicas. POS e modo
legado continuam disponíveis para rollback de apresentação.

Comanda → Adicionar itens → lista/categorias/quantidades → Enviar direto.
Voltar retorna ao estado anterior; draft nunca soma ao saldo. Resumo mostra todas
linhas apesar de filtros. Personalização obrigatória preservada em diálogo curto;
configurações distintas não se fundem. Resultado desconhecido bloqueia edição e
novosenvios, oferecendo somente intenção original. Repetição usa editor existente.

API navigation:requestedSurface(tab/bill/catalog), addItemsRequest contador e
onContextChange para shell. TableSelection permanece canônica. Navegar não muta.
Conta/recebimento do E04 e barra E05 dependem seus slices; nenhumAC inteiroPASS
sem jornada integradaWeb/Compose e comparação360/390/430.
