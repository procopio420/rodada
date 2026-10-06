# ADR 0004 — Tab identity, table occupancy and guest access

**Status:** Accepted

## Contexto

O piloto do Bar do Aderlan possui mesas móveis/flexíveis, grupos que podem dividir contas, clientes que mudam de lugar e necessidade futura de permitir pedido direto pelo celular.

Modelar pedido ou conta diretamente por mesa criaria acoplamento incorreto:

- uma mesa pode conter várias contas;
- uma conta pode existir sem mesa;
- pagar uma conta não significa que o grupo saiu;
- mesa precisa de ciclo de limpeza/giro;
- QR/NFC/perfil são meios de acesso, não a verdade financeira.

## Decisão

A entidade financeira obrigatória é `Tab`.

> **Identity optional, Tab mandatory.**

Todo `Order` pertence a uma `Tab`.

`Table` é um recurso físico. `TableOccupancy` é o período em que um grupo usa a Table e pode agregar várias Tabs.

```text
Table
└── TableOccupancy
    ├── Tab A
    │   ├── Order
    │   └── Ledger
    ├── Tab B
    └── Tab C
```

Uma Tab pode também existir sem TableOccupancy.

## Resolução da Tab

A mesma Tab pode ser encontrada/acessada por diferentes caminhos:

- `display_label`/nome/apelido pesquisável;
- Customer/profile autenticado;
- código curto;
- GuestSession do navegador;
- QR dinâmico;
- tag/pulseira NFC.

Tokens técnicos ficam em `TabIdentifier` e são revogáveis. Customer e display label continuam relações/campos de domínio próprios.

NFC é conveniência operacional, não prova forte de identidade.

## QR da mesa

O QR físico da mesa:

- contém token público aleatório/opaco;
- nunca expõe ID sequencial;
- resolve `Table`, não `Tab`;
- inicia/recupera GuestSession;
- associa a sessão à ocupação/generation quando houver;
- pode ser desativado/bloqueado pelo staff.

## Lifecycle da mesa

```text
AVAILABLE → OCCUPIED → DIRTY → CLEANING → AVAILABLE
```

A primeira associação/pedido pode criar a ocupação de acordo com `guest_ordering_mode`.

Fechar a última Tab não libera a mesa automaticamente.

O staff executa `release table` quando o grupo sai. Isso encerra a ocupação e move a mesa para `DIRTY`.

Ao concluir limpeza:

- a mesa volta para `AVAILABLE`;
- `access_generation` incrementa;
- sessões da geração anterior deixam de autorizar pedidos.

## Guest ordering modes

Configuração por mesa/venue:

- `DISABLED`: somente staff.
- `JOIN_ACTIVE`: cliente só pede quando já existe ocupação ativa.
- `DIRECT`: scan pode iniciar fluxo de ocupação/comanda quando a mesa está disponível.

`DIRECT` é mais fluido e deve ser usado em mesas escolhidas pelo estabelecimento. Controles mínimos: token opaco, rate limit, auditoria, bloqueio imediato pelo staff e revogação por geração.

Provas de presença mais fortes, como NFC ou código dinâmico, podem ser adicionadas sem mudar o modelo.

## Consequências

- pedido, pagamento e saldo deixam de depender de mesa;
- divisão de conta é natural;
- cliente pode mudar de lugar mantendo a mesma Tab;
- guest ordering e NFC podem evoluir sem criar uma segunda arquitetura financeira;
- limpeza e giro de mesa tornam-se mensuráveis;
- implementação precisa tratar resolução/autorização de Tab separadamente de identidade de Customer.
