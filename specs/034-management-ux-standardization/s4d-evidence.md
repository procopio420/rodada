# S4d — formulários de configuração

2026-10-20, branch `codex/management-ux-alerts`, base HEAD `860b25d93da486d2416c6ddaccfdccd9605f8953`; alterações locais acumuladas, sem commit/push/publicação.

Recorte R2: formulário nomeado pelo título, fieldset Dados da configuração, ações responsivas e checkbox44px com quebra para ampliação. Preservados labels, limites, tipos, valores em centavos, disabled, handlers, payloads e mensagens. Sem alteração de persistência, auth ou regras de preços.

## Validação

- Baseline12 PASS antes do código.
- Build webpack e typecheck PASS; ESLint do novo teste PASS. Erro herdado de set-state-in-effect no componente permanece conforme S4b.
- `test:visual management-customization-forms.spec.ts management-customization-lists.spec.ts management-customization-entry.spec.ts`:20 PASS39,5s no rerun final.
- Primeira execução:12falhas nos alvos checkbox e8PASS; segunda:2falhas de overflow360zoom e18PASS. Corrigidos tamanho44px e quebra dos labels, sem relaxar testes.
- Três formulários em360/390/430/1280, axe/layout, CSSzoom200%, rascunho preservado, Máximo desabilitado em SINGLE/ativo emMULTI, prioridade do grupo desabilitada nos outros tipos e cancelamento sem escrita. API interceptada: não comprova integração real de gravação.
-36PNG antes/depois/zoom e hashes de imagens/fontes em [evidências](../../docs/development/evidence/spec034-customization-forms/). Inspecionados variação390, grupo390 e opção360zoom. Input de nome é uma linha e exibe texto parcial na ampliação; valor completo é preservado e verificado. CSSzoom não equivale a zoom nativo.
- Revisão do autor R2 e diffcheck PASS. Leitor de tela, zoom nativo, operação real e suíte global não executados; falhas anteriores mantidas. PASS local do recorte, NO-GO release/piloto global.

Próximo responsável: continuação S4e, seção de disponibilidade; ler contrato de disponibilidade antes de alterar UI e preservar handlers/recovery.
