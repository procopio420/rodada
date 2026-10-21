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
erros de cliente e versão da apresentação. Este slice não fecha AC23, não mede
antes/depois e não substitui instrumentação Web/Compose nem piloto.

Aceite da slice: permissões/anon/duas Venues, limites de período/cutoff, estação
snapshot, missing/invalid/provenance, leitura repetida sem mutation e SQL sem N+1.
