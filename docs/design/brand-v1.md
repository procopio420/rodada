# Rodada — Branding v1

**Aprovado como identidade inicial:** 13/10/2026. **Escopo:** marca, não redesign de estados operacionais.

## Conceito

Marca ousada, brasileira e noturna: bar real com tecnologia confiável. **O "o" de Rodada** funciona como bolacha de chope/porta-copo visto de cima, com onda de líquido e bolhas. Funciona para bares de cerveja e de drinks. Não parecer fintech, banco, delivery, marca de cervejaria nem SaaS genérico.

## Assets oficiais

| Arquivo | Uso |
| --- | --- |
| `assets/brand/v1/wordmark.svg` | Marca principal em fundo escuro |
| `assets/brand/v1/wordmark-on-light.svg` | Marca em fundo papel/claro |
| `assets/brand/v1/symbol.svg` | Símbolo sem texto: app, favicon, QR, avatar |
| `assets/brand/v1/symbol-mono.svg` | Impressão de uma cor (sobre fundo escuro) |
| `assets/brand/v1/lockup.svg` | Logo com assinatura institucional |
| `assets/brand/v1/tokens.json` | Valores e texto canônicos |

SVGs vetoriais são **arte-final v1 recriada a partir do conceito aprovado**, não trace fiel do mockup gerado. Não usar capturas do moodboard como arquivos de produção ou como QR funcional.

## Paleta

| Token | Hex | Função |
| --- | --- | --- |
| Noite | `#120F0C` | Fundo principal |
| Âmbar | `#F5A524` | Líquido, marca, acentos |
| Papel | `#F3ECE1` | Letras e anel em fundo escuro |
| Superfície | `#252019` | Plano secundário |
| Ink | `#17130F` | Texto sobre claro/âmbar |

A marca **não muda a semântica** de success/danger/info/warning nem os tokens de interação; `docs/design/system.md` continua sendo a fonte de verdade do produto.

## Tipografia

- **Wordmark:** lettering geométrico, arredondado e pesado embutido como curvas SVG — não depende de fontes instaladas.
- **Interface e landing:** Archivo local (já utilizado no projeto).
- **Valores e contadores:** JetBrains Mono.
- Assinatura de `lockup.svg`: texto auxiliar usando Archivo/Arial; para impressão de alta precisão, converter em curvas no arquivo final.

## Voz

- **Institucional:** “Tudo que faz o bar rodar.”
- **Campanha:** “Me vê uma rodada aí.”
- Direto e brasileiro, com personalidade de balcão sem exagerar em gírias ou promessas comerciais não verificadas.

## Regras de aplicação

1. Em fundo noturno usar a versão padrão; sobre papel/creme usar `wordmark-on-light.svg`.
2. Preferir logo isolado em peças comerciais e símbolo isolado em app/favicon/QR. Nunca transformar logo em botão de estado.
3. Proteção mínima: **1/4 do diâmetro do símbolo** ao redor da marca.
4. Símbolo recomendado a partir de 24px (conferir manualmente a 16px); logo principal a partir de 120px de largura.
5. Não distorcer, sombrear, acrescentar gradientes, emoji, copos literais ou contornos decorativos.
6. No QR da mesa, preservar o código real e sua quiet zone. O QR ilustrativo do conceito não serve para produção.
7. Na Play Store usar o PNG **gerado do SVG oficial**; o Android usa vetor adaptativo correspondente. Não publicar ilustração de moodboard como ícone.

## Integrações

- Canon: `assets/brand/v1/` (fonte única).
- Landing Nginx: `apps/landing/brand/` + Archivo já versionado em apps/web.
- Web/PWA: `apps/web/public/brand/` + metadata/favicon/manifest.
- Android: `ic_rodada_foreground.xml` (mesma geometria e cores).
- Arte Play Store: `python3 scripts/android-generate-play-artwork.py` produz `play-artwork/icon-512.png` e `feature-1024x500.png` localmente (requer Pillow e CairoSVG).
- Auditoria: `python3 scripts/verify-brand-v1.py` verifica arquivos e duplicatas de publicação; evitar criar workflow novo só para branding.

## Pendências fora do commit

- Conferir browser (mobile/desktop), 16px/favicon, máscara do launcher Android e arte da Play Console.
- Não houve deploy, publicação da Play Store ou teste em dispositivo físico.
- Disponibilidade jurídica/registro da marca no INPI ainda não investigados.
