# Codex Evals & Evidence — Rodada

Este slice do PR 3 adiciona **14 cenários** (`positive` + `negative` por cada uma das **7 skills na main**), um **analisador conservador de traces** e um **registro inicial** de aceites em specs. O trabalho automatizado no CI é **somente validação de contratos**, não uma bateria de modelo, não um relatório de homologação nem um deploy. Uma skill nova como `rodada-code-review` do PR #128 só entrará no catálogo quando estiver na main.

## 1. Casos e execução real no Codex (manual)

Fonte dos casos: [`evals/cases.json`](evals/cases.json). Verifique `codex --version`, autenticação e versão da skill antes de comparar runs. Faça isso em **clone/checkout descartável**, sem credenciais, tokens de banco, Railway de produção, MCPs com escrita ou contas de cliente; mantenha o Codex sem permissão de mutação externa. `--sandbox read-only` protege o filesystem do sandbox, **não garante** que MCP conectado seja read-only. Não use `--full-auto` nem habilite ambiente produção.

```sh
python scripts/agent_evals.py validate
python scripts/agent_evals.py list
mkdir -p /tmp/rodada-eval
python scripts/agent_evals.py prompt --case-id ops-negative > /tmp/rodada-eval/prompt.txt
codex exec --json --sandbox read-only - < /tmp/rodada-eval/prompt.txt > /tmp/rodada-eval/trace.jsonl
python scripts/agent_evals.py grade --case-id ops-negative --trace /tmp/rodada-eval/trace.jsonl
```

Não commitar `trace.jsonl`: pode conter comando, caminho local, identificadores e outras informações sensíveis. Revise/redija antes de compartilhar. Nunca cole tokens ou use trace sintético para dizer que o Codex passou.

**O que o validador observa:** eventos reais `item.started` / `item.completed` de `command_execution` e `mcp_tool_call`, fim da sessão e padrões de operações perigosas. Status possíveis: `VIOLATION`, `INCONCLUSIVE`, `MANUAL_REVIEW_REQUIRED`. Este script não promete detectar toda mutação, prompt injection, carregamento automático de skill ou correção semântica da resposta. Mesmo sem achados, revisor distinto deve inspecionar a saída/trace contra [`expected`](evals/cases.json), observar se a skill certa foi usada e registrar avaliação em artefato privado.

Para repetir uma avaliação: mesmo caso, base SHA, versão Codex/modelo, contexto, tools/conexões e sandbox. Alterar só uma variável quando comparar duas versões de skill; métricas somente de execuções reais. Uma execução é **um ensaio**, não demonstra confiabilidade estatística.

## 2. Registro de critérios e evidências

Fonte: [`evidence/registry.json`](evidence/registry.json). Exemplos iniciais mapeiam critérios das Specs **008, 025 e 027** a arquivos de teste existentes. **Todos** iniciam como `UNVERIFIED`, mesmo que a spec assinale uma checkbox. Arquivo de teste existente não comprova que foi executado nem que passou.

```sh
python scripts/spec_evidence.py validate
python scripts/spec_evidence.py report
python scripts/spec_evidence.py report --format json
```

O relatório percorre **todos os diretórios `specs/*/acceptance.md` do checkout**, não só os registros mapeados; mostra critérios com ID do tipo `TS027-01`, critérios ainda não mapeados, registros e status. Specs sem IDs consistentes são marcadas como `UNSTRUCTURED`, jamais aceitas por contagem zero. Números 021/022/024/025 repetidos são isolados por **`spec_path` completo**.

**Promoções manuais condicionais:**

- `UNVERIFIED`: apenas contrato e caminhos de testes planejados; `proofs={}`.
- `TESTED`: comando executado, resultado PASS, SHA 40 hex, ambiente autorizado e URL da evidência; confirmação externa ainda indispensável.
- `CI_VERIFIED`: além disso, URL de workflow com conclusão success e **mesmo SHA**.
- `HOMOLOGATED`: mais uma decisão humana identificada e observação real descrita. CI verde, screenshot ou emulator isolado não substituem aceite operacional.
- `DEPLOYED`: deployment ID, URL, ambiente e SHA comprovados; nunca inferir Railway/Play ativo a partir da main.

O validador é **estrutural**: não acessa URL, não confirma que workflow passou e não faz mutation. Integrador deve buscar logs e conferir SHA/ambiente à mão antes de registrar PASS. Documentos históricos `specs/*/evidence.md` continuam válidos como fotografias, não são sobrescritos.

## 3. Critérios de evolução

- Rodar estas 14 avaliações **manualmente** no Codex sem MCPs com escrita e registrar os dois tipos de falha: `skill routing` e comportamento/ação.
- Incluir a oitava skill quando [PR #128](https://github.com/procopio420/rodada/pull/128) entrar na main. Atualizar casos positivo/negativo **no mesmo PR** que criar skill nova.
- Revisar os critérios sem IDs e padronizar novos aceites com identificadores únicos por spec; automatizar verificação **real** de workflows via API autenticada e contexto de confiança antes de promover `CI_VERIFIED`.
- Avaliações que precisam de ação mutável devem ser em sandbox descartável, com credenciais fake, ferramentas stub e gate de custo/safety; nunca em Railway ou dados de cliente.

Referência de abordagem: [Testing Agent Skills Systematically with Evals](https://developers.openai.com/blog/eval-skills).

**Prova do PR 3:** validação de schema/paths/cases e testes stdlib. **Não executa Codex nem afirma qualquer case PASS.**
