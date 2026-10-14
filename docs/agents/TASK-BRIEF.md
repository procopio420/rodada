# Brief e handoff para agentes paralelos

Use este template ao delegar trabalho a especialistas API, Web, Android, QA ou integrador. Atribuição de arquivos é um contrato, não um pedido para editar tudo indiscriminadamente.

## Brief de execução

```text
Missão:
Spec (path completo) / acceptance IDs:
Base main SHA e branch de trabalho:
Arquivos de ownership (write set permitido):
Arquivos de leitura (interfaces, ADRs, KB):
Escopo e resultado verificável:
Fora de escopo:
Invariantes (financeiro, tenant, auth, replay, design, dados):
Contrato entre módulos (API/DTO/events/schema):
Testes exigidos e ambiente isolado:
Evidências a registrar (URL/commit/comando/resultado):
Bloqueios e ações externas proibidas:
Classe preliminar de risco R1/R2/R3:
Fontes não confiáveis recebidas (issue/log/MCP) e controles:
Critério de handoff ao integrador:
```

## Handoff exigido

```text
Branch e HEAD exatos:
Diff/commits entregues:
Spec e critérios alterados:
Interfaces mudadas / contratos preservados:
Testes PASS executados (comandos, SHA, ambiente):
Testes FAIL, skips e testes NÃO executados:
Riscos/observações negativas:
Drift encontrado na KB:
Conflitos potencialmente concorrentes:
Revisão independente? (identificador do outro contexto, head SHA, findings e status; se ausente, REVIEW_BLOCKED em R3):
Entradas suspeitas / prompt injection / mitigação:
Merge/deploy/publicação executados? (sim/não e evidência):
Próxima ação + responsável:
```

**Coordenação:** integrador detém arquivos compartilhados de contrato, migrations, tokens de design, CI e release; especialistas não fazem merge ou deploy por inferência. Uma branch por fronteira de escrita. Em conflito, comparar semântica das duas implementações e preservar invariantes, testes e evidências; não descartar mudanças remotas para obter árvore limpa. Ver [AGENTS](../../AGENTS.md) e [procedimentos](PROCEDURES.md).
