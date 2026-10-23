# Spec 035 — Critérios de aceite e matriz de QA

**Status:** `NOT RUN / NO-GO` para implementação real. Os checkboxes abaixo representam testes **a executar**, não aprovação implícita pelo protótipo.  
**Alvo:** Bar, Cozinha, Passe e Expedição em backend autoritativo, não HTML estático.

## Happy paths e limites por dispositivo

- [ ] **AC-01** Dado um pedido confirmado com 2 linhas Bar e 1 Cozinha, quando projetado, então cada estação vê apenas seus itens e cada linha mantém o mesmo `OrderItem.id`/estado sem misturar Tab.
- [ ] **AC-02** Dada ficha FG84, quando entrar pedido Bar, então FG84 é legível em Fila/Passe sem scan nem etapa obrigatória; a fila Bar nunca recebe item da Cozinha; se o pedido PICKUP também tiver Cozinha, ele aparece exclusivamente na estação KITCHEN conforme Spec 032.
- [ ] **AC-03** Dada Mesa 12 com duas Tabs, quando expedição/filtragem abrir a comanda A, então nenhuma linha da B entra na seleção.
- [ ] **AC-04** Dado burger normal + burger sem cebola, quando renderizados, então ambos têm linhas/customizações inequívocas e continuam independentes para status e lote.
- [ ] **AC-05** Dado item simples válido e etapa aceita pela API, quando operador tocar `Pronto`, então exatamente uma intenção canônica é aplicada; UI não forja READY ao receber erro/conflito.
- [ ] **AC-06** Dado pedido com dois itens elegíveis, quando usar conclusão em lote, então o servidor aplica todas as linhas ou rejeita todas; alergia/bloqueio/versão divergente impedem batch inseguro.
- [ ] **AC-07** Dada produção parcial de N unidades **após contrato aprovado**, quando 1 ficar pronto, então contador, Passe, Dispatch e auditoria convergem sem duplicar consumo financeiro.
- [ ] **AC-08** Dado novo pedido enquanto usuário está no Passe/Ajustes/Expedição, quando evento chegar, então aviso persistente mostra station/count e botão leva ao ticket certo; tocar no aviso não muda o pedido.
- [ ] **AC-09** Dado atraso/urgência, quando o relógio/eventos atualizam, então marcador textual aparece sem reordenar cartões no meio do trabalho.
- [ ] **AC-10** Dado Bar cheio, quando operador finaliza bebidas, então a ação principal é encontrada sem abrir menu e sem confirmar pickup/entrega para liberar novo trabalho.

## Passe/expedição e segurança

- [ ] **AC-11** Dado READY sem pickup após limite visual configurado, então registro continua acessível em “sem retirada registrada”; não criar `PICKED_UP`/`DELIVERED` automaticamente.
- [ ] **AC-12** Dada expedição opcional, quando um item estiver pronto e outro aguardando, então mostra o que falta e `Ver prontos deste pedido` filtra inclusive prontos antigos; `Ver Passe geral` remove filtro.
- [ ] **AC-13** Dado modo simples, quando item ficar pronto, então não há confirmação obrigatória de expedidor/retirada.
- [ ] **AC-14** Dada alergia não confirmada, quando tentar READY/lote, então ação segura exige conferência e não permite finalizar em lote indiscriminadamente.
- [ ] **AC-15** Dado risco de contato cruzado impossível de mitigar, quando selecionar “Não consigo preparar com segurança”, então status suspenso e encaminhamento ao responsável são **confirmados na API**; retomada exige autorização válida e log.
- [ ] **AC-16** Dada correção recebida durante preparo, quando o aviso aparecer, então operador entende `solicitada ≠ aplicada`; item não é alterado sem procedimento autorizado.
- [ ] **AC-17** Dado cancelar 1 de 3 antes do preparo, sem complicação financeira, quando autorizado, então ficam 2 unidades; repetir a mesma key não cancela outras; valor de Charge/reversão segue Spec 017.
- [ ] **AC-18** Dada tentativa de cancelar item PREPARING/READY/paid, quando ainda depende de manager/review, então UI mostra “aguardando” e só muda produção quando servidor confirmar; recusa mantém o estado original.
- [ ] **AC-19** Dado remake, quando aprovado, então nova linha possui ID e vínculo original, sem modificar histórico/estado/marcos do item anterior.
- [ ] **AC-20** Dado Produto indisponibilizado após confirmar pedido, então novos pedidos são bloqueados na confirmação canônica, mas o ticket anterior continua na produção.
- [ ] **AC-21** Dado acionamento de “Imprimir”, então indicar envio/êxito/falha verificáveis, sem afirmar impressão na falha; fallback conforme integração real.

## Falhas, concorrência e recuperação

- [ ] **AC-22** Dado SSE indisponível e API saudável, então UI explicita estado de frescor, executa leitura adequada e não trata cache como confirmação.
- [ ] **AC-23** Dado API indisponível, então ações não confirmadas ficam claramente pendentes/bloqueadas conforme operação; UI não inventa resultado.
- [ ] **AC-24** Dado ACK perdido após comando válido, então retry conserva **mesma identidade/chave/payload** e readback, sem duplicar READY, batches ou correções.
- [ ] **AC-25** Dadas duas sessões alterando mesmo item, então conflito 409/versão resolve com reconsulta e mensagem clara, sem aplicar a seleção obsoleta.
- [ ] **AC-26** Dada sessão expirada, Venue trocado ou falta de capability, então ações não podem mutar outro Venue nem aproveitar token ou intenção de outra sessão.

## UX, acessibilidade e pico

- [ ] **AC-27** Em `360/390/430 px`, retrato, navegação Fila/Passe/Produtos/Ajustes acessível sem rolar toda a fila; nenhuma ação essencial oculta, largura sem overflow horizontal não intencional.
- [ ] **AC-28** Em `768/850/1024` e `1280/1440/1920 px`, grade refluída de modo real (sem `transform: scale`), mouse/touch e variações retrato/paisagem sem clip; 30 tickets simultâneos.
- [ ] **AC-29** Com fonte 200%, teclado, TalkBack/VoiceOver ou leitor de tela desktop, destino, quantidade, restrição e CTA permanecem entendíveis; foco retorna ao item após modal/comando; TAB/Escape previsíveis.
- [ ] **AC-30** Botões touch >=44 px e CTA de produção preferencialmente >=56 px; estados distinguíveis por texto e cor; opção reduzir movimento respeitada.
- [ ] **AC-31** Dado clique em item X em fila de 30 e chegada de novo SSE, posição/foco não saltam para Y, botão não age em item diferente e notificação não repete áudio em replay.
- [ ] **AC-32** Nenhum operador precisa tocar em “Peguei/Entreguei” apenas para alimentar métricas; marcos inferidos preservam proveniência.
- [ ] **AC-33** Textos em português operacional: `Pedidos`, `Passe`, `Resumo por produto`, `Marcar pronto`, `Corrigir/refazer`; termos de laboratório como `Simular aprovação` não aparecem no produto.
- [ ] **AC-34** Revisão com bartender e cozinheiro executando tarefas representativas em hardware, com erros observados e condições documentadas; aprovação explícita antes do rollout.

## Evidências/gates obrigatórios

| Gate | Comando/artefato esperado | Resultado neste commit |
| --- | --- | --- |
| Código Web | build, lint, TypeScript, unit/components por PR | **não executado** |
| Visual | `cd apps/web && npm run test:visual` e screenshots comparáveis | **não executado** |
| Domínio | Django/pytest + DB, concorrência, ledger/dispatch quando afetados | **não executado** |
| Realtime/recovery | SSE/snapshot/replay, API down, ACK perdido, duas sessões | **não executado** |
| Segurança | auth/venue/capabilities, alergia/correção auditadas | **não executado** |
| Homologação | operador, tablet/PC/celular físicos, impressão/fallback | **não executado** |
| Deploy | CI do SHA e aprovação de release separados | **não executado** |

**Nota de evidência:** as iterações do HTML já tiveram testes de navegação relatados na discussão de design, mas esses relatos **não validam o aplicativo conectado** e não são marcados como PASS nos critérios acima. Esta entrega altera somente documentação em branch de protótipo.

## Paridade visual — AC-35 a AC-46 (nenhuma executada)

- [ ] **AC-35** A referência foi importada sem alteração a partir do blob SHA 8b4a2a4a5f2e90496c4aa54156ad0428590dc6c5, com commit/manifesto e captura #surface isolada.
- [ ] **AC-36** O mesmo conjunto determinístico de Orders/Tabs/códigos/relógio alimenta HTML e API/Web, sem dados reais do Aderlan nem mascaramento de diferenças semânticas.
- [ ] **AC-37** Bar e Cozinha, na fila normal, apresentam shell, header, 3 métricas e cards com <=2px de diferença de bounding boxes principais e contorno de CTA conforme visual-parity.md.
- [ ] **AC-38** As regiões operacionais estáticas comparáveis apresentam pixel diff <=2% e regiões de destino, ação e aviso crítico <=1% (pixelmatch threshold 0.1), em 390/850/1200/1440 com evidências guardadas.
- [ ] **AC-39** Navegação mobile inferior e desktop superior, grades 1/2/3, safe-area e rolagem interna mantêm posição/sem overflow em 360/390/430/768/850/1024/1200/1440/1920.
- [ ] **AC-40** Passe recente/antigo, Resumo por produto, Expedição ativa/inativa e Ajustes reproduzem estruturas/CTAs/estados do protótipo em Bar/Cozinha; filtro por ID não confunde duas Tabs na mesma mesa.
- [ ] **AC-41** Modal de alergia, alteração, bloqueio, correção, ACK incerto e erro 409 apresenta hierarquia visual equivalente ou variante explicitamente aprovada; foco acessível/retornado.
- [ ] **AC-42** Texto 200%, teclado, toque, screen reader, reduzido movimento, alertas textuais e targets >=44 px passam sem comprometer a primeira ação.
- [ ] **AC-43** Um drift introduzido no teste faz o gate visual falhar; restaurar UI retorna PASS sem regenerar o baseline silenciosamente.
- [ ] **AC-44** IMMEDIATE_PICKUP (água/refrigerante/cerveja embalados) permite uma ação server-authoritative a READY, sem PREPARING artificial na UX e sem evento de entrega inventado; PREPARED não muda.
- [ ] **AC-45** Cada PR de UI publica referência, resultado, diff, fontes/versões, fixture, porcentagem por região, trace e revisão independente; nenhum AC é marcado PASS sem execução.
- [ ] **AC-46** GO da Spec 035 só após AC-01..46 PASS, contrato READY direto/parciais/alergia resolvidos ou recortes explicitamente não disponibilizados, testes de domínio, paridade Bar+Cozinha e validação operacional; CI verde isolado não é homologação.
