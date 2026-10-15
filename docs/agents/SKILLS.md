# Rodada — project-local Agent Skills

Skills are **task procedures**, not substitutes for [AGENTS](../../AGENTS.md), [KB](README.md), product specs or release evidence. Version-controlled local skills follow the open `SKILL.md` + YAML `name`/`description` front matter convention.

## Discovery and activation

- **Codex (ferramenta adotada no Rodada):** descobre `.agents/skills/<name>/SKILL.md` no repositório. Não usar nem manter `.claude/skills/`.
- A descrição em YAML orienta o disparo automático; para selecionar explicitamente, mencione `$rodada-django-api`, `$rodada-nextjs-web`, `$rodada-static-html`, `$rodada-ui-design`, `$rodada-android-compose` `$rodada-pos-safety`, `$rodada-code-review`, `$rodada-ux-research`, `$rodada-ux-critique`, `$rodada-ux-handoff` ou `$rodada-accessibility-review`.
- Para usar em tarefa de outra pasta do monorepo, execute Codex dentro do checkout; as skills raiz são descobertas a partir do repositório. Se uma alteração recente não aparecer na sessão, reinicie/atualize a sessão Codex.
- O GitHub não ativa uma skill em sessões já abertas: o agente precisa descobrir a pasta e carregar as instruções.

| Skill | Where to use it | Trigger |
| --- | --- | --- |
| [`rodada-django-api`](../../.agents/skills/rodada-django-api/SKILL.md) | `apps/api` | Models, DRF, concurrency, migrations, permissions |
| [`rodada-nextjs-web`](../../.agents/skills/rodada-nextjs-web/SKILL.md) | `apps/web` | Next.js, BFF, tenant, Web flows |
| [`rodada-static-html`](../../.agents/skills/rodada-static-html/SKILL.md) | `apps/landing` | HTML, CSS, SEO, legal pages |
| [`rodada-ui-design`](../../.agents/skills/rodada-ui-design/SKILL.md) | Web, Android, landing, brand | UX, visuals, screenshots, accessibility |
| [`rodada-ux-research`](../../.agents/skills/rodada-ux-research/SKILL.md) | Discovery, pesquisa de campo, validação com o bar | Jornadas, entrevistas, teste de usabilidade e síntese de evidências |
| [`rodada-ux-critique`](../../.agents/skills/rodada-ux-critique/SKILL.md) | Android/Web/screenshots e fluxos reais | Crítica heurística, densidade, scroll, hierarquia, erro, estados |
| [`rodada-ux-handoff`](../../.agents/skills/rodada-ux-handoff/SKILL.md) | UX aprovada → spec/plan/tasks/acceptance | IA, fluxos, telas, interações, estado, contratos e handoff |
| [`rodada-accessibility-review`](../../.agents/skills/rodada-accessibility-review/SKILL.md) | Web/Android/Guest e revisão pré-PR | WCAG 2.2, teclado, TalkBack, fonte, IME, contraste, toque |
| [`rodada-android-compose`](../../.agents/skills/rodada-android-compose/SKILL.md) | `apps/attendance-android` | Kotlin, Compose, offline/lifecycle |
| [`rodada-pos-safety`](../../.agents/skills/rodada-pos-safety/SKILL.md) | Cross-cutting | Money, idempotency, tenant/guest security |
| [`rodada-ops`](../../.agents/skills/rodada-ops/SKILL.md) | OPS, Railway, cadastro | Runbooks, incidentes e mudanças de ambiente com aprovação |
| [`rodada-code-review`](../../.agents/skills/rodada-code-review/SKILL.md) | PRs e segurança | Revisão independente, risco R1/R2/R3 e achados reproduzíveis |

## Task routing

1. Read [AGENTS root](../../AGENTS.md) and module AGENTS, identify the spec by **full path**, then read **only** the relevant skill body.
2. On Web UI work, combine `rodada-nextjs-web` + `rodada-ui-design`. On Android UI, combine `rodada-android-compose` + `rodada-ui-design`.
3. On money, permission, Host isolation, QR or offline retry, **also** use `rodada-pos-safety`; tests and release evidence remain mandatory.
4. Landing HTML gets `rodada-static-html` + `rodada-ui-design` only if the task affects visuals. No unnecessary React/Next framework for a static page.
5. For Railway MCP, onboarding de Venue/staff e incidentes, use `rodada-ops` + o runbook específico em [OPS](../ops/README.md); nenhuma mutação externa sem aprovação.
6. Para review de patch/PR, especialmente R3, use `rodada-code-review` em **contexto independente** do autor e inspecione o diff inteiro antes de concluir.
7. Don't load every skill merely because it's present; keep agent context bounded and inspect project code for actual APIs/version.

## Maintenance

Edite somente `.agents/skills/<name>/SKILL.md`. O [validador da KB](../../scripts/check_agent_kb.py) valida frontmatter, nomes, descrições e links; não roda testes de aplicação nem autoriza deploy. Não duplique skills em pastas de outras ferramentas. Don't add undocumented permission bypasses, secrets, outside network calls or release authority to skill instructions.

Referências: [Codex Skills](https://developers.openai.com/codex/skills) e [Agent Skills standard](https://agentskills.io/).
## UX designer skill pack (Codex)

Quatro skills locais originais e especializadas complementam a skill de coordenação `rodada-ui-design`, sem duplicá-la e sem criar um gerador de UI genérico:

1. **Discover:** `$rodada-ux-research` para tarefa, operador, fricção e evidência; não inventar entrevista, teste ou métrica.
2. **Critique:** `$rodada-ux-critique` para screenshot real, prioridade do viewport, interação, hipóteses e achados com evidência.
3. **Design & Handoff:** `$rodada-ux-handoff` para alternativas, decisão, estados, Android/Web, tokens e aceite executável.
4. **Accessibility & QA:** `$rodada-accessibility-review` para foco, teclado, TalkBack, fonte 200%, áreas seguras e responsividade.

O roteiro padrão é **pesquisa suficiente → crítica → proposta/contrato → implementação específica → QA visual e operacional**. Só carregar o que a tarefa pedir. Skill não permite alterar UI sem spec nem autoriza merge/deploy.

**Curadoria externa:** adaptamos princípios de [Anthropic Design Plugin](https://github.com/anthropics/knowledge-work-plugins/tree/main/design), [Vercel Web Interface Guidelines](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines), [Nielsen Norman Group](https://www.nngroup.com/articles/ten-usability-heuristics/) e [WCAG 2.2](https://www.w3.org/TR/WCAG22/). Não fazemos instalação cega dos pacotes externos: algumas skills originais usam comandos/integrações de Claude ou carregam instruções mutáveis da Internet em tempo de execução. As versões Codex aqui são revisáveis, locais, pequenas e seguem AGENTS.md; referência externa nunca ganha autoridade de execução. Nenhuma biblioteca/font ou script de terceiros foi importado.

