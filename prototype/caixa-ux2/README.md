# Rodada — Caixa UX 2.0 (protótipo)

Protótipo navegável de recebimentos, caixa e histórico. **Somente dados fictícios**, persistidos em `localStorage`; não acessa backend, PSP, POS, fila de Bar/Cozinha ou banco real.

## Especificação operacional para implementação

O contrato consolidado da experiência do caixa (jornadas, linguagem de sangria/suprimento, estados financeiros, responsividade, mapeamento para Spec 012 e 18 critérios de aceite para o produto real) está em **[Caixa 2.0 — contrato de UX operacional](../../docs/design/caixa-ux2-operational-ux.md)**.

Este README registra o histórico dos ajustes do protótipo; a especificação operacional é a referência para implementação Web/API e QA, sem substituir as regras financeiras da Spec 012.

## Auditoria de operador — 2026-10-17

Correções aplicadas a partir do uso simulado de um caixa movimentado:

1. **Contagem cega selada** — durante conferência, totais e movimentos da gaveta não ficam expostos, inclusive na aba Atividade. O número contado é persistido antes de mostrar o valor esperado e não pode ser editado após essa revelação. Interromper conferência requer o gerente e fica auditado na simulação.
2. **Divisão em partes persistente** — após cobrar a primeira parcela, as demais usam o número restante de pessoas e o saldo canônico. O estado da divisão resiste a recarregar a página e a pagamentos com resultado incerto.
3. **Troco persistente** — após pagamento em dinheiro, o troco aparece em um aviso de alta visibilidade até `Troco entregue`; o aviso também sobrevive ao reload, sem obrigar uma confirmação antes de atender outra conta.
4. **Cobrança incerta global** — alerta na tela Receber, prioridade na lista, acesso direto à tentativa e bloqueio de novo pagamento/fechamento enquanto o resultado for desconhecido.
5. **Estorno sem reabertura implícita** — não modifica o estado de encerramento da comanda. Para estornos após encerramento, exibe pendência gerencial separada e conserva a reversão no histórico.
6. **Venda rápida e produção** — itens ganham roteamento demonstrativo `BAR` ou `KITCHEN`, visível na comanda e Atividade. **Não há envio verdadeiro às estações**: integração com o produto Web/API é uma etapa distinta.
7. **Divisão por itens** — quando há pagamento anterior sem atribuição de itens, a interface impede nova divisão por unidades e orienta cobrar por valor, evitando atribuição dupla.

## Segunda auditoria — 2026-10-17 (correções complementares)

Foram corrigidos os quatro novos P1 e os dois P2 encontrados em cenários adversos:

1. **Divisão igual sem edição oculta**: parcelas do plano ficam bloqueadas no formulário; a ação de confirmação verifica o valor exato no JavaScript, inclusive para Pix/cartão demonstrativos. Valores diferentes devem passar pelo fluxo explícito de divisão por valor. `paidParts` só avança após valor correto.
2. **Estorno em dinheiro financiado**: se o dinheiro físico estimado não for suficiente, a interface explica o bloqueio, e o handler rejeita o estorno; é preciso fazer um suprimento autorizado ou encaminhar à administração. Nunca registra saldo da gaveta negativo.
3. **Troco entregue antes do fechamento**: o turno não entra em contagem enquanto houver lembrete aberto de troco. O bloqueio é verificado também nos handlers de contagem e fechamento e sobrevive ao reload. Confirmar a entrega acrescenta evento auditável demonstrativo.
4. **Revisão de estorno pós-fechamento**: comandas históricas com revisão pendente aparecem na lista inicial (e no filtro `Revisar estornos`), com acesso direto à revisão. Gerente informa PIN e providência; registra evento e marca revisão, mas **não altera o ledger, não cobra cliente e não reabre a comanda**. O saldo pós-estorno permanece para acerto separado, mesmo quando o caso deixa de ser uma revisão pendente.
5. **Teclado/rolagem em telas pequenas**: re-render preserva a posição vertical e horizontal dentro da área rolável do modal.
6. **Troco sem sobreposição de diálogo**: o lembrete fica oculto enquanto um diálogo está aberto, sem ser apagado. Reaparece automaticamente ao fechar; sua camada também fica abaixo da do modal.

O smoke passou de 7 para **17 cenários** e adicionou tentativas de alterar valores bloqueados, estorno sem fundos + suprimento, contagem bloqueada por troco, revisão gerencial, persistência/reload, ocultação e posição de rolagem do modal. Estes são testes de lógica com DOM simulado: permanece obrigatória a inspeção visual/teclado em navegadores desktop, tablet e telefone, além da integração real do backend e testes de transações/concorrência.

## Linguagem simples para movimentar dinheiro — 2026-10-17

Na seção **Turno de caixa**, as ações agora priorizam o que o operador quer fazer, mantendo o nome contábil apenas como ajuda:

- **Retirar dinheiro** — *Sangria*. Ex.: tirar dinheiro da gaveta e guardar no cofre. Reduz o dinheiro físico esperado.
- **Adicionar dinheiro** — *Suprimento*. Ex.: pegar dinheiro do cofre para reforçar troco na gaveta. Aumenta o dinheiro físico esperado.

Os modais descrevem o sentido da movimentação, dão um exemplo, solicitam valor e motivo e mostram **dinheiro antes → quanto entra/sai → dinheiro esperado depois**. O botão final usa *Confirmar retirada* ou *Confirmar entrada*. O histórico mostra a ação em linguagem natural junto ao termo contábil. Não altera pagamentos de clientes nem vendas.

Os rótulos e os efeitos financeiros continuam exclusivamente no protótipo, não na página real do Caixa do Rodada. Três novos cenários de smoke cobrem os textos e o efeito do saldo na gaveta.

## Smoke de regressão

```bash
node prototype/caixa-ux2/smoke.test.cjs
```

Teste sem dependências que usa o mesmo JavaScript do protótipo e simula 17 cenários de interações/eventos e reload. É um teste de lógica de UI, **não** equivale a Playwright em navegador, integração financeira, auditoria da API ou homologação no caixa do estabelecimento.

## Abrir

Abrir `prototype/caixa-ux2/index.html` no navegador. Para voltar à massa de teste inicial, usar **Reiniciar demonstração**. Não usar o PIN fictício mostrado no protótipo como credencial real.

## Limite de aceitação

Estas correções referem-se somente à branch `prototype/caixa-ux2`. A página `apps/web/app/cash/page.tsx` em `main` não foi modificada. Para implantar a UX 2.0 no produto, mapear fluxos a backend canônico (ledger, shift, payment status, tenant auth, request-id, aprovação gerencial) com testes reais de desktop/tablet/mobile, teclado, impressão e conectividade antes de considerar produção.
