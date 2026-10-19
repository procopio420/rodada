# Rodada UX 2.0 — Perfil, progress bar de limite e garantias

**Status:** experimento de UX, não integração. **Data:** 2026-10-16. **Referência canônica:** `specs/002-house-account/spec.md`, `docs/adr/0011-house-account-policy-snapshots-and-operational-approval.md`, `specs/002-house-account/acceptance.md`.

## Decisão de interface

A capacidade operacional deve ser uma **barra de progresso visível na comanda**, no catálogo e na revisão, sem se tornar mais um passo obrigatório. A composição é:

- Título **Limite de consumo**, perfil local da Tab e valores **R$ consumidos de R$ limite**.
- **Capacidade disponível** em números, sem obrigar o operador a inferi-la pela cor da barra.
- Segmento sólido = **exposição atual confirmada** (no protótipo, saldo fictício); segmento listrado = **novo pedido em rascunho**, que ainda não foi confirmado.
- Marca sutil em **80%** com mensagem textual de atenção; 100% ou projeção acima do limite mostram status explícito e ações contextuais.
- Ao ultrapassar, a barra não finge ter mais de 100%: o excedente aparece em texto preciso. **O botão só fica bloqueado quando o tenant está em ENFORCE**; em WARN_ONLY a venda continua sem confirmação extra. A barra permanece um resumo visual, não um atestado de autorização.
- Limite zero não produz porcentagem/progressbar enganosa. Em **WARN_ONLY** é um aviso e não impede venda; em **ENFORCE**, novos pedidos com consumo positivo ficam bloqueados.
- **Ver detalhes** é opcional e abre perfil/snapshot, limite, exposição, capacidade, pedido projetado, estado de garantia e opções para resolver. Não expor históricos administrativos em toda tela.

## Dados disponíveis na Spec 002

Perfis por Venue (defaults **apenas demo**):

| Perfil | Limite demo |
| --- | ---: |
| VISITOR / Visitante | R$ 30 |
| KNOWN / Conhecido | R$ 80 |
| REGULAR / Regular | R$ 200 |
| HOUSE / Da casa | R$ 500 |
| RESTRICTED / Restrito | R$ 0 |

Uma Tab usa o snapshot de política na abertura. Atualizações de relacionamento não mudam silenciosamente uma Tab em andamento. A projeção canônica já suporta `relationship_snapshot`, `effective_limit_cents`, `remaining_capacity_cents`, `exposure_cents`, `percentage_used`, `limit_warning`, `consumption_blocked`, `approval_requested`, `action_reasons` e `override_expires_at`.

**Somente o servidor decide se um pedido cabe no limite.** O valor do catálogo e do rascunho é prévia, sujeito a revalidação de preço, taxa e estado do ledger. Uma regra independente em REQUIRES_ACTION não é apagada por recebimento ou autorização de limite.

## Recuperação operacional

- Ao atingir/ultrapassar o limite, mostrar aviso e oferecer opções **não obrigatórias**: receber parte da conta (mantendo rascunho e Tab aberta) ou solicitar aumento à gerência. Em WARN_ONLY o garçom continua vendendo. Em ENFORCE, o sistema mantém o draft e pede resolução sem criar Order.
- Override real é ação exclusiva de gerente com capability, PIN/reautenticação recente, motivo, novo limite total, expiração até 24h e idempotência, segundo Spec 002. O garçom não aprova seu próprio pedido.
- Recebimento parcial só reduz exposição depois de confirmação financeira canônica; não criar Payment no frontend. Reconnect e volta do aplicativo revalidam capacidade; cache não autoriza gasto.
- Restrito/limite zero sinaliza o perfil operacional; **não equivale a proibição universal de venda**. O comportamento de novos pedidos depende do modo efetivo do tenant. Não supor que existe antecipação integrada.
- Se o envio foi tentado e a resposta é incerta, preservar a intenção original e conciliar; não reenviar outro pedido automaticamente.

## Garantia financeira não é limite

A ADR 0011 determina que aprovação operacional **não cria garantia financeira**. Não afirmar cartão pré-autorizado, caução depositada, PIX pago, crédito pré-pago ou saldo garantido sem eventos e registros canônicos.

Evoluções futuras separadas:
1. Pré-autorização/captura/liberação de cartão por PSP com prazo e reconciliação.
2. Depósito reembolsável com passivo em ledger segregado e fluxo de devolução.
3. Crédito pré-pago com origem de fundos, consumo e restituição auditados.

Até lá, o protótipo mostra **garantia não registrada na simulação**. Aumento de limite não vira cobrança, cartão reservado nem dinheiro confirmado.

## Exemplos fictícios da navegação

- Marina, Regular: R$ 56 usados de R$ 200 (28%); R$ 144 disponíveis.
- Rafael, Visitante: R$ 14 usados de R$ 30 (~47%); batata de R$ 28 em faixa listrada excede R$ 12. Com WARN_ONLY ele pode enviar informado; com ENFORCE, precisa receber valor parcial ou obter aprovação. Receber R$ 13 na simulação deixa saldo de R$ 1 e permite o pedido em ambos os modos.
- João, Visitante: R$ 28 de R$ 30 (~93%), estado de atenção.
- Carla, Conhecido: R$ 22 de R$ 80.
- Bruna, Da casa: R$ 93 de R$ 500.
- Balcão 1, Restrito: referência zero; WARN_ONLY informa e permite prosseguir, ENFORCE bloqueia novos pedidos positivos.

Tudo ocorre no HTML `prototype/ux-2-0/index.html` em memória, com saldo/pagamento/aprovação **fictícios**. Não há autorização de gerência real, garantias, efeitos no banco ou PSP. **12/12 verificações de navegação/estados do modo configurável passaram em JS/DOM simulado**, sem teste de layout no Chrome Android nem validação no app integrado.

## Gates de implementação

- Reusar a projeção canônica, e não inferir perfil pelo nome, sem criar outro policy engine no cliente.
- Componente visual único para Android e Web equivalente: 360/390/430dp, fonte ampliada, TalkBack/VoiceOver e status em texto (não só cor).
- Testes de 0%, 79%, 80%, 99%, 100%, limite 0, over-limit, pagamentos parciais, concorrência, expiração de override, outra causa REQUIRES_ACTION e resposta ambígua.
- Validação física de tarefa: ninguém precisa abrir `Ver detalhes` em toda comanda; barra deve orientar e não ocupar excessivamente a tela durante pico.


## Decisão nova — enforcement configurável por tenant

**Contrato de produto desejado:** enum explícito \`WARN_ONLY | ENFORCE\` por tenant. No modelo atual do Rodada, a fronteira operacional de isolamento é \`Venue\`; portanto o armazenamento efetivo deverá ser **uma configuração por Venue (bar/tenant operacional)**, sem criar uma entidade \`Tenant\` não existente apenas para a UI. Se o produto futuramente introduzir uma organização com vários Venues, a política deverá definir herança/override sem afetar isolamento financeiro.

| Modo | Leitura e feedback | Novo pedido acima do limite | Recebimento parcial |
| --- | --- | --- | --- |
| \`WARN_ONLY\` | Exibir barra, perfil, exposição e excedente sem um modal obrigatório | **Permitido**, com aviso passivo ao garçom | Permitido, reduz exposição quando confirmado |
| \`ENFORCE\` | Mesmo aviso, informando bloqueio do modo configurado | **Negado pelo backend** sem criar Order/Charge; preservar intenção | Permitido, restaura capacidade se não houver outros bloqueios |

A configuração é administrada em **Gerência → Políticas de consumo** por ator com permissão gerencial e reautenticação recente, versionada e auditada com ator, valor anterior, valor novo e data. Não é controlada por waiter, Guest, Caixa ou parâmetro de pedido. A prévia no protótipo dentro de \`Ver detalhes\` é exclusivamente um controle de **simulação** para comparar os modos, não uma decisão de autorização de staff.

**Valor padrão / migração:** o protótipo inicia em \`WARN_ONLY\`, seguindo a preferência de operação de venda fluida. Entretanto, a Spec 002 implementada atualmente é **hard enforcement**. Na migração real, Venues existentes devem preservar o comportamento efetivo **\`ENFORCE\` até decisão explícita e auditada**, evitando relaxamento silencioso. A mudança para \`WARN_ONLY\` deve ser deliberada pela gerência, com versão/revisão de policy. O produto pode adotar \`WARN_ONLY\` para Venues novos depois de aprovar o risco de negócio; isso ainda não está implementado.

### Alterações de contrato necessárias antes de produção

1. Adicionar configuração tipada/versionada de enforcement por Venue. Não usar preferências locais, QR, ID do dispositivo nem estado de tela como fonte.
2. Expor no read model autorizado de Tab o **modo efetivo** e versão, preservando os limites herdados/snapshot da Relationship; o modo e o limite em si são conceitos diferentes.
3. Aplicar o modo no mesmo ponto transacional de confirmação (Tab lock + preço canônico + ledger + idempotency replay) para pedidos do staff, Caixa, Android e Guest QR. Em WARN_ONLY, ultrapassar a exposição não pode levantar \`SPENDING_LIMIT_EXCEEDED\` **por esse motivo isolado**; em ENFORCE mantém o contrato atual.
4. Rever \`REQUIRES_ACTION\` e \`SPENDING_LIMIT\`: no modo WARN_ONLY, a causa pode ser apresentada como alerta de risco **sem bloquear a venda**. Quaisquer outras causas independentes de bloqueio/autorização devem continuar intactas. Não limpar razões manualmente nem forjar autorização.
5. Mudança concorrente de modo durante um pedido deve ser decidida pela versão efetiva **no momento da confirmação canônica**. Replays idempotentes devolvem o mesmo resultado anterior. Política e ledger devem ser auditáveis e reconciláveis.
6. Aviso/UI não dispensa feedback de erro real de outras classes (permissão, disponibilidade, conflito, pagamento pendente, sessão revogada, fechamento financeiro, perda de conexão). A frase **"nunca bloquear a venda"** se refere **ao limite de consumo sob WARN_ONLY**, não a contornar validações essenciais.
7. Aprovação gerencial/override de limite, prazo e motivo da ADR 0011 continuam distintos da configuração de modo e **não representam garantia financeira**.

### Testes de integração necessários

- Matriz WARN_ONLY × ENFORCE, com exposição 0/79/80/99/100/120%, limite zero e Restricted; staff/Android/Guest/Caixa.
- Troca de modo e limite durante requisições concorrentes, replay/timeout, em Venue A e Venue B isolados.
- Sob WARN_ONLY, outros motivos de atenção continuam impondo suas próprias regras; Payment parcial não fecha Tab nem invalida rascunho; cobrança e refund usam o mesmo ledger.
- Controle gerencial autenticado, audit, permissão negada de waiter e cliente, settings cache/revalidação, dispositivos offline.
- E2E real com API PostgreSQL e screenshots Android/Web; o protótipo não é prova de backend configurável.

**Entrega realizada nesta branch:** protótipo isolado com modo simulado e barra compacta. **Fora desta PR:** migrations, modelo/configuração real, mutation da API, override da Spec 002, deploy e rollout.
