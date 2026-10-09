# Fidelidade ao material fornecido — Spec 022

Revisão em 08/10/2026, branch `codex/ux-operational-polish`. Complementa a revisão histórica da spec 021. O merge de `origin/main` em `68130c8` preservou Quick Catalog, edição/regeneração de ProductIcon e operações de comanda.

## Referência e aplicação

Os cinco ZIPs fornecidos estão preservados em `prototype/material-reference`, incluindo HTML original, assets e runtime exportado. `local.html` troca apenas a URL de fontes por fontes locais licenciadas. Nenhum runtime do mockup é importado no app.

| Material | Aplicação verificada | Diferença funcional explícita |
| --- | --- | --- |
| Sistema Rodada | Tokens quentes, Archivo condensada, JetBrains Mono, botão papel/ink, bordas e divisórias em Web, protótipo e Android | Superfícies existentes mantêm suas permissões e controles reais |
| Tela da Cozinha | Cabeçalho 72px, colunas 420/520/340 em 1280px, total por Product, tickets, passe | Transições individuais; sem batch, equipamento ou SLA inventado |
| Uma noite no bar | Mesma linguagem no catálogo, comandas, produção e entrega | Roteiro exportado é uma simulação, não estado operacional |
| Modo pico | Filtro nativo com entregas reais, mais antigas primeiro, Agora/+Pedir/Contas | Entregue conclui a ação existente; não chamar isso de claim/Pegar |
| Sem sinal → Sincronizado | Tema e conectividade reais; mecanismos existentes de reconciliação preservados | Sem fila genérica de ações ou contagem fictícia de sincronização |

ProductIcon permanece 1:1 com Product. Fritas e Brahma do material são atribuições explícitas e auditadas somente no banco descartável da revisão. UI preserva ícone publicado durante regeneração e usa o proxy canônico de assets do catálogo. Products novos continuam usando o fluxo de geração existente.

## Evidência mensurada

- A1: cinco originais executáveis, fontes locais e licenças OFL. A comparação não depende de Google Fonts em runtime.
- A2: botão equivalente da Cozinha, 116×56px, **0 pixels diferentes (0%)**, gate de 0,1%. CSS original não foi alterado; mesmo browser, fonte, texto e coordenadas inteiras evitam diferença artificial de rasterização.
- A3: teste confirma cabeçalho 72px e colunas 420/520/340. Nove telas passam nos viewports 360×800, 390×844, 430×932, 768×1024, 1280×800 e 1440×900, sem overflow, alvo abaixo de 44px ou violações WCAG AA detectadas.
- A4/A5: teste diferencia Products com nomes iguais, soma quantidades por ID, exclui READY/PICKED_UP da produção e separa Em entrega. API conserva isolamento por Venue. Falha de refresh pausa mutations.
- A6: **127 testes visuais**, **5 integrações com Django/BFF reais**, typecheck e build Web passaram após o merge. API: **28 testes**, 27 passaram e 1 teste dependente de PostgreSQL foi pulado no SQLite local. Android: assembleDebug, 20 testes unitários e lintDebug.

A galeria local separa os cinco materiais, 96 comparações determinísticas antes/depois e 20 capturas de API real. `scripts/ux-review-api.py --sqlite` usa banco temporário; o volume é distribuído entre comandas para respeitar limites. Imagens e toolchain ficam em `visual-artifacts/`, ignorado pelo Git. Não incluir tokens ou PIN em evidências.

Android foi instalado em emulador API 37, 390×844, usando o Django local real. Login e carregamento de comandas/entregas foram exercitados. Inspeção corrigiu sobreposição com a barra do sistema e hierarquia de produto/destino. Debug solicita permissão de rede local no Android 17, conforme [documentação oficial](https://developer.android.com/privacy-and-security/local-network-permission?hl=en); release não declara essa permissão de desenvolvimento.

Capturas `native-now.png`, `native-peak.png` e `native-tabs.png` confirmam filtro Pico e acesso a Contas. Modo avião/Wi-Fi desligado mostrou SEM SINAL e erro real (`native-offline.png`), preservando snapshot; após restaurar rede/Atualizar, ONLINE voltou (`native-reconnected.png`). Nenhuma cobrança foi iniciada nessa verificação. Dialogs usam containers e raios do tema compartilhado.

## Limites de fidelidade

0% aplica-se ao controle equivalente medido, não à tela inteira nem a todos os fluxos. Screenshots com dados/ações diferentes não podem servir como gate de igualdade total. Mobile empilha a composição desktop; nomes longos continuam completos.

Não há nova implementação de claim/lote, SLA, sensor, dispatch completo, provider financeiro ou queue offline genérica. Não há validação de concorrência PostgreSQL local nem homologação física/Tap on Phone. Essas capacidades exigem specs e backend próprios; reproduzir a simulação como sucesso real contrariaria o domínio.

Entrega para revisão: [PR #45](https://github.com/procopio420/rodada/pull/45), Specs 021/022, sem deployment ou merge automático.
