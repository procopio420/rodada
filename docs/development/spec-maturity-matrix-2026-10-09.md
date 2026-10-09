# Rodada — Matriz de maturidade das especificações

**Data da fotografia:** 09/10/2026 (America/Sao_Paulo)  
**Repositório:** `procopio420/rodada`  
**Base verificada:** `main` em `7227f7d36` (merge do PR #60).  
**Natureza:** avaliação **preliminar** de maturidade técnica e pendências — **não é um termo de aceite, percentual de implementação nem homologação para produção**.

## Como ler os estados

| Estado | Significado |
| --- | --- |
| **Pronta** | Recorte contratado tem implementação e/ou tarefas declaradas concluídas, sem lacuna funcional relevante identificada nesta revisão. Exige validação transversal antes de virar aceite formal. |
| **Quase pronta** | Implementação substancialmente entregue, com poucas lacunas residuais ou evidências específicas por fechar. |
| **Avançada** | Fluxo principal implementado, mas integrações, UX, recovery, hardware, fornecedor ou parte material dos critérios continuam pendentes. |
| **Parcial** | Há base funcional, porém faltam fluxos significativos do contrato original. |
| **Pendente** | Implementação completa do contrato não foi evidenciada; a spec pode ter estrutura parcial já existente. |

> **Atenção:** as checklists de `tasks.md` não são evidência suficiente de conclusão. Existem itens desmarcados cujo código já existe e itens marcados que ainda exigem aceite/homologação. Antes de fechar uma spec, cruzar `spec.md`, `acceptance.md`, implementação, teste e evidência com SHA/ambiente.

## Resumo

| Estado | Frentes |
| --- | ---: |
| Pronta | **7** |
| Quase pronta | **3** |
| Avançada | **6** |
| Parcial | **7** |
| Pendente | **2** |
| **Total** | **25** |

São **23 números de especificação (001–023)**, mas **25 frentes documentadas**, pois 021 e 022 possuem dois recortes cada. Os números refletem uma classificação qualitativa de maturidade, não uma contagem de aceites comprovados.

## Matriz completa

| Spec | Área | Maturidade | Principal lacuna / ação de fechamento |
| --- | --- | --- | --- |
| [001](../../specs/001-core-pos/) | Core POS | **Avançada** | Reconciliar checklist legado com implementações atuais, matriz de critérios e smoke integrado. |
| [002](../../specs/002-house-account/) | Conta da Casa | **Pronta** | Validar novamente invariantes, limites, override e integração do release. |
| [003](../../specs/003-dispatch/) | Dispatch | **Parcial** | Inferência conservadora, provenance/correção, coordenação avançada e automação sem exigir taps manuais. |
| [004](../../specs/004-table-guest-ordering/) | Mesas e Guest | **Parcial** | FloorPlan/placements, identificadores, fluxos de salão e recovery mais completo. |
| [005](../../specs/005-catalog-ai-icons/) | Catálogo e ícones IA | **Quase pronta** | Validação com geração real: legibilidade em tamanho pequeno, sem textos/logos e contrato visual. |
| [006](../../specs/006-payments-tap-on-phone/) | Pagamentos / Tap on Phone | **Avançada** | Acesso a SDK privado, credenciais de merchant, homologação e Pix/Tap reais; testes simulados não provam liquidação. |
| [007](../../specs/007-management-cockpit/) | Cockpit gerencial | **Parcial** | Projeções consistentes, painel de exceções, alertas, métricas e fechamento/analítica completa. |
| [008](../../specs/008-staff-auth-roles-devices/) | Auth, Roles e Devices | **Quase pronta** | Completar testes BYOD, revogação e fluxos nativos em aparelho. |
| [009](../../specs/009-tab-operations/) | Operações de comanda | **Avançada** | Jornadas Web/caixa, conflitos, histórico/provenance e detalhes de identificadores. |
| [010](../../specs/010-product-modifiers-variants/) | Modificadores e variantes | **Quase pronta** | Analytics de mix e validação final ponta a ponta; núcleo de ordering já avançado. |
| [011](../../specs/011-pricing-discounts-service-charge/) | Pricing, descontos e serviço | **Pronta** | Reexecutar regressão integrada de ledger, rateio e relatórios após merge do PR #60. |
| [012](../../specs/012-cash-management/) | Gestão de caixa | **Parcial** | Cobertura completa de jornadas, conferência, divergências, UX e aceite de operação real. |
| [013](../../specs/013-venue-configuration/) | Configuração do estabelecimento | **Parcial** | Gestão tipada, mudanças seguras/versionadas, onboarding e interfaces administrativas completas. |
| [014](../../specs/014-connectivity-degraded-operation/) | Realtime e operação degradada | **Avançada** | SSE/outbox/replay existem; completar reconciliação offline, intents e testes de falha/capacidade. |
| [015](../../specs/015-receipts-printing-fallbacks/) | Recibos e impressão | **Avançada** | Provar impressão em hardware real, fallback e contratos específicos; emissão fiscal fora do escopo atual. |
| [016](../../specs/016-covers-party-size/) | Covers / número de pessoas | **Pendente** | Observações auditáveis de quantidade, API, UX, concorrência, provenance e analytics. |
| [017](../../specs/017-order-corrections-exceptions/) | Correções e exceções | **Parcial** | Completar preview, remake/replacement, autorização contextual e interfaces integradas. |
| [018](../../specs/018-notifications-operational-escalation/) | Alertas e escalonamento | **Pendente** | Motor de alertas: regras, dedupe, cooldown, ack/resolução, escalonamento, push e histórico. |
| [019](../../specs/019-specialized-surface-routing/) | Superfícies especializadas | **Pronta** | Recorte entregue; manter validação de rotas, autenticação e navegação nos domínios canônicos. |
| [020](../../specs/020-web-operational-completion/) | Web operacional | **Pronta** | Recorte entregue; executar novamente testes E2E e integrações reais. |
| [021A](../../specs/021-operational-ux-polish/) | UX operacional | **Pronta** | Recorte de polimento entregue; não equivale à paridade visual integral da 023. |
| [021B](../../specs/021-prototype-design-integration/) | Integração de protótipos | **Pronta** | Integração inicial entregue; fidelidade total é responsabilidade da 023. |
| [022A](../../specs/022-full-product-implementation/) | Produto completo | **Parcial** | Fechar R01–R18 por evidência e gates G0–G4, incluindo segurança, carga, pilotos e homologação. |
| [022B](../../specs/022-material-visual-fidelity/) | Fidelidade visual material | **Pronta** | Recorte específico entregue, sem declarar pixel-perfect completo. |
| [023](../../specs/023-updated-prototype-visual-parity/) | Paridade visual atualizada | **Avançada** | Concluir V01–V07 globalmente; divergências documentadas e matriz Android/device/acessibilidade ainda abertas. |

## Priorização sugerida

### Implementação de maior impacto

1. **016 — Covers**, **018 — Alertas**, **013 — Configuração**, **007 — Cockpit**: entregar os domínios e jornadas ausentes com testes por critério de aceite.
2. **003 — Dispatch** e **004 — Mesas/Guest**: fechar diferenças entre o fluxo operacional real do bar e o contrato planejado.
3. **012 — Caixa** e **017 — Correções**: fechar exceções que podem acontecer durante um turno, antes de aceitar o piloto.
4. **009/014/023**: concluir UX, resiliência, recovery e qualidade visual sem regressões financeiras ou operacionais.
5. **001/002/005/008/010/011/015/019/020/021/022B**: revalidar o que já existe, sem reimplementar funcionalidades maduras.

### Bloqueios externos e gates de release

- **Pagamentos (006):** acesso e aprovação comercial/merchant, credenciais, SDK Tap privado, testes de sandbox e dispositivo NFC físico; confirmação real de Pix, estorno e liquidação.
- **Impressão (015):** levantamento e teste com impressoras/OS/driver usados no Bar do Aderlan.
- **Piloto:** medir uso em pico, autorização entre estabelecimentos, concorrência financeira em PostgreSQL, perda de rede, restart, restore e plano de rollback.
- **Fiscal:** emissão fiscal não faz parte automaticamente do escopo aceito; demanda decisão e integração separadas.

## Evidência exigida para encerrar cada critério

Para cada critério de `acceptance.md`, registrar:

- `PASS`, `PARTIAL`, `MISSING`, `EXTERNAL_BLOCKED` ou `OUT_OF_SCOPE`;
- arquivo/rota do código e PR/commit da `main`;
- teste reproduzível, resultado, SHA e ambiente;
- falhas, skips, comportamento degradado e dependências;
- próximo passo e responsável quando não for `PASS`.

**Não converter automaticamente o rótulo `Pronta` desta matriz em `PASS` de todos os critérios.**

## Estado de release comprovado até esta fotografia

A [evidência de demo de 09/10](demo-evidence-2026-10-09.md) reporta **GO condicional para demo local supervisionada com pagamentos manuais/de teste**, incluindo turno com serviços reais e PostgreSQL. Isso **não** certifica liquidação via adquirente, Pix real, Tap on Phone, aparelhos/impressoras físicas, implantação em produção ou substituição do VR System.

Fontes relacionadas:

- [Spec 022 — critérios de aceite](../../specs/022-full-product-implementation/acceptance.md)
- [Spec 023 — critérios de aceite](../../specs/023-updated-prototype-visual-parity/acceptance.md)
- [Plano de produto completo](../architecture/full-product-implementation-plan.md)
- [Readiness da demo](../architecture/2026-10-09-demo-readiness.md)
- [Prontidão dos provedores de pagamento](../payments/provider-readiness-2026-10-09.md)
- [Revisão visual 023](../design/spec023-review.md)

**Próxima atualização:** substituir esta classificação qualitativa pela matriz verificável por *critério de aceite*, sem alterar histórico ou mascarar lacunas.
