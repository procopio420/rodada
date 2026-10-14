# Runbook — Railway MCP: investigar, implantar e reverter

**Risco:** alto para qualquer escrita. **Estado padrão:** diagnóstico **somente leitura**. `Railway MCP` é a ferramenta de infraestrutura; GitHub/Actions verificam código e testes. Consulte também [operações](README.md) e [deploy Railway existente](../../deploy/railway/README.md), que descreve uma demo **histórica** (não receita automática para um novo projeto).

## Gates antes de qualquer mudança

- [ ] Pedido identifica **projeto, ambiente, serviço e ação**; usuário aprovou explicitamente deploy/rollback e destino atual. No caso de um PR/merge isolado, não inferir autorização.
- [ ] Confirmar branch+SHA do código de origem, tag/build alvo e exigências de CI conforme [política](../ci-workflows.md). `main` remota pode mudar após investigação.
- [ ] Classificar ambiente `demo`, `staging` ou `pilot`; serviço Railway pode servir app unificado, landing, Postgres. **Não** promover demo com PINs/seed conhecidos a piloto.
- [ ] `describe_environment` e `get_staged_changes` mostram **todas** alterações pendentes, inclusive de outros operadores. Se houver diff inesperado, **parar**. Sem mutações no DB/variáveis/DNS implícitas.
- [ ] Dispor de build anterior saudável e plano de restauração, migrações forward-compatible, escopo de tenant, health e rollback para VR System no piloto.

## Procedimento — fase de leitura com Railway MCP

1. `Railway.list_projects` → escolher o projeto por **nome e ID lidos na hora**, nunca inferir ID histórico.
2. `Railway.list_services(projectId)` → listar environment IDs e service IDs; **passe environmentId em TODAS as consultas seguintes**.
3. `Railway.describe_environment(projectId, environmentId)` → identificar serviços, fontes GitHub/branch, state/staged, deployment atual, volumes e custos prováveis. `Railway.describe_service` para Dockerfile, start/health, domains e metadados.
4. `Railway.get_staged_changes(projectId, environmentId)` → registrar patchId, changeCount, `destructive`, recursos afetados. Caso status `APPLYING`, aguardar resolução, não empilhar mudanças.
5. `Railway.list_deployments(projectId, environmentId, serviceId)` → conferir `meta.commitHash`, status e build anterior; o SHA do último push **não é necessariamente** o deploy ativo.
6. `Railway.environment_status(..., includeSuccessful=true)` → observar estado LIVE, falhas e pending work; `Railway.get_logs` com `types: ["build","deploy"]` apenas para incidentes e janela pequena. **Sanitizar** qualquer evidência: logs podem conter identificadores, tokens ou entradas de clientes.
7. `Railway.list_domains` + `Railway.domain_status` se tiver questão de DNS/TLS. Prova de certificado Railway **não substitui** handshake do navegador e roteamento externo via Cloudflare.

**Não chamar** `Railway.list_variables` para inventário: devolve valores em claro; `describe_service.variableNames` é suficiente para checar presença sem exibir segredo.

## Procedimento — publicação (somente após GO explícito)

**Caminho A — código novo:** se o serviço rastreia GitHub, conferir `source.repo`/`source.branch` e se auto-deploy está habilitado de fato. Integrar código no repositório **somente quando autorizado**; observar deployment criado para SHA alvo. `Railway.redeploy` **NÃO puxa um commit novo**, reaproveita build já existente. Se não houver trigger do SHA alvo, não inventar um comando MCP que crie novo deployment sobre o serviço existente: documentar a necessidade do mecanismo GitHub/CLI ou dashboard aprovado. `Railway.create_deployment` cria serviço novo, não é atalho.

**Caminho B — configuração staged:** depois de inspecionar `get_staged_changes`, garantir que somente campos esperados estão staged; solicitar aprovação para **todo o patch**. Só então `Railway.accept_deploy(environmentId)` (com mensagem de change). Esse comando pode aplicar mudanças de outro operador se não forem revistas. Variáveis, domínio, source, volume, réplica e banco exigem aprovação própria.

**Caminho C — reusar build anterior ou reiniciar:** se autorizado, `Railway.redeploy(projectId, serviceId, environmentId, deploymentId?)` usa um build já existente; registrar `deploymentId` e confirmar variáveis e migrations antes. `restart_service` reinicia processo **sem novo build**; não confundir com correção de código.

## Evidências de conclusão

- Mesmo `projectId/environmentId/serviceId`, source branch+SHA esperado, deployment ID efetivamente LIVE e URL externa verificada.
- `environment_status` sem pending work inesperado; build + deploy logs sem erro crítico; GET `/health/`, `/ready/` e rotas Web importantes como `/staff`; autenticação e isolamento em Venue de teste.
- Se houver mudança de host: testes de reserved/unknown Host, sessão de outro Venue e guest token, TLS válido e cookies host-only. Não reutilizar dados reais nem confirmar pedido no demo compartilhado sem consentimento.
- Release high-risk: ensaio de turno, reconciliação manual, fiscal/PSP/hardware e aceite humano separadamente. Relatório precisa incluir **não executado**.

## Rollback / NO-GO

- Se Health/5xx deteriorar, congelar deploys e confirmar o erro. `Railway.get_deployment_diagnosis` para falhas, depois `get_logs`.
- Reversão de **imagem/build** mediante aprovação: escolher deployment anterior `canRedeploy`/`canRollback` e `redeploy` com ID exato quando suportado; sem prometer restaurar variáveis antigas. O rollback do dashboard Railway pode ter semântica distinta; conferir no momento.
- Nunca reverter PostgreSQL com migração destrutiva automaticamente; migrações `start.sh` são aplicadas na inicialização. Após rollback, validar compatibility e dados.
- Se a alteração foi de feature flag/Host/DNS, reverter apenas o que foi aprovado, manter `VenueDomain` para auditoria e usar plano [Spec 025](spec025-preview-rollout.md). Preservar URL de contingência.

**Proibido nesta fase:** `accept_deploy`, `redeploy`, `restart_service`, `set_variables`, `create_project`, `generate_domain`, `retry_domain_certificate`, comandos em DB ou ações de produção sem aprovação explícita.
