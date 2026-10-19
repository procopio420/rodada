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

## Gate de código dinâmico e cobertura da barra real

O CI #224 rejeitou new Function no harness da barra. O teste foi migrado para
navegar Attendance real com fixtures de API, sem transpile/eval/rota de teste.
Mantém 0/79/80/99/100/120%, projeção500 nas versões expandidas, zero/DTOinválido,
capacidade canônica e foco/alvo44. Suíte final9/9PASS em1,1min cobrindo360/390/430/
1280 e fontes1/2x. Tentativas anteriores falharam por seletor no filho emvezraiz,
rascunho persistido entre fixtures e expectativa de texto sópresente na versão
expandida; corrigidas sem bypass/remoção do gate. Execuções paralelas anteriores
colidiram nos paths de artefatos; contagem final vem do handle36204, não do report
sobrescrito. Capturas/report limpos exigem execução isolada com output próprio.

R3 financeiro independente sobre3fc2ac55: NO_FINDINGS_WITH_GAPS (outrocontexto
review_e04_final), sem execução independente/GitHubapproval. Lacunas: repetir
recovery/keepOpen emAttendance (atuais ensaios principais emPOS), storagephase
failure e callbackfailure. Agente independente assumiu testes adicionais.

## Página de pagamento fiel — incremento68b7f48c

Conta abre páginaReceber conta com saldo canônico pré-preenchido, campo manual,
Dinheiro selecionado, ação parcial ou integral+encerrar e opção manteraberta.
Stage bloqueia trocaTab durante formulário; não cria intenção até confirmar.
PIX/CARD indisponíveis e seleçãoCaixa são diferenças necessárias ao contrato real,
registradas como gate de paridade, sem aprovação implícita. MotorPayment/Close
reutilizado. Visual4/4PASS nos4tamanhos(15s), build/typecheck/lintPASS.

Revisão independente do incremento encontrou P2: Tab fechada por outrooperador
podia esconder formulário e manter bloqueio. Correção preserva saídaVoltar e
mostra estado canônico terminal, sem novoPayment. Regressão visual concorrente
adicionada; reexecuções visual/PG emandamento, não marcarPASSantesresultado.

Testes independentes6194fbb9 incorporados:3/3PASS noSHAoriginal do teste/produção
3fc2, cobrindoAttendance selectednull/reload, Payment/Close ACKlost, Close503,
consumo concorrente+callback503 e falha storage na faseconfirmed. Sobre68b7 foram
7/8PASS: única falha eraassert final do campo POSantigo, agora navegaReceber e
valida campo da páginaUX2, mantendo todas as verificações monetárias.

## Evidência final deste incremento

Web05f5c25a: build/typecheck/lintPASS; páginaPagamento+fechamento concorrente5/5
visualPASS(16,9s). Testesfinanceiros7/8PASS naexecução conjunta, oitavoPASSdirigido
(16,8s) apósaguardarlimpezadoenvelopeemvezdeassumirqueCLOSEDsignificacallbackterminado.
Dinheiro/ledger/chaves/Paymentcountscontinuamverificados. Novos3cenáriosindependentes
Attendancepassaramnessaexecuçãoconjunta. R3correção8fbc:NO_FINDINGS_WITH_GAPS;nullsem
pendingaindanãotemregressãoprópria. Nãoalegar8/8numúnicorun.

Capturaspareadasversionadasemdocs/development/evidence/spec033-payment comSHAs,
hashes, mesmosaldo2400,quatrolargurase diferenças explícitas. ParidadefinalE04
permanecependente(Android/2x/aprovaçãodiferenças/CI/regressãocompleta).
