# Web

Target: Next.js responsive/PWA, mobile-first e staff-first.

Superfícies conceituais:

```text
/staff      PDV, Tabs, pedidos, mesas
/bar        produção + disponibilidade + quick add dos itens da estação
/kitchen    produção + disponibilidade + quick add dos itens da estação
/dispatch   tarefas, claims e runs
/guest      QR/PWA do cliente
/owner      visão gerencial, configuração e métricas
```

Não duplicar regras de domínio por superfície.

Exemplo: ao marcar Fritas como indisponível em `/kitchen`, `/staff` e `/guest` devem refletir a mesma `ProductAvailability`. A API ainda revalida no submit para cobrir tela/carrinho stale.

Bar/Cozinha também possuem **+ Item**. O fluxo rápido herda a estação, pede nome + preço e permite gerar o ícone por IA. A tela nunca espera a imagem para salvar o Product; usa placeholder/estado de geração e atualiza quando o asset estiver pronto.

Primeira interface deve funcionar bem em celular Android, com botões grandes e fluxo rápido.

O protótipo sem backend está em `prototype/`.
