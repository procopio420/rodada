# Rodada UX 2.0 — P0/P1: confirmação, recuperação e menos fricção

**Data:** 2026-10-16. **Escopo implementado:** protótipo HTML isolado, sem serviço remoto, banco, gateway ou mudança no app publicado. **Status:** comportamento de UX demonstrável; integração real ainda precisa dos gates de domínio abaixo.

## Resultado UX

| Prioridade | Problema observado | Decisão aplicada no protótipo |
| --- | --- | --- |
| P0 | Toast depois do envio não comunica onde o pedido está | O workspace da Tab exibe **Pedido SIM-xxxx confirmado · simulação**, com os itens e rotas **Bar / Cozinha · Na fila (simulação)**. Persistente ao navegar entre telas enquanto a página está aberta. O CTA Adicionar itens permanece prioritário. |
| P0 | Resposta incerta induz reenvio e pedido duplicado | Envio cria intenção congelada \`key\`, destino, itens, preços totais da demo; no cenário de resposta perdida mostra **Envio sem confirmação** e botão **Verificar envio · mesma intenção**, preserva o rascunho e impede segundo envio daquela Tab até reconciliação. |
| P1 | Revisão do pedido obrigatória acrescenta clique | Catálogo envia diretamente após selecionar itens; **Ver resumo** é opcional, com destino visível no catálogo e possibilidade de ajustar quantidades. Não inventar confirmação extra quando operador já decidiu. |
| P1 | Mais uma rodada passa por revisão dupla | Selecionar/ajustar itens → **Repetir rodada · enviar**, sem tela obrigatória intermediária. Se há rascunho/resultado incerto, não mistura pedidos silenciosamente. |
| P1 | Voltar elimina contexto do operador | A navegação preserva seleção da Tab, filtros, rascunho por Tab e estado desconhecido. Depois de pedido confirmado, Voltar da comanda com mesa retorna **àquela mesa**; trocar de Tab não apaga o rascunho da anterior. |
| P1 | UX em pico e mobile | Ação primária permanece acima do resumo persistente; card de limite continua compacto. Controles de simulação ficam recolhidos por padrão sob detalhe técnico, não como etapa do garçom. |

## Não confundir o demo com garantia de rede

O HTML **não envia pedidos**. \`state.orderIntents\` / \`tab.orders\` são memória JS efêmera; atualizações de Bar/Cozinha são legendas de fixture. No exemplo, a perda de resposta é acionada em **Cardápio → Teste de conexão (simulação)**. Clicar **Verificar envio** imita um readback positivo; **não é** um pedido reconsultado por API.

Recarregar a página **apaga** essa memória: o protótipo não garante recuperação pós-restart, e não deve declarar operação offline funcional. Não associar um novo \`Order\` a uma tela só porque o botão foi tocado.

### Contrato para integração real

1. **Intenção canônica:** gerar \`idempotency_key\` persistível por tentativa legítima de novo pedido, amarrada a \`venue_id\`, \`tab_id\`, \`source\`, destino/occupancy quando aplicável, e fingerprint de linhas/canonical pricing. Guardar antes do primeiro envio, não criar nova chave ao perder ACK.
2. **Confirmar:** usar \`confirm_order\` e replay existentes (Spec 001/002), mantendo bloqueio transacional, locks e proteção de preço/disponibilidade. O cliente só declara \`CONFIRMED\` após resposta/readback canônico com \`order_id\`, \`tab_version\` e \`OrderItem\` confirmados.
3. **Destino:** derivar \`fulfillment_station_snapshot\` de cada item e routing resultante — não inferir que “Bebidas = Bar” em produção. UI deve distinguir \`CONFIRMED\`, \`ACCEPTED\`, \`PREPARING\`, \`READY\` e \`DELIVERED\`; “encaminhado” não significa aceito nem entregue.
4. **Falha / timeout:** \`UNKNOWN\` não é falha definitiva e não é sucesso. Congelar a mesma intenção e evitar um segundo envio. Reconciliar pelo ID/chave da requisição via estado do servidor; se o endpoint atual não oferece lookup suficiente, acrescentar **read-after-write** sem criar pedido duplicado. Replays com mesma key + mesmo fingerprint devolvem resultado anterior; payload divergente gera conflito.
5. **Persistência móvel:** Android deve armazenar a intenção mínima até o readback, com lifecycle/restart e política segura de dados; Web deve tratar refresh e reconexão sem perder a intenção não resolvida, respeitando privacidade/armazenamento. Reconstruir após recuperar sessão autorizada; nada de guardar token Guest inseguro.
6. **Concorrência:** versões de Tab, estado da ocupação, limite por Venue \`WARN_ONLY/ENFORCE\` (Spec 031) e preços são revalidados no servidor. Se uma Tab encerra ou muda destino, rejeitar ou pedir correção; nunca “retomar” pedido para outra Tab por associação de mesa.
7. **Sem cliques extras:** o resumo do pedido é opcional; a confirmação explícita é o toque **Enviar**. Em erro recuperável, oferecer Verificar e ação de correção clara sem mudar destino. Manter visível a origem, a pessoa e a comanda.
8. **Erro definitivo:** diferenciar \`PRODUCTS_NOT_CONFIRMABLE\`, \`SPENDING_LIMIT_EXCEEDED\`, auth, Tab CLOSED, conflito e resposta desconhecida. No modo WARN_ONLY, limite só é aviso; outros erros continuam bloqueando de acordo com suas políticas.
9. **Acessibilidade:** \`aria-live\`/status persistente, foco/teclado, medidas 320/360/390/430dp, densidade de conteúdo e modo de alto movimento.

## Jornadas de regressão

- Um pedido de uma bebida na Tab de Marina abre envio direto do cardápio; status confirma ID, Bar e valor. Navegar para outra Tab e voltar preserva confirmação.
- Pedido de comida e bebida roteia para **duas estações** no mesmo card (somente fixture; integração deve usar snapshots canônicos).
- Simular resposta perdida: o saldo e o rascunho **não devem ser confirmados duas vezes**; a comanda entra em estado incerto, e um clique de reconciliação produz **um único** histórico de pedido. Não oferecer outro envio da mesma Tab até resolver.
- Manter rascunho em Marina, mudar para João, adicionar item e voltar: ambos os rascunhos continuam separados.
- **Ver resumo** e Voltar preservam quantidades; o envio também funciona sem abrir resumo.
- Mais uma rodada confirma após seleção, sem duplicar outro rascunho presente; mudança de limite bloqueia/apenas alerta conforme política de tenant.
- Pagamento parcial, fechamento, entrega e liberação da mesa continuam independentes de status de pedido não confirmado.
- Validar Android 360/390/430, fontes ampliadas, toque em pico, múltiplos estados, sleep/reconnect, refresh e app process death antes de rollout.

### Evidências desta iteração

Testes JavaScript/DOM sintéticos com fixtures cobrem navegação, fluxo direto, perda simulada de resposta, reconciliação sem repetir saldo, rascunhos separados, repetição, limite e pagamentos. **Não equivalem a teste de navegador ou validação visual do Android.** Screenshots móveis e E2E integrado ainda são gates abertos.

## Fora do escopo

Não foi criada nova tela principal, feature de pagamento, fluxo de entrega por mapa, gateway de recuperação de rede, Worker offline, schema financeiro ou alteração da aplicação Android/Web de produção.

Links: [UX 2.0 README](README.md); [limites e garantias](limits-and-guarantees.md); [fechamento e giro da mesa](settlement-and-table-turnover.md); Spec 001, 002, 004, 031 e issue E2E #106.
