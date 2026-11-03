# Etapa 3 — recebimento de cartão externo no Atendimento Web

Data: 03/11/2026. **Implementado e testado localmente; NO-GO produção.**
Gate visual completo FAIL (785 PASS / 155 FAIL), comparação dirigida concluída;
aprovação R3 autenticada permanece REVIEW_BLOCKED. Não confundir revisão de agente com aprovação GitHub.

Autorização humana: “pode fazer amigo estou acompanhando obrigado”, após indicar
etapa 3/cartão externo como próximo trabalho. Escopo: somente esta slice,
sem retirada rápida/PR314, PSP, Pix, Android, merge, deploy ou acesso remoto.

## Candidato e contrato

- Base `7d4168376c386e07e7387de3d34de2fa4294bd77` (etapas 1–2 do PR324).
- Código funcional `afae48a1d5598ea20289dfb0b1b703ad9c9e1f6c`;
  testes reforçados em `6e7b17b8ab8b3da95bb8b0f1aef91240937f89db`.
- Branch local `codex/pilot-stage3-external-card`. Main remota reconsultada:
  `67972d09200d43357b5b88dc0f64218967e4c24b`.
- Risco R3, por pagamentos, gateway e intenção recuperável.
- [Contrato da slice](../../specs/033-attendance-ux2-productization/epics/E04-settlement-and-table-turnover/external-terminal/spec.md),
  com plano/tarefas/aceite preparados antes do código; proprietárias Spec006
  PAY-008, Spec012, Spec014/026 e Spec033 E04. Sem ADR nova ou mudança de ledger.

## Comportamento entregue

Atendimento oferece **Cartão externo** na tela de recebimento. Operador informa
o valor aprovado na maquininha e marca “Conferi a aprovação na maquininha externa”
antes de registrar. Rodada não aciona maquininha nem afirma integração com PSP.

Método canônico EXTERNAL_TERMINAL, separado de CASH/CARD integrado. Não exige
caixa aberto e não envia cash_point_id ou cria movimento físico. CASH mantém seu
caixa e comportamento. Parcial mantém saldo/Tab aberta; integral segue fechamento
canônico. Mesa continua ocupada após quitação, exigindo saída explícita.

Novo envelope schema3 exclusivo de EXTERNAL_TERMINAL, sem caixa, com método/valor/
identidade/chave congelados antes do POST; schema1/2 CASH preservados. Gateway
aceita somente CASH/EXTERNAL_TERMINAL com shape específico. Rejeita CARD, PIX,
TAP_TO_PAY, CARD_ONLINE, OTHER, arrays e campos indevidos. Backend existente
continua autoridade para sessão, capability, Venue, versão, saldo e idempotência.

Resposta perdida/reload repete a intenção original. Readback confere ID/Tab/
método/valor/status; método divergente mantém pendência. Fase confirmada salva
antes de fechar; retomar não reposta Payment já identificado. Outra sessão não
adota intenção; sessão revogada não recupera acesso restaurando cookie antigo.

Arquivos: componente `pos-cash-receipt.tsx`, CSS de workspace, gateway
`app/api/attendance/[...path]/route.ts`, testes reais/visuais e contrato.
Nenhuma alteração de API Python, schema de banco, grants ou secrets.

## Validação

Ambiente: Windows, Node24.22.1, Python3.12.14, Next16.3.8, Django5.2.19,
PostgreSQL17.11 local/descartável em 55432; mesmas ferramentas da etapa2.
Nenhuma operação de cliente real, dinheiro real ou banco de demo/produção.

- PASS: primeira execução Web 22 testes (sete novos e 15 regressões CASH).
- PASS: nove casos novos após adicionar envelope inválido e misto.
- PASS: caso de revogação real (logout204; replay com cookie antigo401).
- PASS: suite final 10/10, 1,2 min, com mesa explícita e assertiva OCCUPIED após
  quitação por cartão, no teste 58dda307. A primeira assertiva procurava a mesa
  pela lista de Tabs ativas, que exclui CLOSED; teste corrigido para guardar e
  conferir tableId estável, sem alterar produto nem enfraquecer OCCUPIED.
- PASS: 39 testes PostgreSQL de ledger/pagamentos/concorrência, permissões e
  resumo por método: `test_payments_concurrency.py`, `test_access_permissions.py`,
  `test_ledger_payments.py`, `test_cash_payment_method_summary.py`.
- PASS: auth/tenant Node14, TypeScript, build e ESLint dos arquivos da slice.
- FAIL: visual completo `npm run test:visual -- --workers=4`, 940 casos,
  785 PASS / 155 FAIL, 16,4 min. Sem skips adicionais ou baselines/tolerâncias
  relaxados. Primeira execução local com um worker interrompida para repetir
  integralmente com quatro workers, sem alterar configuração de CI.
- Comparação dirigida na base 7d416837: todas as 155 falhas do candidato cobertas;
  152 testes também falharam na base. Os outros três passaram na base e no
  candidato em repetição isolada: ranking430, Quick Catalog390 e contexto de
  caixa sem ACK perdido. Esses sinais de instabilidade não tornam verde o gate.
  A base completa940 não foi executada; não presumir identidade de causa de
  todos os erros somente porque um mesmo teste falhou nos dois candidatos.
  [Resumo sanitizado por caso](evidence/pilot-stage3-external-terminal/visual-comparison.json).
- Os quatro cenários visuais alterados de recebimento (360/390/430/1280) passaram
  com mesma fixture CASH→externo, Space no checkbox e layout/a11y.
- PASS: KB (49 documentos/312 links na conferência anterior à atualização final),
  cinco testes do verificador, diff e links da slice; contagem final no handoff.

Nos testes reais: aprovação externa explícita e formulário/teclado/a11y nas
larguras360/390/430; parcial/integral sem caixa; saldo e método; misto com efeito
físico apenas CASH; lost ACK, readback com método errado, sessão diferente,
envelope inválido, sessão revogada/cookie antigo, capability, cross-Venue,
métodos/campos proibidos. Mocks de método errado são injeção de falha de leitura;
pagamento/ledger são reais em PostgreSQL. Fixture API prepara produtos/Tab/mesa.

[Capturas reais de formulário 360/390/430](evidence/pilot-stage3-external-terminal/)
inspecionadas: cartão externo separado, texto sem alegação de integração, checkbox
explícito e área de toque44px. No visual, mesma fixture antes/depois da seleção
CASH→externo, Space no checkbox, alvo44px e axe. Não é certificação WCAG ou
homologação humana/em dispositivo físico.

## Revisão independente

Revisor: contexto novo `/root/review_external_terminal`, somente leitura, conforme
AGENTS e skill rodada-code-review. Revisou base→afae48a1 e deltas de testes→6e7b17b8→58dda307.
**Sem achados reproduzíveis; NO_FINDINGS_WITH_GAPS**. Não executou testes; resultados
de execução são do autor. Segunda inspeção não encontrou relação demonstrável
entre as falhas visuais de pedidos/chamadas e o patch; comparação executada na
base foi executada pelo autor depois, registrada acima; não foi substituída
pela avaliação estática do revisor. [Registro da revisão](evidence/pilot-stage3-external-terminal/review.md).

Revisão não é GitHub App qualificado/aprovação autenticada. Gate formal R3 segue
**REVIEW_BLOCKED**, sem recomendação de merge ou produção. Qualquer alteração de
código subsequente exige reavaliação do novo diff.

## Limites e continuidade

Etapa3 não significa concluir todos os gaps do piloto. Gate visual amplo está
FAIL, com comparação registrada; correção de fixtures/seletores/instabilidades
amplas deve ser uma slice própria, sem remover teste ou relaxar tolerância.
CI remota, operador físico/maquininha real, fiscal, rede real, R3 autenticado,
backup/restore/rollback e retenção continuam pendentes. Android não foi alterado
ou homologado. Não houve merge/deploy/publicação de produto.

Próximo responsável: mantenedor prioriza a dívida do gate visual e providencia
revisão R3 autenticada antes de merge. Código do recurso local concluído; etapa3
permanece EM_EXECUCAO pelos gates e pela priorização dos outros gaps. Etapas4–6 e
qualquer ampliação da etapa3 seguem dependências/autorizações do plano.

## Evidência final e ambiente encerrado

[Fotografia sanitizada do PostgreSQL](evidence/pilot-stage3-external-terminal/canonical-local.json):
10 Tabs sintéticas, 14 Payments e um CashMovement ligado ao CASH do caso misto.
[Manifesto da slice](evidence/pilot-stage3-external-terminal/manifest.json) contém
hashes de fonte e artefatos, normalizando LF em texto. Relatórios HTML, traces e
logs brutos ficam em `.local/pilot-stage3`, não versionados. Capturas históricas
reescritas pela suite foram preservadas localmente e restauradas ao Git original;
nenhum baseline foi atualizado para mascarar falha. PostgreSQL é encerrado ao
final; nenhum serviço Windows ou infraestrutura remota configurados.
