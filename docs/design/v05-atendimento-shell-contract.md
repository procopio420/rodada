# V05 parcial — navegação inferior do Atendimento

Contrato registrado antes do código em 09/10/2026. Base origin/main 742faac639adc998f3a4da6d8af485b407317851; branch isolada codex/v05-atendimento-shell. Branch do usuário e entregas anteriores preservadas; sem cherry-pick de mudanças Web.

Fonte: prototype/references/night/Main.dc.html, export night no manifest, telefone .phone 390×844 CSS px. .nav: 84 px, padding inferior 8, colunas laterais flexíveis e central 136; botão .ngo: margens 10/4/2, raio 12, sombra inferior 4; laterais: ícone 24, texto 14, gap 5, marcador ativo 3. Moldura 44 px do telefone não pertence ao produto.

Recorte: composable compartilhado de navegação, chamado pela tela real, dados/callbacks tipados, sem alterar viewmodel, API, pagamentos, pedido ou autenticação. Agora e Contas selecionam as mesmas seções; Pedir continua abrindo a comanda como já implementado (não alegar equivalência da jornada completa). Mesas/Caixa permanecem como extensão acima da barra canônica, respeitando a capability atual. Busy bloqueia Pedir. Seleção deve ter semântica e não depender somente de cor. SafeDrawingPadding de AuthApp permanece único; não duplicar insets na barra.

Fixture apenas em androidTest, com o mesmo composable de produção e callbacks locais. Referência original imutável; capturar região .nav com fontes carregadas. Android: 390 dp, densidade conhecida; medir região sem redimensionar imagem. Antes de aprovar baseline nativa, comparar geometria, cores e texto com HTML. Rasterização deve ser reportada, não escondida com tolerância ampla. Este recorte não aprova baseline total.

Gates: unitários, assembleDebug, lintDebug, instrumentação (geometria, seleção, callbacks, busy, extensão adjacente com/sem Caixa), captura nativa repetida. Registrar ambiente e limitações em vez de declarar device físico/API mínima/teclado/font scale verificados sem prova. V05 global permanece aberta; header, Agora interno, demais jornadas e visual regression gate completo fora deste recorte.

Medição executável confirmou borda superior 1 px: laterais 127×75, botão central 128×63 no conteúdo 390. Token Subtle (já canônico no sistema) usado nas laterais inativas. Sombra de tecla 4 dp. A referência literal inclui cantos da moldura; crop derivado remove apenas border-radius da .phone, não a região .nav, para separar chrome de apresentação.
