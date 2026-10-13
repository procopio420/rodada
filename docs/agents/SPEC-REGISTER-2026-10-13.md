# Registro de specs e evidências — fotografia 13/10/2026

**Base da fotografia:** `main@60a95551bda27af2025c8da08b921e10f0fe1610`. **Escopo:** inventário estrutural de **30 diretórios de spec presentes na main**, mais acompanhamento de PRs relevantes. Não é uma matriz de aceite integral, não substitui `acceptance.md` nem afirma deploy. Para estado vivo, conferir GitHub no momento da execução.

## Regra de identificação

**Sempre use o caminho completo**. Números **021**, **022**, **024**, **025** aparecem duas vezes. O número isolado não identifica spec nem autoriza editar pasta errada. **027 ainda não integra esta fotografia da main**; a implementação proposta está no [PR #107](https://github.com/procopio420/rodada/pull/107).

## Inventário da main (sem inventar maturidade)

| Contrato por pasta | Capacidade | Estado comprovável nesta auditoria |
| --- | --- | --- |
| [`001-core-pos`](../../specs/001-core-pos/) | POS, venda, Tab/Order | Não revalidado neste snapshot |
| [`002-house-account`](../../specs/002-house-account/) | Conta da Casa | Não revalidado neste snapshot |
| [`003-dispatch`](../../specs/003-dispatch/) | Despacho operacional | Não revalidado neste snapshot |
| [`004-table-guest-ordering`](../../specs/004-table-guest-ordering/) | Mesa, ocupação e QR | Não revalidado neste snapshot |
| [`005-catalog-ai-icons`](../../specs/005-catalog-ai-icons/) | Catálogo, ícones IA | Não revalidado neste snapshot |
| [`006-payments-tap-on-phone`](../../specs/006-payments-tap-on-phone/) | Pagamentos/terminal | Sem homologação de provider real |
| [`007-management-cockpit`](../../specs/007-management-cockpit/) | Gerência | Não revalidado neste snapshot |
| [`008-staff-auth-roles-devices`](../../specs/008-staff-auth-roles-devices/) | Acesso e aparelhos | Não revalidado neste snapshot |
| [`009-tab-operations`](../../specs/009-tab-operations/) | Movimentos de comanda | Não revalidado neste snapshot |
| [`010-product-modifiers-variants`](../../specs/010-product-modifiers-variants/) | Modificadores | Não revalidado neste snapshot |
| [`011-pricing-discounts-service-charge`](../../specs/011-pricing-discounts-service-charge/) | Precificação | Não revalidado neste snapshot |
| [`012-cash-management`](../../specs/012-cash-management/) | Caixa | Não revalidado neste snapshot |
| [`013-venue-configuration`](../../specs/013-venue-configuration/) | Configuração Venue | Não revalidado neste snapshot |
| [`014-connectivity-degraded-operation`](../../specs/014-connectivity-degraded-operation/) | Conectividade | Não revalidado neste snapshot |
| [`015-receipts-printing-fallbacks`](../../specs/015-receipts-printing-fallbacks/) | Impressão | Não revalidado neste snapshot |
| [`016-covers-party-size`](../../specs/016-covers-party-size/) | Pessoas/ocupantes | Não revalidado neste snapshot |
| [`017-order-corrections-exceptions`](../../specs/017-order-corrections-exceptions/) | Correções | Não revalidado neste snapshot |
| [`018-notifications-operational-escalation`](../../specs/018-notifications-operational-escalation/) | Notificações | Não revalidado neste snapshot |
| [`019-specialized-surface-routing`](../../specs/019-specialized-surface-routing/) | Rotas por módulo | Não revalidado neste snapshot |
| [`020-web-operational-completion`](../../specs/020-web-operational-completion/) | Web operacional | Não revalidado neste snapshot |
| [`021-operational-ux-polish`](../../specs/021-operational-ux-polish/) | UX operacional | Não revalidado neste snapshot |
| [`021-prototype-design-integration`](../../specs/021-prototype-design-integration/) | Protótipos/visual | Não revalidado neste snapshot |
| [`022-full-product-implementation`](../../specs/022-full-product-implementation/) | Produto completo | Não revalidado neste snapshot |
| [`022-material-visual-fidelity`](../../specs/022-material-visual-fidelity/) | Fidelidade visual | Não revalidado neste snapshot |
| [`023-updated-prototype-visual-parity`](../../specs/023-updated-prototype-visual-parity/) | Paridade visual | PR #118 aberto; aceite global pendente |
| [`024-attendance-web`](../../specs/024-attendance-web/) | Atendimento Web | PR #118 cobre partes; aceites ainda não reconciliados |
| [`024-venue-menu-import`](../../specs/024-venue-menu-import/) | Importação de cardápio | PR #118 cobre partes; aceites ainda não reconciliados |
| [`025-pilot-cohesion-dev-tools`](../../specs/025-pilot-cohesion-dev-tools/) | Coesão/DevTools | Não revalidado neste snapshot |
| [`025-tenant-host-routing`](../../specs/025-tenant-host-routing/) | Hostname/Venue | Código na main (#116); aceite pendente |
| [`026-operational-ux-friction`](../../specs/026-operational-ux-friction/) | Fricção operacional | Contrato na main; PR #119 aberto |

**"Não revalidado" ≠ faltando implementação**. Afirmações de conclusão exigem evidência por critério e SHA; checklist marcando ou branch aberta não basta.

## Trilhas ativas e responsáveis de integração

| Frente | Situação no GitHub examinada em 13/10 | Próxima prova |
| --- | --- | --- |
| [025 host routing](../../specs/025-tenant-host-routing/) | PR [#116](https://github.com/procopio420/rodada/pull/116) mergeado, enquanto PR [#101](https://github.com/procopio420/rodada/pull/101) permanece aberto | Reconciliar código e branches, CI, dois Venues, TLS/preview e aceite independente de rollout |
| [026 operational UX](../../specs/026-operational-ux-friction/) | PR [#119](https://github.com/procopio420/rodada/pull/119) aberto | Casos de perda de resposta, readback, UX e integração no head final |
| 027 claim/contextual attendance (fora da main) | PR [#107](https://github.com/procopio420/rodada/pull/107) aberto | Rebase inteligente, QR-first e aceite host/tenant conforme código mergeado |
| [023 paridade](../../specs/023-updated-prototype-visual-parity/) e [024 Web](../../specs/024-attendance-web/) / [024 cardápio](../../specs/024-venue-menu-import/) | PR [#118](https://github.com/procopio420/rodada/pull/118) aberto | Critério a critério com Web/API/Android e teste de aparelho quando aplicável |
| [006 pagamentos](../../specs/006-payments-tap-on-phone/) | Integrações sem aceite real de provider/merchant no escopo Web-only | Não anunciar cartão/Tap integrado sem homologação |

## Evidência mínima antes de promover um status

Registrar `spec_path`, ID de critério, URL de PR/commit, `main_sha` ou `head_sha`, testes executados (comando, ambiente, quantidade e resultado), cenário negativo, migração/recovery quando pertinente e decisão de aceite com nome do responsável. Separar:

- **CONTRATO** — comportamento proposto; `spec.md` não demonstra implementação.
- **CODIFICADO** — alteração no head; PR aberto não é main nem release.
- **TESTADO** — comando executado e resultado persistido para SHA/ambiente.
- **CI** — workflows do SHA verificados e obrigatórios aprovados.
- **HOMOLOGADO** — operação real, hardware/rede/provedor/fiscal e aceite humano quando necessários.
- **EM PRODUÇÃO** — deployment identificado, URL/versão comprovadas e plano de rollback.

Cada promoção exige prova própria; não substituir `HOMOLOGADO` por `CI`. Não sobrescrever fotografias históricas. Consultar [procedimentos](PROCEDURES.md), [plano](IMPROVEMENT-PLAN.md) e [status da release](../releases/spec-status-2026-10-13.md).
