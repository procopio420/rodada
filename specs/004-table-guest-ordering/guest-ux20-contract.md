# Spec 004 — Cliente UX 2.0: Mesa, Ficha e Híbrido

**Decisão de produto: 16/10/2026. Status: UX/especificação congeladas para implementação; produção NÃO homologada.**

Fontes complementares: docs/product/guest-experience.md, docs/design/guest-ux20-two-tab-navigation.md, specs/004-table-guest-ordering/spec.md, docs/domain/model.md. Protótipo de referência: prototype/guest-ux-20/index.html na branch prototype-guest-ux20-20261016.

## 1. Decisões definitivas

1. Há UM único Cliente Rodada, web/PWA, com apresentação determinada pelo contexto do estabelecimento.
2. O gerente configura a operação: MESA, FICHA ou HIBRIDO. **O cliente NÃO escolhe o modo.** O QR e a área/ponto de atendimento determinam a experiência.
3. MESA: cardápio elegível de bebidas e comidas, produção no Bar/Cozinha e entrega à mesa. QR físico de Table identifica mesa; pedidos e dinheiro pertencem à Tab, não à Table.
4. FICHA: **somente bebidas, alcoólicas ou não**, produzidas no BAR para **retirada no balcão**. Sem comida, porções, pratos, lanches, combos mistos ou roteamento para Cozinha. Código curto como FG84 exibido na ficha digital e na fila do bartender, com conferência visual.
5. HIBRIDO: operação simultânea Mesa + Ficha no mesmo Venue, segregada por área e tipo de QR. QR de Table conduz a Mesa; QR específico do bar/pista conduz a Ficha.
6. MVP: configuração manual pelo gerente no Manage, com autorização e auditoria. Horários/turnos automáticos são **roadmap**, não bloqueiam o lançamento inicial.
7. Mudar o modo NÃO converte Tab, pedidos, pagamentos ou ocupação já ativos. Novas sessões seguem a nova configuração. Staff mantém a capacidade de bloquear novos pedidos se necessário.
8. Navegação guest tem EXATAMENTE duas abas: **Pedir + Minha comanda** (Mesa) ou **Pedir + Minha ficha** (Ficha). Não existe aba Agora para cliente.
9. Depois de enviar pedido: permanecer em Pedir, mostrar confirmação compacta visível com número do pedido e ação Ver pedido. Continuar pedindo não exige passo adicional.
10. QR, código FG84 e nome não são credenciais financeiras. O backend valida GuestSession/Tab, disponibilidade, regras de catálogo, modo e pagamentos.
11. Todos os itens do protótipo são DEMO. Não confundir tela aprovada com integração de API, PSP, Django, Manage ou produção.

## 2. Matriz

| Modo do Venue | QR Mesa (Table) | QR de balcão/pista | Catálogo | Fulfillment |
| --- | --- | --- | --- | --- |
| MESA | Mesa, quando habilitada | Ficha desabilitada | Bebidas + comidas elegíveis | Bar/Cozinha, entrega à mesa |
| FICHA | Desabilitado para NOVAS sessões Mesa | Ficha | Somente bebidas autorizadas | BAR, retirada pelo cliente |
| HIBRIDO | Mesa | Ficha | Depende do tipo do QR, não da escolha guest | Mesa recebe entrega; Ficha retira no BAR |

QR de mesa não deve ser reinterpretado como QR de Ficha quando configuração muda. Ambos resolvem pontos tipados com tokens opacos estáveis. O QR identifica contexto, jamais dá acesso automático a uma conta alheia.

## 3. Mesa: jornada e invariantes

- QR Table permanente identifica somente Table. A API consulta status, permissão de guest ordering e ocupação/generation.
- Mesa disponível: cliente pode iniciar ocupação autonomamente quando permitido. Mesa ocupada: pode criar Tab individual ou entrar em Tab existente com autorização. Uma TableOccupancy admite muitas Tabs.
- Tab é unidade financeira; múltiplas Tabs na mesma mesa não misturam saldos, itens, pagamentos ou limites.
- Catálogo da Mesa inclui somente produtos habilitados para entrega no contexto da mesa. Comida segue Cozinha e bebida segue Bar, conforme roteamento canônico do Product.
- Pedido confirmado permanece na tela Pedir. Minha comanda mostra todos os pedidos ativos, resumo de status, Mais uma rodada, saldo, pagar e detalhamento recolhível.
- Mover localização/contexto da mesa não recria Tab nem altera ledger ou QR. Pedido não cria confirmação fictícia de entrega.
- Pagamento parcial ou integral não libera mesa. Liberação, limpeza e rotação de geração de acesso são operações próprias da Table.
- Guest sem celular continua sendo atendido pelo staff, com itens na Tab autorizada.
- Bloqueio de pedidos guest não impede pagamento, consulta de conta, suporte do staff ou pedidos internos.

## 4. Ficha: bar somente bebidas

- QR BAR_PICKUP é afixado no balcão, entrada ou pista; aponta para um GuestAccessPoint do tipo BAR_PICKUP, NÃO para uma mesa fantasma.
- Cliente abre ou retoma Tab sem TableOccupancy; no acesso inicial é emitido um código curto legível (ex. FG84) que aparece na ficha e na fila de produção.
- Código possui unicidade entre fichas ativas dentro do escopo do Venue/turno, conferida transacionalmente. Evitar colisão e reaproveitamento simultâneo; definir expiração/reativação auditáveis. Código não é prova de autorização.
- Somente Product explicitamente classificado BEVERAGE e elegível para BAR_PICKUP pode entrar no pedido da Ficha; inclui água, refrigerante, cerveja, chope, drinks e equivalentes não alcoólicos.
- Não se basear em esconder a categoria Comidas/Porções na interface: **o servidor recusa** food, acompanhamentos com preparo de cozinha, combos mistos, modifiers que incluam comida e manipulações de API.
- Produtividade: a fila do bartender exibe FG84 e itens/quantidades dos pedidos; bartender faz conferência visual e entrega. Sem scan, PIN ou confirmação compulsória para cada retirada.
- Cliente ou bartender podem marcar item como retirado de modo opcional; essa marcação não altera, por si, o fato canônico da fila do BAR. Não retirar pedidos prontos só porque o cliente marcou.
- Estados guest resumidos: Recebido → Preparando → Pronto para retirar. Minha ficha prioriza código FG84, itens prontos, pedidos ativos, histórico recolhido.
- Navegação Pedir + Minha ficha. Em Minha ficha há apenas UMA entrada para o financeiro: **Conta e pagamento** (subtela), sem botões concorrentes Pagar/Ver conta.
- Ficha permite pagamento parcial, integral e pré-pago quando configurado; pagamento confirmado não encerra automaticamente Tab. Sessão e pagamento pendentes são recuperáveis e idempotentes.
- Nunca expor score, rating de risco, limite total ou alerta de crédito. Se Venue exigir um adiantamento, mostrar somente o valor necessário e por quê, sem revelar a política interna.
- Ficha não recebe couvert por quantidade de QR escaneados; qualquer cobrança explícita segue regras de cobrança e party-size reais (Spec 016).

## 5. Híbrido: simultaneidade por área/QR

- Mesas operam como Mesa, com comidas e bebidas e entrega; pista/bar como Ficha, bebidas apenas para retirar.
- Experiência é resolvida no servidor por Venue + ponto de acesso/QR + configuração efetiva + GuestSession/Tab preexistentes. Nem hora do celular, nem GPS, nem preferência guest escolhem o modo.
- Um cliente pode possuir duas Tabs distintas sem fusão nem pagamento automático entre elas.
- Mover uma Tab de Mesa para Ficha (ou vice-versa) NÃO é automático. Transferência cross-mode por staff é um futuro fluxo explícito, auditado e com revalidação; fora do fechamento de UX.
- No Híbrido, a mesma disponibilidade e os mesmos fatos de Order/Payment são refletidos em Cliente, Bar, Cozinha, Caixa, Atendimento e Manage; pedidos Ficha jamais geram trabalho de Cozinha.
- QR de acesso desabilitado mostra mensagem curta e alternativa autorizada, sem transformar a entrada numa Tab diferente.

## 6. Manage: configuração e precedência

### MVP manual
- Gerente autorizado define modo do Venue: TABLE, FICHA ou HYBRID.
- Em Híbrido, cadastra áreas/pontos de acesso tipo TABLE ou BAR_PICKUP e gera QR por ponto, com prévia da experiência que esse QR abrirá.
- Define publicação/elegibilidade de bebidas para Ficha, disponibilidade operacional, políticas guest por tipo de acesso e pode bloquear novos pedidos de um tipo.
- Toda mutação: capability, isolamento por Venue, versão, ator/timestamp, auditoria, conflitos concorrentes e API como fonte de verdade.
- Configuração de modo é **separada** de Table.guest_ordering_mode já existente (DISABLED | JOIN_ACTIVE | DIRECT). Este último controla PERMISSÃO na mesa; não define a experiência Mesa/Ficha/Híbrido.
- Para Venue legado sem configuração migrada, comportamento padrão compatível é MESA, não Ficha inferida.
- O servidor nunca aceita modos/eligibility arbitrários enviados pelo guest.

### Troca de modo com atendimento aberto
- Snapshote experiência da Tab na abertura (TABLE ou FICHA); modo continua estável enquanto Tab aberta.
- Mesa → Híbrido às 21h: Tabs Mesa abertas continuam com pedidos, saldo e entrega Mesa; novas sessões atendem regras do modo Híbrido.
- Híbrido → Ficha: Tab Mesa ativa continua consultável e quitável; seu direito de novos pedidos segue política operacional explicitamente definida para sessões legadas, não inferência de UI.
- Nunca converter retroativamente ledger, Order, Payment, GuestSession ou TableOccupancy. Atualização de modo não encerra uma ocupação.
- Gerente pode bloquear novos pedidos sem apagar histórico; operações financeiras e suporte seguem regras próprias.
- Toda mudança deixa evento auditado e versão usada para resolver novas sessões.

### Agenda/horário futuro
- Apenas roadmap: períodos de atendimento por fuso IANA do Venue, corte de dia operacional, turnos que cruzam meia-noite, exceções/feriados, conflitos e override manual prioritário.
- Exemplo ilustrativo: dia MESA, noite HIBRIDO. Nenhum horário é assumido por padrão.
- No momento da virada, SOMENTE novas sessões usam a configuração nova; sessão existente mantém experiência congelada. Nunca exigir migração automática de Tab às 21h.

## 7. Esboço de contratos tipados (proposta técnica, NÃO migração já implementada)

- VenueGuestExperiencePolicy: venue_id, mode TABLE|FICHA|HYBRID, version, updated_at/by, effective_revision.
- GuestAccessPoint: venue_id, kind TABLE|BAR_PICKUP, opaque_token, table_id apenas se TABLE, zone_id opcional, enabled, version.
- Tab.experience_snapshot: TABLE|FICHA imutável durante uma visita. Tab sem mesa continua suportada.
- ProductGuestEligibility ou projeção derivada tipada: beverage/food, channel TABLE_DELIVERY|BAR_PICKUP e routing real. Não inferir somente do nome de categoria.
- PickupDisplayCode: code FG84, venue_id, tab_id, active window, uniqueness e rotação/revogação; visível mas não segredo.
- Reusar Tab, Order, Payment, GuestSession, TableOccupancy, Dispatch, Product e ledger já canônicos. Não criar um segundo financeiro para Ficha.

## 8. Fluxos e exceções compartilhadas

MESA: QR Table → ocupação/sessão → criar ou entrar em Tab autorizada → Pedir bebidas/comidas → enviar Order idempotente → confirmação discreta no cardápio → Minha comanda (pedidos, saldo, pagar, Mais uma rodada) → sair → staff libera Table.

FICHA: QR BAR_PICKUP → criar/retomar Tab sem mesa → exibir FG84 → Pedir somente bebidas → fila BAR com FG84 → cliente retira visualmente → Minha ficha (prontos primeiro, conta e pagamento) → fechamento Tab.

- Se produto ficou indisponível ou preço mudou antes da confirmação, apresentar alteração e preservar carrinho; nada de ordem fantasma.
- Se rede caiu ou ACK é incerto, reconciliar pelo identificador da intenção; não reenviar pedido duplicado.
- Ao pagar, permitir parcial e integral, sem fechamento automático. PSP e ledger, não a UI, determinam confirmação.
- Pix/cartão pendente: persistir intenção, reconsulta, sem duplicidade mesmo após refresh e concorrência.
- Limites de exposição internos nunca são exibidos. WARN_ONLY apenas informa equipe; REQUIRE_PARTIAL solicita valor discreto; PREPAID usa crédito confirmado.
- Contestação de item/pagamento abre solicitação de revisão; nunca apagar charge/registrar refund sem evento financeiro confirmado.
- Retirada da Ficha: código FG84 conferido pelo bartender, sem obrigação de leitura ou dupla confirmação.
- Acessibilidade mobile 360/390/430, uma mão, toque ≥44 px, menu sem jargão, foco em sheets, safes areas, teclado virtual, bom contraste.

## 9. Cenários obrigatórios para aceite

| ID | Cenário | Aceite |
| --- | --- | --- |
| UX-01 | Mesa livre QR | Abre catálogo Mesa direto sem login |
| UX-02 | Mesa ocupada com 2 Tabs | Cria Tab própria ou entra autorizado; ledger separado |
| UX-03 | Ficha QR no balcão | Abre Ficha sem mesa, exibe FG84 |
| UX-04 | Bebida na Ficha | Bar recebe FG84 + itens, sem Cozinha |
| UX-05 | Comida na Ficha via UI ou API | Rejeita sem criar Order/Charge |
| UX-06 | Combo bebida+comida na Ficha | Rejeita inclusive modifiers e fraude de API |
| UX-07 | Híbrido com ambos os QRs | Mesa oferece comidas/bebidas; pista só bebidas |
| UX-08 | Cliente tenta escolher o modo | UI não oferece seletor; QR e servidor resolvem |
| UX-09 | Alteração manual durante Tabs abertas | Sessões ficam com modo antigo; novas seguem novo |
| UX-10 | Horário muda durante sessão | Nada muda automaticamente no MVP |
| UX-11 | Código FG84 duplicado | Gerador recusa colisão ativa; fila não mistura Tab |
| UX-12 | Retirada | Conferência visual, confirmação opcional, sem bloqueio |
| UX-13 | Pedido enviado | Cliente fica no Cardápio; aviso visível e Ver pedido |
| UX-14 | Pagamento parcial em ambas experiências | Tab permanece ativa e idempotência mantém saldo |
| UX-15 | Pix pendente e refresh | Reconsulta mesma intenção sem cobrar de novo |
| UX-16 | Staff bloqueia guest ordering | Novos pedidos bloqueados, conta/staff preservados |
| UX-17 | Mudança de mesa | Não altera Tab/ledger nem resolve Ficha |
| UX-18 | Duas Tabs/Venues | Sem vazamento de pedidos, pagamentos e código/QR |
| UX-19 | App sem conexão, produto esgotado, retry | Mensagem e recuperação sem dupla Order |
| UX-20 | Cliente sem celular | Staff atende sem exigir QR ou cadastro |

## 10. Gates e significado de fechamento

### APROVADO — contrato de UX/produto (não execução)
- [x] Duas abas; sem Agora.
- [x] Mesa com bebida/comida e entrega.
- [x] Ficha somente bebidas retiradas no BAR, FG84 e confirmação opcional.
- [x] Híbrido simultâneo por QR/área, sem escolha cliente.
- [x] Manage manual MVP, automação por horário adiada.
- [x] Sessão antiga não migra de modo ao trocar configuração.
- [x] Pedidos, conta, repetição, pagamentos, exceções e ações principais documentados.

### PENDENTE — para fechar implementação real (nenhum item presumido PASS)
- [ ] Configuração tipada Venue e pontos de acesso no Django/Manage, com autorização/auditoria e migrações.
- [ ] Catálogo Ficha filtrado e enforcement de bebida + BAR_PICKUP no backend/dispatch.
- [ ] QR BAR_PICKUP real, FG84 único/revogável e integração com fila BAR.
- [ ] Preservar Tab/GuestSession/Order/ledger durante mudanças de modo com teste concorrente.
- [ ] Migrar protótipo aprovado para Cliente Web/PWA real; garantir que Android/Atendimento não herda navegação de guest.
- [ ] Regressão PostgreSQL de auth, cross-Venue, catálogo, idempotência, PSP, pagamento parcial, bloqueios e concorrência.
- [ ] Browser visual 360×640, 390×844, 430×932, desktop + foco, teclado, a11y, safe areas, captura de screenshots.
- [ ] E2E Cliente–Bar–Cozinha–Caixa–Manage, CI no SHA final, revisão independente e merge.
- [ ] Homologação operando com bar real e plano de rollout/rollback.

**Fora do MVP:** agendamento automático; comida na Ficha; escolha cliente; fusão automática Mesa/Ficha; exigência de CPF/login; scan da retirada; novo tipo de ledger.

**Definição:** CLIENTE FECHADO EM UX = decisões aprovadas, protótipo é fonte de comportamento e este contrato é fonte das regras. CLIENTE FECHADO EM PRODUÇÃO = todos os gates de implementação e homologação executados com evidências. Este documento não declara backend, deploy, PSP ou screenshots reais já concluídos.
