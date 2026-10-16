# Rodada UX 2.0 — Perfil, progress bar de limite e garantias

**Status:** experimento de UX, não integração. **Data:** 2026-10-16. **Referência canônica:** `specs/002-house-account/spec.md`, `docs/adr/0011-house-account-policy-snapshots-and-operational-approval.md`, `specs/002-house-account/acceptance.md`.

## Decisão de interface

A capacidade operacional deve ser uma **barra de progresso visível na comanda**, no catálogo e na revisão, sem se tornar mais um passo obrigatório. A composição é:

- Título **Limite de consumo**, perfil local da Tab e valores **R$ consumidos de R$ limite**.
- **Capacidade disponível** em números, sem obrigar o operador a inferi-la pela cor da barra.
- Segmento sólido = **exposição atual confirmada** (no protótipo, saldo fictício); segmento listrado = **novo pedido em rascunho**, que ainda não foi confirmado.
- Marca sutil em **80%** com mensagem textual de atenção; 100% ou projeção acima do limite mostram status explícito e ações contextuais.
- Ao ultrapassar, a barra não finge ter mais de 100%: o excedente aparece em texto preciso e o botão de enviar fica bloqueado. A barra permanece um resumo visual, não um atestado de autorização.
- Limite zero não produz porcentagem/progressbar enganosa; apresenta um estado de bloqueio por política.
- **Ver detalhes** é opcional e abre perfil/snapshot, limite, exposição, capacidade, pedido projetado, estado de garantia e opções para resolver. Não expor históricos administrativos em toda tela.

## Dados disponíveis na Spec 002

Perfis por Venue (defaults **apenas demo**):

| Perfil | Limite demo |
| --- | ---: |
| VISITOR / Visitante | R$ 30 |
| KNOWN / Conhecido | R$ 80 |
| REGULAR / Regular | R$ 200 |
| HOUSE / Da casa | R$ 500 |
| RESTRICTED / Restrito | R$ 0 |

Uma Tab usa o snapshot de política na abertura. Atualizações de relacionamento não mudam silenciosamente uma Tab em andamento. A projeção canônica já suporta `relationship_snapshot`, `effective_limit_cents`, `remaining_capacity_cents`, `exposure_cents`, `percentage_used`, `limit_warning`, `consumption_blocked`, `approval_requested`, `action_reasons` e `override_expires_at`.

**Somente o servidor decide se um pedido cabe no limite.** O valor do catálogo e do rascunho é prévia, sujeito a revalidação de preço, taxa e estado do ledger. Uma regra independente em REQUIRES_ACTION não é apagada por recebimento ou autorização de limite.

## Recuperação operacional

- Ao atingir/ultrapassar o limite, oferecer **receber parte da conta**, mantendo o draft e a Tab aberta, ou **solicitar aumento à gerência** sem desbloquear por antecipação.
- Override real é ação exclusiva de gerente com capability, PIN/reautenticação recente, motivo, novo limite total, expiração até 24h e idempotência, segundo Spec 002. O garçom não aprova seu próprio pedido.
- Recebimento parcial só reduz exposição depois de confirmação financeira canônica; não criar Payment no frontend. Reconnect e volta do aplicativo revalidam capacidade; cache não autoriza gasto.
- Restrito/limite zero exige fluxo de antecipação autorizado ou resolução gerencial apropriada; não supor que existe cobrança antecipada integrada.
- Se o envio foi tentado e a resposta é incerta, preservar a intenção original e conciliar; não reenviar outro pedido automaticamente.

## Garantia financeira não é limite

A ADR 0011 determina que aprovação operacional **não cria garantia financeira**. Não afirmar cartão pré-autorizado, caução depositada, PIX pago, crédito pré-pago ou saldo garantido sem eventos e registros canônicos.

Evoluções futuras separadas:
1. Pré-autorização/captura/liberação de cartão por PSP com prazo e reconciliação.
2. Depósito reembolsável com passivo em ledger segregado e fluxo de devolução.
3. Crédito pré-pago com origem de fundos, consumo e restituição auditados.

Até lá, o protótipo mostra **garantia não registrada na simulação**. Aumento de limite não vira cobrança, cartão reservado nem dinheiro confirmado.

## Exemplos fictícios da navegação

- Marina, Regular: R$ 56 usados de R$ 200 (28%); R$ 144 disponíveis.
- Rafael, Visitante: R$ 14 usados de R$ 30 (~47%); batata de R$ 28 acrescentada como faixa listrada — excede R$ 12. Receber R$ 13 na simulação deixa saldo de R$ 1 e permite o pedido de R$ 28.
- João, Visitante: R$ 28 de R$ 30 (~93%), estado de atenção.
- Carla, Conhecido: R$ 22 de R$ 80.
- Bruna, Da casa: R$ 93 de R$ 500.
- Balcão 1, Restrito: limite zero, novos pedidos bloqueados.

Tudo ocorre no HTML `prototype/ux-2-0/index.html` em memória, com saldo/pagamento/aprovação **fictícios**. Não há autorização de gerência real, garantias, efeitos no banco ou PSP. **12/12 verificações de navegação/estados passaram em JS/DOM simulado**, sem teste de layout no Chrome Android nem validação no app integrado.

## Gates de implementação

- Reusar a projeção canônica, e não inferir perfil pelo nome, sem criar outro policy engine no cliente.
- Componente visual único para Android e Web equivalente: 360/390/430dp, fonte ampliada, TalkBack/VoiceOver e status em texto (não só cor).
- Testes de 0%, 79%, 80%, 99%, 100%, limite 0, over-limit, pagamentos parciais, concorrência, expiração de override, outra causa REQUIRES_ACTION e resposta ambígua.
- Validação física de tarefa: ninguém precisa abrir `Ver detalhes` em toda comanda; barra deve orientar e não ocupar excessivamente a tela durante pico.
