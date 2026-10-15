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

## Revisão de fluxo — Mesas e comandas unificadas
Solicitação subsequente: unir Mesas/Contas e usar pop-up para o cardápio da comanda.
Esta seção substitui a navegação separada do primeiro experimento nesta branch.

- Entrada principal “Mesas e comandas”, sem aba Contas. Agora preserva chamadas/entregas.
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
