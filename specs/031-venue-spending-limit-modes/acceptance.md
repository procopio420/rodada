# Acceptance — Spec 031: enforcement configurável de limite

**Estado inicial:** nenhum AC validado; documento é contrato de aceite futuro.  
**Evidência mínima:** comando de teste, resultado e commit SHA; contratos HTTP/DB; screenshots reais por dispositivo; teste PostgreSQL de transação/conflito; reviewer independente.  
**Oráculos:** Spec 002 e ADR 0011 continuam em vigor para todo assunto não modificado explicitamente por esta Spec 031.

## Persistência, acesso e isolamento

- [ ] **AC-001** Migration mantém **todos os Venues existentes** em `ENFORCE`, inclusive sem Relationship, com limite zero e Tabs OPEN/REQUIRES_ACTION já acima da referência. Nenhum fato de ledger, versão de Tab ou histórico de cliente é alterado.
- [ ] **AC-002** Bootstrap de novos Venues gera policy única, com modo inicial escolhido explicitamente pelo rollout e sem depender de chamada de leitura; fallback sem registro é `ENFORCE` com alerta operacional.
- [ ] **AC-003** Constraint de Venue único, enum válido, versão positiva; falhas de migration/rollback testadas; sem modelo paralelo de Tenant.
- [ ] **AC-004** GET de configuração de `Venue A` nunca devolve policy de `Venue B`, mesmo usando UUID/hostname/parâmetros manipulados.
- [ ] **AC-005** Apenas gerente com `venue.configure` **e PIN/reautenticação recente** consegue PUT; waiter, cashier sem capability, Guest, sessão revogada e cross-Venue recebem acesso negado.
- [ ] **AC-006** PUT com `mode`, `expected_version`, motivo e idempotency key retorna modo + versão persistidos; audit tem before/after/ator/venue/tempo/versão. Replay idêntico não cria segundo efeito/audit; reuse divergente e CAS antigo retornam 409 adequados.

## Decisão de venda e ledger

- [ ] **AC-007** Em `WARN_ONLY`, Tab aberta com limite R$30, exposição R$28 e novo pedido de R$10: backend confirma Order + OrderItems + Charge **uma vez**; exposição final R$38; evento e readback informam excesso R$8 e modo efetivo.
- [ ] **AC-008** Mesma Tab/pedido em `ENFORCE`: `SPENDING_LIMIT_EXCEEDED` 409 antes de criar Order/OrderItems/Charge; audit/replay preservam consistência; draft cliente não é apagado.
- [ ] **AC-009** Limite R$0 para RESTRICTED: WARN_ONLY confirma pedido positivo válido com aviso, ENFORCE bloqueia pedido positivo; `percentage_used=null`, sem divisão por zero, sem fingir garantia.
- [ ] **AC-010** Em ambas as modalidades, 79% não alerta, 80% alerta, 100% aparece claramente; WARN_ONLY permite chegar a 120%+ e continua sinalizando o excesso; ENFORCE rejeita novos incrementos acima da referência. Valores exatos em centavos.
- [ ] **AC-011** Preços são calculados por snapshot canônico, nunca confiando na soma enviada pelo cliente ou na porcentagem renderizada pela barra.
- [ ] **AC-012** Um pagamento parcial **confirmado** diminui exposição; recebimento pendente/falha/chargeback não libera capacidade falsamente. Não fecha automaticamente a Tab, apaga draft ou inventa garantia.
- [ ] **AC-013** Refund confirmado aumenta exposição na medida do ledger; override vigente/expirado tem semântica da Spec 002, não cria Payment; policy mode não modifica `LimitOverride` nem snapshot da Tab.
- [ ] **AC-014** Em WARN_ONLY, ajustes/taxas positivas e demais gateways inventariados deixam de rejeitar **exclusivamente por limite**; ENFORCE conserva o gate atual; aprovações específicas e proteções financeiras independentes seguem exigidas.
- [ ] **AC-015** Produtos indisponíveis, estações desabilitadas, Venue incorreto, Tab SETTLING/CLOSED, auth ausente, correções pendentes e demais restrições independentes continuam protegidos nos dois modos, mesmo com limite alto.

## Estado e compatibilidade

- [ ] **AC-016** `financial_position` retorna `spending_limit_mode`, `spending_limit_policy_version`, `limit_exceeded` e semântica correta de `limit_warning` / `consumption_blocked`; em WARN_ONLY não há falso `consumption_blocked` por excesso.
- [ ] **AC-017** WARN_ONLY com **somente** `SPENDING_LIMIT` não força Tab a REQUIRES_ACTION; causas separadas (`REFUND_REQUIRED`, `OTHER_ACTION_REQUIRED`, review gerencial etc.) persistem e não podem ser bypassadas.
- [ ] **AC-018** Alternância ENFORCE↔WARN_ONLY com Tabs abertas e acima da referência preserva dívida, estado histórico, ordem dos efeitos, reconciliação e versão de Relationship snapshot. Modo novo se aplica a próximas confirmações, não reescreve passado.
- [ ] **AC-019** Staff Web, Caixa, Android e Guest QR recebem mesmas decisões de backend e DTOs seguros; nenhum cliente antigo/stale consegue definir/forçar `mode` por payload de pedido. UI não declara “permitido” quando o readback negou.
- [ ] **AC-020** Em WARN_ONLY, a comanda mostra barra **compacta**, perfil, consumo/limite e alerta textual; rascunho usa faixa listrada; o CTA principal segue utilizável sem modal de autorização extra. Em ENFORCE, mostra bloqueio com orientação de parcial/gerência. Testes em 360/390/430dp + leitor de tela/fontes maiores.

## Concorrência, auditoria e rollout

- [ ] **AC-021** Duas confirmações concorrentes da mesma Tab com modos diferentes nos requests não podem definir regra divergente: policy corrente do Venue é a autoridade, serialização é documentada e demonstrada com PostgreSQL real (incluindo update simultâneo de modo).
- [ ] **AC-022** Replay de mesmo idempotency key/fingerprint após mudança de policy retorna resultado original e não duplica Order/Charge/audit; mesma key com payload diferente retorna conflito; timeouts têm recuperação verificável.
- [ ] **AC-023** Teste de isolamento com Venue A WARN_ONLY e Venue B ENFORCE usa os mesmos produtos/perfis e prova resultados distintos no backend, sem vazamento de dados/atores ou claims.
- [ ] **AC-024** Observabilidade registra decisões acima do limite, bloqueios do ENFORCE, versões e erro de policy de modo mínimo, sem PII excessiva; rollout preserva ENFORCE legado e possui rollback auditado sem alterar ledger.
- [ ] **AC-025** CI e evidências incluem PostgreSQL com transações reais, suites domínio/API, browser/Web, Android build/unit/lint, Guest/Caixa E2E e revisão independente R3 concluída; resultado declara claramente falhas/skips e ambiente. Nenhum deploy antes do aceite.

## Quadro de execução sugerido

| Slice | ACs | Gate |
| --- | --- | --- |
| S1 · Persistência + auth | 001–006 | Migração segura e API versionada |
| S2 · Domínio financeiro | 007–015, 021–023 | Ledger/idempotência/concorrência |
| S3 · Projeções + canais | 016–020 | UX acessível, API e E2E |
| S4 · Gerência | 004–006, 020, 024 | Manager-only readback audit |
| S5 · Rollout | 021–025 | Review R3, compat e controle de ativação |

**Não substituir evidências reais pelo protótipo da PR #212.**
