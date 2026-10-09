# Plano de execução — Rodada demonstrável até sexta-feira à noite

**Janela:** quinta-feira, **08/10/2026** → sexta-feira, **09/10/2026**, período da noite (**America/Sao_Paulo**).
**Status:** plano de execução, **não** declaração de conclusão.
**Base auditada:** `main` em `5458e5e4e235d63efea07e3cd1f92152201bb517` em 08/10/2026.
**Dono do objetivo:** coordenação de integração; cada frente tem agente/PR próprio.
**Planos de referência:** [Spec 022](../../specs/022-full-product-implementation/spec.md), [roadmap técnico](technical-roadmap.md), [plano longo](full-product-implementation-plan.md), [Spec 023](../../specs/023-updated-prototype-visual-parity/spec.md).

> **META INEGOCIÁVEL PARA 09/10 À NOITE:** uma **demo operacional integrada e repetível**, executada sobre API e dados persistidos reais em ambiente de teste, mostrando um turno reduzido do Bar do Aderlan sem erros críticos, falsos estados de pagamento ou passos manuais escondidos. **Não é** homologação de produção nem autorização para desligar o VRSystem.
>
> **Regra de priorização:** primeiro fazer o caminho ponta a ponta funcionar e ser demonstrável; depois acrescentar funcionalidades que não coloquem esse caminho em risco. Testes e reconciliação têm precedência sobre expandir escopo.

## 1. Resultado verificável que queremos demonstrar amanhã

**Fluxo obrigatório (P0, a demo é NO-GO se não passar):**

1. Inicializar stack local documentada, com **PostgreSQL**, migrations e dados de teste identificados; abrir Atendimento Android, Bar/Cozinha Web, Caixa e Gerência.
2. Autenticar operador autorizado pelo **Venue + PIN** em aparelho BYOD, sem aprovação manual de telefone pessoal; registrar qual ambiente e usuário de teste foram utilizados.
3. Abrir **Tab anônima**, localizar/criar outra Tab e associar opcionalmente a uma ocupação, preservando `Tab ≠ Table`.
4. Lançar um pedido com pelo menos um produto do Bar e um da Cozinha; confirmar pela API, com preço em centavos, histórico e Charge **uma única vez**.
5. Ver o pedido nas filas corretas; executar transições reais de preparo/pronto, indisponibilizar item e comprovar que um novo pedido inválido é rejeitado pelo servidor.
6. Acompanhar o estado atualizado nas superfícies: **SSE se integrado e aprovado**; caso contrário, polling/revalidação existentes com atraso conhecido e status de desatualização explícito. Não afirmar realtime concluído quando for polling.
7. Abrir a Tab, demonstrar saldo/exposição e cobrar **parcialmente** com método de teste/manual corretamente identificado (dinheiro ou terminal externo); receber restante e fechar a Tab. Somente usar Pix integrado com PSP real se credenciais, contrato e confirmação estiverem de fato disponíveis; simulação nunca vira dinheiro recebido.
8. Mostrar em Gerência/relatório/caixa a operação registrada e reconciliar manualmente **Charge − Payment − Refund/Adjustment = saldo** em centavos.
9. Demonstrar **ao menos uma exceção real:** limite da Conta da Casa bloqueando consumo, correção/estorno permitido ou conflito/retry idempotente. Permissões indevidas devem ser negadas.
10. Repetir o fluxo após reiniciar os clientes; não depender de requests fictícias, prints estáticos ou ajustes SQL manuais para declarar sucesso.

**Demonstração adicional desejável, não bloqueadora:** cliente QR pede e recupera histórico após reload; duas comandas em mesma ocupação; split/merge de comanda não paga; variantes/modificadores; atualização imediata por SSE; visuais aprimorados. Uma falha nesses itens vira dívida explícita, não motivo para falsificar a demo básica.

**Critérios negativos (NO-GO ainda que a interface pareça boa):** pedido duplicado após retry; cobrança duplicada; pagamento simulado apresentado como confirmado; alteração de saldo sem ledger canônico; acesso cross-Venue/guest indevido; item indisponível aceito; crash na jornada principal; divergência monetária não explicada; testes essenciais vermelhos; dependência de API mockada para o happy path.

## 2. Estado verdadeiro de partida (não inferir conclusão de checkbox)

**Já disponível na `main`:**
- Núcleo Core POS, pedidos/OrderItems, ledger, pagamento parcial/manual, produção Bar/Cozinha, QR guest, permissões, caixa/estornos e House Account com bloqueio de exposição; casos existentes têm testes, mas **não** significam produto 100% homologado.
- Operações de Tab com transferência, split/merge e auditoria: [PR #47](https://github.com/procopio420/rodada/pull/47), incorporado.
- Adapters Pix Paytime e SumUp e fluxo Android com teste/simulação: [PR #48](https://github.com/procopio420/rodada/pull/48) e [PR #49](https://github.com/procopio420/rodada/pull/49), incorporados; **não há comprovação de ativação do merchant, Pix liquidado nem Tap privado rodando em produção**.
- Fluxos Web adicionais (catálogo básico, histórico guest, relatório/CSV e histórico de caixa): [PR #43](https://github.com/procopio420/rodada/pull/43), incorporado; Web ainda faz polling em pontos operacionais.
- Protótipos e nova fundação visual: [PR #51](https://github.com/procopio420/rodada/pull/51), incorporado; **paridade visual integral ainda pendente**.

**PRs abertos verificados em 08/10 (revalidar antes de agir):**
- [#44 — pesquisa VR System](https://github.com/procopio420/rodada/pull/44): documentação, não prova de quais módulos o Aderlan usa.
- [#45 — polimento Web/Android](https://github.com/procopio420/rodada/pull/45): potencial sobreposição com #51; **não fazer merge sem reconciliar mudanças e CI**.
- [#46 — Quick Catalog + ícones IA](https://github.com/procopio420/rodada/pull/46): parte de catálogo já existe na main; comparar delta efetivo, migrações, dependências e conflitos antes de merge. Ícones de IA **não** bloqueiam demo.

**Lacunas relevantes ainda não demonstradas como concluídas na `main`:**
- `010` variantes/modificadores; `011` pricing/descontos/serviço; `014` SSE/outbox/replay; `015` impressão/fallback; `018` alertas; restante de `013` configuração e `007` cockpit. Não alegar que trabalho solicitado a agentes já está mergeado.
- Live Tap on Phone: **bloqueado por SDK/acesso privado, credenciais, ativação e homologação**. Pix live também exige contrato/provedor e testes reais.

## 3. Ações em ordem estrita, com dono por frente e entregável

| Ordem / prioridade | Frente responsável | Próxima ação concreta | Evidência e condição de conclusão | Dependência |
| --- | --- | --- | --- | --- |
| **0 — P0** | **Integração/coordenação** | Criar uma branch de integração derivada da `main` atual; revisar os PRs #44/#45/#46, conflitos e duplicação; preservar migrações e contratos. Atualizar quadro de PRs. | Branch compila; deltas únicos identificados; nenhum merge cego de visual ou catálogo | Imediato |
| **1 — P0** | **Integração + QA** | Congelar o roteiro acima como fixture de **turno reduzido** (2 estações + Android + Caixa + Gerência) em PostgreSQL; executar uma primeira vez na `main` antes das próximas features. | Relatório por passo com PASS/FAIL, SHA, ambiente, comandos e screenshots/logs saneados | 0 |
| **2 — P0** | **Agente 014 (runtime)** | Implementar outbox+SSE com cursor/replay, autenticação por Venue/guest, revalidação de gaps e fallback; integrar às superfícies sem reescrever o domínio. | Pedido confirmado aparece nos clients sem refresh; reconnect não perde fato; falha de stream não bloqueia API. Se incompleto, manter polling seguro e sinalizar limitação | Contratos de API existentes; coordenação de arquivos |
| **3 — P0** | **Agente 010 (customização)** | Completar variantes/modificadores com snapshot de preço, validação server-side e exibição nas filas, **sem quebrar produto simples**. | Teste E2E Android/guest → API → cozinha com adicional pago; pedido simples original segue íntegro | Catalog/ordering vigentes; coordenar com 005 |
| **4 — P0** | **Integração/QA** | Rebase/cherry-pick seletivo dos PRs prontos com CI, migrations e revisão; executar o turno reduzido novamente após cada merge sensível. | API, Web, Android e PostgreSQL verdes no SHA integrado; nenhuma regressão de saldo/produção | 1; novos PRs aprovados |
| **5 — P1** | **Agente 011 (pricing)** | Implementar corte mínimo testável de desconto/cortesia/taxa apenas após estabilizar ledger e variantes; aprovação e rateio em centavos. | Preview, persistência e testes de idempotência, parcial e autorização; não bloquear P0 se não houver PR seguro | 3 + finanças existentes |
| **6 — P1** | **Agente 015 (impressão)** | Documentos de conta/produção derivados, fila PrintJob idempotente e reimpressão; iniciar por impressão digital/fallback se hardware não disponível. | Documento correto/versão; falha de impressora não afeta pedido/pagamento | 4; hardware opcional |
| **7 — P1** | **Gerência/configuração (007/013)** | Corrigir somente bloqueadores da demo: seed, perfis, catálogo, relatórios/CSV, histórico de caixa e configurações mínimas sem SQL durante demonstração. | Operador consegue conduzir roteiro com permissões certas; relatório confere com ledger | 1 e 4 |
| **8 — P2** | **Produto/research (003/004/016/017/018/022/023)** | Usar resultado do PR #44 e entrevistas para selecionar gaps realmente usados pelo Aderlan; terminar visual pixel-perfect e recursos avançados depois do gate P0. | Backlog reordenado com evidência de uso; nenhuma feature especulativa no caminho crítico | Após demo |

**Responsabilidade de arquivos:** pagamento `payment_provider/` + Android `payments/`; catálogo `catalog/` + QuickCatalog; Tab `tab_operations/`; tempo real em módulo/clients isolados; variantes em domínio próprio com integrações mínimas no `ordering/`; pricing em serviços financeiros próprios; impressão em novo módulo. Arquivos transversais (URLs, modelos comuns, migrations, app roots, design tokens e `production-board`) são ponto de integração **serializado pela coordenação**; agentes não devem rebasear uns sobre worktrees sujas ou sobrescrever a mesma alteração simultaneamente.

**Specs são fonte de intenção:** modificar a spec/ADR de domínio quando comportamento mudar; um PR termina só quando código, testes e critérios de aceite condizem. Não criar uma spec 024 só para recontar o plano de 001–023.

## 4. Agenda de execução

| Janela | Decisão/resultado esperado |
| --- | --- |
| **Quinta 08/10 — restante da noite** | Triagem #44/#45/#46; checkout/seed; teste do fluxo P0 na main; registrar bloqueios reproduzíveis; contratos mínimos entre 010 e 014. |
| **Sexta 09/10 — manhã** | Agentes fecham slices mínimos 010 e 014; integrações em PRs pequenos; QA reexecuta erros críticos e testes PostgreSQL. Preparar ambiente demonstrável. |
| **Sexta 09/10 — tarde** | **Feature freeze** no candidato de demo: não adicionar novas features ou refatorações visuais. Integrar apenas PRs aprovados; corrigir P0, executar checks e teste de turno em ambiente descartável. |
| **Sexta 09/10 — noite** | Rodar a demo do item 1 **sem improvisos**; registrar resultados, limitações e recomendação GO/NO-GO para **demo supervisionada**. Se não passou, mostrar exatamente o fluxo que passou e listar as falhas. |

Não prometer homologação de provedor, hardware físico ou operação integral em um dia. A cadência acima é **alvo**, não garantia de entrega assíncrona.

## 5. Gates verificáveis antes de dizer “funciona”

### G0 — Build e integridade
- [ ] `main`/branch candidato identificada pelo SHA; todas as migrations aplicáveis em banco descartável e `makemigrations --check --dry-run` sem drift.
- [ ] API `pytest` + `manage.py check`, com testes PostgreSQL para concorrência/ledger (não confundir passes em SQLite com prova de locks).
- [ ] Web `npm run typecheck`, `npm run build`, `npm run test:visual`, `npm run test:integration` com API real.
- [ ] Android `./gradlew testDebugUnitTest assembleDebug`; lint e smoke no emulador/aparelho conforme ambiente disponível.
- [ ] PRs revisados sem conflitos silenciosos; nenhuma mudança em credenciais/segredos para tornar demo possível.

### G1 — Turno reduzido ponta a ponta
- [ ] Android staff entra, abre Tab e confirma pedido com Bar + Cozinha; endpoint real persiste Orders/Charges e role/capability é exigida.
- [ ] Filas mostram apenas itens/estações corretos, estado muda corretamente, falta de produto é bloqueada na API.
- [ ] Conta da Casa aplica limite ou política existente sem contornar autorização.
- [ ] Pagamento parcial/manual de **teste** altera ledger exatamente uma vez; saldo e fechamento conciliam em centavos.
- [ ] Guest QR (se apresentado) respeita autorização e recupera pedidos; caixa e Gerência mostram os mesmos fatos canônicos.
- [ ] Retry, timeout ou operação repetida não duplicam order/charge/payment.

### G2 — Resiliência e comunicação honesta
- [ ] Derrubar apenas SSE/polling não interrompe HTTP saudável; UI marca snapshot antigo e revalida.
- [ ] Se SSE foi entregue, reconectar após perda de eventos e revogar sessão são cenários testados; caso contrário, nomear o polling como fallback, **não** tempo real concluído.
- [ ] Pagamento simulado fica identificado; `CONFIRMATION_PENDING` não conta como recebido, não aciona tentativa cega nem permite fechar com saldo incompatível.
- [ ] A demonstração pode ser repetida após restart de clients usando dados de teste persistidos sem reiniciar manualmente a história financeira.

**Definições de resultado:**
- **GO — DEMO:** G0+G1 integralmente aprovados; G2 aprovado para os transportes/métodos efetivamente exibidos; evidência anexada.
- **GO CONDICIONAL — DEMO COM LIMITES:** caminho básico real comprovado, mas funcionalidades adicionais ausentes; listar claramente o que **não** mostrar e os fallbacks honestos.
- **NO-GO — DEMO:** qualquer regra financeira/isolamento/acesso falhou, integração quebra o caminho principal ou só funciona com mocks.
- **NO-GO — SUBSTITUIR VRSYSTEM:** até testes físicos no bar, conciliação de turno paralelo, rollback, acesso/homologação de pagamento aplicável e verificação das obrigações fiscais/operacionais. “Não usamos fiscal no sistema” ainda precisa ser confirmado com o estabelecimento/contador.

## 6. Comandos de referência e evidência exigida

Validar e adaptar à máquina/CI conforme [API README](../../apps/api/README.md), [Web README](../../apps/web/README.md) e [Android README](../../apps/attendance-android/README.md):

```bash
# API, após instalar dependências e configurar ambiente de teste
cd apps/api
python manage.py check --settings=rodada_api.settings_test
python manage.py makemigrations --check --dry-run --settings=rodada_api.settings_test
pytest

# Web, após instalar dependências e browser de teste
cd apps/web
npm run typecheck
npm run build
npm run test:visual
npm run test:integration

# Android
cd apps/attendance-android
./gradlew testDebugUnitTest assembleDebug lintDebug
```

**Obrigatório:** reexecutar casos sensíveis em PostgreSQL; o caminho de SQLite rápido não comprova concorrência. Guardar logs com redaction, resultado de testes, SHA, ambiente, print das superfícies e balanço esperado/real. Não anexar PIN, bearer token, credenciais, dados de cliente ou secrets.

Salvar a evidência de amanhã em `docs/development/demo-evidence-2026-10-09.md` (criar **somente ao executar**; não marcar sucesso antecipadamente) com:

- SHA de origem e SHA candidato; PRs integrados e descartados, responsáveis por cada decisão.
- Versões de API/Web/Android/DB, ambiente e se houve dispositivo físico.
- Tabela dos passos 1–10: `PASS / FAIL / NOT_RUN`, evidência, causa e workaround permitido.
- Resultados dos testes por suíte e distinção SQLite/PostgreSQL.
- Pagamentos: `MANUAL_TEST / SIMULATED / SANDBOX_CONFIRMED / LIVE_CONFIRMED` por caso, sem confundir status.
- Bug list com severidade/reprodução; recomendação final de demo e separadamente de cutover.

## 7. Pós-demo — execução sem inventar nova prioridade

Após o gate de amanhã: fechar `011` e `015` se não concluídas; depois `013` configuração sem SQL, `007` dashboard/projeções e `018` alertas; aprofundar `004` mapa/guest, `003` dispatch, `017` corrections e `016` covers segundo observação real e [pesquisa VR](https://github.com/procopio420/rodada/pull/44). `023` fecha paridade visual sem fingir 0,1% para telas não equivalentes; `022` continua plano integrador até todos os gates de produto.

**Reconciliação de checklists é tarefa explícita:** `005` e `009` continuam com tarefas desmarcadas apesar de código/PRs; `007` tem trabalho parcial com tasks não atualizadas; `001` e `012` também podem ter divergências entre lista e implementação. Para cada item, relacionar `código + teste + critério` e marcar apenas evidência real; não calcular percentuais falsos usando somente `[x]`.

**Primeira ação do próximo agente:** ler este plano e a `main` atual, identificar um P0 verificável do item 3, implementá-lo numa branch isolada, executar os testes correspondentes e abrir PR pequeno. **Próxima ação da coordenação:** rodar G0/G1 da main e integrar somente o que melhora o resultado de sexta-feira.

## 8. Anexo — panorama das 23 specs na main em 08/10

**Esta tabela indica código/resultado conhecido, não percentual de tarefas:** cada spec já possui `spec.md`, `plan.md`, `tasks.md` e `acceptance.md`; marque tarefas apenas depois de relacionar implementação, teste e critério.

| Spec | Estado interpretado | Próxima ação |
| --- | --- | --- |
| [001](../../specs/001-core-pos/spec.md) | Parcial / base funcional | Revalidar turno completo e integração |
| [002](../../specs/002-house-account/spec.md) | Checklist completo; código com testes | Garantir limites/overrides na demo |
| [003](../../specs/003-dispatch/spec.md) | Parcial | Runs, SLA e provenance após demo |
| [004](../../specs/004-table-guest-ordering/spec.md) | Parcial | Mapa/identificadores e UX depois do P0 |
| [005](../../specs/005-catalog-ai-icons/spec.md) | Catálogo básico entregue; PR #46 aberto | Conciliar ícones/worker; IA não bloqueia |
| [006](../../specs/006-payments-tap-on-phone/spec.md) | Adapters Pix e simulação; live bloqueado | Homologar PSP/SDK, Guest e realtime financeiro |
| [007](../../specs/007-management-cockpit/spec.md) | Dashboard/relatórios parciais | Projeções, fechamento, métricas e alertas |
| [008](../../specs/008-staff-auth-roles-devices/spec.md) | Base avançada | Completar smoke BYOD/revogação |
| [009](../../specs/009-tab-operations/spec.md) | Implementação principal mergeada (#47) | Auditar checklist/testes e UX de conflitos |
| [010](../../specs/010-product-modifiers-variants/spec.md) | Especificada, não comprovada na main | Implementar como frente prioritária |
| [011](../../specs/011-pricing-discounts-service-charge/spec.md) | Reversões pontuais; motor pendente | Pricing e taxa após gate P0 |
| [012](../../specs/012-cash-management/spec.md) | Operacional parcialmente | Integrar UX/contingência e fechamento |
| [013](../../specs/013-venue-configuration/spec.md) | Parcial (ex.: calendário); centralização pendente | Configuração do Venue sem SQL |
| [014](../../specs/014-connectivity-degraded-operation/spec.md) | Especificada; SSE/outbox pendente | Frente prioritária; fallback honesto |
| [015](../../specs/015-receipts-printing-fallbacks/spec.md) | Especificada, implementação pendente | PrintJob/documentos, não bloquear demo sem hardware |
| [016](../../specs/016-covers-party-size/spec.md) | Especificada, implementação pendente | Após campo validar importância |
| [017](../../specs/017-order-corrections-exceptions/spec.md) | Cancelamento/estorno parciais | Remake e replacement com auditoria |
| [018](../../specs/018-notifications-operational-escalation/spec.md) | Especificada, implementação pendente | Após runtime e cockpit |
| [019](../../specs/019-specialized-surface-routing/spec.md) | Checklist completo | Regressão de hosts/superfícies |
| [020](../../specs/020-web-operational-completion/spec.md) | Checklist completo (#43) | Regressão com features novas |
| [021](../../specs/021-prototype-design-integration/spec.md) | Checklist completo (#51) | Preservar visual atual em integrações |
| [022](../../specs/022-full-product-implementation/spec.md) | Plano integrador, não entrega | Continuar após demo |
| [023](../../specs/023-updated-prototype-visual-parity/spec.md) | Paridade integral pendente | Gates visuais sem bloquear fluxo P0 |

**Atenção:** PRs de agentes podem alterar este panorama durante a execução. Reavaliar o HEAD antes de usar a matriz como relatório de andamento; **planejamento não prova entrega**.
