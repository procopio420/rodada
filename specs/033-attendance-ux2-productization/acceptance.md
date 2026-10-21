# Acceptance — Spec 033: Atendimento 2.0 integrado

**Aceite global PENDING.** Inventário atual: [E06 por evidências](e06-current-evidence.md). Prototipagem HTML e as 27 verificações sintéticas da PR #212 não provam API/Android. Registrar para cada AC: PR, commit SHA, ambiente, comandos, screenshots/logs, reviewer e status PASS/FAIL/BLOCKED.

## E01: identidade e contexto
- [ ] AC-01 Staff toca chamada QR com Tab/Occupancy válida e chega à comanda exata na Web e no Android; outra comanda na mesma mesa nunca é escolhida por label.
- [ ] AC-02 Mesa→Tab→pedido/conta e Voltar preservam destino, drafts A→B→A, posição/foco e chamadas pendentes; balcão e multi-Tab funcionam.
- [ ] AC-03 Sessão revogada, Venue trocado, ocupação encerrada ou geração antiga não abre a Tab; há fallback seguro sem inventar ID.

## E02: pedido
- [ ] AC-04 Envio de pedido do catálogo em uma ação, resumo opcional; resultado exibe OrderId real, lines, estação e status correto após readback (não declarar READY sem fonte).
- [ ] AC-05 ACK perdido depois de commit e restart Web/Android recupera mesma chave+payload, nunca duplica Order/Charge nem contamina Tab diferente.
- [ ] AC-06 Repetir rodada ajusta quantidades, revalida preço/modificadores/disponibilidade e cria novo Order com nova chave somente se submissão legítima.
- [ ] AC-07 Limite ENFORCE, indisponibilidade, conflito de versão e erro definitivo preservam intenção até resolução correta e não mostram sucesso falso.

## E03: Dispatch e trabalho
- [ ] AC-08 Agora separa SERVICE/BILL e READY, cada fila com contadores e freshness independente, 50 tarefas sem extravasamento mobile.
- [ ] AC-09 Service QR navega para Tab, Bill QR para conta; quando não há identidade válida, escolha explícita / erro seguro; navegar não assume nem conclui tarefa.
- [ ] AC-10 READY abre o item/destino canônico, mantém provenance e permite ação autorizada sem obrigar confirmação apenas para métricas.
- [ ] AC-11 Task em posse de outro staff, mesa movida, sessão antiga, concorrência e timeout não permitem mutation indevida nem fazem tarefa sumir por navegar.

## E04: conta e mesa
- [ ] AC-12 Saldo e histórico de recebimentos são canônicos; parciais não encerram automaticamente a Tab, rascunho não é somado à conta.
- [ ] AC-13 Recebimento integral + fechamento rápido só acontece após evidência financeira e close autorizado; ACK incerto não gera segundo pagamento/close.
- [ ] AC-14 Mesa com duas Tabs não libera após a primeira ser encerrada; última Tab CLOSED não dispara release sem saída real confirmada.
- [ ] AC-15 OCCUPIED→DIRTY→CLEANING→AVAILABLE e revogação de GuestSession/epoch seguem versão e domínio, sem reutilizar ocupação antiga.
- [ ] AC-16 Caixa/turno, estorno, provider, permissão gerencial e ajustes financeiros não são contornados por UX mais curta.

## E05: limite e perfil
- [ ] AC-17 Barra de 0/79/80/99/100/>100% é compacta, acessível e usa modo efetivo do Venue; rascunho aparece visualmente distinto de exposição confirmada.
- [ ] AC-18 WARN_ONLY permite pedido excedente apenas quando o servidor da Spec 031 permite; ENFORCE bloqueia no backend e informa recuperação sem driblar outras regras.
- [ ] AC-19 Sem token de garantia/PSP/caução real, a UI não afirma garantia; perfil/snapshot e atualização gerencial são auditáveis fora do cliente staff.

## E06: homologação/release
- [ ] AC-20 Jornada integrada com PostgreSQL e canal staff Web+Android, Guest QR, produção Bar/Cozinha, Caixa, Table; resultados verificáveis por Order/Task/Payment IDs.
- [ ] AC-21 Falha de rede e de readback, repetição idempotente, troca de operador, revogação e app morto passam em Web/Android real.
- [ ] AC-22 Screenshots 360/390/430/desktop, fonte ampliada, TalkBack/foco/teclado e teste de toque mostram CTA sem scroll desnecessário e sem overlap.
- [ ] AC-23 Comparativo antes/depois mede passos, tempo intenção→produção, erro/duplicação e mesa disponível; métricas não geram trabalho extra ao garçom.
- [ ] AC-24 CI, revisão independente R3, feature rollout por Venue/role e rollback comprovado; nenhum P0/P1 aberto; aceite humano do operador/piloto antes do GO.

**GO global exige AC-01..24 PASS e dependências críticas aceitas.** É permitido liberar cortes menores sem declararem “Atendimento 2.0 concluído”, desde que gates próprios de cada slice estejam satisfeitos.
