# S5 — fechamento local da padronização

2026-10-20. Branch `codex/management-ux-alerts`, base HEAD `860b25d93da486d2416c6ddaccfdccd9605f8953`; working tree acumulado, sem commit/push/merge/publicação. Estado remoto não atualizado nesta rodada.

## Correção final

Reproduzida perda de foco no retorno produtos→Cardápio: teste products360 falhou em toBeFocused antes da implementação. Helper existente ampliado para products/customizations; componente de links lembra origem/scroll e restaura foco ao montar a aba; retorno HTML registra origem, mantendo URL. Entrada direta cria origem padrão. Storage bloqueado preserva navegação sem garantir foco. Guardas de cliques modificados preservados. Sem dados de catálogo/credenciais no storage e sem alterações de auth, dinheiro, preços, API ou comandos.

Arquivos:lib/client/management-return.ts;components/management-catalog-navigation.tsx;app/manage/page.tsx;app/manage/products/page.tsx;components/catalog-customization-editor.tsx;teste management-menu-return.spec.ts, todos em apps/web.

## Validação executada

- Regressão antes:1FAIL por foco inativo, URL e aba corretas.
- Build webpack/typecheck PASS; ESLint dos novos componentes/helper, wrapperprodutos, manage/page e teste PASS. Lint herdado dos módulos existentes permanece conforme relatório conjunto.
- Oito retornos responsivos, dois links diretos e storage bloqueado, com foco visível acima da barra e ausência de escrita de API.
-9PNG (baselineproducts360 e8depois), hashes de imagens/fontes em [evidências](../../docs/development/evidence/spec034-menu-return/). Inspeção antes/depoisproducts360 e customizations390 confirma foco visível sem alteração da disposição.
- Revisão independente local `/root/review_team_ux`:NO_FINDINGS_WITH_GAPS. Copy/hrefs preservados, duas novas origens permitidas, áreas montadas condicionalmente. Reviewer não executou testes. Gaps: cliques modificados e restauração numérica de scroll grande sem teste explícito; Back/Forward coberto na suíte adjacente. GateR3 autenticado global segue REVIEW_BLOCKED.

## Matriz final de evidência

| Área/critério | Resultado local | Limite de aceite |
| --- | --- | --- |
| Cinco abas, destinos, aliases/histórico (AC01/02) | PASS automatizado na composição e regressões | Percurso de operador pendente |
| Retorno/foco Gestão e Cardápio (AC03) | PASS nas rotas exercitadas | Bloqueios/recovery reais e casos manuais não homologados |
| Hierarquia, tokens e ações (AC04/05/06/08) | Implementados nos recortes S1–S4; capturas e testes | Não comprova ganho operacional medido |
| Financeiro/auth/recovery (AC07/09) | Regressões interceptadas, auth4/tenant10 na rodada conjunta | Integração Django/PostgreSQL, concorrência/replay e review autenticado pendentes |
| Responsividade/acessibilidade (AC10) |360/390/430/1280,axe/teclado,CSSzoom/fontes nos recortes | Zoom nativo/leitor de tela/dispositivo e operador NOT_RUN |
| Evidência e revisão (AC11/12) | Manifests,build/tipos e review local | Lint7erros herdados FAIL; suíte global não concluída; CI/PR final não publicados |

## Decisão e próximo responsável

Padronização visual planejada S1–S4 e fechamento local S5 entregues. Nenhum novo recorte visual planejado na fila. Não equivale a concluir todos os ACs ou homologar produto. GO apenas para inspeção local. NO-GO para release/piloto/merge até gates pendentes; não há autorização de publicação.

Próximo responsável: validação manual com operador e integração/review final em escopo autorizado; priorizar achados reproduzidos e separar falhas herdadas de regressões. Não reiniciar o redesign nem apagar alterações locais. Rollback da apresentação deve ser por diff atribuído/revisado, sem reset do checkout ou alteração de dados.

Execução final focalizada: management-menu-return, management-navigation, management-subpages, management-menu-entry e management-customization-entry —54 PASS em1,7min. Não repetida toda a composição de245casos após a correção localizada; resultados anteriores e rerun21 de sessão constam em s5-review-evidence.md.
