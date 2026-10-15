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
