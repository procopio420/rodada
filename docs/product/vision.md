# Visão do Produto

## Problema

Bares de alto fluxo são sistemas físicos dinâmicos. O software tradicional costuma representar bem venda e caixa, mas representa pior o que acontece entre o cliente querer algo e esse algo chegar até ele.

No Bar do Aderlan, além disso:

- mesas aparecem onde houver espaço;
- clientes mudam de lugar;
- o bar ocupa imóveis, calçadas e rua;
- muitos clientes são conhecidos pessoalmente;
- atendimento, produção, entrega e pagamento convivem em alto volume.

Um PDV tradicional parte de “mesa fixa + pedido + conta”. Rodada parte de:

> **pessoa/grupo + tab + pedido + localização atual + trabalho operacional + pagamento.**

## Tese

Rodada combina três primitivas que normalmente vivem separadas:

1. **PDV transacional** — vender, cobrar, fechar e auditar.
2. **Dispatch operacional** — saber o que precisa acontecer agora, por quem e onde.
3. **Relacionamento financeiro** — reconhecer quem é da casa e adaptar limite/pagamento à relação.

## Experiência alvo

```text
João da Oficina
🏠 DA CASA

Tab aberta        R$ 184
Limite            R$ 500
Localização       Rua · P37

Pedido #921
4 Brahma          PRONTO
1 Fritas          EM PREPARO

Próxima ação
→ entregar cervejas no run Rua
```

O mesmo sistema entende venda, cliente, produção, entrega e dinheiro.

## Diferenciação pretendida

Não é “mais um PDV com QR”.

- PDVs tradicionais registram transações.
- CRMs registram relacionamento.
- KDS organiza produção.
- ferramentas de fila/dispatch coordenam trabalho.

Rodada tenta fechar o loop:

```text
IDENTIDADE
  ↓
RELACIONAMENTO
  ↓
PEDIDO / VENDA
  ↓
PRODUÇÃO
  ↓
DISPATCH / ENTREGA
  ↓
PAGAMENTO
  ↓
HISTÓRICO
  └────────→ RELACIONAMENTO
```

## Resultado desejado no piloto

O produto é bom se o Aderlan conseguir perceber, numa noite cheia:

- menos pedido perdido;
- menos tempo entre pronto e entregue;
- menos necessidade de perguntar “quem vai levar?”;
- fechamento mais confiável;
- regulares tratados como regulares sem depender da memória do dono;
- mais throughput com a mesma equipe.

## Métrica norte

> **Aumentar pedidos entregues e pagos por hora sem piorar a experiência.**

Métricas auxiliares:

- pedido → entrega;
- pronto → retirada;
- chamadas esquecidas;
- entregas por run;
- exposição aberta;
- diferenças de caixa;
- pedidos/garçom/hora.
