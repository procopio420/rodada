# Plano — Spec 030

## Slice 1 — página estática e narrativa (este PR)
1. Reescrever `apps/landing/index.html` com texto emocional/provocativo em PT-BR, mantendo canal comercial e links legais.
2. Versionar cópias de screenshots de fixture presentes em `docs/design/evidence/spec023-demo-web/` dentro de `apps/landing/screens/` para uso estático sem dependências externas.
3. Garantir responsividade e fallback sem JavaScript.
4. Atualizar README e adicionar checagem de contrato estático.

## Slice 2 — fotografia e prova do piloto (futuro, condicionado)
Após autorização de uso e revisão visual, substituir/combinar arte abstrata por fotografias reais do estabelecimento. Adicionar somente depoimentos autorizados e fatos verificáveis. Não pressupor esse material.

## Slice 3 — medição e experimentos (decisão futura)
Definir metas e consentimento antes de analytics, eventos ou testes A/B. Sem scripts de terceiros por padrão.

## Gate
Testes estáticos e checagem visual real de 360/390/430/desktop, acessibilidade de teclado e imagens Docker. Deploy/merge separados, somente com autorização.


## Slice 1b — revisão de conversão por dispositivo
- CTA pequeno responsivo no header (360 px sem quebra).
- CTA fixo somente após sair do hero e antes da seção final (progressive enhancement inline, sem tracking).
- Texto comercial orientado a momentos reais de bar cheio, com fluxo de pedido/produto concreto.
- Galeria enquadrada e legendada como prova de teste, sem falsa fotografia de cliente.
- Contratos Playwright para hero, scroll e CTA em novas larguras.

## Slice 3 — sistema visual contemporâneo (PR #188)
1. Tirar arte-pôster do primeiro viewport; texto de marca em HTML com hierarquia editorial e CTA acima da dobra.
2. Usar o recorte humano da arte como fotografia ilustrativa sem tipografia embutida, mantendo a peça original só em OG.
3. Construir um tour de três experiências usando screenshots reais de fixture, com fallback sem JS.
4. Reduzir ruído de múltiplos cards decorativos: ritmo por seções de alto contraste, linhas e recortes.
5. Rodar QA e screenshots mobile (320/360/390/430), tablet e desktop 1440/1920; validar tabs e CTA sticky.
6. Sem merge/deploy, dados de produção, dependências externas ou alteração de branding.
