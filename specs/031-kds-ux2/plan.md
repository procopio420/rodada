# Spec 031 — Plano de implementação KDS UX 2.0

**Estado:** planejado/documentado; **não executado**. A implementação exige revisão de contratos antes de mutações.  
**Protótipo:** [kds-bar-cozinha.html](../../prototype/ux2/kds-bar-cozinha.html). **Fonte:** [spec.md](spec.md).

## 0. Preparação

- Atualizar a branch de trabalho a partir de `main` sem sobrescrever worktrees/PRs concorrentes. Ler `AGENTS.md` da raiz e de `apps/web`/`apps/api`, esta Spec integralmente, Spec 003/014/017/026, ADR 0018, skills `rodada-nextjs-web`, `rodada-ui-design`, `rodada-ux-handoff`, `rodada-accessibility-review` e, quando houver mutação, `rodada-pos-safety`.
- Inventariar o comportamento efetivo da `apps/web/components/production-board.tsx`, `apps/web/lib/client/production-*`, contrato REST, SSE, batch, Corrections, Dispatch e auditoria no SHA de execução; registrar discrepância entre spec, HTML e código como DRIFT.
- Montar fixture reproduzível com Bar, Cozinha, ficha FG84, mesma mesa com duas Tabs, modificadores, alergia, 30 pedidos, quantidades parciais e falha de rede. Não usar Venue/contas reais para teste.
- Congelar cópia “antes” (mesmo SHA, cenário, fonte, navegador e viewport). Não mexer em baseline visual apenas para passar CI.

## Sequência de slices (PRs separados por contrato)

### S1 — Fila ticket-first e navegação, só apresentação (R2)
- Refatorar `ProductionBoard` em cabeçalho compacto, `Pedidos`, `Passe`, `Resumo por produto` e `Ajustes`.
- Tickets por `order_id` mantendo ações por `OrderItem.id`/versão e customizações explícitas; fila estável, destaque NEW/atraso/urgência; remove QuickCatalog/admin do primeiro viewport quando indevido, sem remover recurso permitido.
- CSS adaptativo real, 360/390/430 e 768/850/1024 e desktop; bottom nav acessível e 56 px no CTA.
- Reusar os comandos e componentes existentes sem habilitar `READY` direto ou parcial não suportado.
- **Gate:** screenshots/Playwright, teclado/foco, URL/estação/venue corretos, nenhuma regressão de permissão/fila.

### S2 — Atenção, acessibilidade e mudança observável (R2/R3 conforme evento)
- Aviso persistente de ticket novo e alteração mesmo fora da fila; ir ao ticket exato, sem reorder por SSE. Som opt-in, sem repetição de áudio por replay.
- Garantir foco, scroll, alteração anunciada em leitor de tela, estado busy/disabled, contraste e configurações por Venue/dispositivo conforme autorização.
- Diferenciar notificação, revisão e resolução canônica; não converter um botão “li” em aprovação/cancelamento.
- **Gate:** evento duplicado/out-of-order, 30 tickets, ACK incerto, 200% font, screen reader e Playwright.

### S3 — Passe/Dispatch e expedição opcional (R2/R3)
- Projeções canônicas READY / pickup / delivered; prontos recentes e área “sem retirada registrada”, filtro por `order_id` a partir da expedição e acesso ao Passe geral.
- Separar seleção/visibilidade de “entregue”. Implementar modo simples sem confirmação de retirada; expedição opcional de Venue com dependências Bar + Cozinha.
- Não permitir que uma expedição mista altere estados financeiros nem presuma conclusão cruzada; preservar parcialidades.
- **Gate:** mistura de estações, múltiplas Tabs por mesa, passe antigo, retorno de filtro, dispatch sem tap obrigatório.

### S4 — Exceções e segurança (R3)
- Motivos, quantidades e solicitação/aprovação/recusa de correções consumindo Spec 017; estágio/pagamento/permissão verificados no servidor.
- Alergia: detalhes e reconhecimento; opção de incapacidade de preparo que suspende a linha e gera evento auditável/autorização de retomada **somente após contrato aprovado**.
- Nenhuma mutação em snapshot imutável; remake cria novo OrderItem e lineage.
- **Gate:** falha de autorização, concorrência, revisão de risco e testes negativos; sem liberação artificial de item inseguro.

### S5 — Comandos rápidos e quantidade parcial (R3; dependente de decisão de domínio)
- Decidir e especificar se `Marcar pronto` direto gera transição legal ou comando combinado atômico; não encadear duas mutações clientes sem journal/readback.
- Definir modelo autoritativo para unidade parcial, projeção do Passe/Dispatch, arredondamentos/ausência de efeito financeiro, audit trail e replay concorrente.
- Só então expor `1 pronto`/`N prontos` e lote multitem seguro; batch rejeita seleção divergente integralmente.
- **Gate:** payload fingerprint, esperado/atual, duplo clique, duas sessões, replay, entrega parcial e zero duplicações.

### S6 — Configuração, disponibilidade e impressão (R2/R3)
- Limiar de alerta, som e densidade persistidos com scope adequado; preferências locais só quando não alterarem operação do Venue.
- Disponibilidade versionada única por produto/venue; pedido confirmado não desaparece.
- Impressão via agente/fallback real (Specs 015/028) com status, idempotência de reimpressão e falha, sem bloquear preparo indevidamente.
- **Gate:** dois Venues, permissão, toggle concorrente e impressão falhada.

### S7 — Homologação operacional e rollout (R3)
- Testes API/Web integrados com PostgreSQL, SSE, downtime/reconnect, journal e suite visual do SHA; teste de turno completo, inclusive cenários da issue #106 onde aplicáveis.
- Operadores reais: ao menos bartender e cozinheiro (e expedidor se habilitado) executam tarefas com observação, sem entrevista inventada. Registrar erros de interpretação, ações, tempo medido quando houver instrumento e sugestões.
- Piloto opt-in por Venue, rollback de UI sem migrar/corromper dados, monitoração de eventos/erros e runbook.
- **Gate:** checklist de `acceptance.md` com evidências por ambiente/SHA e aprovação humana. Sem “GO” apenas porque o HTML funciona.

## Arquitetura sugerida (não implementação aprovada)

`ProductionBoard` continua coordenador de leitura/recovery. Separar subcomponentes puramente apresentacionais (`StationHeader`, `TicketGrid`, `Ticket`, `ReadyPass`, `AllDaySummary`, `ExpeditionView`, `StationSettings`) e hooks/adapters reutilizando projection cache, intents, SSE, snapshot/refetch e autorizadores existentes. Evitar backend novo para CSS, mas **não** forçar abstração front-end para representar partial ready/blocks que não existem no domínio.

### Falhas e rollback

- Sem API: mostrar snapshot carimbado/desatualizado, bloquear ações inseguras conforme Spec 014, jamais enviar novas intenções com nova chave para sanar ACK ambíguo.
- Sem SSE com API saudável: polling/refetch e guardas de frescor, indicador legível.
- Conflito versão/lote: rejeitar com motivo e opção de recarregar, sem aplicar metade ocultamente.
- Falha de impressão: notificar e seguir com fallback seguro; não anunciar “impresso” antes do ACK.
- Rollback: flag de experiência por Venue/client e manutenção do backend canônico; evitar mudança de schema irreversível no mesmo PR de UI.

## Evidência obrigatória em cada PR

Registrar SHA base e head, spec/critério, arquivos, testes/comandos executados, fixture, viewport, screenshots antes/depois equivalentes, traces de falhas, riscos/limites, reviewer independente proporcional à mudança e decisão explícita sobre rollout. **Não inferir** pass de captura do protótipo para build Web em execução.
