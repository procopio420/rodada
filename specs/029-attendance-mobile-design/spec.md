# Spec 029 — Experimento de UX mobile no Atendimento Web

## Objetivo e escopo
Melhorar a leitura de Mesas, Cardápio e Conta em `/attendance`, preservando
Spec 024 (`specs/024-attendance-web`) e Spec 027 (`specs/027-table-service-claim`).
Branch de experimento: `codex/ux-teste-mobile`. A primeira slice foi somente Web;
o port Android nativo autorizado posteriormente segue o contrato abaixo.
A referência externa em vídeo não pôde ser acessada; não há alegação de reprodução.

## Comportamento
- Mesas em grade com número, ícone, estado textual, zona e contagem canônica de
  comandas abertas. Expandir mantém as ações atuais. Filtro local por estado e busca
  podem ser combinados; nenhum resultado difere de nenhuma mesa cadastrada.
- Cardápio usa ProductIcon publicado/fallback existente, nome completo, preço,
  disponibilidade e quantidade no rascunho. Toque mantém adição/configuração atual.
- Atalhos Cardápio, Pedido atual e Conta levam às regiões da comanda selecionada,
  sem esconder o rascunho nem criar nova etapa. Resumo do rascunho acompanha a
  navegação e é explicitamente separado dos valores já registrados.
- Itens confirmados mostram preço unitário/subtotal apenas quando a API fornece
  o preço histórico; nunca usar preço atual do catálogo. Conta mantém BillSummary
  e suas regras; saldo canônico ganha destaque sem somar o rascunho ao consumo.

## Invariantes e fora de escopo
Sem mudanças em API, permissões, autenticação, pagamentos, fechamento, descontos,
idempotência ou persistência. Manter confirmações destrutivas, recuperação, limites
de quantidade, separação Table/Tab e estados loading/erro/desatualizado existentes.
Sem dependências novas, dados de produção inventados ou alterações no restante do PDV.

## Aceite
Ver [acceptance.md](acceptance.md), [plan.md](plan.md) e [tasks.md](tasks.md).

## Ajuste dos filtros de mesa — 2026-10-15

Os filtros de estado devem ficar integralmente visíveis, sem faixa de rolagem
horizontal. Usar grade de duas colunas no celular e três a partir do breakpoint
desktop existente. Permitir quebra de rótulos, preservar contagens, estado ativo,
foco e alvos de pelo menos 44px. Não mudar seleção nem regras de domínio.

## Revisão de fluxo — Mesas e comandas unificadas
Solicitação subsequente: unir Mesas/Contas e usar pop-up para o cardápio da comanda.
Esta seção substitui a navegação separada do primeiro experimento nesta branch.

- Entrada principal “Mesas e comandas”, sem aba Contas. Agora preserva chamadas/entregas.
  A busca conjunta inclui comandas sem mesa e revela automaticamente seus resultados.
- Busca encontra mesa e nome/referência de suas comandas. Expandir mesa revela
  comandas abertas e a ação contextual Nova comanda; selecionar uma comanda só
  abre seu pop-up após leitura canônica com table_id/occupancy_id.
- Nova comanda parte da mesa escolhida: livre usa service/open-tab; ocupada usa
  occupancy/tabs/open com geração. Conservar a mesma intenção no resultado incerto.
  Venue com serviço contextual desativado mantém ocupação/associação legadas;
  criação sem mesa continua acessível sem inventar vínculo atômico inexistente.
- Comandas fora das ocupações listadas ficam na mesma área, em “Outras comandas”.
- Pop-up persistente contém apenas a comanda escolhida e seus atalhos
  Cardápio/Pedido atual/Conta; não exibe a lista global nem formulário de criação
  de outra comanda. Ao abrir, posiciona o cardápio para seleção rápida.
- Fechar por Voltar ou Escape preserva rascunhos e devolve foco à origem. Reabrir
  A, abrir B e voltar a A conserva seleções isoladas. Componente não desmonta ao fechar.
- Modal não fecha enquanto leitura/mutação, confirmação incerta, correção ou diálogo
  filho estiverem ativos. Reload com operação pendente revela recuperação no pop-up,
  bloqueando troca de destino e preservando chave/corpo existentes.
- Histórico, personalização, confirmação de descarte/remoção/fechamento continuam
  disponíveis com foco contido; mensagens de erro aparecem na camada visível.
- Sem mudanças em contratos de backend, flags, permissões ou regras financeiras.

Validação: fixtures equivalentes antes/depois, 360/390/430/1280, foco/Escape,
rascunhos A/B, leitura negada, indisponível, abertura contextual/incerta e reload
com confirmação pendente. Gate de integração real e operação no bar permanece externo.

## Port Android nativo — 2026-10-14

Fluxo: Mesas e comandas → expandir mesa → selecionar/criar explicitamente Tab →
janela nativa de contexto → Cardápio / Pedido atual / Conta → Voltar à origem.
Agora e Caixa continuam disponíveis; remover a navegação duplicada Contas.

- A navegação mantém o botão central **+ Pedir** entre Agora e Mesas; ele abre um
  seletor rápido de comandas abertas, com busca, e não envia pedido nem cobra
  nada ao tocar. Criar comanda sem mesa é uma ação explícita no seletor.
- Histórico de comandas fechadas é lido sob autenticação do Venue, sem exigir
  permissão de reabertura, somente ao abrir Histórico (fora do refresh recorrente).
- Entrada padrão Mesas e comandas, com busca por mesa/zona/nome/referência de Tab,
  filtros combináveis por estado e grade adaptável (uma coluna com fonte ampliada).
  Expandir revela operações existentes e comandas, preservando QR/generation,
  responsabilidade, limpeza e confirmações. Outras comandas ficam na mesma área.
- A janela nativa abre só após leitura canônica autorizada; Cardápio é a entrada.
  Pedido atual mostra todas as linhas, independente dos filtros do catálogo;
  Conta concentra saldo, recebimentos, histórico, correções e operações existentes.
  Valores do rascunho nunca são somados ao saldo canônico.
- Voltar fecha o contexto e conserva draft em memória por Tab/sessão, incluindo
  configurações e IDs de linha. A/B/A não mistura itens. Logout/troca de sessão
  descarta drafts não submetidos; morte do processo não promete restaurá-los.
  Intenções submetidas continuam no armazenamento cifrado existente e prevalecem
  sobre drafts. Nunca mudar payload/UUID/sessão nem executar comando ao navegar.
- Bloquear saída/troca durante leitura, mutação, pagamento/ordem ambígua ou intenção
  de mesa pendente. Filhos de personalização/pagamento/correção preservam suas
  confirmações. Exibir erros na camada visível; reabrir recuperação no alvo original.
- Produtos têm nome completo, preço, disponibilidade, quantidade e personalização.
  Reduzir produto com várias configurações leva à revisão integral. Não gerar nova
  identidade visual nem adicionar dependências; ícone sem asset nativo usa fallback.
- Estados: carregando, vazio real, busca sem resultado, negado, desatualizado,
  indisponível, confirmação incerta, sucesso canônico e sessão divergente.
  Toque >=48dp, Back nativo, rolagem/IME, 360/390/430dp e fontScale 1/2.

Exceção explícita de recuperação: correção/estorno incertos podem usar “Conferir
pendências” para retornar à fila Agora e abrir a consulta do registro original.
Essa transição não remove intenção, não confirma resultado nem executa replay;
draft não submetido permanece por Tab. A consulta excepcional é exibida dentro
da janela nativa quando há Tab selecionada, e seu retorno volta à fila preservada.
Pedidos/pagamentos ambíguos mantêm o bloqueio e a reconciliação original.

Sem mudanças de API, domínio, permissões, ledger, persistência de recovery ou
providers. Reutilizar Specs 014/026/027; não copiar HTML nem redesenhar o restante
do produto. Risco R3 no isolamento dos drafts/contextos: revisão independente
obrigatória antes de recomendar integração, sem merge/deploy autorizado.

## Simplificacao dos filtros — 2026-10-15

A pedido do operador, esta decisao substitui a grade de filtros acima: remover
os filtros de estado do Atendimento Web. Manter busca por mesa/comanda, todos
os estados visiveis nas mesas e os vazios/erros existentes. Sem mudar Android.

## Mesa em popup — 2026-10-15

Selecionar uma mesa abre janela modal nativa HTML com titulo Mesa + identificador,
estado, comandas e acoes existentes. A grade nao expande nem muda sua geometria.
Voltar/Escape devolve foco ao botao da mesa. Selecionar uma Tab abre o workspace
existente sobre a janela da mesa; ao voltar, a lista contextual continua disponivel.
Preservar confirmacoes filhas, permissoes, erros visiveis e bloqueio de saida durante
operacao em andamento/ambigua. Sem mutacao ao abrir/fechar. Estados sem comandas,
indisponivel, loading e falha seguem os contratos atuais. Web apenas.
Aceite: 360/390/430/1280, teclado/foco, mesa livre/ocupada, filhos, A/B/A,
leitura negada e ACK perdido sem relaxar recovery.

## Clique fora da mesa — 2026-10-15

O popup de mesa fecha por clique no fundo externo, com foco devolvido a mesa.
Clique dentro, inclusive espacos vazios, nao fecha. Nao fechar durante operacao
em andamento ou ambigua. Dialogos filhos preservam seus bloqueios e confirmacoes.

## Alinhamento Android da tela de mesas — 2026-10-15

Escopo visual nativo: aproximar a tela de mesas da Web atual, sem alterar catalogo,
pagamentos ou recovery. Remover filtros, mover navegacao principal para o topo,
mostrar nome canonico do Venue no cabecalho, compactar historico e agrupar outras
comandas sob abertura explicita. Cartoes em duas colunas (uma com fonte ampliada),
fundo Control e borda superior semantica: AVAILABLE Success, OCCUPIED Info,
DIRTY/CLEANING Amber, OUT_OF_SERVICE Danger, desconhecido Muted; texto obrigatorio.
Toque na mesa abre Dialog nativo rolavel com TableCard existente. Back/toque fora
fecha apenas quando nao ha loading/submitting/intencao pendente; filhos mantem
confirmacoes. Preservar drafts, capabilities, callbacks e comandos existentes.
Aceite: emulador, 360/390/430dp e fonte 1/2, UI de estados em fixture descartavel,
clique/Back, build/JVM/lint e Compose pertinente; sem alegar paridade global.

## Regressao: nova Tab em mesa livre no Android — 2026-10-15

O cliente HTTP deve aceitar a rota existente service/open-tab usada por
openFirstTableTab. A allowlist atual omite essa rota e falha localmente depois
de preservar a intencao, bloqueando navegacao. Corrigir apenas a rota permitida;
manter payload/chave/sessao, bloqueios e reconciliacao existentes. Aceite: HTTP
real local recebe a rota e corpo original no envio/replay; rotas alheias seguem
rejeitadas. Recuperar a intencao local existente sem apagar storage nem criar
nova chave. Mudanca R3 de recovery exige revisao independente.

## Ajuste operacional de limpeza — 2026-10-15

DIRTY oferece Concluir limpeza diretamente, conforme adendo da Spec004.
Liberacao confirmada retorna a lista DIRTY; limpeza confirmada retorna AVAILABLE.
Nao mostrar Organizar mesa ou acoes de comanda no popup DIRTY/CLEANING. Voltar/Back
permanece. Nao criar inicio de limpeza ficticio. Falha conserva contexto.

## Nome operacional obrigatorio em novas comandas staff — 2026-10-15

No Atendimento Android/Web, o campo Nome ou apelido fica sempre visivel, obrigatorio
apos trim, max120; sem toggle de exibir/ocultar. Abrir desabilitado para vazio/espacos.
Aplica-se a mesa livre, ocupada e abertura staff sem mesa. Nome nao exige cadastro,
Customer, CPF ou identificacao civil. Comandas existentes sem nome sao preservadas.
API staff /tabs/ exige display_label valido; abertura contextual rejeita novas
intencoes sem nome, mas replay de recibo antigo com corpo/chave originais continua
valido. Nao alterar payload de intencao ja submetida nem forcar nome num replay.
Guest/domino interno nao passa a exigir identidade. Sem migration.
