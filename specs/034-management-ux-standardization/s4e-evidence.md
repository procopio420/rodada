# S4e — disponibilidade na Gerência

2026-10-20, branch `codex/management-ux-alerts`, base HEAD `860b25d93da486d2416c6ddaccfdccd9605f8953`; alterações locais acumuladas, sem commit/push/publicação.

Recorte R2 de apresentação: `managementLayout` opcional em CustomizationAvailability, ativado somente pelo editor da Gerência. Seção nomeada, nomes com quebra, linhas em uma coluna no celular e duas no desktop, ações44px. Default mantém classes anteriores usadas por production-board no Bar/Cozinha. Nenhuma mudança em state, pending, POST, payload/versão, callbacks, labels ou mensagens.

## Evidências

- Baseline4 PASS antes do código.
- Build webpack/typecheck PASS; ESLint do componente de disponibilidade e teste novo PASS. Lint herdado do editor principal permanece conforme S4b.
- Testes de disponibilidade nas quatro larguras: layout/axe e CSSzoom200%, duas ações opostas, payloads UNAVAILABLE/versão3 e AVAILABLE/versão2, ambas desabilitadas durante pending,403 e readback sem alteração otimista de estado.
- API interceptada: nenhuma alteração de disponibilidade real; integração de sucesso, concorrência/replay e operação real não comprovados por estes testes.
-12PNG antes/depois/zoom e hashes de imagens/fontes em [evidências](../../docs/development/evidence/spec034-customization-availability/). Inspeção antes/depois390, depois1280 e360zoom: ações dentro da seção e nomes completos; em ampliação palavras quebram em várias linhas. CSSzoom não comprova zoom nativo.
- Revisão do autor R2, handlers comparados ao HEAD e inalterados. Bar/Cozinha não exercitados manualmente neste recorte; opt-in preserva seu JSX/classes anteriores. Manual/leitor de tela, integração real e suíte global permanecem pendentes. NO-GO release/piloto global.

Próximo: S5 revisão conjunta da Gerência, navegação e estados; não abrir novos recortes sem achado concreto. Depois correções finais/documentação e gates pendentes.

Execução composta: test:visual management-customization-availability.spec.ts management-customization-forms.spec.ts management-customization-lists.spec.ts management-customization-entry.spec.ts —24 PASS51,3s. Diffcheck PASS.
