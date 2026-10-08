# Revisão UX operacional — Spec 021

Data: 2026-10-08. Base: `main`/`origin/main` confirmado em `4ba9c237b74878730c8b133e70dd8b02087c2cd7`. Branch: `codex/ux-operational-polish`. A fundação PR #40 e a conclusão Spec 020 são preservadas.

## Matriz priorizada

| Surface | Device | State | Issue | Severity | Fix | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Cozinha | seis viewports | normal/lotado | Catálogo empurra preparo para baixo | P1 | Fila e passe antes de catálogo/cadastro | `before/kitchen-390.png` → `kitchen-390.png` | Implementado |
| Bar | seis viewports | normal/lotado | Mesma hierarquia; largura limitada no desktop | P1 | Split produção/passe a partir de 768 px; nomes 20 px | `bar-1440.png`, `kitchen-1440.png` | Implementado |
| Gerência | mobile/tablet/desktop | normal/warning | Conta da Casa/formulários antes do pulso | P1 | Exceções → pulso → operação → Gestão/Conta da Casa | `before/manage-390.png` → `manage-390.png` | Implementado |
| Gerência | mobile | normal | READY contado junto de itens em fila | P1 | "Em preparo" exclui READY; delivery permanece separado | Teste de hierarquia/contagem e API real | Implementado |
| Cliente | seis viewports | normal/long/disabled | CSS expande ícone e cola nome, estação e preço | P0 | Button existente, ícone fixo 58 px, colunas/gap de tokens | `before/guest-390.png` → `guest-390.png` | Implementado |
| POS legado | mobile/desktop | indisponível | Item indisponível parece selecionável | P0 | Disabled + texto explícito; API continua validando | `pos-warnings-360.png`, `real-api/pos-unavailable-390.png` | Implementado |
| Caixa | seis viewports | aberto/fechado/warning | Sem novo bloqueio visual observado; risco financeiro exige manter contrato | — | Abertura, fechamento, PIN, revisão antiga com turno ativo preservados | `cash-390.png`, `real-api/cash-success-390.png` | Verificado; sem mudança financeira |
| Estornos | seis viewports | normal/empty/erro | Sem novo overflow; rótulos técnicos de método/status ainda aparecem | P2 | Registrar dívida de linguagem; sem alterar fluxo de confirmação nesta slice | `refunds-390.png`, captura real sem pagamento elegível | Revisado; tradução futura |
| Staff | seis viewports | login/erro/sessão | Sem novo bloqueio visual observado | — | Teclado/foco/login/cookies/revogação preservados | `staff-390.png`, `real-api/staff-local-390.png` | Verificado |
| Relatórios | seis viewports | normal/loading/error/long | Sem nova regressão; fatos e exposição atual têm rótulos separados | — | Filtros/calendário/CSV preservados | `reports-390.png`, `real-api/reports-390.png` | Verificado |
| Android Atendimento | Android | — | Sem JDK/SDK/adb/emulador nos locais verificados | Ambiente | README e código inspecionados; nenhum build/capture Android alegado | `apps/attendance-android/README.md` | Bloqueado por ambiente |
| Banco | local | real API | PostgreSQL/psql/docker não encontrados | Ambiente | Django real em SQLite temporário; runner suporta opt-in PostgreSQL dedicado | `scripts/ux-review-api.py` | PostgreSQL local não validado |

Os caminhos de evidência acima são relativos a `visual-artifacts/`, ignorado pelo Git. Não armazenar credenciais, tokens de sessão ou PIN nas imagens/galeria.

## Evidência e revisão humana

O índice `visual-artifacts/index.html` combina 96 capturas determinísticas de superfícies/estados com comparações antes/depois disponíveis e evidência real em seção separada. Os seis viewports são **360×800, 390×844, 430×932, 768×1024, 1280×800 e 1440×900**. Estados adicionais usam 360×844, conforme a suíte anterior. Capturas são full-page; a altura identifica o viewport do navegador, não a altura total do arquivo. As nove telas são Staff, Bar, Cozinha, Cliente com token, Gerência, Caixa, Estornos, POS e Relatórios.

Capturas de Cozinha, Bar, Gerência, Cliente, Caixa, Estornos, POS, Staff e Relatórios foram abertas e inspecionadas; também há leitura de desktop e estados de nomes longos/warning. Os screenshots determinísticos não são evidência de backend. `real-api/` vem do Django/BFF reais nos testes e da instância local seeded. A simulação local distribui o volume entre comandas distintas para respeitar os limites reais; não desativa política financeira. A primeira tentativa excedeu o limite e foi rejeitada; o banco temporário foi reiniciado para repetir o cenário corrigido.

Para o designer: revisar prioridade da fila/passe e densidade em desktop, acesso ao catálogo após o trabalho operacional e posição de Conta da Casa em Gestão. A escolha atual reduz o conteúdo antes da próxima ação e preserva todos os controles. Em fila longa mobile, passe/disponibilidade continuam exigindo scroll; não foi criado filtro, sticky navigation ou nova máquina de estados. Carrinho guest sem edição de quantidades permanece dívida de interação existente e precisa de contrato próprio antes de expansão.

## Cenários reais e limites

| Cenário | Resultado verificado | Limite |
| --- | --- | --- |
| Bar/Cozinha cheios | API local com 12 intenções idempotentes, múltiplas comandas e estados NEW/PREPARING/READY; visual lotado com nomes longos | Sem métrica SLA/telemetria inventada; exceção simulada apenas em fixture visual |
| Gerente no celular | Pulso/produção, exceções de caixa e estorno, links funcionais, Gestão/Conta da Casa | Não declarar analytics avançado nem realtime contínuo |
| Guest | QR válido, comanda, confirmação, histórico após reload, READY e revogação reais | Sem pagamento provider; polling existente de 5 s |
| Atendimento | Sessão Web e seleção de comanda/indisponibilidade reais | Cenário Android e Tap on Phone não PASS neste ambiente |
| Fechamento | Abrir, contar, fechar, divergência, PIN e revisão histórica reais | SQLite não prova concorrência PostgreSQL |
| Relatórios | Consulta e CSV autenticado/protegido contra fórmula | Sem previsão, ranking ou métricas fabricadas |

`/guest` sem token não existe como página local. O router contém `/guest/[token]`; o launcher aponta para a mesa demonstrativa criada na instância atual. Hosts canônicos/aliases continuam sob os testes existentes.

## Reprodução

Na raiz, iniciar API descartável: `python scripts/ux-review-api.py --sqlite`. `seed_demo` é aplicado exclusivamente nesse banco temporário. Para PostgreSQL, provisionar **rodada_ux_review** isolado, configurar variáveis conforme README da API e usar `--postgres`; o script rejeita outro nome de banco. Ele nunca cria/remove bancos PostgreSQL. Ao reiniciar SQLite, toda a demonstração é nova.

Web: `cd apps/web`, `npm run build`, definir `RODADA_API_BASE_URL=http://127.0.0.1:8000`, `npm run start -- --hostname 127.0.0.1 --port 3000`. Na raiz: `node scripts/ux-review-live.mjs` prepara volume de demonstração e captura nove telas reais; `node scripts/ux-review-gallery.mjs` gera launcher/galeria. Servir somente os artefatos: `python -m http.server 3200 --bind 127.0.0.1 --directory visual-artifacts`. Abrir `http://127.0.0.1:3200/`; login via `/staff` com credenciais locais do README da API, sem colocá-las no índice.

Para preservar baseline antes de editar, executar a suíte visual e depois `node scripts/ux-review-gallery.mjs --before`. Não executar `--before` depois da alteração: isso sobrescreveria o registro anterior. Reexecutar a suíte e gerar o índice após mudar UI. Artefatos/baselines de imagem continuam ignorados; nenhuma expectativa de screenshot foi relaxada.

Nesta máquina `npm` não está no PATH. Foram executados os entrypoints Node equivalentes: `node node_modules/typescript/bin/tsc --noEmit`, `node node_modules/next/dist/bin/next build` e `node node_modules/@playwright/test/cli.js test` (com `--config playwright.integration.config.ts` para integração). `RODADA_TEST_PYTHON` aponta ao Python 3.12 gerenciado. Chromium existente foi reutilizado. A execução precisou de permissão fora do sandbox para SWC/Chromium e sockets locais; a execução restrita falhou por acesso negado, não por erro de produto.

## Validação

Typecheck e build passaram. Integração final: **5 testes passaram**, incluindo item indisponível na estação/disabled no POS, idempotência, histórico guest, revogação, permissões, caixa histórico e CSV. Os sete primitives equivalentes mantêm **0% de diferença** com gate de 0,1%. A comparação Kitchen inteira mede **9,8171%** e continua artefato de workflows distintos, sem alegação de paridade total. Matriz visual completa: **125 testes passaram**; após o destaque final de comandas REQUIRES_ACTION, os **13 testes de Gerência** foram repetidos e passaram, junto de build e integração real. A documentação distingue essa revalidação focada de uma execução completa adicional. Nenhum deploy, cobrança de provider, validação física ou concorrência PostgreSQL local é alegado.
