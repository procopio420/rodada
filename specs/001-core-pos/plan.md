# Plan — Spec 001

## Slice 1 — Foundation

Venue, staff roles, catalog, products, `ProductAvailability` e seed de demo.

Separar desde o início ativação administrativa (`Product.active`) de disponibilidade operacional (`AVAILABLE | UNAVAILABLE`).

## Slice 2 — Tabs + Orders

Criar Tab anônima ou com `display_label`, criar Order, adicionar itens e snapshot de preço.

O modelo de Tab não deve exigir mesa/Customer e deve permanecer compatível com múltiplos identificadores futuros.

## Slice 3 — Ledger + Payments

Charges derivadas, payments manuais, exposure e fechamento.

## Slice 4 — Fulfillment + station controls

Estados/timestamps de OrderItem, tela operacional simples de Bar/Cozinha e controle de disponibilidade dos produtos da estação.

Toda confirmação de Order revalida disponibilidade no servidor; mudança posterior não altera OrderItem já confirmado.

## Slice 5 — Optional location context

Suporte opcional a ServicePoint/TableOccupancy sem acoplar ledger à mesa e com múltiplas Tabs no mesmo contexto físico.

## Slice 6 — CashShift + audit

Caixa básico, cancelamentos, ajustes e auditoria.

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

### T06a
Reutilizar a paginação de 200 registros da API, sem alterar domínio ou projeções financeiras. Compartilhar a navegação da página com o diálogo de histórico; serializar a navegação e descartar respostas de atualização anteriores. Validar mais de 200 registros, erro de página e preservação do rascunho nas duas superfícies em 360/390/430.

### T06b
Adicionar search_label derivado e migração de backfill; filtrar no backend antes do offset, sem extensão PostgreSQL. Web separa texto editado da busca aplicada, reutiliza guard de respostas obsoletas e paginação. Cobrir acentos/caixa/espaços, substring literal, >200, homônimos, sem nome, Venue, erro/concorrência de leitura e rascunho; PostgreSQL, Web/API mobile e suíte visual.

### T06c
Reutilizar TableOccupancy/TabOccupancyAssignment e detalhe autorizado de Tab; acrescentar precondição opcional de contexto ao GET existente, sem novos locks ou mutations. Listagem de ocupação filtra vínculos liberados. AttendanceWeb preserva contexto de retorno e solicita seleção ao workspace já montado, reutilizando seleção serializada e rascunhos por Tab. Validar múltiplas comandas, conflito/vínculo antigo, outro Venue, falha/retry, pendência, foco/retorno e Web/API 360/390/430.

### T07a — Android
Reutilizar OrderCart e os callbacks existentes; alternar a revisão por controle persistente, manter busca/posição do catálogo e detalhes contábeis expansíveis sem alterar PaymentDialog. Validar navegação, bloqueios e estados financeiros com Compose, unitários, assemble e lint; aparelho e API permanecem gates distintos.

### T07c — destino explícito Android
AttendanceNavigation envia Pedir para Contas; callback apenas ativa orientação. Reutilizar TabList/selectTab, filtrar fechadas no modo pedir e dar ação separada Nova comanda. Guard loading/busy conserva estados. Testes verificam routing real da navegação e callbacks distintos da lista, vazio/homônimos, mais regressões financeiras. Não ampliar busca/paginação nem persistência Android.

### T08a — repetição Android
Revisão local por IDs/snapshot, catálogo atual, inclusão guardada no draft e confirmação existente com nova intenção. Testes de regressão de snapshots/replay em PostgreSQL e Compose com fonte ampliada; ações do diálogo em coluna para preservar alcance.

### T08b — repetição staff Web
Reutilizar rascunhos por Tab e useOrderIntent, ler detalhe/catálogo antes de revisar com ActionDialog e bloquear contextos divergentes. Conferir preço/configuração, falha, legado, inclusão única e preservação de outras Tabs. Jornada real PostgreSQL com resposta perdida/replay em 360/390/430, tipos/build e visual completo.

### T08d — revisão compartilhada no PDV
Habilitar guard de repetição nas duas superfícies de OrderWorkspace, exibir
histórico/revisão no PDV e nomear região do rascunho. Bloquear recibo durante
leitura/revisão e repetição durante personalização. Reutilizar autorização,
catálogo e intenção sem mutation nova. Testes PDV espelham os critérios comuns,
acrescentam recebimento ambíguo e encerramento durante revisão. Journeys reais
PostgreSQL validam preço atual, snapshot antigo, drafts por Tab e replay.


T10c.1: journal por sessão/chave; lock Tab antes de Item também na transição individual; precondições atômicas e recibo por linha. Cobrir replay, autorização, conflitos, concorrência e rollback em PostgreSQL. T10c.2: seleção/revisão e intenção persistida Web.

T10c.2: hook de intenção persistida, ActionDialog de seleção/revisão e resultado por linha. Fixtures testam perda de resposta, readback, sessão, armazenamento, conflito e revisão obsoleta; PostgreSQL/Web real prova replay sem duplicar. Executar tipos/build/visual completo e mobile360/390/430.

T10c.2: diálogo recebe foco de origem explicitamente; leitura pós-recibo tem prioridade sobre refrescos concorrentes. Pendência só é liberada depois de recibo por linha validado e leitura atual. Próxima T10d: investigar e remover bloqueios independentes somente por escopo protegido (UX23); gate amplo continua aberto.

T10d.1: reutilizar validação/envelope/recibo de lote; journal browser de intenções individuais por item, coordenador de leituras pós-comando e botões verificados com lock por ID. Manter legado/lote/disponibilidade conservadores. Testar concorrência, erro de uma linha, estado obsoleto, reload/replay, sessão/storage e mobile em fixtures/Web/API PostgreSQL; visual completo sem relaxar baseline.
T10d.2: lock individual considera IDs do lote persistido; validar envelope e vínculo de sessão do lote antes de enviar item independente. Manter bloqueio global pré-persistência/revisão e demais escopos; testar coexistência/replay e regressões em PostgreSQL e visual completo.
T10d.3: journal AvailabilityCommand, migração, serviço transacional com lock sessão
NO KEY UPDATE e ProductAvailability, validação do opt-in no endpoint existente.
Testar replay/conflito/no-op/rollback/autorização/concorrência em PostgreSQL,
regressões financeiras e catálogo. UI independente somente após contrato validado.
## T10d.4 — disponibilidade Web por produto (Spec026)

Reutilizar comando versionado de disponibilidade e coordenador de readback da
produção. Journal por produto/sessão antes do POST; recibo validado antes de
remover pendência. Separar controles de disponibilidade das barreiras de
configuração/legado e verificar sessão dos journals coexistentes. Evidências e
limites em specs/026-operational-ux-friction/revalidation.md.
