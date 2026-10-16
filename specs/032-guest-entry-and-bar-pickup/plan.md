# Spec 032 — Plano de execução

**Estado:** PROPOSTO. Nenhuma feature aceita/implantada por este documento.

## Estratégia

Manter contratos das Specs 004, 009, 014, 026, 029 e proposta 031. Implementar slices verticais com PRs curtos, evidência independente e sem mudar a UX do Atendimento atual até validação de screenshots/jornadas. O PR da Spec 032 é apenas o handoff.

### S0 — Contrato e teste de jornada

- Fixar estados, cópias, ownership e critérios antes de alterar código.
- Mapear implementação atual em `apps/api/modules/hospitality`, `guest_access`, `ordering`, `fulfillment`, `ledger`; identificar migrations/capabilities reais. Não presumir que toda semântica proposta já existe.
- Preparar fixtures determinísticas para mesa existente, improvisada, QR geral, grupo com 4 clientes, balada com retirada, reconnect e troca 21:59 → 22:00.

### S1 — Mesa nova com tag opcional

- API para registro pré-provisionado de PhysicalTag e binding transacional Venue/Table, com constraint única, CAS e auditoria. Legado `Table.public_token` mantém compatibilidade.
- Atendimento Web/Android: criar mesa primeiro, ação `Vincular QR` ou `Agora não`, indicador discreto e rebinding seguro.
- QR desconhecido / sem tag / danificado / camera denial não impede mesa interna. Prever reversão e desatribuição.
- Testes API PostgreSQL corrida + permissões/tenant + integração UI.

### S2 — Entrada e ocupação pelo cliente

- Resolver QR de mesa sem alterar status; CTA explícito de entrada cria/adere à ocupação com idempotência e locking. TTL provisório policy-driven sem apagar atividade/dinheiro.
- Isolamento Tab por guest session, convite intencional e revogação por generation.
- Proteções com rate-limit, emergency block e exposição. E2E dois clientes simultâneos e atacante com URL antiga.

### S3 — QR geral e continuidade

- Entidade de acesso público Venue-scoped (sem Table) para PWA; manter BFF Host/CSRF/session guardrails.
- Retomar Tab com sessão válida; nova Tab somente via ação explícita. Deep link/identificador privado de recuperação.
- Fluxo `Pedir para retirar` e passagem do QR geral ao QR de mesa mantendo draft e identidade.
- Reconciliar dependências com #146, sem duplicar TabIdentifier.

### S4 — Modalidade e direito de retirada

- Mode/policy tipada por Venue; snapshot de fulfillment por Order; modo coexistente de mesa e balcão.
- Definir PickupGroup / PickupCode com índice único no Venue, quarentena de reuso, origem de liberação e liberação somente mediante evidência canônica.
- Projeção de fila Bar/Cozinha; cliente com código legível, tempo/estado, fallback impresso.
- Testar status de pagamento falso, conta restrita, pagamento pendente, 2 códigos concorrentes e limites.

### S5 — Retirada de baixo atrito

- Bar: códigos grandes, busca instantânea, ênfase em `Pronto`, estados com provenance. Padrão sem obrigação de confirmação.
- Cliente: `Já retirei` não obrigatório, `Não recebi` como exceção, grupos/parcial, histórico/reconciliação. Staff pode confirmar/corrigir.
- A UI limpa a fila visual sem falsificar o fato de entrega. Códigos duplicados/atrasados continuam encontráveis.
- Alinhar feedback com Spec 031 apenas após reconciliar source/semântica.

### S6 — Conta, encerramento e recuperação

- Pagamento real/externo com status canônico e gate; não presumir PSP disponível.
- Recuperação de sessão/ficha após navegador fechado ou celular perdido; claim autorizado e revoke.
- Fechamento individual não muda mesa; liberação física só por comando adequado.
- Cross-surface E2E Web + Atendimento + Bar + Caixa com horário 21:59→22:00 e reconexão.

### S7 — QA, rollout protegido

- Executar gates proporcionais à stack: Django check/migrations, pytest PostgreSQL concorrência, Web typecheck/auth/integration/build/visual, Android unit/assemble/lint, testes de host/two-venue.
- Capturas reais 360/390/430, fontScale 1/2, teclado/IME/safe areas, foco, contraste, leitor de tela, desktop. Comparar antes/depois com fixtures.
- Revisão independente R3 para money/auth/data e provas explícitas. Sem review não rotular aprovado.
- Feature flags por Venue e rollback sem apagar dados, canary isolado, teste operacional em bar com autorização específica antes de alterar piloto/deploy.

## Sequência e responsabilidade

S0 → S1/S2 → S3 → S4 → S5 → S6 → S7. Atravessar S4/S5 só após contrato de autorização do pedido e capability de pagamento. Um integrador mantém schema/contrato comum; Android, Web e API trabalham em PRs separados, sem edição paralela de migrações/arquivos de interface.

## Métricas

Tempo até primeiro pedido aceito, tempo para abrir mesa improvisada, primeiro pedido → pronto, tempo para localizar código FG84, percentual de retirada UNKNOWN/GUEST_DECLARED/STAFF_CONFIRMED, pedidos perdidos, recuperação de sessão, fraudes/contestações, cancelamentos, taps do bartender por pedido (meta happy path = 0). Segmentação por Venue, horário, modalidade, com/sem mesa. Não confundir percepção com métrica medida.

## Evidência esperada

Cada slice aponta critérios `S032-*`, diff/commit, testes realmente executados, fixture e ambiente, cenário negativo, resultados de acessibilidade e responsável/revisor. CI verde não equivale a homologação no Santo Malte nem no Aderlan.
