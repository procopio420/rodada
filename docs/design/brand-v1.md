# Rodada — branding v1 (arte vetorial fiel à referência)

**Status:** identidade inicial aprovada. **Revisão:** 13/10/2026.

## O que aprovamos

Marca brasileira, ousada, noturna e calorosa: bar de verdade + tecnologia que simplifica a operação. Logo em letras minúsculas, **grossas, arredondadas e orgânicas**. O segundo caractere é um `o` em forma de **porta-copo/copo visto de cima**, com líquido âmbar e duas bolhas. Evitar banco digital/fintech, delivery, cervejaria literal e SaaS genérico.

Esta revisão substitui o wordmark geométrico fino do primeiro commit no PR #120. Os caminhos abaixo usam **contornos vetorizados diretamente da referência visual aprovada**, com simplificação de curvas para uso real em SVG/Android. O resultado é aproximado à imagem gerada, não um arquivo-fonte de design original. Confirmar visualmente antes de publicação ou registro da marca.

## Arquivos-fonte

| Arquivo | Aplicação |
| --- | --- |
| `assets/brand/v1/wordmark.svg` | Logo principal em fundo noturno |
| `assets/brand/v1/wordmark-on-light.svg` | Letras Ink sobre papel |
| `assets/brand/v1/symbol.svg` | Ícone no app, PWA, QR, favicon |
| `assets/brand/v1/symbol-mono.svg` | Uso monocromático (sobre fundo escuro) |
| `assets/brand/v1/lockup.svg` | Logo com tagline institucional |
| `assets/brand/v1/tokens.json` | Cores, fontes e copy |

Os SVGs do wordmark têm contornos e não dependem da disponibilidade de nenhuma fonte. `lockup.svg` tem texto auxiliar da tagline; para gráfica, converter em curvas antes de enviar à impressão. Os arquivos `apps/landing/brand/`, `apps/web/public/brand/` e `apps/web/public/favicon.svg` são **cópias de distribuição**, não novos originais.

## Cores canônicas

| Nome | Hex |
| --- | --- |
| Noite | `#120F0C` |
| Âmbar | `#F5A524` |
| Papel | `#F3ECE1` |
| Superfície | `#252019` |
| Ink | `#17130F` |

Sem gradientes ou novas cores de estado. Os status de operação continuam regidos por `docs/design/system.md` (warning/success/danger/info), não pela marca.

## Tipografia

- Wordmark: **lettering exclusivo em curvas**, não renderizar a partir de Archivo ou fonte genérica.
- UI: **Archivo**, como já implementado.
- Valores: **JetBrains Mono**, conforme design system.

## Tom de voz

- **Institucional:** “Tudo que faz o bar rodar.”
- **Campanha:** “Me vê uma rodada aí.”
- Direto, brasileiro e descontraído; evitar promessas sem evidência de crescimento de vendas.

## Uso correto

1. Logo padrão creme/âmbar sobre fundo noturno; variante Ink/âmbar em papel.
2. Símbolo isolado no Android, favicon, PIN/QR e avatars; não embutir uma fotografia ou screenshot no ícone.
3. Área livre recomendada de 1/4 do diâmetro do símbolo.
4. Conferir legibilidade em 16px; preferir >=24px para ícone e >=120px de largura para logo principal.
5. Não rotacionar, deformar, acrescentar contornos ou reposicionar bolhas/líquido.
6. Card/QR: preservar a quiet zone do QR verdadeiro. QR da imagem conceitual não é uma peça funcional.
7. Produtos continuam usando tokens e ícones específicos do próprio design system.

## Distribuição e geração

- `apps/landing/brand/`: cópias dos SVGs canônicos (landing `rodada.bar`).
- `apps/web/public/brand/`: cópias para PWA e frontend.
- `apps/attendance-android/app/src/main/res/drawable/ic_rodada_foreground.xml`: vetor Android baseado nos mesmos contornos.
- `scripts/android-generate-play-artwork.py`: gera PNGs da Play Store a partir de SVGs canônicos (Pillow e CairoSVG).
- `scripts/verify-brand-v1.py`: confere XML e cópias do SVG; sem criar workflow GitHub Actions adicional.

**Limites:** o pacote/PR não é deploy, nova AAB, aprovação na Play Store ou teste em aparelho físico. É necessário conferir visualmente no app Android, favicon e navegador, e validar a disponibilidade de marca no INPI em momento apropriado.
