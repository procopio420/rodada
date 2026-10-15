# Spec 030 — Landing comercial Rodada (rodada.bar)

## Objetivo
Transformar a landing institucional em uma página comercial de marca: **“Mais uma rodada. Menos trabalho.”**, combinando orgulho do bar movimentado e provocação contra a operação confusa.

## Público / conversão
Donos e gestores de bares brasileiros, começando por operações de alto movimento. Conversão primária: conversa para demonstração via WhatsApp oficial já presente no site.

## Comportamento
- Hero apresenta marca, benefício e CTA imediatamente.
- A navegação mobile em 320–380px usa CTA curto, sem quebra de linha.
- O CTA fixo mobile começa oculto, surge apenas depois que o hero sai da viewport e volta a ocultar na seção final; sem JS, links convencionais permanecem funcionais.
- A galeria contextualiza o uso real do software com capturas de fixture, sem forjar cenas ou métricas.
- Explicar problema → fluxo atendimento/produção/gerência → produto → piloto → FAQ → CTA.
- Exibir apenas screenshots locais de ambiente de teste rotulados como tal.
- Dar respostas prudentes a preço, migração, equipamento e conectividade.
- Manter rotas públicas de privacidade, termos e exclusão de conta.

## Fora de escopo
Cadastro, pagamento, geração de leads com dados pessoais, analytics, automação WhatsApp, integração com API, implantação/homologação e atualização dos apps de operação. Não fabricar prova social, métricas ou depoimentos.

## Design e segurança
Reutilizar `assets/brand/v1` distribuídos em `apps/landing/brand/`, Archivo local, paleta do `docs/design/system.md`, sem JS remoto. Imagens de teste sem dados de clientes reais. Considerar 360/390/430 e desktop, teclado, foco visível e movimento reduzido.

## Hero publicitário — Slice 2
- Arte ilustrativa aprovada pelo usuário, integrada em apps/landing/marketing/rodada-campanha.jpg.
- No desktop a imagem completa acompanha CTA real; no mobile há título acessível e versão otimizada `marketing/rodada-campanha-mobile.webp` com enquadramento focado no atendimento.
- Frase secundária revisada: “Seu bar merece movimento. Menos correria.”
- O QR na arte não é escaneável; tratá-lo como ilustração, sem sugerir cliente/piloto real.
- Metadados og:image para compartilhamento e Docker incluindo pasta marketing/ e screenshots da galeria.

## Direção 2026 — Slice 3 (substitui o hero-pôster)

- A campanha ilustrativa permanece apenas como material social `og:image`; o hero da landing **não** pode depender de lettering ou logo rasterizados na foto.
- O hero usa H1/CTA verdadeiros, responsivos, pesquisáveis e acessíveis. A fotografia recortada é contexto humano secundário, rotulada como ilustração de IA.
- A primeira dobra combina posicionamento direto, demonstração e produto sem fingir números de clientes, dashboard ao vivo ou receita.
- Mostrar um tour interativo real de interface para Atendimento, Bar e Gerência com capturas versionadas de ambiente de testes. Interação muda somente a apresentação; não usa API, não registra pedido, não chama endpoints e não coleta dados.
- Navegação do tour por clique/toque/teclado com `role=tab`, `aria-selected`, `aria-controls`, `role=tabpanel` e foco visível. Sem JS, as três áreas continuam visíveis em sequência.
- Motion é aprimoramento discreto, respeita `prefers-reduced-motion` e nunca impede a compreensão do conteúdo.
- CTA mobile fixo segue surgindo após o hero; no fim da página deve desaparecer para não cobrir o último convite.
- Manter `rodada.bar` canônico, WhatsApp aprovado, rotas legais e disclaimer de imagens conceituais.


## Slice 4 — microinterações e movimento (2026-10-15)

- **Camada P1:** transições discretas de 160–250 ms em CTA, nav, abas e FAQ. O FAQ usa `details` nativo com abertura interpolada apenas em browsers compatíveis.
- **Camada P2:** hero em sequência sutil, troca visual do tour (~240–290 ms) e revelação de seções apenas uma vez após entrar na viewport (até 480 ms). Não usar carrossel automático, parallax constante ou animações decorativas sem propósito.
- CTA mobile ganha fade + slide controlado por `IntersectionObserver`, `visibility`, `inert` e `aria-hidden`. A ausência de JS mantém a barra `hidden` e os links normais continuam operáveis.
- Animar somente `opacity`/`transform` nos reveals, respeitar `prefers-reduced-motion` em animações e transições, preservar conteúdo visível mesmo sem JS e garantir que abas/FAQ continuem operáveis por teclado.
- Sem rastreamento, CDNs, dependências ou mudanças na lógica operacional do Rodada.
