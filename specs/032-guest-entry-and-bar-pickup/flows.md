# Spec 032 — UX handoff e matrizes de estado

## Regra de design

Operação real de pico é a referência. Uma tarefa dominante por viewport, próximo passo explícito, sem escaneamento obrigatório de ficha no bar e sem depender de confirmação humana para gerar telemetria. Padrões/tokens de `docs/design/system.md`, mobile 360–430px e touch >=44px.

## Fluxo A: criar mesa improvisada (staff)

1. `Mesas` → `+ Adicionar mesa` → identificador/Zone/posição, `Criar mesa`.
2. Assim que API confirma, mostrar mesa pronta e ação secundária contextual `Vincular QR` e `Agora não`.
3. `Vincular QR` abre scanner de tag pré-provisionada ou entrada de identificador com validação. Sucesso: `QR vinculado`. Conflito: `Esta tag está na Mesa X. Transferir?` apenas para autorizado, com aviso de impacto.
4. `Agora não`: sair sem bloqueio; badge discreto `Sem QR`, ação `Vincular` no detalhe. Não exibir pop-up em todas as aberturas.
5. Desmontar mesa temporária: confirmar encerramento físico se ocupada; liberar tag separadamente. Não apagar dados históricos.

Estado: empty → creating → created-unlinked → linking → linked | retry/error | skipped. O botão Criar não deve disparar 2 mesas num retry.

## Fluxo B: cliente na mesa

`Scan QR` → cardápio + mesa identificada (`Mesa 12`) → `Começar nesta mesa` → Tab própria anônima → `Adicionar itens` → `Revisar` → `Enviar pedido` → status canônico.

- Scan read-only: browsing, nenhuma mesa bloqueada.
- CTA cria sessão provisória/ocupação por mecanismo transacional. Segunda pessoa: `Entrar na Mesa 12`, com **minha própria comanda**; compartilhar exige ação explícita.
- Mesa já ocupada: não reabrir nova ocupação. Mesa em limpeza: `Mesa ainda indisponível` + `Chamar atendimento` quando disponível.
- Se o pedido falha: preservar itens, mostrar motivo de disponibilidade/limite e ação `Revisar pedido`.
- Se a pessoa troca de mesa: oferta `Atualizar minha mesa` no detalhe, sem forçar novo consumo.
- QR fotografado: não declarar `presença validada`; política de risco pode limitar itens e pedir verificação adicional.

## Fluxo C: QR geral / retirada

`Scan QR geral` → `Pedir para retirar` (primário) / `Continuar minha comanda` quando há sessão / `Ver cardápio` → selecionar itens → revisar com `Retirar no bar` → pagamento confirmado OU adição autorizada à comanda → `Pedido recebido`.

**Celular do cliente:**
- Número `FG84` em tipografia de leitura à distância com título `Mostre este código no balcão`.
- Itens do próprio grupo, nome do ponto de retirada, status e `Já retirei` secundário, disponível somente quando fizer sentido.
- Pagamento pendente: mostrar `Aguardando pagamento` e não exibir falsamente `Liberado`.
- `Não recebi` abre exceção discreta com suporte, sem fabricar nova venda.
- Fechar navegador: `Meus pedidos` retoma sessão com storage ou link privado; FG84 isolado não dá acesso a detalhes financeiros.

**Painel Bar:**
- Aba default `Prontos` e `Em preparo` com contadores; linha curta `FG84 — 2× Chopp — Pronto`; busca fixa `Buscar código`.
- Nenhuma confirmação compulsória. Ação opcional `Entregue`, com gestos opcionais que nunca sejam único mecanismo; `Ver` para exceção/parcial.
- Fichas velhas ocultas da fila principal vão para `Verificar`, não são dadas como entregues.
- `FG84 não consta`: buscar por código/estado, informar ao cliente `Vamos verificar no caixa` e chamar ajuda, não vender de novo automaticamente.

## Fluxo D: pagamento/saída

`Minha conta` mostra somente valor autorizado, lançamentos e estado de pagamento canônico → `Pagar minha parte` / `Pagar conta` conforme permissão → provider/caixa → `Pagamento confirmado` ou `Aguardando confirmação`.

- Conta em mesa quitada: `Sua conta está quitada`; não mostrar `Mesa liberada` nem exigir confirmação de saída.
- Guest sem mesa: `Pronto, aproveite!` ou `Seu pedido está disponível para retirada` conforme status; sem recolhimento de tag.
- Equipe libera Table quando grupo realmente sai; o status pode passar a DIRTY mesmo que Tab individual esteja fechada.
- Falha de pagamento: `Não conseguimos confirmar seu pagamento. Confira o status antes de tentar de novo.`; retry usando intenção original.

## Matriz mínima por persona

| Persona | Tarefa principal | Primeira dobra | Erro recuperável |
| --- | --- | --- | --- |
| Cliente mesa | Pedir | mesa, cardápio, carrinho | sessão vencida, indisponibilidade |
| Cliente sem mesa | Retirar | modo retirada, itens, status | pagamento pendente, código perdido |
| Garçom | Atender | Agora/mesa/comanda atual | tag conflito, sem QR |
| Bartender | Achar FG84 | prontos, busca, código/itens | código ausente/repetido, parcial |
| Caixa | Confirmar dinheiro | valor canônico, identidade autorizada | resposta desconhecida, ficha perdida |
| Gerente | Resolver exceção | bloqueios, disputa, revisão | QR abusado, entitlement sem prova |

## Cenários adversos obrigatórios

1. Cliente escaneou para ver cardápio e foi embora → sem ocupação fantasma.
2. Dois clientes entram juntos na mesa livre → 1 Occupancy e 2 Tabs privadas.
3. Grupo troca de mesa no meio de pedido de entrega → reavaliar destino explícito e mostrar encaminhamento.
4. Cliente em mesa vai ao balcão e escaneia QR geral → Tab atual continua, modalidade do novo Order = PICKUP.
5. Cliente escolhe Pix, abandona checkout → não gera ficha liberada.
6. Cliente já tem conta autorizada e quer ficha → Order cobrado na mesma Tab, sem pagamento instantâneo fake.
7. Bartender entrega sem tocar em nada → código continua consultável como estado incerto, não contabilizar entrega confirmada.
8. Cliente marca retirado mas só levou metade → retificar grupo, source preservada.
9. Última Tab paga, pessoas continuam sentadas → mesa permanece OCCUPIED até staff release.
10. Falta de rede/refresh antes de ACK → readback/replay sem duplicidade, draft conservado.
11. Tag que saiu da mesa 7 é vinculada à mesa 29 → URL antiga não revela ocupação 7 nem dá poderes sobre comanda antiga.
12. Duas pessoas mostram screenshot de FG84 → política de risco e estado legível; não prometer prova antifraude sem validação.

## Linguagem e acessibilidade

Evitar `TableOccupancy`, `PickupGroup`, `TabIdentifier`, `claim` nos rótulos. Usar `Mesa`, `Minha comanda`, `Meu pedido`, `Pronto para retirar`, `Já retirei`, `Ainda não recebi`, `Aguardando confirmação`. Código grande, texto/ícone além de cor, foco lógico, TalkBack, input/IME e fontes 200% sem truncar CTA. Dark mode alinhado ao design system; sem QR em imagem estática como prova de teste real.

## Proposta de teste de usabilidade (não executado)

Simular um turno no Santo Malte com um operador de cada função, cronometração real e roteiro de erros, sem dados reais de consumidores ou pagamentos. Observar taps por tarefa (bartender = 0 na entrega padrão), tempo para achar código, duplicidades/retrabalho e entendimento de status. Evidências precisam indicar build/SHA e dispositivo.
