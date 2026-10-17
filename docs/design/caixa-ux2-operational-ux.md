# Rodada — Caixa 2.0: contrato de UX operacional

**Estado:** referência de design homologada apenas por smoke de lógica do protótipo; **NÃO** homologada na aplicação real nem em bar.
**Versão de referência:** `prototype/caixa-ux2/index.html`, branch `prototype/caixa-ux2`, commit inicial desta consolidação `f97b5f4979b9` (as mudanças posteriores somente de documentação não mudam o protótipo).
**Data:** 17/10/2026.
**Papéis:** operador de caixa, gerente autorizado, garçom/atendimento (origem de comandas).
**Contrato de domínio:** [Spec 012 — Cash Management](../../specs/012-cash-management/spec.md) e [aceite](../../specs/012-cash-management/acceptance.md); pagamentos/estornos seguem Spec 006 e contratos canônicos existentes. Esta página especifica **apresentação, jornada e interação**, não substitui as validações de backend.

## 1. Objetivo e princípios

O operador deve conseguir receber, movimentar dinheiro físico e encerrar o turno sem conhecer contabilidade nem interpretar estados técnicos. Em horário de pico: **reconhecer a conta → entender quanto falta → cobrar com segurança → atender a próxima pessoa**.

Princípios obrigatórios:

1. **Vocabulário da tarefa antes do jargão.** Ex.: `Retirar dinheiro` antes de `Sangria`.
2. **Valor e consequência visíveis.** Sempre mostrar o saldo pertinente, método, antes/depois e confirmação adequada.
3. **Dinheiro físico ≠ consumo ≠ recebimento por Pix/cartão.** Nunca misturar o saldo da gaveta e o saldo da comanda.
4. **Confirmado somente com evidência canônica.** UI otimista não vira lançamento financeiro.
5. **Uma intenção = um efeito.** Duplo toque/reload/timeout não duplicam Payment, Refund, CashMovement ou pedido.
6. **Exceção recuperável no contexto.** Cobrança incerta, estorno histórico e diferença do caixa têm destino de resolução.
7. **Menos cliques, sem eliminar segurança.** PIN/nota explicativa quando exigidos; sem confirmação redundante para operações simples.
8. **Mesmo conceito em desktop, tablet e celular.** Priorizar valor, estado e próxima ação.

## 2. Estrutura de navegação

| Área | Pergunta do operador | Conteúdo e ações |
| --- | --- | --- |
| **Receber** | Quem está pagando? Quanto falta? | Busca por mesa, ficha, cliente ou código; filtros; comanda selecionada; itens, total, recebido, saldo; cobrar/dividir/encerrar; venda rápida; pendências |
| **Turno de caixa** | Quanto dinheiro físico está sob minha responsabilidade? | CashPoint/turno, fundo, dinheiro esperado, **Retirar dinheiro / Adicionar dinheiro**, histórico, conferência cega, fechamento, divergência |
| **Atividade** | O que aconteceu e o que preciso revisar? | Pagamentos, estornos, entradas/retiradas, tentativas sem confirmação, comprovantes, decisões de gerente, retorno de conferência |

O contexto do estabelecimento, operador, CashPoint e situação do turno deve permanecer claro em todas as superfícies. No celular, a lista → detalhe da comanda é uma navegação progressiva, com ação principal acessível; em desktop, a lista e o detalhe podem aparecer lado a lado.

## 3. Vocabulário obrigatório: entrada e saída da gaveta

### 3.1 Textos e sinais visuais

| Ação primária | Nome tradicional secundário | Explicação exibida | Efeito em dinheiro físico | Botão final |
| --- | --- | --- | --- | --- |
| **Retirar dinheiro** | **Sangria** | “Levar dinheiro ao cofre ou outra gaveta” | **Diminui** o dinheiro esperado | **Confirmar retirada** |
| **Adicionar dinheiro** | **Suprimento** | “Colocar troco ou reforço do cofre” | **Aumenta** o dinheiro esperado | **Confirmar entrada** |

Os rótulos principais são verbos concretos. O termo tradicional continua visível para conciliar treinamento, relatórios e processos antigos. Usar ícone de menos/mais e texto, **não apenas vermelho/verde**.

**Cópia na tela Turno de caixa:**
> O que você precisa fazer com o dinheiro físico da gaveta? Estas ações não registram venda ou pagamento do cliente.

**Cópia complementar:**
> Retirou dinheiro? O saldo da gaveta diminui. Colocou dinheiro? O saldo aumenta. Pix e cartão não ficam na gaveta.

### 3.2 Modal “Retirar dinheiro”

- Título: **Retirar dinheiro da gaveta**.
- Subtítulo: **Sangria = saída de dinheiro** + identificação do CashPoint/turno.
- Contexto: **O dinheiro vai SAIR do caixa**.
- Exemplo: “Tirar R$ 200 da gaveta para guardar no cofre”.
- Inputs: **Quanto dinheiro você vai retirar?**; motivo obrigatório com atalhos como **Envio ao cofre** / **Troco para outra gaveta**; campo “Para onde foi o dinheiro?”.
- Resumo antes de registrar: **Dinheiro na gaveta antes** → **Vai sair da gaveta (−)** → **Dinheiro esperado depois**.
- Limite: valor positivo; motivo obrigatório; turno OPEN; capability autorizada; não permitir valor acima do disponível no fluxo do protótipo. Uma eventual exceção/override em produção precisa de política explícita do backend e auditoria (Spec 012).
- Botão final: **Confirmar retirada**. Erro: “Não há esse valor na gaveta. Você pode retirar até R$ X”.
- Histórico: **Retirada · Sangria**, com valor negativo, motivo, operador, hora e identificador canônico.

### 3.3 Modal “Adicionar dinheiro”

- Título: **Adicionar dinheiro à gaveta**.
- Subtítulo: **Suprimento = entrada de dinheiro** + CashPoint/turno.
- Contexto: **O dinheiro vai ENTRAR no caixa**.
- Exemplo: “Pegar R$ 100 do cofre e colocar na gaveta para dar troco”.
- Inputs: **Quanto dinheiro você vai adicionar?**; motivo como **Reforço de troco** / **Transferência de gaveta**; campo “De onde veio o dinheiro?”.
- Resumo: **Dinheiro na gaveta antes** → **Vai entrar na gaveta (+)** → **Dinheiro esperado depois**.
- Limite: valor positivo; motivo; turno OPEN; autorização; idempotência.
- Botão final: **Confirmar entrada**.
- Histórico: **Entrada · Suprimento**, com valor positivo e identificação completa.

**Exemplo aritmético:** gaveta com R$ 300; adicionar R$ 200 → R$ 500; retirar R$ 100 → R$ 400. Nenhum dos dois cria Order, Charge ou Payment. Pix/cartão nunca aumentam o caixa físico.

**Mapeamento sem migração de domínio:**
`Adicionar dinheiro` → `CashMovement.kind=SUPPLY` (+);
`Retirar dinheiro` → `CashMovement.kind=WITHDRAWAL` (−).
Preservar identidade, reason, actor, timestamp, CashPoint, shift, chave idempotente e append-only.

## 4. Jornada do operador: recebimento

1. **Encontrar a conta:** buscar mesa/ficha/código/cliente ou priorizar **Pediram conta**. Contas diferentes na mesma mesa continuam independentes.
2. **Revisar:** itens consumidos, total, pagamentos confirmados, saldo remanescente e alerta de cobrança incerta.
3. **Cobrar:** método dinheiro, Pix, cartão. O protótipo demonstra Pix/cartão; a aplicação real só deve exibir meios efetivamente habilitados e com evidência de confirmação do provedor ou comprovante externo verificado na política da casa.
4. **Dinheiro:** registrar montante devido e entregue; calcular `troco = entregue − valor do pagamento`; registrar no caixa físico apenas o **valor líquido do pagamento confirmado** (não o bruto entregue); mostrar **Troco a devolver** após confirmação até operador marcar entregue.
5. **Pagamento parcial:** saldo permanece visível; a próxima cobrança usa somente o remanescente. Cancelar um modal não desfaz pagamentos já confirmados.
6. **Quitação:** saldo zero não é sinônimo de comanda encerrada; oferecer **Encerrar comanda**. Uma comanda encerrada não libera automaticamente a mesa/ocupação, especialmente se outra comanda da mesa estiver aberta.
7. **Comprovante:** indicar claramente se documento é demonstrativo/não fiscal; não confundir prévia com prova de liquidação.

### Dividir pagamento

- **Partes iguais:** escolher quantidade, criar plano persistente e fixar o valor de cada parcela calculado sobre o **saldo ainda devido / pessoas ainda pendentes** (ajuste de centavos na última distribuição). Exibir “2 de 4 partes pagas”, próxima parte e restante. Não permitir editar o valor no modal desse plano; para cobrar quantia diferente, usar **Por valor** explicitamente. Recarregar página não deve reiniciar plano.
- **Por valor:** receber uma quantia informada, positiva e não superior ao saldo canônico; é uma cobrança parcial, não uma parte “igual”.
- **Por itens:** selecionar unidades ainda atribuíveis, com encargos proporcionais do protótipo; evitar que pagamentos anteriores *sem* atribuição de itens sejam atribuídos novamente. Havendo tais pagamentos, o protótipo bloqueia nova divisão por itens e orienta **Por valor**.
- **Resultado incerto:** plano e seleção congelados junto à intenção de pagamento. Reconciliar o mesmo ID antes de prosseguir; nunca contar “parte paga” antes da confirmação.

### Venda rápida

Permitir venda avulsa sem selecionar mesa. No protótipo, mostra quais itens iriam para **Bar**/**Cozinha**, mas não envia produção real. Na implementação, a ação precisa criar Order/itens canônicos, despachar para as estações e manter a comanda caso a cobrança seja abandonada. **Não representar fila simulada como pedido recebido pela estação.**

## 5. Jornada do operador: turno de dinheiro físico

| Estado | Ações e leitura permitidas |
| --- | --- |
| **Sem turno** | Conferir o fundo fisicamente e abrir turno para o CashPoint selecionado |
| **OPEN** | Receber dinheiro, suprir, retirar, consultar movimentos, iniciar conferência |
| **COUNTING / contagem cega** | Bloquear movimentações ordinárias; ocultar saldo esperado, fundo e valores do histórico até registrar a contagem; guardar observação humana distinta do esperado |
| **COUNTING / contagem registrada** | Revelar esperado, contado e diferença; não permitir edição silenciosa da contagem; finalizar ou interromper por ação gerencial auditada |
| **CLOSED** | Histórico, saldo e divergência imutáveis; revisão gerencial separada; nova abertura conforme regras do CashPoint |

**Fechamento:** `esperado = fundo inicial + CASH_PAYMENT líquido + SUPPLY − WITHDRAWAL − CASH_REFUND + ajustes autorizados`. Contado é o total físico observado, e `diferença = contado − esperado`. O fechamento não inventa Payment, não apaga histórico e não corrige divergência automaticamente.

**Troco não entregue:** no protótipo, impede iniciar/confirmar contagem até resolver todos os lembretes `Troco entregue`, inclusive após reload. Na API real, a custódia/entrega e eventual exceção gerencial exigem estado e trilha persistidos no servidor; `localStorage` não prova que o dinheiro foi entregue.

**Divergência:** mostrar falta/sobra em linguagem comum; gerente revisa com motivo/PIN recente. Revisão não altera contagem ou esperado; correção tardia exige movimento imutável específico da Spec 012.

## 6. Exceções financeiras e recuperação

| Cenário | Resposta de UX | Comportamento canônico exigido na implantação |
| --- | --- | --- |
| Pix/cartão ainda processando ou timeout | **Cobrança sem confirmação** destacada no Receber e Atividade, com **Verificar agora**; bloquear nova cobrança da mesma intenção | Releitura autenticada de Payment/intent e provedor; não transformar timeout em pago |
| Reload / force-stop durante cobrança | Preservar identificador e contexto; retomar tentativa | Chave idempotente ligada a Tab, Venue, operador e payload; não criar nova intenção automaticamente |
| Offline | Avisar sem conexão, impedir confirmação financeira falsa; permitir contingência autorizada | Não contabilizar confirmação local como pagamento servidor |
| Estorno de dinheiro maior que saldo físico | Explicar valor disponível e bloquear lançamento | Validar novamente no servidor, sob lock/concurrency, antes de movimentar |
| Estorno em comanda encerrada | **Não reabrir** implicitamente. Caso aparece em **Revisar estornos** e **Atividade** | Refund e ledger append-only; caso histórico vinculado com revisão gerencial e acerto separado |
| Revisão gerencial do estorno | Registrar providência, PIN e decisão, sem coletar dinheiro automaticamente | Permissão/reautenticação server-side; auditoria, motivo, versão, IDs; jamais “marcar revisado” = “saldo liquidado” |
| Movimento duplicado/resultado perdido | Mostrar pendência e tentar reconciliar, não duplicar | Mesmo request-id e payload imutável; verificar efeito canônico |
| Fechamento concorrente a pagamento | Sinalizar que turno mudou e exigir atualização | Payment incluído antes do snapshot fechado ou rejeitado/reconciliado; nunca omitido silenciosamente |

## 7. Responsivo, acessibilidade e ergonomia

- **Desktop:** painel com lista de comandas e detalhe simultâneo; filtros e saldo sempre legíveis. Evitar modal sobreposto por alertas flutuantes.
- **Tablet:** navegação curta entre **Receber / Turno / Atividade**; ações grandes, sem depender de hover.
- **Celular (incluindo 360–430px e fontes ampliadas):** lista → detalhe; ação primária acessível; formulário e botões não cobertos pelo teclado; feedback de erro no contexto; rolagem interna do modal preservada durante inputs.
- **Troco flutuante:** aviso persistente fora do modal; enquanto um diálogo está aberto, ocultar **visualmente** o lembrete sem apagá-lo; reaparece ao fechar. O fechamento do turno continua bloqueado se houver troco pendente.
- Botões com verbo completo; labels independentes de cor; foco visível; uso com teclado; mensagens de erro com instrução realizável.
- Em **Retirar/Adicionar**, ícone +/- e direção (“SAIR/ENTRAR”) devem funcionar mesmo em monocromia e para operadores com pouca familiaridade com o sistema.
- Não exigir leitura de palavras em inglês técnico, referências de PSP ou IDs para o caminho feliz.

## 8. Implementação: protótipo versus aplicação real

| Item | Protótipo atual | Para considerar entregue no produto |
| --- | --- | --- |
| Telas e navegação | HTML/JS local em `prototype/caixa-ux2/index.html` | Implementar paridade Web em `apps/web/app/cash/page.tsx` e áreas compartilhadas; decidir e validar escopo Android à parte |
| Dados | Massa fictícia com `localStorage` | Query/mutation autenticadas no backend real; Tenant/Venue/CashPoint/Tab e permissões |
| SUPPLY / WITHDRAWAL | Movimento local demonstrativo | Endpoints canônicos e `CashMovement` append-only; idempotência, motivo, actor, concurrency |
| Pagamentos Pix/cartão | Botões **simular confirmado/incerto** | Nunca usar como atestado de dinheiro real; integrar somente capacidades habilitadas e homologadas |
| Dinheiro/troco | Troco calculado e lembrete local | `CashTenderDetail`, confirmação autoritativa e política de custódia por turno; preservar efeito líquido |
| Estorno pós-close | Pendência/revisão local demonstrativa | Refund canônico + workflow gerencial separado + trilha auditável |
| Contagem/fechamento | Estados simulados e contagem cega selada | Transições `OPEN → COUNTING → CLOSED` e snapshots atômicos da Spec 012 |
| Impressão/produção | Prévia e roteamento simulado | Impressora/fila/estação reais somente após gates específicos |
| Segurança | PIN `1234` **somente demo** | Reautenticação, permissões, CSRF/sessão, rate limits, logs sem PIN e isolamento por Venue |

**Importante:** a Spec 012 já define os tipos e invariantes financeiros. **Não criar segunda verdade** no frontend nem enviar valor com sinal invertido; direção do movimento e contratos de `CashMovement` são responsabilidade da API.

## 9. Critérios de aceite por fluxo (para execução real)

Marcar PASS somente com evidências da implementação real na versão/ambiente indicados, nunca só com o HTML:

- [ ] **CX-01** Operador encontra mesa, ficha ou balcão pelo código; duas Tabs da mesma ocupação são exibidas/quitadas separadamente.
- [ ] **CX-02** Ao receber CASH de R$ 82 com R$ 100 entregue, o troco é R$ 18 e a gaveta cresce **R$ 82**, uma única vez.
- [ ] **CX-03** Troco pendente permanece acessível após reload/troca de tela e não desaparece sem confirmação; política de bloqueio de fechamento validada no servidor.
- [ ] **CX-04** Dividir R$ 112 em quatro partes resulta em quatro pagamentos de R$ 28; tentar mudar a segunda para R$ 1 não marca outra parte paga.
- [ ] **CX-05** Divisão por valor e por itens preserva saldo, atribuição e limites; pagamentos anteriores sem atribuição não geram atribuição dupla.
- [ ] **CX-06** Pix/cartão incerto permanece pendente e bloqueia duplicação; resolver “não cobrado” ou “confirmado” depende de readback real.
- [ ] **CX-07** Quitação e fechamento da Tab não liberam automaticamente mesa/ocupação.
- [ ] **CX-08** **Retirar dinheiro (Sangria)** exibe explicação, exemplo, valor, motivo e saldo antes/depois; gera um único WITHDRAWAL, reduz o saldo físico e não cria Payment.
- [ ] **CX-09** **Adicionar dinheiro (Suprimento)** exibe explicação, exemplo e resumo; gera um único SUPPLY, aumenta o saldo físico e não cria Payment.
- [ ] **CX-10** Retirada maior que disponível é barrada conforme política do backend; erro não produz movimento.
- [ ] **CX-11** Estorno em dinheiro sem saldo suficiente não torna gaveta negativa nem marca Refund como pago; com saldo/autorizações, um único CashRefund canônico.
- [ ] **CX-12** Estorno em Tab encerrada não reabre a Tab; revisão gerencial não cria dinheiro ou quita saldo automaticamente.
- [ ] **CX-13** Contagem cega oculta esperado e histórico até registrar total físico; diferença permanece auditável.
- [ ] **CX-14** Fechamento concorrente a pagamento respeita fronteira do turno e reconciliação pós-reload.
- [ ] **CX-15** Desktop, tablet, mobile 360–430px, zoom/fontes maiores, teclado e perda de rede: sem ações ocultas, focos presos, scroll saltando ou sucesso falso.
- [ ] **CX-16** Duplo clique, timeout, perda após commit e requests repetidos não criam duplicatas e mantêm ledger/audit íntegros.
- [ ] **CX-17** Operador reconhece sem instrução prévia a diferença entre retirar/adicionar dinheiro e entre saldo físico e venda.
- [ ] **CX-18** Impressão/produção e fiscalidade respeitam gates independentes; prévias nunca afirmam entrega física ou emissão fiscal.

**Testes já executados:** `node prototype/caixa-ux2/smoke.test.cjs` — **17/17 cenários de interação simulada** validados nesta branch, cobrindo cópia de adicionar/retirar, matemática local, divisão, estorno, troco, revisão e reload. Essa evidência **não** marca as caixas CX-01..18 como aprovadas para produção.

## 10. Plano de entrega por corte

1. **Paridade de navegação e copy** (Receber/Turno/Atividade; labels Retirar/Adicionar; responsividade; estados sem alterar dados).
2. **Integração do caixa físico** (SUPPLY/WITHDRAWAL, fundo, estados do turno, contagem cega, autorização e auditoria).
3. **Integração de recebimentos** (cash/troco, parcial, divisão, intents incertos, quitação sem liberar mesa).
4. **Exceções e revisão** (estorno com saldo físico, Tab encerrada, divergência, recovery/replay; UX contextual).
5. **Homologação e release** (testes API PostgreSQL + browser E2E multiusuário + 360/390/430/tablet/desktop + cliente/caixa real assistido; imprimir ou contingenciar apenas dentro do escopo aprovado).

**Política de liberação:** seguir [Spec 012](../../specs/012-cash-management/spec.md), [spec de aceite](../../specs/012-cash-management/acceptance.md), evidências por SHA, revisão independente, QA financeiro e aceite presencial. Merge do protótipo ou testes locais verdes **não** equivalem a deploy, habilitação de PSP, pagamento homologado ou operação fiscal.

## 11. Referências verificáveis

- [HTML interativo](../../prototype/caixa-ux2/index.html) — demo, não produto.
- [README e decisões de auditoria](../../prototype/caixa-ux2/README.md).
- [Regressões de lógica](../../prototype/caixa-ux2/smoke.test.cjs).
- [Spec 012](../../specs/012-cash-management/spec.md) / [aceite 012](../../specs/012-cash-management/acceptance.md).
- [Caixa Web real](../../apps/web/app/cash/page.tsx): implementação separada, **não alterada** por esta documentação.
