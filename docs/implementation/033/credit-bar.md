# Spec033 E05-a — projeção de limite Web

Contrato: `specs/033-attendance-ux2-productization/epics/E05-customer-policy-surface/{spec,tasks}.md` na branch de especificação, PR216. PR212 `creditPanel` é a referência visual.

E05-01/02/03/06, contribuição Web: componente de leitura recebe `financial_position` já canônico e projeção separada do rascunho. Exposição, limite efetivo, capacidade e relacionamento são campos existentes; nenhum endpoint ou policy engine novo. Aritmética do progresso nunca autoriza pedido. ENFORCE permanece backend; Spec031/WARN_ONLY é dependência externa.

Critérios deste componente: números canônicos; 80% visível; faixa listrada para rascunho; 0 e >100% textuais; relacionamento desconhecido não inventado; dados ausentes indicados como indisponíveis; detalhes só quando fornecido callback. Testes em 360/390/430/desktop e texto 2x. Integração no workspace, Django real e Compose são gates próprios, não comprovados pelo harness isolado.

Medidas de `creditPanel` são preservadas. O alvo invisível de Detalhes amplia o hit area para 44px sem deslocar layout aprovado. Estado de excesso sem rascunho diz "Consumo" para não atribuir saldo histórico a pedido não enviado. Não existe alternância de modo na UI nem afirmação de garantia.

## Evidência do componente

`cd apps/web && npx playwright test --config tests/visual/credit-bar.config.ts`: 9 testes; screenshots `test-results/credit-bar/credit-{360,390,430,1280}-{1,2}x.png`. Harness transpila o componente React real em memória e carrega CSS/fontes reais, sem criar rota de teste no produto. Não substitui integração/API ou comparação visual completa com o protótipo.

`npm run typecheck`: PASS. Casos: 0/79/80/99/100/120%, projeção500centavos, zero de limite, cinco perfis e desconhecido, capacidade canônica sem recálculo, DTO ausente/inválido, foco de detalhes e hit area44px. Nenhuma mutation, cobrança, pedido ou autorização ocorre neste componente.
