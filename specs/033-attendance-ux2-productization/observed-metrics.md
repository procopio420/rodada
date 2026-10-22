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
