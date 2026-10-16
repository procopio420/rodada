# Spec 031 — Limite de consumo por estabelecimento: alertar ou bloquear

**Status:** PROPOSED — documentação pronta para implementação; sem mudanças funcionais nesta PR.  
**Origem:** UX 2.0, feedback operacional de 2026-10-16.  
**Dependência:** [Spec 002 — Conta da Casa](../002-house-account/spec.md), [ADR 0011](../../docs/adr/0011-house-account-policy-snapshots-and-operational-approval.md), regras canônicas do ledger.  
**Produto:** cada estabelecimento escolhe **Só alertar** (`WARN_ONLY`) ou **Bloquear pedidos** (`ENFORCE`) para sua política de **limite operacional de consumo**.

## 1. Resultado esperado

Na Gerência, um responsável autorizado configura por **Venue** se pedidos que excederiam o limite operacional da comanda devem ser somente sinalizados ou rejeitados. O staff vê o consumo em uma barra **compacta** e informa o cliente quando conveniente, sem mudar de tela ou assumir aprovação gerencial para cada venda.

- `WARN_ONLY`: ultrapassar o limite **não impede confirmação de pedido por esse motivo isolado**. O ledger registra integralmente o consumo; o atendente recebe alerta sem confirmação extra e continua a venda.
- `ENFORCE`: manter a rejeição transacional existente (`SPENDING_LIMIT_EXCEEDED`) **antes** de gravar Order, OrderItem ou Charge, com recuperação por pagamento parcial confirmado ou aprovação gerencial válida.
- Ambos: exposição, limite efetivo, saldo, porcentagem e excedente continuam sendo calculados de dados canônicos; o limite não vira depósito nem garantia financeira.

**Atenção:** “Nunca bloquear venda” aplica-se **somente** ao excesso de limite quando o Venue escolheu `WARN_ONLY`. Não suprime autorização, segurança, disponibilidade de produto, fechamento de comanda, políticas fiscais, sessões inválidas, motivos independentes de `REQUIRES_ACTION` ou falhas de rede.

## 2. Fronteira de tenancy e dados

Neste monólito, o tenant operacional é `venue.Venue`, **não** um modelo `Tenant` novo. Criar `VenueSpendingLimitPolicy` (nome indicativo, ajustar à convenção do módulo `house_account`) com:

| Campo | Requisito |
| --- | --- |
| `venue_id` | PK/FK `Venue` único, `on_delete=PROTECT` |
| `mode` | enum `WARN_ONLY` / `ENFORCE`, não aceitar outros valores |
| `version` | inteiro positivo, incrementa em cada mudança efetiva |
| `updated_at` | timestamp UTC |
| Auditoria | `AuditEvent` com ator, venue, antes/depois, versão, motivo/justificativa e instante |

A relação **`RelationshipKind → VenueRelationshipPolicy.limit_cents` permanece intacta**. O limite por perfil é capturado na abertura da Tab; `LimitOverride` aprovado também permanece íntegro, expirável e auditado. **O modo de aplicação é uma política corrente do Venue**, não reescreve os snapshots das Tabs nem seus fatos financeiros. O modo efetivo usado em uma confirmação deve ficar documentado na auditoria do evento quando houver excesso.

### 2.1. Migração e defaults sem relaxamento silencioso

- **Venues já existentes** no momento da migração recebem `ENFORCE`, preservando o comportamento da Spec 002 até opt-in gerencial.
- **Novos Venues**, após habilitação controlada da funcionalidade, podem iniciar em `WARN_ONLY` conforme decisão de produto, com inicialização explícita da linha de política no provisionamento e exibindo a opção ao gerente. Antes do rollout, nenhum Venue muda de comportamento por ausência de linha ou default de código.
- Leitura sem registro deve ter fallback de compatibilidade para `ENFORCE` **e observabilidade** (não alterar silenciosamente política em request de cliente); a migração/backfill e bootstrap tornam a linha obrigatória no estado final.
- Nova versão não altera pedidos/recibos/histórico existentes. Mudança `WARN_ONLY→ENFORCE` pode deixar Tabs acima da referência: preservar dívida e evitar mutação financeira retroativa; próximos incrementos de exposição seguem a nova política.
- Rollout com flag/controle de habilitação, migração antes de publicar clientes e opção documentada de reverter ao comportamento `ENFORCE` mediante escrita auditada. Não fazer alteração global de modo em lote por padrão.

## 3. Política transacional canônica

Centralizar leitura e decisão da política no serviço de domínio (house account), **sob o contexto de Venue da Tab**, não de hostname fornecido pelo cliente. Os caminhos existentes de staff, cashier, Guest QR e Android que confirmam Order usam a **mesma decisão no servidor**.

Para uma nova confirmação:
1. Autenticar/verificar escopo, localizar Tab e fazer `select_for_update` conforme contrato atual.
2. Resolver replay idempotente **antes de recusar por mudança de política**; replay do mesmo fingerprint devolve o resultado original sem duplicar Order/Charge.
3. Calcular preço canônico do pedido, obter exposição do ledger e limite efetivo (snapshot da Tab + override temporário).
4. Ler modo vigente do Venue com estratégia de sincronização consistente durante updates concorrentes (ver seção 7).
5. Comparar `exposure + new_financial_effect > effective_limit` (estritamente maior); limite zero suporta só pedido que não aumente a exposição em `ENFORCE`, sem divisão por zero.
6. Em `ENFORCE`, rejeitar com `SPENDING_LIMIT_EXCEEDED` e payload de posição/mode/versão, sem efeitos colaterais de pedido.
7. Em `WARN_ONLY`, **permitir** confirmação se nenhuma **outra** regra rejeitar. Criar Order/OrderItems/Charge e auditoria normal, anotando alerta de excedente, modo e versão como metadados não financeiros. O readback da Tab mostra exposição real (inclusive `> effective_limit`).
8. Preservar atomicidade, lock order, idempotência, isolamento de Venue e atualização de `Tab.version`.

**Outros incrementos de exposição:** auditar e adaptar todos os gates da Spec 002, incluindo `apps/api/modules/ledger/pricing.py` (taxas/ajustes positivos) e operações de Tab que aumentem saldo (`apps/api/modules/tab_operations/services.py`, p.ex. transferências). `WARN_ONLY` não deve continuar bloqueando **por limite** nessas rotas, mas **não** elimina autorizações/limites próprios de desconto, taxa, transferências ou recuperação financeira. Não usar um `if` apenas no controlador do pedido.

## 4. Estado de atenção e projeções

A Spec 002 deriva `SPENDING_LIMIT` em `financial_position()`, marca `REQUIRES_ACTION` e expõe `consumption_blocked`. Atualizar a projeção para evitar o falso “bloqueado” quando a regra real é só aviso.

Contrato de leitura proposto (campos aditivos, sem remoção abrupta):

| Campo | Semântica |
| --- | --- |
| `spending_limit_mode` | `WARN_ONLY` ou `ENFORCE` efetivo no Venue |
| `spending_limit_policy_version` | versão da configuração aplicada à leitura |
| `effective_limit_cents` | referência operacional já existente |
| `exposure_cents` | saldo/exposição derivado do ledger existente |
| `remaining_capacity_cents` | `max(0, limit - max(0, exposure))` |
| `percentage_used` | porcentagem de exposição, pode exceder 100; `null` com limite zero |
| `limit_warning` | aviso `>=80%` inclusive sob `WARN_ONLY` |
| `limit_exceeded` | booleano de posição, independente do modo |
| `consumption_blocked` | `true` **por limite** só em `ENFORCE`, inclusive `limit=0` |
| `action_reasons` / `state` | razões e status canônicos, sem confundir aviso com ordem de bloqueio |

Em `WARN_ONLY`, `SPENDING_LIMIT` deve ser **aviso**, não uma causa para `REQUIRES_ACTION`. Se essa for a **única** razão, sincronizar Tab de `REQUIRES_ACTION` para `OPEN` com auditoria e contrato de revalidação. Outras razões (`REFUND_REQUIRED`, `OTHER_ACTION_REQUIRED`, correção em andamento etc.) **não** podem ser limpas ou contornadas ao mudar modo/pagar parcial. O mapeamento completo de ações permitidas por outros motivos é requisito explícito de implementação e testes, não pressuposição.

A projeção deve ser backward-compatible para Web/Android/Guest que dependem do campo anterior. Ao atualizar, alinhar termos: barra de alerta usa warning, nunca status vermelho de “bloqueado” em `WARN_ONLY`.

## 5. API gerencial e autorização

Aproveitar o módulo `house_account`, o gateway/proxy existentes e autenticação canônica. Contrato sugerido:

- `GET /api/pos/house-account/enforcement/`: modo efetivo, versão, default/fallback, data e capacidade da sessão para editar. Não expor dados de outro Venue.
- `PUT /api/pos/house-account/enforcement/`: `{mode, expected_version, reason, idempotency_key}`; resposta com modo/versão persistidos. Somente para gerente com capability `venue.configure` e reautenticação recente, **também verificadas no serviço**, como em políticas da Spec 002.
- Valores inválidos `400`; sem capability `403`; sem reauth `403` canônico; `expected_version` desatualizada `409 POLICY_VERSION_CONFLICT`; `idempotency_key` reutilizada com payload divergente `409 IDEMPOTENCY_CONFLICT`.
- Mesma intenção repetida por timeout devolve mesma resposta/audit sem segunda mutação; mudanças iguais não incrementam versão se idempotentemente reconhecidas. Atualização auditada inclui autor, antes/depois, motivo, versão e correlation id.
- O GET para visualização pode obedecer às capacidades atuais do módulo; **nunca** permitir escrita por waiter/Guest/Caixa, query string, host, payload de Order ou estado do device.
- UI da Gerência: Configurações → Políticas de consumo → **Só alertar** / **Bloquear pedidos**, texto de consequência e confirmação de alteração uma única vez (mudança rara e sensível). Mostrar versão e estado efetivamente salvo/readback. Não transformar o card compacto de comanda em editor gerencial.

Os paths são propostas; o integrador deve conciliar as rotas existentes em `apps/api/rodada_api/urls.py` e documentação REST antes de implementar, evitando duplicar o endpoint `house-account/policies/` de limites por relacionamento.

## 6. Experiência por canal

- **Atendimento Web e Android:** barra curta no contexto de Tab (perfil + exposição/limite) com status textual; no pedido mostrar impacto do draft listrado; em `WARN_ONLY`, botão Enviar disponível mesmo acima; em `ENFORCE`, desabilitar otimisticamente **sem confiar no cliente**, oferecer parcial ou pedir aprovação. Aviso não exige clique extra.
- **Caixa:** mesmas projeções e regras. Recebimento parcial confirmado pode aumentar capacidade, sem encerrar automaticamente a Tab.
- **Guest QR:** recebe aviso legível, não obtém alteração de política nem controle gerencial; resultado do servidor prevalece.
- **Modo offline/stale:** nunca usar cache de modo/limite para autorizar bypass em `ENFORCE`. Recuperar intenção idempotente após reconexão e exibir o modo real do readback.
- **Acessibilidade:** status escrito, não apenas cor; 360/390/430 dp, fonte ampliada, sem scroll horizontal e sem card gigantesco competindo com o CTA principal.

## 7. Concorrência e auditoria

A leitura transacional de `spending_limit_mode` não pode ser uma decisão temporal ambígua. Documentar uma **ordem de locking consistente** entre confirmação de Tab e update de política (por exemplo, adquirir lock da linha de política de Venue **antes** do lock da Tab quando necessário, e revisar fluxo atual de locks; ou usar versão/config snapshot verificado sob bloqueio apropriado). Não introduzir inversão de locks / deadlock com pagamento ou refund.

Contrato exigido:
- Um pedido iniciado no modo A e confirmado no modo B segue o **modo efetivo na linearização da transação**, exceto replay já materializado, que mantém resultado original.
- Um update concorrente não divide um único efeito financeiro entre versões nem permite extrapolação acidental em `ENFORCE`.
- O evento de pedido acima do limite em `WARN_ONLY` registra tipo, modo, versão, `Tab` e exposição antes/depois (sem dados pessoais além do mínimo operacional). Não criar Payment fictício.
- Logs/auditoria devem permitir reconstruir a política efetiva no momento de cada pedido e evitar explosão de notificações por cada item; limite é alerta informativo agregado.

## 8. Compatibilidade e fora de escopo

Spec 031 **propõe revisar o aspecto de enforcement da Spec 002** quando implementada; até lá, Spec 002 / ADR 0011 e API existente continuam soberanas. Não alterar sem avaliação o snapshot da Relationship, idempotência, isolamento, garantias reais, lifecycle do PSP, ledger, regras de correção, proteção fiscal nem auditoria.

**Não é parte da Spec 031:** caução, preauth de cartão, garantia jurídica, crédito entre bares, scoring externo, promoção automática de perfil ou transformar `WARN_ONLY` em autorização universal de operações inválidas.

**Nenhum modo configurável está implementado nesta spec documental.** O protótipo de UX 2.0, PR #212, apenas simula alternância.

## 9. Referências de código e riscos conhecidos

- `apps/api/modules/house_account/models.py`: `VenueRelationshipPolicy` é por `Venue + RelationshipKind`; modo é dimensão separada.
- `apps/api/modules/house_account/services.py`: `financial_position()` deriva estado, razões, limite efetivo e `consumption_blocked`; `sync_attention()` atualiza Tab e audit.
- `apps/api/modules/ordering/services.py`: `confirm_order()` já usa Tab lock, replay e compara `exposure + order_total` ao limite.
- `apps/api/modules/ledger/pricing.py`: existe gate adicional para taxa/ajuste que aumenta exposição.
- `apps/api/modules/tab_operations/services.py`: inspecionar outros gates de capacidade, incluindo transferências.
- `apps/api/modules/house_account/views.py`: `PolicyView.put` chama `Capability.VENUE_CONFIGURE` no serviço, embora `required_capability` da classe seja `CUSTOMER_MANAGE`. Auditar e normalizar autorização antes de adicionar mutation.
- `docs/adr/0011-house-account-policy-snapshots-and-operational-approval.md`: transações, motivos independentes e limite != garantia.

**Gates de aceite:** [acceptance.md](acceptance.md). **Plano técnico:** [plan.md](plan.md). **Sprints incrementais:** [tasks.md](tasks.md).
