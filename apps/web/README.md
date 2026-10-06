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

Bar/Cozinha também possuem **+ Item**. O campo de nome é autocomplete do catálogo: resultados existentes mostram o mesmo ProductIcon, preço, estação e disponibilidade. Selecionar um resultado reutiliza o Product; se não existir correspondência exata, aparece **Criar "{nome}"** e a confirmação faz resolve-or-create automaticamente.

Para Product novo, a estação vem do contexto e o preço é informado no fluxo rápido. Não existe botão "Gerar ícone": Product + ProductIcon nascem juntos, a geração começa automaticamente e a tela usa placeholder até o asset ficar pronto.

Primeira interface deve funcionar bem em celular Android, com botões grandes e fluxo rápido.

O protótipo sem backend está em `prototype/`.
