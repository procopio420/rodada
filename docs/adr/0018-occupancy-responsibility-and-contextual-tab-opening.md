# ADR 0018 — Responsabilidade da ocupação e abertura contextual de comanda

**Status:** Accepted; implementação em validação
**Date:** 2026-10-12
**Relates to:** Spec 027, Spec 004, Spec 009, Spec 008, ADR 0004, ADR 0009.

## Contexto

O Rodada separa mesa (Table), período de uso (TableOccupancy) e comanda (Tab). Na experiência atual, funcionários precisam ocupar mesa, associar Tab e entrar na Tab em operações distintas. "Claim" de uma tarefa de Dispatch não indica quem coordena a mesa. A identidade opcional e a possibilidade de múltiplas comandas devem permanecer.

## Decisão

1. **Ownership de serviço pertence à ocupação atual, não à mesa ou Tab.** `TableOccupancy.responsible_staff` nullable representa o responsável atual; `responsibility_version` e histórico auditável registram claim/transferência. QR DIRECT e ocupações antigas podem não ter responsável.
2. **Staff start = ocupação + responsável inicial**, atômicos e idempotentes, **sem abrir comanda automaticamente**. Só o criador staff de nova ocupação recebe responsabilidade inicial; funcionário que chega depois não a toma por navegação/pedido.
3. **Comanda contextual é um comando de domínio atômico** que cria `Tab` + `TabOccupancyAssignment`. Não compor duas APIs no cliente nem criar Tab fora da transação que registra seu destino.
4. **Claim não é uma trava de atendimento.** Staff autorizado pode abrir/selecionar Tab, pedir e auxiliar enquanto outro staff é responsável. Alterar owner é ação explícita versionada; ownership não substitui `confirmed_by`, `opened_by` ou `DispatchTask.claimed_by`.
5. **Uma ocupação ativa é única por mesa e generation.** Corridas retornam snapshot/409 com efeito zero ao perdedor; replays com mesma intent não repetem efeitos. Release/cleaning/guest revogação preservam o contrato da Spec 004.
6. **UI orientada à tarefa.** "Iniciar atendimento" → ficha da mesa → "Nova comanda" ou seleção de Tab → cardápio. O cliente não conhece o modelo interno. Web companion expõe apenas rotas operacionais.

## Alternativas rejeitadas

- `Table.waiter_id` permanente: transfere o responsável entre grupos/turnos por engano.
- `Tab.waiter_id` como dono da mesa: não representa um grupo com várias contas.
- Claim obrigatório para cada pedido: cria gargalo e impede colaboração no pico.
- Start automático com Tab anônima: gera comandas vazias e risco de duplicatas ao chegar uma segunda pessoa.
- Client fazer `POST tabs/` seguido de `POST assign/` sem transação: deixa Tab órfã e estado ambíguo na rede.
- Autoatribuir ao último operador: ownership varia por atividade lateral, sem escolha da equipe.

## Consequências

Requer campos nullable/versionados, comandos novos com idempotência persistida, sincronização com gateway Web, status de responsabilidade em Android/Web e testes concorrentes PostgreSQL. É mudança aditiva; specs existentes continuam proprietárias de dinheiro, QR, guest authorization, movimentação, caixa e dispatch. Até implementação e validação, este ADR **não declara comportamento existente** nem substitui as regras em produção.

## Contrato implementado em 13/10/2026

`ServiceCommand` retém chave, fingerprint do destino/payload e resultado sem expiração automática. Locks seguem intenção → Table → TableOccupancy → Tab; o registro da intenção impede a mesma chave concorrente em destinos diferentes de passar como outro comando. Mutations antigas de associação adotam Table antes de Occupancy. A auditoria alimenta a outbox transacional existente; o dispatcher publica somente registros confirmados.

Projeção staff é carregada em lote, considera pedidos GUEST confirmados dentro do intervalo do vínculo atual e itens pendentes, e exclui comandas encerradas da seleção ativa. Dados de ownership não entram no contexto guest. Ver `specs/027-table-service-claim/evidence.md` para resultados e gates ainda pendentes.

O rollout usa flag tipada no Venue, inicialmente false, sem backfill. Alterações gerenciais usam ServiceCommand (ação rollout), fingerprint, CAS e auditoria, com lock intenção → Venue; não travam mesas nem reescrevem visitas. Start/open/claim verificam a flag somente após procurar replay e validar o destino no Venue, admitindo conclusão de comandos já em voo durante rollback. Clientes leem a flag em GET de mesas e mantêm fluxo legado desligado. Carrinho Web é vinculado à sessão e salva payload original antes do POST; não libera intenção desconhecida em 401/403/5xx. MOVE_LOCATION permanece na Spec 009 e não passa pelo domínio de ownership.
