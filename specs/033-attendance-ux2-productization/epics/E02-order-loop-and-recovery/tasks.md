# E02 — Tarefas executáveis

**Owner de contratos:** Spec 001/014/026; changes em Django somente quando gap confirmado. Coordenação com E01 sobre order-workspace.tsx.

- [ ] **E02-01 Baseline:** testar caminho existente Web useOrderIntent + OrderWorkspace e Android recovery cifrado com timeout/restart e perda após commit; mapear os gaps reais de JSON/estação.
- [ ] **E02-02 DTO readback:** usar OrderDetails/OrderItem históricos e fulfillment_station_snapshot; ampliar projeção apenas se faltam ID/status/estação; sem usar preço atual nem label inferido.
- [ ] **E02-03 Status durável Web:** cartão compacto na comanda com OrderRef, itens, status e estação, após readback; renderizar UNKNOWN com CTA seguro; manter “Adicionar itens” em destaque.
- [ ] **E02-04 Envio direto:** catálogo confirma em um toque com resumo opcional; conservar personalização e todas as validações de menu/availability, inclusive quantidade positiva e destino único.
- [ ] **E02-05 Repetir rodada:** editor rápido de quantidades/seleção, nova key após decisão legítima, sem dupla revisão e sem mesclar draft de outra intenção.
- [ ] **E02-06 Web reconciliação:** conferir persistência já existente e testar refresh/tab change/reauth/erros 4xx; freeze key+payload; não duplicar ledger.
- [ ] **E02-07 Android reconciliação:** reusar Keystore/intent store, alterar apenas UX e readback; reinício, troca de sessão e revogação não adotam intenção de outro usuário.
- [ ] **E02-08 Fila produção/status:** WebSocket/SSE só atualiza projeções; se desconectado fallback refetch, não inventar “pronto”.
- [ ] **E02-09 Tests:** PostgreSQL real + Web Playwright + Android JVM/instrumentado para lost ACK, duplicate submit, key replay, station split, stale rate, old Tab, offline.
- [ ] **E02-10 Gate:** R3 se mexer transação/ledger; logs de idempotência sem PII; AC-04..07 PASS em duas plataformas. Sem chamada ao PSP.

**PRs sugeridas:** E02-a projeções/status, E02-b envio/resumo/repetição, E02-c recuperação mobile e QA. Só mover dono da intenção se a implementação existente falhar no baseline.
