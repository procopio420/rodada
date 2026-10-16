# Plan — Spec 031: enforcement de limite configurável por Venue

**Status:** PLANNED — sem implementação nesta PR de documentação.  
**Fontes obrigatórias:** [spec.md](spec.md), [acceptance.md](acceptance.md), Spec 002, ADR 0011, `AGENTS.md` e skills/KB aplicáveis.

## Estratégia

Entregar em slices pequenos e verificáveis. A configuração pertence a `Venue` (tenant operacional). `VenueRelationshipPolicy` e snapshots de Relationship da Tab continuam independentes. **Não fazer hardcode em Android/Web**: o servidor é o único autorizador. Preservar modo `ENFORCE` para Venues existentes; `WARN_ONLY` será padrão somente para Venues novos após configuração/rollout explícito, sem relaxamento automático do legado.

## S1 — Persistência e API privilegiada (backend)

**Write set candidato:** `apps/api/modules/house_account/{models,services,views,migrations}`, `apps/api/rodada_api/urls.py` e testes correspondentes, coordenados pelo integrador.

1. Confirmar modelos/rotas existentes e reusar padrões de política versionada. Criar enum `WARN_ONLY/ENFORCE`, relação única por Venue, constraints de modo/versão e timestamps. Evitar modelo artificial de `Tenant`.
2. Migration data backfill de **todos os Venues existentes para `ENFORCE`**, sem alterar Tabs, Orders, Payments nem ledger. Bootstrap idempotente para novos Venues, definido pelo feature rollout. Fallback de leitura sem registro = `ENFORCE` com métrica de integridade, nunca mudança implícita.
3. `GET` readback autorizado; `PUT` recebe `mode`, `expected_version`, `reason` e `idempotency_key`. Validar capability `venue.configure` e reautenticação recente tanto na view quanto no serviço; CAS transacional, audit com `before/after` e resposta idempotente à repetição.
4. Investigar a divergência pré-existente `PolicyView.required_capability=CUSTOMER_MANAGE` vs `authorize(VENUE_CONFIGURE)`; preservar compatibilidade e escolher boundary seguro antes de publicar endpoint novo.
5. Definir semântica de atualização repetida/no-op, version conflict e idempotency conflict; validar cross-Venue e sessões revogadas.

**Gate:** migrations e testes de API/auth PASS; ainda não expor `WARN_ONLY` a usuários reais antes de S2.

## S2 — Decisão canônica de consumo (backend)

**Write set candidato:** `apps/api/modules/house_account/services.py`, `apps/api/modules/ordering/services.py`, `apps/api/modules/ledger/pricing.py`, `apps/api/modules/tab_operations/services.py`, testes de domínio, auditoria e concorrência.

1. Definir avaliador reutilizável do limite que devolve `mode`, versão, exposição ledger, limite efetivo, excesso projetado, aviso e `should_reject`, sem duplicar motor financeiro.
2. Revisar `confirm_order()`: sob lock da Tab, resolver replay idempotente, validar disponibilidade e precificar canonicamente, ler política de Venue de modo linearizável. Se `ENFORCE`, manter rejeição `SPENDING_LIMIT_EXCEEDED` antes de gravar; se `WARN_ONLY`, continuar a confirmação quando **somente** limite foi excedido. Preservar outros bloqueios.
3. Revisar aumentos de exposição fora do pedido: `ledger/pricing.py` (taxas/ajustes) e operações de Tab, inclusive transferências. Aplicar decisão compartilhada sem relaxar aprovações por outros motivos.
4. Refatorar `financial_position()` / `sync_attention()`: aviso de `SPENDING_LIMIT` em `WARN_ONLY` não deve forçar `REQUIRES_ACTION`. Motivos não financeiros ou independentes continuam íntegros. Em `ENFORCE`, semântica compatível com Spec 002.
5. Audit de decisões acima do limite com `mode`, `policy_version`, `tab`, total do pedido e exposição antes/depois sem criar Payment ou garantia. Não emitir um evento duplicado em replay.
6. Locking: implementação atual bloqueia **Tab antes** de checar limite. Uma opção é **Tab → VenuePolicy** em confirmações, e atualizações de policy bloquearem **somente** a linha de policy, sem tocar Tabs na mesma transação. Demonstrar ausência de inversão/deadlock com Payment/refund e idempotência.
7. Mudanças de modo afetam **novas confirmações**, inclusive Tabs abertas, mas não reescrevem seus snapshots de relacionamento nem fatos já realizados.

**Gate:** PostgreSQL real cobrindo race update policy vs confirm, replay, and ledger integrity; `ENFORCE` preserva os testes da Spec 002.

## S3 — Projeções e canais (API, Web, Android, Guest)

1. Acrescentar projeções `spending_limit_mode`, `spending_limit_policy_version`, `limit_exceeded`; ajustar `consumption_blocked` para indicar bloqueio **por limite**, não percentual cru.
2. Confirmar que os clientes Web/Android/Guest/Caixa interpretam a nova regra e não bloqueiam localmente acima do limite quando `WARN_ONLY`. Mensagens de erro de outras classes seguem intactas.
3. Comanda: barra **compacta** com consumo/limite e capacidade disponível; catálogo/revisão mostram impacto do pedido sem modal de aviso obrigatório.
4. Revalidação em foco/reconnect/recuperação de offline; UI nunca pode mudar o modo efetivo sem GET canônico.

**Gate:** contratos e E2E multi-canal, tela mobile 360/390/430dp, fonte ampliada e acessibilidade.

## S4 — Gerência e autorização

1. `Manage → Configurações → Políticas de consumo`: selecione **Só alertar** ou **Bloquear pedidos** por Venue, descrição do efeito e aviso para valores acima da referência.
2. Somente operador com `venue.configure` e reautenticação recente pode salvar. Corrigir tela apenas após confirmação readback.
3. `409` de versão com refresh e nova decisão; timeout mantém chave da mesma intenção sem criar uma segunda mutação; erros de auth claros.
4. Registrar versão/autor/data e histórico auditável; garçom vê o modo, **não edita**.

**Gate:** teste real de escrita gerencial, staff/guest negados e readback em outra sessão do mesmo Venue.

## S5 — Rollout, verificação e compatibilidade

1. Migração primeiro, componentes cliente depois; Venue legado continua `ENFORCE` até alteração explícita auditada.
2. Verificar independência Venue A/B, novas/antigas Tabs, RESTRICTED/zero, 79/80/99/100/120%, parcial, refund, override expirado, motivos independentes de ação, idempotência e concorrência.
3. Rodar checks API/PostgreSQL, web E2E, Android unit/instrumented/build/lint e Guest QR com evidências reproduzíveis.
4. Rollout progressivo por Venue e controle de habilitação; métricas de pedidos permitidos com aviso, rejeições em ENFORCE, erro de política e conflitos, sem PII desnecessária.
5. Plano de rollback: opção administrativa auditada para ENFORCE, sem mutar ledger passado ou aplicar bloqueios retroativos. Flags somente de rollout, não fonte alternativa para o modo.
6. Exigir revisão independente classe R3 por afetar ledger/limite e claims de segurança. Sem merge/deploy antes dos gates.

## Decisões a fechar no PR de implementação

- Serialização exata de atualizações do modo concorrentes com confirmação, alinhada ao lock order existente.
- Default para **Venues novos**: somente ativar `WARN_ONLY` após product/security sign-off, sem herança acidental do legado.
- Eventuais caminhos de consumo fora do `confirm_order`: inventário completo antes do rollout.
- Compatibilidade para clientes offline antigos e sem leitura do campo `mode`: nunca fazer bypass baseado em campo ausente.
- Normalização de `PolicyView` atual sem regressão de `CUSTOMER_MANAGE`/gerência.

**Escopo atual:** escrever spec/plan/tasks/acceptance e abrir PR draft separado da UX 2.0. Nenhuma migration, endpoint, policy ou interface real foi modificada.
