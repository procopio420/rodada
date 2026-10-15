# Plano — Spec 026

## Ordem executável na main integrada

Detalhamento e dependências em [tasks.md](tasks.md), T01–T14, base `ad5d64f`.
Começar por T01 e pela menor lacuna comprovada de T02. Depois priorizar T03
(segurança financeira) e T04 (draft/seleção). T05/T06 sustentam recuperação e
busca; T07–T13 são slices específicas; T14 reúne evidência integrada.
Cada slice atualiza os contratos proprietários e critérios antes de implementar.
Não refazer melhorias da Spec 025 nem presumir UX-34 corrigido pela remoção
parcial de quantidade da Spec 017. O diagnóstico T01 e o recorte gerencial sem
devolução T02 estão entregues localmente; ver [revalidation.md](revalidation.md).
T03a/UX-08 e T03b/UX-22 entregues: recebimento CASH e estorno manual
recuperáveis. T04/UX-06/35 entregue localmente com draft por comanda em memória
e reseleção previsível. T05a recupera o mesmo pedido staff Web após resposta
perdida/reload na mesma aba/sessão. T05b cobre guest com sessão/ocupação/revogação
originais. Próxima slice do plano: T06/UX-02, busca/paginação de comandas staff.
Demais gates permanecem abertos.

## Plano original de investigação

1. Fixar main/deploy e revalidar diferenças, começando pelo PR #98 e UX-03.
2. Reproduzir UX-34 em base descartável, diagnosticando correção/alocação/estorno.
3. Executar protocolo G1 do relatório em vazio/normal/pico, mobile e Android.
4. Priorizar segurança e contexto: drafts, intenção durável, envio financeiro,
   paginação, liberação de mesa e motivo isolado por proposta.
5. Contratar slices de pedido/busca/repetição/guest com specs proprietárias.
6. Contratar produção em lote e ações independentes somente com regras de conflito.
7. Fechar circuito de exceção: deep link, autorização contextual e recuperação.
8. Medir antes/depois em cenários equivalentes e validar no piloto observado.

O plano original acima descreve a entrega documental; a atualização T02 tem
implementação local e validação própria, sem homologação de piloto/deploy.
Fonte operacional: relatório, seções G e H; limitações não desaparecem por
existir teste de aparência ou build bem-sucedido.

## T03a — UX-08: recebimento em dinheiro no POS

1. Contratar intenção CASH na Spec006 e fingerprint físico na012; lifecycle
   sessionStorage na014, separado de estorno UX-22 (T03b).
2. Componente de recebimento preserva envelope antes de fetch, bloqueia workspace
   durante envio/ambiguidade, verifica sessão e usa replay exato + Tab readback.
3. Conferir caixa/tender no replay sem migration ou mudança de snapshots.
4. Testar PostgreSQL, perda real de resposta após commit, replay concorrente,
   rejeição, reload, sessão distinta/revogada, storage falho e mobile360/390/430;
   build/tipos, visual completo e lint sem relaxar critérios.

## T03b — execução do estorno manual recuperável

1. Envelope antes do POST; guard síncrono, campos congelados e retomada explícita.
2. Validar sessão e fingerprint de replay CASH/correção; preservar locks/auditoria.
3. Testar perda após commit/readback, reload, PIN/sessão/storage, divergência e
   concorrência em PostgreSQL; jornadas Web/API360/390/430, visual completo/build.

## T04 — rascunhos locais por destino

1. Substituir carrinho único por mapa Tab→linhas; setter ligado à Tab original.
2. Remover resets em seleção/abertura; manter limpeza da Tab confirmada apenas.
3. Seleção assíncrona bloqueada, reseleção revela e foca título; descarte confirmado.
4. Validar A→B→A, nova Tab, configurações distintas, catálogo alterado, foco,
   pendência e regressões; Web/API/PostgreSQL, mobile360/390/430 e visual completo.

## T05a — plano do recorte staff Web

Hook client para envelope/scope/storage/replay; OrderWorkspace mantém drafts
T04 separados e apresenta retomada fora dos controles bloqueados após reload.
Reutilizar idempotência transacional da API, sem novo efeito financeiro.
Testar resposta perdida/reload/readback, payload congelado, sessão/revogação,
storage inválido/falho e rejeição inicial em mobile360/390/430. Confirmar
Order/Charge/auditoria únicos em PostgreSQL; visual completo, tipos e build.

## T05b — plano mínimo

Acrescentar scope não secreto ao contexto existente; hook guest preserva
intenção usando a credencial já gerida pelo fluxo, sem duplicá-la. Reutilizar
confirm_guest_order e seu replay. Cobrir reload/resposta perdida/readback,
contexto divergente/revogação/bloqueio/storage, Web360/390/430 e PostgreSQL.
Executar visual completo, build/tipos e lint dos arquivos Python alterados.

### T06a
Reutilizar a paginação de 200 registros da API, sem alterar domínio ou projeções financeiras. Compartilhar a navegação da página com o diálogo de histórico; serializar a navegação e descartar respostas de atualização anteriores. Validar mais de 200 registros, erro de página e preservação do rascunho nas duas superfícies em 360/390/430.

### T06b
Adicionar search_label derivado e migração de backfill; filtrar no backend antes do offset, sem extensão PostgreSQL. Web separa texto editado da busca aplicada, reutiliza guard de respostas obsoletas e paginação. Cobrir acentos/caixa/espaços, substring literal, >200, homônimos, sem nome, Venue, erro/concorrência de leitura e rascunho; PostgreSQL, Web/API mobile e suíte visual.

### T06c
Reutilizar TableOccupancy/TabOccupancyAssignment e detalhe autorizado de Tab; acrescentar precondição opcional de contexto ao GET existente, sem novos locks ou mutations. Listagem de ocupação filtra vínculos liberados. AttendanceWeb preserva contexto de retorno e solicita seleção ao workspace já montado, reutilizando seleção serializada e rascunhos por Tab. Validar múltiplas comandas, conflito/vínculo antigo, outro Venue, falha/retry, pendência, foco/retorno e Web/API 360/390/430.

### T06d
Corrigir validade de geração e motivo na API MOVE_LOCATION da Spec 009 antes
de expor o comando no Atendimento Web. Reproduzir as falhas antes do código;
testar neutralidade financeira, replay/autorizações e concorrência com liberação
em PostgreSQL descartável. A próxima slice entrega a escolha/confirmação Web.

Web: componente sempre montado, ActionDialog e tokens existentes, locks de
Atendimento e gateway restrito. Ler origem antes da confirmação; preservar
intenção, verificar sessão/resultado/readback antes de removê-la. Testar rejeição,
storage, sessão, reload/resposta perdida, Web/API PostgreSQL e 360/390/430;
build/tipos e suíte visual completa sem relaxar tolerâncias.

### T07a — carrinho Android
Implementar alternância persistente catálogo/carrinho com estado de scroll separado e detalhes financeiros expansíveis por Tab. Preservar confirmação financeira e intenções pendentes. Validar Compose com catálogo de 146 produtos, callbacks, bloqueios e fonte ampliada; executar unitários, assemble e lint Android. Não fechar os demais critérios T07.

### T07b — liberação Android
Reutilizar AlertDialog e callback existente, capturando mesa/ocupação e mostrando efeitos. Bloquear confirmação com permissão retirada, busy ou ocupação local divergente. Validar cancelamento, confirmação única e mudança de contexto em Compose; unitários/build/lint e regressões PostgreSQL de mesas/guest/ledger.

### T07c — Pedir e Nova comanda Android
Reutilizar TabList e selectTab: Pedir navega para Contas com orientação, sem creation. Nova comanda ganha ação explícita na lista. Distinguir IDs em homônimos, bloquear loading/busy e testar routing/seleção/criação separados, estado vazio e regressões de navegação em emulador. Unitários/build/lint e regressões financeiras PostgreSQL.

### T07d — teclados e parsing Android
Adicionar opções decimal/NumberPassword aos campos financeiros pendentes; corrigir parser compartilhado para gramática explícita e conversão exata em centavos. Testar ponto/vírgula, agrupamento, negativo, letras e limites de Long; callbacks financeiros e InputType no emulador; unitários/build/lint e regressões financeiras PostgreSQL. Não mudar API, revisão nem envelopes.

### T08a — repetir rodada Android
Ler IDs/configuração do snapshot canônico; montar revisão pura com diferenças e bloqueios. Incluir somente após revisão/revalidação, preservando draft e fluxo de nova intenção. Testar configuração, preços, indisponibilidade, legado, cancelamento, mudança durante revisão e callbacks no emulador; unitários/build/lint e regressões PostgreSQL. Web e jornada Android/API completa permanecem gates separados.

### T08b — repetir rodada Atendimento Web
Leitura canônica autorizada de histórico/catálogo, revisão com ActionDialog e inclusão guardada no draft existente. Preservar recuperação e locks de T04/T05; testar diferenças/configuração, falha/legado/inativo, alterações durante revisão e replay com resposta perdida. Executar tipos/build, suíte visual completa e jornadas Web/API PostgreSQL em 360/390/430, sem alterar baseline.

### T08c — repetição guest
Reutilizar reviewRepeatedOrder/ActionDialog e comparadores de GuestScope de T05b. Ler contexto/catalog com token original ao abrir e incluir; proteger revisão contra scope/Tab/token/policy divergentes e consumo/pendência. Validar diferença/legado/configuração, bloqueio/revogação e replay em fixtures e Web/API PostgreSQL 360/390/430, tipos/build e suíte visual completa.

Descoberta T08c: projetar table_ordering_enabled no contexto, pois reads guest deliberadamente ignoram bloqueios de mutation. Testar true/blocked/disabled em API e manter domínio de autorização existente.

### T08d — repetição no PDV Web
Remover a restrição de superfície no guard compartilhado e expor revisão no
histórico do PDV, sem duplicar correções/ações do Atendimento. Reutilizar diálogo,
inclusão e intenção. Proteger recebimento durante leitura/revisão. Testar PDV
360/390/430, inválidos, mudança de catálogo, pendências e Web/API PostgreSQL;
executar tipos/build, regressões financeiras e visual completo sem baseline novo.

### T09a — quantidades guest
Agrupar no draft com identidade de configuração por IDs e nota exata, incluindo
edição e repetição; rejeitar overflow de 99 de forma integral. Usar controles e
tokens existentes, saída acessível e total recalculado em centavos. Manter intenção
imutável e locks; aumento condicionado à disponibilidade/contexto, redução local
para correção. Testar diferentes configurações, limite, preço/disponibilidade,
bloqueio/revogação, resposta perdida/replay e Web/API PostgreSQL 360/390/430.
Executar tipos/build, regressões financeiras e suíte visual completa.

### T09b — busca e categorias guest
Projetar category no GET autorizado existente; reutilizar helpers de apresentação
já aplicados no Atendimento. Filtrar somente a projeção visual, mantendo catálogo
completo para draft/revisão. Busca global por nome, categoria persistente local,
fallback Todos e feedback vazio/contagem. Ação Pedido atual rola/foca região do
draft; sem nova navegação/mutation. Testar 146 itens (143 do CSV versionado + três fixtures existentes), mobile,
configurações, atualização de catálogo, bloqueios/revogação e Web/API PostgreSQL.
Executar Ruff, tipos/build, regressões financeiras e visual completo.

### T10a — acesso mobile ao passe/disponibilidade
Reutilizar tokens e controles existentes em navegação sticky exclusivamente mobile.
Rolar/focar regiões montadas sem mutation; contar snapshot sem inventar zero.
Validar pico com 30 linhas, 360/390/430, ambas estações, retorno, estados vazios/
loading/erro e locks. Executar tipos/build e visual completo sem baseline novo.

### T10b — resumo por configuração
Criar derivação pura da projeção confirmada: assinatura JSON estável sem campos
financeiros, modificadores ordenados, identidade/routing verificados e legado
independente. Exibir CustomizationText existente no resumo. Não tocar mutations.
Cobrir igualdade, diferenças, campos adicionais, legado, preços, ordenação,
catálogo alterado e estados em unitários, fixtures mobile e Web/API PostgreSQL.
Referência V03 mantém dados históricos: documentar divergência de resumo quando
fixture não registra configuração, sem alterar export ou tolerância.

Próxima T10c: implementar verticalmente comando de lote idempotente/transacional
e revisão explícita Web. Nenhum preparo por seleção implícita; revalidar escopo,
configuração/estado/quantidade e autorização no servidor. Testar replay/conflito,
resposta perdida, snapshot obsoleto, concorrência e rollback de falha por linha/
Dispatch em PostgreSQL; conservar auditoria/timestamps/ledger/Payments.


T10c.1: journal por sessão/chave; lock Tab antes de Item também na transição individual; precondições atômicas e recibo por linha. Cobrir replay, autorização, conflitos, concorrência e rollback em PostgreSQL. T10c.2: seleção/revisão e intenção persistida Web.

T10c.2: hook de intenção persistida, ActionDialog de seleção/revisão e resultado por linha. Fixtures testam perda de resposta, readback, sessão, armazenamento, conflito e revisão obsoleta; PostgreSQL/Web real prova replay sem duplicar. Executar tipos/build/visual completo e mobile360/390/430.

T10c.2: diálogo recebe foco de origem explicitamente; leitura pós-recibo tem prioridade sobre refrescos concorrentes. Pendência só é liberada depois de recibo por linha validado e leitura atual. Próxima T10d: investigar e remover bloqueios independentes somente por escopo protegido (UX23); gate amplo continua aberto.

T10d.1: reutilizar validação/envelope/recibo de lote; journal browser de intenções individuais por item, coordenador de leituras pós-comando e botões verificados com lock por ID. Manter legado/lote/disponibilidade conservadores. Testar concorrência, erro de uma linha, estado obsoleto, reload/replay, sessão/storage e mobile em fixtures/Web/API PostgreSQL; visual completo sem relaxar baseline.
T10d.2: lock individual considera IDs do lote persistido; validar envelope e vínculo de sessão do lote antes de enviar item independente. Manter bloqueio global pré-persistência/revisão e demais escopos; testar coexistência/replay e regressões em PostgreSQL e visual completo.
T10d.3: journal AvailabilityCommand, migração, serviço transacional com lock sessão
NO KEY UPDATE e ProductAvailability, validação do opt-in no endpoint existente.
Testar replay/conflito/no-op/rollback/autorização/concorrência em PostgreSQL,
regressões financeiras e catálogo. UI independente somente após contrato validado.

T10d.4: hook de journal por produto com validação estrita de intenção/recibo,
versão capturada e readback serializado existente. Separar disponibilidade do
inert global das ferramentas; manter modificadores/QuickCatalog protegidos.
Verificar vínculo dos journals coexistentes à sessão antes de novo envio.
Validar falhas, coexistência e replay em fixtures/Web/API PostgreSQL, tipos/build
e suíte visual completa; conservar baselines e tolerâncias.
### T11a/T11b — Android Agora
Derivar destino explícito de RecoveryIntent para Tab/task, projetando somente
categoria, estado, captura e resumo seguro. Revalidar storage/sessão/ID antes e
depois da leitura; reutilizar seleção canônica sem POST e preservar drafts ativos.
Extrair painel de recuperação e navegação de filas para testes Compose. Prontos
como padrão/pico, Chamadas preservam ordem canônica e Pendências concentram
evidências/ordens guardadas. Testar callbacks, busy/stale, sessão e payload em
unitários/Compose, build/lint Android; verificar contratos financeiros em PostgreSQL.
Tipos sem endpoint resolutor direto continuam gates explícitos; não inventar API.

T11a/T11b: revisão visual a 200% revelou compressão da linha de entrega e dos filtros. Entrega agora usa coluna; filtros usam coluna acima de fontScale 1.3. Evidências finais e limitações em revalidation.md.

T11c: usar CashGateway.shiftDetail com shiftId do envelope original, revalidar
sessão e envelope após GET, manter snapshot de conferência separado do caixa
operacional e testar navegação/retorno sem mutation, inclusive turno fechado,
falha e outra sessão. Não alterar o contrato nem a regra financeira do backend.

T11d: três consultas mínimas por IDs canônicos e capability, isoladas por Venue;
resolver payment e correction conjuntamente para settlement, sem listar comandas.
Android valida contrato antes de GET da Tab e publica contexto de conferência
separado somente após validar sessão e envelope novamente. Testar autorização,
cross-Venue/cross-Tab, alvos inexistentes/aplicados/encerrados e ausência de efeitos
financeiros, com instrumentação Android/API e matriz de fonte/tamanho.

T12a: estado Record por ID para justificativas, captura imutável no closure existente,
lock durante PIN e limpeza seletiva. Rótulos de apresentação compartilhados para
pagamentos/estornos/fechamento, fallback explícito desconhecido; fixtures com duas
propostas, PIN, cancelamento e autoaprovação. Tipos/build/visual completo obrigatório.

T12b.1: resolver shift pela API autenticada existente, conferir IDs/caixa antes da
seleção, validar preferred shift em load e impedir fallback. Query via location no
efeito inicial; foco em resumo acessível após leitura. Links por tipo canônico e
origem allowlist; fixtures de autorização/falha/histórico, build/tipos/visual completo.

T12b.2: nova conferência Web read-only com resolver existente protegido por
refund.create e GET Tab; comparar alvos e identidade de sessão antes/depois,
invalidar respostas antigas na revogação. Link PAYMENT no alerta com origem
local validada; foco após leitura e fixtures mobile/falhas sem mutation financeira.

T12b.3: componente read-only para item/correção reutiliza padrão de conferência
Payment, resolvers existentes e detalhe Tab, com validação de identidade e sessão.
Links em alerta e estornos; fixtures incluindo estados históricos, divergência e
sessão; build/tipos/visual completo sem mudar baseline.

Paginação compacta (14/10/2026): reutilizar OperationalIcon e Button secundário, com setas de 44 px e status central. Manter handlers e bloqueios; conferir mobile, busca, rascunhos e histórico nos testes existentes.

Contas: limitar apresentação a 10 resultados e avançar offset em 10 quando a leitura tiver mais itens; usar next_offset canônico no fim. Preservar PDV com 200 e busca global.

## T08e — Plano de execução

1. Expandir a revisão pura para aceitar quantidades por ID da linha histórica,
   rejeitar IDs arbitrários, todos desmarcados, valores fora de 1–99 e overflow.
2. Implementar checkbox e editor ± / input numérico nas revisões Android Compose
   e Web compartilhada (Atendimento, PDV, guest), com subtotal/contagem dinâmicos.
3. Preservar as leituras e guards existentes; confirmar seleção somente no draft
   da Tab/GuestScope original. Guest reconsulta contexto antes de agrupar.
4. Validar com testes unitários de seleção, instrumentação Android, integração
   Web/API em 360/390/430, visual e replay. Não alegar validação não executada.
