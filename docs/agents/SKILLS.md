# Rodada — project-local Agent Skills

Skills are **task procedures**, not substitutes for [AGENTS](../../AGENTS.md), [KB](README.md), product specs or release evidence. Version-controlled local skills follow the open `SKILL.md` + YAML `name`/`description` front matter convention.

## Discovery and activation

- **Codex / agents supporting open repository skills:** canonical `.agents/skills/<name>/SKILL.md` folders.
- **Claude Code:** thin `.claude/skills/<name>/SKILL.md` entrypoints discover each name and link to the exact canonical file; content stays single-source to prevent drift. These are regular Markdown files (not symlinks), safe to clone on Windows.
- For agents with no auto-discovery, find matching name below and read its canonical `SKILL.md` explicitly. Discovery depends on the agent runtime; a GitHub merge alone does not magically install skills on an existing chat session.

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

Only edit canonical `.agents/skills` procedures; keep thin `.claude/skills` wrappers with matching `name` and `description`. The existing lightweight [KB check](../../scripts/check_agent_kb.py) validates discovery manifests and links; it does **not** run app tests or approve deployments. Don't add undocumented permission bypasses, secrets, outside network calls or release authority to skill instructions.

External format references: [Agent Skills standard](https://agentskills.io/) and documentation for your selected runtime.