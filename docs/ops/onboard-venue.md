# Runbook — cadastrar um novo bar (Venue)

**Risco:** alto; novo estabelecimento pode afetar autenticação, DNS, isolamento e cobrança. **Modo inicial:** planejamento e leitura; qualquer INSERT ou ativação exige consentimento. [Índice OPS](README.md), [Spec 025](../../specs/025-tenant-host-routing/spec.md) e [contrato de host](../architecture/tenant-routing-contract.md).

## Gates

1. Confirmar proprietários, nome público, `Venue.slug` interno único, alias de hostname único, timezone, corte do dia, módulos, proposta de cardápio, QR e referência de aprovação. Não pedir PIN pelo chat nem commitar dados pessoais.
2. **Sem projeto Railway novo:** o app Next+BFF/Django e PostgreSQL são compartilhados. Não criar um serviço/db por bar. Não reutilizar a base da demo com credenciais conhecidas para dados reais.
3. Checar via consulta **read-only** `Venue`, `VenueDomain`, `StaffMember.login_identifier` (globalmente único) e `VenueStaffMembership`; verificar colisões de slug, domínio, alias reservado, conta e UUID.
4. O alias `bardoaderlan.rodada.bar` **não** é igual ao slug `bar-do-aderlan`; outro bar seguirá essa regra. Não criar `api`, `www`, `admin`, `bar` etc como alias.
5. Aprovação formal para criar Venue, primeira conta OWNER, acesso ao banco protegido, política de backups, rota de contingência e eventual liberação de hostname. Nenhum dado real em demo.

## Procedimento

**Provisionamento inicial:** ainda **não há endpoint API público de criar Venue**. O [script de primeiro owner](../../deploy/railway/pilot-provisioning.md) foi definido para **banco piloto vazio, isolado e aprovado**; **não o execute cegamente** na base compartilhada/multi-Venue. Para bares adicionais, processo de operador com `manage.py shell` sob acesso protegido e trilha de auditoria própria; Railway MCP **não expõe comando de shell interativo**.

Ordem aprovada para um executor autenticado:

1. **Read-only:** conferir que o `slug`/domínio propostos estão livres e `login_identifier` do owner não conflita globalmente; guardar evidências sem PIN/PII.
2. **Transação Django supervisionada:** `Venue(slug, name, guest_mutations_blocked=True)`, `full_clean`, persistir; provisionar `StaffMember` com `set_pin`/hash seguro, `VenueStaffMembership(role=OWNER)`; anexar `AuditEvent(event_type="access.owner_bootstrapped")` com referência de mudança, operador e Venue. Em caso de conflito abortar atomicamente; **não** renomear usuário de outro bar.
3. **Hostname:** criar `VenueDomain(hostname=<alias>.rodada.bar, venue=<Venue>)` primeiro com `is_active=False`/`is_verified=False`. `VenueDomain.save()` normaliza/valida e checa nomes reservados. Verificar quem controla DNS e TLS; só marcar `is_verified=True` após prova independente de ownership/TLS. **Não ativar** até preview negativo cross-Venue/Host ser aprovado. DNS wildcard sozinho **não** cadastra Venue.
4. **Configuração:** owner acessa Venue recém-criado por fluxo autorizado, configura fuso/corte do dia, stations, caixa, mesas e permissões. Importar cardápio aprovado pelo [runbook de CSV](catalog-import.md); produtos e preços só aparecem após aplicação explícita.
5. **Guest:** manter `guest_mutations_blocked=True` até validar QR opaco, ciclo de ocupação, geração/epoch, revogação e request cross-Venue. Não distribuir QR real antes do gate.
6. **Ativação:** testar dois Venues independentes (mesas, usuários, pedidos, SSE, guest, refresh, pagamentos), host desconhecido fail-closed, cookies host-only, domínio/TLS. Somente após aceite de segurança e rollout [Spec 025](spec025-preview-rollout.md) habilitar `VenueDomain.is_active` e o tráfego.

## Evidências

Registrar `Venue.id`, slug, alias, change ID, responsável, commit/versão do app, `VenueDomain` verified/active, pruebas negativas cross-tenant, smoke por módulo e plano de contingência. **Não** guardar PIN, sessão, refresh/access token ou PII no ticket. Ao fim, a criação do Venue não implica que PSP, fiscal ou impressão estão homologados.

## Rollback / contenção

- **Antes** de ativação: manter Venue/Domain sem tráfego, `guest_mutations_blocked=True`, não divulgar URLs.
- **Depois** de ativação: desabilitar alias `VenueDomain.is_active=False` / liberar novamente bloqueio guest apenas após aprovação; não apagar Venue, usuários, ledger ou histórico de pedidos. Manter trilha de auditoria.
- Se houve qualquer operação financeira real, nenhuma reversão por `DELETE` de dados. Escalar revisão transacional/fiscal.
