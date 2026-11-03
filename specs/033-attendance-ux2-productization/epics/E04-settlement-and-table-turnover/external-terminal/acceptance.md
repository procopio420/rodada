# Aceite — terminal externo Web

- [x] A1: confirmação externa explícita antes de POST; EXTERNAL_TERMINAL parcial
  e integral reais em PostgreSQL, sem caixa aberto/CashMovement, valor inteiro.
- [x] A2: parcial preserva saldo/Tab OPEN; integral/readback fecha conforme
  contrato, mesa não liberada; misto CASH/terminal contabilizado por método.
- [x] A3: ACK perdido/reload/double tap preservam payload/chave/método e um Payment;
  fase confirmada/readback falho não reposta após identificação canônica.
- [x] A4: contexto original revalidado; sessão revogada/trocada, capability ausente,
  cross-Venue, envelope/valor/método/campos inválidos não geram pagamento.
- [x] A5: CASH schema1/2 legados mantêm recuperação e efeito único no caixa;
  métodos PSP/PIX/CARD/OTHER não habilitados no Atendimento.
- [ ] A6: 360/390/430, teclado/foco, confirmação legível, pending e erro acessíveis;
  visual completo, types/build e testes pertinentes passam sem afrouxar baseline.
- [ ] A7: revisão independente R3 vinculada ao candidato; gates externos e CI
  ausentes explícitos. Implementação local não significa aceite de produção.

Evidência local de A1–A5: [relatório da slice](../../../../../docs/releases/pilot-stage3-external-terminal-2026-11-03.md),
10 casos novos em PostgreSQL, 15 regressões CASH e 39 testes API. Código em
afae48a1; teste final em 58dda307. Marcações limitadas ao recorte Web local;
A6/A7, aceite global Spec033 e produção continuam pendentes.
