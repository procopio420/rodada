# Etapa 4 — ensaio local de restauração

Em 04/11/2026, na branch `codex/pilot-stage3-external-card`, SHA
`783869db27eccfb30654fe3769126841cc5f9499`, foi ensaiada a recuperação de
um backup sintético em PostgreSQL 17.11 local, com dois bancos descartáveis
distintos. O runbook de backup e restauração foi adaptado para PowerShell.
O destino foi criado com nome novo, sem `dropdb`.

`migrate`, `seed_restore_rehearsal` e `verify_restore` passaram na origem.
`pg_dump` em formato custom levou 0,96 s e `pg_restore --exit-on-error` levou
1,77 s. No destino, `migrate --check`, `check` e `verify_restore` passaram.
O verificador confirmou saldo zerado, vínculo entre estorno e reversão,
caixas aberto e fechado, ocupação e sessão guest ativas e histórico de entrega
concluído. `tests/test_full_shift_smoke.py` passou em banco de teste separado.
O servidor PostgreSQL local foi encerrado.

SHA-256 do dump sintético: `148c5022b0d0699e04fe2fb369f8b56d259322280ced06c15bd27efbe6e2f94b`.
Artefato e metadados locais em `.local/pilot-stage4-20261104010024`.
Os tempos medem apenas dump e restore dessa fixture pequena.

## Ensaio de rollback Web

O navegador acessou uma origem local única. Um proxy alternou o build Web
candidato `783869db` e o build da base `7d416837`, sobre a mesma API e o
mesmo PostgreSQL sintético de integração. Esse ensaio é separado do banco
restaurado acima. A troca preservou cookies e `sessionStorage` na mesma aba.

No cenário de pedido misto BAR/Cozinha com resposta perdida após o commit,
o build anterior preservou o envelope, reenviou o mesmo payload e recebeu o
ID original. O readback confirmou um pedido, dois itens, saldo de 1.500
centavos e zero pagamentos. O teste focal passou em 17,9 s. Tentativas
anteriores falharam na contagem do interceptador local. A execução final
conferiu o payload e o ID na resposta de replay e o estado canônico na API.

No cenário de cartão externo, o pagamento foi confirmado no servidor e a
resposta foi interrompida. A versão anterior exibiu o bloqueio de recuperação,
preservou o envelope do recebimento e manteve um único pagamento. Ao retornar
ao candidato, a recuperação usou o mesmo payload e o mesmo ID. Permaneceu um
pagamento de 500 centavos e saldo aberto de 1.500 centavos. A versão anterior
não consegue reconciliar esse formato de intenção. Antes de uma reversão
operacional, é preciso tratar os recebimentos pendentes, com retorno a uma
versão compatível e conferência canônica pela gerência quando necessário.

Runner temporário e logs brutos estão em `.local`. O PostgreSQL foi encerrado.

## Retenção e pendências

O teste PostgreSQL `test_old_first_receipts_are_pruned_without_losing_daily_aggregates`
passou. Uma observação vencida foi removida, o agregado diário permaneceu e
uma nova leitura do pedido antigo não voltou a incrementar o contador.
Para o ensaio agendado, falta identificar ambiente e responsável, registrar
horário, saída e última execução bem-sucedida, e provar alerta em caso de
falha ou ausência de execução. A fila de receipts vencidos precisa ser
monitorada porque o comando tem limite por lote e por execução.

### Ensaio do agendamento e detecção de falhas

O runner local disparou o comando real `prune_attendance_telemetry` por
temporizador contra um banco PostgreSQL 17.11 novo e descartável. Na primeira
execução, com limite de um registro por tipo, ficou um receipt vencido. Na
segunda, a fila zerou. Os dois receipts recentes e o total diário de sete
eventos foram preservados, assim como as contagens de pedidos e pagamentos.
Uma execução com tamanho de lote inválido retornou código 1 e manteve o
registro da última execução bem-sucedida. Com relógio simulado, o detector
ficou normal em 24 h e indicou atraso em 27 h para um limite de 26 h.
O PostgreSQL foi encerrado. Runner e resultado ficam em
`.local/pilot-stage4-retention.py` e `.local/pilot-stage4-retention-evidence.json`.

Proposta para o piloto: execução diária, registro persistente da última
execução bem-sucedida, alerta por código de saída diferente de zero e por
ausência de sucesso em 26 h, e acompanhamento da fila de vencidos após a
limpeza. O temporizador e o detector locais foram exercitados. A agenda
persistente e a entrega do alerta ainda precisam ser verificadas no ambiente
do piloto, com um responsável designado.

A etapa 4 segue em execução. Faltam comprovar a retenção agendada e a reversão
no ambiente aplicável. No SHA `783869db`, Web e Knowledge Base passaram no
GitHub. A revisão R3 autenticada do PR #325 permanece pendente. Produção
continua NO-GO.

O [roteiro de homologação física Web da etapa 5](pilot-stage5-web-homologation-checklist-2026-11-04.md) está preparado. A execução física segue pendente.

### Configuração proposta para a revisão operacional

O inventário histórico registra `rodada-aderlan-demo-20261009/demo`. Antes de
aprovar a operação, o mantenedor deve confirmar projeto, ambiente, Postgres,
imagem implantada, ausência de mudanças pendentes e responsável pelo alerta.
Esta sessão não dispõe de conector nem CLI Railway autenticada para confirmar
esses dados atuais. [Inventário histórico](../ops/spec025-gate3-canary.md)

| Campo | Proposta |
| --- | --- |
| Serviço | Job dedicado `rodada-telemetry-retention`, sem domínio público, com imagem imutável do candidato aprovado |
| Agenda | `0 8 * * *`, diariamente às 05h em São Paulo (08h UTC) |
| Processo | `python /app/apps/api/manage.py prune_attendance_telemetry --batch-size 1000 --max-batches 10` |
| Conexão | Referências do Postgres privado do ambiente aprovado, verificadas pelo mantenedor |
| Monitor | Consulta independente ao histórico e aos logs. Alertar em falha ou execução pulada e após 26 h sem sucesso comprovado. Registrar destino do alerta e responsável antes de ativar |
| Fila | Conferir registros vencidos restantes após a execução. Sucesso do processo pode coexistir com fila pendente por causa do limite dos lotes |

O comando dedicado encerra após a limpeza. Confirmar que o comando de início
efetivo é o da tabela, pois o comando padrão da imagem inicia a aplicação e
aplica migrações. A agenda Railway usa UTC e pode pular a próxima execução
se a anterior continuar ativa. [Dockerfile](../../deploy/railway/Dockerfile) ·
[Railway Cron Jobs](https://docs.railway.com/cron-jobs)

Para aceitar, registrar duas execuções consecutivas disparadas pela agenda,
com SHA, horário, ID da execução, resultado e contagens sanitizadas. Confirmar
que registros recentes e agregados permanecem no ambiente de ensaio. Provar
entrega de alerta em teste controlado com a integração de monitoramento e
conferir recuperação do monitor após novo sucesso. Em caso de falha, suspender
a agenda do job dedicado sob autorização e investigar antes de reativar.
A suspensão impede novas limpezas. Registros já apagados só podem voltar por
procedimento de restauração aprovado. [Histórico de cron no Railway](https://docs.railway.com/cli/cron)
