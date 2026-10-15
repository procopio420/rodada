# Critérios e evidência

## Aceite Android nativo (port posterior)
- [x] Entrada unificada, busca/filtros e Outras comandas; permissões preservadas.
- [x] Cardápio/Pedido atual/Conta separados; saldo exclui draft e histórico usa API.
- [x] A/B/A preserva configurações/linhas; sessão divergente não herda draft.
- [ ] Leitura negada mantém alvo anterior (inspeção feita; falta ensaio HTTP negativo específico do port).
- [x] Navegar não envia pedidos/pagamentos; A/B/A real não alterou pedidos canônicos.
- [x] Guardas locais de intenção ambígua; payload/UUID/recovery preservados por reutilização e inspeção. Queda real de POST não reexecutada nesta slice.
- [x] Back real, indisponíveis, 360/390/430dp e fonte 200% nos cenários automatizados.
- [ ] Personalização com IME/TalkBack e comparação global antes/depois ainda requerem ensaio específico.
- [x] Build/JVM/lint/Compose e revisão independente registrados em [android-evidence.md](android-evidence.md).

## Web — evidência histórica
- [x] Mesas: grade, estados com texto, busca/filtro combinados e vazio contextual.
- [x] Abrir mesa/comanda mantém navegação e ações existentes.
- [x] Cardápio: ícone, preço, seleção visível; indisponíveis continuam bloqueados.
- [x] Quantidades, observações e rascunho por comanda preservados nos cenários testados.
- [x] Atalhos com foco e resumo do pedido sem encobrir controles.
- [x] Conta: preço histórico ou ausência explícita, subtotal e saldo canônico.
- [x] 360/390/430 e desktop sem overflow, alvos 44px e axe sem violações nos novos cenários.
- [x] Typecheck, lint pertinente, auth, build e testes visuais executados (resultados abaixo).

Sem homologação de operação real, Android ou produção. Nenhum merge/push/deploy autorizado.
PRs abertos consultados via conector GitHub: #158 (diretrizes UX em revisão),
#155 (Spec 028 impressão) e #118 (aceites 023/024). Não foram integrados.

## Execução local — 2026-10-14

Base `bbaa14799d832c60b3c2404f0e34e70f387512b1` + diff local da branch
`codex/ux-teste-mobile`. Detalhes de autoria/limites: [evidence.md](evidence.md).

| Verificação executada em apps/web | Resultado |
| --- | --- |
| `node node_modules/typescript/bin/tsc --noEmit` | PASS |
| `node node_modules/next/dist/bin/next build` | PASS, inclusive build final |
| `node --experimental-strip-types --test tests/session-refresh.test.mjs` | 4 PASS |
| ESLint dos testes alterados, AttendanceDraft e página Attendance | PASS |
| ESLint attendance-web + order-workspace | FAIL: 2 erros/2 warnings, iguais ao conteúdo de HEAD verificado por stdin |
| Playwright: mobile-design, catalog, draft, tables-mobile, dialogs | 23 PASS, 39,8s |
| Playwright mobile-design após ajuste final de largura dos filtros | 10 PASS, 19,0s |
| Playwright completo `test --workers=4` | 515 PASS / 28 FAIL, 8,8 min; execução anterior aos últimos refinamentos de saldo/falha inicial |
| `git diff --check` | PASS |

O completo foi executado até o fim. As 28 falhas estão em attendance/ocupação (1),
order-intent (5), tab-drafts/atendimento (3), tab-location-move (12) e table-entry (7).
Há roteiros que procuram “Abrir”, identificação opcional antiga e ações de mesa
recolhidas ou rótulos de movimento anteriores. Não foram removidos nem enfraquecidos.
Isso não equivale a baseline runtime integral verificada: o conjunto permanece FAIL.
Relatório completo preservado em `apps/web/playwright-report/index.html`, traces em
`apps/web/test-results/visual/`; rodada focada em `apps/web/test-results/ux-mobile-final/`.

## Pendências
- Comparação com capturas de antes: não concluída, conforme evidence.md.
- Reconciliar os testes legados que falharam e obter o gate completo verde.
- Integração real API/PostgreSQL, CI do futuro commit e avaliação com garçom/dispositivo:
  não executadas nesta slice. Não há medição real de redução de toques/tempo.
- Revisão independente não executada; coordenar sobreposição documental com PR #158.

Status: IMPLEMENTADO / TESTADO_LOCAL para o experimento Web. NO-GO para release.

## Revisão unificada após rebase — 2026-10-14

Esta fotografia substitui a navegação separada do primeiro experimento. Branch
`codex/ux-teste-mobile` sobre `origin/main@47043184408c090ddae33df17d4d72010603f764`,
com alterações locais restauradas e sem conflito Git pendente.

- [x] Mesas/Contas unificadas; entrada por mesa e acesso a outras comandas.
- [x] Criação contextual em mesa livre/ocupada; mesma chave/corpo após resposta perdida.
- [x] Popup grande com catálogo, revisão e conta separados; contexto/resumo visíveis.
- [x] Quantidade e personalização junto do produto; diminuir esgotado sem permitir envio.
- [x] Fechar/reabrir e A/B/A preservam drafts; seleção de Tab nova não descarta draft anterior.
- [x] Leitura negada mantém destino anterior; erro fica visível na superfície correta.
- [x] Escape, foco de origem e diálogos filhos de edição/descarte/histórico validados.
- [x] ACK perdido bloqueia saída; reload e retry usam o mesmo payload/chave e Tab.
- [x] Flag contextual desligada conserva criação sem mesa; capability ausente não expõe criação.
- [x] Chromium 360/390/430/1280: sem overflow de documento, controles >=44px e axe nos cenários novos.

Comandos equivalentes aos scripts de package.json, executados em apps/web:

| Verificação | Resultado atual |
| --- | --- |
| TypeScript `tsc --noEmit` e Next `build` | PASS |
| `playwright test attendance-mobile-design.spec.ts pos-repeat-order.spec.ts customization.spec.ts --workers=2` | **33 PASS**, 27,9s |
| Testes de sessão/refresh | **4 PASS** |
| ESLint ActionDialog/OrderWorkspace/AttendanceCatalogCard/teste do experimento | PASS |
| `git diff --check` | PASS |

Ajuste final do ícone de histórico para não estreitar o conteúdo: build PASS;
4 jornadas 360/390/430/1280 revalidadas, incluindo botão Voltar 100% dentro do
viewport e auditoria axe/controles. Sem nova alteração funcional após os 33 PASS.

Capturas reais: `apps/web/visual-artifacts/029/unified/`; traces da rodada final:
`apps/web/test-results/ux-unified-final/`. Referências da primeira proposta foram
preservadas em `before-unified/`; suas fixtures iniciais não são idênticas a todas
as novas fixtures de múltiplas comandas, portanto não há gate pixel-perfect global.

Os resultados 515/28 anteriores continuam históricos, anteriores à main nova e ao
fluxo unificado; não são resultado desta revisão. Suíte visual integral legada
não reexecutada nesta rodada e precisa migrar os roteiros de navegação Contas.
Integração real PostgreSQL, fonte/zoom 200%, IME, leitor de tela e validação com
garçom não executados. Não declarar homologação nem redução medida de tempo/toques.
