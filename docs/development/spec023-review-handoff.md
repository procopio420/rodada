# Spec 023 — entrega para revisão

Ponto de entrada: branch `codex/spec023-review`, baseada em main `742faac`. Reúne V01–V05 e a correção de navegação Android com fonte ampliada. Código validado no commit `3c3f208`; commits posteriores deste fechamento documentam a publicação.

## Branches publicadas e verificadas

| Branch | Commit da entrega |
| --- | --- |
| codex/v01-kitchen-inventory | c909c93 |
| codex/v02-field-status-badge | 4c0b15d |
| codex/v03-kitchen-fixture | 570a832 |
| codex/v04-kitchen-tickets | aff8c67 |
| codex/v05-atendimento-shell | aeed2ec |
| codex/spec023-review | 3c3f208 (implementação integrada) |

Publicação autorizada explicitamente pelo usuário; os seis commits foram conferidos em origin. A branch original `codex/ux-operational-polish` permanece em `6e2f4ca`, igual ao remoto. Main permanece em `742faac`. Sem merge ou implantação.

Para revisar o conjunto, usar `codex/spec023-review`; não é necessário mesclar separadamente as cinco branches de origem. Os relatos históricos de ausência de publicação descrevem o momento de cada recorte e são preservados.

## Evidências e limites

[Relatório integrado](../design/spec023-review.md) e [manifesto de evidências](../design/evidence/spec023-review/sha256.json).

Web: typecheck/build aprovados, 160 testes visuais e 8 de realtime. Android: 38 unitários, build/lint aprovados e 12 execuções instrumentadas nas seis combinações de largura/fonte. Captura canônica preservada; 137 evidências históricas conferidas.

CI remoto será evidência separada no PR. Não se declara fidelidade total: tickets ainda divergem 16,6898% da referência; navegação canônica HTML/Android diverge 1,746%. API autenticada, dispositivo físico, API26, teclado e telas internas com fonte ampliada permanecem sem verificação nesta entrega.

Próximos recortes pequenos: header/safe areas com fixture de sessão; comparação de tipografia por região; posicionamento do aviso de conectividade da Cozinha. Atualizar contrato, plano, tarefas e aceite antes de alterar comportamento.
