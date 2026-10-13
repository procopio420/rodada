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

## Pilot refund durability — 2026-10-12

- Refund request persistence failure rolls back reservation and sends no POST.
- Matching pending-refund replay succeeds during provider outage without I/O; conflicting replay remains domain 409.

## Recorte POS Web CASH — Spec026 T03a

- [x] Duplo envio/perda após commit/reload convergem ao mesmo Payment e movimento.
- [x] Replay divergente de caixa/tender não altera ledger, audit ou snapshots.
- [x] Sessão distinta/revogada/storage falho preservam pendência sem enviar/adotar.
- [x] Readback confirma Payment antes de liberar; rejeição inicial permite revisão.

Evidência local: Spec026/revalidation.md, seção T03a. Não cobre estorno,
fechar aba ou resolução gerencial entre sessões; gates anteriores mantidos.

## T03b — critérios do recorte manual

Evidências em Spec026/revalidation.md; gates externos permanecem abertos.

- [x] Mesmo Refund após duplo toque, resposta perdida, reload e readback falho.
- [x] Payload congelado; PIN recente, sessão divergente/revogada e storage falho
  não descartam nem adotam intenção ambígua. Rejeição inicial segura permite edição.
- [x] Replay divergente rejeitado; saldo/refundable, Payment/snapshots, ledger e
  auditoria preservados; concorrência produz um único efeito em PostgreSQL.
- [x] Jornada real Web/API e mobile360/390/430; visual completo, build/tipos e lint
  registrados sem declarar provider, piloto, aparelho ou deploy homologados.

### T07d — entrada financeira Android
- [x] Decimal e NumberPassword no recorte; máscara/review preservados.
- [x] Parser exato rejeita sinais/texto/fração excessiva/overflow; confirmações inválidas bloqueadas.
- [x] Pagamento/limite/estorno testados em emulador e regressões PostgreSQL PASS.
Evidência Spec 026 revalidation.md: 61 unitários, sete cenários em seis configurações, 48 PostgreSQL, build/lint sem erros. IME físico e seleção automática não homologados.
