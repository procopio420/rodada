# Epic E06 — Validação integrada e release do Atendimento 2.0

**Prioridade P0 gate transversal**, não uma feature adicional. Dono: QA/E2E + Android/Web + API + piloto. **Não publicar até o GO operacional.**

## Baseline antes de executar

- Inventariar issue #106 (suites full-shift), Spec 026/029 (já implementado versus evidência stale), Specs 001/003/004/006/012/014, PRs #212 (conceito), #213 (QR/FG84), #215 (modo limite).
- Fixar SHA de main, flag/venue e versão do app Android; registrar o que é operacional hoje. Não inferir aceitação a partir de prints do protótipo isolado.
- Definir tarefas humanas por persona: garçom com 20 mesas, bartender, cozinha, caixa, gerente, cliente QR. Medir turnos calmo/pico.

## Gates e métricas

G0 — Observabilidade: medir passos essenciais e tempos da UX 2.0 para pedido→confirmação, confirmação→Bar/Cozinha, troca de Tab, resposta incerta, conta→fechamento e última Tab→mesa AVAILABLE. Não exigir comparação com UX legada. Dados medidos ≠ estimados.

G1 — Segurança/CI: autenticação, isolamento Venue, Tab vs Table, ledger, idempotência, retriable uncertainty, autorização de manager, replay, acessos Guest e QR epoch. PostgreSQL real e suite existente #106.

G2 — UX Web/Android: telas 360/390/430 + desktop; Compose no emulator e pelo menos um aparelho físico; teclado, TalkBack, fonte ampliada, foco/Escape/Back, scroll, landscape quando suportado, carga de 50 tasks. Capturas e relatórios anexados por commit SHA.

G3 — Integração ponta a ponta: Staff cria/abre Tab, confirma Order, Bar/Cozinha muda estados, serviço/entrega, cliente pede conta, pagamento parcial e integral autorizado, close, release, limpeza, nova ocupação. Perda de ACK depois do commit não duplica nem cobra duas vezes.

G4 — Campo e release: UX 2.0 padrão para todos os tenants, sem flag de apresentação ou retorno à UX antiga. Verificar capacidades e políticas canônicas por Venue/role, observabilidade e reversão técnica segura de deploy/migrações, preservando ledger/histórico. R3 review independente de auth, finanças, isolamento e decisões do servidor. Piloto do bar dá GO humano.

## Telemetria mínima

- Distâncias eventuais e tempo quando houver evidência: QR/chamado→ação, staff intent→Order confirmed, Order confirmed→production received, READY→destino (provenance), pedido conta→close, Tab CLOSED→release, DIRTY→AVAILABLE.
- Erros/latências/idempotency conflict/multiple-attempts/falhas e recuperação. Não contabilizar inferência como entrega confirmada.
- Não rastrear GPS indoor, performance pessoal contínua do garçom nem adicionar taps instrumentais.

## Fora de escopo
Deploy automático da documentação, gate substituído por protótipo, algoritmo de rotas, alterar modo de consumo global e homologar PSP só por smoke.

## Aceite
AC-20..24 da matriz geral. Sem “100% DONE” se produção não rodou, testes foram skipped ou Android físico não validado.
