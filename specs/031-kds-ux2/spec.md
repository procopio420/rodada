# Spec 031 — Rodada KDS UX 2.0: Bar, Cozinha e Expedição

**Estado:** intenção de produto/UX documentada; **não implementada no aplicativo real e não homologada**.  
**Data:** 2026-10-17.  
**Referência de UI:** [protótipo navegável](../../prototype/ux2/kds-bar-cozinha.html) (branch `codex/kds-ux2-raw-preview`, versão polida no commit `f9be812`).  
**Owners funcionais:** Production (Bar/Cozinha), Dispatch/Passe, Venue/Configuração; Ordering/Corrections e Reliability conservam seus contratos.  
**Relacionado:** [princípios](../../docs/product/principles.md), [design system](../../docs/design/system.md), [Spec 001](../001-core-pos/spec.md), [Spec 003](../003-dispatch/spec.md), [Spec 010](../010-product-modifiers-variants/spec.md), [Spec 013](../013-venue-configuration/spec.md), [Spec 014](../014-connectivity-degraded-operation/spec.md), [Spec 017](../017-order-corrections-exceptions/spec.md), [Spec 023](../023-updated-prototype-visual-parity/spec.md), [Spec 026](../026-operational-ux-friction/spec.md), [ADR 0018](../../docs/adr/0018-idempotent-production-batches.md).

> **Fonte de verdade:** este documento especifica o comportamento desejado para implementação. O HTML é uma simulação local; não demonstra integração com Django/PostgreSQL, staff auth, SSE, impressoras, permissões ou reconciliação offline. Se divergir de contratos de domínio já aceitos, não copiar a simulação: abrir decisão de contrato/ADR e ajustar os critérios antes de alterar a API.

## 1. Problema, objetivos e não objetivos

**Operadores:** bartender em ambiente ruidoso com fila de bebidas e ficha; cozinheiro com comandas e modificadores; expedidor que coordena itens e mesas. Dispositivos: celular de apoio, tablet touch à bancada e PC/monitor fixo, inclusive orientação retrato e paisagem.

**Job to be done:** reconhecer o próximo trabalho, preparar e concluir itens com o mínimo de interações, identificar imediatamente riscos e alterações, encaminhar o que está pronto e sobreviver a picos/perda de conectividade **sem inventar preparo, retirada ou entrega**.

**Objetivos:**
- Ticket-first: pedido e itens acionáveis ocupam a maior parte da tela; não um dashboard de métricas.
- Uma ação primária por linha; exceções e gestão por divulgação contextual, sem esconder risco.
- Fila estável por ordem de chegada; destaque de urgência sem salto inesperado de cartões.
- Modificadores e restrições de cada unidade identificáveis; sem mesclar linhas incompatíveis.
- Estados de Bar, Cozinha e Expedição independentes por item e estação.
- Passe útil mesmo sem taps de confirmação obrigatória de retirada; dados históricos sempre rastreáveis.
- Mesma semântica em 360–1920 px, touch/mouse/teclado/tecnologias assistivas.
- Estados pendentes, stale e ambíguos explícitos, com autoridade na API.

**Fora do escopo:** PDV de venda no KDS, cobrança, limite de crédito, ledger, emissão fiscal, inventário profundo, alteração silenciosa de pedido, sincronização P2P/offline plena, impressão efetiva no protótipo, telemetria inferida como confirmação, autenticação por código FG84, obrigatoriedade de expedição ou de registro de retirada.

## 2. Entidades e invariantes

1. `Order` pertence a `Tab`; mesa e `TableOccupancy` dão **contexto de destino**, nunca identidade/autorização. Uma mesa pode ter várias Tabs; usar IDs canônicos estáveis internamente.
2. `OrderItem` é a unidade canônica do preparo; agrupar por `order_id` para exibição não funde estados, quantidades, personalizações ou estações.
3. Roteamento de `Product.fulfillment_station` separa `BAR` e `KITCHEN`. **Modo ficha/retirada no bar só contém itens elegíveis de Bar, nunca comida da Cozinha**. `FG84` é referência visual curta, não token de acesso.
4. Pedido confirmado preserva snapshot (produto, variante, modificadores, nota, preço histórico) mesmo após indisponibilidade. Item “1 sem cebola” aparece em linha própria se difere do outro.
5. Informação de alergia/restrição crítica não é mero detalhe de estilo: identificação textual, acesso à orientação, possibilidade de suspender e escalar; conclusão por lote não ignora restrições.
6. `NEW/ACCEPTED/PREPARING/READY/PICKED_UP/DELIVERED` e correções são **eventos de domínio**, não simples flags de UI. Não regredir `READY` para “em preparo” ao desfazer erro; usar correção/refeitura auditável.
7. `READY` significa pronto, **não** entregue; passagem do tempo não gera `PICKED_UP` ou `DELIVERED`. Retirada opcional não pode ser exigida para medir staff.
8. SSE apenas notifica/atualiza; confirmação, permissão, consistência e idempotência vêm do servidor. Não enviar novamente uma mutação com ACK perdido usando chave nova.
9. Disponibilidade de produto é única por Venue/canais; mudar disponibilidade afeta novas confirmações, não apaga produção já confirmada.
10. Priorizar autonomia em bares pequenos: `modo simples` funciona sem expedidor separado; `modo expedição` é configuração opcional e **não** cria etapa mandatória em cada item.

## 3. Arquitetura da informação

| Área | Bar | Cozinha | Expedição (opcional) |
| --- | --- | --- | --- |
| **Pedidos** (padrão) | Tickets de bebidas, ficha FG84 ou mesa; conclusão rápida | Tickets de pratos, nota e segurança; preparo individual | Não é necessário abrir para “confirmar” uma retirada |
| **Passe** | Bebidas prontas para servir/retirar; código/mesa destacados | Pratos prontos; contexto de destino | Abertura diretamente nos prontos do pedido/mesa escolhido |
| **Resumo por produto** | Quantidade ainda pendente por bebida | Quantidade pendente por prato | Visão consultiva, sem comandos de lote ocultos |
| **Expedição** | Não apresentada no protótipo da estação Bar | Opcional, agregando estado Bar + Cozinha por pedido | Mostrar quem falta, quem está pronto e o próximo passo |
| **Ajustes** | SLA ilustrativo, som, fonte, disponibilidade | Idem + modo expedição | Configuração por Venue/capability, não por botão público sem guarda |

Na produção, **Ferramentas de simulação** e seletor de dispositivo/estação do HTML desaparecem. Acesso real é por rota, estação autorizada e sessão da equipe. O controle de conectividade é *indicador*, não um interruptor de “online” real.

## 4. Jornada e ação principal

### 4.1 Entrada / ticket novo
1. Um pedido confirmado gera itens dirigidos à estação correta; a fila mostra destino, referência de pedido, idade, quantidade, nome e customizações.
2. O ticket novo recebe marcador textual **NOVO** e aviso persistente, inclusive enquanto o operador estiver no Passe, Expedição ou Ajustes; som é **opt-in** e complementar.
3. O operador pode ir direto ao ticket pelo aviso. Reconhecer trabalho não deve exigir clique separado; o marcador desaparece a partir de uma interação significativa ou de reconhecimento explícito conforme contrato final — nunca apenas pelo decurso do tempo.
4. A fila usa ordem de entrada estável; prioridade e atraso aparecem por indicador sem remanejamento inesperado durante o preparo.

### 4.2 Preparo por item
- **Bar / bebida de pronta entrega:** ação principal `Marcar pronto` ou `N prontos`, sem obrigatoriedade visual de “iniciar preparo”. O adaptador de API executa **somente transições legalmente aceitas**. Se o servidor exigir transição intermediária, implementar comando autoritativo idempotente ou explicitar a etapa; não fingir transição aceita.
- **Cozinha:** ação principal orientada ao trabalho, preferencialmente `Marcar pronto` para o operador que já executou o preparo; `Marcar em preparo` é ação complementar, não tap de telemetria obrigatório. Validar compatibilidade com política canônica antes de habilitar CTA.
- **Quantidade parcial:** `1 pronto`/quantidade explícita não deve transformar parcialmente um `OrderItem` único como se o modelo atual suportasse isso; requer projeção/contrato de unidade/lote idempotente e estado derivado correto. Até existir, UI não deve oferecer ação falsa.
- **Conclusão coletiva:** somente com pelo menos duas linhas compatíveis e verificadas, na mesma estação, sem restrições críticas, alterações pendentes, bloqueio ou status desconhecido; contrato de batch atômico com recibo/versão (`ADR 0018`). Nunca equivale a confirmar uma entrega.
- Atualizar o ticket sem perder scroll/foco; retirar da fila apenas após confirmação canônica; manter feedback e opção de consultar Passe.

### 4.3 Restrições alimentares e incapacidade de preparar
1. Ticket expõe marcador textual **ALERGIA / RESTRIÇÃO CRÍTICA** e nota completa sem depender de cor.
2. Operador abre `Conferir alergia`; verifica ingredientes, equipamentos e risco de contato cruzado. Confirmação de leitura **não é garantia de segurança** e não suprime autorização necessária.
3. Caso não seja possível assegurar o preparo, `Não consigo preparar com segurança` suspende a liberação operacional e solicita responsável; status e responsável/atualização são auditáveis. Não usar apenas flag local.
4. Reavaliação exige permissão e instruções válidas; até então, o item não é marcado pronto, entregue ou agrupado num lote.
5. Um pedido com modificação depois de confirmado segue Spec 017; **não editar o snapshot original**.

### 4.4 Mudanças recebidas / correções
- Alteração ou cancelamento recebido deve gerar aviso persistente em qualquer área e no ticket afetado, com `Revisar alteração recebida`.
- Revisão não modifica itens automaticamente e não pode simplesmente “dar como lida” uma solicitação que continua dependendo de autorização. Exibir claramente `solicitado`, `aguardando gerente`, `aplicado`, `recusado` e `erro/reconciliar`.
- Cancelamento permite quantidade inteira válida de unidades **remanescentes** (ex.: cancelar 1 de 3), com motivo, regra de pagamento, estágio e autorização conforme Spec 017. Uma solicitação em preparo não subtrai produção até aplicação canônica autorizada.
- Refeitura/replacement cria **novo OrderItem** vinculado à origem e mantém marcos financeiros/operacionais originais.
- Mensagens “simular aprovação”, “simular recusa” e mudança de estado local existem **apenas** no HTML.

### 4.5 Passe e retirada sem tap obrigatório
- Passe mostra **itens prontos recentes**, com quantidade e destino. Para ficha, código curto visível para conferência verbal/visual; bartender não precisa escanear ou confirmar cada retirada.
- Itens prontos antigos saem do foco primário para uma seção claramente rotulada **sem retirada registrada**; continuam encontráveis por pedido/código/mesa e **não** são promovidos a entregues.
- Expedição abre Passe **filtrado por `order_id` canônico**, não somente por nome de mesa, incluindo itens antigos daquele pedido. Deve haver `Ver Passe geral`.
- Interações de registro de retirada podem existir como conveniência/exceção e precisam conservar `PICKED_UP` distinto de `DELIVERED`; inferências de saída mostram proveniência.
- Evitar “lista infinita”: estratégia de retenção/arquivamento é **visual**, não mudança inventada de estados ou limpeza da responsabilidade de dispatch.

### 4.6 Expedição
- **Modo simples:** Bar/Cozinha sinalizam pronto; não há nova confirmação obrigatória.
- **Modo expedição:** cartão por pedido reúne Bar e Cozinha, mostra `prontos/esperados` por estação e a próxima dependência (“Aguardando Cozinha”, “Aguardando Bar”, “Prontos para encaminhar”). Apenas ações contextualmente válidas.
- Não concluir um pedido misto só porque os itens de uma estação estão prontos; preservar despacho parcial quando a política permitir, evitando presumir sincronização simultânea.

## 5. Fila, alertas e densidade

- **Atraso:** marcador textual + cronômetro, parametrizado por Venue/estação e, futuramente, por classe de preparo. **5 min Bar, 12 min Cozinha e 9 min de Passe no HTML são exemplos**, não SLA real, nem justificativa para autoconcluir/entregar.
- **Novo pedido:** sinal persistente até reconhecimento adequado, inclusive fora da Fila; clicar leva ao ticket exato. Eventos não duplicam cartões após reconexão.
- **Alteração:** alerta distinto de “novo”; preservar a notificação até resolução/revisão autorizada, sem tocar em itens imutáveis.
- **Fila:** manter posição durante atualizações. Marcadores de “prioridade” e “atrasado” não reordenam o DOM imprevisivelmente.
- **Resumo por produto:** somar unidades ainda pendentes somente para consulta. Não mesclar de forma executável variações de preparo, modificadores, alergias ou estações.
- **Visual:** tickets com destino, itens e CTA dominante; ações administrativas e impressão dentro de “Outras ações”, nunca competindo com preparo. Impressão utiliza mecanismo da Spec 028/015 quando disponível, com feedback de falha/reimpressão.

## 6. Responsividade e acessibilidade

| Contexto | Comportamento |
| --- | --- |
| Celular 360 / 390 / 430 px | Uma coluna, fila rolável **dentro da área de trabalho**, navegação inferior sempre acessível, safe-area, labels compactos, ações de preparo de preferência 56 px; não esconder informação crítica por falta de espaço |
| Tablet 768 / 850 / 1024 px | Grade touch-first adaptativa (tipicamente duas colunas quando há largura), sem redução artificial por `transform: scale`, suporte paisagem/retrato |
| Desktop 1280 / 1440 / 1920 px | Grade mais densa (tipicamente três colunas), visibilidade simultânea de vários tickets, suporte teclado/mouse/monitor a distância |
| Texto ampliado | Ajustes de fonte/densidade; reflow a 200%, sem clip de modificadores/alertas/CTA |
| Teclado/leitor de tela | Alvos >=44 px, principais de produção preferencialmente 56 px; foco visível/preservado, etiquetas e status textuais, diálogo com trap de foco e retorno à origem, ``aria-live`` proporcional sem tempestade de anúncios |
| Movimento/áudio | Reduzir animação com `prefers-reduced-motion`; som opcional acionado após gesto |

Medidas de breakpoint são contratos de teste, não garantia de que **toda** largura já foi validada em hardware. O protótipo deve funcionar sem zoom CSS; implementação real deve usar tokens/componentes do design system.

## 7. Matriz de estado por item e UI

| Fato canônico / fluxo | Apresentação | Ação permitida | Recuperação |
| --- | --- | --- | --- |
| NEW/ACCEPTED | Aguardando | Iniciar/concluir **se a API permitir** | Versão divergente → nova leitura |
| PREPARING | Em preparo | Concluir item ou lote válido | Intent idempotente + readback |
| READY | Passe; tempo de espera | Retirada opcional/exceção | Não regredir READY diretamente |
| PICKED_UP | Retirada registrada com origem | Entrega/correção autorizada | Não inferir entregue |
| DELIVERED | Histórico/expedição concluída | Exceção apropriada | Não reabrir item antigo |
| Pedido alterado | Alerta pendente | Revisar/solicitar gerente | Aplicar somente via Spec 017 |
| Alergia crítica | Destaque e bloqueio quando cabível | Conferir/escalar | Permissionamento de reavaliação |
| Correção solicitada | Pendente de autorização | Aguardar decisão | Não subtrair linha antecipadamente |
| Refeitura aprovada | Novo item vinculado à origem | Produzir novo item | Histórico original intacto |
| Realtime indisponível, API saudável | `Reconectando`/`Desatualizado` | Mutação só após guarda de frescor/versão | Snapshot e replay SSE |
| API indisponível / ACK perdido | Offline/incerto + último estado confirmado | Não repetir ação nova | Retry com **mesmo** payload/key, reconciliação conforme Spec 014 |
| Sem permissões/sessão expirada | Ação oculta/bloqueada com motivo | Reautenticar | Sem mutação no tenant errado |
| Fila vazia | “Tudo em dia” | Navegar para Passe/Resumo | Não apagar histórico |

## 8. Dependências de implementação — NÃO copiar como prontas

| Frente | Situação observada no código/documentos | Decisão de integração |
| --- | --- | --- |
| Fila `ProductionBoard` | UI Web real existe, com `station=BAR/KITCHEN`, estados e ações por item/lote | Substituir apresentação em slices, manter endpoints/guards existentes |
| Single transition | `NEW/ACCEPTED → PREPARING` e `PREPARING → READY` são caminho usado pelo board; `ADR 0018` exige `PREPARING` para READY por lote | CTA “Pronto” direto precisa backend válido/adaptador seguro, ou passo explícito; não bypass |
| Preparo parcial | HTML soma `ready` localmente por unidade | Exige contrato de quantidades e efeitos em Dispatch, auditoria, idempotência |
| Correção parcial | Spec 017 restringe efeitos conforme etapa e pagamento | UI consulta políticas/revisão real; aprovação não é botão client-side |
| Alergia e bloqueio | HTML apenas simula `blocked`/`acknowledged` | Definir onde eventos e permissões são persistidos, e regra de suspensão/liberação |
| Expedição/retirada | HTML usa valores locais e Passe filtrado | Basear em Dispatch/OrderItem canônico e proveniência de milestones |
| Mudança de pedido | HTML produz `notice` fictício | Consumir eventos de correção/edição auditáveis; não tratar “recebido” como “aplicado” |
| Impressão | HTML só notifica | Integrar com impressão real e fallback configurado |
| Conexão | HTML liga/desliga bool, bloqueia mutações | Seguir Spec 014: API x SSE x freshness e journaling, sem inventar fila offline |
| Disponibilidade | HTML altera estado em memória | Reutilizar fluxo canônico versionado de Venue/Catálogo |

## 9. Critérios, decomposição e evidência

Veja [plan.md](plan.md) para slices e migração segura, [tasks.md](tasks.md) para execução por agente e [acceptance.md](acceptance.md) para cenários Given/When/Then e gates. Nenhum checkbox de integração/validação foi aprovado por esta documentação.

**Perguntas que exigem decisão antes de codar:** contrato de `READY` direto para bebidas; representação parcial de `OrderItem`; permissões/entidade persistida para bloqueio de alergia; política de expedição e recorte de itens prontos; limiares operacionais e se sinal de “visto” precisa de ack explícito. A implementação não deve escolher a resposta apenas pelo comportamento fictício do protótipo.
