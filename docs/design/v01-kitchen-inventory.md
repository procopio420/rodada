# Spec 023 · V01 parcial — inventário da Cozinha

Verificação: 09/10/2026. Escopo: inventário documental, sem alteração da aplicação. V01 dos cinco exports e V02–V07 continuam pendentes.

## Base e evidências

- Main conferida por fetch: `1dfdf8a62bd98a4d48cc87b2079b3b2842b7a02a`. Checkout isolado: `codex/v01-kitchen-inventory`. Comparação feita com essa main, não com a branch de trabalho mais recente.
- Branch preservada: `codex/ux-operational-polish`, `6e2f4ca4f386f6ee54325cbff2fdf09b05bef597`, local/remote iguais antes do inventário. Os merges dessa branch não foram incorporados silenciosamente à base documental.
- [Contrato versionado](../../prototype/references/kitchen/visual-contract.json), [medidas/estados brutos](evidence/v01-kitchen/measurements.json), [fixture de inspeção](evidence/v01-kitchen/inspection-fixture.json), [hashes das evidências](evidence/v01-kitchen/sha256.json), [harness reproduzível](evidence/v01-kitchen/capture.mjs).
- ZIP `Tela da Cozinha-html.zip`: SHA-256 `ffa32367f3a04131922f75f2d7ebb4968c92e01451c7c32d6e4be1a94d428e63`, igual ao manifesto. HTML importado: SHA-256 `f4cccbe86677348f83a94d60083db6ae2a100f2984e43143151b7879b4d944c6`. São hashes de fontes diferentes, não erro de integridade; importador usa fonts/runtime locais.
- Windows, Node 24.19.0, Playwright 1.58.2, Chromium 145.0.7632.6, DPR 1, locale pt-BR, timezone America/Sao_Paulo. Archivo variável e JetBrains Mono carregadas; hashes de fontes, runtime e cinco SVGs no contrato. `document.fonts.ready/check` passaram; não foi feita auditoria de glyph a glyph.
- Referência e main inicial capturadas duas vezes, com hashes idênticos em cada par; nenhum erro de render nas duas páginas. API e sessão interceptadas no navegador; nenhuma escrita em banco nem prova de autenticação/transição real.

## Estado literal e interações

Existe **uma instância `.k`**, com um estado demonstrativo estático: quatro pratos no resumo, cinco tickets visuais e três linhas no passe. O header mostra “6 pedidos”, “1 passou da meta”, “3 no passe”, relógio fixo “23:14” e “chapa · fritadeira · meta 12 min”. Cinco tickets contêm seis linhas de produto porque P08 reúne Fritas e Calabresa.

| Região/estado demonstrado | Conteúdo observado | Como alcançar / limite |
| --- | --- | --- |
| Preparo | P22 13:10 vermelho, P08 9:22 âmbar, P25 6:15, P41 4:10, P37 0:31 com NOVO; barras ilustrativas | Abrir o HTML; nenhuma política/SLA é comprovada por essa imagem |
| Passe sem retirada | P12 “Ninguém pegou · 3:40” vermelho; B4 “Esperando · 1:20” âmbar | Linhas presentes simultaneamente, não estados navegáveis |
| Passe com responsável | P44 “Carlos levando”, avatar azul | Demonstração sem origem/confiança de milestone; não equivale a ownership real |
| Ação / foco | Cinco botões “Pronto”; primeiro botão recebe foco nativo | Clicar cada um preservou HTML da `.k` e URL; não houve novo estado. Foco via teclado/harness tem outline nativo `auto 1px` |
| Ausentes do export | Vazio, loading, API error, stale/retry, salvamento, indisponibilidade, timestamp desconhecido | Extensões da aplicação; sem referência literal, sem selo de equivalência |

Classe `Component` só retorna `{}` em `renderVals`; botões não têm handlers no HTML. [Inicial](evidence/v01-kitchen/reference-initial-1280.png) e [foco](evidence/v01-kitchen/reference-focus-1280.png) preservam o export. Hover/pressed não foram contratados; nenhum fluxo operacional real foi validado.

## Dimensões e recortes canônicos

Coordenadas em CSS px, origem superior esquerda do documento, DPR 1. O root é o conteúdo de produto, sem rail/moldura externa. Não há status bar ou safe area desenhada neste export. Bordas de 1 px fazem parte dos recortes.

| Recorte único | x / y / largura / altura | Evidência |
| --- | --- | --- |
| `.k` | 0 / 0 / 1280 / 800 | [Painel](evidence/v01-kitchen/reference-initial-1280.png) |
| `.k > header` | 0 / 0 / 1280 / 72 | [Header](evidence/v01-kitchen/reference-header.png) |
| `.k > section:nth-of-type(1)` | 0 / 72 / 420 / 728 | [Resumo](evidence/v01-kitchen/reference-summary.png) |
| `.k > section:nth-of-type(2)` | 420 / 72 / 520 / 728 | [Tickets](evidence/v01-kitchen/reference-tickets.png) |
| `.k > section:nth-of-type(3)` | 940 / 72 / 340 / 728 | [Passe](evidence/v01-kitchen/reference-pass.png) |
| `.tk:nth-of-type(2)` | 420 / 130 / 519 / 93,25 | Grid interno 84 / 243 / 116, gap 16 |
| `.tk:nth-of-type(2) .btn` | 803 / 148,125 / 116 / 56 | Raio 8; sombra inset inferior 4 px |
| `.pass:nth-of-type(2)` | 940 / 130 / 340 / 65 | Grid 64 / 216, gap 12 |

Medidas tipográficas de identificação, sem promoção de tokens (V02 pendente): título 38 px / peso 900 / largura 66%; prato 44 px / 900 / 64% / line-height 39,594 px; quantidade Mono 52 px / 800; item de ticket 21 px / 700 / line-height 26,25 px; botão 18 px / 850 / 84%; chip 16 px / 700, altura 30 px; status do passe 14 px / 800. Medidas completas e estilos calculados estão no JSON.

## Diferenças diante da main observada

[Main inicial completa](evidence/v01-kitchen/main-initial-1280.png) · [região de produção](evidence/v01-kitchen/main-workspace-1280.png). A fixture conserva produtos/idades de tickets, divide P08 em duas linhas e representa P44 como READY para inspecionar a composição; **não é fixture equivalente ao export**. O catálogo de inspeção usa Fritas/Omelete explicitamente fictícios, só no navegador; `+ Item` aparece com capability de fixture, sem login real.

| Região | Referência | Main `1dfdf8a` | Classificação / próxima decisão |
| --- | --- | --- | --- |
| Geometria externa | Root 1280×800; header 72; 420/520/340 | Root 1280×1543,469; header em (20,16), 1240×80,578; workspace em (20,120,578), 1240×1052,719, colunas 310/620/310 | Diferença estrutural observada; não passa aceite de paridade |
| Resumo | Ícone, nome grande, quantidade, equipamento/capacidade e chips | Lista simples de nomes e quantidades, agregada pelo nome | Composição divergente; identidade Product depende de campo canônico (endpoint da main não fornece Product/Order IDs) |
| Tickets | Destino/zona separados; P08 reúne dois produtos; barras e ação alinhada | Uma linha por OrderItem, comanda textual e badge; ação abaixo do conteúdo no fluxo desta main | Preservar ação individual; agrupamento visual exige fixture/contrato explícito |
| Passe | Tempos, textos distintos e responsável/avatar | Badge “Pronto”, tempo ready_at e comanda; nenhum responsável | Ownership, SLA, equipamentos e zonas não vêm da projeção atual; não copiar nomes/avatares fictícios |
| Extensões | Sem catálogo ou erro/retry | Disponibilidade e `+ Item` após produção; notices e ações pausadas | Comparar extensões em contrato próprio, sem ocultar conteúdo operacional |

Resumo literal mistura universos: Bolinho mostra 3 (2 em preparo + 1 no passe); Torresmo mostra 1 apesar de não aparecer na fila; Calabresa mostra 2, mas chips P41/P12 diferem dos tickets P08/P41. Fritas soma 4 coerentemente. “6 pedidos” versus cinco tickets/seis linhas tem semântica não explicitada. V03 precisa derivação coerente e rastreável; nunca reproduzir soma incorreta ou usar mask para esconder a divergência.

A projeção da main contém id, state, quantity, product_name, tab_label, created_at e ready_at; não fornece equipamento, capacidade, meta, zone ou responsible. NEW/ACCEPTED/PREPARING mapeiam Aceitar/Preparar/Pronto. Na inspeção PICKED_UP enviado pela fixture não apareceu em fila/passe; isso foi observado, sem implementar correção.

## Extensões da aplicação capturadas

| Evidência | O que foi observado | O que não comprova |
| --- | --- | --- |
| [Inicial](evidence/v01-kitchen/main-initial-1280.png) | Fila, passe, Fritas disponível, Omelete indisponível e catálogo fechado | Dados reais ou disponibilidade server-side |
| [Salvando](evidence/v01-kitchen/main-saving-1280.png) | POST interceptado e mantido pendente; “Salvando…” e botões de operação desabilitados | Confirmação de READY |
| [Snapshot desatualizado](evidence/v01-kitchen/main-stale-1280.png) | Após +5s de relógio, leitura 503 mantém estado anterior e pausa ações | Reconexão/replay realtime |
| [Vazio](evidence/v01-kitchen/main-empty-1280.png) | Resumo “Tudo em dia”, fila e passe vazios | Estado literal do export |
| [Carregando](evidence/v01-kitchen/main-loading-1280.png) | Leituras mantidas pendentes e indicadores locais | Latência ou timeout real |
| [Erro inicial](evidence/v01-kitchen/main-error-1280.png) | 503 de inspeção, notice e “Tentar atualizar” | Backend disponível ou retry bem sucedido |
| [NEW/ACCEPTED/tempo ausente](evidence/v01-kitchen/main-missing-time-1280.png) | Aceitar, Preparar e “Tempo não informado”; PICKED_UP fora das regiões | Transições reais, entrega, retirada ou provenance |

A reference fica 1280×800 também em viewports 360/430/768: overflow horizontal observado, sem adaptação mobile literal. A main não apresentou overflow horizontal nessas três capturas e empilha as três regiões em uma coluna (320/390/720 px úteis). [360](evidence/v01-kitchen/main-initial-360.png), [430](evidence/v01-kitchen/main-initial-430.png), [768](evidence/v01-kitchen/main-initial-768.png). São observações de layout, não contratos derivados aprovados nem auditoria WCAG completa.

## Próximos ajustes pequenos (propostas, não realizados)

1. Fechar a fixture coerente por Product/OrderItem e a distinção de dados ausentes antes de comparar pixels (V03).
2. Contratar separadamente header, resumo, primeiro ticket e passe; começar pelas medidas externas/tipografia já registradas (V02/V04).
3. Documentar referência derivada sem equipamento/SLA/ownership enquanto a API não os expuser; preservar transições individuais.
4. Criar contratos derivados para 360/430/768; não reduzir a imagem de 1280 para simular responsividade (V07).

Nenhum CSS, componente, API, export, token ou teste da aplicação foi alterado. Build de inspeção passou com webpack porque Turbopack rejeita junction de node_modules fora do root; não é confirmação do build Turbopack desta base. Testes de backend, fluxos reais, WCAG completa, paridade ≤0,1%, V02–V07, Android e deployment não foram executados nesta tarefa. O valor histórico 11,2106% do plano não foi revalidado nem adotado como resultado atual; dados/recortes ainda não equivalentes impedem usar uma nova porcentagem como aceite.

## Reprodução

Na raiz do checkout com dependências Web disponíveis: servir referência com `python -m http.server 9123 --bind 127.0.0.1`; em `apps/web`, compilar e iniciar Next em 127.0.0.1:9124. Executar `node docs/design/evidence/v01-kitchen/capture.mjs` na raiz. URLs opcionais: V01_REFERENCE_URL e V01_APP_URL. O script sobrescreve apenas evidências deste diretório, não os exports/aplicação. Regeneração após revisão exige atualizar sha256.json e identificar a nova base/ambiente; não usar imagens atuais como baseline de aprovação.
