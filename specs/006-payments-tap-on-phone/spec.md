# Spec 006 — Payments + Tap on Phone

**Status:** Draft for implementation after Core POS financial foundation

## Objetivo

Fazer o pagamento acontecer como parte natural da vida da `Tab`, sem exigir que o garçom troque de dispositivo ou replique dados manualmente.

Premissa de UX:

> **O celular do garçom também pode ser o terminal de pagamento.**

No happy path, o staff abre a comanda, toca **Pagar**, escolhe o valor/método e, para cartão por aproximação, o cliente aproxima cartão, celular ou relógio no próprio aparelho compatível do staff.

Pagamento pertence à **Tab/comanda**, nunca à mesa.

## Usuários

- **Staff/Waiter**: recebe pagamentos e acompanha saldo da Tab.
- **Cashier**: recebe, reconcilia e trata exceções operacionais.
- **Manager/Owner**: pode estornar, resolver divergências e configurar providers/permissões.
- **Guest**: pode pagar a própria Tab pelo fluxo autorizado do customer web sem chamar staff.

## Invariantes

- `Tab` é a unidade financeira; `Table` e `TableOccupancy` são contexto físico.
- uma Tab pode receber zero, um ou vários pagamentos;
- pagamento parcial é comportamento nativo;
- saldo é derivado do ledger, não de um booleano mutável como `tab.paid`;
- fechar/pagar a última Tab não libera automaticamente a mesa;
- o domínio central não depende de Cielo, Stone, Adyen ou qualquer provider específico;
- Tap on Phone deve ser exposto por uma porta/adaptador de provider;
- **Paytime Tap on Phone é o primeiro adapter do MVP**, sem tornar Paytime parte do domínio central;
- a cobrança Tap on Phone do happy path acontece dentro do Rodada Atendimento, sem handoff obrigatório para aplicativo externo;
- o valor da cobrança nasce da Tab e não deve ser digitado novamente em outro dispositivo no happy path;
- toda tentativa de pagamento possui idempotência;
- estados ambíguos nunca podem ser tratados como falha segura para nova cobrança;
- webhooks são idempotentes e auditáveis;
- o frontend não é fonte de verdade para confirmação;
- pagamentos confirmados, estornos e ajustes nunca são apagados para "corrigir histórico";
- Guest e Staff devem enxergar a mesma posição financeira da Tab em realtime quando o canal estiver disponível;
- falha de Tap on Phone não pode impedir pagamento por método alternativo;
- operação financeira manual precisa registrar ator, horário e motivo/contexto quando aplicável.

## Modelo conceitual

### Payment

Valor recebido ou em processo de recebimento contra uma Tab.

Campos mínimos:

- `id`;
- `venue_id`;
- `tab_id`;
- `amount_cents`;
- `currency`;
- `method`;
- `provider` opcional;
- `provider_payment_id` opcional;
- `status`;
- `principal_amount_cents`;
- `tip_amount_cents` default 0;
- `created_by` opcional para guest/system;
- `created_at`;
- `authorized_at` opcional;
- `confirmed_at` opcional;
- `failed_at` opcional;
- `cancelled_at` opcional;
- metadata operacional não sensível.

Métodos iniciais:

```text
TAP_TO_PAY
PIX
CARD_ONLINE
CASH
EXTERNAL_TERMINAL
OTHER
```

Estados conceituais:

```text
CREATED
PENDING
PROCESSING
AUTHORIZED
CONFIRMATION_PENDING
CONFIRMED
FAILED
CANCELLED
PARTIALLY_REFUNDED
REFUNDED
```

`CONFIRMATION_PENDING` significa que o Rodada ainda não sabe se o provider concluiu a operação. Enquanto esse estado existir, uma nova cobrança equivalente não deve ser iniciada automaticamente.

### PaymentAttempt

Cada interação com um provider ou método manual relevante.

Campos mínimos:

- `id`;
- `payment_id`;
- `idempotency_key`;
- `provider`;
- `provider_attempt_id` opcional;
- `status`;
- `started_at`;
- `finished_at` opcional;
- erro/código normalizado opcional;
- metadata técnica segura.

Retries podem criar novas tentativas quando necessário, mas não podem duplicar uma cobrança já confirmada.

### ProviderEvent

Inbox idempotente de eventos externos.

Campos mínimos:

- `provider`;
- `provider_event_id`;
- `received_at`;
- `processed_at` opcional;
- `payload_hash`;
- `processing_status`;
- referência ao Payment/Attempt quando resolvida.

O payload bruto pode seguir política própria de retenção/segurança; o domínio precisa manter evidência suficiente para reconciliação e auditoria.

### Refund

Estorno total ou parcial de um Payment confirmado.

Campos mínimos:

- `payment_id`;
- `amount_cents`;
- `provider_refund_id` opcional;
- `status`;
- `created_by`;
- `created_at`;
- `confirmed_at` opcional;
- `reason` opcional.

Refund não altera nem apaga o Payment original.

## Ledger e saldo

A posição financeira da Tab é derivada dos lançamentos:

```text
charges
payments confirmed
refunds confirmed
adjustments
```

Exemplo:

```text
CHARGE      +64,00
CHARGE      +18,00
CHARGE      +22,00
PAYMENT     -50,00
PAYMENT     -30,00
PAYMENT     -24,00
------------------
BALANCE       0,00
```

Quando o saldo efetivo chega a zero, a Tab pode transicionar para encerramento financeiro conforme regra do Core POS. Isso **não** muda automaticamente `TableOccupancy`.

## PAY-001 — Fluxo de pagamento do Staff

Na Tab:

```text
COMANDA #27
R$ 186,40

[Adicionar pedido]
[Pagar]
```

Ao tocar **Pagar**:

```text
Quanto será pago?

○ Conta inteira
○ Minha parte
○ Escolher itens
○ Outro valor
```

Depois:

```text
Como deseja pagar?

Aproximação
Pix
Dinheiro
Maquininha externa
```

O valor escolhido é enviado diretamente ao método/provider. Staff não precisa redigitar valor, Tab ou mesa.

## PAY-002 — Tap on Phone

Quando device + provider suportarem Tap on Phone:

```text
Tab
→ Pagar
→ Aproximação
→ provider inicia cobrança
→ cliente aproxima cartão/celular/relógio
→ provider responde
→ backend confirma posição
→ Tab atualiza
```

Requisitos:

- integração deve ficar atrás de `PaymentProvider`/`TapToPayProvider` ou porta equivalente;
- o primeiro adapter implementado será `PaytimeTapProvider`;
- o SDK Paytime deve ser integrado diretamente ao Rodada Atendimento;
- não abrir aplicativo externo para concluir o happy path de aproximação;
- Staff app detecta capability do device;
- backend conhece capabilities do provider;
- device incompatível não oferece ação como disponível;
- UI nunca declara sucesso definitivo apenas por callback local quando confirmação server-side ainda estiver pendente;
- perda de conectividade após envio deve convergir para `CONFIRMATION_PENDING`, não para retry cego;
- provider específico não vaza para o modelo central de Tab/Charge/Payment.

Interface conceitual:

```ts
interface PaymentProvider {
  createPayment(input: CreatePaymentInput): Promise<PaymentResult>;
  getPayment(id: string): Promise<PaymentResult>;
  cancelPayment(id: string): Promise<PaymentResult>;
  refundPayment(id: string, amount?: Money): Promise<PaymentResult>;
}
```

## PAY-003 — Pagamento parcial

Pagamento parcial é permitido sem operação especial de "dividir conta".

Exemplo:

```text
Saldo: R$ 200
Cliente paga: R$ 80
Novo saldo: R$ 120
```

A Tab permanece aberta enquanto houver saldo/exposição ou enquanto sua regra de lifecycle exigir.

## PAY-004 — Divisão por itens/pessoa

A UX pode ajudar a calcular um valor por:

- itens selecionados;
- participante/identidade da Tab;
- valor arbitrário;
- saldo total.

Essa seleção é uma ajuda de composição e pode ser registrada para UX/auditoria, mas o ledger continua tendo valor monetário como verdade financeira.

## PAY-005 — Pix

Fluxo:

```text
Pagar
→ Pix
→ cobrança/QR
→ aguardando
→ webhook/provider confirmation
→ Payment CONFIRMED
→ Tab atualiza
```

No fluxo normal, staff não marca Pix como pago manualmente.

Exceções de reconciliação ficam disponíveis apenas a papéis autorizados e sempre geram auditoria.

## PAY-006 — Guest payment

Guest com acesso válido à Tab pode abrir **Minha comanda → Pagar**.

Métodos P0/P1 dependem de provider configurado, inicialmente podendo incluir Pix e cartão online.

Confirmação deve:

- atualizar a mesma Tab usada pelo staff;
- refletir em realtime no Staff App;
- impedir que pagamento pelo Guest crie uma segunda "conta";
- respeitar revogação/autorização da GuestSession.

## PAY-007 — Dinheiro

Dinheiro exige confirmação humana:

```text
Conta: R$ 82
Recebido: R$ 100
Troco: R$ 18

[Confirmar recebimento]
```

Registrar `confirmed_by_staff_id` e timestamp.

Dinheiro não deve fingir confirmação de provider.

## PAY-008 — Maquininha externa como fallback

O Rodada deve aceitar registro explícito de pagamento realizado fora da integração:

```text
Pagar
→ Maquininha externa
→ staff cobra fora do Rodada
→ Confirmar pagamento externo
```

Esse caminho é fallback, não happy path.

UI e auditoria devem diferenciar `EXTERNAL_TERMINAL` de Tap on Phone integrado.

## PAY-009 — Falhas e estado ambíguo

Falha segura:

```text
Pagamento não concluído.
Nenhum valor foi confirmado.
[Tentar novamente] [Outro método]
```

Estado ambíguo:

```text
Estamos confirmando este pagamento.
Não cobre novamente ainda.
```

`CONFIRMATION_PENDING` deve acionar consulta/reconciliação com provider antes de liberar retry equivalente.

## PAY-010 — Idempotência

Toda tentativa integrada possui `idempotency_key`.

Obrigatório proteger contra:

- double tap;
- retry do frontend;
- timeout;
- retry do backend;
- webhook duplicado;
- reprocessamento de fila.

Mesma intenção + mesma chave não pode gerar duas cobranças.

## PAY-011 — Webhooks e reconciliação

Eventos externos são processados por inbox idempotente.

Eventos conceituais:

```text
payment.authorized
payment.confirmed
payment.failed
payment.cancelled
payment.refunded
```

Nomes concretos do provider são adaptados para eventos internos.

Devem existir rotinas de reconciliação para Payments presos em `PROCESSING` ou `CONFIRMATION_PENDING`.

## PAY-012 — Refund

Manager/Owner ou papel explicitamente autorizado pode estornar total ou parcialmente.

Regras:

- preservar Payment original;
- criar Refund/lançamento reverso;
- atualizar saldo/exposição;
- registrar ator, valor e motivo opcional;
- refletir mudança em realtime.

## PAY-013 — Gorjeta

Gorjeta é separada do consumo e não é Product/OrderItem.

Modelo:

```text
principal_amount
tip_amount
total_amount
```

A política de gorjeta pode ser configurável por Venue. UI avançada pode entrar após o P0, mas o modelo não deve impedir sua adoção.

## PAY-014 — Realtime

Mudanças financeiras relevantes propagam para:

- Staff;
- Guest da mesma Tab;
- Cashier;
- Owner/Manager quando estiverem visualizando a operação.

Exemplo:

```text
João pagou R$ 88 via Pix ✓
```

Nenhum refresh manual deve ser necessário quando realtime estiver conectado.

## PAY-015 — Permissões e auditoria

Staff padrão pode:

- iniciar Tap on Phone;
- registrar dinheiro;
- registrar terminal externo;
- iniciar Pix.

Manager/Owner ou papéis configurados podem:

- cancelar quando tecnicamente permitido;
- estornar;
- resolver divergências;
- executar override/reconciliação manual.

Eventos financeiros relevantes registram:

- actor;
- device/session quando aplicável;
- venue;
- tab/payment;
- timestamp;
- estado anterior/novo;
- motivo quando aplicável.

## PAY-016 — Device/provider capabilities

Backend expõe capabilities normalizadas, por exemplo:

```ts
type ProviderCapabilities = {
  tapToPay: boolean;
  pix: boolean;
  cardOnline: boolean;
  partialRefund: boolean;
  tips: boolean;
};
```

Staff app também avalia capability do device:

- NFC;
- plataforma/versão suportada;
- provider provisionado;
- conectividade;
- autorização/provisionamento do aparelho **pelo provider de pagamento**, quando requerido.

O registro automático do dispositivo em Access (Spec 008) e seu estado `UNTRUSTED | TRUSTED | REVOKED` **não são** o provisionamento/homologação do PSP. Um garçom com membership ativa pode usar o Rodada Atendimento no celular pessoal, mesmo `UNTRUSTED`, sem aprovação manual do gerente para operar pedidos e comandas.

Apenas o fluxo Tap on Phone exige compatibilidade e eventuais requisitos adicionais do provider. Se NFC/SDK/provisionamento não estiver disponível, o botão de aproximação fica indisponível, com fallback explícito para outros meios autorizados; login, pedidos e consultas continuam funcionando.

A UI deriva disponibilidade dessas capabilities, não de hardcode de marca.

## PAY-017 — Métricas

Registrar pelo menos:

- tempo de "Pagar" até confirmação;
- approval/failure rate;
- método;
- provider;
- pagamentos por Tab;
- proporção de pagamentos parciais;
- Tap on Phone vs terminal externo;
- Guest vs Staff initiated;
- tempo em `CONFIRMATION_PENDING`;
- refund rate;
- gorjeta média quando habilitada.

Métrica norte operacional:

> **Tempo entre o cliente decidir pagar e o pagamento estar confirmado.**

## Rodada Atendimento

A superfície de atendimento é um **aplicativo Android nativo em Kotlin + Jetpack Compose**.

Motivos principais:

- Tap on Phone é capacidade central, não integração periférica;
- acesso direto e previsível a NFC, lifecycle Android e SDKs de pagamento;
- menos dependência de bridge/webview para operações financeiras;
- espaço para futuras integrações nativas de câmera, impressão, Bluetooth e dispositivos operacionais;
- UX touch-first otimizada para o garçom em operação de pico.

No MVP:

```text
Rodada Atendimento (Android)
        |
        v
TapToPayProvider
        |
        v
PaytimeTapProvider
        |
        v
Paytime Tap on Phone SDK
        |
        v
NFC do próprio aparelho
```

O usuário permanece no Rodada durante a cobrança. A tela pode usar componentes obrigatórios do SDK quando exigido por certificação/segurança, mas não deve exigir troca para outro aplicativo.

As demais superfícies não são obrigadas a usar Android nativo:

- Cozinha: Web/PWA;
- Bar: Web/PWA;
- Cliente: Web/PWA via QR, sem instalação obrigatória;
- Gerência: Web responsiva.

Todas usam o mesmo backend e o mesmo modelo de domínio. Compartilhamos contratos e design tokens; não forçamos compartilhamento de componentes de UI entre Compose e React.

## Segurança

- nunca persistir PAN/CVV no Rodada;
- dados sensíveis de cartão permanecem no SDK/provider apropriado;
- logs não podem conter credenciais ou dados de cartão;
- validar assinatura/autenticidade dos webhooks conforme provider;
- usar amount/currency do backend como fonte de verdade;
- operações administrativas sensíveis exigem autorização server-side;
- referências externas devem ser suficientes para reconciliação sem copiar payload sensível desnecessário.

## Fora de escopo desta spec

- fiscal/NFC-e/SAT;
- settlement bancário avançado;
- conciliação contábil completa;
- chargeback/dispute workflow completo;
- loyalty;
- carteira financeira Rodada;
- split marketplace entre múltiplos recebedores;
- roteamento inteligente por MDR/taxa;
- adquirência própria.

Esses temas exigem specs próprias quando virarem prioridade.

## Live integration slice (2026-10-08)

Paytime Pix uses authenticated REST transaction creation with a persisted Payment UUID
as `reference_id`. No provider idempotency guarantee is assumed: a failed/ambiguous
create is reconciled and never submitted again. Config is scoped by Venue, held in
server settings/secrets, and disabled unless complete. Webhooks require configured
HTTP Basic credentials and an authenticated provider lookup; incoming callback
status/amount alone never confirms money. Amount, transaction ID, method and
establishment must match before applying a provider fact. QR/EMV is retained for
recovery after restart. Provider cancellation/refunds are unavailable until their
contracts are integrated; manual refunds must not pretend to refund provider money.

Tap SDK activation remains blocked by the private Maven artifact, license,
application registration and merchant/device provisioning. The native port must
support lifecycle and capability checks and treat local completion as evidence for
backend reconciliation, never as confirmed receipt. Unknown expiration or missing
provider reference retains confirmation pending; local clocks cannot authorize retry.
