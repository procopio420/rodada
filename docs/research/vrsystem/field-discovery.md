# Field discovery: 60-minute script + proof collection
**Purpose:** convert public capability claims into `CONFIRMED`, `REPORTED`, `NOT_USED_CONFIRMED` and `UNKNOWN` for the **specific Aderlan venue**. No assumed availability/configuration or fabricated button counts.

## Prepare
Owner consent and one named staff guide. Prefer **before service** for administrative screenshots and **peak service** for pure observation. Do not interfere with sales, issue refunds or alter settings. Obtain permission before photographing any screen and mask customer names, contact, CPF, totals tied to specific people, payment identifiers, access tokens, staff PINs and serial/license keys. Respect provider/vendor terms; no password requests, database dumps, remote access or unauthorized extraction. Save files offline in a project-approved restricted folder; label device, timestamp, version, screen/module, role and what was redacted. Separate observed fact from staff recollection.

## Single-page interview: natural-language questions
### Aderlan (owner; ~10 min)
1. “O que faria você desistir do Rodada no primeiro dia, mesmo com o atendimento mais rápido?”
2. “Quais relatórios você abre toda noite e no fim do mês? Mostra um sem dados pessoais?”
3. “Qual versão e quais módulos da VR vocês pagam? Pode mostrar só os **nomes e valores** da fatura/contrato, ocultando cadastro e chaves?”
4. “A venda gera nota fiscal/NFC-e no sistema? Quem cuida disso, vocês ou contador? Pode chamar o contador para validar a mudança?”
5. “Quem pode mexer em preços, descontos, cortesia, cobrança de 10%, caixa e cancelamento?”
6. “Se o sistema parar por 20 minutos em noite cheia, como vocês vendem, registram e acertam depois?”

### Caixa (~10 min)
1. “Me mostra: abrir comanda, achar conta, cobrar 2 pessoas separadas e imprimir a conta. Onde costuma travar?”
2. “Vocês juntam mesa ou comanda? Dividem itens de uma mesa entre clientes? Com que frequência?”
3. “É comum cobrar parte Pix, parte cartão, parte dinheiro? Como confere valor da maquininha?”
4. “Fazem sangria e fundo inicial? Como conferem troco e diferença no fim do turno?”
5. “Como desconsidera item repetido, corrige valor ou reabre uma conta fechada?”
6. “O que sai da impressora e o que é eletrônico? Mostra quais botões imprimem **ticket não fiscal** versus nota?”

### Chef/cozinha (~10 min)
1. “Quando entra um pedido novo, como sabe? Demora ou aparece só quando alguém imprime?”
2. “Como chegam observações e adicionais? Se for meio a meio ou sem ingrediente, aparece claro?”
3. “Quando parte de um pedido fica pronta, o que você faz? E se atrasar?”
4. “Se a impressora ou tela travar, quem avisa? Como evitam fazer duas vezes?”
5. “Quais produtos você bloqueia quando acabam? Como o caixa e garçons descobrem?”

### Operador de bar (~5 min)
1. “Quem lança e quem recebe pedido de bebida? Aparece separado da cozinha?”
2. “Como faz dose/tamanho e adicionais? O que mais atrapalha durante o pico?”
3. “Que tela/ticket você realmente usa? O que faria se caísse agora?”

### Garçom (~10 min)
1. “Me acompanha num pedido comum — onde você vai e quantas vezes volta ao caixa?”
2. “O que você faz quando duas pessoas querem uma comanda só ou contas separadas?”
3. “O cliente pede mais um item enquanto a cozinha prepara: como altera?”
4. “Usaria seu celular pessoal? Qual versão Android, NFC e internet você usa? Aceitaria app de trabalho? Quem paga dados/bateria?”
5. “Como confirma pedido pago, cancela erro ou pede ajuda sem abandonar a mesa?”

## 60-minute observation (suggested)
| Time | Observe | Record |
| --- | --- | --- |
| 00–05 | Consent, exact installed software, workstation/module/version, normal role | public version, module list, devices, printer/terminal type (no passwords) |
| 05–15 | Cashier opens/locates Tab, customer arrives, split table/comanda, sends mixed Bar/Kitchen order | exact clicks/key presses and screens, order path and devices, user-perceived obstacles |
| 15–25 | Chef and bar receive and mark items; modifications/notes | time from confirmed order to visible station card, grouped/partial readiness; print dependencies |
| 25–35 | Cashier partial tender, difference/troco, print/check, fee/discount and close | tender count, source of finality, audit approvals and exception resolution |
| 35–45 | Observe peak-like concurrency, second order and mistaken duplicated item; **simulate only in authorized sandbox** | staff route, permission behavior, latency, retries, duplicate handling |
| 45–52 | Owner's daily report, open Tabs, fiscal handling, historical correction | report names, fiscal producer/issuer path, exact accounting handoff |
| 52–60 | Network/printer/power contingency explanation (do NOT break production); export/license/backup question; recap | missing risks, signed owner exceptions and next evidence needed |

If visiting during actual peak: prioritize **observation**, not test transactions. Film/screenshare only with express staff/owner permission and avoid capturing patrons.

## Configuration/screenshots safe checklist
- [ ] App/module executable names, visible version (Gourmet, PDV, KDS, Droid, VR Pedidos, Bridge)
- [ ] Table/comanda setup screen; code/barcode use; physical plastic/paper cards
- [ ] Sample *redacted* product with base price, variants/addition, prep time, print station
- [ ] Payment tender types and cashier opening/closing settings (mask identifiers)
- [ ] Printer/ticket configuration, per-station routing, print-at-add vs at-close
- [ ] KDS current screen + visible config (without private admin credential); whether it is actually used
- [ ] Discrepancy/reports dropdowns and exports, never patron transaction row with PII
- [ ] Fiscal toggles, sample redacted DANFE/QR receipt **only if permitted** and accountant-confirmed explanation
- [ ] Hardware inventory: receipt printers, kitchen printer, cash drawer, barcode scanner, terminal, PC OS, LAN/Wi-Fi
- [ ] Vendor invoice name and plan/modules/device/license counts with private details hidden

## Rapid relevance classifications
Use a sheet with columns `capability, VR installed? (yes/no/unknown), actually used (CONFIRMED/REPORTED/UNKNOWN/NOT_USED_CONFIRMED), frequency per shift, role, critical on Saturday?, observed action count, observed latency, alternative, evidence timestamp, interviewer, confidence`. Ask explicitly which functions are *ever used*, not only what the license offers.

## Measurements without invented benchmarks
Choose same 10 scenario scripts in [operational-workflows](operational-workflows.md). Use manual stopwatch plus video only if consented. Timestamp three moments (staff confirms; API/printed signal; staff sees station order), register device/network and whether customer/order was real vs controlled test. Sample many events across ordinary and peak shifts; report P50/P95 and range with counts. Record interruptions as failures rather than discarding them. A “30s KDS” statement in historical docs is **not** measured baseline for installed VR.

## Decisions owner needs to sign off
1. Payment methods that cannot disappear.
2. Whether printing is **mission-critical** for kitchen, cashier, patron.
3. Which menu modifier/combination/fee patterns are unavoidable.
4. How to handle open Tabs at midnight/cutover.
5. Fiscal process and vendor relationship; accountant signs classification and issuing responsibility.
6. Acceptable training/roll-back procedure and staffing during pilot.
