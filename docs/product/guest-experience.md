# Guest Experience — UX do cliente

Este documento define a experiência canônica do cliente no Rodada e complementa a Spec 004 e o Design System. **A decisão de UX 2.0 de 16/10/2026 tem precedência sobre descrições históricas do MVP:** [contrato Mesa/Ficha/Híbrido](../../specs/004-table-guest-ordering/guest-ux20-contract.md). Não confundir protótipo de UX com implementação Web já homologada.

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

## Modo de operação: Mesa, Ficha ou Híbrido

O **gestor** escolhe no Manage e o **QR/ponto de acesso** resolve a experiência. O cliente não escolhe o modo.

- **Mesa:** QR permanente de Table; bebidas e comidas configuradas para servir na mesa; entrega por Bar/Cozinha.
- **Ficha:** QR de BAR/Pista, Tab sem mesa, código FG84 na ficha/fila do bartender; **somente bebidas e retirada no bar**, sem cozinha, sem comida ou combos mistos.
- **Híbrido:** mesas e ficha simultaneamente dentro do mesmo Venue, de acordo com QR/área; não fundir identidades ou cobranças.
- **MVP:** gerente altera manualmente a configuração; turnos automáticos ficam fora. Mudança de modo afeta novas sessões, nunca converte Tab/ledger/sessões existentes.

Este modo de **experiência do Venue** é independente do controle técnico Table.guest_ordering_mode (DISABLED/JOIN_ACTIVE/DIRECT).

## Navegação

A experiência cliente UX 2.0 possui **exatamente dois destinos principais**:

- **Mesa:** Pedir | Minha comanda.
- **Ficha:** Pedir | Minha ficha (com subtela Conta e pagamento).

**Não existe Agora guest** nem tela independente de Pedidos. Pedir é a home operacional do cliente: após enviar, permanece no cardápio e mostra confirmação compacta visível, sem navegação forçada.

### Pedir e repetir

Quick-add prioritário, detalhes apenas para variantes/observações. **Mais uma rodada** permite desmarcar itens e ajustar quantidades, confirmar uma única vez e já enviar. Produtos que deixaram de estar disponíveis exigem revisão do carrinho; pedidos cancelados não são sugeridos como repetição.

### Acompanhar pedidos

**Minha comanda** reúne status resumidos de todos os pedidos ativos (Recebido / Preparando / Pronto-chegando), dois mais relevantes em destaque, Ver todos e saldo. Consumo detalhado e histórico financeiro ficam recolhidos, pagamento é acessível e a ação de ajudar fica no cabeçalho.

**Minha ficha** prioriza código FG84, Pronto para retirar, Em andamento e histórico recolhido; retirada é opcional, sem scan ou confirmação obrigatória. A Ficha possui apenas uma entrada de **Conta e pagamento**.

As telas não inventam microestados/entregas que o staff não confirmou. O resumo persistente não precisa de aba própria.

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
  ├─ Minha comanda / Minha ficha → status, repetição e saldo
  ├─ solicitar atendimento → Dispatch
  └─ Conta e pagamento (subtela da ficha / comanda) → pagamento
```

## Referências

- `specs/004-table-guest-ordering/spec.md`
- `specs/004-table-guest-ordering/guest-ux20-contract.md`
- `docs/design/guest-ux20-two-tab-navigation.md`
- `docs/adr/0004-tab-identity-and-table-occupancy.md`
- `docs/adr/0006-dynamic-table-placement-and-floorplan.md`
- `docs/domain/model.md`
- `docs/design/system.md`

## Escopo operacional entregue versus roadmap — 14/10/2026

No MVP, localização é Zone textual e acesso é GuestSession de dispositivo.
**Nota histórica (MVP antes da decisão UX 2.0):** navegação Cardápio/Pedidos/Conta usava atalhos persistentes com foco nas regiões
montadas; não perde draft nem confirma pedido ao navegar. Microestados são
projetados como Recebido/Preparando/Pronto-chegando; entrega e cancelamento
exigem fato canônico. O mapa e seus fluxos acima são intenção futura (#144),
grupo #145, código/QR de Tab/NFC #146, perfil/claim #147 e relatórios #148.
Não exigir mapa/código/login no pedido anônimo. Ver Spec004/closeout.md.
