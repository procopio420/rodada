# Demo — Bar do Aderlan

Objetivo: mostrar um loop real de **PDV + produção + recebimento**. Todas as ações
abaixo usam estado persistido na API; não dependa de valores simulados no cliente.

Antes da demonstração, siga o [runbook local](./local-runbook.md) e execute
`python manage.py smoke_demo` em `apps/api`.

## Cena 1 — entrar e abrir atendimento

1. Entrar como `Bia Staff` com PIN `1234`.
2. Abrir uma Tab sem mesa, com um `label`/apelido opcional.
3. Mostrar que a Tab acabou de abrir com exposição R$ 0,00.

## Cena 2 — vender

1. Adicionar `4 Brahma` e `1 Fritas`.
2. Confirmar pedido.
3. Mostrar que Brahma roteia para Bar e Fritas para Cozinha.
4. Voltar à Tab: as charges persistidas tornam a exposição R$ 76,00.

## Cena 3 — operar

1. No Bar, avançar a Brahma por `ACCEPTED` e `READY`.
2. Na Cozinha, avançar Fritas por `ACCEPTED`, `PREPARING` e `READY`.
3. Mostrar que cada item pronto cria trabalho de entrega persistido; um operador
   pode assumir e concluir esse trabalho.

## Cena 4 — disponibilidade (momento operacional opcional)

1. Como `Ana Gerente`, marcar Fritas como indisponível.
2. Mostrar o produto indisponível no catálogo e que um carrinho aberto não confirma.
3. Marcar disponível novamente para continuar a venda.

## Cena 5 — controlar exposição e fechar

1. Mostrar que fechar antes de receber falha por exposição em aberto.
2. Como `Ana Gerente` (PIN `0420`), receber um pagamento parcial manual.
3. Mostrar a exposição reduzida, ainda aberta.
4. Receber o restante, chegar a R$ 0,00 e fechar a Tab.
5. Tentar adicionar outro pedido: a API rejeita a Tab fechada.

## Cenas para mostrar apenas se a superfície correspondente estiver pronta

- associação da Tab ao ponto `P37 / Rua`;
- cliente da casa e limite operacional;
- agrupamento de entregas em `Run`;
- QR de convidado e pagamentos por provedor.

## Pergunta para o Aderlan

> “Se isso funcionasse numa sexta cheia, onde você acha que mais mudaria sua operação?”
