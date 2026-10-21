# S4b — entrada de variações e adicionais

2026-10-20, branch `codex/management-ux-alerts`, base HEAD `860b25d93da486d2416c6ddaccfdccd9605f8953`, alterações locais sem commit/push/publicação.

Recorte R2 de apresentação: cabeçalho espaçado com retorno explícito à aba Cardápio, link de edição de nomes com alvo44px e seletor em seção nomeada com ajuda acessível. Preservados aviso sobre centavos/histórico, carregamento, mensagens, select/onChange/disabled e todos os formulários/comandos. CSS local, sem mudança de preços/auth/recovery.

## Validação

- Baseline:4 testes PASS antes do código.
- Build webpack e typecheck PASS.
- Visual: `management-customization-entry.spec.ts management-menu-entry.spec.ts management-navigation.spec.ts`:26 PASS49,5s.
- Novo teste ESLint PASS. Componente:FAIL herdado `react-hooks/set-state-in-effect` linha27; reproduzido por ESLint do arquivo em HEAD na linha25. Não suprimido.
- Quatro larguras360/390/430/1280, axe/layout e CSSzoom200%; seleção de produto, abertura de rascunho e limpeza ao desmarcar, sem escrita na API. Consultas de customização interceptadas: isso não comprova integração real.
-12PNG antes/depois/zoom e hashes de imagens/fontes em [evidências](../../docs/development/evidence/spec034-customization-entry/). Inspeção antes/depois390, depois1280 e360zoom. Em CSSzoom200%, título quebra em várias linhas e select nativo exibe texto parcial; sem overflow de página. Zoom nativo/leitor de tela e homologação operacional pendentes.
- Revisão do autor R2, diffcheck PASS. Suíte global não repetida e falhas anteriores continuam pendentes. PASS local do recorte; NO-GO release/piloto global.

Próximo:S4c listas de variações e grupos, depois formulários. Não marcar toda a página concluída.
