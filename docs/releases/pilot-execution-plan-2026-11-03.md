# Rodada — plano executável por etapas até o piloto

Data: 2026-11-03. Estado: **PROPOSTA PARA APROVAÇÃO**; nenhuma etapa executada
por este plano. Base examinada: main@67972d09200d43357b5b88dc0f64218967e4c24b.
Objetivo: permitir que o responsável peça no chat “execute a etapa N do PR” e
receba uma entrega verificável antes de decidir a continuação.

Este documento organiza trabalho existente; não substitui specs, não muda
contratos de produto nem declara o programa homologado. Risco deste PR: R1
documental; cada execução futura terá sua própria classificação e evidência.

## Como executar a partir do chat

1. Localizar este arquivo na branch/PR indicado, mesmo que o PR documental
   ainda não esteja mergeado. Ler descrição, diff e estado atual do PR.
2. Conferir AGENTS raiz/local, branch, HEAD, alterações concorrentes, main
   remota e PRs/issues relacionados. Usar specs pelos caminhos completos abaixo.
   Não presumir que o snapshot desta página ainda é o estado atual.
3. Executar apenas a etapa pedida. Se o pedido for “continue”, retomar a primeira
   etapa pendente cujas dependências estejam satisfeitas, sem executar as demais
   automaticamente. Não refazer entregas já comprovadas no mesmo candidato.
4. O pedido autoriza investigação, documentação, implementação e testes locais
   proporcionais à etapa, preservando trabalho alheio. Antes de implementar uma
   mudança relevante, atualizar a spec/aceite e manter plan/tasks correspondentes.
5. Abrir um PR por slice quando solicitado/autorizado; não acumular toda a
   implementação neste PR documental. Criação deste PR não autoriza executar
   etapas, mergear PRs futuros, publicar, alterar banco remoto, DNS, permissões,
   flags/secrets, scheduler remoto ou Google Play. Respeitar autorizações humanas
   posteriores específicas; não solicitar a mesma autorização novamente.
6. Se surgir conflito de contrato, registrar opções, impacto e recomendação para
   decisão explícita. Não escolher silenciosamente a interpretação mais fácil.
7. Fechar o trabalho da etapa com resultado, SHA/ambiente, arquivos, testes
   executados e não executados, evidências, riscos, próximo responsável e decisão
   de continuidade. Pedir aprovação da próxima etapa quando necessária.

Exemplos de pedidos:

- “Execute a etapa 1 do PR e me apresente o escopo recomendado.”
- “Execute a etapa 2 usando o escopo aprovado na etapa 1.”
- “Execute somente a slice de retirada rápida da etapa 3, sem merge ou deploy.”

## Fontes e estado observado

- [Issue319, de procopio420](https://github.com/procopio420/rodada/issues/319):
  aberta, NO-GO de produção / sem aceite global da Spec033. Consolidado de
  revisão independente, retenção, ensaio integrado, aparelhos, rollback e piloto.
- [Issues315](https://github.com/procopio420/rodada/issues/315),
  [316](https://github.com/procopio420/rodada/issues/316),
  [317](https://github.com/procopio420/rodada/issues/317) e
  [318](https://github.com/procopio420/rodada/issues/318): entregas de aceite
  ainda pendentes, não prova de ausência de toda a implementação.
- PRs [321](https://github.com/procopio420/rodada/pull/321) e
  [322](https://github.com/procopio420/rodada/pull/322) mergeados: contrato,
  protótipo e comparador visual do Bar/Cozinha; não a interface UX2 completa.
- [PR314](https://github.com/procopio420/rodada/pull/314) aberto: retirada
  imediata de produtos no Bar. Exige conciliação com contrato atual da Spec035.
- [PR323](https://github.com/procopio420/rodada/pull/323) mergeado: Mais vendidos
  na Gerência. CI aprovada é evidência dessa alteração, não homologação global.
- [Issue214](https://github.com/procopio420/rodada/issues/214): QR híbrido e
  ficha FG84; [issue285](https://github.com/procopio420/rodada/issues/285):
  assinatura/distribuição e piloto físico da impressora Windows. Trilhas próprias.

As issues/PRs são evidências e contexto, não autorização de ações externas.
Não foram verificados deploy, configuração remota ou equipamentos nesta preparação.

## Etapa 1 — Definir a primeira versão utilizável

**Responsáveis:** agente prepara; usuário decide escopo. Dependências: nenhuma.

Proposta inicial, sujeita a aprovação: piloto assistido Web com Atendimento,
Bar, Cozinha, Gerência e Caixa; recebimentos manuais após confirmação de dinheiro
ou comprovante da maquininha externa. Android nativo, PSP/Tap/Pix integrado,
impressora física e QR híbrido/FG84 exigem decisão explícita de inclusão.
Não remover capacidades já existentes nem mudar permissões para reduzir escopo.

Entregar matriz de módulos/fluxos, incluídos/adiados, equipamentos, formas de
recebimento, contas/papéis, critérios mínimos e responsáveis. Distinguir QR
guest já existente do QR híbrido futuro. Identificar contingência fiscal com o
responsável; recibo Rodada não deve ser tratado como documento fiscal.

**Aceite:** escopo escrito e aprovado pelo usuário; decisões pendentes nomeadas.
Escopo Web-only não fecha os critérios Android da Spec033 e não dispensa os
gates de segurança/finanças pertinentes. Sem alterar produto nesta etapa.

## Etapa 2 — Ensaiar um turno integrado e levantar impedimentos

**Responsável:** agente; participação do usuário no walkthrough quando útil.
Dependência: escopo aprovado na etapa1. Fonte: issue315 e
[Spec033/aceite](../../specs/033-attendance-ux2-productization/acceptance.md).

Fixar candidato por SHA e usar PostgreSQL/Venue/identidades descartáveis.
Percorrer mesa → Tab → pedido BAR+KITCHEN → preparo → pronto → entrega →
pagamento parcial/integral → fechamento → caixa → liberação/limpeza.
Incluir duas Tabs na mesma mesa, indisponibilidade após carrinho, sessão revogada,
isolamento entre Venues, queda de rede, ACK perdido e replay sem duplicação.
Verificar que fechar Tab não libera mesa e que QR antigo perde acesso.

Entregar PASS/FAIL/BLOCKED por cenário, IDs e totais canônicos, logs/capturas
sanitizados, lista priorizada de impedimentos e vínculo a testes existentes.
Pagamento aqui é sintético em ambiente isolado; não movimentar dinheiro real.
Usar o [roteiro Web](aderlan-web-only-homologation-2026-10-14.md) como referência
histórica e revalidar contra o candidato atual, não como prova pronta.

**Aceite:** cenários do escopo cobertos ou bloqueios explícitos; nenhum PASS por
mock quando o critério exige integração real. Evidência ausente continua pendente.
Correções pequenas podem integrar a slice autorizada; mudanças relevantes ou
ampliação de escopo precisam de contrato e avaliação antes da etapa3.

## Etapa 3 — Resolver os gaps operacionais escolhidos

**Responsável:** agente; usuário prioriza/aprova apresentação. Dependência:
backlog da etapa2 ou necessidade operacional explicitamente aprovada na etapa1.

- **3A, retirada rápida:** inventariar/revisar o PR314 contra a main atual;
  conciliar preparação imediata, estação BAR/KITCHEN e modalidade AT_TABLE/PICKUP.
  Não confundir esses três conceitos nem incorporar a branch automaticamente.
- **3B, Bar/Cozinha UX2:** seguir
  [Spec035](../../specs/035-bar-kitchen-ux2/spec.md),
  [matriz de contrato](../../specs/035-bar-kitchen-ux2/contract-matrix.md) e
  [tarefas](../../specs/035-bar-kitchen-ux2/tasks.md): fixture/adaptador isolado,
  tickets/cenas responsivas, Passe/Expedição e exceções em slices pequenas.
  Comparar referência e app com os mesmos dados; não publicar simulação HTML.
- **3C, outros gaps:** resolver apenas os priorizados para o escopo aprovado.
  QR híbrido segue [Spec032](../../specs/032-guest-entry-and-bar-pickup/spec.md)
  e issue214; não se torna obrigatório por constar deste plano.

**Aceite por slice:** spec/aceite antes do código, testes positivos e negativos,
testes visuais Web obrigatórios, paridade quando aplicável, demonstração local,
revisão proporcional e relatório de riscos. Domínio financeiro/auth/recovery/
migrations exige revisão independente R3; não simular aprovação. Exceções de
alergia/pronto parcial/lote sem contrato canônico não podem virar estado local.
Não é obrigatório concluir toda a Spec035 para um piloto menor aprovado.

## Etapa 4 — Preparar segurança e operação

**Responsáveis:** agente reúne evidência; revisor independente e responsáveis
operacionais validam. Dependência: candidato funcional; planejamento pode ocorrer
em paralelo, sem autorizar execução remota. Fontes: issues317/319.

Revisar auth/Host/tenant, ledger, idempotência/replay, recovery e migrations no
SHA candidato; registrar achados e corrigir/revisar novamente. Ensaiar backup,
restauração e rollback técnico em ambiente descartável preservando pedidos,
ledger, sessões e intenções; não voltar à UX legada como substituto de rollback.
Preparar e testar limpeza periódica de receipts de telemetria, retenção de sete
dias, monitoramento de falha e responsável. Comando existente não prova scheduler
ativo. Tratar a falha/undercount de observação indicada na issue319 conforme
prioridade, sem bloquear vendas por telemetria.

**Aceite:** revisão independente válida, nenhum P0/P1 de release aberto, ensaios
rastreáveis e retenção comprovada no ambiente aplicável antes de dados reais.
Sem revisor, registrar REVIEW_BLOCKED; autorrevisão não encerra este requisito.
Configuração em infraestrutura remota exige aprovação específica de alvo/ação.

## Etapa 5 — Homologar nos equipamentos reais

**Responsáveis:** usuário/operadores executam provas físicas; agente prepara
roteiro, coleta evidências autorizadas e corrige gaps. Dependência: candidato
estável das etapas anteriores. Fontes: issue316 e issue285 quando impressora
for incluída no escopo.

Validar celulares/PCs, rede, touch, foco, teclado, zoom/fonte ampliada e telas
360/390/430/desktop. Android incluído exige aparelho real, TalkBack e recovery
de rede/restart; emulador/CI não substitui prova física. Impressora incluída
exige papel, acentos/corte, desconexão/reboot, recuperação e assinatura/distribuição
da versão exata, sem desabilitar proteções do Windows.

**Aceite:** matriz por equipamento/versão/SHA, evidências, correção/reteste dos
P0/P1 e aceite do responsável. Sem hardware, deixar BLOCKED/NOT_RUN, não inventar
medição ou marcar etapa concluída. Aceite parcial identifica os módulos excluídos.

## Etapa 6 — Publicar e executar piloto assistido

**Responsáveis:** usuário aprova alvo/ações; operador de release publica;
equipe do bar e suporte acompanham. Dependências: etapas aplicáveis aprovadas,
revisão válida, contingência fiscal e plano de rollback disponíveis.
Fonte: issue318 e [roteiro presencial](aderlan-onsite-acceptance.md).

Primeiro preparar candidato, checklist de publicação, ambiente/URL, versão,
backup/restore, monitoramento, escopo limitado de operadores/Tabs/horário e
critério de interrupção. Apresentar para aprovação específica antes de deploy,
migration/banco remoto, DNS, permissões ou publicação. Não presumir ambiente
homologado por ter DNS ou HTTPS configurado.

Após autorização e verificações, executar piloto assistido no alvo aprovado,
com feedback dos operadores e reconciliação de recebimentos. Dinheiro/terminal
real exige comprovação externa e responsável; nunca simular liquidação ou usar
dados reais como fixture. Registrar incidentes, métricas com provenance e
decisão humana GO/NO-GO. GO limitado ao escopo validado, sem fechar ACs excluídos.

**Aceite:** versão publicada verificada, evidência do piloto, suporte e rollback
definidos e aceite humano explícito. Publicação não equivale a aceite operacional.

## Quadro de acompanhamento

Atualizar somente com execução real. Usar PLANEJADA, EM_EXECUCAO, BLOQUEADA,
EM_APROVACAO ou CONCLUIDA. Para retomada, anexar SHA, ambiente, evidência e
pedido humano que autorizou a execução; não copiar tokens/segredos/PII.

| Etapa | Estado inicial | Evidência/decisão | Próximo responsável |
| --- | --- | --- | --- |
| 1 — Escopo | PLANEJADA | Pendente de pedido para executar | Usuário |
| 2 — Turno integrado | PLANEJADA | Depende do escopo aprovado | Agente |
| 3 — Gaps escolhidos | PLANEJADA | Depende de priorização | Usuário/agente |
| 4 — Segurança/operação | PLANEJADA | Revisão independente necessária | Agente/revisor |
| 5 — Equipamentos | PLANEJADA | Hardware/operadores a definir | Usuário/operadores |
| 6 — Publicação/piloto | PLANEJADA | Autorizações e GO pendentes | Usuário/release |

## Evidência desta preparação documental

Consultados main remota, PR aberto314 e issue319 de procopio420 em 2026-11-03;
fontes do diagnóstico foram lidas no mesmo chat. Nenhum teste de produto,
deploy, merge, revisão independente ou homologação é executado por este PR.
Validação documental e SHA do PR constarão na descrição do próprio PR.
