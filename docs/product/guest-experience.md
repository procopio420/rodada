# Guest Experience — UX do cliente

Este documento define a experiência canônica do cliente no Rodada e complementa a Spec 004 e o Design System.

## Norte

O cliente não precisa entender como o restaurante opera por dentro.

A experiência reduz intenções a ações diretas:

- quero pedir → adiciono e envio;
- quero outra igual → peço novamente;
- quero saber do pedido → vejo um estado simples;
- preciso de algo → faço uma solicitação específica;
- quero saber quanto gastei → abro Conta;
- quero pagar → peço/realizo pagamento quando o método estiver disponível.

Por trás disso, o Rodada coordena mesa, posição, ocupação, comanda, fulfillment, dispatch e billing.

## Primitivas

```text
Table            = objeto físico + QR permanente
TablePlacement   = onde a mesa está agora
TableOccupancy   = sessão física de atendimento naquela mesa
Tab              = comanda / unidade financeira
GuestSession     = autorização do dispositivo
```

Nenhuma dessas entidades deve ser colapsada na outra.

## Entrada pelo QR

Toda Table pode ter QR permanente, inclusive uma mesa móvel ainda sem posição no turno.

O QR:

1. resolve apenas a Table por token opaco;
2. cria ou recupera GuestSession;
3. consulta placement e ocupação atuais;
4. conduz o cliente para localizar a mesa, criar/entrar em Tab e pedir.

Nunca usar número sequencial como segredo ou contrato público.

## Mesa sem posição

Uma mesa recém-colocada na rua, calçada ou outro espaço pode ainda não estar atribuída ao floorplan.

```text
Escanear QR
  ↓
Mesa 27
  ↓
"Onde vocês estão?"
  ↓
Mapa 2D simplificado
  ↓
cliente toca aproximadamente na posição
  ↓
confirmar
  ↓
criar/entrar em comanda
```

O staff pode executar a mesma ação. Quem posicionar primeiro resolve o contexto para os demais.

Se houver edição concorrente, versão stale não sobrescreve silenciosamente um placement mais novo.

## Floorplan

O mapa 2D não é CAD. É um canvas operacional com referências relativamente estáveis:

- salão;
- calçada;
- rua;
- anexos;
- balcão;
- entrada;
- zonas úteis.

Staff vê a versão operacional completa. Guest recebe uma projeção sanitizada, somente com informação suficiente para reconhecer onde está.

Coordenadas são normalizadas `x/y`, não latitude/longitude.

## Movimento e retirada do mapa

A Table pode ser arrastada durante a noite.

Mover troca o TablePlacement e preserva:

- TableOccupancy;
- Tabs;
- pedidos;
- ledger;
- QR;
- GuestSession enquanto a occupancy/generation continuar válida.

Se a mesa for guardada ou retirada fisicamente do layout, staff encerra o placement atual. A Table continua existindo e o mesmo QR poderá ser usado quando ela voltar.

## Mesas agrupadas

Mesas fisicamente juntas podem formar um `TableGroup` temporário.

```text
[27][28]
   [31]

Grupo: Aniversário João
```

O grupo melhora visualização e dispatch, mas não funde QR, Table, TableOccupancy, Tab ou ledger.

Ao escanear uma mesa agrupada, o guest pode receber contexto do grupo e opções autorizadas para entrar numa Tab já usada pelo grupo, sem transformar o grupo em unidade financeira.

## Criar ou entrar em comanda

Depois de resolver o contexto físico:

- criar nova Tab anônima ou com label;
- entrar em Tab existente por fluxo autorizado;
- opcionalmente ligar Customer/profile;
- permitir múltiplas Tabs na mesma ocupação.

Login nunca é requisito do fluxo básico.

## Navegação

A experiência guest possui três destinos primários:

```text
Cardápio | Pedidos | Conta
```

Nada além disso compete como navegação principal no MVP.

### Cardápio é a home

O primeiro pedido não encerra a jornada. Em bar, pedir é recorrente.

Depois de enviar um pedido, o cliente volta naturalmente ao Cardápio e pode continuar consumindo.

Cards favorecem quick-add:

```text
Original 600 ml        R$ 14
                         [ + ]
```

Abrir detalhe apenas quando modificadores, quantidade especial ou observação forem necessários.

## Pedidos

A tela Pedidos mostra histórico e pedidos ativos.

O Rodada não expõe microestados que o staff não mede de forma confiável.

Baseline guest:

```text
Recebido
Preparando
Pronto / chegando
```

Esses estados são projeções dos estados internos de fulfillment.

Um resumo persistente opcional (`LiveOrderBar`) pode aparecer no rodapé:

```text
2 pedidos preparando · Ver pedidos
```

### Pedir novamente

Pedido anterior oferece **Pedir novamente** se o Product continuar disponível.

O objetivo é evitar que o cliente navegue repetidamente pela taxonomia para pedir a mesma bebida/comida.

## Solicitar atendimento

Evitar depender apenas de **Chamar garçom**.

Preferir intenções estruturadas:

- Quero pagar;
- Preciso de talheres;
- Preciso de gelo;
- Falar com alguém.

Isso gera `DispatchTask` com contexto útil antes de alguém chegar à mesa.

O guest não precisa acompanhar claim/ownership interno do funcionário.

## Conta

Conta representa a Tab, nunca a Table.

Mostrar:

- itens da Tab;
- total/exposure permitido;
- pagamentos quando existirem;
- ações de pagamento/fechamento suportadas.

Quando houver identidade suficiente para atribuir itens a participantes, a UX pode apresentar **minha parte** e o total do grupo. Split avançado e pagamento mobile entram em specs próprias sem mudar o princípio Tab-first.

## Segurança da sessão

QR permanente não significa autorização permanente.

A GuestSession fica ligada ao contexto atual de ocupação/generation. Liberar/limpar a mesa revoga a capacidade da geração anterior de criar novos pedidos.

Staff pode bloquear guest ordering sem impedir pedidos internos ou fechar Tabs.

## Regras de UX

- mobile-first, 360–430 px;
- uso com uma mão;
- alvo de toque mínimo de 44 px;
- pouca digitação;
- login opcional;
- sem jargão operacional;
- estados simples e verdadeiros;
- uma ação primária clara por etapa;
- nunca fazer Table parecer unidade financeira;
- nunca expor detalhes internos do floorplan staff para guest.

## Fluxo completo

```text
QR da Table
  ↓
resolver Table
  ↓
placement existe?
  ├─ não → localizar no mapa 2D
  └─ sim → usar contexto atual
  ↓
criar / entrar em Tab
  ↓
Cardápio
  ↓
enviar Order
  ↓
Cardápio continua ativo
  ├─ Pedidos → acompanhar / pedir novamente
  ├─ solicitar atendimento → Dispatch
  └─ Conta → total / pagamento quando suportado
```

## Referências

- `specs/004-table-guest-ordering/spec.md`
- `docs/adr/0004-tab-identity-and-table-occupancy.md`
- `docs/adr/0006-dynamic-table-placement-and-floorplan.md`
- `docs/domain/model.md`
- `docs/design/system.md`
