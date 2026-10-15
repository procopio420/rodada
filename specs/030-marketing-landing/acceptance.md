# Critérios de aceite — Spec 030

## Slice 1
- [x] Hero traz “Mais uma rodada. Menos trabalho.” e “Seu bar merece movimento. Não confusão.”
- [x] CTA de demonstração aponta para WhatsApp oficial pré-existente, sem captura silenciosa de dados.
- [x] Fluxo comunica atendimento, produção e gerência sem prometer taxas/receitas.
- [x] Capturas de teste locais têm texto alternativo e aviso de que não são homologação/produção.
- [x] Preço, migração, equipamentos e conectividade não recebem promessas não verificadas.
- [x] Links legais e canonical de `rodada.bar` preservados.
- [x] Documento usa HTML semântico, CSS responsivo, foco visível e opção de movimento reduzido.
- [x] Renderização Chromium em 360/390/430/768/1440 sem overflow, imagens quebradas, erros de página ou CTA abaixo da primeira dobra. [Execução](https://github.com/procopio420/rodada/actions/runs/38759159228).
- [x] Após a revisão comercial: header não quebra entre 320–380px, CTA do hero continua disponível, CTA fixo começa oculto, aparece após o hero e some no CTA final. [Evidência de 10 viewports](https://github.com/procopio420/rodada/actions/runs/38764191415).
- [ ] Aprovação humana das capturas para publicação e revisão de acessibilidade assistiva completa.
- [x] Verificações estática e visual executadas após revisão de conteúdo, respectivamente [Landing](https://github.com/procopio420/rodada/actions/runs/38764191585) e [Visual QA](https://github.com/procopio420/rodada/actions/runs/38764191415). Checar CI novamente após qualquer alteração posterior.

Os critérios testados provam a renderização/contrato do **PR**, não homologação em bar, inspeção em Safari/Firefox ou publicação em `rodada.bar`.
