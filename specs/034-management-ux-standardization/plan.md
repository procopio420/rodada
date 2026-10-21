# Plano por etapas — Spec 034

Uma PR de implementação por slice, com baseline próprio. Não declarar todas as
áreas prontas por compartilhar CSS. PR268 contém planejamento; PR269/S1a e
PR270/S1b estão em draft. S1c–S1j permanecem locais, sem PR própria ou release.

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

S1j: resultados de Clientes/CSS e parâmetro opcional de mensagem do executor;
somente quatro consultas recebem null. Regressão da mensagem indevida primeiro,
baseline/source em visual-artifacts/spec034-customer-results. Não tocar comandos
de mutação, policy/override ou rede/persistência. Reviewer somente leitura.

S1i: wrappers de busca/cadastro no componente house-account.tsx e CSS Module
próprio. Cópia anterior em visual-artifacts/spec034-customers/before-house-account.tsx
separa o diff da slice. Políticas/limites/visitas/resultados/handlers fora do write set.

S1h: JSX da equipe em Setup e CSS Module, sem tocar state/handlers/gates/DTOs.
Baseline preservada em visual-artifacts/spec034-team para comparação de source
e pixels. Revisor independente somente leitura após candidato; autor preserva
ownership de escrita. Sem recomendação de merge ou aprovação GitHub por review local.

S1g: JSX de Mesas e zonas em Setup, CSS Module próprio, teste visual/evidência.
Tipos/estado/handlers, TableServiceRollout e equipe ficam intactos; não modificar
auth, permissões ou recuperação para obter aparência nova.

S1f: JSX/CSS dos trabalhos recentes, mantendo literalmente condições e handlers;
baseline com três estados e teste próprio de layout/condicionais/comandos403.

S1e altera somente apresentação da lista de destinos e CSS Module de Impressoras,
teste/evidência próprios. Não tocar agentes/rotas/trabalhos ou handlers existentes.

S1d toca somente JSX do formulário de destino, CSS Module próprio, teste focado e
documentação. Capturar baseline antes; preservar handlers e componentes de agentes,
rotas e trabalhos. Não extrair componente compartilhado sem necessidade comprovada.

S1c: formulário de Alertas, CSS Module local e teste próprio; três fieldsets de
prazos e confirmação separada. Baseline capturada antes do patch no build S1b,
mesma fixture em quatro larguras. Handlers/regras não fazem parte do write set.

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

S2a: baseline determinística, CSS Module restrito ao resumo/atalhos, regressões de navegação/estados e comparação antes/depois. Nenhuma mudança em dados/comandos.

S2b: baseline4larguras; CSS Module restrito à produção/entregas; lista semântica, agrupamento e atalhos existentes; teste de volume e erro inicial. Não tocar Salão nesta slice.

S2c: baseline4larguras antes do produto; reutilizar grade de contadores/atalhos localS2b e lista de indisponíveis; validar vazio/volume/teclado/zoomCSS e regressões.

S3a: baseline4larguras, destinos descritivos reutilizando CSS de Gestão sem alterar retorno/autorização; CSS local para linhas de caixa; revisão independenteR3 e testes focados. Não redesenhar páginas internas nesta slice.

Correção solicitada: link /staff no aviso de sessão encerrada existente;2testes focadosPASS, sem alteração de autenticação.

Refino visual de sessão: CSSModule local e hierarquia lock/título/texto/ação usando tokens; preservar contrato de login. Cinco testes focados PASS.

S3b: primeiro somente cabeçalho/data/ações existentes; CSSModule isolado, fieldset/retornoFinanceiro. Baseline4larguras e regressões daily-close antes de expandir para revisões/correções.

S3c: agrupar resumo emCSSlocal, lista semântica de bloqueios e regiões; handlers e formulário de revisão preservados; baseline4larguras e regressões financeiras antes de expandir para propostas.

S3d: fieldset/fields/ação de solicitação apenas; CSSModulelocal, manter handlers; baseline4larguras, teste403payload e regressõesPIN.

S3e: artigos nomeados e formulário de decisão local; mesmos comandos/estados. Baseline4larguras e regressãoPIN/autoria/rascunhos.

S3f: fieldset/região PIN eCSSlocal; baseline4larguras com REAUTH_REQUIREDsimulado, cancelamento sem replay, composiçãoS3b–S3f e regressõesPIN.

S3g: entradaEstornos apenas, labelsvisíveis/retorno eCSSlocal; sem alterar intent/comandos. Baseline/regressões financeiras existentes/reviewR3.

S3h: grupo/resumo e histórico locais, mesmo seletor/cálculos/locks; baseline4larguras e regressões refundintent/labels/zero-refund.

S3i: campos e ação emfieldsetlocal, labelsvisíveis/IDs, nenhumhandleralterado. Baseline4larguras,403payload e regressões financeiras/reviewR3.

S3j: heading/painelpendenteCSSlocal, mesmaverificação/locks; baseline4larguras e composiçãoEstornos/reviewindependente.

S3k: fieldsets/gradeCSSlocal eheaderFinanceiro, handlersliteralmenteiguais; baseline4larguras/PUT403conversão e reviewR3; não tocaraprovações.

S3l: artigos/valores/açãoCSSlocal, callbacksiguais; baseline4larguras e403/reviewR3, depois composiçãoPolítica/aprovações.

S3m: cabeçalho/fieldsetperíodoCSSlocal somente; baseline4larguras eGET/403stale/CSVdisabled; campos/totais/calendarCSVinalterados.

S3n: particionarsomente2keysatuaisidentificadas e preservar outras/fallback/ordem interna;CSSlocalresumo,baseline4larguras e regressõesperíodo/parity.

S3o: resultadosdiários emartigos eprodutos/métodos/pedidos emlistasCSSlocal; expressões/mensagensvaziaspreservadas; baseline4larguras eregressões/reviewR3.

S3p: artigoscaixa/links/fieldsetCalendárioCSSlocal;valores/handlersmesmos;baseline4larguras,403PATCH ecomposiçãoReports/reviewR3.

S4a: reutilizar managementDestination e cabeçalho de subpágina; CSS local para ações. Validar build, tipos, lint e suites de entrada, editor e navegação com fixture determinística.

S4b: CSS module local para cabeçalho e seleção; preservar componente cliente e handlers. Teste focalizado de entrada e regressão de navegação.

S4c: classes locais e regiões sem alterar expressões/handlers; validar listas e entrada com fixtures interceptadas.

S4d: fieldset e CSS local; sem alterações de lógica. Validar três rascunhos, build/tipos e regressões entrada/listas.

S4e: prop opcional de layout no componente compartilhado, ativado apenas na Gerência; classes locais sem alterar handlers. Testar comandos interceptados403 e regressões do editor.

FechamentoS5: estender destinos do helper de retorno existente e encapsular links do Cardápio/retorno em componentes locais. Testar foco/visibilidade sem gravações de API. Não alterar auth/financeiro.

## Fechamento local em 2026-10-20
S1–S4 implementados em recortes documentados; S5 composto e retorno de foco corrigido. [Matriz final](s5-closeout-evidence.md). Não há novo recorte visual planejado. Próximo trabalho: validações manuais/integração e correções de achados reais, com escopo próprio. Preservar patches locais sem commit/push autorizados, pendências de lint/global e review autenticado. Não reabrir o redesign por checkboxes históricos que incluem gates de aceite.

Manutenção catálogo: substituir loader inicial usado somente pelo efeito por assinatura assíncrona da consulta com cleanup local. Sem tocar select/command/save/availability. Regressão de transporte antes da correção.

Manutenção Impressoras: consulta local readPrinting + aplicador estável, efeito com callbacks e cleanup; reload de mutações preservado. Baseline de filtro tardio antes do código.

Setup: readSetup+applyResources estável por canManage, efeito só confirma respostas assíncronas atuais. Fresh derivado do contexto confirmado; load manual preserva limpeza e gate. Revisão independente por envolver dados/equipe.

Preços: readPricing puro, aplicador estável, efeito com callbacks/cleanup. load de ações mantém propagação de erro/fluxo existente; não alterar perform. Revisão independente e testes interceptados.

Estornos: readRefundResources puro, aplicador estável e efeito assíncrono com cleanup. load continua setLoading/try/catch/finally em recargas após intent. Não alterar submit/selectTab/reauth/journal. Validar manual-refund-intent e correção sem devolução.

Clientes: readHouseResources puro + aplicador estável; seleção por selectedId e lookup na lista atual. Clear de seleção no callback canônico evita efeito de sincronização e evita reaparecimento automático. Não alterar approve/intent/action/reauth ou API. Revisão independente obrigatória.

Catálogo rápido: iniciar estado de busca nos handlers existentes, efeito apenas consulta debounce/abort. Não alterar API/payload/seleção ou permissões.

### Consulta de pessoas — manutenção global
Extrair leitor canônico sem setters, manter callbacks estáveis para sucesso/erro e usar Promise callbacks com cleanup na consulta inicial. Validar lint, tipos, build e teste visual de ausência no popup; registrar limite de cobertura por o componente não ter callsite ativo.

### Manutenção global — leitura da equipe,2026-10-21
Extrair readStaffMembers e callbacks estáveis. Estado de acesso observado invalida freshness quando allowed muda sem remontar nem limpar intenção. Efeito inicial usa callbacks/cleanup; load manual conserva invalidação antes da leitura. Rodar testes DEV existentes e falha inicial/sem permissão.

### Manutenção global — quantidade de remoção,2026-10-21
Substituir efeito de clamp por reconciliação condicional do próprio estado em render (só quando editável e valor divergir). Testar no fluxo atual Mesas→comanda→conta; evitar modificar helpers legados nesta slice.

### Manutenção global — relógio da estação,2026-10-21
Mover setNow inicial para callbacks assíncronos de snapshot/recovery, mantendo intervalo e cleanup. Validar relógio com tempo fixo emBar/Cozinha, idades e ausência de comandos, mais regressão de lote.

### Manutenção global — leitura de ajustes,2026-10-21
Extrair leitor assíncrono e aplicador estável. Efeito inicial usa Promise callbacks/cleanup e manual continua usando mesmo caminho. Não mudar fórmulas, POST ou storagekey.

### Manutenção global — consulta de sessão,2026-10-21
Compartilhar aplicador de resposta e falha entre leitura inicial e loadSession manual. Inicial não precisa repetir loadingtrue/errornull já definidos por useState. Ignorar callbacks iniciais após cleanup. Testes de UI, auth e tenant mais revisão independente.

### Manutenção global — rollout das mesas,2026-10-21
Extrair readPolicy sem setters. Capturar storage sem setters no efeito e aplicar em callbacks de consulta/cleanup. Refresh manual mantém caminho e POST intactos. Testes interceptados de replay/reload, storage corrompido e GETfalho mais regressões setup.

### Manutenção global — bootstrap do cliente,2026-10-21
Extrair leitor sem setters e aplicador compartilhado; inicial Promise callbacks/cleanup, retry manual conserva loading. Reconciliação condicional do próprio estado limpa receipt em troca de token/Tab. Executar suítes guest e reviewindependenteR3.

### Validação integrada — executor Windows,2026-10-21
Adicionar backendWindowsmsvcrt combyte0,contençãoretry apenasEACCES/EAGAIN/EDEADLK;liberarfinally. UIDnamespaceportátil. Rodar unittests de bloqueio/retry e integração focada exclusivamente em banco descartável allowlisted;não usarDBdeinspeção.
