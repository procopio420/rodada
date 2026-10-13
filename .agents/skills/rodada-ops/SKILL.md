---
name: rodada-ops
description: Use when operating or diagnosing Rodada on Railway MCP, onboarding venues, provisioning staff access, importing catalogs, responding to incidents, or planning backups and rollbacks.
---

# Rodada operational agent — read-first/runbook-driven

1. Read [OPS runbook index](../../../docs/ops/README.md) and choose the **single** runbook matching the request.
2. Read [AGENTS](../../../AGENTS.md), [procedures](../../../docs/agents/PROCEDURES.md), relevant spec and system boundary; for financial/tenant operations also use `rodada-pos-safety`.
3. Before mutation, gather via available read-only tools: actual Railway project/environment/service, GitHub SHA/PR, pending staged changes, current deployment, owner/venue identity and existing authorization constraints.
4. Default to **plan and read-only investigation**. A request to "prepare a runbook" or "investigate" is not approval to deploy, create staff/Venue, modify DNS, expose secret, alter database, trigger payment or accept staged changes.
5. Explicit confirmation must name the target and operation. Treat `Railway.accept_deploy` as applying **all** staged environment changes; `Railway.redeploy` reuses a build; no current Railway MCP `manage.py shell` action.
6. Never use `Railway.list_variables` just to inspect variables: returns secret values. Use `describe_service.variableNames` and sanitize logs.
7. If source documentation conflicts with live code/capabilities, stop at the read-only boundary and report drift, not a guessed success.
8. Every handoff reports actions **actually executed**, SHA, environment, evidence, untested gates and rollback readiness. CI/Railway SUCCESS is not certification of real-money flow, TLS or site pilot.

Choose a procedure:
- [MCP Railway deploy/rollback](../../../docs/ops/railway-mcp-release.md)
- [Onboard Venue](../../../docs/ops/onboard-venue.md)
- [Staff account/access](../../../docs/ops/staff-access.md)
- [Incident diagnosis](../../../docs/ops/incident-response.md)
- [Catalog import](../../../docs/ops/catalog-import.md)
- [Backup and restore](../../../docs/ops/backup-restore.md)
