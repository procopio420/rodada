# Acceptance — Spec 006

- [x] Payment pertence a Tab e nunca depende de Table.
- [x] Uma Tab aceita múltiplos Payments.
- [x] Pagamento parcial reduz saldo sem exigir "dividir conta".
- [x] Saldo é derivado do ledger e não de `tab.paid`.
- [x] Pagar a última Tab não libera automaticamente TableOccupancy.
- [x] Staff consegue iniciar **Pagar** diretamente da Tab.
- [ ] No happy path integrado, valor não é digitado novamente em outra maquininha.
- [x] Rodada Atendimento executa o fluxo operacional em app Android nativo Kotlin + Jetpack Compose.
- [ ] Staff com membership ativa consegue operar pedidos em celular BYOD UNTRUSTED sem aprovação administrativa do aparelho.
- [ ] Celular sem NFC ou não provisionado pelo PSP continua com comandas e pedidos, além dos fallbacks de pagamento autorizados.
- [ ] Habilitação/homologação de Tap on Phone pelo PSP é verificada separadamente de login e DeviceRegistration do Rodada.
- [ ] Device compatível oferece Tap on Phone sem acoplar o domínio a uma marca.
- [ ] Paytime é o primeiro adapter real de Tap on Phone do MVP.
- [ ] Cobrança Tap on Phone acontece dentro do Rodada Atendimento, sem abrir aplicativo externo no happy path.
- [ ] Device/provider incompatível não oferece Tap on Phone como disponível.
- [x] Double tap/retry com a mesma intenção não cria cobrança duplicada.
- [ ] Timeout após envio entra em estado reconciliável e não libera retry cego.
- [ ] `CONFIRMATION_PENDING` impede nova cobrança equivalente até resolução.
- [x] Frontend sozinho nunca é fonte de verdade de confirmação.
- [ ] Webhook duplicado é idempotente.
- [ ] Evento externo é rastreável por provider_event_id/payload_hash.
- [ ] Pix confirmado pelo provider atualiza automaticamente a Tab.
- [ ] Staff não precisa marcar Pix como pago no fluxo normal.
- [ ] Guest autorizado pode pagar a mesma Tab, sem criar conta paralela.
- [ ] Pagamento Guest aparece no Staff em realtime quando conectado.
- [x] Dinheiro registra quem confirmou o recebimento.
- [x] Terminal externo existe como fallback explícito e auditável.
- [x] Payment confirmado nunca é apagado para representar estorno.
- [x] Estorno total/parcial cria Refund/efeito reverso rastreável.
- [x] Apenas papéis autorizados executam estorno/reconciliação manual.
- [ ] Payment Provider é abstraído por porta/adaptador.
- [ ] Capabilities de provider/device guiam a UI sem hardcode de marca.
- [ ] PAN/CVV nunca são persistidos pelo Rodada.
- [ ] Logs não expõem credenciais nem dados sensíveis de cartão.
- [ ] Métrica de tempo entre intenção de pagar e confirmação é registrada.
- [x] Fluxo P0 continua funcional quando Tap on Phone estiver indisponível, usando método alternativo.

## Provider readiness — 2026-10-09

- [x] Callback without its initiating browser cookie cannot exchange a code.
- [x] Revoked staff/session or denied OAuth cannot create a connection.
- [x] Lookup without artifacts retains the original Pix display data.
- [x] One unavailable merchant does not prevent other scheduled lookups.
- [x] TEST_DOUBLE/SIMULATED evidence is distinct from SANDBOX_CONFIRMED/LIVE_CONFIRMED.

- [x] Unsigned SumUp checkout notifications only request authenticated lookup; duplicate/reordered hints cannot settle money.
- [x] One provider merchant transaction has one canonical financial owner; a second settlement remains CONFIRMATION_PENDING (PostgreSQL race + migration checks).

These checks prove TEST_DOUBLE and SIMULATED boundaries only. Private SDK, actual sandbox/live captures and merchant approval remain unchecked external gates.
