# Manutenção — carregamento e seleção de Clientes

2026-10-20. Branch `codex/management-ux-alerts`, base HEAD `860b25d93da486d2416c6ddaccfdccd9605f8953`; working tree acumulado, sem commit/push/merge/publicação. Recorte R3 de leitura/contexto adjacente a autorização temporária de limite, com revisão independente.

## Correção

Eliminadas duas ocorrências herdadas de set-state-in-effect: carregamento inicial e sincronização do objeto selecionado. GET de sessão e paginação/deduplicação de comandas foram mantidos em readHouseResources. Aplicador estável conserva chave venue/staff/session, limpeza de PIN/histórico/clientes/visitas/intenção quando o ator muda e stale/erro.

A seleção guarda somente ID e deriva o objeto da lista canônica atual. Na aplicação dos dados, ID ausente é limpo; se a comanda reaparecer depois, não há reseleção automática. Limpeza por troca de ator precede a validação funcional do ID. Inspect continua limpando os mesmos rascunhos e a mesma intenção.

Consulta inicial passa a usar callbacks assíncronos com cleanup. Load manual/pós-ação, polling15s com visibilidade e listeners online/focus/offline mantêm comportamento anterior. Action, reauth, approve, payload, chave idempotente, expires e recuperação da intenção não mudaram. Sem supressão de lint, timer artificial ou mudança visual.

## Validação executada

- Baseline de ESLint:2 erros nas linhas108/115. Lint final do componente e teste:PASS.
- Inventário completo dos16 arquivos de implementação acompanhados na Gerência:0 erros e0 avisos. Os sete erros originalmente acompanhados foram resolvidos. Isso não equivale a lint de todo o repositório.
- Build webpack/typecheck, auth4 e tenant10:PASS.
- `test:visual management-customer-read.spec.ts management-customer-layout.spec.ts management-customer-results.spec.ts`:18 PASS em22,8s.
- Novos casos: atualização canônica de limite preserva rascunho; remoção/reaparecimento não reassocia seleção; override com resposta perdida mantém mesmo payload/chave após refresh; troca de ator limpa seleção; falha inicial mantém stale e não envia comando.
- Regressões de busca/cadastro,200/403, permissão negada, limites somente leitura, GET sem confirmação de mutação e reauth passaram nas quatro larguras dos testes existentes.
- [Hashes e inventário de lint sanitizado](../../docs/development/evidence/spec034-customer-read/). Não houve alteração de aparência nesta rodada.

## Revisão e limites

Review independente `/root/review_team_ux`:NO_FINDINGS_WITH_GAPS. Conferidos seleção canônica, validação funcional/limpeza por ator, paginação e intenção/payload preservados. Reviewer não executou os testes.

Limites herdados: concorrência entre refreshes/eventos, histórico/override retornando após troca de ator e callbacks manuais depois de desmontar não receberam ordenação/invalidação nova. Não inferir isolamento/replay reais de mocks. Integração Django/PostgreSQL, concorrência, operador, suíte global e lint global não foram executados nesta rodada. GateR3 autenticado continua REVIEW_BLOCKED; NO-GO para release/piloto.

## Continuidade

Manutenção dos sete erros de lint acompanhados concluída localmente, sem novos erros nesse conjunto. Próximo responsável: validação composta final após as manutenções e gates globais/manuais/integração autorizados. Preservar todas as alterações locais, sem reabrir o redesign nem declarar produção pronta por estes resultados.
