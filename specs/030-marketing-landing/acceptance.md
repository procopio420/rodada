# Critérios de aceite — Spec 030

## Histórico (slices 1 e 2)
Os primeiros slices testaram o hero publicitário com arte gerada, a versão comercial 2.1 e 10 viewports. Esses resultados são históricos e **não validam a renderização atual**. A arte publicitária continua disponível para compartilhamento (`og:image`), mas não ocupa mais a primeira dobra como pôster.

## Slice 3 — experiência web 2026 (atual)
- [x] Headline, conteúdo e CTA do hero são HTML semântico; nenhum texto essencial depende da imagem.
- [x] Logo SVG oficial, Archivo local e cores definidas no brand v1 preservados.
- [x] Fotografia de contexto secundária sem lettering baked-in visível no enquadramento verificado; legenda diz que é ilustração de IA e QR decorativo.
- [x] Tour interativo com três telas reais de fixtures: Atendimento, Bar e Gerência; sem dados ao vivo nem pedidos reais.
- [x] Tabs funcionam com clique/toque e teclado (setas); aria-selected e aria-controls acompanham o estado.
- [x] Sem JavaScript, conteúdo das três áreas e links de CTA permanecem acessíveis.
- [x] CTA de WhatsApp funciona nos formatos testados; CTA fixo aparece somente após o hero no mobile e some na seção final.
- [x] Testes estáticos e verificação em Chromium 320, 360, 375, 390, 430, 768, 820, 1024, 1440 e 1920 sem overflow, fontes/imagens quebradas ou erros JS.
- [x] Metadados OpenGraph, caminhos de documentos legais e empacotamento Docker preservados.
- [ ] Testes manuais em Safari/Firefox, celular físico, leitor de tela, zoom elevado e aprovações comercial/publicitária.
- [ ] Revisão independente do PR antes da integração.
- [ ] Merge e deploy separados, apenas com autorização específica.

### Evidências (SHA de implementação)
- `057d822f58aaa2fd992b2812565b672ac89ce133`
- [Chromium 10 viewports + tours + fallback sem JS](https://github.com/procopio420/rodada/actions/runs/38781092807)
- [Contrato estático](https://github.com/procopio420/rodada/actions/runs/38781092815)
- Capturas completas e geometria no artefato de CI. Ver [auditoria visual](../../docs/design/landing-campaign-qa-2026-10-15.md).

**Estes resultados são de um preview do código estático, não evidência de deploy, homologação operacional ou resultado comercial.**
