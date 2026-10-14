# Acceptance — Spec 027: início de atendimento e claim de ocupação

**Estado:** critérios técnicos implementados e cobertos por homologação automatizada; resultados por head em `evidence.md`. Piloto observado continua pendente. IDs TS027-01..TS027-36.

## Início da mesa e responsabilidade

- [x] **TS027-01** — Dada mesa AVAILABLE, quando staff com `table.manage` toca "Iniciar atendimento", há exatamente uma TableOccupancy nova, mesa fica OCCUPIED e funcionário autenticado vira responsável sem formulário obrigatório.
- [x] **TS027-02** — O start staff não cria Tab, Order, Customer, Payment, GuestSession, party-size nem lançamentos no ledger.
- [x] **TS027-03** — Ao confirmar start, a ficha mostra mesa, área, "Em uso", "Atendimento: você", zero comandas e "Nova comanda".
- [x] **TS027-04** — Cliente em `DIRECT` que inicia mesa via QR cria/recupera ocupação sem responsável; staff pode reivindicar depois sem recriar a ocupação ou revogar a guest session.
- [x] **TS027-05** — Fechar a última Tab nunca libera a mesa nem retira sua responsabilidade automaticamente.
- [x] **TS027-06** — Mesa DIRTY, CLEANING e OUT_OF_SERVICE não pode iniciar; servidor retorna estado, UI oferece ação compatível sem pular limpeza.
- [x] **TS027-07** — Mesa OCCUPIED não aceita outro start como nova ocupação ou takeover implícito; UI mostra contexto atual e ações seguras.

## Comandas vinculadas e pedido

- [x] **TS027-08** — Da ocupação ativa, "Nova comanda" exige apenas confirmação e nome opcional; associa Tab + ocupação atômica e abre cardápio com Mesa/Tab corretas.
- [x] **TS027-08a** — Em Contas no Atendimento Web, Nome da Comanda é obrigatório e permanece visível; “Abrir comanda” apresenta mesas AVAILABLE e OCCUPIED com ocupação ativa. Mesa disponível inicia visita e comanda atomicamente; mesa em uso recebe nova comanda na ocupação existente, preservando o responsável. Mesas sujas, em limpeza e fora de uso não aparecem.
- [x] **TS027-09** — Se associação falha, Tab nova e efeitos relacionados são revertidos; não há Tab órfã por race.
- [x] **TS027-10** — A ocupação comporta duas ou mais Tabs com pagamentos/exposições independentes.
- [x] **TS027-11** — Comandas aparecem como ações clicáveis na mesa e abrem imediatamente a Tab selecionada no Android/Web.
- [x] **TS027-12** — Homônimos e comandas anônimas são desambiguados por contexto de exibição não secreto; ação mantém Tab ID correto, sem resolver por nome.
- [x] **TS027-13** — Uma Tab já vinculada à outra ocupação não é associada cegamente; UI mostra mover comanda e API rejeita attach indevido.
- [x] **TS027-14** — Pedido em Tab de mesa usa destino da ocupação atual e `Order.confirmed_by` do ator; não altera responsável.
- [x] **TS027-15** — Abertura de Tab sem mesa/balcão segue permitida sem criar ocupação fictícia.
- [x] **TS027-16** — Seleção de outra mesa/comanda não descarta draft pendente silenciosamente; resultado incerto de pedido não permite nova intent indistinta.

## Ownership / claim

- [x] **TS027-17** — Claim sem responsável, com versão correta, atribui ator e registra evento único.
- [x] **TS027-18** — Takeover de colega exige ação explicitamente rotulada com identificação do responsável existente; server atualiza versão + audita de/para.
- [x] **TS027-19** — Mesmo garçom pode receber pedido em mesa assumida por colega sem claim, sem bloqueio e sem trocar responsável.
- [x] **TS027-20** — Dois claims concorrentes com mesma versão geram uma transferência e um 409 RESPONSIBILITY_CONFLICT, sem overwrite silencioso.
- [x] **TS027-21** — Claim de mesmo funcionário responsável é no-op auditável sem alterar versão de responsabilidade.
- [x] **TS027-22** — Usuário sem sessão/capability ou de outro Venue não inicia/assume/abre comanda na ocupação e não obtém dados de staff de outro Venue.

## Consistência, rede e ciclo de vida

- [x] **TS027-23** — Start concorrente por dois funcionários em PostgreSQL gera exatamente uma ocupação e só um responsável inicial; perdedor vê snapshot existente.
- [x] **TS027-24** — Mesmo `idempotency_key` + fingerprint repete resposta/IDs sem novos efeitos; mesma chave com payload divergente produz 409.
- [x] **TS027-25** — Timeout após commit, reload Web, kill/restart Android e retry não duplicam ocupação, claim, Tab nem eventos; o resultado desconhecido é exibido como verificação, não sucesso.
- [x] **TS027-25a** — Replay de `service/open-tab` retorna a mesma mesa e Tab; uma mesa que deixou de estar AVAILABLE falha sem criar Tab ou ocupação parcial.
- [x] **TS027-26** — `release_table` concorrente a `tabs/open` termina em Tab vinculada antes do release **ou** rollback integral do open; sem Tab órfã.
- [x] **TS027-27** — Liberar mesa não fecha Tabs, revoga autorizações guest pertinentes e inicia DIRTY; limpeza preserva fluxo/geração da Spec 004; owner não vaza para próxima ocupação.
- [x] **TS027-28** — SSE/outbox publica somente após commit; Android/Web se atualizam a partir de leitura canônica, sem confirmação prematura.
- [x] **TS027-29** — Android/Web usam o mesmo contrato; gateway Web não expõe dinheiro/estorno/caixa, nem retorna informação de owner para guest.
- [x] **TS027-30** — Em Android real e Web móvel 360–430px, primeira ocupação requer 1 toque, comanda da mesa é clicável, CTAs têm alvos acessíveis e textos de estado/error comunicam intenção e destino.

## Destaque de QR sem responsável

- [x] **TS027-31** — QR lido e carrinho criado sem pedido confirmado não geram alerta urgente; ocupação sem responsável tem apenas indicação discreta `Sem responsável`.
- [x] **TS027-32** — O primeiro pedido `source=GUEST` confirmado numa ocupação sem responsável faz surgir `Pedido via QR · Sem responsável` na Mesa e em Agora, com destino correto, contagem e antiguidade derivadas da API (Android e Web).
- [x] **TS027-33** — Pedidos guest adicionais e replays idempotentes atualizam um **único** destaque por `occupancy_id`/`generation`, sem banners duplicados, novos DispatchTasks ou mutações financeiras.
- [x] **TS027-34** — Quando item dessa ocupação fica pronto, destaque reflete prontidão real sem iniciar preparo, criar entrega fictícia ou modificar o fluxo de produção.
- [x] **TS027-35** — Claim explícito bem-sucedido remove `Sem responsável` após confirmação/readback em ambos clientes, preserva pedidos, origem e filas; navegação, pedido e entrega sem claim não removem alerta.
- [x] **TS027-36** — Release, limpeza/geração nova, refresh/reconnect, concorrência de claim e isolamento de Venue não deixam alertas órfãos nem revelam dados operacionais a guest; texto acessível sem depender só de cor.

## Evidências exigidas para marcar PASS

- Teste de serviço e API para validação, permissões, idempotência, mesma chave/novo payload, relação Tab↔ocupação e semântica de release.
- Teste integrado em **PostgreSQL com duas conexões reais** para corrida start/start, claim/claim e release/open, verificando estados persistidos e audit events.
- Testes instrumentados Android / UI Web (Web: `npm run test:visual`, além de integração) com fixtures determinísticas, homônimos e interrupção do fluxo.
- Testes QR `DIRECT` com pedido não confirmado/confirmado/pronto, equipe sem responsável e com claim, múltiplos pedidos idempotentes, reload e próximo ciclo da mesa; inspecionar também o painel Agora e o limite de dados expostos a guest.
- Demonstração documentada no Railway isolado sem pagamentos reais e, depois, turno observado no piloto. Registrar versão do deploy e não confundir estimativa com medição.

## Refinamentos verificáveis

- [x] Venue começa desativado; somente venue.configure altera flag com versão, chave original e audit. Rollback conserva replay de start/open/claim confirmados.
- [x] MOVE_LOCATION pela mesa exige confirmação origem/destino e tab.move; não altera ledger/guest/owner.
- [x] Android global Nova comanda mantém alvo/medidas e texto sem clipping.
- [x] Carrinho Web e pedido desconhecido sobrevivem reload na Tab original, sem nova chave/payload e sem liberar contexto antes de reconciliação.
- [x] POST Android start e open realmente commitados com resposta perdida sobrevivem force-stop/offline e replay com exatamente um efeito SQL.
- [ ] Piloto no estabelecimento observado, com before/after real registrado separadamente do ensaio automatizado.

Os checks acima registram evidência técnica automatizada (API real/PostgreSQL, UI Web e emulador Android). Não significam piloto observado, demonstração Railway nova ou uso de aparelho/merchant real. Esses gates externos continuam pendentes.
