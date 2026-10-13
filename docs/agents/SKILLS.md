# Rodada — project-local Agent Skills

Skills are **task procedures**, not substitutes for [AGENTS](../../AGENTS.md), [KB](README.md), product specs or release evidence. Version-controlled local skills follow the open `SKILL.md` + YAML `name`/`description` front matter convention.

## Discovery and activation

- **Codex (ferramenta adotada no Rodada):** descobre `.agents/skills/<name>/SKILL.md` no repositório. Não usar nem manter `.claude/skills/`.
- A descrição em YAML orienta o disparo automático; para selecionar explicitamente, mencione `$rodada-django-api`, `$rodada-nextjs-web`, `$rodada-static-html`, `$rodada-ui-design`, `$rodada-android-compose` ou `$rodada-pos-safety`.
- Para usar em tarefa de outra pasta do monorepo, execute Codex dentro do checkout; as skills raiz são descobertas a partir do repositório. Se uma alteração recente não aparecer na sessão, reinicie/atualize a sessão Codex.
- O GitHub não ativa uma skill em sessões já abertas: o agente precisa descobrir a pasta e carregar as instruções.

| Skill | Where to use it | Trigger |
| --- | --- | --- |
| [`rodada-django-api`](../../.agents/skills/rodada-django-api/SKILL.md) | `apps/api` | Models, DRF, concurrency, migrations, permissions |
| [`rodada-nextjs-web`](../../.agents/skills/rodada-nextjs-web/SKILL.md) | `apps/web` | Next.js, BFF, tenant, Web flows |
| [`rodada-static-html`](../../.agents/skills/rodada-static-html/SKILL.md) | `apps/landing` | HTML, CSS, SEO, legal pages |
| [`rodada-ui-design`](../../.agents/skills/rodada-ui-design/SKILL.md) | Web, Android, landing, brand | UX, visuals, screenshots, accessibility |
| [`rodada-android-compose`](../../.agents/skills/rodada-android-compose/SKILL.md) | `apps/attendance-android` | Kotlin, Compose, offline/lifecycle |
| [`rodada-pos-safety`](../../.agents/skills/rodada-pos-safety/SKILL.md) | Cross-cutting | Money, idempotency, tenant/guest security |

## Task routing

1. Read [AGENTS root](../../AGENTS.md) and module AGENTS, identify the spec by **full path**, then read **only** the relevant skill body.
2. On Web UI work, combine `rodada-nextjs-web` + `rodada-ui-design`. On Android UI, combine `rodada-android-compose` + `rodada-ui-design`.
3. On money, permission, Host isolation, QR or offline retry, **also** use `rodada-pos-safety`; tests and release evidence remain mandatory.
4. Landing HTML gets `rodada-static-html` + `rodada-ui-design` only if the task affects visuals. No unnecessary React/Next framework for a static page.
5. Don't load every skill merely because it's present; keep agent context bounded and inspect project code for actual APIs/version.

## Maintenance

Edite somente `.agents/skills/<name>/SKILL.md`. O [validador da KB](../../scripts/check_agent_kb.py) valida frontmatter, nomes, descrições e links; não roda testes de aplicação nem autoriza deploy. Não duplique skills em pastas de outras ferramentas. Don't add undocumented permission bypasses, secrets, outside network calls or release authority to skill instructions.

Referências: [Codex Skills](https://developers.openai.com/codex/skills) e [Agent Skills standard](https://agentskills.io/).