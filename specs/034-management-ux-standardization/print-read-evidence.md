# Manutenção — leituras de Impressoras

2026-10-20. Branch `codex/management-ux-alerts`, base HEAD `860b25d93da486d2416c6ddaccfdccd9605f8953`; alterações locais acumuladas, sem commit/push/publicação. R2 de leituras, preservando comandos/recovery.

## Problema e correção

Ocorrência herdada de set-state-in-effect no efeito de impressão. Separados GETs em readPrinting e aplicação estável dos resultados; efeito usa callbacks assíncronos e cleanup, mantendo intervalo5s, filtros/paginação, mensagens e reload depois de mutações. Nenhum timer artificial/supressão de lint.

Reproduzido problema real antes do código: resposta inicial failed_only=false liberada depois do filtrotrue substituía o job atual por job-old-query, embora botão Mostrar todos estivesse ativo. Cleanup invalida aplicação de respostas/erros das assinaturas anteriores ao mudar filtro/página/desmontar. Mutate/copyIntent/payloads/reimpressão intactos.

## Validação

- Baseline válida antes do código:1FAIL no assert final de job-filtered-query; snapshot mostrou job-old-query. Duas tentativas anteriores foram inválidas por mocks incompletos de agentes, corrigidos antes da reprodução válida.
- Build webpack/typecheck e ESLint de printing/page.tsx + novo teste PASS.
- Suite composta21casos:20PASS1FAIL por fixture ausente endpoints no teste de transporte inicial; mock adicionado. Rerun dos3testes de leitura:3PASS3,3s.18regressões de destinos/trabalhos/comandos passaram na composição. Não declarar21PASS em uma mesma execução.
- Testes cobrem filtro tardio, polling5s com falha de transporte, parada após saída e mensagem inicial. Comandos existentes interceptados preservam retry/confirm/cancel/reprint; quatro larguras/axe/layout exercitados pelas suites de UI. Sem alteração de aparência nesta rodada.
- Lint dos módulos anteriormente afetados:5erros restantes(pricing15,setup44,refunds55,house-account108/115); impressão e catálogo limpos. Contagem6→5.
- [Hashes de fontes/teste](../../docs/development/evidence/spec034-print-read/SOURCE-SHA256SUMS). Testes usam API interceptada, sem impressão física nem integração real. Não houve emissão de trabalho real.

## Revisão e limites

Revisor independente `/root/review_team_ux`:NO_FINDINGS_WITH_GAPS no loader. Conferidos GETs/aplicação/mensagens/polling e comandos intactos, sem execução de testes pelo reviewer. Última mudança após review adicionou somente fixture de endpoints ao teste de transporte; código de produto revisado permanece igual.

Limite explícito: active protege consultas do efeito após cleanup. Load após mutação e requisições sobrepostas do mesmo filtro continuam sem ordenação/invalidação, como antes. Não declarar todas as corridas de leitura resolvidas. GateR3 autenticado global REVIEW_BLOCKED, sem recomendação merge/deploy. Suíte global/integração real/manual não repetidas; NO-GO release/piloto permanece.

Próximo responsável: manutenção limitada dos5erros restantes, com revisãoR3 quando tocar financeiro/auth/dados/recovery. Preservar todas as slices e não reabrir redesign.
