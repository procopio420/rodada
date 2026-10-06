# ADR 0006 — Dynamic table placement and floorplan

**Status:** Accepted

## Contexto

No piloto, mesas são móveis. Elas podem sair de dentro do estabelecimento, aparecer na calçada/rua, ser juntadas, separadas, guardadas ou movidas durante a noite.

Tratar `Table 27` como uma coordenada fixa criaria o mesmo erro conceitual que tratar mesa como conta.

Também queremos que toda mesa possa carregar um QR permanente, inclusive quando ainda não sabemos onde ela será colocada naquele turno.

## Decisão

Separar identidade física de posição espacial:

```text
Table          = objeto físico + QR estável
TablePlacement = posição atual/temporal no FloorPlan
TableOccupancy = sessão física de atendimento
Tab            = sessão financeira
```

Uma Table pode existir e estar disponível sem placement ativo.

Guest ou staff pode criar o primeiro placement ao iniciar o atendimento. Staff pode mover a mesa depois arrastando-a no mapa ou encerrar o placement se a mesa for retirada/guardada.

Mover ou retirar do mapa nunca recria ou migra Tab, Order, ledger ou QR.

## FloorPlan

O FloorPlan é um canvas 2D operacional, não uma planta CAD e não geolocalização.

Posições usam coordenadas normalizadas para funcionar em diferentes viewports.

A projeção guest deve ser sanitizada e conter apenas referências úteis para localização.

## Concorrência

Placement mutations usam versionamento/optimistic locking.

Se staff e guest posicionarem ao mesmo tempo, uma versão stale não sobrescreve silenciosamente a posição já confirmada.

## Agrupamento

`TableGroup` pode representar mesas fisicamente juntas.

O grupo é temporário e operacional. Não funde Table, QR, TableOccupancy, Tab ou ledger.

## Dispatch

Dispatch pode resolver destino/Zone a partir do placement ativo. Isso permite que uma mesa móvel continue útil para batching, prioridade e runs sem tornar coordenada parte da identidade financeira.

## Consequências

- QR pode ser colado permanentemente em qualquer mesa;
- layout pode mudar livremente durante a noite;
- cliente pode ajudar a localizar uma mesa recém-colocada;
- staff mantém controle e pode corrigir, mover ou retirar mesas do mapa;
- histórico de movimento pode ser auditado;
- regras financeiras continuam independentes da planta física;
- o modelo suporta o caos real do bar sem inventar mesas fixas.
