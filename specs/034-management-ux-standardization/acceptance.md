# Aceite — Spec 034

**Estado original do planejamento:** NOT_RUN. Evidências incrementais de S1a/S1b
estão nos relatórios próprios; nenhum aceite global é declarado por esta tabela.
Fixtures controladas são evidência visual, não prova de integração/produção.

Rodada composta S1 de20/10:112 testes focados PASS; build/tipos/auth/tenant PASS.
Lint dos módulos existentes e suíte ampla FAIL; gatesR3/integração/aceite humano
pendentes. [Evidência composta e limites](composed-s1-evidence.md). Nenhum AC global
é fechado somente pelos casos automatizados desta composição.

S1b cobre cabeçalho/retorno nas quatro rotas de configuração; AC03 tem evidência
de foco e navegação, mas não aprovação de todos os bloqueios/recovery dos módulos.

| ID | Critério verificável | Evidência exigida na implementação |
| --- | --- | --- |
| AC01 | Cinco áreas e aliases existentes continuam abrindo o destino correto; recarregar, Back/Forward e link direto mantêm título/seleção coerentes | Regressão de navegação e percurso real |
| AC02 | Gestão conserva setup, clientes, alertas, impressoras e sessão; cada linha tem um único link, título compreensível e descrição específica quando útil | Inspeção de destinos, screenshot e teclado |
| AC03 | Abrir/voltar de configuração restaura área e foco na origem; confirmação bloqueante mantém contexto e impede saída indevida | Percurso positivo e negativo por rota tocada |
| AC04 | Layout usa tokens/primitives existentes e CSS gerencial escopado; ícones/tipos/raios/ritmo coerentes com uma superfície adjacente | Diff de estilos, inventário e comparação visual |
| AC05 | Ações utilitárias identificáveis e secundárias; status de rede não muda por estética nem some quando há risco | Nome acessível, leitura/reconexão/erro e captura |
| AC06 | Agora preserva alertas críticos e ação contextual antes de resumos; Operação mantém destinos e distingue informação indisponível de zero | Fixture com exceções, volume alto e erro parcial |
| AC07 | Financeiro preserva centavos, saldo, calendário, estados, permissões, reauth e recuperação; navegar não emite comando nem cria pagamento | Negativos e, se tocado fluxo financeiro, integração Django/PostgreSQL + review R3 |
| AC08 | Cardápio mantém criação única e edição existente, seleção/busca/draft e proteção contra polling; navegar não grava produto | Regressões editor/QuickCatalog e erro/busy |
| AC09 | Cada rota tocada cobre loading/vazio/erro/stale/revogação; mutações cobrem pending/timeout/readback sem segundo envio acidental | Matriz por rota e testes pertinentes, sem asserts enfraquecidos |
| AC10 | 360/390/430/1280 e zoom/fonte200% sem ação cortada/encoberta, scroll horizontal ou alvo <44px; foco e leitura lógica, ícones nomeados | Pixels e hit areas, teclado, axe e leitor de tela; limites manuais explícitos |
| AC11 | Comparação antes/depois usa mesmo fixture/estado/papel/viewport; testes focados, typecheck/build/lint e test:visual executados | Manifest por SHA, logs sanitizados e falhas históricas preservadas |
| AC12 | Cada slice tem diff restrito, review proporcional e evidência por critério; reversão da UI não muda dados; sem claim de ganho/produção não medido | Checklist de PR, estratégia de rollback e decisão qualificada |

## Aceite humano de UX

S1j: consultasGET de inspeção/busca/visitas/políticas não exibem confirmação de
mutação; PATCH autorizado conserva reauth/payload/feedback/PIN. Resultados com
ações legíveis em quatro larguras/zoom200%. Review local não substitui integração
financeira, duas Venues, resposta perdida ou gateR3 autenticado no SHA final.

S1i: grupos Buscar cliente/Cadastro e relacionamento, labels/ordem preservados,
comando de cadastro e erro200/403 por fixtures, busca somenteGET, quatro larguras/
zoom/axe. Review localR3 não substitui integração financeira/PII/tenant ou gate
autenticado no SHA final. Não aprovar todo o módulo de Clientes por este recorte.

S1h: apresentação de equipe em dois grupos nomeados, seleção/estado atual e aviso
preservados; testes de layout e negativos simulados não comprovam autorização
servidora/tenant. Review independente local exigido pelo contexto de acesso;
gateR3 autenticado/CI e integração real não são substituídos por fixtures.

S1g: parte AC04/09/10/11, listas de recursos somente quando confirmadas, vazio
por tipo, criação agrupada e estados/ordem/draft/gates existentes conservados.
Quatro larguras/zoom/axe, transição local mesa→zona e refresh, regressão setup
existente; não equivale a homologar permissões, QR ou banco real.

S1f: parte AC04/09/10/11 coberta por trabalhos incerto/falha/impresso, estado e
erro não recolhidos, documento correto, comandos condicionais e motivo preservados,
quatro larguras/zoom/axe e POSTs interceptados com erro. Não equivale a ensaio físico,
review de recovery ou integração real de reimpressão.

S1e: AC04/09/10/11 parcialmente cobertos pela lista de destinos com nomes longos,
articles nomeados e h3, estados/bridge/estações preservados, edição local por
destino sem POST, quatro larguras/zoom200%/axe e comparação determinística.

S1d: AC04/09/10/11/12 parcialmente cobertos por grupos nomeados de destino,
campos/condicionais/ordem de foco preservados, nenhuma escrita ao editar localmente,
payload/busy/erro200/403 simulados e antes/depois com fixture constante nas quatro
larguras. Pareamento, impressão física e recuperação não são aprovados pelo recorte.

S1c: AC04/09/10/11/12 exigem grupos Produção/Pagamento/Atendimento nomeados,
cinco campos numéricos com unidade/limites preservados, confirmação separada,
draft conservado em refresh e payload/409/erro/busy existentes em fixture.
Comparação usa a mesma política versão1 (300/600/300/120/300 segundos) em
360/390/430/1280px. Integração real e leitor de tela manual não são inferidos.

Após S1, percorrer encontrar impressoras, configurar alerta e retornar à Gestão.
Após S2–S4, percorrer abrir uma exceção, localizar revisão de fechamento e editar
um produto. Usar ambiente descartável para qualquer gravação. Registrar resultado,
obstáculos e opinião do avaliador sem publicar identidade/dados pessoais.
Tempo e número de ações só serão comparados se medidos no mesmo cenário.
Aceite visual não é homologação financeira, de hardware ou de estabelecimento.

### S2a — resumo e acessos rápidos de Agora

Recorte visual: manter alertas/exceções antes do pulso, os mesmos valores confirmados e os mesmos destinos. Nomear a região do resumo e a navegação de acessos rápidos; empilhar indicadores e atalhos no celular, expandindo em duas colunas a partir de768px. Detalhes adicionais permanecem expansíveis por teclado. Não alterar carregamento, cache, autorização, ciência de alerta ou cálculo monetário. Loading/erro sem snapshot continuam sem resumo; estado antigo continua identificado pelo aviso existente. Aceite: quatro larguras360/390/430/1280, fonte200%, axe, alvo44px, teclado, destinos e nenhuma escrita ao consultar/expandir.

### S2b — produção e entregas em Operação

Gerente consulta contadores existentes de Bar/Cozinha/prontos e abre detalhes por teclado; atalhos levam às estações existentes. Região nomeada Produção e entrega, contadores agrupados, entregas como lista com destino/produto/idade preservados; nomes longos quebram, idades legíveis; vazio explícito apenas sob snapshot existente. Estado antigo conserva aviso global; erro inicial/sem permissão não produz zeros. Sem novos endpoints, paginação, ordenação, estados, comandos ou cálculo; Salão fica para próximo recorte. Aceite:360/390/430/1280,8entregas/nomes longos/sem destino, lista expansível, axe, teclado, alvos44px, ampliaçãoCSS200% local, nenhuma escrita e regressões de navegação/Agora. Zoom nativo e leitor de tela permanecem aceite manual.

### S2c — Salão e itens indisponíveis

RecorteR2 visual. Região Salão nomeada, mesmos contadores de ocupadas/limpeza e quatro destinos existentes, agrupamento Surface2 e atalhos em uma coluna mobile/duas desktop. Itens indisponíveis permanecem expansíveis, com mesma condição/filtro e nomes completos em lista semântica. Não alterar APIs, cache, permissões, cálculo, eventos ou comandos. Vazio confirmado conserva zeros no Salão e ausência do bloco indisponíveis; erro inicial não mostra resumo; snapshot antigo mantém aviso existente. Aceite360/390/430/1280 com12nomes longos, teclado/foco, alvos44px, axe/overflow/CSSzoom2 local e nenhuma escrita; regressõesS2a/S2b/navegação. Zoom nativo/leitor de tela/aceite humano pendentes.

### S3a — entrada Financeiro

Recorte de apresentação dos três grupos existentes e cinco destinos: caixa/turnos, fechamento, correções/estornos, serviço/descontos/aprovações e relatórios. Reutilizar padrão de destino descritivo de Gestão, nomes acessíveis preservados e descrições curtas. Nomear regiões e melhorar quebra dos resumos de caixas no mobile. Preservar literalmente seleção de caixas ativos, valores, fallback Ver caixa, mensagens, estados e destinos. Sem comandos novos, indicadores, autorização, cache, API ou cálculo. Não confundir contagem com pagamento confirmado. Loading/erro inicial não mostra totais; vazio e snapshot antigo conservam contrato atual. Aceite360/390/430/1280 com caixaOPEN/COUNTING/zero/valor ausente, nomes longos, cinco destinos, teclado/axe/alvos44px/CSSzoom2 e nenhuma escrita; regressões de navegação/Operação/Agora. R3 conservador por apresentação financeira, revisão independente obrigatória; integração real/gate autenticado e aceite humano permanecem pendentes.

Sessão encerrada em/manage: Entrar novamente aponta /staff, é operável por teclado e só aparece no estado de revogação existente; não executar login ou alterar sessão automaticamente.

Aviso de sessão refinado: tema Rodada, ação56px sem sublinhado, mobile/desktop e nomes acessíveis; contrato de revogação e destino /staff intactos.

### S3b — fechamento diário, cabeçalho e dia operacional

Recorte visual R3 conservador: retorno explícito Voltar ao Financeiro (/manage#financeiro), título/descrição existentes, região Dia operacional e fieldset Selecionar dia. Campo e ações empilhados no mobile/duas colunas desktop, tokens existentes. Preservar literalmente data vinda do calendário da API, onChange, load(day), generate(), condições de loading/busy/permissão/reauth, mensagens e idempotência. Não tocar revisões, bloqueios, propostas ou PIN. Aceite: baseline e depois360/390/430/1280, teclado/alvos44px/axe/CSSzoom2, consultaGET do dia escolhido sem writes; regressões existentes de fechamento/PIN e review independente. Integração real e aceite manual continuam pendentes.

### S3c — revisão imutável e bloqueios

RecorteR3 de apresentação: região Revisões imutáveis nomeada; resumo financeiro agrupado sem alterar quatro valores/cálculos; métodos/caixas/bloqueios com separadores e lista semântica de bloqueios sempre visível. Preservar ordem/status/fallback/versão/fingerprint e links exatos dos turnos. Histórico e nomes longos não podem alargar a tela. Não alterar form/handler de revisão, permissões, mensagens, PIN, geração, cache ou propostas. Aceite4larguras, quatro valores distintos, caixa longo, bloqueiosCASH_SHIFT eUNRESOLVED_PAYMENT, ausência de confirmar emINCOMPLETE, alvo44px no turno, axe/CSSzoom2 e nenhuma escrita; regressões dePIN/rascunhos e review independente. Aceite humano/zoom nativo/integração real pendentes.

### S3d — solicitação de correção depois do fechamento

Somente formulário existente: fieldset Solicitar ajuste de caixa, três campos agrupados e ação separada; controlesSurface2/tokens existentes etextarea legível, mobile/desktop. Preservar labels, IDs, valores,onChange,canRequest,disabled,propose,parseSignedCents,idempotência/PIN e readback. Não alterar lista/decisão de propostas. Aceite4larguras/nomes/axe/CSSzoom2/teclado, payload-1000centavos/403 comrascunho preservado e sem sucesso; regressõesPIN/solicitação própria. R3 exige revisão independente. Sem escrita real; integração e aceite humano pendentes.

### S3e — lista e decisão das propostas

Recorte visualR3: propostas em artigos nomeados pelo caixa, cabeçalho/valor/estado textual e metadados separados; campo de motivo e ações agrupados. Pendente/aprovada/rejeitada continuam labels existentes, mesma ordem/condições, sem cor como única informação. Preservar integralmente valores/reason/date/decision/movement, autoria própria,canReview,disabled,decisionReasons,decide ePIN. Sem novos comandos ou persistência. Aceite4larguras, quatro propostas incluindo própria/aprovada/rejeitada, nomes longos/axe/CSSzoom2/alvos44px e nenhuma escrita ao editar; regressãoPIN/autoria/rascunhos emdaily-close.spec.ts. Revisão independente obrigatória; real/manual pendente.

### S3f — PIN e composição do fechamento

Somente apresentação do painel existente de reautenticação: região nomeada Confirmar PIN do gerente, fieldset Confirmar identidade, controles/ações agrupados emCSSlocal. Não alterar pendingAction,pin,busy,reauthenticate,cancelamento,replay,chaveoriginal ou autenticação. Máscara/inputMode/autocomplete preservados. Aceite4larguras/axe/CSSzoom2, PIN vazio desabilita confirmação, gerar revisão bloqueado enquanto aguarda, Cancelar por teclado remove painel sem reenviar comando, regressõesPIN/replay/rascunhos no teste existente. Capturas sem PINdigitado. Composição conjunta dos recortes locais e revisão independenteR3; integração real e aceite humano permanecem pendentes.

### S3g — entrada de Estornos

Cabeçalho/retornoFinanceiro, fieldset Confirmar identidade com label visívelPINdo gerente, regiãoComanda e label visível no seletor. Mesmo títuloEstornos, handlers/valores/condições/seleção/reauth/PIN/intentjournal eworkspaceLock. Sem modificar pagamento/reembolso/recuperação. CSSModule local somente dois blocos; botões/inputs44px, estados existentes preservados. Aceitebaseline4larguras,axe/CSSzoom2,nenhumwrite aoconsultar e regressõesmanual-refund-intent/correction-without-refund/refund-labels. R3review independente; real/manualpendente.

### S3h — resumo e histórico do pagamento em Estornos

Somente apresentação: regiãoConsultar pagamento distinta do labelPagamento elegível, label visível para seleção, grupoSaldo do pagamento com três valores existentes e histórico em lista com título. Mesmas expressões,status,labelsfallback,ordem e valores; nenhuma mudança de handlers,disabled,locks,formulário oujournal/recovery. Não criar confirmação para leitura. Aceite4larguras,12/5/7distintos e10/10/0 emestornado, histórico com motivo longo,axe/CSSzoom2/nowrites e regressões existentes. R3review independente;real/manualpendentes.

### S3i — formulário de estorno/caixa

Fieldset Preparar estorno e labelsvisíveis para valor/motivo/caixa e correçãoopcional, comIDsassociados. Mesmos aria-labels/valores/onChange/condições/disabled/handlerrefund, journal e regras de correçãoexata. Não alterar PIN, readback ou recuperação. Labels distintos do nome dofieldset/região. CSS local mobile com alvo mínimo44px e tokens existentes. Aceite4larguras/axe/CSSzoom2,payload500centavos/caixa e403preservandorascunho; regressõescorreçãoexata/PIN/replay/storage. R3review independente,real/manualpendentes.

### S3j — aviso de estorno pendente e composição

Recorte exclusivamente visual: painel pendente ganha headingEstorno pendente/íconewarning, bordaâmbar e ação descritiva existente com largura disponível. Preservar parágrafos, pending/amount, onClick submitsemnovoargumento, busy/reviewLocked/disabled e workspacebloqueado. Nenhuma alteração emintent/storage/chaves/replay/readback. Não comunicar sucesso antes de confirmação. Aceite4larguras/axe/CSSzoom2/teclado e duas respostasperdidascom payloadidêntico, camposcontinuambloqueados; composiçãoS3g–S3j/regressõesfinanceiras/reviewR3. Real/manualpendentes.

### S3k — política de preços e serviço

Cabeçalho com retornoFinanceiro; fieldset Regras de cobrança com campos existentes/ordem/rótulos preservados e fieldset Confirmar alteração paraPIN/salvar. Grade móveluma/desktopduascolunas e checkbox44px comtokens existentes. Não alterar labels, policy,conversão basispoints,perform/reauth,versão,disabled ou endpoints. Solicitações de ajuste fora do recorte. Aceite4larguras,estadoinicial10%,edição12.5→1250centésimospercentuais,PUTexpected_version3/payloadinalterado,403sem sucesso ePINnão capturado emimagem,axe/CSSzoom2,regressõesadjacentes e revisãoR3. Real/manualpendentes.

### S3l — solicitações de ajuste

RegiãoSolicitações de ajuste nomeada; artigos nomeados pela comanda(fallbackexistente), metadados e valoresAntes/Depois separados e ação44px. Preservar requester/command/reason,preview cents/100.toFixed2 e nomes existentes, ordem,performurl/body{},PIN,busy/disabled,load e vazio. Sem novo cálculo/tradução ou comandos. Aceite4larguras/longos/fallback,110.00→99.00 distintos,semPINdesabilita,403apósreauthsemfalsosucesso/PINlimpo,axe/CSSzoom2 e regressõespricing/policy/Financeiro. Capturas semPINdigitado. R3reviewindependente;real/manualpendentes.

### S3m — cabeçalho e período dos relatórios

RetornoFinanceiro comícone,períodoregiãonomeada/fieldsetSelecionar período e gradeDatasDe/Até/ações. PreservarcalendáriovindoAPI,fuso/corte/limite366dias,required/start/end/onChange,onSubmitload,disabledAplicar/CSV eexpôrúltimorelatórioem erro. Nenhuma alteração emtotais/CSV/saveCalendar/URLs/dados. Aceitebaseline4larguras,dataAPI,GETperíodoescolhido,403comresultadopreservado/CSVbloqueado,axe/CSSzoom2/datascompletas/teclado/nowrites e reviewR3. Integração real/manualpendentes.

### S3n — resumo financeiro dos relatórios

Separar visualmente No período eEstado atual, este somente keys current_open_exposure_cents/current_open_tabs jádocumentados como atuais. Todas demais métricas e fallbackdesconhecido permanecemvisíveis no período,mesmoslabels/formatação/valores; nãofiltrarperda/recalcular nemalterarCSV/consultas. RegiãoResumo financeiro nomeada,metadata/anterioraviso preservados,gradeuma coluna mobile/duasdesktop. Aceite4larguras,8métricasdistintas incluindo adicionaldesconhecida,2atuais/númerossemmoeda,axe/CSSzoom2/nowrites,regressõesperíodo eparityreports/reviewR3. Real/manualpendentes.

### S3o — resultados por dia e listas de relatórios

RegiãoPor dia operacional com artigosnomeados pelasdatas;produtos,métodos,pedidos emlistasnomeadas,semmudarordem/expressões/rótulos/fallback/vazios. CSSlocalmobile:nomesquebram/valoresmono separados;desktopalinha valores. Preservar paresajustes/estornos,valoreszero/negativos,históricoprodutos econtagens,report/consulta/CSV/calendárioinalterados. Não tocarfechamentoscaixa. Aceite4larguras,doisdiasincluindozero,valores100/85/-5/15,produtolongo,CASH/PIX,pedidoConfirmado/Cancelado,axe/CSSzoom2/nowrites,regressõesperíodo/resumo/parity e revisãoR3. Real/manualpendentes.

### S3p — fechamentos de caixa e calendário dos relatórios

RegiãoFechamentosdecaixa/artigosnomeadoscaixa+data,mesmosstatus/revisão eparesEsperadooriginal/corrigido,Contado/diferença,incluindoausente—/negativo. Linksmesmosdestinos comalvo44px. DetailsCalendáriocontinuarecolhido,fieldsetCalendário do estabelecimento parafuso/corte/ação. PreservaronChange,min/max,loading/disabled,PATCHbody,saveCalendar/aviso/load/CSV. Aceite4larguras,100/95/90/-10 eausentes,reviewpending/open,axe/CSSzoom2/links,403PATCHcorte5semfalsosucesso e composiçãoReports/reviewR3. Real/manualpendentes.

### S4a — entrada do Cardápio e ações de produtos

Recorte R2 de apresentação: dois destinos descritivos na aba Cardápio, retorno explícito ao Cardápio na página de produtos e ações adicionar/editar em grade responsiva. Preservar URLs, permissões, diálogos, polling, handlers e campos. Fora de escopo: variações, preços, disponibilidade e comandos. Aceite: quatro larguras, descrições acessíveis, retorno à aba, ação única de adicionar, abertura/Escape/foco do editor, CSS zoom 200% e nenhuma escrita no percurso de inspeção.

### S4b — entrada de variações e adicionais

Recorte R2: alinhar cabeçalho e retorno ao Cardápio, manter aviso sobre centavos e histórico, agrupar seleção de produto com instrução acessível. Preservar select, opções, onChange, disabled, mensagens e todos os comandos/formulários. Fora de escopo: listas, formulários, preços e disponibilidade. Aceite: baseline e depois em 360/390/430/1280, axe/layout, CSS zoom 200%, destinos preservados e inspeção sem escrita.

### S4c — listas de variações e grupos

Recorte R2 de apresentação: regiões nomeadas Variações e Grupos de opções, linhas responsivas com nomes e valores legíveis e ações44px. Preservar ordem, formatação monetária, flags Padrão/Desativada/Desativado, intervalos, botões, handlers, payloads e disabled. Não alterar formulários, associação/desassociação nem disponibilidade. Aceite: fixture selecionada com nomes longos, valores1250/250 e flags; antes/depois360/390/430/1280; axe/layout e CSSzoom200%; editar cada tipo abre rascunho correto e cancelar sem escrita.

### S4d — formulários de configuração

Recorte R2 de apresentação: formulário nomeado pelo título, campos agrupados em fieldset e ações responsivas com alvos44px, checkbox com área confortável. Preservar todos os labels, tipos, limites, required, valores, disabled, handlers, payloads e mensagens; sem alterar persistência ou preços. Aceite: três tipos em360/390/430/1280, antes/depois, axe/layout/CSSzoom200%, rascunhos preservados, regras de Máximo/priority e cancelar sem escrita. Fora de escopo: disponibilidade e mudanças de contrato.

### S4e — disponibilidade na Gerência

Recorte R2 de apresentação, opt-in somente no editor da Gerência: seção nomeada, linhas responsivas e alvos44px, nomes longos com quebra. Preservar labels, disponibilidade, pending, POST/state/expected_version, readback e mensagens; Bar/Cozinha mantêm layout anterior. Aceite: baseline/depois360/390/430/1280, axe/layout/CSSzoom200%, ações opostas com versões preservadas, pending desabilita ambas,403 mantém estado e relê dados. Nenhum comando real. Fora de escopo: recuperação/replay, API e alterações de regra.

### S5 — composição automatizada de 2026-10-20
Revisão das cinco abas e39arquivos de Gerência:244PASS/1FAIL entre245casos. Falha de expectativa antiga no teste de sessão corrigida,21history/session-login PASS no rerun;produto não alterado. Build/tipos/auth4/tenant10 PASS;lint7erros herdados FAIL. [Relatório e limites](s5-review-evidence.md). AC01–12 mantêm cobertura parcial: testes de fixture/review local não substituem integração real,manual ou gateR3 autenticado. Próxima etapa confirma foco Cardápio e consolida matriz final.

### S5 — fechamento do retorno ao Cardápio

AC03 inclui produtos e variações: ao voltar, manter aba Cardápio e focar o destino correspondente, visível acima da navegação; reutilizar armazenamento de contexto existente, sem conteúdo de catálogo ou credenciais. Links diretos criam origem padrão; storage bloqueado mantém navegação sem prometer foco. Cliques modificados não alteram contexto da aba original. Preservar URLs/aliases e handlers de domínio. Aceite: regressão falha antes, quatro larguras/dois destinos, links diretos e storage indisponível; composição de navegação/Gestão/editor permanece válida.

### Fechamento local e matriz final — 2026-10-20
[Fechamento e limites por AC](s5-closeout-evidence.md). Retorno/foco de produtos/customizações corrigido após teste falhar antes.54regressões PASS no candidato final;build/tipos/lint focado PASS;review local NO_FINDINGS_WITH_GAPS. Implementação visual planejada entregue localmente. Aceite global continua parcial:manual/integração real/gateR3 autenticado/CI final pendentes e falhas herdadas explícitas. Não equivale a GO de release/piloto.

### Manutenção pós-fechamento — consulta inicial do catálogo

Eliminar a ocorrência herdada de set-state-in-effect no editor de variações sem adiar setters artificialmente nem suprimir regra. Efeito faz consulta externa e atualiza estado no retorno assíncrono; desmontagem ignora resposta tardia. Manter URL include_inactive=true, mensagens da API e formulários/comandos. Falha de transporte deve exibir erro sem rejeição não tratada nem formulário gravável. Aceite: lint do componente PASS, erro500 e falha de rede sem escrita/pageerror, regressões de seleção/editor e build/tipos. Outros6erros de lint fora deste recorte.

### Manutenção pós-fechamento — leituras de Impressoras

Remover a ocorrência herdada de set-state-in-effect sem timers artificiais ou supressão. Separar consulta de aplicação dos resultados: efeito assina retorno assíncrono; manter GETs/filtros/paginação, intervalo5s, mensagens e load após comandos. Cleanup invalida resultados da assinatura anterior quando filtro/página muda ou tela desmonta, impedindo lista antiga de substituir filtro atual. Sem alteração de mutações/idempotência/copyIntent. Aceite: regressão tardia falha antes, polling5s/falha de transporte/parada após saída, build/tipos/lint e regressões de destinos/trabalhos/comandos interceptados. Outros5erros fora do recorte.

### Manutenção pós-fechamento — leitura inicial de Setup

Remover ocorrência herdada de set-state-in-effect no carregamento inicial sem supressão ou adiamento artificial. Separar consulta dos recursos/aplicação dos resultados e assinar consulta no efeito com cleanup. Manter GETs de mesas/zonas e consulta de vínculos somente quando canManage, mensagens e reload manual/pós-comando. Fresh só vale para o contexto canManage confirmado, impedindo uso de resposta anterior quando capacidade muda. Preservar envio/reauth/PIN/versões/uncertainCreate/sending e load(false) que conserva erro de mutação. Aceite: lint/build/tipos e regressões de setup/equipe, rede503/transport, recarga bloqueia escrita e preserva rascunho, consultas sem staff.manage não pedem vínculos. Outros4erros de lint fora do recorte.

### Manutenção pós-fechamento — consulta inicial de Preços e serviço

Remover lint herdado sem supressão/timer artificial, separando os GETs e aplicação de resposta. Efeito assina consulta assíncrona e ignora conclusão após desmontagem. Preservar URL, resultados parciais, cálculo em basis points/centavos, PIN/reauth/versões, comandos e load manual/pós-comando. Falha de transporte inicial deve ser exibida sem pageerror nem autorização para salvar política ausente. Aceite: regressão network falha antes,503 com mensagem da API, save sem política bloqueado mesmo com PIN, nenhuma escrita nas consultas, regressões positivas/negativas de política e aprovação, build/tipos/lint e review independente. Demais3erros fora deste recorte.

### Manutenção pós-fechamento — consulta inicial de Estornos

Remover erro herdado de set-state-in-effect sem supressão/timer artificial. Separar GETs de comandas/caixas e aplicação de resultados; efeito mantém loading inicial true até resolução, trata erro como antes e ignora conclusão após desmontagem. Preservar resultados parciais, caixas com turno aberto e escolha válida, load pós-intent, saldo/centavos, PIN/reauth e useManualRefundIntent/locks/IDs/payloads. Aceite: lint/build/tipos, consulta atrasada/erro/rede/filtrocaixas sem POST, regressões positivas/negativas de estorno e replay/readback interceptado, review independente. Outros2erros de lint fora do recorte.

### Manutenção pós-fechamento — carregamento e seleção de Clientes

Eliminar os dois set-state-in-effect herdados sem supressão ou timers artificiais. Separar GET de sessão e paginação de comandas da aplicação dos dados; efeito inicial assina consulta/cleanup e mantém polling15s, visibility e eventos online/focus/offline. Manter seleção por ID, derivando snapshot da lista canônica; atualizar ID na aplicação dos dados e limpá-lo quando comanda desaparece, sem reassociação automática se reaparecer. Preservar contexto venue/staff/session, limpeza de PIN/histórico/clientes/visitas e intent quando ator muda, comportamento stale/loading/erro, autorização/reauth, idempotency_key/payload/expires e todos comandos. Aceite: lint/build/tipos, seleção atualizada/remove/reaparece, intenção ambígua preservada no refresh e retry com mesmo payload, troca de ator sem seleção antiga, falha de leitura sem escrita, regressões de Clientes e review independente. Não declarar toda corrida herdada resolvida.

### Manutenção dos erros de lint acompanhados — conclusão local
Em20/10, os sete erros originalmente registrados nos módulos da Gerência foram corrigidos em recortes documentados. Inventário final16arquivos:0erros/0avisos; não equivale a lint global. [Último recorte e limites](customer-read-evidence.md). Critérios globais e aceite humano permanecem parciais; testes de fixture/review local não substituem integração real nem reviewR3 autenticado.

### Manutenção global — debounce do Catálogo rápido

Remover set-state-in-effect herdado do início da busca, sem suprimir lint nem criar adiamento artificial. Reset de searching/searchOk/active pertence aos eventos que iniciam nova busca: abrir painel fechado, editar nome e voltar da criação. Preservar debounce180ms/AbortController, não reiniciar ao clicar no acionador de painel já aberto, esconder opções anteriores durante busca e impedir criação antes de resposta confirmada. Manter permissões, estações, preços/centavos e POST resolve-or-create. Aceite: lint/build/tipos, abrir/reabrir/voltar, digitação rápida/abort e regressões de criação/edição.

### Consulta de pessoas — manutenção global
- Lint do componente sem set-state-in-effect; tipos/build passam.
- Leitura inicial aplica sucesso/erro somente enquanto ativa; consulta manual e409 reutilizam o mesmo leitor.
- Nenhuma alteração no POST, payload pendente, chave ou markup; popup de mesas continua sem controle e sem requests party-size.

### Manutenção global — leitura da equipe,2026-10-21
Administrar equipe: lint sem set-state-in-effect; sucesso/erro inicial e retry manual funcionam; sem staff.manage não consultar lista; criação ambígua preserva payload/chave e bloqueia edição. Build/tipos e regressões DEV passam.

### Manutenção global — quantidade de remoção,2026-10-21
Remoção: lint sem set-state-in-effect; resposta perdida preserva quantidade/payload/chave e locks; após rejeição resolvida e refresh com quantidade menor, escolha é limitada antes de novo envio. Modal/acessibilidade permanecem.

### Manutenção global — relógio da estação,2026-10-21
Sem set-state-in-effect no relógio de ProductionBoard; idade correta já no primeiro snapshot, atualização em15s, timestamp ausente/inválido explícito. Não gerar POST automaticamente.

### Manutenção global — leitura de ajustes,2026-10-21
Lint sem set-state-in-effect; consulta lenta mantém preview desabilitado; recuperação de intenção mantém payload/chave; build/tipos e testes focados passam.

### Manutenção global — consulta de sessão,2026-10-21
Lint sem set-state-in-effect; leitura inicial pendente não expõe sessão/login; sucesso mostra sessão e401/403 mostra login; transporte mostra erro explícito. Comandos e renovação existentes intactos.

### Manutenção global — rollout das mesas,2026-10-21
Sem set-state-in-effect; recuperação preserva mesma alteração após resposta perdida/reload, storage corrompido bloqueia POST e consulta falha não habilita botão. Não alterar canConfigure ou comandos.

### Manutenção global — bootstrap do cliente,2026-10-21
Lint global sem erros após correção; recuperação de pedido não cria sessão nova, replay mantém chave/payload; QRrevogado e carrinho/permissões preservados; navegação/quantidades/repeat/receipt regressões passam.

### Composição final local —2026-10-21
Validação conjunta local:296casosPASS/0falhas/7,3min em uma execução completa. Não equivale a integração real,CI,homologação manual ou reviewautenticado. Ver relatório para seleção/gaps.
[Evidência](composed-final-evidence.md).

### Validação integrada — executor Windows,2026-10-21
Módulo guard importa em Windows; leitor aguarda reset de outro processo e liberação ocorre após exceção; erro de lock não reconhecido falha fechado. Restrições de banco/host e retrySQLSTATE intactas. Revisão independenteR3 antes de recomendações.
