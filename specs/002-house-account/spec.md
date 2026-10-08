# Spec 002 — Conta da Casa

**Status:** P0 implementation

## Objetivo

Adicionar identidade, relacionamento e política de exposição ao Core POS.

## Histórias

- buscar/criar Customer rapidamente;
- definir Relationship `VISITOR | KNOWN | REGULAR | HOUSE | RESTRICTED`;
- herdar operating limit ao abrir Tab;
- mostrar exposure e percentual utilizado;
- mover Tab para `REQUIRES_ACTION` ao atingir limite;
- receber parcial sem fechar Tab;
- permitir override temporário de limite por manager;
- manter histórico entre visitas;
- alterar Relationship sem retroagir tabs abertas.

## Política demo

| Relationship | Limite |
|---|---:|
| Visitor | R$ 30 |
| Known | R$ 80 |
| Regular | R$ 200 |
| House | R$ 500 |
| Restricted | R$ 0 |

## Fora de escopo

- score externo;
- reputação entre estabelecimentos;
- promoção automática de relationship;
- cobrança automática;
- pré-autorização.

## Contrato P0 de enforcement

- Políticas por Venue são persistidas, com defaults demo em centavos (3000,
  8000, 20000, 50000, 0). Tab anônima usa VISITOR. Na abertura, snapshot
  imutável de categoria, versão e limite; associação posterior não o reescreve.
- Exposição vem exclusivamente do ledger: Charges + Adjustments - Payments
  confirmados + Refunds confirmados. Capacidade = max(0, limite efetivo -
  exposição); percentual usa exposição não negativa e é null se limite zero.
- Confirmação bloqueia Tab em transação, resolve replay idempotente antes de
  validar política, calcula preço canônico e rejeita exposição projetada acima
  do limite antes de criar Order/OrderItem/Charge. Todos os canais usam isto.
- Ao atingir limite (inclusive RESTRICTED zero), REQUIRES_ACTION. Motivos de
  atenção independentes são preservados; pagamento/override não apaga outros.
- Override é limite total explícito, temporário, com expiração obrigatória
  (máximo 24h), motivo, ator e chave idempotente. A última aprovação substitui
  a anterior; expiração não revive aprovação anterior. Exige capability e
  reautenticação recente verificadas também no serviço.
- Staff pode solicitar aprovação; apenas manager autorizado pode conceder.
  Mudança de Relationship exige gestão autorizada. Reavaliar Tab aberta é
  comando separado, explícito e auditado; nunca modifica pedidos ou pagamentos.
- Aprovação operacional não constitui garantia financeira e não gera Payment.
  Garantia real depende de pré-autorização/captura de provider ou depósito
  reembolsável com ledger de passivo separado, fora do P0.
- Clientes revalidam via API ao recuperar conexão; cache não autoriza consumo.
- Migração aplica VISITOR às Tabs existentes sem inventar identidade; exposição
  histórica acima do limite não é alterada e exige resolução antes de consumo.

## API e superfícies

- `GET/POST /customers/`, `GET/PATCH /customers/{id}/`: busca local, cadastro,
  relacionamento e histórico de visitas. Staff lê; `customer.manage` escreve;
  alteração exige reautenticação recente.
- `GET/PUT /house-account/policies/`: cinco categorias; atualização exige
  `venue.configure` e reautenticação. Não altera snapshots já abertos.
- `POST /tabs/{id}/customer/`: associação autorizada sem reescrever snapshot.
- `POST /tabs/{id}/reassess-policy/`: motivo obrigatório, `tab.limit.override`
  e reautenticação; auditoria registra snapshot anterior e novo.
- `POST /tabs/{id}/approval-request/`: solicitação auditada e idempotente;
  não concede capacidade. Gerência vê a solicitação até aprovação/fechamento.
- `POST /tabs/{id}/limit-override/`: aprovação idempotente, `limit_cents` total,
  `reason`, `expires_at` e `idempotency_key`; permission e PIN recentes.
- `GET /tabs/{id}/house-history/`: histórico privilegiado de decisões da Tab.
- Projeções de Tab incluem exposição, limite base/efetivo, capacidade,
  percentual, warning (>=80%), bloqueio, motivos e expiração. Em limite zero,
  percentual é null; não há divisão por zero ou precisão inventada.
- Atendimento mantém abertura anônima em um toque, com busca opcional de cliente;
  Gerência reutiliza Panel/DataRow/Field/Notice/Button; Guest recebe feedback e
  não recebe controles gerenciais. Validação API é independente da UI.
- Revalidação bounded a cada 15s enquanto a superfície está ativa, também em
  reconnect/focus; Android revalida ao retomar e ao recuperar rede. Este slice
  usa o fallback HTTP existente, sem criar outro transporte de realtime.
