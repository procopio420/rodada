# Refinamentos locais do piloto Web — 05/11/2026

Base `1c10f307ec37098f881eccf932fdfe98c1879f72`, branch
`codex/pilot-stage3-external-card`, [PR #325](https://github.com/procopio420/rodada/pull/325).
O PR de refinamentos tem essa branch como base para separar o diff novo do
recebimento por cartão externo. A integração de pagamentos com provedor fica
fora deste recorte. O cartão externo existente registra aprovação conferida
na maquininha.

| Área | Comportamento e aceite |
| --- | --- |
| Bar | Busca inicial mostra produtos elegíveis diretamente; limpar volta às categorias. A grade de catálogo longo rola sem sobreposição. [Spec 026](../../specs/026-operational-ux-friction/spec.md) · [Aceite](../../specs/026-operational-ux-friction/acceptance.md) |
| Atendimento | Voltar indica destino. Gestos revisitam as telas da mesma comanda e preservam o rascunho. Entregas do mesmo destino e comanda canônicos são agrupadas, com confirmação do grupo ou seleção de itens. Cada entrega exige revalidação e leitura de DONE/DELIVERED; o envio dos restantes para na primeira pendência. [Aceite da Spec 033](../../specs/033-attendance-ux2-productization/acceptance.md) |
| Limite de consumo | No Atendimento Web em Só alertar, ultrapassar a referência projetada abre uma confirmação. A Gerência consegue tentar salvar sem eventos ao vivo quando a API responde. PIN, escopo, versão e leitura canônica continuam obrigatórios. [Spec 031](../../specs/031-venue-spending-limit-modes/spec.md) · [Aceite](../../specs/031-venue-spending-limit-modes/acceptance.md) |
| Gerência | Barra superior e grupos em colunas no desktop. Navegação inferior no celular. Operação compara filas e proporção de mesas. Financeiro compara saldos esperados já retornados pela API, com zero, negativos e ausência de valor tratados separadamente. [Spec 034](../../specs/034-management-ux-standardization/spec.md) · [Aceite](../../specs/034-management-ux-standardization/acceptance.md) |
| Mais vendidos | Colunas verticais dos dez itens e pizza por categoria atual do cardápio, sem Todos, com cores fixas por categoria. Data e atualização no cabeçalho. Eventos ao vivo e consulta periódica de 15 segundos. [Contrato da Spec 007](../../specs/007-management-cockpit/best-sellers.md) |

## Evidência e limites

- Durante a implementação, o build Web e rodadas Playwright focadas passaram
  para as superfícies acima. As rodadas incluíram largura móvel e desktop,
  teclado, catálogo longo, grupos com confirmação parcial, mudança de destino
  e resposta perdida, atualização por evento simulado e por consulta
  periódica, além de caixa com valor negativo, zero e ausente.
- Os testes visuais usam fixtures sintéticas. O resultado consolidado é
  registrado no PR. Suíte visual integral, testes Web integrados com
  PostgreSQL, homologação em celular e homologação operacional continuam
  pendentes neste recorte.
- No commit-base, [Web](https://github.com/procopio420/rodada/actions/runs/41775884534)
  e [Knowledge Base](https://github.com/procopio420/rodada/actions/runs/41775884435)
  passaram. Esse resultado pertence ao #325. Em 05/11, a consulta de revisões
  do #325 retornou vazia.
- Risco máximo R3 pela apresentação financeira e pelo fluxo de política de
  consumo. Revisão independente autenticada pendente (`REVIEW_BLOCKED`).
  Conferir PIN/versão/escopo do editor, revalidação e recuperação da entrega
  por item, autorização e proveniência dos totais financeiros.

## Continuidade

O mantenedor acompanha a CI e encaminha a revisão independente. A integração
com a main depende da cadeia do #325 e dos gates do novo commit. Railway,
deploy, iPhone e aceite de produção ficam na homologação. Sem ADR nova neste
recorte.
