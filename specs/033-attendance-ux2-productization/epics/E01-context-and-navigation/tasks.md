# E01 — Tarefas executáveis

**Dependência:** baseline E06-01. **Write set inicial:** apps/web/components/attendance-web.tsx, order-workspace.tsx, apps/attendance-android UI e DTO/API de seleção autorizada, se comprovadamente necessário. Evitar conflito com E02 no order-workspace.

- [ ] **E01-01 Inventário:** comparar main atual, Spec 024/026/029 e PR #212 em screenshots e contratos; listar funções existentes, estados já cobertos e o que falta. Saída: matriz before/after e owner por arquivo.
- [ ] **E01-02 Identidade segura:** especificar destino typed StaffTaskTarget/TabSelection baseado no endpoint real, sem confiar em destination_label. Testar Venue incorreto, generation inválida, revogação, Tab CLOSED e role sem leitura.
- [ ] **E01-03 Web Agora e Mesas:** consolidar navegação no shell existente sem desmontar OrderWorkspace nem reiniciar useOrderIntent; contadores e seleção de Tab preservados, tab sem mesa pesquisável.
- [ ] **E01-04 Seleção sem cliques redundantes:** mesa ocupada com uma ou várias Tabs, seleção explícita da Tab; + Pedir dentro da Tab abre catálogo; + Pedir sem seleção pede contexto; criação rápida por diálogo, nunca formulário sempre aberto.
- [ ] **E01-05 Port nativo Compose:** mesmas jornadas sem WebView; integrar estado de navegação ao state holder/ViewModel já existente; Back não perde sessão/intent/draft.
- [ ] **E01-06 Deep links e retorno:** originator task/mesa/Tab preservado; após pedido, conta ou retorno, focar Tab/mesa correspondente; erro de destino stale mostra ação para reabrir lista, sem mutar o registro.
- [ ] **E01-07 Tests Web e Android:** testes A→B→A, modo balcão, multi-Tab, ocupação nova/antiga, 403/404/409, concorrência de seleção; Web focus/keyboard + Compose back.
- [ ] **E01-08 Gate:** capturas 360/390/430 e emulador nativo, suite CI, reviewer de tenancy/auth. Concluir apenas com AC-01/02/03 PASS.

**PRs pequenos:** 1) contratos mínimos, 2) Web, 3) Compose (pode paralelizar após congelar DTO). **Não** criar uma nova entidade financeira para a mesa.
