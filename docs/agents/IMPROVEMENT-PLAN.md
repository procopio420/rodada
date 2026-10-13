# Plano de evolução — AI engineering agents no Rodada

**Objetivo:** agentes com contexto seletivo, entregas verificáveis e integrações sem conflito; o produto permanece spec-driven. Horizonte de execução **por gates, não por cronograma presumido**.

| Fase | Prioridade | Entrega | Gate de aceite |
| --- | --- | --- | --- |
| 0. Foundation | P0 | AGENTS raiz atualizado; AGENTS locais API/Web/Android; índice da KB; procedimentos; auditoria de drift | Links resolvem, arquivos versionados, regras não contradizem invariantes do produto; PR revisado |
| 1. Truth reconciliation | P0 | ADR sucessora de domínio `.bar`, README/host docs atualizados segundo a decisão; tabela de rollout vs intenção | Sem referência canônica contraditória em docs **vigentes**, validação de Host/tenant/preview documentada; histórico preservado |
| 2. Spec evidence registry | P1 | Matriz por `spec_path` com estado, owner, base SHA, PR, teste e evidência; reconciliar #101/#116/#107/#118/#119 e demais PRs | Nenhum ACCEPTED/PASS sem vínculo teste+SHA; separar main, PR e deploy; nada marcado a partir de checklist isolada |
| 3. Small KB checks | P1 | Verificação rápida de paths/links locais, specs sem colisão de identidade por caminho, heads/snapshots marcados, PR template "KB impact" | Check rápido e determinístico, sem runners pesados duplicados; falsos positivos controlados |
| 4. Delegation lanes | P1 | Templates de tarefa/handoff para API, Web, Android, QA e integrador; ownership de arquivos e integração em fila | Dois agentes paralelos conseguem entregar mudanças em módulos distintos sem perda de trabalho; integ. testa ambos |
| 5. Proof-of-work automation | P2 | Compilar resultado de testes e CI por SHA, comparar com critérios por spec, produzir resumo de drift sem prometer release | Relatório auditável com links/ambiente, falhas preservadas, não declara homologação a partir de CI |

## Diretrizes da arquitetura de agentes

**Orquestrador:** decompõe pedidos, escolhe spec e informa HEAD; controla mudanças transversais, integra evidências e faz revisão de riscos. **Especialistas:** API/domínio, Web/UX, Android/device, QA/integrador. **Revisor independente:** valida invariantes financeiros, tenant, auth e regressões de não-happy path quando o slice toca áreas críticas.

Evitar "um agente que altera tudo": subagentes compartilham contrato e base, **não** worktree/arquivos concorrentes. Critérios e evidências são propriedade de um integrador no final. Não provisionar serviços, workflows ou ambientes pagos como parte desta iniciativa.

## Indicadores de melhoria (medir, não inventar)

- Tempo até localizar contrato correto; % PRs com spec/aceite/links; docs drift identificados antes de merge.
- % changes com teste negativo quando afetarem dinheiro/tenant/offline; quantidade de conflitos e rework pós-integração.
- % afirmações de pronto suportadas por SHA/CI/ambiente; incidentes de "verde em branch, não em main".
- Custo de Actions por PR e duração dos gates após adoção das regras (não aumentar sem benefício comprovado).

**Não faz parte desta fase:** agentes operacionais com acesso a dinheiro de clientes, decisões autônomas de deploy/Play/DNS e habilitação de pagamento real.

## Evidência de execução — 13/10/2026

- **Fase 0:** concluída por PR #121, documentação e regras versionadas na main.
- **Fase 1 (contrato documental):** ADR 0018 + README/host docs alinhados a `rodada.bar`, código Spec 025 reconciliado com merge do PR #116; **rollout e homologação continuam pendentes**.
- **Fase 3 (primeiro slice):** `scripts/check_agent_kb.py` + testes stdlib + workflow Knowledge Base com path filters; sem dependências, banco ou runners Android/PostgreSQL. Só verifica documentação, não aceita comportamento.
- **Fases 2, 4 e 5:** seguem abertas para evidências por SHA e coordenação multiagente automatizada.
