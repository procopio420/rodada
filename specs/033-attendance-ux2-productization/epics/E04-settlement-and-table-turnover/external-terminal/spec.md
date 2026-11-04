# E04 — recebimento manual em cartão externo no Atendimento Web

Slice da etapa 3 do piloto, autorizada em 03/11/2026. R3: dinheiro/gateway/recovery.
Proprietárias: Spec006 PAY-008 (EXTERNAL_TERMINAL), Spec012 (dinheiro físico),
Spec014/026 (intenção imutável), E04/AC-12..16. Não altera contrato de backend.

## Comportamento

- Na área de recebimento do Atendimento, oferecer Dinheiro e Cartão externo.
  Pix e integrações de cartão continuam indisponíveis. Não inicia cobrança nem
  afirma comunicação/liquidação com provedor.
- Cartão externo exige marcar “Conferi a aprovação na maquininha externa” antes
  de registrar. Valor em centavos, parcial/integral, comanda e saldo canônicos.
  Marcação não é prova de provedor: é confirmação explícita do operador autorizado.
- Registrar método EXTERNAL_TERMINAL no endpoint de pagamentos existente,
  expected_version, originating_session_id e chave idempotente. Não enviar
  cash_point_id para terminal; sem exigir caixa aberto nem alterar CashMovement.
  Dinheiro mantém exigências atuais e comportamento de caixa.
- Persistir intenção antes do POST, congelando método/valor/Tab/identidade/chave.
  Não trocar de método ou adotar outra sessão/Tab enquanto houver ambiguidade.
- Preservar envelopes CASH schema1/2 byte a byte. Novo schema3 exclusivo de
  EXTERNAL_TERMINAL, com fase PAYMENT_PENDING/CONFIRMED e gateway original.
  Validar shape fechado por método, falhar seguro em envelope inválido.
- Após ACK/readback perdido/reload: mesma intenção, mesmo Payment; readback
  exige ID, Tab, método, valor e status confirmado. Guardar fase confirmada
  antes de fechar; falha de close não pode gerar outro pagamento.
- Parcial mantém OPEN; integral e fechamento seguem política canônica atual,
  respeitando draft. Fechar Tab não libera mesa. Autorização continua server-side.
- BFF permite somente CASH e EXTERNAL_TERMINAL com campos exatos por método.
  CARD/PIX/TAP_TO_PAY/CARD_ONLINE/OTHER, campos extras e formatos inválidos negados.
  Não alterar grants, Host/tenant, cookies, API financeira ou ledger.

## Fora de escopo

PSP, Tap/Pix, refund novo, leitura de cartão, armazenamento de comprovante/PII,
offline first-time acceptance, mudança de papéis, Android, deploy e produção.
Nome do componente/chave legados mantidos por compatibilidade; POS legado CASH
permanece com seu formulário atual. Exposição externa nesta slice é Atendimento.

[Plano](plan.md) · [Tarefas](tasks.md) · [Aceite](acceptance.md).
