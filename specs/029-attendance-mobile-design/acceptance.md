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

## Filtros sem rolagem lateral — 2026-10-15

Base: codex/ux-teste-mobile, HEAD 54c57808cec0098be2934faa964dd6dd9cd5b41d + diff local.
- Grade de duas colunas no celular e tres a partir de 768px; rotulos completos,
  contagens, foco e selecao preservados; sem faixa de rolagem horizontal.
- Next build (inclui TypeScript): PASS.
- Gate test:visual focado em attendance-mobile-design.spec.ts: 15 PASS, 20,6s.
  Executado pelo CLI Playwright equivalente ao script, com portas isoladas.
  Inclui 360/390/430/1280, ausencia de overflow nos filtros, seis botoes com
  alvo >=44px e sem texto cortado, alem das jornadas/auditoria axe existentes.
- Navegador real: grade confirmada; Disponivel mostrou vazio correto e Todas
  restaurou as mesas. Captura local ignorada em
  visual-artifacts/android-native-port/web-filters-final.png.
- Sem mudanca de regras, API ou Android. Suite visual integral nao reexecutada;
  resultados acima sao do recorte pertinente, nao aprovacao global/release.

## Filtros removidos por solicitacao — 2026-10-15

Substitui a decisao da grade acima. Atendimento Web conserva apenas busca por
mesa/comanda; estado continua visivel em cada mesa. Estado React/CSS dos filtros
removidos; vazio agora orienta ajustar a busca. Android nao alterado.
Next build/TypeScript PASS; test:visual focado attendance-mobile-design.spec.ts:
15 PASS (19,7s), incluindo busca/vazio, ausencia dos filtros e quatro larguras.
Navegador real atualizado e sem filtros. git diff --check PASS. Suite integral
nao reexecutada. Sem commit/push/merge/deploy.

## Mesa em popup — 2026-10-15

Base: codex/ux-teste-mobile @ 54c57808cec0098be2934faa964dd6dd9cd5b41d + diff local.
Selecionar mesa abre ActionDialog com estado, comandas e acoes; a grade nao expande.
Voltar/Escape restaura foco. Workspace da comanda abre sobre a janela contextual;
fechar retorna a ela. Mensagens da mesa ficam na camada visivel. Bloqueios e
confirmacoes existentes preservados. Android/API/dominio nao alterados.
Next build/TypeScript PASS; test:visual focado attendance-mobile-design.spec.ts:
16 PASS (20,7s), incluindo quatro larguras, axe nas jornadas existentes, foco,
geometria da grade, leitura negada, filhos e ACK perdido. Primeira rodada: 14 PASS,
2 FAIL (alerta duplicado e roteiro que tentava trocar mesa sem fechar modal);
alerta corrigido e roteiro adaptado a nova sequencia, sem reduzir asserts.
git diff --check PASS. Suite visual integral nao reexecutada; sem GO de release.

## Clique no fundo do popup de mesa — 2026-10-15

ActionDialog recebe dismissOnBackdrop opt-in, habilitado apenas na janela de mesa.
Fechamento exige inicio e fim do clique fora dos limites; padding interno nao fecha.
locked continua bloqueando a saida; outros dialogos nao mudam por padrao.
Build/TypeScript PASS; test:visual focado attendance-mobile-design.spec.ts:
16 PASS (20,6s), incluindo clique interno/externo, retorno de foco e Escape.
Suite integral nao reexecutada. Web local reiniciada para carregar a alteracao;
sem alterar API/banco/Android, sem commit/push/merge/deploy.

## Retorno direto da limpeza — 2026-10-15

Base codex/ux-teste-mobile @54c57808cec0098be2934faa964dd6dd9cd5b41d + diff local.
Contrato de dominio atualizado em specs/004-table-guest-ordering/spec.md e adendo
027; UX em Spec029. API complete_cleaning agora aceita DIRTY liberada e CLEANING
legado. Mantem transacao/lock/autorizacao/geracao, ready_at/ator e audit; inicio de
limpeza nao observado permanece null, sem evento de inicio ficticio.

Android: liberar -> releitura DIRTY -> fecha popup; DIRTY/CLEANING mostram somente
Concluir limpeza e Voltar; concluir -> releitura AVAILABLE -> fecha popup.
Notificacao modal de sucesso removida somente nessas duas acoes. Erro preserva
contexto e feedback. Web aplica mesmo fluxo; fechamento exige leitura canonica do
id/status esperado. Releitura falha nao fecha por sucesso. Foco agora e restaurado
pelo ActionDialog, removendo efeito legado que concorria com o foco do popup pai.

Gates executados: API18 testes PostgreSQL em banco test_rodada_cleaning_tests,
incluindo tenant, repeticao409 sem incremento/evento extra e corrida com duas
conclusoes (uma aceita); manage.py check e makemigrations --check --dry-run PASS.
Web build/TypeScript e18 testes visuais focados PASS (22,8s), incluindo POST200+
GET503 conserva popup. Android assembleDebug/assembleDebugAndroidTest/90JVM/lint
PASS; Compose11 em390/fonte1, mais2 em360/fonte2 e2 em430/fonte1:15 execucoes PASS.
Primeira rodada Web16/18: foco legado concorrente corrigido e fixture503 corrigida
para o contrato code/message; asserts originais mantidos. Sem reduzir testes.

Revisao independente R3 /root/review_direct_cleaning, contexto separado e somente
leitura: P2 de fechamento sem readback corrigido, NO_FINDINGS_WITH_GAPS confirmado
apos ajustes de foco e teste concorrente. Revisor nao executou os gates; nao e
aprovacao GitHub. Resposta perdida real e homologacao de operador/dispositivo
continuam externas. Suite Web integral nao reexecutada. GO apenas para teste local.

APK instalado com -r preservando dados, size/density/fonte/animacoes restaurados.
API ASGI8000 e Web3000 atualizadas; API readiness200 e Android ONLINE. Nenhuma
mesa existente foi liberada/limpa nesta validacao: jornadas mutaveis somente em
fixtures/test DB. Sem seed/reset/migration, pagamentos, commit/push/merge/deploy.
Logs locais em visual-artifacts/android-native-port/direct-cleaning-*.log.

## Nome/apelido sempre visivel e obrigatorio — 2026-10-15

Base codex/ux-teste-mobile @54c57808cec0098be2934faa964dd6dd9cd5b41d + diff local.
Android remove toggle e opcionalidade em mesa livre/ocupada; abertura sem mesa
igual. Campo max120, bloqueia vazio/espacos e trim no envio. Selecionar Customer
nao muda requisito nem exige cadastro. Web contextual e OrderWorkspace usam campo
sempre visivel e required/trim no botao. API staff TabCreateSerializer obrigatorio;
open_tab_in_occupancy rejeita novo label vazio APOS replay de recibo existente.
Guest e open_tab interno inalterados; comandas sem nome existentes preservadas.

Gates finais: API96 testes PostgreSQL separados, zero falhas/erros/skips (JUnit
required-name-api-verified.xml), incluindo acesso, pagamento fixture, house account,
ordering, guest, concorrencia e recibo legado vazio. Web build/TypeScript PASS e18
jornadas focadas PASS (29s). Android build/lint/90JVM PASS, Compose9 em390/fonte1 e4
em360/fonte2 PASS, incluindo vazio/espacos/trim/max120 e ausencia do toggle.

Revisao independente R3 /root/review_required_name: P2 fixtures antigas e limite
standalone corrigidos, resultado NO_FINDINGS_WITH_GAPS; revisor nao executou gates.
Fixtures positivas sem nome agora recebem nome operacional; teste ordering que
exigia explicitamente staff sem label foi atualizado ao novo contrato, preservando
asserts de ausencia de mesa/Customer, estado, ator e audit. Negativos auth intactos.

Ampliacao Web para table-service.spec.ts/tab-drafts.spec.ts encontrou roteiros
legados do Atendimento anterior ao popup (falhas de navegacao); execucao interrompida
apos essas falhas. Nao e PASS global; nao suprimidos nem relaxados os criterios.
Suite integral e migracao desses roteiros continuam pendentes. Logs/resultado
focado separado em apps/web/test-results/required-name-focused.

API8000/Web3000 atualizadas; APK instalado -r, formulario real de mesa ocupada
inspecionado sem criar Tab. Captura local name-required-final.png e logs
required-name-*.log em visual-artifacts/android-native-port. Emulador restaurado
para size/density/fonte1 e animacoes normais; formulario deixado aberto.
Sem migrations/reset/seed, nova comanda/pedido/pagamento, commit/push/merge/deploy.


## Regressão de consultas sobrepostas — PR184

Trace Web495 (106PASS/3FAIL/3skip) mostrou cinco leituras completas de Tabs
pendentes e o detalhe enfileirado, sem envio ao BFF. Leitura de200 Tabs demorou
cerca de10s. Consultas regulares agora compartilham a leitura em andamento;
comandos de mesa, serviço e movimento exigem leitura iniciada depois da mutation.

Teste novo falha antes (três leituras, esperado uma) e passa depois. Build/tipos
e23 testes focados PASS, incluindo captura antiga anterior aoPOST atrasada e
confirmação somente após segunda leitura. Roteiros integrados de mesa e movimento
alinhados aos popups/limpeza direta, mantendo asserts financeiros e replay.
Integração PostgreSQL no Linux/CI final permanece necessária. Sem mudança de
baselines ou timeout, sem reset da demonstração.


## Aceite local — categorias e quantidade
- Entrada só com categorias; produtos surgem apenas no popup escolhido.
- Escolher produto não insere; cancelar conserva draft; Adicionar3 insere3.
- Personalizar preserva variantes/observações e separa configurações.
- Quantidade1–99; excesso de linha bloqueado, sem perda silenciosa.
- Produto/opção indisponível depois de abrir não pode ser adicionado.
- Back/foco/camadas e revisão integral funcionam; pendência impede mutação.
- A/B/A conserva rascunhos isolados; navegação não confirma pedido/pagamento.
- Android/Web360/390/430 e fonte ampliada, build/lint/testes e captura real.
Evidência e limites em [category-evidence.md](category-evidence.md). Aceite local
do fluxo; sem homologação PostgreSQL integrada/produção e sem PASS da suíte
visual legada completa.
