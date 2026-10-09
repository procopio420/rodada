# V04 parcial — tickets da Cozinha

## Entrega verificada

Cinco pedidos agrupam seis itens de produção. P08 aparece uma vez como destino, com Fritas e Calabresa mantendo estado, horário e ação próprios. A apresentação usa a identidade de Order, preserva a ordem recebida e mantém itens sem order_id independentes. Orders diferentes com a mesma Tab não são mesclados. Nenhum contrato da API ou regra operacional foi alterado.

O teste de transição confirma exatamente um POST com estado READY para Fritas/P08; Calabresa/P08 continua PREPARING com seu próprio botão. Não foi introduzida conclusão coletiva.

[Contrato documentado antes do código](v04-kitchen-tickets-contract.md). Reutilizados componentes, tokens e fixture V03. Os tamanhos existentes de destino/ação foram nomeados como tokens no design system.

## Base e preservação

Base isolada main/origin/main 742faac639adc998f3a4da6d8af485b407317851; branch codex/v04-kitchen-tickets. A infraestrutura V03 (570a832) foi reaplicada localmente como c2158f0. A branch original codex/ux-operational-polish permaneceu limpa em 6e2f4ca4f386f6ee54325cbff2fdf09b05bef597. Sem merge, push ou publicação.

## Comparação com a mesma referência

Fixture: 2026-10-09T02:14:00Z, mesmos produtos, quantidades, estados e horários da V03. A referência executável original permanece intacta. As normalizações de dados são as já documentadas na V03; nenhuma nova normalização visual, máscara ou baseline foi aplicada. O hash da captura de referência é idêntico ao anterior: 608b5814a75482103c840c03fca8a84978bb6fe957a2b509e649fa7b494449c9.

| Região | Antes | Depois |
| --- | --- | --- |
| Viewport 1280×800 | 127.755 pixels / 12,4761% | 120.164 pixels / 11,7348% |
| Tickets 520×728 | 70.772 pixels / 18,6951% | 63.181 pixels / 16,6898% |

Redução de 7.591 pixels divergentes. Cabeçalho, resumo e passe mantêm as métricas anteriores. Comparador pixelmatch threshold 0.1/includeAA false e limite de equivalência de 0,1% preservados. A comparação total ainda não atende esse limite; V04 global continua aberta.

[Evidências e hashes](evidence/v04-kitchen-tickets/sha256.json), [comparação lado a lado](evidence/v04-kitchen-tickets/v03-kitchen-tickets.side-by-side.png), [métricas antes/depois](evidence/v04-kitchen-tickets/comparison-summary.json). Os snapshots textuais retidos tiveram apenas finais de linha e whitespace de linhas normalizados para versionamento; a fonte executável não foi alterada.

## Validação

- Typecheck e build padrão Next/Turbopack: passaram.
- Suíte visual completa: 153 testes passaram; realtime: 8 passaram.
- Cozinha e Bar adjacente: 360, 430 e 1280 px; cinco grupos/seis itens, acessibilidade, sem overflow, ações individuais e destino verificados. Desktop: destino 84 px e ação 116×56; mobile: alvo mínimo 44 px.
- Capturas repetidas da referência e aplicação: estabilidade verificada pelo teste V03 mantido.
- Revisão visual das capturas desktop/mobile da Cozinha e mobile do Bar realizada.

O congelamento dos timers da fixture impedia o Axe de terminar na primeira tentativa. Os novos testes mantêm a data fixa com temporizadores ativos; os limites e verificações não foram reduzidos. O resultado aceito é a execução completa posterior, registrada em [log](evidence/v04-kitchen-tickets/v04-all.log).

## Limitações e próximos recortes pequenos

A evidência de comportamento usa rotas interceptadas no navegador; não houve validação contra backend real. Metadados ausentes de cliente/localização, indicadores/SLA, posição causada pelo aviso de conectividade e demais diferenças de composição permanecem documentados na V03. Não foram inventados dados para aproximar a imagem.

Próximos ajustes: comparar espaçamento/tipografia dentro do bloco agrupado usando os recortes existentes; definir separadamente o contrato de posicionamento do aviso de conectividade. Metadados operacionais exigem contrato antes de implementação. Nenhuma fidelidade total é declarada.
