# Spec 032 — Acceptance e cenários de teste

**Nenhum critério está aceito ainda.** Para marcar `[x]`, anexar SHA/ambiente, testes executados e captura/evidência quando visual. Critérios de projeto não comprovam implementação.

## Identidade física e mesa
- [ ] **S032-A01** Mesa existente com QR vinculado abre/fecha atendimento sem perguntar pelo QR novamente; tela de criar mesa não reaparece.
- [ ] **S032-A02** `Nova mesa` cria Table instantaneamente mesmo com scanner negado; oferece `Vincular QR` ou `Agora não`; mesa sem tag opera internamente e exibe indicador discreto.
- [ ] **S032-A03** Concorrem dois staffs tentando atribuir a mesma PhysicalTag a mesas diferentes: só um vínculo vence; erro esclarece conflito e não move Tab/Occupancy/Order.
- [ ] **S032-A04** Transferir/remover tag de mesa temporária requer autorização/auditoria; antigo QR não aponta para nova mesa após desatribuição; QR legado continua válido durante rollout.
- [ ] **S032-A05** Tag estrangeira/retired/inválida não revela Venue/mesa, não cria sessão e não permite bind.

## Entrada, ocupação e guest authorization
- [ ] **S032-A06** Scan read-only de QR de mesa AVAILABLE não muda `Table.status` nem cria ocupação até CTA; CTA `Começar nesta mesa` é guest-first e cria ocupação sem staff.
- [ ] **S032-A07** Double click / 2 guests simultâneos criam no máximo uma ocupação ativa da mesa, mas cada participante mantém sua Tab privada por padrão.
- [ ] **S032-A08** Sessão guest antiga após release/cleaning/rebind não consegue enviar pedido; só a geração/capability atual autoriza; staff emergency block é imediato.
- [ ] **S032-A09** Começo provisório vazio expira segundo política sem deixar fantasma; qualquer Order/Charge/Payment pendente, chamada ou operação aceita impede expiração arbitrária; não se presume presença física segura pelo QR.
- [ ] **S032-A10** Mesas DIRTY/CLEANING/OUT_OF_SERVICE mostram erro orientado a próxima ação e não admitem order guest; staff segue podendo atender por seus próprios fluxos autorizados.
- [ ] **S032-A11** Um visitante da mesma Table não consegue ler saldo ou pedidos privados de outro sem compartilhamento explícito.

## QR geral e continuidade
- [ ] **S032-A12** QR geral abre fluxo sem Table; pessoa sem sessão cria Tab anônima explicitamente, sem cadastro obrigatório.
- [ ] **S032-A13** Pessoa com Tab autorizada vinda do QR da mesa vê `Continuar minha comanda` ao abrir QR geral; não duplica Tab/saldo/draft; voltar à mesa mantém Tab.
- [ ] **S032-A14** Troca de Table é transacional, preserva o ledger e revalida placement/Occupancy/generation; não entrega pedido antigo na mesa errada silenciosamente.

## Pedido, pagamento e pickup
- [ ] **S032-A15** Dois pedidos aceitos em 21:59/22:01 preservam AT_TABLE/PICKUP respectivamente após mudança do Venue; coexistem na fila correta.
- [ ] **S032-A16** QR geral: Pagar agora só libera retirada após pagamento canônico confirmado. Pix pending/timeouts e pagamento externo não verificado **não** geram voucher elegível.
- [ ] **S032-A17** `Na conta` libera retirada apenas em Tab autorizada/limite válido; visitante anônimo sem crédito autorizado não burla pagamento.
- [ ] **S032-A18** Código curto humano (ex. FG84) é único entre pickup groups vivos no mesmo Venue, distingue letras/números, exibe os mesmos itens/código em Guest/Bar; colisão/concorrência e quarentena testados.
- [ ] **S032-A19** FG84 sozinho não permite claim de Tab, consulta de saldo, manipulação de pedido ou pagamento, nem acesso a outro Venue.
- [ ] **S032-A20** Cliente identifica seu grupo como `Pronto`; bartender acha FG84 pela busca sem scroll extenso nem scan; nenhum tap compulsório para entregar.
- [ ] **S032-A21** `Já retirei` só registra `GUEST_DECLARED`, nunca `STAFF_CONFIRMED`; ausência de clique mantém `UNKNOWN`; vencimento visual não fabrica `DELIVERED`.
- [ ] **S032-A22** Parcial: retirar 2 de 3 itens deixa terceiro pendente; corrigir erro registra trilha auditável; item não pode ser entregue duas vezes por confirmação concorrente, sem prometer proteção contra fraude sem confirmação.
- [ ] **S032-A23** Reapresentar mesmo FG84 ou screenshot exibe ao staff estado e confiança; modo de risco pode exigir validação adicional explicitamente configurada, sem impor scan na operação padrão.

## Finalização, perda de acesso e conexão
- [ ] **S032-A24** Cliente paga só a própria Tab/parte, não libera mesa nem fecha outra Tab; mesa só libera com transição operacional adequada. Tab sem mesa fecha sem devolver tag.
- [ ] **S032-A25** Reabrir PWA recupera sessão válida e pickup code; sessão revogada aciona recuperação segura, não permite salto automático para outra comanda.
- [ ] **S032-A26** Cliente perde celular: caixa reimprime ficha/recupera pedido por capability, com audit trail e sem mostrar dados financeiros a quem só conhece FG84.
- [ ] **S032-A27** Double tap, 503, ACK perdido, reconnect e reinício de app não geram Order/Payment duplicado; readback resolve intenção original com mesma chave.
- [ ] **S032-A28** Host errado, tenant errado, GuestSession expirada e tab status CLOSED não autorizam pedidos nem acesso financeiro; audit/rate-limit aplicados.

## UX, campo, segurança e rollout
- [ ] **S032-A29** Primeira dobra 360/390/430 mostra próximo passo e contexto; fluxo QR guest não exige CPF/instalar app, tem foco visível, contraste, targets >=44px e leitura de tela; fontScale 2x sem perda de CTA.
- [ ] **S032-A30** Turno de teste 20h–02h inclui mesa improvisada, 4 participantes, QR geral, modo balada, pagamento pendente, pedido misto, retirada parcial, troca de mesa, navegador fechado, falta de rede e liberação operacional, com estado canônico final.
- [ ] **S032-A31** Status CODED/TESTED/CI/HOMOLOGATED/DEPLOYED só sobe mediante evidência real do SHA e revisão independente R3 para risco alto; sem deploy por aprovação documental.

## Instrumentação de produto

Testar eventos com provenance de: scan, explicit-start, occupancy-confirm, order-accepted, payment-confirmed, pickup-ready, pickup-declared, pickup-staff-confirmed, exceptional-pickup, table-release. Medir clique até primeiro pedido, busca FG84, falhas de sessão e taxa de UNKNOWN sem mascará-la.
