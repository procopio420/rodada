# Etapa 5 — homologação física do piloto Web

Roteiro preparado para o escopo aprovado na [etapa 1](pilot-stage-1-scope-2026-11-03.md), com os [critérios físicos da issue #316](https://github.com/procopio420/rodada/issues/316). Referência de código: `783869db27eccfb30654fe3769126841cc5f9499`, [PR #325](https://github.com/procopio420/rodada/pull/325). Conferir o SHA efetivamente servido antes de iniciar. Todos os cenários físicos estão **NOT_RUN**. Android nativo, impressora, retirada imediata e PSP/Pix integrado seguem fora deste recorte.

Antes da sessão, registrar ambiente e URL aprovados, Venue de teste, versão servida, responsáveis pelo ensaio e pela contingência, equipamentos, SO, navegador, viewport e rede. Usar comandas e contas de teste autorizadas. O operador do caixa confere a aprovação na maquininha antes de registrar cartão externo. Qualquer movimentação real na maquininha depende do responsável financeiro.

| Posto | Cenário | Evidência para passar |
| --- | --- | --- |
| Atendimento Web em celular | Abrir duas comandas na mesma mesa, confirmar pedido misto e localizar a conta correta | Um pedido por envio, destino fixo, histórico na comanda certa e toque utilizável |
| Bar e Cozinha em telas físicas | Conferir fila por estação, iniciar preparo, marcar pronto e entregar no Atendimento | Itens chegam à estação correta, preparo inicia por ação explícita e a entrega fica registrada |
| Cliente por QR em celular | Ler o QR físico, pedir e tentar usar a sessão antiga após a liberação | Pedido na comanda certa e sessão anterior perde acesso após liberação |
| Caixa e Gerência em desktop | Registrar dinheiro e cartão externo após conferência, testar parcial e integral, reconciliar fechamento | Saldo e comprovantes conferem. Cartão externo não movimenta o caixa em dinheiro. Fechar a conta mantém a mesa ocupada |
| Atendimento em celular e desktop | Busca, foco após cancelar descarte, teclado, Escape/Voltar, fonte ampliada e zoom | Ação principal acessível, foco previsível e controles sem sobreposição que impeça toque |
| Atendimento e produção na rede do piloto | Interromper e retomar Wi-Fi durante tarefa de teste, recarregar e conferir situação canônica | Intenção preservada, recuperação na sessão original e nenhum pedido ou pagamento duplicado |

Cobrir Web em 360, 390 e 430 px e desktop. Registrar se cada largura foi medida em aparelho ou em simulação. Para a amostra de 50 tarefas da issue #316, distribuir as tarefas pelos postos Web e registrar cada tentativa individualmente. Pausar o ensaio ao encontrar duplicação, falso sucesso financeiro, perda de intenção ou acesso indevido. Classificar P0/P1/P2 e retestar os fluxos afetados após corrigir P0/P1.

| Data/hora | Posto e tarefa | Aparelho, SO, navegador e largura | SHA | PASS/FAIL/BLOCKED/NOT_RUN | Evidência e responsável |
| --- | --- | --- | --- | --- | --- |
| A preencher | | | | NOT_RUN | |

O responsável pelo piloto registra o aceite Web e as exclusões. O fechamento da etapa 4 ainda depende de evidência da agenda, entrega do alerta e rollback no ambiente aplicável, além da revisão R3 autenticada. [Ensaios locais da etapa 4](pilot-stage4-local-rehearsal-2026-11-04.md)
