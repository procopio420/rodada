# S4c — listas de variações e grupos

2026-10-20. Branch `codex/management-ux-alerts`, HEAD base `860b25d93da486d2416c6ddaccfdccd9605f8953`; alterações acumuladas locais, sem commit/push/publicação.

Recorte R2: regiões Variações e Grupos de opções, linhas em uma coluna no celular e duas no desktop, grupos delimitados e ações com alvo mínimo44px. Nomes longos quebram sem deslocar botões para fora da tela. Preservadas expressões monetárias, flags, intervalos, ordem, todos os handlers e disabled. Formulários e disponibilidade não alterados.

## Evidências

- Baseline4 PASS antes do código.
- Build webpack/typecheck PASS; ESLint do novo teste PASS. Erro herdado do componente já reproduzido em S4b permanece; não foi suprimido nem corrigido neste recorte.
- `test:visual management-customization-lists.spec.ts management-customization-entry.spec.ts`:8 PASS16,5s.
- Quatro larguras360/390/430/1280, axe/layout e CSSzoom200%; flags e valores1250/250 preservados; editar variação/grupo/opção abre o nome correto e cancelar não envia escrita. API interceptada, sem prova de integração real.
-12PNG antes/depois/zoom, hashes de imagens e fontes em [evidências](../../docs/development/evidence/spec034-customization-lists/). Inspeção antes/depois390, depois1280 e360zoom: corrigido overflow anterior no nome longo do grupo. CSSzoom amplia apenas a seção de configuração; seletor nativo pode truncar texto. Disponibilidade ainda usa layout anterior e será tratada separadamente.
- Revisão do autor R2 e diffcheck PASS. Zoom nativo, leitor de tela, operador e suíte global não executados; falhas globais anteriores continuam pendentes. PASS local do recorte; NO-GO release/piloto global.

Próximo responsável: continuação S4d, formulário de variação/grupo/opção; inventariar contratos e capturar baseline antes de editar.
