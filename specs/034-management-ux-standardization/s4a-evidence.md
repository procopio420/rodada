# S4a — entrada do Cardápio e produtos

Em 2026-10-20, branch `codex/management-ux-alerts`, base HEAD `860b25d93da486d2416c6ddaccfdccd9605f8953`; alterações locais acumuladas, sem commit/push/publicação.

Recorte R2: destinos descritivos com nomes e descrições acessíveis; página de produtos com retorno à aba Cardápio e cabeçalho espaçado; ações adicionar/editar com 56 px, uma coluna no celular e duas no desktop. CSS local mantém o formulário de criação aberto em linha inteira. Handlers, permissões, polling e diálogos preservados. Variações ficam para o próximo recorte.

## Evidência executada

- Baseline determinística antes do código: 4 testes PASS.
- Build `next build --webpack`, typecheck e ESLint dos arquivos TSX/testes tocados: PASS.
- `test:visual management-menu-entry.spec.ts management-catalog-editor.spec.ts management-navigation.spec.ts`: 34 PASS em 53,8 s após correções.
- Primeira execução: 33 PASS e 1 FAIL; Link do Next duplicava fragmento no retorno. Mantido elemento HTML `a` original, preservando href. Teste de histórico/retorno passou no rerun.
- Inspeção dos pixels detectou sobreposição no cabeçalho inicial; grade e espaçamento locais corrigidos antes do rerun.
- 360/390/430/1280, axe/layout, CSS zoom 200%, abertura/Escape/restauração de foco e ausência de escrita no percurso de inspeção. Regressões existentes cobrem permissões, polling, rejeição de upload e criação com API interceptada.
- 20 PNG antes/depois e zoom, hashes de imagens e fontes em [evidências](../../docs/development/evidence/spec034-menu-entry/). Inspecionados depois 390, entrada390, 360zoom e desktop1280; sem corte nas ações.

Revisão do próprio autor R2; nenhuma alteração de auth/money/recovery. Suíte global não reexecutada e mantém falhas registradas anteriormente. CSS zoom não comprova zoom nativo; leitor de tela, dispositivos e homologação operacional pendentes. PASS local deste recorte; NO-GO para release/piloto da Spec034 sem gates restantes.
