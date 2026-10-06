# Visão do Produto

## Problema

Bares de alto fluxo são sistemas físicos dinâmicos. O software tradicional costuma representar bem venda e caixa, mas representa pior o que acontece entre o cliente querer algo e esse algo chegar até ele.

No Bar do Aderlan, além disso:

- mesas aparecem onde houver espaço;
- clientes mudam de lugar;
- o bar ocupa imóveis, calçadas e rua;
- um mesmo grupo pode querer contas separadas;
- uma comanda pode continuar existindo depois de a pessoa mudar de lugar;
- muitos clientes são conhecidos pessoalmente;
- atendimento, produção, entrega, limpeza e pagamento convivem em alto volume.

Um PDV tradicional parte de “mesa fixa + pedido + conta”. Rodada parte de:

> **tab/comanda + identidade opcional + localização atual + pedido + trabalho operacional + pagamento.**

## Tese

Rodada combina quatro primitivas que normalmente vivem separadas:

1. **PDV transacional** — vender, cobrar, fechar e auditar.
2. **Dispatch operacional** — saber o que precisa acontecer agora, por quem e onde.
3. **Relacionamento financeiro** — reconhecer quem é da casa e adaptar limite/pagamento à relação.
4. **Table Ops + Guest Ordering** — entender ocupação/giro da mesa e permitir self-service sem transformar a mesa na conta.

## A primitiva central: Tab

A unidade financeira é a `Tab`.

Ela pode ser:

- anônima;
- rotulada com nome/apelido pelo garçom;
- ligada a um Customer/Relationship;
- acessada pelo celular do cliente;
- resolvida por código curto;
- associada temporariamente a uma tag/pulseira NFC;
- acessada por QR dinâmico.

Essas são formas de **encontrar a mesma comanda**. Não são contas diferentes.

> **Identity optional, Tab mandatory.**

Todo `Order` pertence a uma `Tab`.

## Mesa é recurso físico, não conta

Uma `Table` pode ter uma `TableOccupancy` ativa. Uma ocupação pode conter várias Tabs.

Exemplo:

```text
Mesa 24 · OCCUPIED
└── Ocupação #812
    ├── Tab Lucas
    ├── Tab Laísa
    └── Tab Rafael
```

Fechar a Tab Lucas não libera a mesa. A ocupação termina quando o grupo efetivamente sai e o staff libera a mesa.

Depois:

```text
OCCUPIED → DIRTY → CLEANING → AVAILABLE
```

Isso permite medir giro e limpeza sem misturar logística física com dinheiro.

## Guest Ordering

Algumas mesas podem ter QR de self-service e outras não.

O QR:

- usa token opaco e não ID sequencial;
- resolve a mesa, não uma comanda;
- abre uma PWA sem exigir instalação;
- permite criar/assumir uma Tab;
- envia pedidos para a mesma pipeline de Bar/Cozinha;
- pode ser bloqueado pelo staff sem fechar a Tab;
- cria uma sessão vinculada à geração da ocupação;
- perde validade quando a mesa é liberada/limpa e a geração muda.

Para mesas com maior risco, o venue pode usar modos mais restritivos, como permitir guest ordering apenas numa ocupação já ativa ou exigir presença adicional via NFC/código dinâmico.

## Experiência alvo

```text
João da Oficina
🏠 DA CASA

Tab aberta        R$ 184
Limite            R$ 500
Mesa               24 · Rua

Pedido #921
4 Brahma          PRONTO
1 Fritas          EM PREPARO

Acessos da tab
📱 Guest session
⌁ NFC 37
# 4827

Próxima ação
→ entregar cervejas na Mesa 24
```

O mesmo sistema entende venda, cliente, produção, entrega, dinheiro e contexto físico.

## Diferenciação pretendida

Não é “mais um PDV com QR”.

- PDVs tradicionais registram transações.
- CRMs registram relacionamento.
- KDS organiza produção.
- ferramentas de fila/dispatch coordenam trabalho.
- sistemas de mesa normalmente confundem localização com conta.

Rodada tenta fechar o loop:

```text
IDENTIDADE OPCIONAL
       ↓
      TAB
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

TABLE / OCCUPANCY ──→ contexto físico + giro + limpeza
```

## Resultado desejado no piloto

O produto é bom se o Aderlan conseguir perceber, numa noite cheia:

- menos pedido perdido;
- menos tempo entre pronto e entregue;
- menos necessidade de perguntar “quem vai levar?”;
- clientes podendo pedir direto em mesas selecionadas;
- menos confusão entre “mesa” e “comanda” quando há conta separada;
- fechamento mais confiável;
- visão clara de mesa disponível, ocupada e aguardando limpeza;
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
- pedidos/garçom/hora;
- pedidos guest/hora;
- tempo de ocupação da mesa;
- saída → início da limpeza;
- duração da limpeza;
- tempo total até mesa disponível novamente.
