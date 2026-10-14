# Rodada — mapa da Knowledge Base para AI Agents

**Tipo:** índice operacional vivo; não é evidência de release. **Revisado:** 2026-10-13. **Base da revisão inicial:** `main@8afd1200c7fd3047e82939486e6b6afc84b14c7f`.

A KB versionada do Rodada é o conjunto `docs/`, `specs/`, `AGENTS.md`, ADRs e testes/evidências vinculados. **Não foi encontrada uma pasta de KB independente na raiz** nesta revisão; não confundir design KB, documentação e eventuais ferramentas externas.

## Entrada rápida — abra apenas o necessário

| Preciso decidir/alterar | Fonte de intenção | Fonte de implementação/evidência |
| --- | --- | --- |
| Produto, postura e domínio | [Visão](../product/vision.md), [princípios](../product/principles.md), [modelo](../domain/model.md) | Código API, testes de domínio |
| Novo comportamento | `specs/<caminho completo>/spec.md`, `acceptance.md`, `plan.md`, `tasks.md` | Testes na branch e evidência com SHA |
| Decisão durável | [ADRs](../adr/), [arquitetura](../architecture/overview.md) | Código/config, ambiente implantado quando realmente verificado |
| UI e interação | [Design system](../design/system.md), [operational UX](../design/operational-ux-review.md), specs visuais | `apps/web`, `apps/attendance-android`, capturas e Playwright |
| API/autorização/pagamento | [Arquitetura](../architecture/overview.md) + specs 001/006/008/009/011/012/014/017 | `apps/api`, PostgreSQL, testes de concorrência |
| Web/BFF/guest/tenant | Specs 004/024/025/026 e ADR 0016 | `apps/web`, suites Web+API, isolamento entre dois Venues |
| Android/recovery | Specs 006/008/014/024/026 + `apps/attendance-android/README.md` | JVM, emulador, force-stop, test device |
| CI, deploy, piloto | [Política de CI](../ci-workflows.md), [readiness](../releases/aderlan-pilot-final-readiness.md), [escopo Web-only](../releases/aderlan-web-only-homologation-2026-10-14.md) | GitHub Actions do **SHA**, Railway/hardware/operador verificados, não screenshots históricos |

Static quality: [incremental gates e dívida](QUALITY-GATES.md). Operações: [runbooks para Codex](../ops/README.md), incluindo Railway MCP, venues, usuários, incidentes e backups. Skills por stack: [catálogo e regras de descoberta](SKILLS.md). Abra a skill correspondente apenas quando a tarefa realmente exigir.

Revisão de AI coding: [protocolo independente por risco](CODE-REVIEW.md) e [proteção contra prompt injection](UNTRUSTED-INPUTS.md). Casos exemplares em [review examples](REVIEW-EXAMPLES.md).

Codex Evals & Evidence: [cenários, trace grading e registro de critérios](CODEX-EVALS-EVIDENCE.md). É um gate estrutural, **não** execução de modelo ou homologação.

Entrada universal: [AGENTS raiz](../../AGENTS.md) → [procedimentos](PROCEDURES.md) → [registro de specs](SPEC-REGISTER-2026-10-13.md) → spec exata → implementação e testes. Para delegação paralela, use o [brief/handoff](TASK-BRIEF.md).

## Evidência visual Android — 13/10/2026

[Auditoria visual executada](../design/android-visual-audit-2026-10-13.md),
[galeria e PNGs originais](../design/evidence/android-visual-audit-2026-10-13/index.html),
[manifesto](../design/evidence/android-visual-audit-2026-10-13/manifest.json) e
[plano em slices / screenshots Play Store](../design/android-visual-audit-2026-10-13-slices.md).
Base auditada: `41e32d9853bc18ad08f136f5ead8bddc80afec77`, APK real, API/PostgreSQL
isolados, cinco experiências executadas em emulador API 36. **NO-GO visual do produto**:
63 testes JVM e 44 PostgreSQL aprovados; teste instrumentado focado reprovado por
clipping com fonte 200%. Fotografia histórica, não homologação da main posterior,
hardware, release ou operação no bar. Dependências e repetição no
[runbook local](../design/evidence/android-visual-audit-2026-10-13/REPRODUCE.md).

## Fonte de verdade: regras para conflitos

1. **Contrato pretendido:** princípios + spec por pasta + ADR vigente. Um documento que diz "planejado" não confirma deploy.
2. **Comportamento implementado:** código/testes do commit inspecionado. Se divergir do contrato, marque **DRIFT**, não reescreva a intenção por dedução.
3. **Estado/GO:** aceite e evidência verificados para SHA, ambiente, data e scope; só homologação humana cobre hardware, fiscal e operação real.
4. **Snapshot datado:** relatórios em `docs/development/`, `docs/design/` e `docs/releases/` podem ser verdadeiros para outro SHA; não são inventário atualizado automaticamente.
5. **Conflito de documentos:** registrar decisão pendente e preservar a história das ADRs. Não presumir que "arquivo mais recente vence" nem que PR aberto foi mergeado.

**Evite seleção por número isolado:** 021, 022, 024 e 025 têm mais de uma pasta, com proprietários de contrato distintos. Nunca criar `specs/028-...` sem verificar a branch atual e PRs abertos: Spec 027 está em trabalho paralelo fora da main observada.

## Atualização obrigatória da KB no mesmo PR

- Mudou regra de produto/domínio: spec e critérios de aceite; ADR se for decisão durável.
- Mudou fluxo/UI: spec, design system se alterou padrão compartilhado, testes/evidência de paridade.
- Mudou auth/tenant/recebimento/recovery: contratos de segurança, cenários negativos e runbook aplicável.
- Mudou CI/deploy/host: política de CI, arquitetura/routing e runbook; distinguir previsto vs implantado.
- Mudou escopo/piloto/release: relatório de status e manifest com SHA/ambiente; não converter resultado automatizado em GO.
- Concluiu tarefa: handoff com SHA, comandos efetivamente executados, resultado e pendências; sem porcentagens não comprovadas.

Relatórios e checkpoints são **append-only de evidência**: conservar datas, IDs e SHA; para novo estado criar nova fotografia ou acrescentar seção datada, não apagar reprovações anteriores.

## Dívida documental conhecida

Leia a [auditoria de 13/10](KB-AUDIT-2026-10-13.md) e o [plano de melhoria](IMPROVEMENT-PLAN.md). A raiz canônica `rodada.bar` está registrada na [ADR 0018](../adr/0018-rodada-bar-canonical-domain.md); a arquitetura de roteamento continua sob Spec 025. **Atualização da decisão documental não comprova wildcard DNS/TLS, isolamento implantado ou homologação.**

Quando não houver evidência suficiente, responda `PENDENTE DE VERIFICAÇÃO` em vez de inferir PASS.
