# Aceite — terminal externo Web

- [ ] A1: confirmação externa explícita antes de POST; EXTERNAL_TERMINAL parcial
  e integral reais em PostgreSQL, sem caixa aberto/CashMovement, valor inteiro.
- [ ] A2: parcial preserva saldo/Tab OPEN; integral/readback fecha conforme
  contrato, mesa não liberada; misto CASH/terminal contabilizado por método.
- [ ] A3: ACK perdido/reload/double tap preservam payload/chave/método e um Payment;
  fase confirmada/readback falho não reposta após identificação canônica.
- [ ] A4: contexto original revalidado; sessão revogada/trocada, capability ausente,
  cross-Venue, envelope/valor/método/campos inválidos não geram pagamento.
- [ ] A5: CASH schema1/2 legados mantêm recuperação e efeito único no caixa;
  métodos PSP/PIX/CARD/OTHER não habilitados no Atendimento.
- [ ] A6: 360/390/430, teclado/foco, confirmação legível, pending e erro acessíveis;
  visual completo, types/build e testes pertinentes passam sem afrouxar baseline.
- [ ] A7: revisão independente R3 vinculada ao candidato; gates externos e CI
  ausentes explícitos. Implementação local não significa aceite de produção.
