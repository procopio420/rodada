# Acceptance — Spec 027: início de atendimento e claim de ocupação

**Estado:** proposta ainda não implementada. Todos os critérios permanecem pendentes até haver arquivo de teste, execução e evidência vinculada. IDs TS027-01..TS027-30.

## Início da mesa e responsabilidade

- [ ] **TS027-01** — Dada mesa AVAILABLE, quando staff com `table.manage` toca "Iniciar atendimento", há exatamente uma TableOccupancy nova, mesa fica OCCUPIED e funcionário autenticado vira responsável sem formulário obrigatório.
- [ ] **TS027-02** — O start staff não cria Tab, Order, Customer, Payment, GuestSession, party-size nem lançamentos no ledger.
- [ ] **TS027-03** — Ao confirmar start, a ficha mostra mesa, área, "Em uso", "Atendimento: você", zero comandas e "Nova comanda".
- [ ] **TS027-04** — Cliente em `DIRECT` que inicia mesa via QR cria/recupera ocupação sem responsável; staff pode reivindicar depois sem recriar a ocupação ou revogar a guest session.
- [ ] **TS027-05** — Fechar a última Tab nunca libera a mesa nem retira sua responsabilidade automaticamente.
- [ ] **TS027-06** — Mesa DIRTY, CLEANING e OUT_OF_SERVICE não pode iniciar; servidor retorna estado, UI oferece ação compatível sem pular limpeza.
- [ ] **TS027-07** — Mesa OCCUPIED não aceita outro start como nova ocupação ou takeover implícito; UI mostra contexto atual e ações seguras.

## Comandas vinculadas e pedido

- [ ] **TS027-08** — Da ocupação ativa, "Nova comanda" exige apenas confirmação e nome opcional; associa Tab + ocupação atômica e abre cardápio com Mesa/Tab corretas.
- [ ] **TS027-09** — Se associação falha, Tab nova e efeitos relacionados são revertidos; não há Tab órfã por race.
- [ ] **TS027-10** — A ocupação comporta duas ou mais Tabs com pagamentos/exposições independentes.
- [ ] **TS027-11** — Comandas aparecem como ações clicáveis na mesa e abrem imediatamente a Tab selecionada no Android/Web.
- [ ] **TS027-12** — Homônimos e comandas anônimas são desambiguados por contexto de exibição não secreto; ação mantém Tab ID correto, sem resolver por nome.
- [ ] **TS027-13** — Uma Tab já vinculada à outra ocupação não é associada cegamente; UI mostra mover comanda e API rejeita attach indevido.
- [ ] **TS027-14** — Pedido em Tab de mesa usa destino da ocupação atual e `Order.confirmed_by` do ator; não altera responsável.
- [ ] **TS027-15** — Abertura de Tab sem mesa/balcão segue permitida sem criar ocupação fictícia.
- [ ] **TS027-16** — Seleção de outra mesa/comanda não descarta draft pendente silenciosamente; resultado incerto de pedido não permite nova intent indistinta.

## Ownership / claim

- [ ] **TS027-17** — Claim sem responsável, com versão correta, atribui ator e registra evento único.
- [ ] **TS027-18** — Takeover de colega exige ação explicitamente rotulada com identificação do responsável existente; server atualiza versão + audita de/para.
- [ ] **TS027-19** — Mesmo garçom pode receber pedido em mesa assumida por colega sem claim, sem bloqueio e sem trocar responsável.
- [ ] **TS027-20** — Dois claims concorrentes com mesma versão geram uma transferência e um 409 RESPONSIBILITY_CONFLICT, sem overwrite silencioso.
- [ ] **TS027-21** — Claim de mesmo funcionário responsável é no-op auditável sem alterar versão de responsabilidade.
- [ ] **TS027-22** — Usuário sem sessão/capability ou de outro Venue não inicia/assume/abre comanda na ocupação e não obtém dados de staff de outro Venue.

## Consistência, rede e ciclo de vida

- [ ] **TS027-23** — Start concorrente por dois funcionários em PostgreSQL gera exatamente uma ocupação e só um responsável inicial; perdedor vê snapshot existente.
- [ ] **TS027-24** — Mesmo `idempotency_key` + fingerprint repete resposta/IDs sem novos efeitos; mesma chave com payload divergente produz 409.
- [ ] **TS027-25** — Timeout após commit, reload Web, kill/restart Android e retry não duplicam ocupação, claim, Tab nem eventos; o resultado desconhecido é exibido como verificação, não sucesso.
- [ ] **TS027-26** — `release_table` concorrente a `tabs/open` termina em Tab vinculada antes do release **ou** rollback integral do open; sem Tab órfã.
- [ ] **TS027-27** — Liberar mesa não fecha Tabs, revoga autorizações guest pertinentes e inicia DIRTY; limpeza preserva fluxo/geração da Spec 004; owner não vaza para próxima ocupação.
- [ ] **TS027-28** — SSE/outbox publica somente após commit; Android/Web se atualizam a partir de leitura canônica, sem confirmação prematura.
- [ ] **TS027-29** — Android/Web usam o mesmo contrato; gateway Web não expõe dinheiro/estorno/caixa, nem retorna informação de owner para guest.
- [ ] **TS027-30** — Em Android real e Web móvel 360–430px, primeira ocupação requer 1 toque, comanda da mesa é clicável, CTAs têm alvos acessíveis e textos de estado/error comunicam intenção e destino.

## Evidências exigidas para marcar PASS

- Teste de serviço e API para validação, permissões, idempotência, mesma chave/novo payload, relação Tab↔ocupação e semântica de release.
- Teste integrado em **PostgreSQL com duas conexões reais** para corrida start/start, claim/claim e release/open, verificando estados persistidos e audit events.
- Testes instrumentados Android / UI Web (Web: `npm run test:visual`, além de integração) com fixtures determinísticas, homônimos e interrupção do fluxo.
- Demonstração documentada no Railway isolado sem pagamentos reais e, depois, turno observado no piloto. Registrar versão do deploy e não confundir estimativa com medição.
