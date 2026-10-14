# Pedidos prontos para o Codex — Rodada OPS

Troque os campos entre colchetes por dados **não secretos**. Todos os prompts ativam a [skill `rodada-ops`](../../.agents/skills/rodada-ops/SKILL.md), obedecem ao [índice](README.md) e às regras de aprovação. Nunca inclua PIN, access token, refresh token, segredos, cartão ou dados reais de clientes no chat.

## 1. Diagnóstico e plano de deploy Railway — sem publicar

> Use `$rodada-ops` e [railway-mcp-release](railway-mcp-release.md). Inspecione via Railway MCP, **somente leitura**, o projeto `[nome]`, ambiente `[demo/staging/pilot]` e serviço `[nome]`. Identifique `environmentId` e `serviceId` reais, source branch, deployment LIVE/SHA, staged changes, últimos deploys, health e warnings. Compare o commit alvo `[SHA]` com os testes GitHub. Entregue plano de rollout, smoke, custo/impacto e rollback; **não dispare deploy, merge, restart ou mudança de variável**.

Após receber e revisar o plano, a aprovação para escrita deve ser explícita, por exemplo: “Autorizo apenas o deploy do SHA `[SHA]` no serviço `[SERVIÇO]`, ambiente `[AMBIENTE]`, projeto `[PROJETO]`, sob o plano `[TICKET]`; não aplique outras mudanças staged.” O agente **deve revalidar** a configuração/patch antes de agir; se o MCP não oferecer o mecanismo exato para o SHA, parar.

## 2. Novo bar — pré-voo

> Use `$rodada-ops` e [onboard-venue](onboard-venue.md). Quero preparar o cadastro do bar `[NOME]`, slug interno `[SLUG]`, hostname público proposto `[ALIAS].rodada.bar`, timezone `[FUSO]`. Confirme exclusividade e validação por meio das fontes autorizadas, sem acessar segredo nem gravar banco. Liste permissões, dono responsável, Guest/QR, catálogo, domínio/TLS e cenários negativos cross-Venue; descreva o bootstrap seguro pendente. **Não crie projeto Railway, Venue, OWNER ou domínio ainda**.

Com os gates completos, o proprietário pode aprovar o onboarding para o destino exato via operação administrativa protegida; o prompt não supõe que o Railway MCP possa executar `manage.py shell`.

## 3. Novo funcionário ou mudança de role

> Use `$rodada-ops` e [staff-access](staff-access.md). No bar `[VENUE]`, quero `[criar usuário / alterar role / revogar acesso]` para `[IDENTIFICADOR INTERNO]`, com role pretendida `[STAFF/CASHIER/MANAGER/OWNER]` e motivo `[TICKET]`. Primeiro verifique contratos, permissões, `expected_version`, owner autorizado, sessões e riscos, **somente leitura**. Descreva exatamente qual endpoint existente pode ser usado ou qual bootstrap supervisionado falta. Não peça PIN pelo chat nem faça mutation sem confirmação do dono.

## 4. Incidente ou TLS

> Use `$rodada-ops` e [incident-response](incident-response.md). Incidente `[TICKET]` no projeto `[NOME]`, ambiente `[NOME]`, sintoma `[500/crash/TLS/QR]`, iniciado `[DATA]`. Faça exclusivamente diagnóstico via Railway MCP e histórico GitHub. Obtenha status LIVE, deployment ID, commit, dados mínimos de erro e `domain_status` se aplicável. Entregue hipóteses priorizadas, evidência sanitizada, impacto, ação sugerida e rollback; **não reinicie, redeploye, altere DNS ou mude variáveis**.

## 5. Catálogo por Venue

> Use `$rodada-ops` e [catalog-import](catalog-import.md). Prepare importação do CSV revisado `[arquivo, sem dados confidenciais]` para o slug interno `[SLUG]`. Revise esquema, formato de preço, station BAR/KITCHEN, produto já existente e diferenças. Execute apenas o preview em **ambiente isolado aprovado**, informe contagens e conflitos. Não usar `--apply` nem `--update-existing` sem aprovação específica.

## Formato de resposta obrigatório do agente

```text
Ação solicitada / ambiente / Venue:
Modo executado: READ-ONLY | ESCRITA APROVADA | BLOQUEADO
Autorização / ticket:
Fonte/branch/commit SHA e IDs de infraestrutura confirmados:
Inventário e evidências (links sanitizados):
Mudanças staged detectadas:
Mudanças de fato executadas:
Testes executados e resultados:
Testes não executados / incertezas:
Riscos e impacto em cliente/dados/custo:
Critérios GO/NO-GO e plano de rollback:
Próximo responsável:
```

Se não houver tool, permissão ou evidência, declarar **BLOQUEADO**; não substituir uma operação por outra nem inventar sucesso.
