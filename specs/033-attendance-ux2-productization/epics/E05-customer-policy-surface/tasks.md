# E05 — Tarefas executáveis

**Owner:** Spec 002 e Spec 031 (PR #215). Não duplicar migration ou roteamento por Venue nesta epic.

- [ ] **E05-01 Gap atual:** verificar DTO financial_position e relação snapshot; mapear campos existentes em Web e Android (limite, saldo, capacidade, warning, consumo bloqueado). Não inferir capability pelo valor.
- [ ] **E05-02 Barra compacta:** componente nativo/Web equivalente: exposto o usado/limite e restante, faixa fina com 80%, rascunho listrado, zero e >100% com textos. Não tomar a primeira dobra nem adicionar toque obrigatório.
- [ ] **E05-03 Segurança do modo:** usar effective policy do servidor e version. Até a Spec 031 pronta, **mostrar ENFORCE existente**; não expor botão WARN_ONLY funcional que a API rejeitaria.
- [ ] **E05-04 Recovery:** em ENFORCE, mostrar pagamento parcial/gerência sem confundir limite com garantia; em WARN_ONLY, permitir Enviar sem modal apenas quando API permite; guardar draft em erro definitivo.
- [ ] **E05-05 R3 da Spec 031:** integrar feature/migration/settings/capabilities apenas após requisitos e PR próprios; validar dois Venues, client stale, versão alterada e PIN de gerente.
- [ ] **E05-06 Tests UI/a11y:** 320/360/390/430 e texto ampliado, progresso acessível 0..100/over, aviso sem bloquear CTA, sem garantir cartão.
- [ ] **E05-07 Gate:** AC-17..19 PASS; verificar que alterar relação do cliente não muda snapshot de Tab aberta e que texto de garantia só deriva de evento real.

**PRs sugeridas:** E05-a barra sob ENFORCE; E05-b integração Spec031 após backend feito. A Spec 031 continua dona de persistência/mode.
