# Tasks — Spec 026

## Entrega documental

- [x] Versionar relatório de 35 achados e navegação real na demo.
- [x] Separar guidance operacional da paridade visual da Spec 023.
- [x] Registrar que PR #98 altera a base do achado UX-03.
- [x] Definir prioridades, dependências e gates futuros sem declarar implementação.

## Execução por tarefas — 12/10/2026

Base conferida: `main` / `origin/main` em `ad5d64f`, após pull fast-forward.
O audit continua histórico: PR #98 e `0bd28d0` alteraram produção e atendimento.
Os checks documentados na Spec 025 não são PASS automático da Spec 026.
Estado atual: T01 concluída; recortes locais documentados abaixo, incluindo T10a/T10b/T10c/T10d.1/T10d.2/T10d.3/T10d.4. Próxima tarefa do plano T11; critérios amplos não comprovados e gates externos permanecem abertos.
Demais tarefas e gates amplos permanecem pendentes. Evidência em [revalidation.md](revalidation.md).

Cada tarefa deve registrar achados, spec proprietária, antes/depois, fora de
escopo, testes e evidência. Atualizar contrato e aceite antes do código.
Marcar concluída somente com evidência; dependência externa fica explicitamente
aberta. Não é necessário concluir toda a matriz de campo para iniciar uma slice
local segura. Não implementar todas as frentes numa única alteração.

### T01 — Atualizar o diagnóstico na main integrada (primeira tarefa)
- [x] Conferir branch, alterações existentes, commit e status da versão publicada separadamente (deploy não verificado).
- [x] Ler Spec 025 de coesão, Spec 017, ADR 0017 e mudanças de `0bd28d0`.
- [x] Revalidar UX-03, UX-06/35 e UX-34 em ambiente local descartável.
- [x] Criar `revalidation.md`: para cada UX-01–35, registrar presente, parcial,
  resolvido com evidência ou não verificado; apontar arquivos e testes existentes.
- [x] Para UX-03, verificar Iniciar preparo → Pronto; não restaurar Aceitar nem
  iniciar automaticamente. Para UX-34, distinguir remoção parcial de quantidade
  de correção após recebimento parcial: são problemas diferentes.
- [x] Saída: lacunas comprovadas e menor próxima slice definida; nenhuma medição
  histórica apresentada como resultado atual ou como deploy verificado.

### T02 — Correção após pagamento parcial (UX-34)
Dependência: T01. Proprietárias: 017, 006 e 011.
- [x] Reproduzir em PostgreSQL descartável: consumo 3800 centavos, recebimento
  de teste 1000, correção de item de 800; inspecionar alocações e disposição.
- [ ] Contratar casos sem valor a devolver, estorno positivo, desconto/serviço,
  cancelamento parcial, item preparado e concorrência; investigar a causa.
- [x] Implementar a menor lacuna comprovada (recorte sem devolução), com próxima ação executável;
  não emitir estorno de zero nem contornar revisão/autorização exigida.
- [x] Testar ledger, saldo, auditoria, replay, concorrência e Payment preservado no recorte;
  ligar revisão ao correction/tab correto e revalidar jornada Web/API.

Recorte T02 entregue (Spec 017 UX-34): cancelamento integral NEW/ACCEPTED com
recebimento parcial e zero a devolver. Revisão autorizada sem Refund, rollback
se saldo/estágio mudou, compatibilidade com zero legado, replay e concorrência;
jornada Web/API/PostgreSQL e responsividade verificadas. Casos pagos de quantidade
parcial e produção avançada continuam exigindo seus fluxos; nenhum gate amplo
acima é automaticamente concluído. Continuação: T03a/UX-08, T03b/UX-22 e T04/UX-06/35 entregues; próxima slice T05/UX-07.

### T03 — Recebimento POS e estorno ambíguo (UX-08/22)
Dependência: T01; coordenar com T02. Proprietárias: 006, 012 e 014.
- [x] Separar recebimento e estorno em duas slices verificáveis.

**T03a — UX-08 / CASH POS (entregue localmente)**
- [x] Intenção persistida antes do envio, ref síncrona contra duplo toque e
  payload/chave congelados durante ambiguidade; replay e readback canônicos.
- [x] Conferir caixa/tender no replay sem reescrever Payment/movimento/snapshot;
  concorrência PostgreSQL produz um único efeito e auditoria.
- [x] Resposta perdida após commit real, reload na mesma aba/sessão, rejeição
  inicial, readback indisponível, sessão distinta/revogada e storage falho testados.

Retomada cobre apenas a mesma aba com storage íntegro. Outras sessões recebem
revisão bloqueada sem adoção; resolução gerencial/fechar aba não estão entregues.
Código, comandos e evidências em [revalidation.md](revalidation.md).

**T03b — UX-22 / estorno positivo manual (entregue localmente)**
- [x] Congelar Payment/correction, valor, caixa, motivo e chave antes do envio
  do estorno; preservar autorização e PIN recente, sem alterar a revisão T02.
- [x] Recuperar o mesmo Refund após resposta perdida/readback falho; contratar
  retomada e sessão sem adotar intenção antiga nem criar estorno substituto.
- [x] Testar payload divergente, saldo/refundable, replay, concorrência e Payment
  intacto em PostgreSQL; Web/API e mobile360/390/430, visual/build/tipos/lint.

T03b cobre endpoints manuais na mesma aba/sessão com storage íntegro. Provider,
fechar aba e resolução entre sessões/aparelhos permanecem abertos.
Evidência T03b:72 testes PostgreSQL,8 Web/API e258 visuais completos naquela slice.

### T04 — Draft por comanda e seleção previsível (UX-06/35)
Dependência: T01. Proprietárias: 001 e 025-pilot-cohesion-dev-tools.
- [x] Preservar draft por destino na troca, abertura e retorno; reselecionar
  abre workspace utilizável. Recolher fica em controle explícito.
- [x] Definir descarte explícito e recuperação de edição local, sem transportar
  produtos para outra comanda; separar draft de intenção já enviada.
- [x] Testar A → B → A, nova comanda, configurações distintas, foco e pendência;
  manter categorias, busca, histórico e cancelamento parcial integrados.

T04 entregue no workspace montado: rascunhos em memória por Tab, descarte
confirmado, reseleção visível e seleção serializada. Não cobre reload, outra aba
ou retomada de pedido enviado. Próxima slice: T05/UX-07, primeiro envelope e
recuperação do mesmo pedido staff Web após resposta perdida/reload; guest exige
seu contrato de sessão/ocupação e validação próprios. Evidência em revalidation.md.

### T05 — Recuperação durável de pedidos Web/guest (UX-07)
Dependências: T03/T04 para contratos compartilhados. Proprietárias: 001, 004 e 014.
- [x] Definir envelope mínimo, armazenamento e lifecycle por Venue/sessão/comanda;
  não persistir credenciais nem adotar intenção de outra sessão/ocupação.
- [x] Retomar consulta do mesmo payload/chave após reload antes de liberar novo
  pedido; testar commit sem resposta, revogação guest e armazenamento indisponível.

**T05a — staff Web (recorte local)**
- [x] Envelope antes do POST e retomada explícita do mesmo pedido na mesma aba/sessão.
- [x] Gateway original preservado; sessão/revogação/storage/readback não adotam nem duplicam pedido.
- [x] PostgreSQL concorrente, Web/API360/390/430 e regressões locais registradas.

**T05b — guest (recorte local)**
- [x] Envelope sem credencial, contexto original e retomada explícita após reload.
- [x] Sessão/ocupação/generation/Tab divergentes, revogação/bloqueio/storage/readback não adotam intenção.
- [x] Quatro jornadas guest reais; efeitos únicos conferidos no banco.

T05 aceita no recorte de reload na mesma aba/sessão/visita. Drafts não enviados
após reload, fechar aba e outra sessão/aparelho não foram implementados.
Evidência final T05b:296 visuais,8 Web/API/PostgreSQL,39 API PostgreSQL,
build/tipos/Ruff/diff PASS; ver revalidation.md. Próxima slice do plano: T06/UX-02,
busca/paginação staff; movimento de mesa permanece separado.

### T06 — Busca, paginação e contexto da mesa (UX-02/12/18/19/24)

- [x] T06d/API: rejeitar geração de destino divergente e preservar motivo na auditoria; neutralidade financeira, replay e corrida com liberação verificados em PostgreSQL.
- [x] T06d/Web: movimento distinto de associação, gateway exclusivo, confirmação explícita e recuperação na mesma aba/sessão; Web/API PostgreSQL, 360/390/430 e suíte visual completa 331 PASS.

Recortes T06a/T06b: paginação e busca global por apelido entregues localmente; código e Android permanecem abertos; entrada pela mesa Web entregue no recorte T06c.
- [x] Validar entrada direta pela mesa Web, retorno, conflito e rascunhos em 360/390/430 (T06c; 318 testes visuais e jornada Web/API PostgreSQL PASS).
- [x] Validar busca global normalizada, homônimos e rascunhos nas duas superfícies (T06b; 310 testes visuais e jornada PostgreSQL PASS).
- [x] Validar navegação além de 200, erro e rascunho nas duas superfícies/histórico (T06a; evidência local em revalidation.md).
Dependência: T04. Proprietárias: 001, 004 e 009.
- [ ] Primeiro resolver paginação/busca com mais de 200 comandas, homônimos,
  sem nome, código e mesa; não tratar primeira página como inventário completo.
- [ ] Depois abrir comanda diretamente pela mesa e retornar ao contexto de origem.
- [ ] Contratar movimento A → B separado de transferência financeira; preservar
  ocupação, identidade, saldo, permissões e conflitos concorrentes.

### T07 — Pedido Android e proteções locais (UX-01/10/11/16/17)
Dependência: T01; reutilizar contratos de T04/T06. Proprietárias: 001, 004, 006 e 023.
- [x] T07a: acesso persistente ao carrinho Android e detalhes financeiros expansíveis; conferência de pagamentos preservada. Evidência local em revalidation.md.
- [x] T07c: distinguir Nova comanda de Pedir; seleção explícita por ID na lista local de contas abertas, sem criação automática. Categorias/busca/paginação Android e ergonomia completa continuam abertas.
- [x] T07b: confirmar liberação Android com mesa e efeito de revogação; cancelar não chama mutation. Mudança da ocupação local, busy e permissão invalidam confirmação; disputa após snapshot continua gate separado.
- [x] T07d: teclado decimal/NumberPassword nos campos do recorte; parse exato de centavos com vírgula/ponto, rejeição de texto/sinais/overflow e validações de conferência. Matriz de emulador e checks PASS; IME físico continua aberto.
- [ ] Verificar fonte ampliada, foco, teclado e alcance em Android; registrar
  emulador e aparelho separadamente e deixar gate físico aberto se indisponível.

### T08 — Repetir rodada (UX-13)
Dependências: T04/T05. Proprietárias: 001 e 010.
- [x] T08d/PDV Web: revisão compartilhada, draft por Tab, bloqueio de personalização/recebimento e nova intenção recuperável. 371 visuais, três jornadas PostgreSQL 360/390/430, 43 financeiros, tipos/build PASS. Próxima: T09a/UX-14.
- [x] T08c/Guest: revisão atual, releitura da visita/catálogo e bloqueio de mesa; draft e intenção recuperável preservados. 359 visuais, quatro jornadas Web/API PostgreSQL, 60 testes API/PostgreSQL, tipos/build/Ruff PASS. Web POS permanece aberto.
- [x] T08b/Atendimento Web: revisão canônica, diferenças/bloqueios, inclusão única preservando drafts e nova intenção recuperável. 342 visuais, 3 jornadas reais 360/390/430, 43 PostgreSQL, tipos/build PASS. Guest/Web POS permanecem abertos.
- [x] T08a/Android: revisão explícita do histórico, IDs/configuração, preços atuais e inclusão guardada preservando draft. 67 unitários, 60 execuções Compose e 61 PostgreSQL PASS; Web/guest e journey Android/API seguem abertos.
- [x] Copiar histórico para novo draft com nova intenção; revalidar preço,
  variant/modifiers, disponibilidade e informar diferenças antes da confirmação.
- [x] Testar item alterado/inativo, configurações diferentes e replay sem duplicação.

Critérios locais T08a–T08d comprovados. Jornada Android/API integral, publicação,
aparelho e medição humana permanecem gates abertos em T14/revalidation.

### T09 — Guest: quantidade e descoberta (UX-14/15)
Dependência: T05. Proprietárias: 004, 010 e 023.
- [x] T09a: quantidades e agrupamento somente de configuração idêntica; limite 99 sem perda de unidades. 385 visuais, três jornadas Web/API PostgreSQL 360/390/430, 60 PostgreSQL, tipos/build PASS.
- [x] T09b: busca/categorias e pedido acessível com 146 produtos de fixture (143 CSV + três fixtures existentes). 393 visuais, três jornadas reais 360/390/430, 61 PostgreSQL, Ruff/tipos/build PASS.
- Criação da comanda no primeiro envio não escolhida nesta execução; fora de
  T09a/T09b. Exige contrato próprio e idempotência se escolhida futuramente.
- [x] Disponibilidade alterada, bloqueio/revogação e mobile 360/390/430 testados localmente em T09a/T09b; publicação/aparelho/medição humana seguem T14.

### T10 — Produção no pico (UX-03/04/05/23)
Dependência: T01; iniciar acesso a passe/disponibilidade antes de lote.
Proprietárias: 001, 003, 019 e 023; atualizar design system se alterar seu contrato.
- [x] T10a: início manual e acesso mobile ao passe/disponibilidade com fila de30 linhas;6 Web/API PostgreSQL,401 visuais completos +1 teste de pendência,42 PostgreSQL, tipos/build PASS.
- [x] T10b: resumo por configuração confirmada e legado independente;5 unitários,6 Web/API PostgreSQL,47 PostgreSQL,408 visuais completos, tipos/build/diff PASS. Contrato futuro de lote registrado, sem mutation em lote entregue.
- [x] T10c: implementar lote explícito por configuração/estação/estado compatíveis,
  com autoria, replay, precondições, conflitos e resultado por linha; não inferir preparo real.
- [x] T10c.1: API canônica de lote, replay, locks Tab→Item, precondições e rollback. 96 PostgreSQL PASS; Web ainda sem seleção/lote.
- [x] T10c.2: seleção/revisão Web e intenção persistida por sessão; resposta perdida, conflitos e mobile 360/390/430. 425 visuais completos +1 volume,6 Web/API PostgreSQL,49 PostgreSQL,5 unitários, tipos/build/diff PASS.
- [x] T10d.1: intenções individuais por item verificável;438 visuais,6 Web/API PostgreSQL,49 PostgreSQL,5 unitários,tipos/build/diff PASS.
- [x] T10d.2: item fora da seleção de lote pendente independente;447 visuais,38 focados,6 Web/API PostgreSQL,49 PostgreSQL,5 unitários,tipos/build/diff PASS.
- [x] T10d.3: API disponibilidade idempotente/versionada;65 Django +16 pytest PostgreSQL PASS,checks/migração/lint novo PASS. UI permanece protegida.
- [x] T10d.4: disponibilidade Web por produto com intenção/versão/recibo e recuperação; produtos e itens verificáveis independentes, demais barreiras preservadas. 465 visuais completos,6 Web/API PostgreSQL,60 Django PostgreSQL,5 unitários,tipos/build/diff PASS. Próxima tarefa T11; gates amplos continuam abertos.
- [ ] T10d: permitir ações independentes somente com concorrência por escopo protegido;
  testar snapshot obsoleto, falha parcial, customização e indisponibilidade.

### T11 — Entregas, pico e recuperação Android (UX-26/27/28)
Dependências: T05/T07. Proprietárias: 003, 014 e 018.
- [ ] Pendência abre sua operação original sem substituir payload ou sessão.
- [x] Prontos/Chamadas/Pendências com prioridade e nomenclatura coerentes (T11b local; evidência em revalidation.md).
- [ ] Investigar obrigatoriedade de taps antes de alterar entrega; inferência
  conserva source/confidence/provenance e ação manual por exceção.

- [x] T11a local: contexto canônico de pedido/pagamento/preço/estrutura e task de entrega, sem mutation na navegação, preservando intenção e sessão.
- [x] T11c local: conferência do turno original de caixa, sem mutation ou troca da seleção operacional; registros preservados e sessão revalidada.
- [ ] T11a restante: resolução canônica de correção/estorno; T11/UX26 amplo permanece parcial.

### T12 — Circuito de exceções e gerência (UX-09/20/21/25/29/30)
Dependências: T02/T03/T06. Proprietárias: 007, 008, 012, 017 e 018.
- [ ] Primeiro isolar motivo por proposta e traduzir enums apenas na UI.
- [ ] Deep links autorizados por Venue selecionam tab/payment/shift/item/correction,
  inclusive histórico elegível, com foco e retorno; testar ID inválido/sem permissão.
- [ ] Reauth junto da decisão sem remover exigência; bloqueios de fechamento
  abrem resolução e auditoria fica acessível. Não autoaprovar ou zerar divergência.
- [ ] Separar projeção gerencial do detalhe por comanda; falha parcial mostra
  cobertura indisponível e não inventa totais; testar volume e número de consultas.

### T13 — Navegação, login e períodos (UX-31/32/33)
Dependência: T01. Proprietárias: 008, 012, 013 e 025-tenant-host-routing.
- [ ] Corrigir rótulo/retorno Caixa → PDV com contexto; linguagem e teclado no login.
- [ ] Não eliminar estabelecimento antes de resolução confiável de tenant e
  isolamento testado; separar essa dependência da melhoria textual.
- [ ] Presets Hoje/Ontem/7 dias pelo calendário operacional; testar cutoff/timezone.

### T14 — Evidência integrada e gate de piloto
Dependência: slices entregues; manter gates externos abertos.
- [ ] Executar protocolo G1 em vazio/normal/pico e rede controlada; comparar
  antes/depois com fixtures equivalentes e identificar commit/configuração.
- [ ] Web 360/390/430, estação desktop e Android com evidências independentes.
- [ ] Testes financeiros em PostgreSQL; lint/typecheck/build aplicáveis e
  `cd apps/web && npm run test:visual` para UI, sem relaxar baseline/tolerância.
- [ ] Registrar erros, recuperação, tempos humanos e espera de API separadamente;
  sem aparelho/observação humana, não afirmar ergonomia ou ganho de tempo real.
- [ ] Revisar diff, isolamento de dados, critérios PASS/FAIL/não verificados e
  pendências; piloto/deploy/provider exigem verificação própria.

## Backlog original (referência; execução controlada por T01–T14)

- [ ] Revalidar UX-03 no deploy atualizado, sem auto-iniciar preparo (local revalidado, deploy aberto).
- [x] Diagnosticar e especificar UX-34 em teste descartável (recorte entregue em T02).
- [ ] Medir matriz de pico/rede/mobile/Android do protocolo G1.
- [x] Especificar preservação de drafts e seleção previsível UX-06/35 (recorte em memória).
- [ ] Especificar envio/recuperação financeira UX-07/08/22.
- [ ] Especificar busca e contexto de mesa UX-02/12/18/19/24.
- [ ] Especificar repetição, catálogo e quantidades UX-01/13/14/15.
- [ ] Especificar lote seguro e acesso a passe/disponibilidade UX-04/05/23.
- [ ] Especificar circuito de exceção UX-09/20/21/25/26/30.
- [ ] Aplicar quick wins com checks proporcionais e gates existentes.
- [ ] Validar antes/depois e preparar turno observado no piloto.
