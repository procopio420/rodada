# Plano por etapas — Spec 034

Uma PR de implementação por slice, com baseline próprio. Não declarar todas as
áreas prontas por compartilhar CSS. A PR atual contém apenas planejamento.

| Etapa | Prioridade | Entrega e limites | Gate / risco de implementação |
| --- | --- | --- | --- |
| S0 — Baseline e padrão | P0 de sequência | Capturar cinco áreas e páginas tocadas; mapear componentes, permissões e estados; registrar proposta do padrão gerencial | Inventário, fixtures, antes/depois planejados e decisão registrada; R1 documental |
| S1 — Gestão | P1, primeiro código | Linhas de navegação descritivas, grupos leves, header/utilitários, foco e retorno; depois setup/clientes/alertas/impressoras em sub-slices | AC01–05, AC09–12; R2 visual, R3 se tocar auth/dados/recovery |
| S2 — Agora e Operação | P1 | Exceções e próxima ação antes de resumos; listas com detalhe progressivo; salão/produção sem competir | AC06, AC09–12; R2/R3 conforme leituras/sessão; nenhum novo KPI |
| S3 — Financeiro | P1 | Organizar entrada de caixa/fechamento, ajustes e relatórios; padronizar consulta e hierarquia dos formulários por rota | AC07, AC09–12; R3 em fluxos financeiros, revisão independente obrigatória |
| S4 — Cardápio | P2 | Harmonizar página e formulários existentes, editor por categorias, feedback e retorno | AC08–12; R2/R3 conforme permissões/escrita; sem duplicar QuickCatalog |
| S5 — Validação composta | P0 de aceite | Navegação cruzada, estados adversos, comparação visual, teclado/leitor de tela e revisão integrada | AC01–12 na composição final; não autoriza release |

P0 de sequência/aceite é gate desta proposta; não classifica um defeito atual como
incidente crítico. S1 é a primeira entrega útil. S2–S4 devem ser reavaliadas após
S1, sem refazer telas que já satisfaçam o padrão.

## Ownership e arquitetura

S0/S1: `apps/web/app/manage/page.tsx`, `components/management-nav.tsx`, componentes
gerenciais e CSS estritamente escopado após inventário. Um responsável por arquivo
compartilhado; não editar o mesmo shell simultaneamente em etapas diferentes.
S2–S4: páginas da rota correspondente, testes relevantes e documentação no mesmo PR.
API, auth/BFF, migrations e Android não fazem parte do write set deste redesign.
Se necessários, parar a slice e propor contrato separado com risco/testes explícitos.

Nenhuma dependência nova de biblioteca ou nova arquitetura de rotas é necessária
por padrão. Reutilizar primitives; extrair somente padrões repetidos comprovados.
Não alterar navigation/hash/CSRF/cache para obter aparência nova. Fontes e tokens
existentes precedem CSS novo; mudança compartilhada exige verificar consumidores.

## Gates por PR de implementação

1. Conferir main/PRs, contratos e escopo; registrar baseline por SHA e rotas.
2. Atualizar aceite da slice, estados, fixture e comparação antes de implementar.
3. Executar testes focados; `npm run typecheck`, `npm run build`, lint dos arquivos
   e **`npm run test:visual`**, mantendo falhas anteriores e sem afrouxar assertions.
4. Percorrer navegador em 360/390/430/1280, zoom/fonte200%, teclado/leitor de tela,
   longos textos e recuperação. Mesmo fixture antes/depois.
5. Se fluxo mutável/financeiro/sessão for tocado: integração real Django/PostgreSQL
   descartável, negativos/concorrência/replay pertinentes e outro contexto revisor R3.
   Sem revisão real: REVIEW_BLOCKED. Nunca testar escrita no banco local compartilhado.
6. Atualizar spec/evidência/checkpoint com PASS/FAIL/NOT_RUN/BLOCKED por critério.

## Rollback e critérios de parada

Cada slice deve permitir reverter apresentação sem alterar dados, endpoints ou
intenção persistida. Confirmar isso em review; não prometer rollback operacional
sem ensaio. Perda de ação/permissão/recuperação, dados ocultos ou mudança indevida
de consumidor compartilhado bloqueiam avanço até correção e regressão.

## Decisões e proposta

Preservar cinco destinos é contrato existente. Linha descritiva e redução de
bordas são propostas visuais a testar em S1. Não há aprovação implícita de uma
composição pixel a pixel nem resultado de pesquisa. Alterações de arquitetura
duráveis exigirão ADR; esta spec não introduz uma decisão desse tipo.
