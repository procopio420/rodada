# Spec 035 — Protocolo executável de paridade visual Bar/Cozinha

**Status: CONTRATO DEFINIDO; COMPARAÇÕES AINDA NÃO EXECUTADAS.**
Referências: [spec](spec.md), [manifesto](visual-cases.json), [protótipo congelado](../../prototype/ux2/kds-bar-cozinha.html). Fonte original: branch codex/kds-ux2-raw-preview, commit 8d12e988eaa3dcd316df6b9543697a5f1be4285f, blob SHA 8b4a2a4a5f2e90496c4aa54156ad0428590dc6c5. Não rebaselinar sem mudança de contrato.

## 1. O que é identidade visual verificável

Paridade NÃO significa colar a UI fictícia nem copiar lógica de simulação. Significa que o usuário percebe a mesma organização, composição, dimensões, hierarquia, cor, tipografia, ritmo, densidade, chips, estados e gestos/CTAs nos mesmos cenários. O backend real mantém seus próprios IDs e proteção. Elementos que não pertencem ao produto (barra externa de simulação, footer de demo, botões para forçar rede e pedido fictício) devem ficar fora do app e da comparação.

Comparar a superfície interna #surface do protótipo com [data-testid=kds-root] no aplicativo; renderizar a superfície do protótipo em 390, 850 e 1200 px em vez de capturar a moldura/gradiente externo. A tela final deve ocupar a viewport real sem borda ornamental; normalizar apenas a moldura de showcase na captura, não "mascarar" conteúdo operacional.

## 2. Tokens e geometria de referência (extraídos do HTML final polido)

| Elemento | Referência do protótipo | Regra |
| --- | --- | --- |
| Base, texto | #120f0c, #f3ece1 | usar token semântico estável do design system ou equivalência exata computada |
| Painéis, elevados | #1b1713, #252019 | sem glassmorphism, gradiente decorativo ou cards aninhados |
| Borda principal | #4d4335 | contraste preservado |
| Âmbar ativo | #f5a524 | navegação, informação de fila e foco, não substituir texto |
| Verde pronto | #93db8c | sempre acompanhado de estado textual |
| Vermelho atenção | #ff775d | atrasos, alergia e bloqueio textual |
| Shell mobile | header + 3 contadores + conteúdo rolável + bottom nav | não rolar navegação junto dos tickets |
| Navegação | topo a partir de 680 px de largura da estação; bottom nav abaixo | 4 destinos ou 5 com Expedição habilitada |
| Grade | 1 coluna até 679, 2 colunas 680–1099, 3 colunas a partir de 1100 px | aplica-se ao container real, não ao viewport externo de showcase |
| Ticket | borda lateral de atenção, header destacado, linhas e ações separadas | destino, idade, observação e CTA na primeira leitura |
| Interação | alvos mínimos 44 px; principal 52 px mobile, alvo 56 px preferencial de produção | foco visível 3 px âmbar |
| Modal | largura máxima 470 px, scroll interno seguro | foco capturado e restaurado |

**Atenção:** CSS final do protótipo sobrescreve regras preliminares do mesmo arquivo. Capturar computed styles do documento renderizado, nunca deduzir valores apenas das primeiras declarações. Fonte padrão da referência é system-ui/Segoe UI; ambiente Linux CI deve fixar fonte/substituição, DPR e antialiasing. Diferença de fonte que mude a quebra de linha é falha de setup ou drift de fonte, não motivo para mascarar ticket.

## 3. Determinismo e fixture compartilhada

- Build de produção do Web contra API/PostgreSQL **de teste** (nunca Demo/Aderlan reais); preparar Venue/StaffSession descartáveis com permissões explícitas.
- Fixture "night-kds-v1": FG84 com Chopp Pilsen 2x e Gin tônica 1x pouco gelo; Mesa 12 com Água com gás 2x e 2 Burger da casa de configurações distintas; Mesa 04 com Caipirinha sem açúcar e itens de cozinha; Mesa 08 com alergia a amendoim; Mesa 02 com prontos recentes e antigos. IDs canônicos diferentes podem ser mapeados para rótulos visuais estáveis: o join é por fixture e IDs, nunca comparação cega entre dados incompatíveis.
- Fixar instante 2026-10-22T22:57:00-03:00, locale pt-BR, timezone America/Fortaleza, DPR=1, reduced-motion=reduce, animações desabilitadas e recursos externos sem variação; congelar countdown/idade e ordenar a fila de forma reproduzível.
- Capturar antes/depois do MESMO cenário, com o app já hidratado e com readback. Proibir capturar skeleton como versão final. Para overlay, abrir a mesma modalidade de diálogo nos dois lados.
- Capturar quatro formatos mínimos: 390x844 (mobile), 850x900 (tablet), 1200x900 (desktop), 1440x900 (wide container pode usar 3 colunas); regressões complementares em 360/430/768/1024/1920 e fonte 200%.
- Testar ambos BAR e KITCHEN, todos os destinos visíveis e estados críticos; usar o inventário em visual-cases.json, não uma única screenshot da fila vazia.
- Elementos dinâmicos só podem ser normalizados por fixture/clock; proibir mascarar cards, textos, avisos, tempo, botões, contadores, modais, navegação, rolamento ou estados. Anonimizar dados de teste antes da captura, nunca produzir PII real.

## 4. Critérios automáticos por região

Para cada cena comparável:
1. Pixelmatch threshold 0.1 com máximo de **2% dos pixels discrepantes na região operacional** e **1% nas regiões do CTA/destino/avisos críticos**; screenshots de diff persistidos no artifact do CI. Limiar proposto pela spec, não métrica já atingida; aferir no ambiente fixado sem ampliar tolerância para fazer passar.
2. Bounding box de header, contadores, cada ticket mapeado, painel de Passe, nav e CTA: diferença por aresta de no máximo **2 px** contra screenshot/DOM geometry de referência, descontada apenas a moldura externa do showcase. Não impor identidade 1:1 a conteúdo que extrapole em 200% text zoom; testar reflow sem truncar.
3. Computed style tokens (base, card, texto, CTA, chip e borda): correspondência dos valores canônicos ou token homologado que renda cor equivalente; fonte, weight, size e line-height preservados nos pontos de referência.
4. Sem horizontal overflow na área operável, texto crítico cortado, ações tap-target abaixo de 44 px, conteúdo de alergia escondido, deslocamento de foco/scroll com SSE, barra mobile fora da safe-area.
5. Playwright + axe checks de contraste/semântica; se pixel diff PASS mas CTA for inacessível, **FAIL**. Caso UI nova obrigatória de domínio não tenha estado equivalente no protótipo, classificar **VARIANT-NEEDS-DESIGN** e congelar nova referência aprovada antes de declarar paridade global.

**Nunca agregar uma média que esconda falha P0**: se Bar passa e Cozinha falha, estado da spec é FAIL/BLOCKED. Threshold global inferior não compensa destino ilegível, alerta ausente ou CTA incorreto.

## 5. Implementação de suíte Playwright (a criar)

- Abrir arquivo do protótipo servido localmente por fixture; escolher estação e dispositivo via controles de laboratório SOMENTE no lado referência; navegar pelas abas via data-view.
- Abrir app real na rota staff correta /bar ou /kitchen, com Venue autorizado e fixture idêntica. No app usar data-testid semântico kds-root, kds-header, kds-summary, kds-nav, kds-ticket-ORDER, kds-item-ITEM, kds-pass, kds-modal, kds-cta-ITEM. Esses são contratos de teste sugeridos, não seletores presentes hoje.
- Conferir readiness pelo snapshot canônico e disponibilidade de interações; controlar o relógio via Playwright clock e eventos com sequência determinística. Capturar screenshot de viewport e de regiões, diff PNG, JSON de bounding boxes/computed styles e trace em FAIL.
- Executar os testes com npm run test:visual e suíte específica opcional npm run test:visual -- --grep kds-parity (criar o conjunto de testes/nomes ao implementar). Gates básicos de typecheck, build, pytest/API+Postgres e integração continuam obrigatórios quando aplicáveis.
- Aplicar no PR a matriz com path da imagem fonte/resultado/diff, número de pixels divergentes, regiões, viewport, stack de browser, commit do protótipo, main/head SHAs, fixture hash, data/hora, aprovador.
- Baseline só é atualizado com diff legível, justificativa por elemento, aprovação de produto/design e commit separado. Quem implementa não pode autoaprovar desvio visual apenas mudando a captura. Não gravar máscaras indiscriminadas.

## 6. Escopo de navegação e estado visual

Pedidos BAR e KITCHEN; Passe normal e antigo; Resumo por produto; Expedição simples/desligado e ativo; Ajustes; novo pedido; alterações; alergia/bloqueio; modalidade FICHA e MESA; preparado vs produto imediato; modal de restrição, correção e conflitos; pico 30 pedidos; sem rede, SSE stale e readback incerto. Para estados não existentes no protótipo, reusar vocabulário visual e criar variação deliberada com referência aprovada, sem fingir match literal.

## 7. GO/NO-GO

**Visual GO** somente com todas as cenas obrigatórias PASS, sem exceção visual sem aprovação, screenshot/traces no commit exato e validação humana independente de Bar e Cozinha. **Product GO** adicionalmente exige AC de domínio e autorização, testes físicos quando aplicável, sem confundir CI com homologação. Reportar sempre números medidos ou "não executado"; nenhuma garantia pode ser declarada antes da execução.
