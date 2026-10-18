# E03-04 / E03-06 — Entrega como página UX2

Contrato: Spec033 E03, AC-08..11 parcialmente exercitados; Spec003 Dispatch e PR212 `viewDelivery` (`ec26e26b`). Base `0f37fb03` / PR243. Não encerra o épico.

O que existia: duas filas, GET de tarefa autorizado e completion canônico idempotente pelo Task ID. Entrega abria ActionDialog. Não foi criado motor de pedidos, pagamentos, claim ou ledger.

Delta: página equivalente à hierarquia aprovada (Voltar, contexto, item/quantidade/estação, estado, retorno e rodapé); abrir e voltar continuam readonly. Revalida Task/OrderItem/Order, destino e ownership antes do comando; confirma DONE+DELIVERED por readback canônico. ACK perdido consulta a mesma tarefa; quando readback falha oferece verificação sem reenviar. Contexto financeiro CLOSED não bloqueia a tarefa e não exige abrir uma Tab financeira.

| Tela/estado | Protótipo | Web | Android | Diferenças / resultado |
| --- | --- | --- | --- | --- |
| READY, 2 Chopp Pilsen, Rafael #1049, Mesa08 | Capturas executáveis 360/390/430/1280 | Capturas mesmas dimensões e dados | Slice independente | Hierarquia reproduzida; textos fictícios substituídos por fatos canônicos |
| Abrir e voltar | Não conclui | Browser fixture + PostgreSQL comprovam OPEN/READY após retorno | Não validado aqui | Sem claim ou completion automática |
| Tab CLOSED com READY | Simulado | Quatro jornadas reais em PostgreSQL | Não validado aqui | Tab permanece CLOSED, saldo zero e pagamentos preservados após entrega |
| Completion ACK perdido | Simulado | Quatro jornadas reais: um POST, mesmo Task/Item DONE/DELIVERED/MANUAL | Não validado aqui | Sem confirmação falsa ou segunda intenção |
| Unknown/readback indisponível | Simulado | Fixture: verificação readonly, sem segundo POST | Não validado aqui | Estado unknown em memória; reinício completo não comprovado |

Textos de simulação e “EXEMPLO” não são apresentados como operação real. O CTA é “Registrar entrega por exceção” para preservar a política canônica de telemetria não obrigatória. Metadados de Venue/operador são reais. Estas diferenças não têm aprovação visual explícita; não declaramos paridade integral aceita. O comparador mostra o desktop inteiro do protótipo, inclusive sua coluna editorial de laboratório, ausente no produto real.

Validação:

- `npm run build`: PASS; `npm run typecheck`: PASS; ESLint dos arquivos modificados: PASS.
- `npm run test:visual -- ux2-delivery-page.spec.ts`: 9 PASS (14.0s): quatro larguras, readonly back, ACK perdido, rival, mudança de destino, unknown/readback. Interceptações são fixtures visuais, não integração.
- PostgreSQL17.6 dedicado, loopback55644, database `rodada_web_e2e`, API8144/Web3144. `attendance.spec.ts`: 1 PASS (20.9s), lifecycle existente adaptado ao novo destino e estado canônico.
- `attendance-delivery-page.spec.ts`: 4 PASS (32.5s), widths360/390/430/1280. CASH e Close reais via API no banco descartável; então entrega READY em Tab CLOSED, retorno readonly, completion commit real com perda injetada apenas no ACK, GETs canônicos e ledger preservado. Capturas `real-closed-delivered-*` são integração real, dados distintos da fixture do comparador.

Revisão independente root R3, base0f37fb03→8ba34c47: **NO_FINDINGS_WITH_GAPS**. Leu novo componente/callers/testes e captura390; nenhum achado reproduzível no preflight identity/destination/rival, readback DONE/DELIVERED ou ausência de mutation ao navegar. Gaps: unknown somente em memória, restart não comprovado, paridade integral/Android e aprovação de diferenças textuais pendentes. Revisão do delta posterior de wrapper/rodapé, header360 e tipografia: nenhum achado reproduzível; fonte final `cca4e61a`.

Gap E03-07 existente: refresh global ainda une delivery/tables/zones; uma falha de Dispatch pode afetar online core. A correção pertence à próxima slice e não está aceita aqui.

Sem merge, deploy, aparelho físico, TalkBack ou aceite global E03. CI amplo e integração da pilha permanecem gates independentes.
