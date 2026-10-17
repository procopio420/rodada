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

## Incremento de página de repetição e recuperação — 2026-10-17

Código base fa1af74b: a apresentação UX2 de Mais uma rodada usa página com
quantidades zero para excluir, ações +/- e envio direto, mantendo o motor
reviewRepeatedOrder/selectedRepeatedLines e useOrderIntent. POS mantém diálogo.
A fixture de ACK perdido agora aguarda autenticação visível antes de criar Tab
pela rota Attendance (401 anteriores eram preparação prematura da fixture).

Validação final: build passou; Playwright visual attendance-ux2-workspace.spec.ts
13/13 em 30,1s (360/390/430/1280, seleção repetição e destinos/recovery);
Playwright integration mesmo arquivo 5/5 em 29,8s com Django e PostgreSQL 17.6
local isolado porta55634. Perda de ACK após commit, reload e replay comprovam
mesmo payload/chave, Order único, exposição1500 e nenhum Payment.
Capturas ignoradas em visual-artifacts/033/ux2-repeat-{width}.png.
Estes testes não comprovam paridade Android, revisão independente da nova página,
suíte completa nem aceite final. PR deve permanecer draft enquanto esses gates
estiverem pendentes. Dependências: #218/#219/#221; identidade autorizada adicional
em #222. Nenhum merge/deploy autorizado ou executado.

## E04 integração em branch separada — 2026-10-17

Branch impl/033-web-account, dependente de #224: PosCashReceipt existente recebe
opt-in Attendance, envelope v2 com gateway original e fase Payment persistida
antes de Close; callback lê Tab exata. Componente permanece montado sem Tab para
recuperação. Pagamento parcial permanece disponível com rascunho; recebimento
integral/encerramento desabilitado com rascunho. Saldo zero usa Close existente.
Backend continua autoridade de cash.shift/capability. Apenas CASH efetivo.

Build passou e integração pos-cash-receipt.spec.ts passou 5/5 em29,7s usando
Django/PostgreSQL17.6 porta55634, incluindo: POS legado ACK perdido, Payment/Close
com ACK perdido/reload, capability negada, consumo concorrente após Payment
seguido de manter aberta sem mutação extra, e jornada inicial UI Attendance
parcial500+integral1500=2000, dois Payments, Tab CLOSED e envelope retirado.
A revisão independente anterior encontrou bloqueio de saldo concorrente e foi
corrigida em473a8e93; nova revisão da correção/integração permanece pendente por
indisponibilidade do executor independente. Nenhuma alegação R3 aprovado.
Paridade da página de pagamento, screenshots e CI deste novo SHA pendentes.

Validação adicional f620ee60: build PASS e Playwright visual workspace+cash receipt
24/24 em48,5s. Inclui sessão alterada/revogada nos schemas1/2, storage corrompido/
indisponível, conflito fingerprint após5xx, readback ausente e repetição nos4tamanhos.
Main fb3ea55d (somente instruções/KB) e correções de CI #224 integradas semconflito.
Testes visuais aqui não são aceite de paridade da nova página de pagamento.

## E04 ciclo de limpeza explícito

A tela anteriormente oferecia complete em DIRTY; agora chama cleaning/start e
aguarda readback CLEANING antes de oferecer cleaning/complete. Nenhum timestamp
é sintetizado no cliente; API existente permanece compatível com clientes antigos.
Teste visual específico PASS1/1(4,9s); integração real PASS1/1(13,2s), antes do
acréscimo final de verificação de timestamps/atores. Fixture inicial sem ocupação
liberada foi rejeitada corretamente pela API; corrigida para representar ocupação
realmente liberada. Nova execução conjunta valida também timestamps e autoria.
Dependências API #218/#222 integradas na branch para testes do contrato completo;
sem merge dessas PRs na main. #225 continua draft, sem aceite de épico/paridade.

Execução conjunta após API #218/#222:10/11 PASS, incluindo limpeza com timestamps
released_at<=cleaning_started_at<=ready_at e atores reais. ACK perdido falhou apenas
na leitura imediata do envelope ainda em limpeza assíncrona após readback; passou
em reexecução1/1(13,5s) aguardando término com expect.poll. Identidade/payload,
Order único, exposição1500 e ausência de Payment continuam assertados. Não relatar
execução conjunta como11/11; evidência é10PASS+reexecução dirigida1PASS.
