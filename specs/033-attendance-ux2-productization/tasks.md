# Backlog mestre — Spec 033 por epic

**Execução parcial em andamento:** as caixas permanecem abertas até evidência suficiente por tarefa e plataforma. Status incremental em `parity.md`, `baseline.md` e nas notas de cada épico; código ou uma suíte estreita não concluem a tarefa. Detalhes e critérios em cada epic. IDs estáveis: E01-xx até E06-xx. Não abrir uma GitHub issue por task automaticamente; esta spec é o tracker mestre.

## E01 — Contexto e navegação

- [ ] E01-01 Inventariar superfícies e destino canônico Tab/Table/Occupancy no Web/Compose (reusar Spec 029/026).
- [ ] E01-02 Definir API de navegação/intent segura e typed, com autorização e versões.
- [ ] E01-03 Implementar Agora/Mesas/Tab/atalhos no Web sem desmontar workspace nem rascunho.
- [ ] E01-04 Port nativo Compose; deep-link e Back preservam foco, Tab e draft.
- [ ] E01-05 Regressões de mesa multi-Tab, balcão, sessão revogada e contextos stale.

## E02 — Pedidos, confirmação e recuperação

- [ ] E02-01 Mapear hooks/intenção atuais, contratos confirm_order, snapshot station e readback.
- [ ] E02-02 Confirmado/pedido/item/estação persistentes após readback, separados de estados de produção.
- [ ] E02-03 Enviar direto do catálogo, resumo opcional e repetir rodada em um envio.
- [ ] E02-04 Web/Android recuperar timeout, restart/reload e ACK perdido com MESMA intenção.
- [ ] E02-05 Manter drafts por Tab e tratar edição de pedido pendente, conflito, limite e availability.
- [ ] E02-06 Testes com perda após commit, replay, preço, concorrência e múltiplas estações.

## E03 — Agora e Dispatch

- [ ] E03-01 Projeção autorizada de SERVICE/BILL/DELIVERY com IDs de destino e gerações; sem inferir por label.
- [ ] E03-02 Filas separadas de Atendimentos e Entregas com estado/counters/freshness independentes.
- [ ] E03-03 Service e Bill QR abrem Tab/conta exatas ou fallback seguro com escolha de Tab.
- [ ] E03-04 READY abre tarefa de entrega exata e ações explícitas de exceção/complete.
- [ ] E03-05 Auditoria/claim/concurrency e recuperação de fila sem auto-mutation na navegação.
- [ ] E03-06 Rodada de testes por zona/mesa móvel, rede ruim e 50 tarefas; otimização por mapa fora.

## E04 — Conta, fechamento e giro

- [ ] E04-01 Auditoria saldo/Payment/CashShift/Tab.close/Table.release e permissões canônicas.
- [ ] E04-02 Expor conta legível, parciais e recibos sem rascunho misturado, Web + Compose.
- [ ] E04-03 Receber integral e fechar com clique reduzido **após** confirmação/readback canônico e revalidação, sem auto-pagamento.
- [ ] E04-04 Tab quitada fecha diretamente; contas independentes na mesma mesa.
- [ ] E04-05 Table release explícito quando grupo saiu; DIRTY/CLEANING/AVAILABLE, QR epoch e cleanup.
- [ ] E04-06 Testes de partial/overpay/refund pendente/timeout, vários clientes e sessão antiga.

## E05 — Limites e relacionamento

- [ ] E05-01 Reusar financial_position/Spec 002, sem novo motor de crédito ou garantias.
- [ ] E05-02 Barra compacta nas Tabs e projeção do rascunho com 80%, estado textual e limite zero.
- [ ] E05-03 Integrar modos efetivos/versão **somente após** implementação da Spec 031.
- [ ] E05-04 Validar WARN_ONLY vs ENFORCE, overrides, parciais, concorrência e erros de servidor.
- [ ] E05-05 Acessibilidade e confirmação de que a barra não ocupa a primeira dobra do CTA.

## E06 — QA, observabilidade e rollout

- [x] E06-01 Baseline real, status Specs 026/029/#106 e cobertura existente; mapear aceites.
- [ ] E06-02 Contratos e E2E integrados Web/Android/Guest/Bar/Cozinha/Caixa em PostgreSQL.
- [ ] E06-03 Capturas 360/390/430 + S24-class/desktop, fonte ampliada, teclado, TalkBack.
- [ ] E06-04 Ensaiar turno vazio/normal/pico com timeout, session swap e dispositivo reiniciado.
- [ ] E06-05 Instrumentar métricas de fricção e erro sem exigir taps artificiais.
- [ ] E06-06 Revisão independente R3, flags Venue/role, rollback, GO/NO-GO e homologação do bar.

A checklist de cada epic decompõe essas tarefas em subtarefas e oferece aceites objetivos. Não marcar concluídas sem teste no mesmo SHA e evidência revisável.

E06-01: [inventário por SHA](e06-current-evidence.md). E06-02..06 seguem abertos; esta marcação aceita somente o inventário.


## Integração verificada — 21/10/2026

[Estado e matriz AC-01..24 por SHA](completion-20261021.md). PRs281/284/286/288
mergeados; dependência031 implementada em backend/Web/Compose. CI288162PASS,
3SKIP; não equivale a aceite global. Instrumentação, flag UX/rollback, pacote
Android atual, paridade completa, aparelho e piloto continuam abertos.
