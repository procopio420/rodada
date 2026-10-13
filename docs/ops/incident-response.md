# Runbook — incidente operacional, deploy, 5xx e certificado

**Modo padrão:** diagnosticar em **somente leitura** e preservar evidência; incident response não concede permissão de mutação. [Índice OPS](README.md), [Railway MCP release](railway-mcp-release.md), [Spec 025 TLS](spec025-preview-rollout.md).

## Gates

- Registrar início, ambiente afetado, impacto real (sem assumir número de clientes), sintomas, última versão saudável, mudança recente e severidade; conferir se demo ou piloto real.
- Em problema de pagamento/duplicação ou perda de isolamento, interromper **novas mutações perigosas** pela estratégia já aprovada e escalar prontamente; não mascarar erro com `200` ou criar pagamentos fictícios.
- Ações que alteram deploy/variáveis/domínio/BD/contas precisam de aprovação explícita; P0 não autoriza automaticamente `accept_deploy` ou `redeploy`.

## Procedimento — triagem via MCP

1. `Railway.list_projects` → `list_services` → `describe_environment(projectId, environmentId)`: confirmar projeto, ambiente, estado staged, serviço e fonte GitHub.
2. `Railway.environment_status(includeSuccessful=true)` e `list_deployments`: deployment LIVE e predecessor, `meta.commitHash`, `recentFailures`, pending work. Se houve falha recente: `get_deployment_diagnosis(projectId, deploymentId)`.
3. `Railway.get_logs(projectId, serviceId, environmentId, types=["deploy","build"], limit=100)`, restringindo janela; se erro HTTP, observar `http_error_rate`, `http_requests`, `http_response_time`/traces quando disponíveis. Nunca colar cookies, PIN, payload de guest ou dados financeiros no relatório.
4. Validar diferença entre:
   - **Build falhou:** dependências/Docker/compile; nenhum novo SHA LIVE.
   - **Deploy/crash:** env var ausente, migration, health, porta/processo, `start.sh`; analisar sem revelar valores de segredo.
   - **HTTP 4xx/401/403:** sessão/Host/capability/Guest; erro de autenticação não é 5xx nem justificativa para liberar acesso.
   - **5xx/timeout:** BFF↔Django, PostgreSQL, rede, saturação, volume de logs e readiness; não reiniciar em loop sem diagnóstico.
   - **TLS/hostname:** `list_domains` + `domain_status`, registros exigidos, status ACME/ownership e handshake externo; Cloudflare proxy e Railway certificados têm camadas distintas.
   - **Operação:** KDS, cozinha `NEW` vs `PREPARING`, SSE defasado e pedido confirmado no DB; não compensar com novo pedido ao ver spinner.
5. Relacionar o primeiro erro com deploy ID/SHA e configuração; produzir hipótese com nível de confiança e próximo teste não destrutivo.

## Procedimento — mitigação aprovada

- Sem deploy válido: voltar ao build conhecido e compatível, via `redeploy` com deployment ID específico quando aplicável. Isso **não** reverte migração nem valores de variáveis antigas; conferir reversibilidade.
- Se o problema for só toggle preview de host: usar [rollback da Spec 025](spec025-preview-rollout.md) em ambiente explicitamente aprovado; não mover DNS/QR em massa.
- Contingência operacional: manter VR System para piloto conforme acordo, tomar pedidos offline segundo procedimento humano aceito. Nunca registrar `pago` sem confirmação real.
- Alteração de acesso comprometido: seguir [staff runbook](staff-access.md), auditar, preservar provas sem exibir credenciais.
- Restauração de dados: seguir [backup](backup-restore.md), primeiro um ensaio isolado. Não apagar/overwrite banco ativo.

## Evidências

`incident_id`, URL sanitizada, período, ambiente, deployment ID/SHA antes/depois, sintomas verificáveis, logs **redigidos**, hipóteses, ação autorizada, restauração de /health /ready + cenário real e regressões negativas. Separar `mitigado`, `resolvido` e `homologado`.

## Rollback / contenção

Reexecutar apenas plano aprovado para aquele ambiente; se falhar, parar e escalar. Não inventar novo serviço Railway pago, não trocar database URL para "testar", não executar `seed_demo` ou `flush`, não expor Postgres à internet, e não degradar isolamento/CSRF/permission gates.
