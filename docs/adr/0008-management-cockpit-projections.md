# ADR 0008 — Gerência usa projeções mobile-first e cockpit de exceções

**Status:** Accepted

## Contexto

O gerente de um bar/restaurante tende a acompanhar a operação em movimento e pelo celular. Um dashboard desktop-first cheio de gráficos reduz utilidade justamente durante o pico.

Ao mesmo tempo, as métricas do Rodada atravessam vários domínios: Ordering, Fulfillment, Dispatch, Floor, Catalog, Billing, Payments e Cash. Consultar todos esses módulos com joins analíticos a cada abertura da home criaria acoplamento, latência e risco de inconsistência semântica.

## Decisão

1. **Rodada Gerência é mobile-first**, com baseline 360–430 px.
2. Durante o serviço, sua home é um **cockpit de exceções**, não um dashboard de BI.
3. Fora do pico, a mesma superfície prioriza fechamento, analytics e planejamento.
4. Gerência lê **projeções/read models derivados de fatos persistidos** dos módulos canônicos.
5. PostgreSQL continua fonte de verdade; Redis/WebSocket apenas acelera atualização.
6. Projeções devem ser idempotentes e reconstruíveis.
7. Números financeiros continuam derivados do ledger e confirmações canônicas.
8. Milestones inferidos preservam `source`/`confidence`; analytics não pode convertê-los em observação certa.
9. O dia de gestão usa **business date/cutoff configurável**, não simplesmente meia-noite.
10. Métricas individuais de equipe servem para diagnóstico, não para leaderboard simplista.

## Consequências

### Positivas

- home rápida no celular;
- alertas aparecem sem navegação profunda;
- histórico e realtime compartilham definições;
- relatórios não precisam executar queries pesadas sobre todo o domínio;
- reprocessamento permite corrigir bugs de projeção sem alterar fatos originais;
- desktop pode oferecer mais densidade sem redesenhar a arquitetura de informação.

### Custos

- exige contratos claros de eventos/fatos;
- exige versionamento/rebuild de projeções;
- consistência de analytics pode ser eventual;
- cada métrica precisa de definição canônica e teste.

## Não decidido aqui

- data warehouse externo;
- ferramenta de BI;
- IA generativa para insights;
- CMV/margem sem fonte de custo;
- forecasting automático.

Esses itens exigem necessidade real e specs próprias.
