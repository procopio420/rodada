# Spec023 — hierarquia parcial da Gerência

Base main `9b8e5e5`, branch isolada `codex/spec023-management-hierarchy`. Contrato `f2c9b3b`, interface `92b344b`, fixture de preços `32dc88e`. Branch original `codex/ux-operational-polish` e branch anterior de revisão preservadas. PRs61/62 identificados; nenhuma alteração de API/Android ou absorção de trabalho não publicado. Main inclui PR63. Evidências antigas permanecem específicas dos seus commits.

## Mudança e evidências

Antes: seis destinos em grade de cinco colunas, sem pictogramas; quatro indicadores com peso semelhante. Depois: cinco destinos com ícone e label, seleção por hash e aria-current; Impressoras permanece em Mais; preços permanece acessível em Gestão. Exposição canônica em largura total/34px; indicadores secundários28px; cabeçalhos20px/ícone20; ícones de navegação24px. Exceções precedem o pulso. Sombra semântica discreta separa barra e informação financeira. Nenhuma mudança financeira, de sessão, disponibilidade ou fulfillment.

- [Antes390](evidence/spec023-management/before-390.png) e [depois390](evidence/spec023-management/after-390.png): fixture visual existente, exposiçãoR$72,00, mesmo conjunto de dados; banco e pessoas reais não fazem parte dessas capturas.
- [Exceções360](evidence/spec023-management/warnings-360.png): divergência precede exposição; sem corte lateral.
- [Ícone](evidence/spec023-management/icon-comparison.png), [medição](evidence/spec023-management/icon-stats.json). Export night imutável SHA256912b59ca1bfc6f0f7c92927ac6e0d8f4f663963f34f7adbb6a228e48c98d0a2f.

A comparação literal do ícone foi14.72%, em posições fracionadas distintas: referência(461.5,816.5), aplicação(30.1875,780.09375), ambas24px e corrgb(243,236,225). Espécimes posicionados em(0,0) com fundo equivalente g1/surface-1 resultaram0%, sem modificar paths/stroke/cor/export ou limiar0.1%. Esse teste mede somente o pictograma Agora. Os outros ícones são extensões locais do vocabulário vetorial, não cópias de uma tela de Gerência inexistente.

## Validação

Typecheck/build passaram. Realtime 8/8. Integração PostgreSQL 11/11 com API ASGI e dispatcher dos scripts existentes, banco exclusivo `rodada_web_e2e`; banco de teste anterior renomeado e preservado como `rodada_web_e2e_before_management_hierarchy`. Banco `rodada_demo`, volumes e serviços ativos não foram alterados.

Primeira suíte visual:186 aprovados/1falha na fixture de preços já existente: GET/api/pos/tabs/slow-tab/ não tinha resposta. Fixture completada com detalhe canônico; assert de botão bloqueado até terminar pricing mantido. Rechecagem de preços7/7. Repetição completa após a correção: **187/187 passaram**, sem retries ou skips.

Gerência, Caixa e Cozinha: layout/acessibilidade360/390/430/768/1280/1440; novos testes de hierarquia e cinco destinos360/430/768. Fonte ampliada controlada apenas nos labels da barra (14→28px): ResizeObserver reserva altura real e labels podem quebrar sem sobreposição do conteúdo. Não equivale a teste global de zoom200%, teclado/OS ou dispositivo físico. Android não foi alterado/revalidado neste recorte. CI remoto é independente dos gates locais.

## Prévia e limites

Prévia separada em http://localhost:3123/manage, API8123 e dispatcher próprios com banco dos testes. Usar hostname localhost para separar cookies da demo127.0.0.1:3119. Entrada pelo /staff com operador de testes existente; acesso fornecido na conversa, não publicado nesta documentação. A entrada pela UI foi verificada: Gerência Ao vivo, seis comandas abertas, exposiçãoR$119,00 provenientes do PostgreSQL após os onze testes. Esses números são dados de testes e não substituem a fixture visualR$72,00. A demo3119/API18764/PG55459 permanecem nos processos existentes.

GO para revisar este recorte da Gerência. V01–V05 globais permanecem abertos; não se declara fidelidade total ou acabamento de todo o app. Tickets HTML ainda têm diferença histórica16.6898% e navegação Android1.746% (não reavaliadas aqui). Próximos pequenos recortes já no escopo023: hierarquia de quantidade/destino/ação dos tickets; composição do fluxo PDV/conta e consistência de ações; headers/áreas internas com fonte ampliada e safe areas. Não copiar este estilo indiscriminadamente para telas sem medir seus estados/referências.

## Atualização concorrente da main

Ao publicar, main avançou para `ae416da` (PR64, commit Lucas `9f1d96b`), com a mesma correção de fixture. Integração somente na branch isolada em `859323b`, mantendo **o arquivo pricing.spec.ts exato da main** e o relatório de release do Lucas; os commits anteriores continuam no histórico. Typecheck e sete testes de preços passaram novamente após essa integração. Os187 visuais,11 PostgreSQL e8 realtime referem-se ao recorte antes dessa atualização; arquivos de aplicação deste recorte permaneceram idênticos. Não houve merge do PR na main ou force push. Branch original continua `6e2f4ca`, sem mudanças; `.worktrees/` existente preservado. CI remoto permanece uma evidência separada.
