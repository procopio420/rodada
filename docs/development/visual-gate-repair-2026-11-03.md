# Correção do gate visual — PR #325

Base examinada: `cd576bd1c6b40f0d4a86da9cb55ed1ec42d6acb7`, branch
`codex/pilot-stage3-external-card`. Escopo autorizado: corrigir a infraestrutura
e os testes visuais para validar os contratos atuais da Spec033, preservando
as asserções financeiras, de recovery, acessibilidade e comparação visual.

Não inclui mudança de regra de domínio, baseline visual, tolerância, CI,
merge ou deploy. A implementação financeira continua sujeita à revisão R3.
Este ajuste de fixtures é R2; mudanças que afetem a cobertura de recovery
devem passar pelo contexto revisor independente antes de encerrar o gate.

## Plano e critérios

- Responder somente aos endpoints conhecidos de observação passiva e listagem
  de grupos, com o contrato do servidor. Requisições desconhecidas continuam
  falhando; overrides negativos de cada teste continuam tendo precedência.
- Investigar falhas restantes e migrar navegações antigas para as páginas
  atuais, mantendo propósito e verificações de cada cenário.
- Rodar casos focalizados durante a correção e `npm run test:visual` integral
  ao final; registrar resultado real e SHA. Typecheck e lint dos testes mudados.
- Atualizar o relatório de release e o PR #325 com evidência e pendências;
  preservar o registro histórico de 785 PASS / 155 FAIL.

## Execução

- Primeira correção: fixtures explícitas de POST de telemetria (202), POST de
  observação de produção (202) e GET de grupos de mesas (lista vazia).
- Primeira reexecução interrompida após diagnóstico das próximas causas; não
  constitui PASS integral. As rodadas focalizadas seguintes isolaram seletores,
  regressões de foco e medições de toque no catálogo.

## Descobertas e regressões dentro do contrato existente

Spec033 AC-22 e design system já exigem alvos44px e retorno de foco. Os testes
existentes expuseram busca de mesa menor que44px e cancelamento de descarte sem
retorno ao acionador. Correções locais: altura mínima do input; captura explícita
do acionador nas duas entradas de descarte (revisão e conta). O teste conserva a
asserção de foco e agora percorre revisão→cancelar→conta→cancelar.

O menu do operador contém Atualizar/Sair no fluxo atual. Durante abertura de Tab
ou recuperação bloqueada, o header também deve respeitar o bloqueio operacional;
adicionados os guards `tableOpening` e `recoveryBlocked`, sem mudar autenticação,
comandos ou intenção persistida. Testes de leitura pendente/corrupção mantêm a
verificação de navegação bloqueada usando os controles atuais.
Agora e Mesas também respeitam `moveLocked`/`recoveryBlocked`, como Pedir já fazia.

O rodapé fixo do catálogo pode cobrir temporariamente parte de um alvo expandido
por pseudo-elemento. A auditoria mantém dimensão e quatro pontos de toque, mas
repete a medição após expor o controle por rolagem e restaura a posição original.
Registra os interceptores e reprova obstruções persistentes. Dois testes dedicados
cobrem oclusão temporária e persistente. Isso preserva o limite anterior: não mede
ownership de todos os controles fora da viewport ou já com retângulo ≥44px.

Na migração, botões/listas/modais antigos foram substituídos pelas regiões atuais,
sem retirar conflitos, payload imutável, sessão/revogação, efeito único ou isolamento
de rascunhos. Repetição inválida verifica pedido vazio; a configurada resolve o
replay e verifica que a variante original continua Pequena. A entrada pela mesa
agora lê saldos canônicos além dos três opens explícitos: toda leitura continua
exigindo o mesmo par table_id/occupancy_id; o teste separado de serialização ainda
exige um GET para dois cliques durante leitura pendente.

Gerência: seletores usam especificamente a navegação gerencial (atalhos adicionais
não são novas abas); retorno ao Cardápio e grade mobile/desktop seguem a Spec034,
sem alteração do produto ou tolerâncias para atender testes históricos.

Revisão independente preliminar encontrou dois P2 (alvo antigo ao descartar pela
conta e lacunas de asserção no rascunho repetido); corrigidos e enviados novamente
ao mesmo contexto revisor. Aprovação autenticada GitHub ainda não comprovada.

Rodadas diagnósticas interrompidas ou limitadas por falhas não são gate PASS.
Resultados e limites estão registrados abaixo.

## Validação de 04/11/2026

- `0e589fa11e3b68463a4b870262c73692ea8c4880`: build e 9 focais PASS.
  Visual integral: **940 PASS / 4 FAIL** (944 casos, Chromium, 4 workers,
  7,6 min). As quatro falhas ocorreram no mesmo seletor de inventário da
  Gerência: dois fieldsets usavam o nome acessível “Mesa 02”.
- `82a9f8d2a3abd9bbb9679c1a12d73b725b10ad5a`: seletor restrito ao fieldset de
  retirada, com payload exato e readback preservados. Auditoria de toque mede
  a área do label nativo associado a checkbox/radio, exige ≥44×44 e ownership,
  sem aceitar label com outro controle interativo. Teste demonstra clique fora
  do glifo que marca o checkbox e reprovação quando o label é reduzido.
  Focal: **9 PASS**, seis inventário e três auditoria.
- [Pontos de toque no catálogo](../releases/evidence/pilot-stage3-external-terminal/visual-repair-touch-targets.json):
  quatro jornadas, interceptores do rodapé antes da rolagem e os quatro pontos
  pertencentes ao controle após expô-lo. Fixture sintética, sem dados de bar.
- `npm run test:integration -- attendance-external-terminal.spec.ts
  attendance-settlement-recovery.spec.ts pos-cash-receipt.spec.ts
  tab-location-move.spec.ts`: **26 PASS** em PostgreSQL17 descartável no código
  `0e589fa1`. O delta até `82a9f8d2` é só de testes visuais, sem mudança do produto.
  Inclui 10 cartão externo, 15 CASH/settlement e 1 movimentação real. Banco encerrado.
- A revisão de outro contexto confirmou os P2 corrigidos e devolveu
  `NO_FINDINGS_WITH_GAPS` para `82a9f8d2`; não executou suites nem aprovou no GitHub.
  A aprovação autenticada permanece `REVIEW_BLOCKED`. O script qualificado exige
  PR fora de rascunho com base `main`; #325 ainda depende do #324.

A rodada final em `82a9f8d2` encerrou com **945 PASS / 0 FAIL / 0 skip** em 7,5 min,
com `npm run test:visual -- --workers=4`. Typecheck, build e lint das fontes
alteradas passaram. [Manifesto de validação](../releases/evidence/pilot-stage3-external-terminal/visual-repair-summary.json).
Os PNGs históricos reescritos pela suíte foram copiados para `.local/pilot-stage3`
e restaurados aos bytes versionados; nenhuma tolerância ou baseline foi reduzida.
