# Spec 034 — Gerência: UX por tarefa e padronização visual

**Estado:** S1a/S1b em PRs draft; recortes S1c–S1j implementados localmente,
2026-10-20. Rodada automatizada composta de S1 registrada; gates/aceite global
pendentes; não é release. Ver [composição S1](composed-s1-evidence.md).
**Base examinada:** `main@e82d36c453d44c861b26f104afa39bcc8706814d`.

## Objetivo e usuários

Evoluir a Gerência Web/PWA para uma experiência coesa, agradável e orgânica,
reconhecível como Rodada e alinhada aos princípios da UX 2.0. Gerentes precisam
identificar exceções durante o serviço, consultar financeiro fora do pico e
encontrar configurações sem explorar uma coleção de módulos.

O recorte inicial é Gestão. A direção se estende às cinco áreas e suas páginas
internas em etapas independentes. Não pressupõe refazer funcionalidades existentes.

## Fontes e precedência

- [Spec 007](../007-management-cockpit/spec.md) e seu [aceite](../007-management-cockpit/acceptance.md): intenção e navegação da Gerência.
- [Design system](../../docs/design/system.md), [marca](../../docs/design/brand-v1.md) e [princípios](../../docs/product/principles.md): identidade e interação.
- [Direção UX 2.0](../../docs/design/ux-2-0/README.md): tarefas, contexto e densidade; o protótipo de Atendimento não é uma referência pixel a pixel para Gerência.
- [Spec 033](../033-attendance-ux2-productization/spec.md): frente adjacente de Atendimento, sem transferir seu ownership para esta spec.
- [Baseline e escopo](baseline.md), [plano](plan.md), [tarefas](tasks.md) e [aceite](acceptance.md).

Spec 034 complementa a apresentação da Spec 007; dinheiro, acesso, idempotência,
calendário operacional, domínio e regras existentes continuam sob seus contratos.
Conflitos descobertos exigem registro e decisão, nunca alteração silenciosa.

## Antes e depois propostos

Gestão hoje agrupa links em painéis com botões secundários de mesma ênfase.
Proposta: seções leves com linhas de navegação inteiras, título, descrição curta,
ícone coerente e indicador de avanço. Menos bordas aninhadas, ritmo consistente
e hierarquia entre tarefa, explicação e ação. “Orgânico” significa continuidade,
espaço e formas dos tokens existentes; não novas ilustrações ou decoração.

Preservar Agora / Operação / Financeiro / Cardápio / Gestão, links diretos e
aliases `vendas` e `mais`. Não criar uma sexta aba nem um segundo menu global.
Cabeçalho identifica a tarefa; ações utilitárias são compactas e têm nome acessível.
Atualizar e histórico não competem visualmente com a tarefa principal.
Freshness permanece verdadeiro, mesmo quando a área contém apenas navegação.

## Categorias e fluxos

| Área | Trabalho principal | Direção proposta |
| --- | --- | --- |
| Agora | Identificar e abrir exceção | Alertas acionáveis antes de pulso; fatos e próxima ação visíveis |
| Operação | Localizar gargalo e abrir contexto | Produção/entrega e salão com resumos e destinos claros, sem listas extensas abertas por padrão |
| Financeiro | Escolher revisão, caixa ou consulta | Separar grupos de tarefas; valores canônicos, pendências e confirmações preservados |
| Cardápio | Criar ou editar produto | Manter uma criação e o editor por categorias; harmonizar página, estados e retorno |
| Gestão | Encontrar configuração ou acesso | Estabelecimento e pessoas; configurações da operação; acesso |

Fluxo inicial: Gestão → linha de destino → tarefa interna → Voltar à Gestão,
restaurando foco na origem e posição quando aplicável. Setup mantém mesas,
zonas e equipe; não inventar acesso de pessoas independente sem endpoint existente.
Sessão continua no fluxo `/staff`; não expandir permissões ou autoexecutar logout.
Página interna compartilhada preserva o retorno contextual de outros módulos.

## Design e arquitetura

Reutilizar `appShell`, navegação gerencial, `OperationalIcon`, heading, campos,
botões, diálogos e notice existentes. Extrair linha de navegação/padrão gerencial
apenas após inventariar reutilização. CSS fica sob escopo da Gerência; revisar
impacto em consumidores compartilhados. Documentar novos padrões aprovados no
design system no PR de implementação; esta proposta não cria tokens.

Paleta noturna, âmbar de seleção, papel para conteúdo; Archivo e JetBrains Mono
para valores. Usar escala 4/8/12/16/20/24/32, raios e estados semânticos existentes.
Sem gradientes, glassmorphism, sombras ornamentais ou indicadores fictícios.
Mobile em uma coluna; desktop pode expandir grupos quando leitura e ordem de
teclado permanecem equivalentes. Não impor alturas fixas que cortem fonte ampliada.

## Estados e recuperação obrigatórios

| Estado | Apresentação e ação |
| --- | --- |
| Inicial/carregando | Status nomeado e espaço estável; sem contadores zero presumidos |
| Vazio confirmado | Explicação específica, ação existente quando autorizada |
| Sucesso de leitura | Conteúdo e contexto reais; nenhuma confirmação de escrita ao navegar |
| Atualizando | Preservar contexto e edição, indicar atualização sem simular offline |
| Desatualizado/offline | Último estado identificado e tentativa de reconexão; sem inventar “Ao vivo” |
| Erro parcial/total | Escopo e retry visíveis; nunca publicar soma parcial como completa |
| Sem permissão/revogada | Acesso explícito; dados protegidos tratados pelo fluxo existente, retorno ao login quando exigido |
| Gravação/busy | Ação e navegação conflitante bloqueadas, anúncio acessível |
| ACK pendente/timeout | Conservar intenção/chave/contexto; verificar readback, não repetir mutation por navegação |
| Erro de validação/conflito | Erro junto ao campo/contexto e decisão explícita; conservar entrada válida |
| Sucesso de escrita | Somente readback canônico; feedback e retorno/foco previsíveis |
| Reload/expiração/retorno | Preservar recuperação existente; não prometer drafts persistidos que o módulo não possui |

## Acessibilidade e casos extremos

Links navegam; botões executam ações. Linha inteira tem um único alvo, sem botões
aninhados. Ícones decorativos não duplicam leitura; ícones sem texto têm nome.
Foco visível, ordem lógica, landmarks e headings; Escape/Back fecham apenas a
camada superior permitida e restauram foco. Estados anunciados sem repetição a
cada polling. Alvos >=44px, ações operacionais conforme design system.

Validar 360/390/430/1280px, fonte/zoom 200%, texto longo, listas extensas,
teclado, safe areas e preferência de movimento reduzido. Rodapé não cobre ações,
mensagens ou foco; sem scroll horizontal da página. Cor nunca é o único estado.

## Invariantes, limites e autorização

Navegação não cria mesa/comanda, pedido, pagamento, aprovação ou alteração de
configuração. Manter Tab distinta de TableOccupancy, saldo em centavos, API
autoritativa, Venue, capabilities, reauth, validações, ledger e auditoria.
Pendente, pago, cancelado e inferido não ganham semântica nova por estética.

Fora do escopo: implementar Spec 031/032, relatórios/métricas novos, novos
cadastros/endpoints, migration, política de limite, impressão física, Android,
troca de marca, auth/BFF, deploy, merge e alteração de CI/baselines para mascarar falhas.

S0 autorizou planejar/publicar PR documental. A continuação autorizada pelo
usuário implementa as sub-slices registradas abaixo. S2–S5 permanecem no plano,
sem declaração de UX global aprovada ou implantação.

## S1a — entrada Gestão, continuidade autorizada em 2026-10-19

Primeira slice de implementação: apenas `/manage#gestao`, com três grupos e cinco
destinos preservados. Linhas inteiras têm ícone decorativo, título como nome
acessível, descrição associada e chevron decorativo. Sem novos dados ou contadores.
O acesso DEV mantém seu componente e gate existentes, separado visualmente.
Utilitários do header ficam compactos somente nesta área; outras abas preservam layout.
Formulários internos e restauração de foco entre rotas ficam para sub-slice própria;
esta entrega não declara AC03 completo. Conteúdo mantém estados/rede existentes.

## S1b — cabeçalhos e retorno de páginas internas

Continuidade autorizada: setup, clientes, alertas e impressoras passam a usar
cabeçalho comum com retorno “Voltar à Gestão”, contexto e descrição da tarefa.
Títulos existentes são preservados. Formulários e comandos não são reorganizados.
Na entrada, a navegação guarda apenas origem enumerada e posição de rolagem,
sem identidade ou dados operacionais. Retorno explícito e Back do navegador
restauram foco ao link original depois de carregar a entrada. Armazenamento
indisponível não bloqueia links. Acesso direto às subpáginas continua funcionando.
Sessão `/staff` fica fora por ser compartilhada. Bloqueios de saída dos módulos
não são substituídos por esse mecanismo; não alegar aceite integral de AC03.

## S1c — formulário de Alertas

Agrupar os cinco prazos em Produção, Pagamento e Atendimento com fieldsets e
legendas. Manter nomes acessíveis, ordem, unidade segundos, limites e valores.
Separar confirmação (motivo, PIN e salvar) dos prazos, sem esconder avisos.
Uma coluna no mobile; campos relacionados podem ocupar duas no desktop.
Somente apresentação: handlers, endpoints, política versionada, reauth, mensagens,
conflito409, preservação de draft e bloqueios permanecem literalmente iguais.
Risco R2; não alterar recovery ou autenticação. Validar quatro larguras, teclado,
zoom200%, axe, payload e estados simulados, sem escrita no banco compartilhado.

## S1d — formulário de destino de impressão

Gerente configura destino existente ou novo, com os mesmos campos e comandos.
Agrupar Nome em Identificação; Saída/Papel/referência condicional em Conexão e
papel; estação/ativação/corte em Uso na operação. Fieldsets nomeados, coluna
mobile, conexão em duas colunas desktop. Salvar permanece explícito após grupos.
Preservar ordem de foco, labels, limites, defaults, edição, estado busy e erros.
Referência continua ausente para BROWSER/AGENT; corte continua desabilitado para
AGENT. Não mudar handlers, polling, payloads, agentes/pareamento, rotas, trabalhos,
idempotência, permissões ou confirmação física. R2 somente JSX/CSS local.
Loading/vazio/erro continuam existentes; não inventar confirmação de papel.
Aceite: quatro larguras, zoom200%, axe, teclado, condicionais, ausência de escrita
ao navegar/configurar e POST simulado200/403 com payload conservado. Impressão
física, pareamento, mutações reais, auth e recovery ficam fora desta slice.

## S1e — leitura dos destinos de impressão

Organizar a lista existente em articles nomeados pelo destino, título h3 e ação
Configurar contextual. Separar saída/papel/ativação, estado de hardware e bridge,
estações ou documentos de cliente. Preservar todos os valores e condicionais:
AGENT não mostra bridge; UNKNOWN sem data continua sem leitura de hardware.
Nomes longos quebram linha; ação tem alvo44px e nome acessível dentro do destino.
Não alterar edit/mutate/polling nem apresentar papel confirmado por saúde/conexão.
Risco R2 visual; lista vazia continua sem destinos, sem inferir erro ou sucesso.
Aceite com dois destinos constantes (NETWORK ativo e AGENT desativado), quatro
larguras e zoom200%, axe, edição local correta e nenhuma escrita ao navegar.

## S1f — leitura dos trabalhos de impressão

Preservar filtros/paginação/motivo e todos os comandos existentes. Substituir
painéis aninhados por articles nomeados pelo ID, estado canônico em h3, referência
e erro explícitos, tentativas e indicação de cópia visíveis, ações em grade de
uma coluna mobile/duas desktop. Não recolher erros ou exigir gesto para lê-los.
Não alterar printState, payloads/UUID, mutate, condições de retry/confirm/cancel/
reprint, busy ou polling. R2 de apresentação; mudanças de recovery fora de escopo.
Aceite: quatro larguras/zoom200%/axe, documento correto, estado incerto sem retry,
impresso sem cancelar, motivo obrigatório para cópia, comandos simulados com erro
sem sucesso fictício. Sem impressão real nem escrita no banco compartilhado.

## S1g — consulta e cadastro de mesas/zonas em Setup

Gerente consulta recursos e cadastra mesa/zona pelo mesmo fluxo existente.
Separar resumo de Mesas/Zonas em listas nomeadas, sem comprimir nomes em texto
corrido; listas aparecem somente com fresh confirmado. Vazio é explícito por tipo,
sem declarar vazio em loading/erro. Novo cadastro usa fieldset com os mesmos campos,
labels, ordem, opções QR e botão, em coluna mobile/duas colunas desktop.
Preservar gates, handlers, payloads, bloqueio de cadastro incerto, refresh/draft,
rollout de atendimento e seção inteira de equipe literalmente iguais. R2 somente
apresentação; auth/dados/recovery não são redesenhados nem simplificados.
Aceite: nomes longos/quatro larguras/zoom/axe/teclado, mesa→zona e refresh sem
perder texto, loading/vazio/erro e regressão existente de cadastro ambíguo/vínculo.
Sem escrita real no banco compartilhado. Não fecha Setup ou S1 completa.

## S1h — apresentação da equipe existente em Setup

Preservar seletor de operador e estado atual; agrupar função/situação em Alterar
vínculo e motivo/PIN/aviso/ação em Confirmar alteração. Aviso de encerramento de
sessões permanece explícito antes de aplicar. Mesmos labels/IDs/opções/ordem,
canManage, reauth, versão, sending/busy/fresh, limpeza do PIN e readback.
Somente JSX/CSS; não mudar permissões, endpoints, modelo de sessão ou recovery.
R3 conservador pelo contexto de edição de acesso: revisão em outro contexto
antes de recomendar merge, sem confundir review local com aprovação GitHub.
Aceite: quatro larguras/zoom/axe/teclado, sem escrita ao abrir, editor ausente sem
capability, reauth recusada sem PATCH, PATCH200/403/409 simulado mantendo payload,
busy, PIN limpo e consulta existente. Integração real/tenant/revogação permanecem
gates próprios; nunca executar alteração de vínculo no banco compartilhado.

## S1i — busca e cadastro de clientes

No componente Conta da casa usado em Clientes, agrupar busca e cadastro/
relacionamento em fieldsets separados; busca mantém campo e botão próximos.
Manter ordem de resultados e todos os controles/labels/IDs, inclusive PIN e
seleção de relacionamento compartilhados. Não alterar handlers/gates/centavos,
override/replay, políticas, visitas, mensagens ou associação à comanda.
R3 conservador por contexto financeiro/PII: revisão em outro contexto antes de
recomendar merge. Aceite por quatro larguras/zoom/axe/teclado, busca sem POST,
cadastro200/403 simulado com payload preservado, erro conservando texto e editor
ausente sem capability. Integração real e aceite financeiro continuam fora do
recorte de apresentação; não criar cliente real para validar a aparência.

## S1j — resultados e feedback de consultas em Clientes

Resultados usam articles nomeados, identificação/relacionamento e ações em coluna
mobile/grade desktop; evitar colunas estreitas em zoom200. Mesmos botões, gates,
ordem, payloads e seleção compartilhada. Busca, visitas, políticas e inspeção de
comanda são consultasGET: não podem anunciar alteração confirmada. O executor
mantém a mensagem de sucesso existente como default das mutações, mas recebe null
explicitamente nas quatro consultas. Busy/erros/reauth/PIN/reload/override e replay
preservados. R3 por mudança de feedback em componente financeiro; revisão em
outro contexto, sem aprovação automática de merge. Regressão deve falhar na base
para a mensagem indevida e passar após correção. Validar leitura sem writes,
mutação simulada mantendo confirmação/reauth e quatro larguras/zoom/axe.

### S2a — resumo e acessos rápidos de Agora

Recorte visual: manter alertas/exceções antes do pulso, os mesmos valores confirmados e os mesmos destinos. Nomear a região do resumo e a navegação de acessos rápidos; empilhar indicadores e atalhos no celular, expandindo em duas colunas a partir de768px. Detalhes adicionais permanecem expansíveis por teclado. Não alterar carregamento, cache, autorização, ciência de alerta ou cálculo monetário. Loading/erro sem snapshot continuam sem resumo; estado antigo continua identificado pelo aviso existente. Aceite: quatro larguras360/390/430/1280, fonte200%, axe, alvo44px, teclado, destinos e nenhuma escrita ao consultar/expandir.

### S2b — produção e entregas em Operação

Gerente consulta contadores existentes de Bar/Cozinha/prontos e abre detalhes por teclado; atalhos levam às estações existentes. Região nomeada Produção e entrega, contadores agrupados, entregas como lista com destino/produto/idade preservados; nomes longos quebram, idades legíveis; vazio explícito apenas sob snapshot existente. Estado antigo conserva aviso global; erro inicial/sem permissão não produz zeros. Sem novos endpoints, paginação, ordenação, estados, comandos ou cálculo; Salão fica para próximo recorte. Aceite:360/390/430/1280,8entregas/nomes longos/sem destino, lista expansível, axe, teclado, alvos44px, ampliaçãoCSS200% local, nenhuma escrita e regressões de navegação/Agora. Zoom nativo e leitor de tela permanecem aceite manual.

### S2c — Salão e itens indisponíveis

RecorteR2 visual. Região Salão nomeada, mesmos contadores de ocupadas/limpeza e quatro destinos existentes, agrupamento Surface2 e atalhos em uma coluna mobile/duas desktop. Itens indisponíveis permanecem expansíveis, com mesma condição/filtro e nomes completos em lista semântica. Não alterar APIs, cache, permissões, cálculo, eventos ou comandos. Vazio confirmado conserva zeros no Salão e ausência do bloco indisponíveis; erro inicial não mostra resumo; snapshot antigo mantém aviso existente. Aceite360/390/430/1280 com12nomes longos, teclado/foco, alvos44px, axe/overflow/CSSzoom2 local e nenhuma escrita; regressõesS2a/S2b/navegação. Zoom nativo/leitor de tela/aceite humano pendentes.

### S3a — entrada Financeiro

Recorte de apresentação dos três grupos existentes e cinco destinos: caixa/turnos, fechamento, correções/estornos, serviço/descontos/aprovações e relatórios. Reutilizar padrão de destino descritivo de Gestão, nomes acessíveis preservados e descrições curtas. Nomear regiões e melhorar quebra dos resumos de caixas no mobile. Preservar literalmente seleção de caixas ativos, valores, fallback Ver caixa, mensagens, estados e destinos. Sem comandos novos, indicadores, autorização, cache, API ou cálculo. Não confundir contagem com pagamento confirmado. Loading/erro inicial não mostra totais; vazio e snapshot antigo conservam contrato atual. Aceite360/390/430/1280 com caixaOPEN/COUNTING/zero/valor ausente, nomes longos, cinco destinos, teclado/axe/alvos44px/CSSzoom2 e nenhuma escrita; regressões de navegação/Operação/Agora. R3 conservador por apresentação financeira, revisão independente obrigatória; integração real/gate autenticado e aceite humano permanecem pendentes.

### Recuperação visual de sessão em Gerência
Quando o callback existente marcar a sessão encerrada, exibir link Entrar novamente para /staff no aviso. Não autenticar automaticamente, não incluir tokens/retorno em URL e não alterar revogação/cache. Erros comuns de rede não exibem esse link. Aceite: link por teclado com alvo44px, login existente e ausência após erro de leitura comum.

Refino visual do aviso de sessão: painel Surface1 com borda/radius existentes, ícone lock em âmbar, título Sessão encerrada em texto normal, instrução curta e ação Entrar novamente de56px sem sublinhado. Preservar historyRevoked, destino /staff, rolealert e erros comuns.

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

### S5 — fechamento do retorno ao Cardápio

AC03 inclui produtos e variações: ao voltar, manter aba Cardápio e focar o destino correspondente, visível acima da navegação; reutilizar armazenamento de contexto existente, sem conteúdo de catálogo ou credenciais. Links diretos criam origem padrão; storage bloqueado mantém navegação sem prometer foco. Cliques modificados não alteram contexto da aba original. Preservar URLs/aliases e handlers de domínio. Aceite: regressão falha antes, quatro larguras/dois destinos, links diretos e storage indisponível; composição de navegação/Gestão/editor permanece válida.

### Manutenção pós-fechamento — consulta inicial do catálogo

Eliminar a ocorrência herdada de set-state-in-effect no editor de variações sem adiar setters artificialmente nem suprimir regra. Efeito faz consulta externa e atualiza estado no retorno assíncrono; desmontagem ignora resposta tardia. Manter URL include_inactive=true, mensagens da API e formulários/comandos. Falha de transporte deve exibir erro sem rejeição não tratada nem formulário gravável. Aceite: lint do componente PASS, erro500 e falha de rede sem escrita/pageerror, regressões de seleção/editor e build/tipos. Outros6erros de lint fora deste recorte.

### Manutenção pós-fechamento — leituras de Impressoras

Remover a ocorrência herdada de set-state-in-effect sem timers artificiais ou supressão. Separar consulta de aplicação dos resultados: efeito assina retorno assíncrono; manter GETs/filtros/paginação, intervalo5s, mensagens e load após comandos. Cleanup invalida resultados da assinatura anterior quando filtro/página muda ou tela desmonta, impedindo lista antiga de substituir filtro atual. Sem alteração de mutações/idempotência/copyIntent. Aceite: regressão tardia falha antes, polling5s/falha de transporte/parada após saída, build/tipos/lint e regressões de destinos/trabalhos/comandos interceptados. Outros5erros fora do recorte.

### Manutenção pós-fechamento — leitura inicial de Setup

Remover ocorrência herdada de set-state-in-effect no carregamento inicial sem supressão ou adiamento artificial. Separar consulta dos recursos/aplicação dos resultados e assinar consulta no efeito com cleanup. Manter GETs de mesas/zonas e consulta de vínculos somente quando canManage, mensagens e reload manual/pós-comando. Fresh só vale para o contexto canManage confirmado, impedindo uso de resposta anterior quando capacidade muda. Preservar envio/reauth/PIN/versões/uncertainCreate/sending e load(false) que conserva erro de mutação. Aceite: lint/build/tipos e regressões de setup/equipe, rede503/transport, recarga bloqueia escrita e preserva rascunho, consultas sem staff.manage não pedem vínculos. Outros4erros de lint fora do recorte.

Detalhe de contexto: mudança de staff.manage invalida fresh durante a reconciliação do estado de leitura, sem remontar Setup ou descartar uncertainCreate/sending/busy/rascunhos. A assinatura antiga é invalidada pelo cleanup; toda transição, inclusive ida/volta, exige nova confirmação. Resposta incerta ou envio pendente continuam bloqueando cadastro até readback e conferência explícita já existentes.

### Manutenção pós-fechamento — consulta inicial de Preços e serviço

Remover lint herdado sem supressão/timer artificial, separando os GETs e aplicação de resposta. Efeito assina consulta assíncrona e ignora conclusão após desmontagem. Preservar URL, resultados parciais, cálculo em basis points/centavos, PIN/reauth/versões, comandos e load manual/pós-comando. Falha de transporte inicial deve ser exibida sem pageerror nem autorização para salvar política ausente. Aceite: regressão network falha antes,503 com mensagem da API, save sem política bloqueado mesmo com PIN, nenhuma escrita nas consultas, regressões positivas/negativas de política e aprovação, build/tipos/lint e review independente. Demais3erros fora deste recorte.

### Manutenção pós-fechamento — consulta inicial de Estornos

Remover erro herdado de set-state-in-effect sem supressão/timer artificial. Separar GETs de comandas/caixas e aplicação de resultados; efeito mantém loading inicial true até resolução, trata erro como antes e ignora conclusão após desmontagem. Preservar resultados parciais, caixas com turno aberto e escolha válida, load pós-intent, saldo/centavos, PIN/reauth e useManualRefundIntent/locks/IDs/payloads. Aceite: lint/build/tipos, consulta atrasada/erro/rede/filtrocaixas sem POST, regressões positivas/negativas de estorno e replay/readback interceptado, review independente. Outros2erros de lint fora do recorte.

### Manutenção pós-fechamento — carregamento e seleção de Clientes

Eliminar os dois set-state-in-effect herdados sem supressão ou timers artificiais. Separar GET de sessão e paginação de comandas da aplicação dos dados; efeito inicial assina consulta/cleanup e mantém polling15s, visibility e eventos online/focus/offline. Manter seleção por ID, derivando snapshot da lista canônica; atualizar ID na aplicação dos dados e limpá-lo quando comanda desaparece, sem reassociação automática se reaparecer. Preservar contexto venue/staff/session, limpeza de PIN/histórico/clientes/visitas e intent quando ator muda, comportamento stale/loading/erro, autorização/reauth, idempotency_key/payload/expires e todos comandos. Aceite: lint/build/tipos, seleção atualizada/remove/reaparece, intenção ambígua preservada no refresh e retry com mesmo payload, troca de ator sem seleção antiga, falha de leitura sem escrita, regressões de Clientes e review independente. Não declarar toda corrida herdada resolvida.

### Manutenção global — debounce do Catálogo rápido

Remover set-state-in-effect herdado do início da busca, sem suprimir lint nem criar adiamento artificial. Reset de searching/searchOk/active pertence aos eventos que iniciam nova busca: abrir painel fechado, editar nome e voltar da criação. Preservar debounce180ms/AbortController, não reiniciar ao clicar no acionador de painel já aberto, esconder opções anteriores durante busca e impedir criação antes de resposta confirmada. Manter permissões, estações, preços/centavos e POST resolve-or-create. Aceite: lint/build/tipos, abrir/reabrir/voltar, digitação rápida/abort e regressões de criação/edição.

### Manutenção global — consulta de pessoas (2026-10-21)
Separar a leitura inicial assíncrona de PartySizeEditor da aplicação de estado. Ignorar respostas da leitura inicial após cleanup. Preservar consulta manual, conflito409, payload/chave de retry e campos pendentes. O componente permanece sem montagem nas telas atuais; não reintroduzir o controle no popup simplificado.

### Manutenção global — leitura da equipe,2026-10-21
Consulta inicial de Administrar equipe separa leitura assíncrona de aplicação de estado, ignora resposta inicial após cleanup e só consulta com staff.manage. Mantém freshness bloqueando comandos antes de confirmação, consulta manual/pós-comando, PIN e payload de tentativa pendente.

### Manutenção global — quantidade de remoção,2026-10-21
A quantidade da remoção confirmada é reconciliada com o item atual durante render apenas quando não busy/uncertain/applied. Preservar clamp1..item.quantity, intenção/chave pendente e estados de confirmação. Nenhuma alteração de comando, autorização ou dinheiro.

### Manutenção global — relógio da estação,2026-10-21
Relógio local de Bar/Cozinha é inicializado ao aplicar snapshot consultado/restaurado e permanece atualizado pelo intervalo15s. Sem snapshot, cabeçalho pode mostrar — até leitura ou primeiro tick. Não alterar comandos, estados, polling ou timestamps canônicos.

### Manutenção global — leitura de ajustes,2026-10-21
Separar leitura inicial de PricingAdjustments da aplicação de estado; ignorar resposta inicial desativada. Preservar load manual, armazenamento por Venue/staff/Tab, intenção/chave, cálculo em centavos, prévia e comandos.

### Manutenção global — consulta de sessão,2026-10-21
StaffAuthScreen consulta sessão inicial por callbacks assíncronos com cleanup. Preservar estados loading/sessionChecked, resultados401/403, erro de transporte, loadSession manual, login/logout/invalidação e permissões.

### Manutenção global — rollout das mesas,2026-10-21
Carregamento inicial de TableServiceRollout captura recuperação local e aplica estado após resposta da consulta canônica (inclusive falha). Botão permanece bloqueado até policy conhecida; storage ilegível bloqueia alteração. Preservar payload/chave e persistência antes do POST, conflitos e readback.

### Manutenção global — bootstrap do cliente,2026-10-21
GuestOrdering separa bootstrap (cache/storage/context ou QRresolve) da aplicação de estado e ignora aplicação inicial desativada. Preservar contextGET quando há intenção pendente, QRresolvePOST caso contrário, cookies/headers, carrinho e replay. Receipt/erro são limpos por reconciliação de identidade token/Tab. Cache aparece após bootstrap resolver; loading bloqueia operação durante leitura.

### Validação integrada — executor Windows,2026-10-21
Executor de integração local mantém isolamento PostgreSQL allowlisted e bloqueio entre processos também no Windows. Linux conserva flock compartilhado/exclusivo. Windows usa bloqueio exclusivo conservador para leitores e resets, serializando sem dispensar proteção. Nenhuma alteração no banco de inspeção ou na política de reset.
