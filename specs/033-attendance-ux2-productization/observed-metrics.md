# E06-07 — projeção de tempos observados (slice 1)

Antes do código: extrair fatos já persistidos, sem criar tracking pessoal, taps,
novo ledger, inferência ou timestamps de intenção fictícios.

GET `/management/attendance-metrics/?start=YYYY-MM-DD&end=YYYY-MM-DD` exige
MANAGEMENT_REPORTS_READ e usa exclusivamente o Venue autenticado. Período máximo
31 dias de negócio inclusivos, com timezone/cutoff canônicos. Métricas agregadas,
sem IDs/labels/notas/atores, nenhuma mutation e nenhuma persistência nova.

Coortes: OrderItem por Order.confirmed_at (CONFIRMED); tasks por created_at.
Intervalos observados: confirmação→aceite de produção e confirmação→READY por
estação snapshot BAR/KITCHEN; criação→claim/conclusão de SERVICE/BILL; READY→
conclusão de DELIVERY somente completion_source=MANUAL; BILL→Tab.closed_at
somente quando Tab pertence ao mesmo Venue e há requested_tab. Timestamps
faltantes e negativos são cobertura missing/invalid, nunca zero artificial.
Conclusão sem provenance manual é unverified, nunca entrega confirmada.
Aceite de produção é estado de domínio ACCEPTED, não recebimento visual da tela.

Cada agregado informa eligible/observed/missing/invalid/unverified e média em
segundos ou null; média apenas das observações válidas, sem ranking por staff.
Timestamps finais podem ser posteriores ao período da coorte. Não derivar
Tab CLOSED→release de mesa multi-Tab por relação corrente; relatório de giro
existente continua canônico para limpeza/disponibilidade.

Fontes não instrumentadas são explícitas: passos, início da intenção, tentativas,
erros de cliente e versão da apresentação. Este slice não fecha AC23, não exige baseline de UX anterior e não substitui instrumentação Web/Compose nem piloto.

Aceite da slice: permissões/anon/duas Venues, limites de período/cutoff, estação
snapshot, missing/invalid/provenance, leitura repetida sem mutation e SQL sem N+1.

## AC-23 — contrato de instrumentação de intenção (pendente de implementação)

- Coorte: intenção de confirmar pedido, iniciada na ação do operador; não inferir esse instante de `Order.confirmed_at`.
- Web e Android emitem o mesmo contrato versionado: `intent_started`, `confirm_attempted`, `confirm_failed`, `confirm_recovered` e `confirm_acknowledged`.
- Correlação por identificador opaco da intenção, estável durante recuperação e idempotência; não enviar nome, ID de funcionário, conteúdo do pedido ou payload de pagamento para telemetria.
- Contar passos essenciais apenas nos fluxos efetivamente instrumentados; nunca derivar passos a partir de pedidos confirmados.
- Duração intenção→confirmação somente quando os dois marcos são observados na mesma intenção; usar relógio monotônico para duração no cliente, com indicação de amostras ausentes após reinício.
- Backend valida schema, autenticação, venue do token, limites e deduplicação; persistência agregada por venue/período, sem trilha individual de operador; rejeitar valores arbitrários e cardinalidade ilimitada.
- Expor denominadores (eligible/observed/missing), tentativas, erros, recuperações e disponibilidade de mesas com definição verificável; separar observações canônicas das observações do cliente.
- Testes obrigatórios: Web, Android, API, tenant isolation, duplicatas/retry, desconexão/restart, dados ausentes e balcão-only.
- Não fechar AC-23 com este contrato: somente após implementação, testes e evidências no mesmo SHA.


## AC-23 — telemetria v2 (contrato implementado em slice, validação pendente)

A telemetria `POST /attendance/telemetry/` preserva clientes v1. Clientes v2 enviam
`event_id`, `version=2`, plataforma, evento, `origin_session` da sessão atual
e `intent_ref` SHA-256 da **chave aleatória de idempotência**. A API rejeita
sessões divergentes, hash malformado, outros campos, valores fora do intervalo,
duplicata conflitante e lotes acima de 8 KiB. O UUID de evento e hash opaco ficam
só em receipts temporários, nunca no relatório; não há staff/Tab/Order/Payload,
nem tracker individual. Receipts expirados são limpos por comando de retenção
de sete dias (a execução agendada deve ser configurada no rollout, não foi
declarada ativa). Um envio perdido pode deixar cobertura incompleta, mesmo
com Order financeiro confirmado; telemetria é best-effort.

`essential_steps` no `confirm_acknowledged` soma **ações efetivamente observadas**
em uma Tab no processo corrente: edições do carrinho e ação de envio. Ações
anteriores à recuperação/reinício e fluxo sem ação de carrinho observada não
recebem contagem inventada. Relatório mostra
`essential_steps_eligible/observed/missing`, total e média só das amostras
observadas; não é número de passos de navegação inteira.

`duration_ms` é relógio monotônico da tentativa de confirmação até readback
canônico; não é duração de uma jornada que atravessa reinício nem comprovante
de chegada à tela Bar/Cozinha. O agregado canônico separado mantém
`Order.confirmed_at→OrderItem.accepted_at/ready_at` por estação, sem
inferir recebimento visual. **A AC-23 integral não está fechada:** falta
medição comprovada intenção→recebimento real em produção, caminho completo
de passos e evidência em operação. Nenhuma comparação com UX antiga é exigida.


## AC-23 — primeiro recebimento visível no Bar/Cozinha (slice implementado)

Bar/Cozinha agora possui um observador passivo de `ProductionBoard`:
- O pedido só é elegível para observação após leitura **fresca** e autenticada
  de `GET /production/{BAR|KITCHEN}/`; restaurar cache offline não gera evento.
- Uma carta/ticket de Order só é reportada após renderização e interseção
  positiva com o viewport em aba visível. Sem clique extra do operador.
- O proxy `POST /api/production-screen-observation` preserva a sessão staff
  existente sem refresh/cookies. A API aceita somente um lote pequeno de
  Orders canônicos do próprio Venue e da estação, sem mudar Order/Task/ledger.
- O primeiro evento por `venue+order+station` recebe deduplicação durável;
  refresh, abas simultâneas e retry não duplicam contagens. Receipts por Order
  são temporários, limpos pelo mesmo comando de retenção de sete dias.
  Ordens antigas fora dessa janela não voltam a ser contadas após limpeza.
- O relatório `production_screen.BAR/KITCHEN` mostra **Orders elegíveis,
  observados e ausentes** agrupados pela data de confirmação do Order.
  `latency_observed/missing` e média são separados do total observado.

**Proveniência do tempo:** o marco inicial é o `received_at` no servidor do
evento autenticado `intent_started` (telemetria v2, vinculado por SHA-256 da
chave aleatória de idempotência). O marco final é `observed_at` do servidor
no primeiro relatório de ticket visível no viewport. Isso mede
**ingresso da intenção → recibo de observação da tela** usando relógio do
servidor, não clocks de dois dispositivos. Se o evento inicial chegou depois,
faltou, foi descartado, veio de fluxo Guest/legado ou saiu da retenção, a
duração é *missing*, nunca estimada.

É evidência de que um **cliente autenticado informou renderização visível**,
não prova de que o funcionário prestou atenção, de entrega de hardware ou de
preparo iniciado. A latência contém rede/filas de observação e não representa
o instante exato do toque no aparelho. A simulação e o teste real em
Chromium/PostgreSQL validam a instrumentação; a homologação com pessoa e
equipamento reais continua fora deste slice. Nenhuma flag de UX legada.
