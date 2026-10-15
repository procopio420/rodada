# Runbook — backup e ensaio de restore PostgreSQL

**Alto impacto.** Não baixar banco real ou dados privados para análise de agente por padrão. [Índice OPS](README.md), [API backup existente](../../apps/api/README.md) e [scripts originais](../../apps/api/scripts/).

## Gates

- Aprovação explícita de ambiente, origem, destino, finalidade, retenção, custódia criptografada, operador e ticket.
- Confirmar o DB de origem sem exibir `DATABASE_URL` ou `POSTGRES_PASSWORD`, disponibilidade de `pg_dump`/`pg_restore`, espaço e compatibilidade da versão.
- Separar backup **existente/atual** de **restore rehearsal**: jamais usar `POSTGRES_DB` como `RODADA_RESTORE_DB`; destino é novo/descartável e isolado.
- `Railway.list_variables` retorna segredos e **não deve** ser usado para listar configuração; verificar nomes com `describe_service`. Railway MCP não disponibiliza `pg_dump` por operação embutida.

## Procedimento

Operador autorizado obtém acesso de DB por canal protegido e segue scripts **existentes**, após inspecionar seu conteúdo na versão do checkout:

```sh
cd apps/api
# Prévia em ambiente descartável e com POSTGRES_* apontando SOMENTE para fonte aprovada.
# Nunca exibir valores dos secrets no terminal/log.
export RODADA_RESTORE_DB=rodada_restore_rehearsal
./scripts/rehearse_restore.sh
```

Alternativa em etapas: `./scripts/backup_postgres.sh`, depois `./scripts/restore_postgres_fresh.sh backups/<arquivo>.dump` e `./scripts/verify_restore.sh` com `RODADA_RESTORE_DB` isolado. Esses scripts **executam escritas no banco de ensaio** e geram artefatos de dados: não executá-los como verificação read-only ou sem permissão.

Checar desde o início a política de dados pessoais (criptografia, acesso mínimo, retenção e descarte). Dados de cliente/funcionário nunca devem ir para logs do agente ou PR.

## Evidências

Data, ambiente, script/SHA, retorno, hash do backup sem expor arquivo, destino descartável, resultado `verify_restore` para ledger/refund/guest/Tab/CashShift e janela de restauro observada. Não divulgar credenciais ou informações pessoais.

## Rollback / contenção

### Exceção lógica autorizada — Spec025, 2026-10-15

Após o Railway recusar backup oficial por exigir Pro, o usuário autorizou
explicitamente backup lógico por SSH, sem upgrade. O escopo é o PostgreSQL privado
existente do projeto `rodada-aderlan-demo-20261009/demo`, com restauração apenas
em PostgreSQL18 local descartável. A captura usa snapshot read-only consistente,
AES-256-GCM em streaming e custódia local fora do repositório com permissões0700
nos diretórios/0600 nos arquivos, chave separada e revisão de retenção em sete dias.
O restore usa tmpfs; não roda migrations/seed/rehearse_restore contra a origem.
Ver [contrato e comandos](spec025-preview-rollout.md#authorized-logical-backup-exception--2026-10-15)
e [resultado/hash](../../specs/025-tenant-host-routing/railway-151-checkpoint.md#logical-backup-exception-and-recovery-proof--2026-10-15).
Essa decisão substitui somente o gate de backup oficial desta execução, sem
autorizar flag compartilhada nem resolver o critério de preview separado.

Se backup ou restore falhar, **não** repetir contra banco ativo, não forçar drop de DB, não avançar migração de schema nem substituir backup anterior. Isolar o ensaio, investigar logs sanitizados e solicitar nova aprovação se o plano mudar. Restore real é um procedimento separado de alto risco e demanda aprovação humana e plano de consistência financeira.
