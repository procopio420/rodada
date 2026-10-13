# Quality Gates — Codex changes / Rodada

**Status:** rollout incremental, separado da [review independente (PR #128)](https://github.com/procopio420/rodada/pull/128) pendente no PR #128. Este documento não confere aprovação de merge, deploy ou aceite de produto.

## Política

- **Evitar debt explosion**: primeiro bloquear regressões novas; gerar relatório das falhas antigas para remediação deliberada. Não esconder erros com `|| true`; modo não bloqueante deve ser explicitamente identificado.
- **Nunca degradar os testes existentes** de Django/PostgreSQL, BFF/Playwright e Android unit/debug. Lint não substitui regressão funcional/financeira ou homologação real.
- **Não adicionar CI pesado duplicado**: anexar ao workflow do módulo; scope `apps/api` ou `apps/web` por path. Uma alteração apenas documental continua no Knowledge Base.
- A análise por linhas adicionadas é temporária: mudanças indiretas numa linha preexistente, regras de várias linhas e erros preexistentes continuam sujeitos a revisão. Full-project lint só vira obrigatório quando o baseline do módulo for sanado ou aceito com baseline versionado revisado.

## Matriz

| Módulo | Check | Modo no PR 2 | CI |
| --- | --- | --- | --- |
| API Django | Ruff `E4,E7,E9,F` em todo `apps/api`, compara diagnóstico com linhas **adicionadas pelo PR** | **Bloqueia** violação nova localizada em linha adicionada; informa quantidade total de dívida | `.github/workflows/api.yml` |
| Web / Next 16 | `npm run typecheck`, build, integração BFF real e visual/a11y existentes | **Bloqueantes**, mantidos | `.github/workflows/web.yml` |
| Web / código novo | Detectar `@ts-ignore`/`@ts-nocheck`, `eslint-disable`, `eval`/`new Function`, `NEXT_PUBLIC_*` com nomes de secrets e token no storage | **Bloqueia** novas linhas suspeitas | `scripts/quality/check_added_lines.py --kind web` |
| Web / ESLint | Next 16 removeu `next lint`; ainda não há ESLint nem lockfile compatível no projeto | **Pendente**: implementar `eslint` CLI com config flat e lockfile, medir dívida antes de tornar blocking. Não chamar checagem regex de ESLint. | Próximo slice |
| Android | `./gradlew lintDebug --stacktrace` | **Bloqueante** após auditoria inicial PASS em [run #38485120931](https://github.com/procopio420/rodada/actions/runs/38485120931); report HTML/XML arquivado por 7 dias. | `.github/workflows/android.yml` |
| Android | JVM tests e `assembleDebug` existentes | **Bloqueantes**, mantidos | `.github/workflows/android.yml` |

## Linha adicionada: contrato e limitações

O script [`check_added_lines.py`](../../scripts/quality/check_added_lines.py) usa `git diff BASE_SHA HEAD --unified=0` com `fetch-depth: 0`, sem executar o texto do diff, sem acesso a segredo e sem mudar arquivos. As linhas `+` são numeradas no arquivo novo, e diagnósticos Ruff JSON cuja `location.row` coincide com elas bloqueiam o check. Resto do arquivo tem lint calculado e **contado**, mas só violações em código novo geram exit 1. Isso evita que dívida antiga bloqueie PRs que não a tocaram. A checagem Web lê também apenas linhas adicionadas.

**Limitações importantes:** um bug novo que se manifesta em uma linha existente, ou uma mudança indireta de contrato, pode escapar da comparação. Revisão humana/independente e os testes continuam obrigatórios para risco R3. `workflow_dispatch` sem base de comparação usa o SHA atual e produz somente relatório total do Ruff, não uma prova de ausência de regressões.

## Validação e evolução

1. Rodar `python -m unittest discover -s scripts/tests -p test_quality_added_lines.py -v`; no CI da API esse check é executado explicitamente.
2. Ler contagem total de Ruff e o resultado de added-line gate; registrar o run/commit.
3. Inspecionar relatório `android-lint-report` nos artefatos de Actions; classificar warnings. `lintDebug` é agora **bloqueante**; sem artefato ou falha de task, tratar como FAIL. No HEAD anterior (#129, SHA `823b91c5`) a task passou e gerou artefato; validar novamente após esta mudança.
4. Adicionar ESLint 9 e `eslint-config-next` alinhado com Next 16 via `npm install -D`, atualizar/commitar package-lock, configurar `eslint.config.mjs`; executar `npm ci && npm run lint`, com baseline real e revisão de falsos positivos. Não instalar dependências transitórias via `npx` no CI.
5. Migrar Ruff para full blocking após corrigir ou aprovar baselines por regra/arquivo e preservar visibilidade de debt. Android já executa `lintDebug` bloqueante, mas problemas de warning permanecem auditáveis.
6. Mensurar tempo extra das Actions; se > ganho de detecção, otimizar job sem remover testes.

Referências: [política de CI](../ci-workflows.md), [AGENTS raiz](../../AGENTS.md), [review (PR #128)](https://github.com/procopio420/rodada/pull/128), [fonte Next 16](https://nextjs.org/docs/app/api-reference/config/eslint).
