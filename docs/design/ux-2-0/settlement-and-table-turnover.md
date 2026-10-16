# Rodada UX 2.0 — Fechar conta e girar a mesa

**Data:** 2026-10-16. **Status:** conceito/validação da jornada em protótipo isolado. Não é homologação do Caixa, do PSP, do Android nem da operação real.

## Problema

A jornada do Rodada não termina na entrega: o atendente/caixa precisa conferir consumo, cobrar ou registrar um recebimento permitido, zerar o saldo, encerrar **cada comanda financeira** e liberar a **ocupação física** quando o grupo sair. A limpeza é uma terceira transição, com responsabilidade operacional própria.

**Nunca confundir:**
- **Tab / comanda:** unidade financeira; pagamento parcial, ledger e encerramento independentes.
- **Table / mesa:** recurso físico; permite várias Tabs na mesma ocupação.
- **CashShift / caixa:** registro de gaveta/turno e conferência de dinheiro. Fechar uma Tab não fecha o turno nem a gaveta.
- **Liberar mesa:** encerra a ocupação e revoga acesso guest da geração anterior, mudando para DIRTY. Não equivale a fechar uma Tab.
- **Concluir limpeza:** torna a mesa AVAILABLE e incrementa access_generation; não altera consumo passado.

Referências normativas: \`specs/001-core-pos/spec.md\` (POS-008/009/012), \`specs/004-table-guest-ordering/spec.md\` (TABLE-003/004 e guest revocation), \`specs/006-payments/\` quando aplicável, \`specs/012-cash-management/spec.md\`, \`docs/domain/model.md\`, \`docs/product/principles.md\`.

## Fluxo aprovado para avaliação — fechamento rápido (sem revisões redundantes)

```text
Comanda → Conta → Receber (valor + método)
  ├─ Parcial → Registrar valor → Conta (permanece OPEN)
  ├─ Total + sem pendências → Receber e encerrar → Mesa diretamente
  └─ Total, mas deseja manter OPEN → Só registrar → Conta
Se saldo já é zero → Encerrar comanda diretamente (um toque)
Se há rascunho → voltar ao pedido ou descartar com confirmação explícita

Mesa com outras comandas abertas → resolver cada Tab
Mesa com READY pendente → Ver entregas
Mesa sem Tabs abertas nem entregas pendentes → Grupo saiu · Liberar mesa (um toque) → DIRTY
Limpeza: DIRTY → Iniciar limpeza → CLEANING → Mesa limpa · Disponibilizar → AVAILABLE
```

**Decisão UX:** botão final já expressa a confirmação e seu efeito. Foram removidas as telas separadas **Revisar encerramento**, **Revisar liberação** e o checkbox sobre saída do grupo. A mesa não é liberada só porque a última comanda foi paga; liberar é um comando explícito. A limpeza continua em etapa operacional distinta.

**Segurança:** a combinação de receber + encerrar só é válida após confirmação financeira e verificação canônica de saldo, sessão, idempotência e autorização pelo backend na futura integração. Se a resposta for incerta, jamais cobrar novamente nem declarar fechamento por otimismo. O protótipo usa estado em memória, sem qualquer pagamento real. Pedidos em rascunho impedem fechamento automático; descartá-los continua exigindo confirmação destrutiva.
### Requisitos por etapa

**Conferir conta:** título, nome/referência canônica da Tab, mesa se houver, valor de consumo confirmado, total recebido, saldo em aberto, histórico de recebimentos e alertas. Rascunhos não entram no total; ajustes e pagamentos seguem a API real, não somam valores do catálogo atual.

**Recebimentos:** a etapa pode representar CASH, CARD, PIX e parciais quando o backend/provedor confirmarem ou quando o registro manual for legitimamente permitido. Nunca chamar botão de "Pago" se o método ainda está pendente ou autorizado apenas como iniciação. Troco e caixa ativo seguem o contrato da Spec 012; pagamentos reais exigem idempotency key, autorização, sessão, validação server-side, readback e tratamento de resposta perdida. Valor deve ser positivo, não exceder exposição sem regra explícita e obedecer escala exata em centavos. Múltiplas pessoas na mesma mesa pagam suas Tabs sem misturar ledger.

**Encerrar Tab:** permitir fechamento ordinário somente com saldo canônico zero; divergência é intervenção gerencial auditada, nunca apagar saldo na UI. Não fechar com rascunho não enviado, envio de pedido/pagamento em estado incerto, sessão inválida ou autorização insuficiente. Produção confirmada pode continuar operacional conforme a Spec 001. A confirmação de Tab é separada de liberar a mesa.

**Liberar mesa:** UX conservadora do piloto pede todas as Tabs desta ocupação encerradas, entregas READY conferidas e confirmação humana de que o grupo efetivamente saiu. Essa regra de bloqueio para liberações cotidianas é proposta de UX, não uma afirmação de que o domínio proíbe toda liberação com Tab aberta; excepcionais/mudanças de localização devem seguir specs proprietárias. A transição OCCUPIED → DIRTY revoga guest requests da ocupação antiga; sessões antigas não devem reabrir sob a nova geração.

**Limpeza:** DIRTY → CLEANING → AVAILABLE são ações distintas. UI mostra status inequívoco e evita oferecer "Abrir comanda" enquanto DIRTY/CLEANING. Ao concluir, a nova geração não mostra Tabs encerradas da ocupação anterior como ativas. Histórico pode continuar acessível em módulo próprio.

## Protótipo funcional isolado

`prototype/ux-2-0/index.html` implementa em memória: saldo e recebimentos fictícios, pagamentos parciais; recebimento integral e encerramento em um comando explícito; opção de só registrar e manter OPEN; botão direto de encerrar quando saldo zero; confirmação destrutiva para descartar rascunho; separação de Tab/Table e bloqueio de liberação com Tabs abertas ou entregas READY; saída do grupo em um toque, depois limpeza separada. O histórico das visitas anteriores não é reutilizado na geração seguinte.

**Nenhum Payment, Pix, cartão, dinheiro, caixa, QR real ou fechamento de produção é afetado.** Recarregar reinicia a simulação. Revisão de browser Android, acessibilidade, concorrência e homologação do backend continuam pendentes.
## Cenários de aceite / teste humano no Android

1. Na Mesa 08, Marina tem R$ 56 e Rafael R$ 14. Registrar R$ 20 e depois R$ 36 na Tab de Marina; encerrar somente a de Marina; Rafael permanece aberto e a mesa não pode ser liberada.
2. Criar um rascunho em Rafael; pagar R$ 14; impedir encerramento até descartar explicitamente ou enviar o pedido. Confirmar que a conta de Marina não é alterada.
3. Com Rafael fechado, conferir entregas READY ainda pendentes (não pressupor que fechamento financeiro equivale a entrega).
4. Concluir entregas da Mesa 08; confirmar que o grupo saiu; liberar a mesa. Estado final deve ser DIRTY, com indicação clara de QR revogado.
5. Iniciar limpeza, depois concluir. A mesa volta a AVAILABLE; a geração nova não incorpora Tabs antigas.
6. Navegação Voltar não fecha comanda, não recebe dinheiro, não libera mesa e não conclui limpeza.
7. Validar múltiplas sessões, conflito de atualização, resposta perdida, reautenticação, permissões, saldo alterado e pagamentos ambíguos antes de implementar em produção.

## Instrumentação futura

Avaliar tempo entre pedido de conta → recebimento → Tab CLOSED; tempo entre última Tab CLOSED → mesa liberada; DIRTY → AVAILABLE; taxa de erro de destino e de intervenção gerencial. Não otimizar cliques escondendo riscos ou criando resultados financeiros fictícios.

## Próxima implementação real

Slice A: revisão canônica de BillSummary e estados de Tab no Atendimento + POS; Slice B: iniciação e confirmação/registro manual de pagamentos com proteções reais; Slice C: encerramento de Tab condicionado por backend; Slice D: liberação e limpeza da mesa, com geração de QR/session correta; Slice E: UX E2E com casos adversos em Web/Android. Manter PRs independentes, revisão de segurança financeira, screenshots 360/390/430 e aceite do operador antes do rollout.

**Fora de escopo agora:** mudar endpoints, banco, permissões, pagamento real, integração PSP, emissão fiscal, deploy ou Play Store.
