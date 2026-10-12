# Rodada — UX Friction Audit
Data: 12/10/2026 · Piloto: Bar do Aderlan  
Referência: `main`, commit `c198c9bd239a5ee0a0884a76ccb9b623245ae162`  
Repositório: https://github.com/procopio420/rodada

**Nota de versionamento no repositório:** publicado como guidance da
[Spec 026](../../specs/026-operational-ux-friction/spec.md), relacionado à Spec 023.
Na main 0a2038d, PR #98 já troca Aceitar → Preparar → Pronto por
Iniciar preparo → Pronto. UX-03 e os nove cliques de H2 descrevem o deploy
c198c9b efetivamente testado; não são medição da nova main.

> Auditoria em duas fases: inspeção de código e navegação real no Railway. A seção H registra jornadas executadas e contagens M; B2 preserva estimativas E da primeira fase. Android, pico controlado e queda deliberada de rede permanecem sem execução. Nenhum tempo humano ou número de gestos de scroll foi inventado.

## Escopo, método e limites da primeira fase

Foram lidos AGENTS.md, README.md, princípios de produto, design system e a revisão operacional anterior; inspecionados componentes Web, telas/ViewModels Android e contratos de comandas, customização, caixa, correções, guest e conectividade. A referência remota de main foi conferida novamente ao final da investigação e continuava no SHA acima.

A tentativa de executar o Web instalou dependências numa cópia isolada e o Next anunciou servidor pronto. Duas tentativas pelo navegador disponível retornaram `ERR_CONNECTION_REFUSED`. Uma verificação HTTP posterior também não alcançou o servidor. Portanto, não se afirma que a interface foi acessada, que o login funcionou ou que uma ação foi realizada. Não foi acessado deployment remoto: não havia evidência suficiente de isolamento de dados para usar uma instalação existente.

Não foi encontrado adb no PATH nem nos caminhos de ferramentas pesquisados. Android foi inspecionado como código; não houve build, emulador, aparelho, teclado real ou teste com uma mão. Não foram executadas migrations, seed, operações de banco, pagamentos ou testes automatizados. Metadados de dependências/Next gerados durante a tentativa local foram restaurados; o checkout terminou sem alterações rastreadas. Nenhum commit, branch, PR, issue, alteração de spec ou deploy foi criado.

**Atualização:** a limitação de navegador foi superada na continuação autorizada pelo usuário no ambiente demo do Railway. Consulte H para as jornadas reais, a versão publicada e as métricas M. A matriz completa de vazio/normal/pico, ergonomia mobile, Android e rede controlada continua incompleta; não apresentar o trabalho como auditoria de campo integral.

### Convenções

- **Confirmado:** comportamento/estrutura diretamente presente no código. Não significa teste em dispositivo.
- **Provável:** impacto ou comportamento depende de volume, estado, API ou interação ainda não reproduzida.
- **Hipótese:** proposta ou risco que exige observação.
- **E:** contagem estimada por inspeção; exclui digitação, foco do teclado, scroll e latência.
- **NM:** não medido. Usa-se NM para todos os tempos e scrolls desta execução.
- **Meta:** orçamento proposto de ações, não benchmark validado.
- **P0:** impediria operação segura ampla, com evidência suficiente. Nenhum P0 demonstrado nesta auditoria.
- **P1:** risco operacional relevante ou fricção frequente no pico.
- **P2:** fricção localizada, aprendizagem ou tarefa menos frequente.
- **P3:** melhoria de baixa urgência.
- **S/M/L:** esforço relativo de implementação, não prazo: pequeno ajuste local; múltiplos componentes/contratos; mudança estrutural com regras, recuperação e validação.

As estimativas E têm pontos de partida explícitos; métricas executadas M estão em H. Uma seleção em select conta como uma decisão/ação abstrata; em celular ela pode exigir mais taps. Uma tela pode ter muitas regiões e scrolls: baixa contagem de páginas não prova baixo esforço.

## A. Resumo executivo

**O problema central é que parte da UX ainda acompanha a estrutura dos registros e estados do sistema, em vez da sequência de trabalho do funcionário.** As prioridades são encontrar a comanda certa, manter o pedido no alcance, agir sobre produção real e resolver exceções com contexto preservado.

| Ordem | Achado | Impacto no bar | Prioridade |
| --- | --- | --- | --- |
| 1 | UX-01 — Android põe carrinho depois do catálogo inteiro e finanças antes de pedir | Procurar produto, descer para conferir e voltar para acrescentar; maior custo com cardápio longo | P1 |
| 2 | UX-02 — Lista principal Android sem busca; Web busca só apelido; POS sem busca equivalente | Localização visual de comandas e risco de selecionar homônimos no pico | P1 |
| 3 | UX-03 — Produção exige três transições por linha | Operador mantém estados em vez de preparar; 10 linhas NEW implicam 30 ações estimadas | P1 |
| 4 | UX-04 — Agrupamento de produção apenas visual e por produto, sem distinguir configuração | Refazer seleção item a item; resumo pode reunir preparos diferentes sob o mesmo nome | P1 |
| 5 | UX-05 — Passe e disponibilidade depois das filas em mobile | Item pronto ou esgotado fica distante da ação atual justamente quando o volume aumenta | P1 |
| 6 | UX-06 — Rascunho Web apagado ao escolher outra comanda | Interrupção do garçom pode virar retrabalho ou pedido esquecido | P1 |
| 7 | UX-07 — Intenção de pedido Web/guest apenas em memória após resultado ambíguo | Reload encerra continuidade do comando; operador precisa investigar antes de refazer | P1 |
| 8 | UX-08 — Pagamento em dinheiro do POS cria chave nova a cada chamada e não bloqueia envio | Risco de tentativas concorrentes/ambíguas; proteção do servidor precisa ser ensaiada | P1 |
| 9 | UX-09 — Atalhos de exceção abrem módulos sem selecionar origem | Gerente precisa lembrar nome, valor e ID, localizar tudo outra vez e pode agir no registro errado | P1 |
| 10 | UX-10 — Liberar mesa Android é ação direta, com revogação de acesso guest | Um toque acidental tem consequência maior que editar rascunho; Web já pede confirmação | P1 |

Outros pontos de alto retorno: repetir rodada, quantidades no guest, catálogo guest pesquisável, contexto de mesa acionável, nomenclatura “Pedir” no Android e reautenticação junto da decisão.

**O que merece preservação:** identidade opcional; comanda separada da mesa; confirmação única de pedido com validação no servidor; pagamentos parciais no domínio; disponibilidade compartilhada; correção append-only; saldo canônico; motivo e autoria em exceções; isolamento de sessão e proteção de confirmação ambígua. Nenhuma proposta autoriza apagar história, criar sucesso offline ou flexibilizar permissão.

Seguir o design system não resolve automaticamente os gargalos. O próprio sistema descreve resumo → fila → passe empilhados e resumo sem mutations em lote. Essa geometria e esse contrato precisam ser reconsiderados quando impedem acesso rápido à próxima ação.

## B. Mapa de jornadas e superfícies

### B1. Inventário da implementação

| Superfície | Implementação inspecionada | Capacidades observadas no código | Limites relevantes |
| --- | --- | --- | --- |
| Atendimento Android | AttendanceScreen, TablesScreen, TabOperationsScreen, PaymentDialog, ViewModel | Comandas, catálogo, customização, correções, pagamentos, caixa, localização, recuperação | Sem validação em aparelho; SDK/provider não homologado por esta auditoria |
| Atendimento Web | AttendanceWeb + OrderWorkspace withoutPayments | Agora, chamadas, comandas/pedidos, categorias, quantidade no draft, mesas/associação/limpeza | Sem pagamentos, estornos ou gestão de caixa; pedido ambíguo em memória |
| Cozinha | ProductionBoard station=KITCHEN | Resumo, fila por pedido, ações por item, passe, impressão, disponibilidade e Quick Catalog | Sem ação em lote; indisponibilidade distante da fila mobile |
| Bar | ProductionBoard station=BAR | Mesmo motor com produtos de bebidas | Não presumir UX especializada só porque muda título/estação |
| Caixa/PDV Web | /cash e /pos | Dinheiro, turno, suprimento/sangria, contagem, revisão e histórico | POS e Caixa são páginas distintas; /pos não é o companion |
| Gerência | /manage e páginas subordinadas | Exceções, operação, configuração, relatórios, fechamento diário e aprovação de correções | Vários atalhos sem ID; carregamento agrega chamadas por comanda |
| Cliente/QR | GuestOrdering | Resolve mesa, abre comanda opcionalmente nomeada, pede, acompanha, chama equipe, solicita conta | Sem controle de quantidade; catálogo linear; não presumir pagamento guest |
| Transversal | StaffAuthScreen, conectividade, recuperação nativa | Login, troca em terminal confiável, reauth, estados de rede, pendências | Políticas e apresentação variam entre superfícies |

Protótipos em prototype/ são referência. Hosts por tenant da Spec 025 são planejamento no README, não capacidade publicada demonstrada. Evidência histórica de testes em documentos não foi convertida em PASS desta execução.

### B2. Comparação de esforço

**Esta tabela preserva a análise estática: toda a coluna de cliques atuais é E, nunca medição. Para contagens executadas, usar H2.** Produto simples significa sem variants/modifier_groups. Os valores partem do contexto indicado e não incluem localizar o alvo por scroll.

| Fluxo / partida | Cliques atuais | Meta sugerida | Problema | Solução proposta |
| --- | --- | --- | --- | --- |
| Android: da lista, abrir anônima e enviar 3 bebidas simples | E: 6 = Pedir + Abrir + 3 produtos + confirmar | 5–6, com zero ida/volta por scroll | Quantidade de ações básica razoável; geometria ruim | Pedido/carrinho acessíveis no mesmo contexto |
| Web: Agora → Contas, abrir anônima e enviar 3 produtos na categoria atual | E: 6 = Contas + Abrir + 3 produtos + confirmar | 5–6 | Lista de comandas e histórico separam regiões | Novo pedido contextual; CTA acessível |
| Android/Web: comanda já selecionada, mais 3 bebidas simples | E: 4 | 4; 2 para repetir lote anterior | Repetição exige reconstrução | Repetir rodada → revisar/enviar |
| Achar comanda Android a partir de Contas | E: 1 seleção, busca visual não quantificada | Busca única + seleção | 1 tap pode esconder longa procura | Busca por nome/código/mesa com desambiguação |
| Web: Contas → buscar nome → selecionar | E: 1 seleção + 1 campo; navegação inicial +1 se partir de Agora | 1 busca + 1 seleção | Filtra somente display_label | Índice integrado de identificadores e localização |
| Web/Android: repetir item confirmado | Sem ação dedicada encontrada; E: nova seleção + confirmação, customização acrescenta passos | 2 a partir do histórico | Memorização do produto e modificadores | Copiar configuração para novo rascunho, revalidar |
| Web: corrigir draft de quantidade 1 para 2 | E: 1 no + | 1 | Já há controle direto | Preservar; tornar recuperação de remoção fácil |
| Guest: pedir 3 unidades de produto simples | E: 4 = 3 taps no catálogo + enviar | 3–4, com uma linha e quantidade visível | Cria três linhas; corrigir exige removê-las | Agrupar configuração idêntica e +/- |
| Guest: editar observação do item já no carrinho | E: 2 = Editar + salvar; 1 campo | 2 | Customização inline desloca contexto | Sheet/modal focado com retorno ao carrinho |
| Produção: 1 linha NEW → READY | E: 3 | 2 onde aceite/preparo forem uma ação operacional | Aceitar e preparar separados | Iniciar preparo → Pronto, com eventos corretos |
| Produção: 10 linhas NEW → READY | E: 30 | E/meta: 2 para lote realmente compatível, ou 20 individualmente | Sem operação por lote | Seleção auditável de lote; nenhuma conclusão implícita indevida |
| Indisponibilizar produto a partir do botão localizado | E: 1 | 1 | Gargalo é encontrar, não confirmar | Atalho de disponibilidade persistente/busca |
| Android: mover comanda já aberta para mesa ocupada | E: 4 = Operações + mover + destino + confirmar | 2–3 | Ação física no meio de operações financeiras | Localização contextual → destino → confirmação proporcional |
| Web: associar comanda a mesa ocupada | E: 3 = Mesas + Organizar + selecionar comanda | 2–3 | Associação não é prova de transferência completa | Lista de comandas clicável e ação de mover explícita |
| Android: parcial em dinheiro, comanda aberta e caixa default | E: 2 = Pagar + confirmar; 1 campo editado | 2 + 1 campo | Dialog financeiro longo; teclado sem tipo monetário explícito | Parcial/total; método e caixa persistidos com conferência |
| POS: receber parcial com comanda selecionada e caixa default | E: 1 botão + 1 campo | 1 confirmação + 1 campo | Segurança do envio e readback, não meta menor | Intent estável, busy, resultado e saldo atualizado |
| Guest: pedir conta com ocupação ativa | E: 1 | 1 | Ação inicial já curta | Preservar e mostrar andamento/responsável |
| Staff: concluir entrega no Android/Web | E: 1 por tarefa | 0 obrigatório para telemetria; 1 por exceção | Ação manual em caminho principal | Evidência passiva quando confiável; manual permanece disponível |
| Android: liberar mesa a partir do card | E: 1 | 2 | Pouca fricção para ação que revoga sessão | Confirmar mesa/efeito, comando idempotente |
| Web: liberar mesa a partir de Mesas | E: 2 | 2 | Proteção adequada no código | Preservar confirmação |
| Web: abertura de caixa no ponto já selecionado, sem turno | E: 1 botão + 1 campo | Igual | Não preencher fundo contado automaticamente | Melhor acesso, sem eliminar conferência |
| Web: sangria em turno ativo | E: 2 botões = Sangria + registrar; 2 campos | 2 + valor/motivo | Dados e histórico antes da ação | Atalho com contexto fixo e motivos sugeridos |
| Web: contagem/fechamento de turno ativo | E: 2 = conferir + confirmar; 1 campo | Igual | Página longa e reauth distante se necessária | Assistente de fechamento com contagem explícita |
| Web: revisar divergência, turno correto já selecionado | E: 1 + motivo; +1 e PIN se exigido | Igual | Procura do turno e reauth abaixo | Deep link e autorização junto da revisão |
| Gerência: abrir contexto do alerta → módulo | E: 2 links, depois relocalizar | 1 link direto + decisão contextual | Perde origem | Transporte de ID com validação e foco |
| Web: login sem sessão | E: 1 envio + 3 campos | 1 envio + 2 campos onde tenant conhecido | Memorizar slug e teclado PIN genérico | Contexto confiável do tenant, operador, PIN |

Não são apresentadas reduções percentuais: comparar estimativa de implementação com meta de design não prova ganho real. Nenhuma jornada financeira foi executada na primeira fase; H documenta registros fictícios de caixa e parcial na demo.

### B3. Carga cognitiva, recuperação e estados

| Jornada | Regiões/contextos inspecionados | Campos e confirmação | Memorização/erro | Recuperação | Complexidade estimada |
| --- | --- | --- | --- | --- | --- |
| Novo pedido Android | Lista/dialog → comanda → finanças → catálogo → carrinho | Apelido opcional; confirmar pedido | Lembrar quantidades enquanto carrinho fora do alcance | Intenção durável nativa; não ensaiada | Média, alta com catálogo longo |
| Novo pedido Web | Contas; abertura; lista; selecionada; draft; histórico; catálogo | Apelido opcional; confirmar | Seleção de outra comanda apaga draft | Sem persistência de draft/intent após reload observada | Média/alta |
| Multicomanda na mesa | Mesas → lista geral de comandas → pedido | Seleção de conta obrigatória | Nome exibido na mesa não é link de pedido | Repetir localização manual | Alta no pico |
| Produção simultânea | Resumo por produto → fila por pedido → passe | 3 transições por linha NEW | Associar configuração/destino do resumo à fila | Atualização bloqueia ações de toda estação | Alta |
| Disponibilidade | Fila/passe/tickets → catálogo da estação | 1 toggle | Encontrar produto esgotado; possível toque errado | Reativação e auditoria; sem “desfazer” comprovado | Média/alta |
| Pagamento parcial | Finanças → dialog/método/caixa | Valor; confirmação; condições dependem de método | Escolher caixa correto; distinguir intento de recebimento | Nativo tem recuperação; POS precisa ensaio | Alta pelo risco |
| Conta solicitada | Guest → fila de chamada staff → atendimento | 1 pedido; claim/conclusão disponíveis | Mesa com várias contas exige desambiguar | Chamadas preservam identidade em retry | Média |
| Fechamento | Turno → conferir → contado → divergência → revisão | Contado; motivo/PIN conforme revisão | Separar dinheiro de gaveta dos recebimentos do venue | Snapshot imutável e revisão explícita | Alta, justificável |
| Correção gerencial | Exceção → módulo → item/pagamento → autorização | Motivo/PIN; ação financeira | Relembrar registro original | Histórico preservado; Web pending sensível a reload | Alta |
| Rede intermitente | Avisos globais, item pendente, inventário de recuperação | Verificar mesmo comando | Não confundir “guardado” com “confirmado” | Proteção existe; acesso à pendência nativa pouco direto | Alta |

**Scrolls, tempos e número real de telas visitadas: NM.** As regiões acima são ordem de composição no código, não um registro de sessão.

| Estado | Configuração proposta para reprodução futura | Riscos previstos por inspeção | Situação nesta auditoria |
| --- | --- | --- | --- |
| Vazio | Sem comandas/pedidos; caixa fechado; guest sem comanda | Pedir abre comanda; repetição e caixa inexistente precisam orientação | Não executado |
| Normal | 8 comandas, 3 mesas multicomanda, 6 linhas de produção, 4 prontos | Troca de contexto e seleção correta da comanda | Não executado |
| Pico | 40 comandas ativas, 60 produtos, 30 linhas em produção, 12 prontos, 3 aprovações | Rolagem proporcional ao volume, serialização de ações, busca incompleta | Não executado |
| Histórico volumoso | Mais de 200 comandas no endpoint, inclusive encerradas | UI ignora paginação e pode não encontrar registro antigo/aberto | Não executado |
| Rede lenta/ambígua | Atraso controlado; resposta perdida depois do commit; retomada/reload | Reconciliação, draft durável, seleção bloqueada e retorno de foco | Não executado |

Esses volumes são fixtures sugeridas de teste, não descrição observada do Aderlan nem estimativa de capacidade do sistema.

## C. Backlog priorizado com evidência

Os códigos E01–E20 remetem aos arquivos imutáveis no apêndice. Sequências são walkthroughs estáticos, não ações executadas.

### UX-01 — Pedido Android subordinado a finanças e catálogo
**P1 · Atendimento Android · adicionar rodada · M · Confirmado na estrutura; impacto provável.**

Evidência E01, TabWorkspace: “Ajustar conta / serviço”, identidade/versão, Operações e BalanceCard antecedem Novo pedido; `items(availableProducts)` antecede OrderCart. O catálogo não tem categorias nessa tela, apenas busca textual. Carrinho e confirmação ficam depois de todos os resultados.

Atual: E 4 ações para três bebidas na comanda aberta; scroll NM. Meta: mesmas 4 ações sem sair do contexto visual de pedido. Recomenda-se resumo compacto de comanda/mesa/saldo, catálogo por categoria e carrinho acessível por barra inferior com contador/valor. Detalhes financeiros sob disclosure; pagamento abre detalhe completo. Benefício: conferir quantidades continuamente e não percorrer todo catálogo para enviar. Não esconder bloqueio de limite ou taxa desatualizada.

### UX-02 — Encontrar comanda depende de reconhecimento visual e apelido
**P1 · Android/Web/POS · busca por nome, código ou mesa · M · Confirmado nas telas; impacto provável.**

E01 renderiza a lista principal Android sem campo de busca. E02 filtra por `tab.display_label...includes(search)` somente em withoutPayments; /pos não exibe essa busca. Busca de cliente no dialog de abertura não substitui busca de comanda. Não foi encontrado resolvedor de código/mesa conectado a essas telas.

Atual: NM para localizar; E 1 seleção depois de encontrar. Meta: uma busca e uma seleção com mesa/código/saldo/estado nos resultados. Normalizar acentos também em nomes de comandas; permitir nome, código e mesa; exibir todas as comandas da mesa e diferenciar homônimos. Benefício: menos procura e menos erro de destino. Nunca selecionar automaticamente por fuzzy match.

### UX-03 — Três ações de produção para uma linha
**P1 · Cozinha/Bar · NEW → READY · M · Confirmado.**

E03: `NEW → ACCEPTED` (“Aceitar”), `ACCEPTED → PREPARING` (“Preparar”), `PREPARING → READY` (“Pronto”). Cada clique persiste e recarrega fila/catálogo.

Atual E 3 por linha; meta 2 quando aceitar e iniciar representam o mesmo ato. Propor “Iniciar preparo” e “Pronto”, com comando canônico capaz de registrar milestones sem fabricar tempo independente de aceite. Para bebida de retirada imediata, avaliar um fluxo específico com contrato próprio. Benefício: menos manutenção de estado. Não saltar transições só no frontend.

### UX-04 — Lote visual não é lote operacional, e ignora configuração
**P1 · Bar/Cozinha · produção simultânea · L · Confirmado; risco de preparo incorreto provável.**

E03 agrupa resumo por `product_id ?? item.id`, soma quantidades e mostra chips de comandas; não usa variant/modifiers/special_instructions na chave e não renderiza CustomizationText no resumo. A fila detalhada mostra customização. Nenhum botão de lote no resumo.

Atual E 30 ações para dez linhas NEW; meta 2 para um lote de dez linhas realmente compatíveis, sem misturar preparo. Recomenda-se separar por produto + configuração operacional e seleção explícita de linhas/quantidades; mostrar destino, exceções e escopo antes de marcar pronto. Server deve validar cada linha/versão e responder conflitos identificáveis. Benefício: bartender prepara e registra uma rodada real de uma vez. Não usar nome/quantidade como identidade nem descartar modificadores.

### UX-05 — Passe e indisponibilidade ficam distantes em mobile
**P1 · Bar/Cozinha · retirar pronto / produto acabou · M · Confirmado.**

E03/E04: resumo por produto, fila individual e passe empilhados em mobile; depois vêm Tickets de produção e Disponibilidade agora. Desktop largo usa três colunas. Dívida antiga permanece.

Atual E 1 toggle depois de localizar; scroll NM. Meta 1 toggle com disponibilidade acessível em até uma mudança de região. Usar navegação persistente Fila/Prontos/Disponibilidade com contagem e sinal de atraso, ou passe fixo compacto e sheet de busca de produtos. Benefício: esgotamento comunicado antes de novos pedidos e pronto menos esquecido. Não esconder fila atrás de resumo duplicado.

### UX-06 — Trocar de comanda apaga pedido em edição
**P1 · Atendimento Web/POS · interrupção enquanto monta pedido · M · Confirmado.**

E02, seleção: `setSelected(...); setTabCollapsed(false); setCart([])`. Abrir nova também limpa cart. Bloqueios protegem pedido pendente de confirmação, mas não draft ainda não enviado.

Atual: perda do draft; custo de reconstrução NM. Meta: zero perda silenciosa. Preservar rascunhos por comanda, identificados como não enviados; ao descartar, oferecer desfazer para edição local. Não transportar rascunho automaticamente para outro consumidor. Benefício: sobreviver a interrupções de atendimento.

### UX-07 — Reload rompe continuidade de pedido ambíguo Web/guest
**P1 · Atendimento Web, POS e Cliente · conexão perdida após envio · L · Confirmado para armazenamento; efeito operacional provável.**

E02 mantém confirmIntentRef e pendingPayload em memória. E05 mantém orderIntent em useRef e cart em useState; sessionStorage armazena sessão/cardápio e chamadas, não envelope do pedido. README Web declara recovery após reload fora do companion.

Atual: NM; usuário precisa investigar estado canônico. Meta: retomada automática da consulta do mesmo intento, sem criar pedido novo. Persistir envelope mínimo por contexto/session/venue, payload imutável, identificador e status; após retorno consultar/revalidar antes de oferecer nova rodada. Benefício: não depender da memória do funcionário para evitar duplicata. Não reutilizar intent de sessão revogada ou de outra visita.

### UX-08 — Recebimento POS sem proteção visível de envio pendente
**P1 · Caixa/PDV /pos · parcial em dinheiro · M · Confirmado no cliente; duplicação não demonstrada.**

E02 collect cria `crypto.randomUUID()` em cada chamada; botão não tem disabled/busy ligado ao recebimento e não há intent persistido. expected_version é enviado e pode proteger concorrência no servidor; isso não prova nem dispensa recuperação após resposta perdida.

Atual E 1 botão + valor; meta igual, com comportamento seguro. Estabelecer intenção antes do POST, bloquear duplo toque, manter payload/chave, readback e status “verificando recebimento”. Benefício: retirar ambiguidade financeira sem adicionar confirmações repetidas. Ensaio obrigatório com duplo toque e resposta perdida após commit; não alegar dupla cobrança confirmada.

### UX-09 — Exceção perde origem ao abrir operação
**P1 · Gerência/relatórios · alerta, estorno, divergência · M · Confirmado.**

E08: links genéricos /cash, /refunds, /pos. E09 exibe source.id, mas “Abrir operação” escolhe só rota; E15 fecha relatório com /cash sem shift_id. Gerente: lê exceção → abre contexto → módulo → procura registro novamente.

Atual E 2 links no caminho de alerta, procura NM. Meta 1 acesso ao contexto acionável ou detalhe já com decisão contextual. Deep link de tab/payment/shift/item, validado no servidor, seleção e foco do registro, retorno para exceção. Benefício: evitar copiar ID mentalmente ou resolver a comanda errada.

### UX-10 — Liberação de mesa Android sem confirmação proporcional
**P1 · Android Mesas · liberar ocupação/QR · S · Confirmado.**

E06: botão chama onRelease; E01 conecta ao ViewModel; E07 executa repository.releaseTable diretamente. A tela não introduz confirmação. Web E10 abre ActionDialog e explica revogação, preservando comandas.

Atual E 1; meta 2. Modal curto “Liberar Mesa X? Clientes precisarão escanear novamente; comandas continuam abertas”, com contagem de comandas e pendências relevantes. Benefício: proteção contra toque acidental. Não recomendar simples desfazer depois de revogar geração/sessão.

### UX-11 — “Pedir” abre uma comanda nova
**P1 · Android · adicionar pedido a cliente existente · S · Confirmado.**

E11: ação central “Pedir” chama onOpenTab; E01 usa `openingTab = true`. Não abre seletor de destino ou pedido na comanda já existente.

Atual: custo do erro NM; abrir nova simples E 2 até conta. Meta: “Nova comanda” para criação, e “Pedir” ligado à comanda selecionada ou a seletor rápido de recentes/mesa. Benefício: alinhar ação e expectativa e reduzir fragmentação de contas. Não criar comanda silenciosamente para toda rodada.

### UX-12 — Comandas da mesa são texto, não entrada para pedido
**P1 · Android/Web · mesa com múltiplas comandas · M · Confirmado.**

E06 imprime occupancy.tabs; E10 usa parágrafos com nomes. Não há onSelectTab no card de mesa dessas telas. Staff precisa ir a Contas e reconhecer nome.

Atual E ao menos navegação + seleção; localização NM. Meta tocar na comanda dentro da mesa e abrir pedido, mantendo retorno à mesa. Ação “Nova comanda nesta mesa” deve herdar ocupação explicitamente. Benefício: preservar contexto físico sem fundir contas.

### UX-13 — Não há ação dedicada de repetir consumo
**P1 · Android/Web/guest · outra rodada/repetir item · M · Confirmado nas superfícies inspecionadas.**

E01/E02/E05 renderizam histórico, customizações e correções/status, sem copiar item/rodada para novo draft. Seleção anterior nativa é lembrada dentro de TabWorkspace, mas não é repetir histórico confirmado.

Atual: reconstrução; E 4 para três produtos simples com catálogo localizado. Meta E 2 para “Repetir rodada” + conferir/enviar; alterações opcionais. Revalidar preço, disponibilidade e modificadores; destacar diferenças. Benefício: atender pedido verbal “mais uma igual” sem memorização. Jamais reenviar o idempotency key do pedido anterior como um novo pedido.

### UX-14 — Cliente sem edição direta de quantidade
**P1 · Guest · ajustar 3 bebidas para 2 · M · Confirmado; dívida anterior mantida.**

E05 addConfigured adiciona nova linha quantity=1; rows só têm Editar/Remover. ProductCustomization não altera quantidade. Não há +/- no guest, embora haja no companion E12.

Atual: remover linha individual, repetir taps no catálogo; meta +/- e agrupamento de configurações iguais. Linhas diferentes por observação continuam distintas. Benefício: revisão legível e menos edição desnecessária. Não agrupar “sem gelo” com bebida padrão.

### UX-15 — Cardápio guest sem categorias ou busca
**P1 · Cliente/QR · encontrar produto · M · Confirmado.**

E05 usa `products.map` no Cardápio, sem filtro, busca ou categoria; acesso exige abrir comanda antes de ver essa seção. Cabeçalho, conexão, atualização, equipe e saldo precedem cardápio.

Atual NM de procura/scroll. Meta catálogo como home, categorias/busca, cart fixo existente; abrir comanda no primeiro envio se contrato permitir e sem duplicar após timeout. Nome opcional continua opcional. Benefício: descoberta imediata e menor barreira para novo visitante. Esta criação integrada é redesenho de fluxo, não quick win sem contrato.

### UX-16 — Detalhamento financeiro compete com pedido no Android
**P2 · Android · rodada cotidiana · M · Confirmado.**

E01 BalanceCard apresenta original, descontos, cortesia, serviço, recebido, estornado, limite, percentual e outras ações; ajuste/limite estão visíveis mesmo sem exceção específica. Web companion já tem resumo compacto/disclosure.

Atual NM; meta mostrar saldo e restrição atual, expandir discriminação sob “Ver conta”. Benefício: leitura operacional curta. Cobrança e ações sensíveis mantêm composição completa. UX-01 cobre posição; este achado cobre densidade.

### UX-17 — Dialog monetário Android sem teclado decimal explícito
**P2 · Android · pagamento parcial/limite/transferência · S · Confirmado nos campos citados; ergonomia provável.**

E01 PaymentDialog rawAmount usa OutlinedTextField sem keyboardOptions; LimitResolutionDialog também não configura teclado monetário/PIN numericamente nesses campos. E13 valor parcial de transferência segue mesma ausência. Outros campos de caixa já usam opções específicas.

Atual NM; meta input monetário com teclado decimal, seleção do valor existente e validação clara, PIN com teclado adequado. Benefício: menos mudança manual de teclado. Testar vírgula/ponto, acessibilidade e IME em aparelho; não copiar esperado para contado.

### UX-18 — Movimento de mesa misturado com operações financeiras
**P2 · Android · mudar localização · M · Confirmado.**

E13 compartilha tela de opções com split/merge/reopen; MOVE_LOCATION mostra mesas ocupadas e pontos; motivo opcional e saldo também aparecem. Ação física exige navegar “Operações”.

Atual E 4 desde comanda aberta; meta E 2–3 com localização acionável no header. Separar visualmente localização de transferência de responsabilidade, sem alterar vínculo histórico do pedido. Benefício: operação cotidiana menos intimidadora e menor chance de confundir mover com dividir saldo.

### UX-19 — Associações de mesa não equivalem a mover comanda
**P2 · Atendimento Web · trocar mesa · M · Confirmado o controle; semântica final provável.**

E10 oferece “Associar comanda” no modal da mesa de destino; não há ação “Mover de A para B” com origem/efeito explicitado. Não foi executada API para concluir se associação de tab já ligada é rejeitada ou tratada.

Atual NM para transferência completa. Meta selecionar destino da própria comanda e confirmar “Mesa A → B”, mantendo saldo e visita correta. Benefício: não ensinar ao funcionário uma sequência informal de associação/liberação potencialmente errada.

### UX-20 — Estornos continuam com enums e sem acesso a comandas fechadas pelo seletor
**P2 · Gerência/estornos · localizar pagamento e devolver · S para linguagem; M para acesso · Confirmado.**

E14 mostra payment.method e payment.status diretamente; histórico de Refund também usa status cru. O seletor filtra `tab.state !== "CLOSED"`. Isso limita descoberta pelo Web, sem demonstrar que o backend proíbe estorno de pagamento de tab fechada.

Atual NM; meta linguagem “Dinheiro · Confirmado” e busca/histórico elegível incluindo encerradas quando regra permitir. Benefício: menor interpretação técnica e menos contorno de fluxo. Não reabrir comanda automaticamente só para estornar. Dívida anterior revalidada.

### UX-21 — Reauth de estorno é um formulário separado antes da decisão
**P2 · Gerência/estornos · autorização · M · Confirmado.**

E14: seção Confirmar gerente → PIN → Confirmar PIN; depois seleção comanda/pagamento, valor/motivo, confirmar. Mensagem diz “Agora confirme o estorno”. Caixa e fechamento diário têm retry inline automático após PIN.

Atual E pelo menos 2 botões + campos/seleções desde página; meta uma decisão de estorno e um PIN contextual quando necessário. Benefício: menos vai-e-volta e identidade confirmada perto do conteúdo aprovado. Preservar reauth exigida, limites e auditoria.

### UX-22 — Formulário de estorno permanece editável após resultado ambíguo
**P1 · Gerência/estornos · timeout/retry · M · Confirmado no cliente; consequência provável.**

E14 conserva intentRef em erro de rede/5xx, mas amount/payment/correction/reason não ficam congelados por essa pendência. Retry recompõe corpo do formulário usando a mesma chave. A mensagem pede não mudar valor, mas UI não impõe isso.

Atual NM; meta bloquear payload ambíguo e mostrar “Verificar estorno de R$ X em pagamento Y”. Alteração só após resolução explícita. Benefício: não depender de obediência à mensagem para manter identidade do comando. Não se afirma que servidor aplicaria corpo diferente; ensaiar rejeição de fingerprint e continuidade.

### UX-23 — Uma mutation bloqueia todas as ações da estação
**P1 · Bar/Cozinha · rede lenta e trabalho paralelo · M · Confirmado.**

E03 usa mutating global e disabled por changingItemId/changingProductId; load(true) consulta fila e catálogo após cada mutation. Enquanto confirma uma linha, outras transições e disponibilidade ficam pausadas.

Atual: tempo bloqueado NM. Meta bloquear aggregate/escopo afetado e serializar onde necessário, permitindo ações independentes seguras. Iniciar por reduzir refresh desnecessário com resposta canônica e invalidação seletiva. Benefício: latência de uma linha não para estação inteira. Não retirar lock sem proteção contra concorrência e snapshot obsoleto.

### UX-24 — Lista paginada tratada como completa em telas centrais
**P1 · Comandas/gerência/estornos · pico/histórico grande · M · Confirmado no contrato e consumidores; cenário não reproduzido.**

E16 TabListCreateView retorna até 200 e next_offset, por mais recentes. E02 load, E08 getResults e E14 load usam results sem consumir paginação. E10 refresh percorre páginas de active tabs, mas OrderWorkspace é outro consumidor independente.

Atual NM de busca falha; meta busca/paginação server-side ou carregamento explícito completo de ativas. Não tratar ausência na primeira página como inexistência. Benefício: encontrar comanda antiga e não subcontar cockpit/exposição. Validar volume >200 em teste isolado antes de definir gravidade de ocorrência real.

### UX-25 — Gerência consulta detalhe de cada comanda para montar exceções
**P1 · Gerência · abrir/atualizar cockpit · L · Confirmado na estrutura; lentidão provável.**

E08 busca sete listas e depois Promise.all(openTabs.map(detail)); o snapshot só é consolidado após detalhes. Um detalhe rejeitado faz o load cair no erro global, mesmo com outras leituras úteis.

Atual tempo NM; meta projeção agregada de exceções/pulso e leitura de detalhes ao abrir registro. Benefício: primeiro conteúdo útil rápido, menos dependência do volume e atualização parcial sem mascarar cobertura incompleta. Marcar dados indisponíveis, nunca apresentar subtotal parcial como total.

### UX-26 — Recuperação Android informa categoria, mas não abre contexto
**P2 · Android Agora · resolver pendências · M · Confirmado.**

E17 RecoveryEvidence contém id/label/capturedAt/reviewOnly; E01 renderiza textos “Pedido”, “Recebimento”, hora e instrução de abrir contexto. Lista geral não tem ação direta por registro; fila específica de pedidos possui outra ação de conferência.

Atual NM de localização; meta card com comanda legível, valor/resumo não sensível, status e “Verificar esta operação” levando ao retry original. Benefício: recuperação guiada sem UUID memorizado. Não adotar registro de outra sessão e não oferecer descarte de evidência ambígua.

### UX-27 — Conclusão manual de entrega no caminho principal
**P2 · Atendimento Android/Web · retirar/entregar · L · Confirmado o botão; obrigatoriedade de uso não comprovada.**

E01 Agora renderiza ENTREGUE por tarefa; E10 renderiza Concluir entrega. AGENTS/princípios pedem não exigir taps apenas para telemetria. Presença do botão não prova que toda entrega precisa dele, nem que inferência inexiste no backend.

Atual E 1/tarefa se usar controle; meta zero toque obrigatório para métricas quando houver evidência suficiente, e ação manual para exceções ou operação sem inferência confiável. Benefício: menos registro enquanto carrega bandeja. Não remover mecanismo de retirada/conclusão antes de provar alternativa; origem/confiança precisam ser visíveis.

### UX-28 — Modo pico Android ainda coloca chamadas antes das entregas
**P2 · Android Agora · várias filas simultâneas · M · Confirmado.**

E01 peak muda título “Só entregas” e omite contas, mas blocos de serviceRequests aparecem sempre que showDeliveries é verdadeiro e precedem deliveryTasks. Pendências locais também vêm antes do conteúdo.

Atual scroll NM; meta prioridades explícitas, filtros Prontos/Chamadas/Pendências e ordenação por urgência canônica; texto do modo descreve o que realmente exibe. Benefício: gargalo pronto não fica enterrado sob chamadas.

### UX-29 — Aprovação de propostas compartilha motivo entre cartões
**P2 · Gerência/fechamento diário · revisar várias correções · S · Confirmado.**

E18 todos os textarea decision-<id> usam o mesmo decisionReason; digitar numa proposta atualiza outras. Botões de cada cartão usam o motivo global.

Atual E 1 decisão + motivo/PIN; meta igual, mas motivo por proposta ou dialog de decisão único ligado a um ID. Benefício: não reaproveitar justificativa acidental de outra correção. Preservar proibição de autoaprovação.

### UX-30 — Bloqueios de fechamento mostram IDs, sem ação para resolver
**P2 · Gerência/fechamento diário · fechar dia incompleto · M · Confirmado.**

E18 renderiza blockers como texto + id.slice(0,8); instrui resolver e gerar outra versão, sem link por blocker. Fingerprint também é exibido no corpo operacional.

Atual NM; meta bloqueio com nome humano, ação “Abrir comanda/Conciliar pagamento/Revisar caixa” contextual e retorno à revisão. Fingerprint em detalhe de auditoria. Benefício: checklist acionável, não lista de códigos para investigar. Não gerar outra versão automaticamente sem necessidade.

### UX-31 — Login pede slug e expõe linguagem interna
**P2 · Transversal Web · entrar/trocar operador · S para linguagem/teclado; M/L para tenant · Confirmado.**

E19 inicia venueSlug vazio; formulário tem estabelecimento, operador e PIN. Texto “sem levar credenciais para o browser”, roles e trust_state crus aparecem em sessão; Field password não define inputMode numérico. Contrato de host por tenant ainda não publicado.

Atual E 3 campos + envio; meta 2 campos + envio quando contexto do estabelecimento estiver validado. Em terminal provisionado, operador recente + PIN, sem abrir acesso automático. Troca rápida continua só nos devices autorizados. Benefício: menos memorização técnica. Resolver venue por host exige isolamento testado; não confiar apenas no texto de um subdomínio.

### UX-32 — Voltar do Caixa leva ao POS com rótulo “atendimento”
**P2 · Caixa/transversal · navegação entre módulos · S · Confirmado.**

E20 header de /cash “Voltar ao atendimento” aponta /pos. Companion /attendance não recebe pagamentos; POS usa header “RODADA / ATENDIMENTO”. São experiências distintas com rótulos sobrepostos.

Atual E 1 link; meta igual, com “Voltar ao PDV” e retorno à comanda/origem correta. Benefício: clareza sobre onde receber e onde apenas registrar pedido. Não fingir paridade Android/Web.

### UX-33 — Relatórios exigem montar intervalo para consultas recorrentes
**P3 · Gerência/relatórios · hoje/ontem/semana · S · Confirmado o controle; benefício hipotético.**

E15 apresenta De/Até/Aplicar e CSV, sem atalhos de períodos usuais. Calendário operacional já é separado e deve permanecer.

Atual E 1 aplicar + até 2 campos; meta 1 “Hoje”, “Ontem”, “Últimos 7 dias”, definidos pelo dia operacional. Benefício: consulta comum mais rápida; datas exatas e timezone continuam visíveis. Não usar meia-noite civil como default silencioso.

## D. Quick wins

Pequeno esforço deve significar mudança localizada sem alterar garantias, não apenas poucos pixels.

| Proposta | Achados | Resultado pretendido | Proteção/validação |
| --- | --- | --- | --- |
| Renomear Pedir/Nova comanda conforme função | UX-11 | Menos criação acidental de conta | Testar pedido em comanda existente e criação anônima |
| Motivo de decisão por proposta | UX-29 | Uma justificativa não aparece em outras propostas | Duas propostas simultâneas com motivos diferentes |
| Traduzir métodos/status/roles e ajustar retorno Caixa→PDV | UX-20/31/32 | Menos interpretação e módulo errado | Manter enums na API/log; linguagem humana na UI |
| Teclados adequados para moeda/PIN | UX-17/31 | Menos troca de teclado | IME real, vírgula, fonte ampliada, screen reader |
| Esconder fingerprint em auditoria expandida | UX-30 | Menos informação concorrendo com decisão | Continuar acessível para investigação |
| Presets de período operacional | UX-33 | Uma ação para intervalo recorrente | Testar cutoff e virada da noite |
| Confirmar liberação de mesa Android | UX-10 | Reduzir toque destrutivo acidental | Mostrar mesa/efeito e preservar acesso até commit |

Não classificar lote de produção, recovery durável ou tenant como quick win. Deep links têm alto retorno, mas exigem seleção/foco/autorização e normalmente esforço M. Proteção do recebimento POS também exige testes de resultado ambíguo, além de desabilitar botão.

## E. Redesenhos estruturais

### E1. Workspace de garçom centrado na comanda e no pedido

Header fixo compacto: nome/código, mesa e saldo; catálogo categorizado; favoritos de operação configurados, não adivinhados; draft acessível continuamente; histórico só quando necessário. “Outra rodada” reutiliza histórico como novo draft. “Mesas” abre comandas acionáveis; mudar mesa não vira transferência financeira.

Estados de rascunho por comanda sobreviverão a interrupções; header e CTA dizem exatamente quem receberá o pedido. Confirmar envia uma intenção e mostra recebido somente após resposta canônica.

### E2. Estação centrada em trabalho, com lote seguro

Fila e passe acessíveis no mesmo viewport de trabalho; disponibilidade em atalho persistente. Resumo distingue configuração e não oferece soma enganosa. “Iniciar” reúne aceite/preparo apenas se o ato físico for único. Produção em lote tem escopo explícito e resultado por linha. Ready não significa entregue.

No Bar, bebida simples/retirada imediata merece avaliação própria; na Cozinha, preparos e modificadores precisam sobreviver ao agrupamento. Não impor o mesmo número de etapas só porque ambos reutilizam ProductionBoard.

### E3. Cockpit de exceção até resolução

A exceção carrega sua identidade até o módulo, abre registro selecionado, disponibiliza próxima ação e retorna ao cockpit. Alertas agrupados por causa não equivalem a apagar alertas; ciência continua diferente de resolução.

Projeção consolidada evita carregar todo detalhe de todas as comandas. Dados parciais têm cobertura explícita e não são total financeiro. Fechamento vira checklist de bloqueios acionáveis, contagem e revisão, preservando versões imutáveis.

### E4. Cliente centrado em cardápio e revisão

Cardápio logo no acesso; categoria/busca; comanda resolvida/criada no momento correto sem cadastro obrigatório. Quantidades editáveis por configuração, botão de carrinho fixo existente, revisão clara e pedido confirmado com acompanhamento simplificado. Conta e chamar equipe continuam ao alcance.

Guest draft e intento são distintos: draft editável; envio ambíguo congelado para consulta. Nenhuma sessão revogada continua válida só porque existe cache.

### E5. Recuperação como fluxo de produto

Uma operação pendente mostra comanda, resumo/valor, última tentativa, estado e próxima ação. Retry consulta o mesmo envelope. Pessoa não precisa saber o que é idempotency key, UUID ou fingerprint.

Se existe cobrança externa/pagamento ambíguo, reconciliar antes de oferecer outra cobrança. Uma pendência de outra sessão segue revisão autorizada, sem adoção automática. Proteção financeira é parte da UX, não texto de aviso.

## F. Proposta de UX ideal no turno

### Garçom

Toca na mesa ou pesquisa nome/código; escolhe a comanda certa entre as do grupo. O contexto permanece visível. Toca três bebidas e envia; vê quantidade/valor no draft sem abandonar catálogo. Na rodada seguinte, “Repetir” recupera configuração e avisa mudanças antes do envio.

Uma seleção errada no draft pode ser desfeita imediatamente. Depois de confirmado, “Corrigir” apresenta alternativas adequadas à etapa e autoriza quando necessário. Para receber parcial, abre Pagar, edita valor e confirma método/caixa; saldo restante aparece no retorno. Fechamento depende de saldo canônico zero e não libera mesa automaticamente.

Pedidos prontos entram na visão de trabalho por destino/urgência; métricas não exigem sequência manual de peguei/entreguei quando houver evidência confiável. Em rede ruim, o draft continua preservado e envio aparece pendente, nunca como produção já recebida.

### Cozinheiro

Vê o trabalho mais urgente, configuração completa e destino; inicia preparo numa ação e marca pronto numa outra. Lotes só unem preparos compatíveis. Passe tem acesso permanente. “Acabou” abre disponibilidade contextual sem navegar por cadastro; mudança atualiza todos os canais após confirmação.

Pedido corrigido aparece como exceção ligada ao original, sem reescrever histórico ou sumir silenciosamente. Falha de rede preserva último snapshot e orienta fallback; não inventa conclusão sincronizada.

### Bartender

Trabalha por rodada/produto com diferenças visíveis: gelo, tamanho, sabores e observações. Pode selecionar linhas compatíveis, produzir e confirmar lote com escopo legível. Bebida imediata tem fluxo proporcional ao preparo, autorizado pelo domínio. Vê prontos por destino e conta pendência no passe, sem alternar repetidamente resumo e ticket.

### Gerente/caixa

Abre cockpit com exceções e próxima ação. Toca na divergência e cai no turno certo; toca no pagamento pendente e consulta o pagamento certo; uma aprovação já mostra valor, origem, efeito e PIN contextual. Não precisa relembrar IDs.

Recebimento em dinheiro deixa claros saldo devido e, quando suportado pelo contrato, valor entregue/troco. Não se assume que PaymentDialog atual oferece troco: isso requer revisão específica. No fechamento, informa contagem física, vê diferença e justifica revisão. Correção posterior gera proposta para outra pessoa autorizada, preservando snapshot original.

Relatórios têm atalhos por dia operacional e distinguem venda, recebimento e exposição atual. Configurações ficam fora do caminho de produção, mas são localizáveis por tarefa.

## G. Plano de melhoria — propostas, sem execução

| Onda | Objetivo | Escopo proposto | Dependências e critério de saída |
| --- | --- | --- | --- |
| 0 — validação empírica | Confirmar ordem/prioridade dos gargalos | Sessão com UI real e teste descartável em todas as superfícies | Métricas de B2 medidas e logs dos cenários de rede; nenhuma produção |
| 1 — preservar contexto e segurança | Reduzir erros/retrabalho antes de estética | UX-06/07/08/10/22/24/29; retorno correto e linguagem | Ensaios de duplo toque, timeout pós-commit, reload, troca de sessão e >200 tabs |
| 2 — operação cotidiana | Acelerar pedido, busca e repetição | UX-01/02/11/12/13/14/15/16/17/18/19 | Jornadas de três bebidas e rodada repetida sem perda de draft/contexto |
| 3 — produção no pico | Registrar trabalho em vez de estados artificiais | UX-03/04/05/23/27/28 | Lote com customizações, conflitos e station feedback; sem falso READY |
| 4 — resolver exceções | Fechar circuito gerencial | UX-09/20/21/25/26/30/31/32/33 | Exceção→registro correto→decisão→retorno; sem seleção manual repetida |
| 5 — piloto observado | Ajustar a partir de turno real | Garçom, produção e gerente; comparação antes/depois | Ganho medido sem aumento de erro, duplicata ou perda de visibilidade |

Ordem dentro das ondas depende da sessão empírica. Não há aprovação para implementar nada neste relatório.

### G1. Protocolo de medição a executar em ambiente apropriado

1. Fixar commit, configuração e dados descartáveis; não reutilizar a base de produção. Usar apenas métodos financeiros de teste e simulação.
2. Preparar vazio, normal e pico conforme B3; Android real/BYOD e PC de estação, além de mobile 360/390/430.
3. Para cada jornada, registrar início/fim, touches físicos incluindo seleção/teclado separadamente, telas/overlays, mudanças de módulo, distância/gestos de scroll, campos, confirmações e consultas ao colega.
4. Cronometrar tarefa desde pedido verbal até resultado confirmado; separar espera de API do tempo humano. Relatar mediana e dispersão, sem benchmark de uma única tentativa.
5. Testar interrupção no draft, nomes iguais, comanda sem nome, mesa multicomanda, item indisponível após seleção e correção depois de iniciar preparo.
6. Rede: atraso controlado, queda antes do envio e perda de resposta depois do commit; retomar, reload e encerramento forçado nativo. Verificar um único efeito canônico e comunicação compreensível.
7. Caixa: parcial sem encerramento, recebimento concorrente, contagem com diferença, aprovação por outro gerente e consulta histórica. Nunca criar movimento para zerar divergência.
8. Testar com uma mão, caminhada segura, ruído, brilho, teclado e fonte ampliada; não assumir que target 44 px torna um controle confortável ou alcançável.
9. Pedir execução sem treinamento prévio de menus, depois repetir com experiência; registrar hesitações e erros, não atribuir “complexidade cognitiva” a uma pontuação inventada.
10. Produzir antes/depois com os mesmos cenários; só então afirmar redução de tempo/taps e definir metas finais.

### G2. Metas operacionais propostas

- Três produtos simples na comanda já aberta: até quatro ações de negócio; draft e confirmação acessíveis sem percorrer todo catálogo.
- Repetir rodada compatível: até duas ações de negócio, com revisão e diferenças visíveis.
- Encontrar por nome/código/mesa: uma busca e seleção explícita; homônimos desambiguados.
- Disponibilidade: uma mudança de região no máximo, depois uma ação de negócio; confirmação proporcional ao risco.
- Alerta: abrir diretamente registro correto, com decisão contextual e retorno.
- Resultado ambíguo: nenhuma chave/payload novos até resolver intenção original; retomada após reload quando suportada.
- Nenhuma perda silenciosa de draft ao mudar consumidor.
- Nenhuma redução de cliques aceita se aumentar erro de pagamento, preparo ou destino.

Estas metas são orçamento de interação; não prometem zero scroll em todos os dispositivos nem aprovação dos contratos propostos.

## Apêndice — evidências reproduzíveis

Todos os caminhos abaixo pertencem ao commit auditado. Links usam o SHA fixo para evitar que main futura mude a evidência.

| Código | Fonte | Trecho/função relevante |
| --- | --- | --- |
| E01 | [AttendanceScreen.kt](https://github.com/procopio420/rodada/blob/c198c9bd239a5ee0a0884a76ccb9b623245ae162/apps/attendance-android/app/src/main/java/com/rodada/attendance/operations/AttendanceScreen.kt) | TabWorkspace, BalanceCard, FrontlineList, PaymentDialog, OpenTabDialog |
| E02 | [order-workspace.tsx](https://github.com/procopio420/rodada/blob/c198c9bd239a5ee0a0884a76ccb9b623245ae162/apps/web/components/order-workspace.tsx) | load, addDraftLine, seleção com setCart([]), confirm, collect, busca |
| E03 | [production-board.tsx](https://github.com/procopio420/rodada/blob/c198c9bd239a5ee0a0884a76ccb9b623245ae162/apps/web/components/production-board.tsx) | next, change, groups, orderGroups, disabled, productionWorkspace, stationTools |
| E04 | [globals.css](https://github.com/procopio420/rodada/blob/c198c9bd239a5ee0a0884a76ccb9b623245ae162/apps/web/app/globals.css) | productionWorkspace block/grid, guestCart fixed, attendanceNav |
| E05 | [guest-ordering.tsx](https://github.com/procopio420/rodada/blob/c198c9bd239a5ee0a0884a76ccb9b623245ae162/apps/web/components/guest-ordering.tsx) | addConfigured, orderIntent, submitOrder, products.map, revisão e chamada |
| E06 | [TablesScreen.kt](https://github.com/procopio420/rodada/blob/c198c9bd239a5ee0a0884a76ccb9b623245ae162/apps/attendance-android/app/src/main/java/com/rodada/attendance/operations/TablesScreen.kt) | TableCard, onRelease, OccupyTableDialog, AssignTabDialog |
| E07 | [OperationsViewModel.kt](https://github.com/procopio420/rodada/blob/c198c9bd239a5ee0a0884a76ccb9b623245ae162/apps/attendance-android/app/src/main/java/com/rodada/attendance/operations/OperationsViewModel.kt) | releaseTable, completeDelivery, recovery de mutation |
| E08 | [manage/page.tsx](https://github.com/procopio420/rodada/blob/c198c9bd239a5ee0a0884a76ccb9b623245ae162/apps/web/app/manage/page.tsx) | load com seven lists + openTabs details; links de exceção |
| E09 | [manage/alerts/[id]/page.tsx](https://github.com/procopio420/rodada/blob/c198c9bd239a5ee0a0884a76ccb9b623245ae162/apps/web/app/manage/alerts/%5Bid%5D/page.tsx) | source.id e Abrir operação sem identidade no link |
| E10 | [attendance-web.tsx](https://github.com/procopio420/rodada/blob/c198c9bd239a5ee0a0884a76ccb9b623245ae162/apps/web/components/attendance-web.tsx) | Workspace, refresh paginado, Mesas, dialogs, Concluir entrega |
| E11 | [AttendanceNavigation.kt](https://github.com/procopio420/rodada/blob/c198c9bd239a5ee0a0884a76ccb9b623245ae162/apps/attendance-android/app/src/main/java/com/rodada/attendance/ui/AttendanceNavigation.kt) | ação central Pedir/onOpenTab |
| E12 | [attendance-draft.tsx](https://github.com/procopio420/rodada/blob/c198c9bd239a5ee0a0884a76ccb9b623245ae162/apps/web/components/attendance-draft.tsx) | quantidade com minus/output/plus; Editar |
| E13 | [TabOperationsScreen.kt](https://github.com/procopio420/rodada/blob/c198c9bd239a5ee0a0884a76ccb9b623245ae162/apps/attendance-android/app/src/main/java/com/rodada/attendance/operations/TabOperationsScreen.kt) | MOVE_LOCATION, split/merge, motivo e confirmar |
| E14 | [refunds/page.tsx](https://github.com/procopio420/rodada/blob/c198c9bd239a5ee0a0884a76ccb9b623245ae162/apps/web/app/refunds/page.tsx) | payment.method/status, filtro CLOSED, reauthenticate, intentRef |
| E15 | [reports/page.tsx](https://github.com/procopio420/rodada/blob/c198c9bd239a5ee0a0884a76ccb9b623245ae162/apps/web/app/reports/page.tsx) | período, CSV, links genéricos de caixa |
| E16 | [ordering/views.py](https://github.com/procopio420/rodada/blob/c198c9bd239a5ee0a0884a76ccb9b623245ae162/apps/api/modules/ordering/views.py) | TabListCreateView.get, limite 200/next_offset |
| E17 | [RecoveryPresentation.kt](https://github.com/procopio420/rodada/blob/c198c9bd239a5ee0a0884a76ccb9b623245ae162/apps/attendance-android/app/src/main/java/com/rodada/attendance/operations/RecoveryPresentation.kt) | RecoveryEvidence e categorias sem navegação |
| E18 | [manage/daily-close/page.tsx](https://github.com/procopio420/rodada/blob/c198c9bd239a5ee0a0884a76ccb9b623245ae162/apps/web/app/manage/daily-close/page.tsx) | decisionReason compartilhado, blockers, fingerprint, reauth |
| E19 | [staff-auth-screen.tsx](https://github.com/procopio420/rodada/blob/c198c9bd239a5ee0a0884a76ccb9b623245ae162/apps/web/components/staff-auth-screen.tsx) | LoginPanel, Field, SessionPanel, trust_state/role |
| E20 | [cash/page.tsx](https://github.com/procopio420/rodada/blob/c198c9bd239a5ee0a0884a76ccb9b623245ae162/apps/web/app/cash/page.tsx) | retorno /pos, histórico antes da posição, startCount/closeShift/reauth |

Outras fontes consultadas: README.md; apps/web/README.md; docs/product/principles.md; docs/design/system.md; docs/design/operational-ux-review.md; specs/004-table-guest-ordering/acceptance.md; specs/009-tab-operations/spec.md; specs/010-product-modifiers-variants/acceptance.md; specs/012-cash-management/acceptance.md; specs/014-connectivity-degraded-operation/spec.md; specs/017-order-corrections-exceptions/acceptance.md; ProductCustomization; ConfirmedItemRemoval; ServiceRequestQueue; ManagementNav; OperationalAlerts; CashShiftScreen; IntegratedPaymentPanel.

### Revalidação das dívidas da revisão anterior

| Dívida antiga | Conclusão atual | Evidência |
| --- | --- | --- |
| Scroll em fila mobile/passe/disponibilidade | Estrutura ainda empilhada; quantidade de scroll não medida | E03/E04 |
| Guest sem edição de quantidade | Permanece; não confundir com +/- já existente no companion | E05/E12 |
| Enums técnicos em estornos | Permanecem no Web; Android tem formatadores humanos em pagamentos | E14/E01 |
| Catálogo antes da operação nas estações | Corrigido quanto ao cadastro; resumo de produção ainda antecede fila/passe | E03 |
| Gerência com cadastros antes da operação | Melhorou: seção única e cadastros em Mais; foco agora é ação contextual e custo de carregamento | E08 |
| Android sem ferramenta na revisão de 08/10 | Limitação novamente presente nesta execução; evidência histórica de build/capture não substitui teste atual | Inspeção do ambiente |

### Decisões que o relatório não permite tomar

Não afirmar tempo de atendimento, aprovação de usabilidade no pico, paridade de capacidades, acessibilidade real em dispositivo, recuperação financeira homologada ou prontidão para substituir o VRSystem. Não tratar passagem em teste visual/documento antigo como operação executada aqui; somente H enumera execução própria no navegador. O backlog está pronto para revisão e validação; as propostas permanecem exclusivamente diagnóstico.


## H. Complemento empírico — navegador no Railway

**Esta seção substitui a limitação de ausência de navegador da primeira entrega.** A inspeção estática continua válida para o commit fixado; a tabela B2 permanece uma tabela de estimativas. As métricas M abaixo registram ações realmente executadas.

### H1. Ambiente e versão

- Ambiente Railway confirmado por consulta de plataforma: projeto `rodada-aderlan-demo-20261009`, environment `demo`.
- Deploy Web `db46ab1f-fdec-4a8a-95d0-a8ea8230cd30`, SUCCESS, commit `c198c9bd239a5ee0a0884a76ccb9b623245ae162`. Coincide com a base inspecionada.
- URL efetivamente aberta: https://rodada-web-demo.up.railway.app/attendance.
- Navegador Chrome disponível, viewport medido pelo DOM: **1363 × 936 px**. Não é validação de ergonomia mobile.
- A main remota avançou para `0a2038dc509a7ade6d3ddc786be372690a1b6f19` durante a continuação. Não houve deploy para atualizá-la. Resultados de navegação descrevem c198c9b, não esse novo HEAD.
- Login realizado pelo formulário seguro do navegador; identidade visível após login: gerente da demo. Nenhum PIN aparece neste relatório.
- Não houve simulação de responses nem API calls para produzir as jornadas: criação, pedido, customização, produção, disponibilidade, recebimento e caixa foram acionados pelos controles reais.
- API/backend no ambiente publicado; dados de teste identificados por **AUDITORIA UX**. Todos os valores de dinheiro são registros fictícios da demo, sem movimentação real, provider, cartão ou Pix.
- Banco existente da demo recebeu apenas os eventos necessários às jornadas autorizadas. Não foi reiniciado, apagado, migrado ou alterado por SQL. Nenhum deploy/configuração/spec/código foi alterado.

O build Web local passou, mas o navegador separado não alcançou o servidor local. A causa identificada é isolamento de rede por execução. A tentativa de instalar Chromium local falhou no download do pacote; isso não é falha do produto. O navegador usado para a evidência abaixo foi o Chrome remoto acessando o Railway, não o runner local.

### H2. Jornadas realmente executadas

M = ações de negócio acionadas no navegador e contadas pela sequência. Foco, teclas, digitação, scroll automático do locator e esperas não são incluídos. Campos são registrados separadamente. Tempos de conclusão continuam NM: duração de ferramenta inclui overhead e não foi usada como tempo de funcionário.

| Jornada | Partida | Ações M | Campos | Resultado observado |
| --- | --- | --- | --- | --- |
| Abrir comanda e registrar 3 bebidas | Contas já aberta | **5**: Abrir + 3 produtos + Confirmar | 1 apelido opcional | Comanda AUDITORIA UX 12-10 1634; Amstel 600ml, Lata e Long Neck; total R$ 30 |
| Mesmo fluxo desde Agora | Acrescentar navegação inicial | **6** incluindo Contas | Mesmo campo | Roteiro completo com uma mudança de seção |
| Produzir as 3 bebidas | Pedido disponível no Bar | **9**: Aceitar/Preparar/Pronto por linha | 0 | Três linhas chegaram ao passe, com destino AUDITORIA UX |
| Segunda rodada, com teste de quantidade e observação | Comanda já selecionada | **6**: adicionar + aumentar + diminuir + Editar + Adicionar + confirmar | 1 observação | 1 Amstel Lata com “Teste de UX: servir sem copo”; total acumulado R$ 38 |
| Buscar comanda por apelido | Contas aberta | **1 seleção**, com campo de busca preenchido | 1 busca | Filtro reduziu a lista à comanda AUDITORIA UX |
| Associar comanda à mesa existente | Seção Contas → Mesas | **3**: Mesas + Organizar + selecionar comanda; fechar modal = +1 | 1 seleção | Mesa 01 passou a listar a comanda auditada ao lado das existentes |
| Abrir guest e montar pedido, corrigindo quantidade | Guest sem comanda | **7**: abrir + 3 águas + remover uma + Fritas + enviar | 1 apelido | Duas águas de R$ 5 e uma Fritas de R$ 28; total R$ 38 |
| Produzir item guest na Cozinha | Linha disponível | **3**: Aceitar + Preparar + Pronto | 0 | Fritas apareceu “Pronto” também no acompanhamento guest |
| Indisponibilizar Fritas e restaurar | Controle localizado na Cozinha | **1** para bloquear; **1** para restaurar | 0 | Guest desabilitou produto; estação voltou a oferecer Indisponibilizar após restauração |
| Abrir turno fictício | Caixa principal sem turno | **1** confirmar abertura | 1 fundo inicial | Turno abriu com R$ 100 |
| Suprimento fictício | Turno aberto, default Suprimento | **1** registrar | 2: valor/motivo | +R$ 20, motivo identificado como auditoria |
| Sangria fictícia | Turno aberto | **2**: Sangria + registrar | 2: valor/motivo | -R$ 10, motivo identificado como auditoria |
| Pagamento parcial fictício | POS com comanda selecionada; caixa default | **1** receber; seleção anterior = +1 | 1 valor | Recebido R$ 10; saldo restante R$ 28; comanda continua aberta |
| Contar e fechar ficticiamente | Turno aberto atualizado | **2**: Conferir caixa + Confirmar fechamento | 1 contado | Esperado R$ 120; contado R$ 119; diferença -R$ 1; revisão pendente |
| Pedir conta via QR | Guest com ocupação ativa | **1** | 0 | “Pedido de conta recebido pela equipe” |
| Atender chamada de conta | Staff após ir a Agora | **3**: Atualizar chamadas + Assumir + Concluir; navegação Agora = +1 | 0 | Responsável passou a “Você”; após conclusão, nenhuma chamada aberta |
| Abrir alerta e operação | Gerência | **2 links**: contexto + operação | 0 | Detalhe tinha ID; destino foi /bar genérico, sem selecionar a linha |
| Corrigir item confirmado após parcial | Linha ainda Novo, comanda auditada | **2**: Remover + Confirmar remoção; Voltar = +1 | Default de motivo, não alterado | Correção exigiu gerência/estorno; modal permaneceu aberto |
| Consultar estorno da correção | /refunds | **1 seleção** de comanda | Seleção | Método/status técnicos e pendência de R$ 0 observados; não executado estorno |
| Aplicar relatório do dia | /reports com período default | **1** Aplicar período | Nenhuma data alterada | Dados reais do ambiente e distinção entre vendas/recebido/exposição renderizados |
| Perda de draft ao trocar conta | Comanda auditada aberta | **3**: adicionar item + selecionar outra + retornar | 0 | Draft com 1 Amstel virou 0 e continuou vazio no retorno |
| Reselecionar conta já selecionada | Resultado da busca | **1** | 0 | aria-expanded virou false; pedido ficou recolhido |

**Telas/módulos navegados de verdade:** Atendimento, Bar, Cozinha, Cliente/QR, Gerência, contexto de alerta, POS, Caixa, Estornos e Relatórios. Overlays de edição, organização de mesa e correção foram abertos e utilizados. Android continua somente inspecionado.

**Não executar estorno de R$ 0 foi uma decisão de auditoria:** o objetivo era documentar o estado incoerente, não insistir num comando sem finalidade financeira.

### H3. Achados anteriores revalidados pela navegação

| Achado | Nova evidência | Estado atualizado |
| --- | --- | --- |
| UX-03 — três transições por item | Nove cliques executados para três bebidas; três para Fritas guest | Confirmado por execução em c198c9b |
| UX-04 — resumo não age em lote | Resumo agrupado; ações executadas linha a linha | Ausência de ação observada; compatibilidade de customizações em lote ainda não ensaiada |
| UX-06 — perda de rascunho | Draft 1 → outra conta 0 → retorno 0 | Confirmado por execução |
| UX-09 — alerta sem deep link ao item | Contexto mostrou ID, “Abrir operação” levou a /bar | Confirmado por navegação |
| UX-12 — mesa com múltiplas contas sem entrada direta | Mesa 01 listou comandas como texto; modal de associação foi necessário | Confirmado por navegação |
| UX-14 — guest sem quantidade | Três taps geraram três linhas 1×; remover uma deixou duas | Confirmado por execução |
| UX-15 — catálogo linear | 146 produtos renderizados, nenhum input type=search; screenshot mostrou informações financeiras antes do catálogo | Confirmado no desktop publicado |
| UX-20 — termos técnicos em estornos | Option “CASH · CONFIRMED · R$ 10,00 disponível” | Confirmado por navegação |
| UX-21 — autorização separada | Formulário de PIN acima da seleção de comanda/pagamento | Confirmado na interface; reauth de estorno não executada |
| UX-23 — bloqueio global da estação | Durante transição de uma bebida, demais linhas e disponibilidade apareceram disabled | Confirmado no estado de envio; duração não medida |
| UX-32 — volta Caixa→POS rotulada atendimento | Link exibiu ← Voltar ao atendimento e destino /pos | Confirmado na interface |
| UX-33 — períodos sem presets | De, Até, Aplicar período e CSV, sem Hoje/Ontem | Confirmado na interface |

### H4. Duas novas fricções confirmadas em execução

#### UX-34 — Correção após parcial encaminha para “Estornar R$ 0,00”
**P1 · Atendimento Web/Estornos · correção de linha confirmada após parcial · M · Confirmado na interface; causa backend ainda não diagnosticada.**

Sequência efetiva: comanda de teste R$ 38 → parcial fictício R$ 10 → saldo R$ 28 → Remover na linha Amstel Lata R$ 8 ainda Novo → Confirmar remoção. O modal mostrou: **“Este item envolve pagamento. A gerência precisa resolver o estorno; ele ainda não foi removido.”** O botão permaneceu **Confirmar remoção**. Ao selecionar a mesma comanda em Estornos, a correção apareceu **“Amstel Lata · exige R$ 0,00”**, texto **“estorno exato de R$ 0,00”** e botão **“Estornar R$ 0,00”**.

Atual: 2 ações para chegar ao bloqueio, depois navegação/reseleção sem resolução; tempo NM. Meta: apresentar disposição financeira compreensível e próxima ação executável. Se não há dinheiro a devolver, resolver a correção segundo a regra de alocação sem exigir estorno inexistente; se há, calcular e mostrar valor correto. Modal deve mudar de “Confirmar remoção” para “Abrir revisão da gerência”, transportando correction/tab IDs. Benefício: evitar ciclo de tentativas sem saída e mensagem financeira contraditória. Não assumir causa nem declarar prejuízo, pagamento duplicado ou reversão aplicada. Este achado entra entre as maiores prioridades de validação antes do piloto.

#### UX-35 — Selecionar novamente a conta recolhe a área de trabalho
**P2 · Atendimento Web · voltar ao pedido pelo resultado da busca · S/M · Confirmado em execução.**

Depois de buscar a comanda já selecionada e tocar no resultado, a área de pedido recolheu: aria-expanded=false e botão interno “Expandir”. A mesma ação que seleciona outra conta também funciona como collapse para a atual.

Atual M 1 toque que oculta o trabalho; +1 para expandir. Meta selecionar resultado sempre levar ao contexto utilizável; recolher fica em controle explícito separado. Benefício: não punir o gesto aprendido “tocar na conta para trabalhar”. Preservar rascunhos e retorno de foco; não eliminar a opção de recolher informações auxiliares.

### H5. Medições geométricas reais e limites

- Guest: **146 produtos**; documento **14.476 px** de altura em viewport **1363 × 936**. Isso equivale a aproximadamente 15,5 alturas de viewport de conteúdo, **não a 15,5 scrolls humanos**. Confirma custo de extensão do menu mesmo no desktop. A contagem de gestos continua NM.
- Cozinha, após as jornadas: documento **4.146 px**. Resumo/fila/passe começaram em y=135 e cada coluna tinha 864 px. Tickets começaram em y=1.027; Disponibilidade em y=1.315 com **2.743 px de altura**. Logo, disponibilidade ficou abaixo da primeira tela mesmo com filas em três colunas desktop.
- Screenshot guest no topo mostrou equipe e discriminação financeira ocupando a primeira tela após abrir comanda; Cardápio estava abaixo. Não foi usada captura como prova de mutation; a prova veio da navegação e do estado retornado.
- Seletores rolaram automaticamente até controles. Essas rolagens não foram tratadas como ergonomia com uma mão nem contadas como gestos.
- Dados preexistentes de demonstração tinham idades de fila de milhares de minutos. Não foram interpretados como SLA real, carga de pico ou falha de funcionário.
- Não houve estado vazio completo reconstruído nem pico controlado; houve estado guest vazio, caixa fechado e operação normal com dados preexistentes.
- Não houve perda deliberada de conexão, throttling, duplo toque financeiro, recovery após timeout de commit ou kill do navegador. As conclusões desses casos permanecem inspeção/hipótese.
- Não houve benchmark com garçom/cozinheiro humano, nem amostra estatística de tempos.
- Não houve teste de SDK de pagamento, Tap to Pay, Pix, Android ou fiscal.

### H6. Registros e estado final da demo

As operações foram mantidas como evidência, sem apagar histórico:
- Comanda **AUDITORIA UX 12-10 1634**: duas rodadas, total nominal R$ 38, parcial fictício R$ 10, saldo visível R$ 28; três bebidas levadas ao passe; correção de Amstel Lata encaminhada para revisão/estorno.
- Comanda **AUDITORIA UX GUEST 12-10**: duas águas e Fritas, total R$ 38, sem recebimento; Fritas levada ao passe; pedido de conta atendido e concluído.
- As duas comandas seguem abertas; não houve pagamento total fictício adicional nem fechamento forçado.
- Turno criado no Caixa principal: fundo R$ 100, suprimento R$ 20, sangria R$ 10 e recebimento R$ 10; **fechado** com esperado R$ 120, contado R$ 119 e diferença -R$ 1. Revisão gerencial continua pendente.
- Fritas foi **reativada** após o ensaio de indisponibilidade.
- Não foram concluídas entregas ou pedidos de outras comandas, liberada a mesa compartilhada ou encerradas sessões guest alheias.
- Não houve estorno, revisão com novo PIN, mudança de configuração, branch, PR ou deploy.

### H7. Prioridade revisada

1. Corrigir o caminho de UX-34 e manter payloads financeiros pendentes íntegros (UX-08/22).
2. Preservar draft por comanda e tornar seleção/reseleção previsível (UX-06/35).
3. Reduzir nove ações de produção para o trabalho efetivamente necessário, com lote seguro (UX-03/04).
4. Tornar guest navegável com 146 produtos e revisão de quantidades (UX-14/15).
5. Levar alertas/pendências ao registro exato (UX-09/30).
6. Validar mobile e Android e repetir as jornadas em pico e rede ruim antes de afirmar ganhos de tempo.

As ondas G continuam propostas de implementação. A execução no navegador complementa o diagnóstico; não autoriza implementar nenhuma delas.
