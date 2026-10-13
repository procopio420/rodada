# Operações do Rodada — runbooks para Codex

Procedimentos **operacionais**, não autorização para agir. Leia [AGENTS](../../AGENTS.md), [procedimentos dos agentes](../agents/PROCEDURES.md) e ative a [skill `rodada-ops`](../../.agents/skills/rodada-ops/SKILL.md) quando a tarefa envolver Railway, cadastro de bar, acesso ou incidente.

| Tarefa | Runbook | Capacidade atual |
| --- | --- | --- |
| Conferir/deployar/voltar versão do app no Railway | [Railway MCP: release](railway-mcp-release.md) | Inventário e diagnóstico via MCP; mudança externa exige autorização |
| Cadastrar um novo bar no mesmo SaaS | [Onboarding de Venue](onboard-venue.md) | Modelo `Venue` e `VenueDomain` existem; bootstrap protegido, sem endpoint público de cadastro |
| Criar funcionário, mudar função ou revogar acesso | [Acesso de staff](staff-access.md) | Gestão de vínculos/dispositivos/sessões via API; criação inicial supervisionada |
| Erro 5xx, deploy falho, TLS, isolamento de tenant | [Incidentes e recuperação](incident-response.md) | Read-only diagnosis no Railway; rollback sob decisão humana |
| Importar cardápio de um bar | [Catálogo CSV](catalog-import.md) | Management command com preview por padrão, `--apply` explícito |
| Proteger dados / ensaio de restore | [Backup & restore](backup-restore.md) | Scripts existentes, somente em ambiente isolado e autorizado |

## Contrato do agente

**Descobrir sem alterar:** `Railway.list_projects`, `list_services`, `describe_environment`, `describe_service`, `get_staged_changes`, `list_deployments`, `environment_status`, `get_logs`, `domain_status`. Proteger/limitar outputs: logs podem ter dados, `list_variables` revela segredos e **não é ferramenta de inventário**.

**Preparar:** indicar projeto, ambiente, serviço, branch/SHA esperado, impacto, custo, dependências, check de segredos **por nomes apenas**, rollout/reversão, critérios de GO/NO-GO, change/ticket e aprovação necessária. Nunca deixar `environmentId` omitido num pedido de escrita: Railway pode assumir produção ou ambiente mais antigo.

**Executar:** só após autorização explícita **da ação e do destino** no pedido atual. `Railway.accept_deploy` publica **todas** as mudanças staged daquele ambiente; `redeploy` coloca no ar um build existente (não é deploy do commit novo). `set_variables`, `generate_domain`, `retry_domain_certificate`, reinícios, banco, staff e pagamentos também são operações com efeito externo. Nunca usar `create_project`/Postgres por novo bar.

**Provar:** guardar ticket, `git SHA`, projeto/ambiente/serviço, deployment ID, `environment_status`, build/runtime logs sanitizados, gates negativos e indicação do operador. O estado `SUCCESS` do Railway **não equivale** a homologação de turno nem autenticação, TLS, fiscal ou PSP.

## Regras de alcance

- Compartilhado por padrão: **um deployment Next+BFF+Django e um PostgreSQL, com vários `Venue` isolados**. Só mudar arquitetura/custo por decisão e ADR aprovadas.
- Ambiente de demo usa contas de teste e não pode receber dados reais. `pilot` é perfil separado, com segredos próprios e `RODADA_PAYMENT_SIMULATION=false`; nunca transformar a demo povoada em produção.
- `Venue.id` é o isolamento. `Venue.slug` interno pode diferir do hostname público; `VenueDomain` requer verificação e ativação independentes.
- Um agente Codex **não possui execução interativa de shell no Railway por meio dos comandos MCP atualmente disponíveis**. Não inventar `Railway.exec`. Se a operação exigir `manage.py shell`, usar acesso administrativo protegido, auditável e explicitamente autorizado, ou registrar bloqueio.
- Se rollback de app não for compatível com a migração do DB já aplicada, **não executar rollback de schema destrutivo**: escalar e manter contingência.

Mais exemplos de pedidos copiáveis: [templates de tarefas OPS](TASK-REQUESTS.md).

Template para solicitar ação ao Codex:

> Use `$rodada-ops`; siga o runbook escolhido. Primeiro execute exclusivamente a fase read-only. Entregue inventário, impacto, SHA alvo, plano de testes e rollback; não modifique Railway, dados ou permissões até eu aprovar o destino e a operação.

Referências: [domínio canônico](../adr/0018-rodada-bar-canonical-domain.md), [runbook Spec 025](spec025-preview-rollout.md), [provisionamento protegido](../../deploy/railway/pilot-provisioning.md), [release gates](../../deploy/railway/aderlan-staging-release-gates.md), [CI](../ci-workflows.md).
