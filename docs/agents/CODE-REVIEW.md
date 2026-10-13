# Protocolo de revisão de AI coding — Rodada

**Escopo:** revisão de implementação, PRs e planos de release produzidos por Codex ou humanos. Preserva [AGENTS](../../AGENTS.md), [procedimentos](PROCEDURES.md) e specs. **Revisão independente não é a mesma coisa que CI e não autoriza merge/deploy**. Skill operacional: [`rodada-code-review`](../../.agents/skills/rodada-code-review/SKILL.md).

## Classificação antes do PR (pelo risco máximo, não pela quantidade de linhas)

| Classe | Exemplos | Evidência/revisão |
| --- | --- | --- |
| **R1 — baixo** | Copy isolada, docs, refactor local sem contrato, assets sem lógica | Autor confere diff e links/testes afetados, registra skips e risco residual. Segundo review opcional. |
| **R2 — moderado** | UX de operação, telas com mutações, catálogo, integração BFF não financeira, alterações de API sem fronteira de auth | Teste positivo + regressão negativa pertinente; revisão de outro contexto/agente recomendada e validação manual do fluxo quando aplicável. |
| **R3 — crítico** | Dinheiro/ledger, pagamentos/reembolsos, POS concorrente, tenant/Host/guest, permissões, dados/PII, migrations/restore, offline replay, alteração de CI/segurança, Railway/DNS/produção, Play publishing | **Revisor independente obrigatório** antes de recomendar merge; inspeção de casos negativos e prova por SHA. Se não houver revisor independente: status `REVIEW_BLOCKED` e encaminhar à revisão humana. Merge/deploy dependem de autorização explícita e dos gates reais. |

Classifique `R3` mesmo que o patch seja pequeno (ex.: uma linha afrouxando CSRF, alterando redirect de host ou removendo teste). Para PR com múltiplas áreas, use a mais severa.

## Ciclo de trabalho

1. **Autor (Codex):** identificar spec por caminho completo, base/head exatos, contratos, write set, hipótese e resultado esperado. Alterar apenas o necessário; executar testes do módulo e negativos de risco. Diferenciar `NOT_RUN`, `FAIL`, `PASS` e `BLOCKED`.
2. **Integrator:** inspecionar main e PRs concorrentes, reunir evidências e enviar ao revisor um brief novo: diff real, base/head, specs, riscos e testes; **não encaminhar apenas o resumo laudatório do autor**.
3. **Reviewer (contexto independente):** nova sessão/agente sem autoria do patch; ativar [skill de code review](../../.agents/skills/rodada-code-review/SKILL.md), conferir todos os arquivos alterados, contratos e resultados, procurar contraprovas; saída somente achados com `path:line`, severidade e cenário reproduzível.
4. **Autor corrige:** incluir regressão que falha antes e passa depois quando possível; atualizar o HEAD. A revisão anterior **não cobre** alterações subsequentes: reavaliar ao menos o novo diff e revalidar gates após rebase/merge de main.
5. **Fechamento:** nenhum P0/P1 aberto em R3, resultados dos testes executados no SHA final, riscos residuais e rollback conhecidos. Se evidência faltar, `NO-GO` ou `REVIEW_BLOCKED`, não declarar "revisado e aprovado".

## Checklist por fronteira (se relevante)

- Auth/tenant: revalidar `Venue` no servidor; negar duas Venues cruzadas em GET/POST/refresh/SSE/guest, Host desconhecido e cabeçalhos forjados; sessão revogada nega replay.
- Financeiro: centavos inteiros, append-only, provas de idempotência (mesma chave/payload e chave reusada com payload diferente), simultaneidade PostgreSQL, pagamento em `pending` e falha após commit.
- Android/estado: force-stop, reconexão, UUID original persistido, não duplicar pedido/pagamento; não tratar `loading` como offline.
- Web: BFF sem tokens no browser, CSRF/cookies host-only, real Django + PostgreSQL para integração, UI 360/390/430 e status real.
- Migração/ops: schema forward-compatible, backup/restore testados isoladamente, `start.sh` migrations, Railway staged changes, branch/SHA, domínios/certificado e custo; nenhum novo projeto Railway por bar.
- AI/tooling: [entradas não confiáveis](UNTRUSTED-INPUTS.md), segredos ausentes do diff/log, nenhum `curl | sh` ou script de terceiro executado sem análise e aprovação.

## Formato de review

```text
Review type: INDEPENDENT | SELF_REVIEW | HUMAN
Base SHA / head SHA:
Classe R1 / R2 / R3 e motivo:
Findings (ordenados P0, P1, P2): arquivo:linha, pré-condição, falha, impacto, correção sugerida
Sem achados reproduzíveis? (sim/não)
Testes conferidos por link/SHA e quais não foram executados:
Dados/segredos/logs analisados? apenas conteúdo sanitizado:
Aprovação de GitHub efetiva? (sim/não; agente não se autoaprova)
Status: BLOCK | CHANGES_REQUESTED | ADVISORY | NO_FINDINGS_WITH_GAPS | REVIEW_BLOCKED
Riscos residuais / responsável / próximo gate:
```

## Estado da proteção de branch — auditoria inicial 13/10/2026

- Repositório `procopio420/rodada`: consulta de **repository rulesets** retornou lista vazia. **Isto não comprova ausência de branch protection legada.**
- Consulta de **`main` branch protection** via conexão GitHub retornou `403 Resource not accessible by integration`. Portanto **não verificado** se review obrigatório, status checks ou conversas resolvidas são exigidos na plataforma.
- Antes de confiar em merge gates automáticos, administrador deve conferir em GitHub Settings → Branches/Rules: PR obrigatório na `main`, checks de API/Web/Android/KB conforme `paths`, aprovação adequada por alguém diferente do autor para R3, prevenção de bypass e proteção contra force push.
- [`CODEOWNERS`](../../.github/CODEOWNERS) define contato para áreas sensíveis; **não força revisão por si só**. A conta do proprietário do repositório não é um revisor independente dos próprios commits. Não afirmar enforcement até verificar configurações pelo administrador.

Este protocolo é mecanismo de **processo documentado**; não existe neste PR bot que faça revisão automática nem gate independente no GitHub comprovado.
