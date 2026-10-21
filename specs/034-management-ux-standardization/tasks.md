# Tarefas — Spec 034

Documento publicado não significa implementação. Itens de produto só fecham com
evidência da composição testada e ligação ao [aceite](acceptance.md).

## S0 — Baseline

- [x] S0.1 Conferir main, PRs concorrentes, ownership e o inventário de rotas (baseline de S1a).
- [x] S0.2 Capturar cinco áreas e página tocada em fixture isolada, com SHA (S1a: somente entrada Gestão).
- [ ] S0.3 Inventariar tokens/primitives, CSS compartilhado, capacidades e estados.
- [ ] S0.4 Registrar composição proposta para Gestão, tarefas de avaliação e decisão.

## S1 — Gestão

S1a cobre entrada; S1b cobre cabeçalhos/retorno/foco; S1c–S1j cobrem recortes de
Alertas/Impressoras/Setup/Clientes. Evidências próprias não fecham a etapa inteira. Demais recortes,
composição, gatesR3 e aceite com operador permanecem pendentes.

- [x] S1.1 Implementar hierarquia/header/utilitários e linha de navegação reutilizável quando necessário (S1a, composição automatizada20/10).
- [x] S1.2 Preservar todos os destinos, labels acessíveis e contexto de retorno (S1a/S1b, composição automatizada20/10; não é aceite de operador).
- [ ] S1.3 Harmonizar setup/clientes/alertas/impressoras em sub-slices separadas após baseline; não redesenhar sessão compartilhada.
- [ ] S1.4 Validar estados, foco/teclado, zoom200%, quatro larguras e antes/depois.

### Slice S1j — resultados/feedback de Clientes

- [x] Reproduzir confirmação indevida apósGET em teste antes do código.
- [x] Separar feedback das quatro consultas, mantendo default das mutações.
- [x] Reflow de resultados e regressõesGET/PATCH/reauth/PIN, com antes/depois.
- [x] Revisão independente local de diff e pixels.
- [ ] GateR3 autenticado/integrado e aceite humano; não fechar Clientes/S1 global.

### Slice S1i — busca e cadastro de clientes

- [x] Baseline em quatro larguras e grupos de busca/cadastro sem alterar handlers.
- [x] Corrigir reflow200% e validar busca/cadastro/negativos/limite somente leitura.
- [x] Review independente local de fonte e capturas, sem aprovação GitHub.
- [ ] Aceite humano, integração real e gateR3 autenticado no SHA final.

### Slice S1h — apresentação da equipe existente

- [x] Baseline em quatro larguras, dois grupos nomeados e aviso preservado.
- [x] Testes200/403/409, reauth recusada, sem capability, busy/PIN/versão.
- [ ] GateR3 autenticado/CI e integração real no SHA final; sem recomendação merge.
- [ ] Aceite humano/leitor de tela e zoom nativo.

### Slice S1g — Mesas e zonas em Setup

- [x] Baseline com recursos de nomes longos em quatro larguras.
- [x] Listas nomeadas e cadastro agrupado sem alterar lógica/gates/equipe.
- [x] Quatro larguras/axe/teclado/zoom, estados e regressão existente de Setup.
- [ ] Aceite humano, leitor de tela e integração real de escrita.

### Slice S1f — trabalhos de impressão

- [x] Baseline com estado incerto/falha/impresso em quatro larguras.
- [x] Hierarquia de estado/erro/tentativas e ações, sem mudar condições/comandos.
- [x] Validar axe/zoom/alvos e comandos interceptados com erro403.
- [ ] Aceite humano, leitor de tela e impressão física.

### Slice S1e — lista de destinos de impressão

- [x] Capturar quatro larguras com dois destinos e nome longo.
- [x] Padronizar título/ação/metadados sem alterar handlers.
- [x] Validar axe/alvos/zoom/overflow e seleção local sem escrita.
- [ ] Aceite humano/leitor de tela; restante de Impressoras não concluído.

### Slice S1d — destino de impressão

- [x] Baseline com destinoNETWORK constante e quatro larguras.
- [x] Agrupar formulário em três fieldsets, preservando handlers/condicionais.
- [x] Testes novos de layout/axe/teclado/zoom e POST simulado200/403.
- [ ] Aceite humano e impressão física; não fechar toda a página de Impressoras.

### Slice S1c — Alertas

- [x] Capturar baseline controlada em quatro larguras antes do código.
- [x] Especificar grupos de prazos e confirmação sem alterar comandos.
- [x] Implementar fieldsets e CSS Module com tokens existentes.
- [x] Validar layout/axe/teclado/zoom200% e estados simulados200/409/403.
- [ ] Aceite humano e leitor de tela manual; não fechar S1 pelo recorte de Alertas.

## S2 — Agora e Operação

- [ ] S2.1 Priorizar exceção e próxima ação; resumos nunca ocultam pendências.
- [ ] S2.2 Harmonizar produção/entregas/salão com detalhes progressivos e destinos corretos.
- [ ] S2.3 Validar vazio/volume alto/stale/erro parcial/sem permissão sem métricas presumidas.

## S3 — Financeiro

- [ ] S3.1 Categorizar entrada de caixa, fechamento, ajustes/aprovações e relatórios.
- [ ] S3.2 Harmonizar uma rota por sub-slice, preservando contexto e calendário operacional.
- [ ] S3.3 Validar parcial/pendente/cancelado/quitado, erros, busy, reauth e intenção ambígua.
- [ ] S3.4 Executar integração real e review R3 se tocar apresentação de ações financeiras/recovery.

## S4 — Cardápio

- [ ] S4.1 Harmonizar entrada e formulários mantendo uma criação e edição por categorias.
- [ ] S4.2 Preservar busca/filtros/draft, erro de campo, pending e retorno ao produto correto.
- [ ] S4.3 Validar listas extensas, nome longo, polling durante edição e permissão negada.

## S5 — Composição e handoff

### Composição parcial de Gestão/S1 — 2026-10-20

- [x] Build/tipos, auth/tenant e112casos focados executados sobre a mesma composição.
- [x] Conferir96hashes/8manifests de capturas S1c–S1j e links da spec.
- [x] Conferir lint limpo dos componentes/helpers/testes focados e registrar4erros herdados nos módulos existentes.
- [ ] Gate global visual, revisãoR3 autenticada, integração real e aceite humano.

Esta rodada não fecha S5 do produto: S2–S4 e gates externos continuam pendentes.

- [ ] S5.1 Rodar typecheck/build/lint focado/test:visual e regressões dos consumidores compartilhados.
- [ ] S5.2 Percorrer ida/volta/histórico/hash/aliases e comparar mesmos estados em quatro larguras.
- [ ] S5.3 Verificar teclado, leitor de tela, foco, zoom200%, safe areas e sem scroll horizontal.
- [ ] S5.4 Registrar evidência por AC/SHA, limitações, review e decisão de aceite visual.
- [ ] S5.5 Registrar próxima etapa e rollback; produção/piloto não derivados de CI.

### S2a — resumo de Agora
- [x] Baseline em quatro larguras e implementação restrita a apresentação/semântica.
- [x] Revisão identificou especificidade e posicionamento global da grade; corrigidos com regressão geométrica.
- [ ] Aceite humano, leitor de tela e gate R3 autenticado; S2 não concluído.

- [x] S2a build/typecheck/lint e30testes finais PASS;12capturas com hashes. Fonte CSS não comprova zoom nativo200%.

### S2b — produção e entregas
- [x] Baseline4larguras e agrupamento/lista/atalhos existentes.
- [x] Build/tipos/lintPASS;22regressõesPASS e5casos focados finaisPASS em rodadas separadas.
- [x] Revisão visual/axe/teclado/CSSzoom2 e12capturas com hashes.
- [ ] Aceite humano/leitor de tela/zoom nativo; próximoS2cSalão.

### S2c — Salão e indisponíveis
- [x] Baseline4larguras, resumo/atalhos e lista semântica com condição preservada.
- [x] Build/typecheck/lint e32testes PASS;12capturas com hashes.
- [ ] Aceite humano/leitor de tela/zoom nativo; S2 global continua pendente.
Próximo recorte S3a: entrada Financeiro.

### S3a — entrada Financeiro
- [x] Baseline4larguras, três grupos nomeados e cinco destinos descritivos.
- [x] Build/tipos/lintPASS;37visuaisPASS;auth4/tenant10PASS.
- [x] Review independente NO_FINDINGS_WITH_GAPS após correçãoP2 de IDs.
- [ ] GateR3autenticado/integração real/zoom nativo/leitor de tela/aceite humano.
Próximo S3b: inventariar fechamento diário e especificar uma slice interna.

- [x] Link Entrar novamente em revogação de Gerência;build/tipos/lint/2testesPASS e review independente local. Aceite autenticado real pendente.

### S3b — cabeçalho/dia do fechamento
- [x] Baseline4larguras, fieldset/data/ações e retornoFinanceiro.
- [x] Build/tipos/lint e14testesPASS;12capturas comhashes.
- [x] Corrigir corte do ano emCSSzoom2mobile identificado no review.
- [ ] GateautenticadoR3/integração/aceite manual.
PróximoS3c revisões/bloqueios.

### S3c — revisões e bloqueios
- [x] Baseline4larguras e resumo/grupos/lista de pendências, comandos preservados.
- [x] Build/tipos/lint e13testesPASS23.1s;12capturas/hashfontes.
- [ ] GateR3autenticado/integração real/aceite humano.
PróximoS3d formulário/propostas de correção.

### S3d — formulário de solicitação
- [x] Fieldset/campos/textarea locais sem mudar comandos.
- [x] Baseline4larguras/build/tipos/lint e17testesPASS30.4s;12capturas/hashes.
- [ ] GateautenticadoR3 e aceite real/manual.
PróximoS3e lista/decisão de propostas.

### S3e — propostas/decisão
- [x] Baseline/artigos/estados/ações com regras preservadas.
- [x] Build/tipos/lintPASS;21testesPASS e4focados reforçadosPASS.
- [ ] GateautenticadoR3/real/manual.
PróximoS3fPIN/composiçãofechamento.

### S3f — PIN e composição local
- [x] Painel/fieldset/açõesPIN, handlers preservados.
- [x] Baseline4larguras/build/tipos/lintPASS;composição30testes54.5sPASS;auth4/tenant10PASS.
- [x] ReviewindependenteNO_FINDINGS_WITH_GAPS;12capturas/hashes.
- [ ] Integraçãoreal/gateR3autenticado/manualpendentes.
Próximo inventário/refino /refunds;S3nãoencerrado.

### S3g — entradaEstornos
- [x] Baseline4larguras e labels/retorno/fieldsetlocal.
- [x] Build/tiposPASS;23testesPASS28.6s;reviewNO_FINDINGS_WITH_GAPS.
- [ ] Lintpágina1erroherdado;gateautenticadoR3/real/manualpendentes.
PróximoS3h pagamentoelegível/resumo.

### S3h — resumo/histórico de pagamento
- [x] Baseline4larguras/grupo/lista/labels sem alterar cálculo.
- [x] Build/tipos/linttestePASS;27testes35.5sPASS;reviewNO_FINDINGS_WITH_GAPS.
- [ ] Lintpáginaherdado/gateR3autenticado/real/manualpendentes.
PróximoS3i formulárioestorno/caixa.

### S3i — formulárioestorno/caixa
- [x] Baseline4larguras/fieldset/labelscomIDs sem alterar comandos.
- [x] Build/tipos/linttestePASS;31testes41.5sPASS;reviewNO_FINDINGS_WITH_GAPS.
- [ ] Lintpáginaherdado/gateR3autenticado/real/manualpendentes.
PróximoS3j avisoestornopendente/composição.

### S3j — pendente/composiçãoEstornos
- [x] Painelpendente/headings/CSSlocal comintentinalterado.
- [x] Baseline4larguras/build/tipos/linttestePASS;35testes48.9sPASS;auth4/tenant10PASS.
- [x] ReviewindependenteNO_FINDINGS_WITH_GAPS;12capturas/hashes.
- [ ] Lintpáginaherdado/gateR3autenticado/real/manualpendentes.
Próxima rota /manage/pricing; S3globalnãoencerrado.

### S3k — política de preços/serviço
- [x] Fieldsets/grade/retorno comcomandosinalterados ebaseline4larguras.
- [x] Build/tipos/linttestePASS;17testes23.3sPASS.
- [ ] Lintpáginaherdado/gateR3autenticado/real/manualpendentes.
PróximoS3l solicitaçõesdeajuste.

### S3l — solicitações/aprovação
- [x] Baseline/artigos/prévia/ações comcomandosinalterados.
- [x] Build/tipos/linttestePASS;21testes30.9sPASS;reviewNO_FINDINGS_WITH_GAPS.
- [ ] Lintpáginaherdado/gateR3autenticado/real/manualpendentes.
Próxima rota /reports,contratoantesdecódigo.

### S3m — relatórios/período
- [x] Baseline4larguras/cabeçalho/fieldsetperiodo semalterar contratos.
- [x] Build/tipos/lintPASS;9focadosPASS+6parityreportsPASS.
- [ ] GateR3autenticado/real/manualpendentes.
PróximoS3n resumo/resultados.

### S3n — resumo financeiro
- [x] Baseline4larguras/partição2keyssemperda/grades.
- [x] Build/tipos/lintPASS;8focados+6parityPASS;valorinteiro360CSSzoomconferido.
- [ ] GateR3autenticado/real/manualpendentes.
PróximoS3o resultadospordia/listas.

### S3o — resultados e listas
- [x] Baseline/diáriosartigos/listas comexpressõespreservadas.
- [x] Build/tipos/lintPASS;12focados+6parityPASS e4repetidoscomsinalnegativo.
- [ ] GateR3autenticado/real/manualpendentes.
PróximoS3p fechamentos/calendar.

### S3p — fechamentos/calendárioReports
- [x] Baseline/artigos/links/fieldset comcontratosinalterados.
- [x] Build/tipos/lintPASS;16focados+6parityPASS;reviewNO_FINDINGS_WITH_GAPS.
- [ ] GateR3autenticado/real/manualpendentes;S3nãohomologadoglobalmente.
PróximoS4Cardápio/inventário.

### S4a — entrada do Cardápio e produtos
- [x] Destinos descritivos, cabeçalho/retorno e ações responsivas.
- [x] Baseline 4 PASS; build/tipos/lint PASS; 34 testes visuais PASS após corrigir retorno e espaçamento.
- [x] 20 capturas e hashes; revisão local R2.
- [ ] Zoom nativo, leitor de tela e homologação operacional.
Próximo: S4b, variações e adicionais.

### S4b — entrada de variações e adicionais
- [x] Cabeçalho/retorno e seletor com ajuda acessível.
- [x] Baseline4 PASS, build/tipos PASS e26visuais PASS;12capturas/hashes.
- [ ] Lint herdado no componente, zoom nativo/manual e gates globais pendentes.
Próximo:S4c listas de variações/grupos; formulários ainda pendentes.

### S4c — listas de variações e grupos
- [x] Regiões nomeadas e linhas/grupos responsivos, handlers preservados.
- [x] Baseline4 PASS, build/tipos PASS,8visuais PASS16,5s;12capturas/hashes.
- [ ] Lint herdado/manual/global pendentes.
Próximo:S4d formulários; disponibilidade ainda pendente.

### S4d — formulários de configuração
- [x] Formulário nomeado, fieldset e ações responsivas/checkbox44px.
- [x] Baseline12 PASS, build/tipos PASS,20visuais PASS39,5s;36capturas/hashes.
- [ ] Lint herdado/manual/global pendentes.
Próximo:S4e disponibilidade; não alterar comandos/recovery.

### S4e — disponibilidade na Gerência
- [x] Layout opt-in da Gerência; Bar/Cozinha mantêm classes anteriores.
- [x] Baseline4 PASS;build/tipos/lint de disponibilidade PASS;24visuais PASS51,3s.
- [x]12capturas/hashes;pending/403/versões/readback interceptados.
- [ ] Manual/integração real/global pendentes.
Próximo:S5 revisão conjunta; depois correções finais e fechamento documental.

### S5 — revisão conjunta de 2026-10-20
- [x]39arquivos de Gerência/245casos executados:244PASS1FAIL de expectativa antiga de sessão.
- [x]Teste corrigido sem mudar produto;21history/session-login PASS no rerun e revisão independente local.
- [x]Build/tipos/auth4/tenant10 PASS;320hashes históricos válidos;20capturas atuais das cinco abas.
- [ ] Lint7erros herdados;gate global/integração real/reviewR3 autenticado/manual pendentes.
Próxima rodada:fechamento,verificar foco no retorno do Cardápio e sincronizar checklist/aceite sem declarar homologação.

### Fechamento local — 2026-10-20
- [x] Perda de foco no retorno do Cardápio reproduzida antes e corrigida pelo mecanismo existente.
- [x]54regressões PASS1,7min;build/tipos/lint focado PASS;review independente local sem achados reproduzíveis.
- [x] Evidência e matriz final em [fechamento local](s5-closeout-evidence.md).
- [ ] Homologação manual/integração real/reviewR3 autenticado/CI final e falhas herdadas de lint/global pendentes.

S1–S4: implementação visual dos recortes planejados entregue localmente. S5: revisão e correção local concluídas; os checkboxes gerais não fechados acima representam requisitos de aceite/gates ainda não comprovados, não uma nova fila de redesenho. Nenhuma nova rodada visual planejada. Não marcar a Spec034 homologada nem autorizar release por esta anotação.

### Manutenção pós-fechamento — leitura inicial do catálogo
- [x] Eliminar ocorrência de lint do catálogo e tratar rejeição de transporte.
- [x] Regressão falha antes;24regressões PASS e2casos de erro PASS no rerun;build/tipos/lint do componente PASS.
- [ ]6erros de lint restantes nos outros módulos;global/integração/manual pendentes.
[Evidência](catalog-read-evidence.md). Sem novas alterações visuais planejadas.

### Manutenção pós-fechamento — leituras de Impressoras
- [x] Erro de lint de impressão eliminado, polling5s e comandos preservados.
- [x] Regressão de filtro tardio falha antes e passa depois;18regressões PASS+3leituras PASS no rerun;build/tipos/lint focado PASS.
- [x] Review independente local do loader sem achados reproduzíveis;limites documentados.
- [ ]5erros herdados restantes;integração real/manual/gates globais pendentes.
[Evidência](print-read-evidence.md).

### Manutenção pós-fechamento — leitura inicial de Setup
- [x] Erro de lint eliminado sem supressão; load manual e pós-comando preservados.
- [x] Freshness invalidada em mudança de capacidade sem descartar recovery ou envio pendente.
- [x] Build/tipos/auth4/tenant10/lint focado PASS;26 casos PASS na composição e6 mesas PASS no rerun,27 distintos cobertos.
- [x] Revisão independente final sem achados reproduzíveis; contraprovas documentadas.
- [ ] Quatro erros de lint restantes; integração real/manual/gates globais pendentes.
[Evidência e limites](setup-read-evidence.md).

### Manutenção pós-fechamento — consulta inicial de Preços e serviço
- [x] Erro de lint eliminado; transporte inicial tratado sem alterar comandos financeiros.
- [x] Regressão network falha antes;10 visuais PASS21,1s;build/tipos/auth4/tenant10/lint focado PASS.
- [x] Revisão independente local sem achados reproduzíveis;limites herdados explícitos.
- [ ] Três erros de lint restantes(refunds e2house-account);integração real/manual/gates globais pendentes.
[Evidência](pricing-read-evidence.md).

### Manutenção pós-fechamento — consulta inicial de Estornos
- [x] Erro de lint eliminado sem alterar intenção, locks, comandos e seleção financeira.
- [x]39 testes PASS58,9s;build/tipos/auth4/tenant10/lint focado PASS.
- [x] Revisão independente local sem achados reproduzíveis;limites de integração explícitos.
- [ ] Dois erros de lint restantes em house-account;gates globais/manual/integração real pendentes.
[Evidência](refund-read-evidence.md).

### Manutenção pós-fechamento — carregamento e seleção de Clientes
- [x] Dois erros de lint eliminados; seleção por ID com snapshot canônico e limpeza de ID ausente.
- [x]18 testes PASS22,8s;build/tipos/auth4/tenant10/lint focado PASS.
- [x] Revisão independente local sem achados reproduzíveis.
- [x] Os16 arquivos de implementação acompanhados têm0erros/0avisos de lint; sete erros originais resolvidos.
- [ ] Integração real, suíte/lint globais, review autenticado e homologação manual continuam pendentes.
[Evidência e limites](customer-read-evidence.md). Não declarar lint global limpo nem produção pronta.

### Validação composta pós-manutenção — checkpoint, 2026-10-20
- [x] Build webpack/typecheck/auth4/tenant10 PASS na rodada.
- [ ] Visual294casos interrompido de forma controlada após39casos concluídos PASS; resultado final não obtido.
- [ ] Lint global iniciado/interrompido; não há PASS ou contagem confirmada.
Retomar pelo PROMPT PARA O PRÓXIMO AGENTE no handoff. Sem alteração nova de produto nesta rodada; preservar todo o working tree e serviços separados de inspeção.

Atualização do checkpoint: JSON global foi encontrado após encerramento e parseado:318arquivos/10erros/0avisos, portanto lint global FAIL observado. Causa não triada. Portas3100/3101 livres, preview3001/API8000 preservados. Visual composto continua parcial39PASS sem resultado final.

### Manutenção global — Catálogo rápido
- [x] Reset de busca movido para eventos, com debounce/abort e comandos preservados.
- [x]15regressões existentes PASS;2novos testes PASS no rerun;build/tipos/lint focado PASS.
- [ ] Lint global:9erros restantes;composição294 ainda parcial;integração/manual/gates finais pendentes.
[Evidência](quick-catalog-search-evidence.md).

### Manutenção global — leitura de pessoas,2026-10-21
- [x] Consulta inicial separada e protegida por cleanup; comandos/retry intactos.
- [x] Lint focado, tipos/build PASS; teste visual focal1PASS4,1s após migração do caminho antigo.
- [x] Revisão independente local do componente sem achados; limite de componente sem callsite registrado.
- [ ] Lint global8erros restantes; composição/manual/integração/review autenticado pendentes.
[Evidência](party-size-read-evidence.md).

### Manutenção global — leitura de Administrar equipe,2026-10-21
- [x] Leitor/callbacks e cleanup; freshness invalidada em troca de acesso sem descartar tentativa.
- [x]6visuais PASS7,9s;build/tipos/lint focado/diff check PASS.
- [x]Revisão independente local sem achados, com limites registrados.
- [ ]Lint global7erros;visual composto/integração/manual/review autenticado pendentes.
[Evidência](developer-staff-read-evidence.md).

### Quantidade de remoção —2026-10-21
- [x] Clamp em render com guarda original;6visuais PASS11,8s;build/tipos/lint focado/diff PASS.
- [ ]Lint global6erros;integração/manual/composição/review autenticado pendentes.
[Evidência](removal-quantity-evidence.md).

### Relógio de estação —2026-10-21
- [x]Relógio inicializado nos callbacks de snapshot;intervalo15s intacto.
- [x]11visuais PASS16,7s;build/tipos/lint focado/diff PASS. Revisão do autor R2.
- [ ]Lint global5erros;integração/manual/composição/review autenticado pendentes.
[Evidência](production-clock-evidence.md).

### Leitura de ajustes —2026-10-21
- [x]Leitura inicial de ajustes separada, cleanup e erro de transporte explícito.
- [x]9visuais PASS11,7s e2novosPASS3,9s;build/tipos/lint focado PASS.
- [ ]Lint global4erros e composição/manual/integração/review autenticado pendentes.
[Evidência](pricing-adjustment-read-evidence.md).

### Consulta de sessão —2026-10-21
- [x]Consulta inicial sessão separada com cleanup;manual/comandos intactos.
- [x]15visuaisPASS11,5s;build/tipos/lintfocado/auth4/tenant10/diff PASS.
- [x]Revisão independente local sem achados.
- [ ]Lint global3erros;composição/manual/integração/reviewautenticado pendentes.
[Evidência](staff-session-read-evidence.md).

### Rollout das mesas —2026-10-21
- [x]ReadPolicy/callbacks/cleanup;POST/recoveryintactos.
- [x]15visuaisPASS15,2s;build/tipos/lintfocado/diffPASS.
- [ ]Lintglobal2errosguest-ordering;composição/manual/integração/reviewautenticado pendentes.
[Evidência](table-service-rollout-read-evidence.md).

### Bootstrap do cliente —2026-10-21
- [x]DoiserrosGuestOrderingeliminados;bootstrap/receipt preservam contratos.
- [x]59visuaisPASS57,4s;build/tipos/lint global0erros0avisos/auth4/tenant10/diffPASS.
- [x]Reviewindependente local semachados,gapsregistrados.
- [ ]Composiçãovisual/manual/integraçãoreal/CI/reviewautenticadopendentes.
[Evidência](guest-bootstrap-evidence.md).

### Composição final local —2026-10-21
- [x]Composição Gerência completa:296PASS/0falhas/7,3min em uma execução (47management+3adjacentes).
- [x]Nenhum novo código;diffcheckPASS. Lintglobal/build/tipos/auth/tenant da rodada anterior válidos para mesmas fontes.
- [ ]Suíteglobalrepositório/integraçãoreal/CI/manual/reviewautenticado pendentes.
[Evidência](composed-final-evidence.md).

### Preparação manual —2026-10-21
- [x]Web3001/API8000/dispatcher/bancoexistenteretomados;readyAPI200 eWeb200.
- [ ]Conferênciamanualautenticada/operadorpendente;semalegaçãodehomologação.
[Runtime e roteiro](manual-review-runtime.md).

### Integração focada —2026-10-21
- [x]ExecutorWindowscompatívelcomexclusãoconservadora;6unitários/RuffPASS.
- [x]13integraçõesWeb/API/PostgreSQLPASS1,8minemclusterdescartávelseparado.
- [x]Revisãoindependentelocalsemachados;serviçosinspeçãopreservados200.
- [ ]Suíteintegraçãointegral/Linux/CI/reviewautenticado/manualpendentes.
[Evidência](integration-focused-evidence.md).
