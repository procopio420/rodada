# Baseline e mapa da Gerência — 2026-10-19

Base de código: `e82d36c453d44c861b26f104afa39bcc8706814d`. Consulta do navegador
local em `/manage#gestao` e captura fornecida identificam Gestão com três grupos,
links repetidos como botões secundários e utilitários no header. A sessão local
tem código adicional; não atribuir sua captura a pixels comprovados da main.
Inspeção de código confirma estrutura equivalente na base examinada. Nenhuma
pesquisa com operadores, duração de tarefa ou taxa de erro foi medida.

## Inventário e categoria

| Categoria | Rotas existentes examinadas/mapeadas | Fontes de código e preservação |
| --- | --- | --- |
| Estrutura | `/manage` e hashes das cinco áreas | `apps/web/app/manage/page.tsx`, `apps/web/components/management-nav.tsx`; títulos, aliases e histórico |
| Gestão | `/manage/setup`, `/manage/customers`, `/manage/alerts/settings`, `/manage/printing`, `/staff` | Agrupamento atual; manter destinos e capabilities reais; não redesenhar login compartilhado |
| Operação | `/manage/tables`, `/manage/table-turnover`, `/attendance`, `/pos`, `/bar`, `/kitchen` | Alterar apresentação gerencial/retorno; implementação de Atendimento/estações fica fora |
| Financeiro | `/cash`, `/manage/daily-close`, `/refunds`, `/manage/pricing`, `/reports` | Revisão e consulta; reauth, saldo, calendário e recuperação existentes |
| Cardápio | `/manage/products`, `/manage/catalog` | Preservar editor de categorias e criação única da Spec007 |

O inventário é de destinos, não prova de execução end-to-end. Páginas compartilhadas
como Caixa, Relatórios e Sessão só recebem adaptações gerenciais de retorno/layout
após checar consumidores; nenhum redesign global está autorizado por este plano.

## Achados e hipóteses

1. **Observado em Gestão:** links de navegação têm aparência de botões homogêneos
   dentro de painéis; hierarquia de destinos pode ser mais clara com linhas
   descritivas e menos bordas repetidas.
2. **Observado no código:** destinos internos usam cabeçalhos/retornos locais;
   padronização deve ser precedida de captura por rota, sem assumir defeito em todas.
3. **Hipótese:** descrições curtas e agrupamento consistente tornam a localização
   de funções mais simples; validar tarefa real, sem alegar ganho percentual.
4. **Já existente:** navegação de cinco áreas, histórico e editor de catálogo.
   Não refazer esses motores nem usar checklists históricas como prova de ausência.

## Dependências e concorrência

PR #247 entregou organização da Gerência. PRs #262/#263 concentram integração UX2
de Atendimento; não são autorização para reescrever sua UI nesta spec.
Busca de PRs abertas com termos Gerência/management/fechamento/relatórios não
identificou proposta específica deste refinamento. Isso não comprova ausência de
trabalho local/concomitante. Antes de cada etapa: fetch, conferir PRs e ownership.

## Evidência a produzir na implementação

Para cada rota tocada: SHA, fixture isolada, mesmo papel/estado/viewport antes e
depois, screenshots comparáveis, tarefas percorridas e resultado de teclado/axe.
Dados não devem conter credenciais, PII ou operação real. Visual controlado não
prova backend: mutações exigem integração Django/PostgreSQL própria e readback.
Não anexar a captura autenticada local ao Git como fixture.

## Estado do planejamento

R1 documental; revisão de autoria, não revisão independente. Aceites de produto
NOT_RUN. Primeira implementação proposta: S1 Gestão após S0 baseline; demais
áreas dependem da avaliação do padrão nessa slice. Ver [plano](plan.md).
