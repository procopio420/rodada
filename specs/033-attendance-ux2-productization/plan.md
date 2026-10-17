# Plano de integração — Spec 033

## Regras de execução

1. Ler AGENTS.md, skills, KB, Specs 001/002/003/004/006/008/012/014/017/024/026/029 e 031 (branch PR #215) antes de tocar o código proprietário.
2. Comparar screenshot/contrato da PR #212 à main atual e registrar **delta**, não copiar código de HTML nem assumir que o draft ficou estável.
3. Uma pequena PR funcional por slice/epic, com testes e evidências. Evitar vários agentes editando order-workspace.tsx ou AttendanceScreen.kt simultaneamente; usar worktrees isoladas.
4. Fazer pilotos por Venue/role com feature flag apenas na apresentação/navegação; ações continuam nos mesmos endpoints canônicos. Compatibilidade e fallback UX existente são obrigatórios.
5. API/read-models compartilhados devem amadurecer antes de ativar deep links Android/Web; repetir mesmo tabId em rota não substitui autorização de Venue, Occupancy ou sessão.

## Ordem sugerida e paralelismo

- **Fase 0 (baseline, curta):** E06-01 inventário de contratos e evidências atuais, fixar SHA, jornada comparativa e aceites; reconciliar PR #212 com main. Sem refactor por reflexo.
- **Trilha A: E01 → E03.** E01 entrega navegação contextual e API de destinos; E03 acopla SERVICE/BILL/READY ao workspace certo, mantendo as filas e permissões existentes.
- **Trilha B: E02.** Reaproveitar useOrderIntent Web e persistência Keystore Android; é paralelizável com E01 após congelar contrato de Tab selection e refocus.
- **Trilha C: E04.** Revisar read models de saldo/Payment/CashShift/TableOccupancy e construir fechamento rápido sem mudar dinheiro; paralela à trilha A após congelar superfície do workspace.
- **Trilha D: E05.** Barra compacta e status atual podem ser feitos com ENFORCE já existente. Toggle de policy só após a Spec 031 (PR #215) implementada e homologada; nenhum bypass local.
- **Integração final: E06.** E2E Android + Web + API + Guest + Bar/Cozinha + Caixa, cenários offline/timeout, acessibilidade e teste de turno. Escalonar rollout só após revisão R3 e sinal verde humano.

## Release slices e PRs

| Slice | Dono | Dependência forte | Saída testável |
| --- | --- | --- | --- |
| 0.1 | E06 | nenhuma | matriz baseline/contratos/reutilização |
| 1.1 | E01 | 0.1 | navegação Web Mesas/Agora/Tab sem regressão |
| 1.2 | E01 | 1.1 | Compose Android com retorno e drafts estáveis |
| 2.1 | E02 | 0.1 | status de Order/OrderItem canônico no workspace Web |
| 2.2 | E02 | 2.1 | recuperação Android/Web e repetir sem duplo envio |
| 3.1 | E03 | 1.1 | destino autorizado de request e READY no backend |
| 3.2 | E03 | 3.1,1.2 | filas separadas + entrada contextual Web/Android |
| 4.1 | E04 | 0.1 | resumo financeiro, saldo parcial e close Web |
| 4.2 | E04 | 4.1,1.2 | pay/close/liberação Compose + ciclo de mesa |
| 5.1 | E05 | 0.1 | progress bar Web/Android sobre leitura real ENFORCE |
| 5.2 | E05 | PR #215 implementada | modo WARN_ONLY/ENFORCE por Venue efetivo |
| 6.1 | E06 | 1–5 pertinentes | matrizes automatizadas e visuais 360/390/430 |
| 6.2 | E06 | 6.1 | revisão, field-shift, feature rollout e GO explícito |

As estimativas/durações ainda são **não medidas**; somente dimensionar depois do inventário 0.1. Slices de E02/E04 que mexam em operações financeiras exigem revisão de idempotência/segurança e não podem ser considerados triviais.

## Regras de merge e rollout

- Não confundir **CI verde** com aceite Android/em bar. Completar ACs na spec e evidências por SHA.
- PRs de UX/design e docs permanecem distintas da implementação: #212 é conceito, #213 cobre Spec 032 e #215 cobre Spec 031.
- Qualquer mudança estrutural de contrato é feita no dono de domínio + ADR se durável; smoke de migração antes de flag.
- Bloqueio de deploy caso falte controle multitenant, intenção recuperável, saldo canônico, revogação de ocupação, autorização ou status real de produção.
- Rollback da apresentação mantém dados financeiros e pedidos históricos intactos. Ativação por Venue/role; não aplicar WARN_ONLY globalmente.

**Não iniciar implementação por esta PR documental.**
