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
