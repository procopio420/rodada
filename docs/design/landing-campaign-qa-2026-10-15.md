# Landing Rodada — revisão comercial e visual (15/10/2026)

**PR** #188 · **branch** `feat/landing-campaign-2026` · **SHA auditado** `0caea2d0433905ab959b1ddbaa2fc46181006f42`

## Tese comercial

A landing não deve competir por quantidade de funcionalidades com ERPs genéricos. Para o dono de bar de alto movimento, vender a sensação de casa cheia **sem perda de controle**, com prova concreta de que o pedido pode sair da mesa e alcançar o setor certo. Campanha: “Mais uma rodada. Menos trabalho.” Submensagem: “Seu bar merece movimento. Não confusão.”

## Revisão real em Chromium

[Execução de Playwright](https://github.com/procopio420/rodada/actions/runs/38759159228) com screenshots e JSONs disponíveis nos artifacts do run.

| Viewport | HTML/CSS | Imagens | CTA principal (final da caixa, px) | Altura viewport | Resultado |
| --- | --- | --- | ---: | ---: | --- |
| Mobile 360×800 | Sem scroll horizontal | 6/6 | 673 | 800 | PASS |
| Mobile 390×844 | Sem scroll horizontal | 6/6 | 638 | 844 | PASS |
| Mobile 430×932 | Sem scroll horizontal | 6/6 | 638 | 932 | PASS |
| Tablet 768×1024 | Sem scroll horizontal | 6/6 | 689 | 1024 | PASS |
| Desktop 1440×900 | Sem scroll horizontal | 6/6 | 684 | 900 | PASS |

Archivo carregada em todos os formatos; sem pageerror; primeiro Tab alcança o link de pular conteúdo. São screenshots e checagens de geometria de **Chromium headless**, não testes em aparelhos reais, Safari, Firefox ou leitores de tela.

## O que foi corrigido
- **Desktop P0 de conversão:** headline quebrava em quatro linhas e levava o CTA para baixo da primeira tela (bottom 895 px em viewport 900 px). Ajuste do tamanho tipográfico mantém o slogan em duas linhas e CTA em 684 px.
- **Verificação mobile:** imagem abaixo da dobra estava marcada como incompleta no screenshot inicial porque `loading="lazy"` adiava o carregamento. O QA agora força decode antes da captura sem modificar o lazy loading do site; 6/6 imagens carregadas em todas as larguras.
- **Precisão comercial/SEO:** título da aba passa a incluir “Sistema para bares” e a navegação usa “Pedir demonstração”, não uma promessa de agendamento automático.

## Diagnóstico de marketing
**O que funciona:** posicionamento claro na primeira dobra; identidade noturna e quente; chamada principal única por contexto; visual real do produto em vez de wireframes; WhatsApp sempre disponível no mobile; FAQ resolve objeções sem promessas não homologadas.

**Antes de mídia paga:** fotografar operação real com autorização, produzir demonstração de 15–25 segundos, adicionar imagem Open Graph compartilhável, documentar oferta comercial para reduzir objeção “quanto custa?”, conseguir depoimento com autorização e definir mensuração de conversão respeitando privacidade. Não inserir números de ganhos, clientes ou aprovação que não possuímos.

**Risco residual:** sticky CTA mobile fica sobre conteúdo durante scroll, deliberadamente para manter contato visível. Validar com donos de bares se prejudica a visualização do mockup; comparar com variante discreta antes de alterar. Screenshot de teste pode divergir do build do piloto.

## Próximos gates
1. Aprovação do conteúdo visual e comercial, respeitando dados/autorizações.
2. Revisão independente + CI no último SHA após integração.
3. Merge e deploy separados mediante autorização explícita.


## Rodada 2.1 — revisão comercial por dispositivo (15/10/2026)

**Base testada antes desta nota:** `5656f02fa41377ebea2294ebe3a3ecf0abea779d` · [Chromium QA](https://github.com/procopio420/rodada/actions/runs/38764191415) · [static checks](https://github.com/procopio420/rodada/actions/runs/38764191585).

### Checklist comercial implementado
- Header mobile usa `Ver demo` em até 380px, com CTA de 44px e nenhuma quebra verificada.
- Copy de identificação imediata do cliente: “Quando o bar lota, o garçom precisa atender — não fazer viagens ao caixa”.
- Narrativa PEDIR → PREPARAR → ACOMPANHAR e legendas que explicam como cada tela ajuda.
- CTA fixo mobile via pequena melhoria inline sem requisições: fica escondido no hero, aparece após o hero e se oculta quando a chamada final está visível. Sem JavaScript, CTAs convencionais continuam acessíveis.
- Galeria usa somente screenshots de ambiente de teste, sem atribuir provas falsas ou usar fotos de terceiros como se fossem do piloto.
- Mantidas informações honestas de preço, internet, equipamentos, funcionalidades, estágio de piloto e links legais.

### Chromium / tamanhos testados
Todos **10/10 PASS**: 320×700, 360×800, 375×667, 390×844, 430×932, 768×1024, 820×1180, 1024×768, 1440×900, 1920×1080. Contrato automatizado: HTTP 200, sem overflow horizontal, fontes/imagens carregadas, sem JS page errors, CTA header na primeira dobra sem quebra, sticky inicialmente oculta, após hero visível somente no mobile e próxima à seção final oculta novamente. Capturas de página inteira e screenshots após o hero estão no artifact do run.

### Aprovação pendente (não confundir com CI verde)
- Teste humano em navegadores reais, incluindo Safari e Firefox, orientação paisagem e leitores de tela.
- Conferir se screenshots de ambiente de teste são material comercial autorizado/publicável. As capturas atuais não são do build mais recente necessariamente.
- Fotos humanas (bar real e equipe) exigem mídia própria com direito de uso; **não** usar banco de imagens representando falsamente o piloto.
- Nova arte social `og:image` em PNG/JPEG e prova social com depoimento autorizado são próximas prioridades comerciais; **não** declarar concluídas.
- Revisão independente da branch e autorização explícita para merge e para deploy.
