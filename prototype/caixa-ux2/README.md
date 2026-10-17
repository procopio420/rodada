# Rodada — Caixa UX 2.0 (protótipo)

Protótipo navegável de recebimentos, caixa e histórico. **Somente dados fictícios**, persistidos em `localStorage`; não acessa backend, PSP, POS, fila de Bar/Cozinha ou banco real.

## Auditoria de operador — 2026-10-17

Correções aplicadas a partir do uso simulado de um caixa movimentado:

1. **Contagem cega selada** — durante conferência, totais e movimentos da gaveta não ficam expostos, inclusive na aba Atividade. O número contado é persistido antes de mostrar o valor esperado e não pode ser editado após essa revelação. Interromper conferência requer o gerente e fica auditado na simulação.
2. **Divisão em partes persistente** — após cobrar a primeira parcela, as demais usam o número restante de pessoas e o saldo canônico. O estado da divisão resiste a recarregar a página e a pagamentos com resultado incerto.
3. **Troco persistente** — após pagamento em dinheiro, o troco aparece em um aviso de alta visibilidade até `Troco entregue`; o aviso também sobrevive ao reload, sem obrigar uma confirmação antes de atender outra conta.
4. **Cobrança incerta global** — alerta na tela Receber, prioridade na lista, acesso direto à tentativa e bloqueio de novo pagamento/fechamento enquanto o resultado for desconhecido.
5. **Estorno sem reabertura implícita** — não modifica o estado de encerramento da comanda. Para estornos após encerramento, exibe pendência gerencial separada e conserva a reversão no histórico.
6. **Venda rápida e produção** — itens ganham roteamento demonstrativo `BAR` ou `KITCHEN`, visível na comanda e Atividade. **Não há envio verdadeiro às estações**: integração com o produto Web/API é uma etapa distinta.
7. **Divisão por itens** — quando há pagamento anterior sem atribuição de itens, a interface impede nova divisão por unidades e orienta cobrar por valor, evitando atribuição dupla.

## Smoke de regressão

```bash
node prototype/caixa-ux2/smoke.test.cjs
```

Teste sem dependências que usa o mesmo JavaScript do protótipo e simula interações/eventos e reload. É um teste de lógica de UI, **não** equivale a Playwright em navegador, integração financeira, auditoria da API ou homologação no caixa do estabelecimento.

## Abrir

Abrir `prototype/caixa-ux2/index.html` no navegador. Para voltar à massa de teste inicial, usar **Reiniciar demonstração**. Não usar o PIN fictício mostrado no protótipo como credencial real.

## Limite de aceitação

Estas correções referem-se somente à branch `prototype/caixa-ux2`. A página `apps/web/app/cash/page.tsx` em `main` não foi modificada. Para implantar a UX 2.0 no produto, mapear fluxos a backend canônico (ledger, shift, payment status, tenant auth, request-id, aprovação gerencial) com testes reais de desktop/tablet/mobile, teclado, impressão e conectividade antes de considerar produção.
