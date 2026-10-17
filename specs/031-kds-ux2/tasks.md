# Spec 031 — Tarefas de execução

**Estado:** todas **pendentes**. Checklist de trabalho futuro; não significa que funcionalidade foi implementada no produto. Referência: [spec.md](spec.md), [plan.md](plan.md), [acceptance.md](acceptance.md).

## Trilha A — Contract & baseline

- [ ] **KDS-01** Inventariar `ProductionBoard`/CSS rotas Bar/Cozinha, `OrderItem`, Dispatch, Availability, Correction, eventos SSE e snapshots; adicionar mapa “já existe / gap / conflito / simulado”.
- [ ] **KDS-02** Construir fixture isolada: FG84 (só Bar), duas comandas numa mesa, mistura Bar+Cozinha, 2 burgers com customizações distintas, alergia, 3 bebidas/cancelar 1, lote e 30 pedidos.
- [ ] **KDS-03** Congelar evidência visual/teclado “antes” no mesmo SHA/viewport/test data; definir replay determinístico com relógio controlado.
- [ ] **KDS-04** Resolver decisão de contrato de READY direto, partial ready, AllergyHold e expedition/filtro canônico com os owners da API antes de ativar ações.

## Trilha B — UX/IA/responsividade

- [ ] **KDS-05** Implementar cabeçalho e navegação ``Pedidos / Passe / Resumo por produto / Ajustes``; retirar controles de simulação da rota real, esconder acesso não autorizado.
- [ ] **KDS-06** Tickets por Order com linhas por Item/configuração, destino reconhecível, código ficha, status, 1 CTA, menu contextual acessível.
- [ ] **KDS-07** Fila estável, indicadores NOVO/ATRASADO/PRIORIDADE/ALTERAÇÃO; timer sem rerender integral e sem “saltos”.
- [ ] **KDS-08** CSS real 360/390/430, 768/850/1024, 1280/1440/1920, retrato/paisagem, safe-area e modo leitura à distância.
- [ ] **KDS-09** Foco após mutação, rolagem preservada, modais trap/return focus, teclado/TalkBack, fontes 200%, redução de movimento e labels sem color-only.

## Trilha C — Operação e expedição

- [ ] **KDS-10** Aviso de novo ticket/alteração em todas as regiões, navegação ao pedido certo, status de visto persistido sem perder alteração pendente.
- [ ] **KDS-11** Passe pronto recente + antigo “sem retirada registrada”, sem inferir entrega; ação opcional de pickup e prova de estado canônico.
- [ ] **KDS-12** Expedição opt-in mostra status cruzado Bar/Cozinha, próxima ação e abre Passe filtrado pelo ID do pedido; suporta prontos antigos e múltiplas Tabs.
- [ ] **KDS-13** Resumo por produto apenas consultivo, sem fusão perigosa de variantes, estações, alergias ou statuses.
- [ ] **KDS-14** Verificar que no modo ficha não entra comida e FG84 não dá acesso/autorização à Tab.

## Trilha D — Segurança, domínio e exceções

- [ ] **KDS-15** Conectar notificação/revisão de alteração aos eventos canônicos sem atualizar OrderItem antes da resolução.
- [ ] **KDS-16** Cancelar 1 de N com motivo e autorização por estágio/pagamento; testar pendente, aprovado, recusado e concorrência.
- [ ] **KDS-17** Refeitura/replacement via novo item vinculado, com auditação e efeitos financeiros legítimos.
- [ ] **KDS-18** Descrever, aprovar e implementar AllergyHold/escalation/resume com permissões e trilha persistida; impedir batch e ready enquanto suspenso.
- [ ] **KDS-19** Migrar CTAs de pronto direto somente para comandos aceitos pela API; se não resolvido, manter ação explícita segura de PREPARING.
- [ ] **KDS-20** Contrato de pronto parcial por unidade, quando aprovado, com Dispatch, histórico e idempotência; não “inventar” contadores locais.
- [ ] **KDS-21** Lote READY compatível e atômico (ADR 0018): snapshot fingerprint, versões, rejeição total, replay/readback.
- [ ] **KDS-22** Disponibilidade canônica, impressão efetiva/fallback, preferências de densidade/som e limiares sob política de Venue.

## Trilha E — Resiliência, testes e aceite

- [ ] **KDS-23** API SSE desconectada, API indisponível, stale/frescor, ACK perdido, retomada com mesma chave, logout e troca de Venue.
- [ ] **KDS-24** Testes Web: unit/component, Playwright, `npm run test:visual`, screenshots antes/depois e acessibilidade; não substituir baseline para “ficar verde”.
- [ ] **KDS-25** Testes API: autorização, consistência de quantities, lotes, replay, concorrência, DB/Dispatch e correções financeiras.
- [ ] **KDS-26** Stress de 30+ pedidos nas três telas; nenhuma perda de foco/scroll, ticket desaparecido, duplicação ou ação em item errado.
- [ ] **KDS-27** Testes com operadores reais e hardware de bancada; registrar gravações/observações consentidas, sem afirmar métricas sem dados.
- [ ] **KDS-28** Revisão independente, feature flag, runbook rollback, aceites rastreáveis e release separado após autorização.

### Regras para o executor

- **Não implementar diretamente a simulação HTML** como fonte de estado canônico.
- Evitar PR único gigante. Cada PR referencia IDs KDS e AC; estado de execução só muda com evidência.
- Ao decidir contrato em KDS-04, atualizar primeiro `spec.md`/`acceptance.md` e ADR quando necessário.
- Não abrir issues novas por padrão: usar este checklist e a issue existente que vier a ser indicada.
