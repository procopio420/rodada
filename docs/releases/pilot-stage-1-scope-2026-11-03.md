# Etapa 1 — escopo proposto da primeira versão utilizável

Data: 03/11/2026. Estado: **CONCLUIDA — ESCOPO APROVADO**. Preparação documental
e aprovação humana registradas. Solicitação: “Execute a etapa 1
do PR #324”. Risco R1: proposta sem alteração de produto, permissões ou operação.

## Base e limites da evidência

- Main remota consultada: `67972d09200d43357b5b88dc0f64218967e4c24b`.
- [PR #324](https://github.com/procopio420/rodada/pull/324): aberto e draft,
  HEAD `1b6b20c74925f20d29e91f52dd9f96dc80669c89`; plano lido na branch
  `codex/pilot-execution-plan`, inclusive diff documental e discussão sem comentários.
- Branch local de entrega: `codex/pilot-stage-1-scope`, baseada nesse HEAD.
- [Plano por etapas](pilot-execution-plan-2026-11-03.md),
  [aceite Spec033](../../specs/033-attendance-ux2-productization/acceptance.md),
  [contratos Spec035](../../specs/035-bar-kitchen-ux2/contract-matrix.md) e
  [Spec032](../../specs/032-guest-entry-and-bar-pickup/spec.md) preservados.
- Issues [315](https://github.com/procopio420/rodada/issues/315),
  [316](https://github.com/procopio420/rodada/issues/316),
  [317](https://github.com/procopio420/rodada/issues/317),
  [318](https://github.com/procopio420/rodada/issues/318) e
  [319](https://github.com/procopio420/rodada/issues/319) consultadas: abertas.
  Permanece NO-GO de produção e aceite global Spec033 pendente.
- [PR #314](https://github.com/procopio420/rodada/pull/314): aberto, não mergeado,
  HEAD `6df4599d89ca3034179d240cc2eb3b26cef154f2`. Retirada imediata exige
  conciliação com Spec035; não compõe a capacidade disponível deste piloto.

Esta etapa define o que deverá ser ensaiado e homologado. Não comprova que os
fluxos passaram em teste integrado, hardware ou produção. O roteiro Web de
[14/10](aderlan-web-only-homologation-2026-10-14.md) é referência histórica.

## Recomendação

Piloto assistido Web em um estabelecimento, com Atendimento, Bar, Cozinha,
Gerência, Caixa e QR guest existente. Priorizar atendimento de mesa e entrega
pela equipe, com recebimentos manuais após conferência externa. Não exigir
conclusão de toda a UX2 do Bar/Cozinha para esse recorte.

Limitar operadores, mesas/comandas e janela de atendimento antes da etapa 6,
conforme capacidade observada no ensaio. Quantidades e duração ainda dependem
do responsável do bar; não há capacidade de pico comprovada.

## Matriz de módulos e fluxos

“Incluído” abaixo é recomendação de escopo sujeita à aprovação, sem declaração
de homologação. Operadores são funções de trabalho, não novos papéis de acesso.

| Módulo/fluxo | Proposta | Mínimo para aceitar o recorte | Responsável proposto |
| --- | --- | --- | --- |
| Atendimento Web | Incluído | Abrir ocupação/Tab, pedido misto BAR+KITCHEN, acompanhar, entregar e consultar conta; duas Tabs na mesma mesa sem confusão | Líder de atendimento + agente no ensaio |
| Bar Web | Incluído, interface existente | Fila BAR, iniciar preparo, marcar pronto e disponibilizar à entrega com IDs canônicos; recuperar desconexão | Operador do bar |
| Cozinha Web | Incluído, interface existente | Fila KITCHEN e transições autorizadas; observações preservadas; pronto não implica entregue | Operador da cozinha |
| Gerência Web | Incluído | Catálogo/preços/disponibilidade, exceções autorizadas, auditoria e leitura dos relatórios de operação | Gerente |
| Caixa Web | Incluído | Abertura/fechamento de turno, parcial/integral, saldo/troco, divergência e revisão; totais conciliados com prova externa | Caixa + gerente |
| Mesa/limpeza | Incluído | Fechar Tab não libera mesa; saída explícita e OCCUPIED→DIRTY→CLEANING→AVAILABLE; revogar acesso antigo | Atendimento + responsável pela limpeza |
| QR guest atual | Incluído no ensaio e sujeito à homologação | Cardápio/pedido/conta/chamadas conforme capacidades existentes e política do Venue; isolamento e revogação testados | Atendimento + agente |
| Correção/cancelamento/estorno | Incluído como exceção existente | Motivo, autorização, trilha e efeito correto em produção/ledger; sem apagar histórico | Gerente/caixa autorizado |
| Balcão/Tab sem mesa | Cenário de ensaio conforme configuração existente | Tab obrigatória e destino canônico; não prometer retirada por ficha | Atendimento + gerente |
| Retirada imediata / PR #314 | Adiada | Reconciliar política de preparo, estação e modalidade antes de implementar etapa 3A | Agente; usuário prioriza |
| Redesign completo Bar/Cozinha, Passe/Expedição e parciais novos | Adiado | Slices Spec035 somente por necessidade priorizada | Usuário + agente |
| Android nativo | Adiado, decisão explícita pendente | Se incluído, ampliar ensaio e provas físicas/TalkBack/recovery | Usuário + operador com aparelho |
| Impressora física Rodada | Adiada, decisão explícita pendente | Se incluída, trilha issue #285 e prova física da versão distribuída | Usuário + operador de impressão |
| PSP/Tap/Pix integrado | Adiado, decisão explícita pendente | Se incluído, contrato/provedor, confirmação canônica e homologação próprios | Usuário + responsável financeiro |
| QR híbrido, QR geral e ficha FG84 | Adiados, decisão explícita pendente | Spec032/issue #214; código público não autoriza acesso ou quitação | Usuário + agente |

O QR guest existente não é a jornada futura da Spec032. Incluir QR atual não
inclui autoabertura híbrida, vínculo de tags, QR geral ou retirada FG84.
Adiar um recorte não remove funcionalidades instaladas nem modifica acesso.

## Equipamentos e rede

| Posto | Equipamento recomendado | Confirmação necessária / responsável |
| --- | --- | --- |
| Atendimento | Celular com navegador suportado, bateria/carregador e Wi-Fi | Modelo, SO, navegador e quantidade — líder de atendimento |
| Bar | Tela dedicada com navegador, energia e rede estável | Modelo, tamanho, touch/teclado e local protegido — operador do bar |
| Cozinha | Tela dedicada com navegador, energia e rede estável | Legibilidade, toque e local de uso — operador da cozinha |
| Caixa/Gerência | PC ou tablet com navegador e maquininha externa quando usada | Perfis/sessões separados por operador; modelo e versão — gerente |
| Guest QR | Celular de teste com câmera/navegador e QR atual do contexto autorizado | Usar dados sintéticos no ensaio — agente/atendimento |
| Rede/contingência | Wi-Fi cobrindo postos e alternativa operacional de queda | Testar perda/retorno, energia e cobertura — responsável local de rede a nomear |

Matriz Web exigida: 360/390/430 px e desktop, foco/teclado, fonte ampliada e
toque real nos equipamentos escolhidos. Usar navegador no celular Android não
equivale a homologar o aplicativo Android nativo. Inventário físico fica pendente
até o usuário indicar equipamentos; não há prova física nesta etapa.

## Recebimentos e contingência fiscal

| Meio | Proposta | Regra para registro |
| --- | --- | --- |
| Dinheiro | Incluído | Caixa confere valor recebido e troco antes do lançamento autorizado |
| Débito/crédito em maquininha externa | Incluído se disponível no local | Conferir transação aprovada/comprovante externo, depois registrar método/valor; conciliar no fechamento |
| Pix externo/manual | Decisão pendente; recomendado deixar fora inicialmente | Se escolhido, exigir confirmação no banco pelo responsável e método suportado; tela do cliente não prova crédito |
| PSP/Tap/Pix integrado | Adiado | Não anunciar liquidação, garantia ou caução sem fonte canônica |

Pagamento parcial não fecha Tab automaticamente. ACK incerto exige readback e
replay da intenção original, sem segundo lançamento. Dinheiro em centavos e
ledger auditável continuam obrigatórios. Na etapa 2, todos os pagamentos serão
sintéticos em PostgreSQL/Venue descartáveis.

**Pendência fiscal:** usuário deve nomear responsável pela emissão fiscal e
confirmar o sistema/procedimento legal e sua contingência com o estabelecimento.
Proposta: manter o sistema fiscal vigente (VR System, se confirmado pelo bar)
disponível com operador treinado e rotina de conciliação. Recibo Rodada é
documento não fiscal. Sem contingência fiscal validada, manter NO-GO para dados
reais. Contingência operacional não substitui rollback técnico do Rodada.

## Contas, papéis e responsáveis

Fonte estática de papéis: [capabilities da API](../../apps/api/modules/access/capabilities.py).
Papéis existentes: STAFF, CASHIER, MANAGER e OWNER; permissões efetivas também
dependem de vínculo ativo e overrides. Não criar contas ou mudar grants nesta etapa.

| Função | Proposta de conta/papel | Validação exigida |
| --- | --- | --- |
| Atendimento | Conta individual STAFF | Tab/pedido/mesa; receber dinheiro exige capability própria, não presumida por ser garçom |
| Bar/Cozinha | Conta individual com acesso à estação autorizado no servidor | Confirmar política/capabilities efetivas de produção e indisponibilidade; não inventar papéis BAR/KITCHEN nem conceder MANAGER só para abrir tela |
| Caixa | Conta individual CASHIER | payment.collect, abertura/ajustes de caixa conforme política; revisão/estorno gerencial não presumidos |
| Gerente | Conta individual MANAGER | Revisão de caixa, estornos/exceções e catálogo conforme grants efetivos |
| Proprietário | OWNER para responsável designado | Configuração/acesso administrativo; evitar uso compartilhado no turno |
| Guest | Sessão guest do contexto autorizado | Sem conta staff; QR/mesa não concedem acesso financeiro a terceiros |

Usuário decide escopo e nomeia líder do piloto, operadores, responsável fiscal,
suporte/release e responsável pela rede. Agente prepara ensaio e evidências;
revisor independente valida R3 no candidato. Não há pessoas nomeadas nem
disponibilidade operacional confirmada neste chat.

## Critérios mínimos antes de piloto real

1. Escopo aprovado pelo usuário e decisões abaixo registradas.
2. Etapa 2: jornada Web integrada com PostgreSQL, pedido BAR+KITCHEN,
   produção/entrega, pagamento parcial/integral, caixa e mesa, com IDs/totais.
3. Casos adversos: duas Tabs na mesma mesa, indisponibilidade após carrinho,
   isolamento entre Venues, sessão/QR revogados, concorrência, queda de rede,
   ACK perdido e replay sem duplicar Order/Charge/Payment.
4. Corrigir e retestar impedimentos P0/P1 do recorte; interface atual de produção
   só é aceitável se o fluxo for utilizável no equipamento real.
5. Revisão R3 independente válida, backup/restore e rollback técnico ensaiados;
   retenção periódica de telemetria comprovada, monitorada e com responsável
   antes de dados reais. Nenhum gate financeiro/auth é dispensado pelo Web-only.
6. Equipamentos/rede/acessibilidade homologados, equipe treinada, contingência
   fiscal aprovada, suporte e critérios de interrupção definidos.
7. Alvo, candidato, janela/limites e ações de publicação aprovados especificamente;
   GO humano limitado ao escopo validado, após as demais etapas aplicáveis.

Nenhum critério acima é marcado PASS nesta etapa. O recorte Web não encerra
ACs Android nem as issues315–319 ou o aceite global da Spec033.

## Decisões de escopo

Aprovação humana em 03/11/2026, neste chat: “aprovo pode fazer”, em resposta
à proposta de escopo da etapa 1. D1–D4 aprovadas conforme recomendação abaixo.
Esta aprovação não identifica responsáveis/equipamentos nem autoriza publicação.

| Decisão | Recomendação | Estado |
| --- | --- | --- |
| D1 — módulos | Web: Atendimento, Bar, Cozinha, Gerência, Caixa e QR guest atual | APROVADA |
| D2 — plataformas/integrações | Adiar Android nativo, impressora, PSP integrado e QR híbrido/FG84 | APROVADA; inclusão futura exige decisão explícita |
| D3 — meios externos | Dinheiro e cartão em maquininha; Pix manual fora inicialmente | APROVADA |
| D4 — fluxo de produção | Fluxo atual, sem incorporar PR314 ou exigir UX2 completa | APROVADA |
| D5 — fiscal | Confirmar sistema vigente/contingência e responsável | Pendente de informação do bar |
| D6 — equipe/equipamentos | Nomear funções e inventariar dispositivos antes da homologação | Pendente de informação do bar |

A aprovação D1–D4 fecha a etapa 1 e a decisão de escopo para o ensaio, mantendo D5–D6
explicitamente pendentes para operação real. Incluir integrações altera a matriz
e os critérios pertinentes antes de avançar. Nenhuma etapa seguinte é executada
automaticamente; próxima entrega prevista é o ensaio da etapa 2, pelo agente,
quando solicitado. Decisão: GO para o escopo do ensaio; NO-GO para produção.

## Validação documental e handoff

Atualização na execução da etapa 2 (03/11/2026): localizado Python 3.12.14
incluído no aplicativo. Gate KB executado com PASS (49 documentos/309 links)
e cinco testes com PASS. Isso resolve o bloqueio ambiental registrado abaixo,
preservado como histórico da primeira tentativa. Escopo continua aprovado.

Arquivos desta entrega: este relatório, link no índice de agentes e atualização
datada do acompanhamento no plano. Sem alteração de spec/ADR ou produto.
Validações desta entrega:

- PASS: conferência local dos três documentos com Node, 52 links locais,
  nenhum destino ausente; não substitui o verificador completo de KB.
- PASS: `git diff --check` e revisão documental do diff e do novo relatório.
- PASS: `git ls-remote` confirmou os SHAs de main e do plano listados acima.
- BLOCKED: `python scripts/check_agent_kb.py` e os cinco testes de
  `test_check_agent_kb.py`: tentados, mas Python indisponível neste ambiente.

Alterações locais ainda sem commit; os SHAs acima identificam as bases, não
um candidato de release. Executar o gate completo da KB em ambiente com Python
antes de apresentar esta alteração como PR validado.
Testes de produto, integração, visuais e hardware: NOT_RUN, pois não houve
mudança de produto nem execução das etapas 2–6. Sem merge, deploy ou escrita remota.
