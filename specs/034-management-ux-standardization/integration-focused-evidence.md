# Integração focada Web/API/PostgreSQL —2026-10-21

Branch codex/management-ux-alerts, base HEAD860b25d93da486d2416c6ddaccfdccd9605f8953,working treeacumulado. Semcommit/push/merge/deploy. R3:infraestrutura de reset de testes;nenhuma implementação deproduto/financeiro alterada nesta etapa.

## Impedimento e correção

Executor importavafcntl incondicionalmente,indisponível noPythonWindows verificado. WSL/Linux não disponível. e2e_db_guard.py agora conserva flock Linux e usa byte0/msvcrt noWindows,comexclusão conservadora de leitores e resets,finallyunlock e retry apenasEACCES/EAGAIN/EDEADLK. Erros desconhecidos propagam antes da operação. Namespace de diretório temporário não depende deos.getuid noWindows. Allowlist localPostgreSQL/rodada_web_e2e e regrasSQLSTATE permanecem.

Regressões ampliadas:handshake do filho antes de tentar lock,espera real por reset de outro processo,release após exceção e erroWindowsdesconhecido falhando fechado. Ajustes de lint organizam imports/contextmanagers e capturam variáveis do cenário de retry. Ruff inicialmente identificou estilo/imports/closures;corrigidos sem alterar intenção dos asserts.

## Evidência executada

-6unitáriosPASS0,268s noWindows;Ruffdos2arquivosPASS;diffcheckPASS.
-**13integraçõesPASS/0falhas/1,8min**,1worker,semretries. Arquivos:developer-staff.spec.ts,guest-order-intent.spec.ts,management-alerts.spec.ts,manual-refund-intent.spec.ts,zz-pricing.spec.ts.
-Cobre cadastro/edição/revogação de equipe comreadback,guestcommittedorder/reload/revogação,política/ack/resolução de alertas,estorno/correção com resposta comprometida perdida360/390/430,desconto/serviço/pagamento parcial/correção e reconciliação final.
-APIs reais Django/PostgreSQL viaBFF;transportes cortados deliberadamente pelos testes de falha não substituem respostas canônicas porfixturesHTTP.

Banco descartável NOVO em clusterseparado visual-artifacts/spec034-integration/pgdata,porta55479,DBrodada_web_e2e. Banco preexistente de mesmo nome em55460 não foi usado/resetado. Allowlist/destino e ausência de conexão ativa foram conferidos antes;novo cluster elimina dependência do estado anterior. Seed/migrate/flush ocorreram somente noDBdescartável novo conforme executor. API8100/Web3110 pertenciam ao runner;cluster55479 encerrado com segurança ao terminar,arquivos preservados. Serviços deinspeçãoWeb3001/API8000/DB55460preservados;readyAPI200 eWebcustomers200reverificados após execução.

Ambiente:RODADA_E2E_POSTGRES=1,POSTGRES_DB=rodada_web_e2e,POSTGRES_HOST=127.0.0.1,POSTGRES_PORT=55479,POSTGRES_USER=rodada,POSTGRES_PASSWORD vazio emtrustloopback,RODADA_TEST_PYTHON apontando aoPythonvenv existente,PYTHONUTF8=1. Comando apps/web:pnpm run test:integration developer-staff.spec.ts management-alerts.spec.ts manual-refund-intent.spec.ts zz-pricing.spec.ts guest-order-intent.spec.ts. HTML temporário apps/web/playwright-report/integration/index.html.

## Revisão e limites

Revisão independente local final:NO_FINDINGS_WITH_GAPS,guard/testehashes registrados. Revisor não executou integração nem operoucluster. Espera indefinida sob EACCES persistente e coordenação entre usuários/TEMPdistintos não validadas. BackendLinux preservado por inspeção,sem execuçãoLinux nesta etapa. Janela dotestechild sinaliza tentativa antesdobloqueio.

Recorte13PASS não equivale à suíteintegral,duasVenues/concorrência completa,homologaçãooperador/dispositivo/fornecedor ouCIremota.296visuais e59guest passaram nasrodadas anteriores,sem somar como execução única. NenhumWebUIalterado aqui;build/tipos/lintglobalWeb da rodada anterior não reexecutados por mudança apenasPythondeinfra. GateR3autenticado REVIEW_BLOCKED;NO-GOrelease/piloto.

Próximo responsável:conferência manual comusuário e fechamento dosgatesremotos/reviewautenticado;expandir integração só conforme risco/gaps reais. Preservarpatches,sem publicarautomaticamente. Hashes docs/development/evidence/spec034-integration-focused/SOURCE-SHA256SUMS.
