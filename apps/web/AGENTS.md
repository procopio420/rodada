<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

## Rodada Web — regras locais

Além de `../../AGENTS.md`, siga `../../docs/agents/PROCEDURES.md`, `../../docs/design/system.md` e `README.md` deste diretório. **Preserve intacto** o bloco `BEGIN:nextjs-agent-rules` acima: ele é mantido pelo Next.js e não deve ser removido em refatorações.

- Next.js 16.3.x, React 19; antes de alterar APIs do framework, leia a documentação instalada em `node_modules/next/dist/docs/` como instrui o bloco gerado.
- BFF é a fronteira de auth: nunca expor access/refresh token no navegador, nem contornar cookies host-only, CSRF, resolução de Venue ou assinatura de origem. Nunca usar URL pública como prova de autorização.
- Todo comando mutável deve ter readback canônico; SSE é atualização, não confirmação. Estados `loading`, rede degradada e erro real são distintos.
- Mesas, comandas, guest, produção e dinheiro mantêm as mesmas regras da API. Não iniciar PREPARING automaticamente; o operador inicia o preparo no fluxo definido.
- Mudanças visuais: validar 360/390/430 px e largura desktop, foco/teclado/touch e `npm run test:visual`; não atualizar baselines sem causa e comparação registrada.
- Gates comuns após `npm ci`: `npm run typecheck`, `npm run test:auth`, `npm run build`, `npm run test:visual`. Com integração Web↔API: `npm run test:integration` em PostgreSQL de teste, conforme `.github/workflows/web.yml`.
- Spec/PR para alteração de fluxo: incluir happy path, condição de corrida, timeout/resposta perdida, renovação/revogação de sessão e replay sem duplicação quando pertinentes.

## Skill sob demanda

Ative [`rodada-nextjs-web`](../../.agents/skills/rodada-nextjs-web/SKILL.md) para App Router, React e BFF; combine [`rodada-ui-design`](../../.agents/skills/rodada-ui-design/SKILL.md) em mudança visual e [`rodada-pos-safety`](../../.agents/skills/rodada-pos-safety/SKILL.md) quando houver dinheiro, Host/sessão, Guest ou replay. **Não edite** o bloco `nextjs-agent-rules` autogerado acima.
